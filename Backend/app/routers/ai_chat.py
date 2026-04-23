"""AI导诊服务路由"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import grpc
import json
import os
import asyncio
from app.utils import success_response, error_response, get_current_user
from app.grpc_client import get_grpc_stub
from app.models.surgery_record import SurgeryRecord
from app.models.ai_chat_session import AIChatSession, AIChatMessage
from app.models.ai_diagnosis_report import AIDiagnosisReport

router = APIRouter(tags=["AI导诊服务"])

GRPC_CHAT_TIMEOUT = float(os.getenv("AI_GRPC_CHAT_TIMEOUT", "90"))
GRPC_DEFAULT_TIMEOUT = float(os.getenv("AI_GRPC_DEFAULT_TIMEOUT", "20"))


class CreateSessionRequest(BaseModel):
    patient_id: str
    patient_name: str
    surgery_date: Optional[str] = None
    surgery_name: Optional[str] = None
    surgery_hospital: Optional[str] = None
    surgery_type: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    is_end: bool = False


class EndSessionRequest(BaseModel):
    session_id: str


@router.post("/create-session")
async def create_session(request: CreateSessionRequest):
    """创建导诊会话"""
    stub, channel, pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    surgery_name = request.surgery_name
    surgery_date = request.surgery_date
    surgery_hospital = request.surgery_hospital
    
    if not surgery_name:
        try:
            print(f"[DEBUG] 查询患者 {request.patient_id} 的手术记录...")
            latest_surgery = await SurgeryRecord.filter(
                patient_id=request.patient_id
            ).order_by("-surgery_date").first()
            
            print(f"[DEBUG] 查询结果: {latest_surgery}")
            if latest_surgery:
                surgery_name = latest_surgery.surgery_name
                surgery_date = latest_surgery.surgery_date.strftime("%Y-%m-%d") if latest_surgery.surgery_date else None
                surgery_hospital = latest_surgery.hospital
                print(f"[DEBUG] 找到手术记录: {surgery_name}, {surgery_date}")
        except Exception as e:
            print(f"[WARNING] 查询手术记录失败: {e}")
    
    try:
        response = stub.CreateSession(
            pb2.CreateSessionRequest(
                patient_id=request.patient_id,
                patient_name=request.patient_name,
                surgery_date=surgery_date or "",
                surgery_type=surgery_name or ""
            ),
            timeout=GRPC_DEFAULT_TIMEOUT
        )
        
        db_session = await AIChatSession.create(
            id=response.session_id,
            user_id=request.patient_id,
            title=surgery_name or "AI问诊",
            surgery_type=surgery_name,
            status="active"
        )
        print(f"[DEBUG] 已保存会话到数据库: {response.session_id}")
        
        surgery_info = None
        if surgery_name:
            surgery_info = {
                "surgery_name": surgery_name,
                "surgery_date": surgery_date,
                "surgery_hospital": surgery_hospital
            }
        
        welcome_message = response.welcome_message
        if surgery_name:
            welcome_message = f"{response.welcome_message}\n\n我了解到您做了【{surgery_name}】手术，\n请您确认一下是这样吗？"

        return success_response(data={
            "session_id": response.session_id,
            "created_at": response.created_at,
            "welcome_message": welcome_message,
            "surgery_info": surgery_info
        })
    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"创建会话失败: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """发送消息并以SSE流式获取AI回复"""
    print(f"[DEBUG] 收到流式聊天请求: session_id={request.session_id}, message={request.message}")

    stub, channel, pb2 = get_grpc_stub()

    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")

    async def event_generator():
        full_content = ""
        try:
            def request_generator():
                yield pb2.ChatRequest(
                    session_id=request.session_id,
                    message=request.message,
                    is_end=request.is_end
                )

            # 将同步 gRPC 流转换为 async queue 以支持心跳
            queue = asyncio.Queue()
            stream_done = asyncio.Event()

            def grpc_stream_worker():
                try:
                    for response in stub.Chat(request_generator(), timeout=GRPC_CHAT_TIMEOUT):
                        queue.put_nowait(response)
                        if response.is_final:
                            break
                except Exception as e:
                    queue.put_nowait(e)
                finally:
                    stream_done.set()

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, grpc_stream_worker)

            while True:
                get_task = asyncio.create_task(queue.get())
                heartbeat_task = asyncio.create_task(asyncio.sleep(15))

                done, _ = await asyncio.wait(
                    [get_task, heartbeat_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                if heartbeat_task in done:
                    yield "data: {\"type\": \"ping\"}\n\n"
                    continue

                item = await get_task

                if isinstance(item, grpc.RpcError):
                    error_msg = item.details() or "gRPC 调用失败"
                    error_chunk = {"error": error_msg.replace("\n", " ").replace("\r", " ")}
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    break
                elif isinstance(item, Exception):
                    error_msg = str(item)
                    error_chunk = {"error": error_msg.replace("\n", " ").replace("\r", " ")}
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    break

                chunk = {
                    "content": item.content,
                    "is_final": item.is_final,
                    "reference": item.reference
                }
                full_content += item.content
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                if item.is_final:
                    break

            await stream_done.wait()

        except Exception as e:
            error_msg = str(e).replace("\n", " ").replace("\r", " ")
            error_chunk = {"error": f"发送消息失败: {error_msg}"}
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """发送消息并获取AI回复"""
    print(f"[DEBUG] 收到聊天请求: session_id={request.session_id}, message={request.message}")

    stub, channel, pb2 = get_grpc_stub()

    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")

    try:
        def request_generator():
            yield pb2.ChatRequest(
                session_id=request.session_id,
                message=request.message,
                is_end=request.is_end
            )

        responses = []
        for response in stub.Chat(request_generator(), timeout=GRPC_CHAT_TIMEOUT):
            responses.append({
                "content": response.content,
                "is_final": response.is_final,
                "reference": response.reference
            })
            if response.is_final:
                break

        if not responses:
            return error_response(code="50005", msg="未收到AI回复")

        full_content = "".join([r["content"] for r in responses])
        final_response = responses[-1]

        return success_response(data={
            "content": full_content,
            "is_final": final_response["is_final"],
            "reference": final_response.get("reference", "")
        })

    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"发送消息失败: {str(e)}")


@router.post("/end-session")
async def end_session(request: EndSessionRequest):
    """结束导诊会话，获取病历报告"""
    stub, channel, pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        # 先获取完整对话历史并保存到数据库
        try:
            history_resp = stub.GetSessionHistory(
                pb2.GetSessionHistoryRequest(session_id=request.session_id),
                timeout=GRPC_DEFAULT_TIMEOUT
            )
            msg_count = 0
            for msg in history_resp.messages:
                await AIChatMessage.create(
                    session_id=request.session_id,
                    role=msg.role,
                    content=msg.content
                )
                msg_count += 1
            db_session = await AIChatSession.filter(id=request.session_id).first()
            if db_session and msg_count > 0:
                db_session.message_count = msg_count
                await db_session.save()
        except Exception as e:
            print(f"[WARNING] 保存对话历史到数据库失败: {e}")

        response = stub.EndSession(
            pb2.EndSessionRequest(session_id=request.session_id),
            timeout=GRPC_DEFAULT_TIMEOUT
        )
        
        report = None
        if response.report:
            report = {
                "patient": {
                    "name": response.report.patient.name,
                    "gender": response.report.patient.gender,
                    "age": response.report.patient.age,
                    "surgery_type": response.report.patient.surgery_type,
                    "surgery_date": response.report.patient.surgery_date,
                    "doctor_name": response.report.patient.doctor_name
                },
                "chief_complaint": response.report.chief_complaint,
                "present_illness": response.report.present_illness,
                "surgery_status": {
                    "wound_healing": response.report.surgery_status.wound_healing,
                    "temperature": response.report.surgery_status.temperature,
                    "appetite": response.report.surgery_status.appetite,
                    "activity": response.report.surgery_status.activity
                },
                "past_history": {
                    "allergy": response.report.past_history.allergy,
                    "chronic_disease": response.report.past_history.chronic_disease,
                    "medication": response.report.past_history.medication
                },
                "ai_analysis": {
                    "health_advice": response.report.ai_analysis.health_advice,
                    "alert_flag": response.report.ai_analysis.alert_flag,
                    "alert_reason": response.report.ai_analysis.alert_reason
                },
                "doctor_advice": {
                    "medical_advice": response.report.doctor_advice.medical_advice,
                    "followup_items": response.report.doctor_advice.followup_items,
                    "next_visit_date": response.report.doctor_advice.next_visit_date,
                    "need_followup": response.report.doctor_advice.need_followup
                },
                "session_info": {
                    "conversation_rounds": response.report.session_info.conversation_rounds,
                    "submitted_at": response.report.session_info.submitted_at
                }
            }
        
        # 更新会话状态为已完成，并保存病历
        try:
            db_session = await AIChatSession.filter(id=request.session_id).first()
            if db_session:
                db_session.status = "completed"
                await db_session.save()

            if report and db_session:
                await AIDiagnosisReport.create(
                    patient_id=db_session.user_id,
                    chat_id=request.session_id,
                    chief_complaint=report.get("chief_complaint", ""),
                    symptoms=json.dumps(report.get("present_illness", ""), ensure_ascii=False),
                    possible_diagnosis=report.get("ai_analysis", {}).get("health_advice", ""),
                    suggestions=report.get("doctor_advice", {}).get("medical_advice", ""),
                    severity="紧急" if report.get("ai_analysis", {}).get("alert_flag") else "普通",
                    report_status="completed",
                    detail=json.dumps(report, ensure_ascii=False)
                )
        except Exception as e:
            print(f"[WARNING] 保存会话状态/病历失败: {e}")

        return success_response(data={
            "report": report,
            "status": response.status
        })
        
    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"结束会话失败: {str(e)}")


