"""AI导诊服务路由"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import grpc
import os
import sys
import json
from app.utils import success_response, error_response, get_current_user
from app.models.surgery_record import SurgeryRecord
from app.models.ai_chat_session import AIChatSession, AIChatMessage

router = APIRouter(tags=["AI导诊服务"])

AI_SERVICE_HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1:50053")
GRPC_CONNECT_TIMEOUT = float(os.getenv("AI_GRPC_CONNECT_TIMEOUT", "3"))
GRPC_CHAT_TIMEOUT = float(os.getenv("AI_GRPC_CHAT_TIMEOUT", "90"))
GRPC_DEFAULT_TIMEOUT = float(os.getenv("AI_GRPC_DEFAULT_TIMEOUT", "20"))
_grpc_stub = None
_grpc_channel = None
_medical_ai_pb2 = None


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


class GetHistoryRequest(BaseModel):
    session_id: str


def get_grpc_stub():
    """获取 gRPC 客户端"""
    global _grpc_stub, _grpc_channel, _medical_ai_pb2
    try:
        if _grpc_stub and _grpc_channel:
            return _grpc_stub, _grpc_channel, _medical_ai_pb2

        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        project_root = os.path.dirname(backend_dir)
        connect_dir = os.path.join(project_root, "GlmAI", "connect")
        if connect_dir not in sys.path:
            sys.path.insert(0, connect_dir)
        
        import medical_ai_pb2
        import medical_ai_pb2_grpc
        
        _grpc_channel = grpc.insecure_channel(
            AI_SERVICE_HOST,
            options=[
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.http2.max_pings_without_data", 0),
            ],
        )
        grpc.channel_ready_future(_grpc_channel).result(timeout=GRPC_CONNECT_TIMEOUT)
        _grpc_stub = medical_ai_pb2_grpc.PostSurgeryFollowUpServiceStub(_grpc_channel)
        _medical_ai_pb2 = medical_ai_pb2
        return _grpc_stub, _grpc_channel, _medical_ai_pb2
    except Exception as e:
        print(f"[ERROR] 连接 AI 服务失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


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

    try:
        await AIChatMessage.create(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        session = await AIChatSession.filter(id=request.session_id).first()
        if session:
            session.message_count += 1
            await session.save()
    except Exception as e:
        print(f"[WARNING] 保存用户消息失败: {e}")

    async def event_generator():
        full_content = ""
        try:
            def request_generator():
                yield pb2.ChatRequest(
                    session_id=request.session_id,
                    message=request.message,
                    is_end=request.is_end
                )

            for response in stub.Chat(request_generator(), timeout=GRPC_CHAT_TIMEOUT):
                chunk = {
                    "content": response.content,
                    "is_final": response.is_final,
                    "reference": response.reference
                }
                full_content += response.content
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                if response.is_final:
                    break

            if full_content:
                try:
                    await AIChatMessage.create(
                        session_id=request.session_id,
                        role="ai",
                        content=full_content
                    )
                    session = await AIChatSession.filter(id=request.session_id).first()
                    if session:
                        session.message_count += 1
                        await session.save()
                except Exception as e:
                    print(f"[WARNING] 保存AI消息失败: {e}")

        except grpc.RpcError as e:
            error_chunk = {"error": f"gRPC调用失败: {e.details()}"}
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_chunk = {"error": f"发送消息失败: {str(e)}"}
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
        
        return success_response(data={
            "report": report,
            "status": response.status
        })
        
    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"结束会话失败: {str(e)}")


@router.post("/history")
async def get_history(request: GetHistoryRequest):
    """获取对话历史"""
    stub, channel, pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        response = stub.GetSessionHistory(
            pb2.GetSessionHistoryRequest(session_id=request.session_id),
            timeout=GRPC_DEFAULT_TIMEOUT
        )
        
        messages = []
        for msg in response.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            })
        
        return success_response(data={
            "session_id": response.session_id,
            "surgery_type": response.surgery_type,
            "messages": messages,
            "created_at": response.created_at,
            "ended_at": response.ended_at,
            "status": response.status
        })
        
    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"获取历史失败: {str(e)}")


@router.get("/sessions")
async def get_user_sessions(
    current_user: dict = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20
):
    """获取用户的AI问诊会话列表"""
    user_id = current_user["user_id"]
    
    try:
        sessions = await AIChatSession.filter(
            user_id=user_id
        ).order_by("-updated_at").offset((page - 1) * page_size).limit(page_size)
        
        total = await AIChatSession.filter(user_id=user_id).count()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "id": session.id,
                "title": session.title,
                "surgery_type": session.surgery_type,
                "message_count": session.message_count,
                "status": session.status,
                "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S") if session.created_at else None,
                "updated_at": session.updated_at.strftime("%Y-%m-%d %H:%M:%S") if session.updated_at else None
            })
        
        return success_response(data={
            "sessions": session_list,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        print(f"[ERROR] 获取会话列表失败: {e}")
        return error_response(code="50006", msg=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取会话详情（包含所有消息）"""
    user_id = current_user["user_id"]
    
    try:
        session = await AIChatSession.filter(
            id=session_id,
            user_id=user_id
        ).first()
        
        if not session:
            return error_response(code="50007", msg="会话不存在")
        
        messages = await AIChatMessage.filter(
            session_id=session_id
        ).order_by("created_at").all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "time": msg.created_at.strftime("%H:%M") if msg.created_at else ""
            })
        
        return success_response(data={
            "session": {
                "id": session.id,
                "title": session.title,
                "surgery_type": session.surgery_type,
                "message_count": session.message_count,
                "status": session.status,
                "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S") if session.created_at else None
            },
            "messages": message_list
        })
    except Exception as e:
        print(f"[ERROR] 获取会话详情失败: {e}")
        return error_response(code="50008", msg=f"获取会话详情失败: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除会话"""
    user_id = current_user["user_id"]
    
    try:
        session = await AIChatSession.filter(
            id=session_id,
            user_id=user_id
        ).first()
        
        if not session:
            return error_response(code="50007", msg="会话不存在")
        
        await AIChatMessage.filter(session_id=session_id).delete()
        await session.delete()
        
        return success_response(msg="删除成功")
    except Exception as e:
        print(f"[ERROR] 删除会话失败: {e}")
        return error_response(code="50009", msg=f"删除会话失败: {str(e)}")
