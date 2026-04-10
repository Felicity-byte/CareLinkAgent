"""AI导诊服务路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import grpc
import os
import sys
from app.utils import success_response, error_response
from app.models.surgery_record import SurgeryRecord
from tortoise import Tortoise
from database import TORTOISE_ORM

router = APIRouter(tags=["AI导诊服务"])

AI_SERVICE_HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1:50053")


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
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        project_root = os.path.dirname(backend_dir)
        connect_dir = os.path.join(project_root, "GlmAI", "connect")
        if connect_dir not in sys.path:
            sys.path.insert(0, connect_dir)
        
        import medical_ai_pb2
        import medical_ai_pb2_grpc
        
        channel = grpc.insecure_channel(AI_SERVICE_HOST)
        stub = medical_ai_pb2_grpc.PostSurgeryFollowUpServiceStub(channel)
        return stub, channel, medical_ai_pb2
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
            await Tortoise.init(config=TORTOISE_ORM)
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
        finally:
            try:
                await Tortoise.close_connections()
            except:
                pass
    
    try:
        response = stub.CreateSession(
            pb2.CreateSessionRequest(
                patient_id=request.patient_id,
                patient_name=request.patient_name,
                surgery_date=surgery_date or "",
                surgery_type=surgery_name or ""
            )
        )
        
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
    finally:
        if channel:
            channel.close()


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
        for response in stub.Chat(request_generator()):
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
    finally:
        if channel:
            channel.close()


@router.post("/end-session")
async def end_session(request: EndSessionRequest):
    """结束导诊会话，获取病历报告"""
    stub, channel, pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        response = stub.EndSession(
            pb2.EndSessionRequest(session_id=request.session_id)
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
    finally:
        if channel:
            channel.close()


@router.post("/history")
async def get_history(request: GetHistoryRequest):
    """获取对话历史"""
    stub, channel, pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        response = stub.GetSessionHistory(
            pb2.GetSessionHistoryRequest(session_id=request.session_id)
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
    finally:
        if channel:
            channel.close()
