from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import json
import grpc
import os
from app.utils import success_response, error_response

router = APIRouter(tags=["伤口分析模块"])

# gRPC 客户端配置（与 server.py 保持一致）
AI_SERVICE_HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1:50053")
GRPC_CONNECT_TIMEOUT = float(os.getenv("AI_GRPC_CONNECT_TIMEOUT", "3"))
GRPC_DEFAULT_TIMEOUT = float(os.getenv("AI_GRPC_DEFAULT_TIMEOUT", "25"))
_grpc_stub = None
_grpc_channel = None
_medical_ai_pb2 = None


class AnalyzeWoundImageRequest(BaseModel):
    session_id: str
    image_base64: str


class ProcessPatientAnswersRequest(BaseModel):
    session_id: str
    answers: dict


def get_grpc_stub():
    """获取 gRPC 客户端"""
    global _grpc_stub, _grpc_channel, _medical_ai_pb2
    try:
        if _grpc_stub and _grpc_channel and _medical_ai_pb2:
            return _grpc_stub, _grpc_channel, _medical_ai_pb2

        import sys
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
        return None, None, None


@router.post("/analyze")
async def analyze_wound_image(request: AnalyzeWoundImageRequest):
    """分析伤口图片
    
    接收前端上传的图片Base64数据，调用AI服务分析伤口，
    返回确认问题列表给患者回答。
    """
    stub, channel, medical_ai_pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        # 调用 gRPC 接口
        response = stub.AnalyzeWoundImage(
            medical_ai_pb2.AnalyzeWoundImageRequest(
                session_id=request.session_id,
                image_base64=request.image_base64
            ),
            timeout=GRPC_DEFAULT_TIMEOUT
        )
        
        if not response.success:
            return error_response(code="50002", msg=response.error or "图片分析失败")
        
        # 构建返回数据
        questions = []
        for q in response.questions:
            questions.append({
                "question": q.question,
                "reason": q.reason
            })
        
        preliminary = {
            "suspected_body_part": response.preliminary_findings.suspected_body_part,
            "suspected_body_part_confidence": response.preliminary_findings.suspected_body_part_confidence,
            "visible_features": list(response.preliminary_findings.visible_features),
            "uncertain_items": list(response.preliminary_findings.uncertain_items)
        }
        
        result = {
            "success": True,
            "need_confirmation": response.need_confirmation,
            "image_valid": response.image_valid,
            "invalid_reason": response.invalid_reason,
            "image_url": response.image_url,
            "questions": questions,
            "preliminary_findings": preliminary,
            "created_at": response.created_at
        }
        
        return success_response(data=result)
        
    except grpc.RpcError as e:
        return error_response(code="50003", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50004", msg=f"处理失败: {str(e)}")


@router.post("/answers")
async def process_patient_answers(request: ProcessPatientAnswersRequest):
    """处理患者回答
    
    接收患者对确认问题的回答，结合之前的图片分析结果，
    生成最终的伤口评估并融合到病历中。
    """
    stub, channel, medical_ai_pb2 = get_grpc_stub()
    
    if not stub:
        return error_response(code="50001", msg="AI服务连接失败")
    
    try:
        # 调用 gRPC 接口
        response = stub.ProcessPatientAnswers(
            medical_ai_pb2.ProcessPatientAnswersRequest(
                session_id=request.session_id,
                answers=request.answers
            ),
            timeout=GRPC_DEFAULT_TIMEOUT
        )
        
        if not response.success:
            return error_response(code="50005", msg=response.error or "处理失败")
        
        # 解析最终报告 JSON
        final_report = {}
        if response.final_report_json:
            try:
                final_report = json.loads(response.final_report_json)
            except json.JSONDecodeError:
                pass
        
        # 构建返回数据
        wound_assessment = {
            "confirmed_body_part": response.wound_assessment.confirmed_body_part,
            "wound_assessment": {
                "location": response.wound_assessment.wound_assessment.location,
                "onset_time": response.wound_assessment.wound_assessment.onset_time,
                "pain_score": response.wound_assessment.wound_assessment.pain_score,
                "pain_description": response.wound_assessment.wound_assessment.pain_description,
                "appearance": response.wound_assessment.wound_assessment.appearance,
                "exudate": response.wound_assessment.wound_assessment.exudate,
                "surrounding_skin": response.wound_assessment.wound_assessment.surrounding_skin,
                "inflammation_signs": list(response.wound_assessment.wound_assessment.inflammation_signs)
            },
            "healing_status": response.wound_assessment.healing_status,
            "risk_alerts": list(response.wound_assessment.risk_alerts),
            "recommendation": response.wound_assessment.recommendation,
            "missing_info": response.wound_assessment.missing_info,
            "suggest_next_question": response.wound_assessment.suggest_next_question
        }
        
        image_info = {
            "url": response.image_info.url,
            "upload_time": response.image_info.upload_time,
            "image_type": response.image_info.image_type,
            "analysis": {
                "confirmed_body_part": response.image_info.analysis.confirmed_body_part,
                "healing_status": response.image_info.analysis.healing_status,
                "risk_alerts": list(response.image_info.analysis.risk_alerts)
            }
        }
        
        result = {
            "success": True,
            "wound_assessment": wound_assessment,
            "image_info": image_info,
            "final_report": final_report
        }
        
        return success_response(data=result)
        
    except grpc.RpcError as e:
        return error_response(code="50006", msg=f"gRPC调用失败: {e.details()}")
    except Exception as e:
        return error_response(code="50007", msg=f"处理失败: {str(e)}")


@router.post("/upload")
async def upload_wound_image(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """上传伤口图片
    
    直接接收文件上传，转换为Base64后再调用分析接口。
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 检查文件大小 (10MB)
        max_size = 10 * 1024 * 1024
        if len(content) > max_size:
            return error_response(code="40001", msg=f"文件大小超过限制 ({len(content)} > {max_size})")
        
        # 检查文件类型
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            return error_response(code="40002", msg="不支持的文件类型，请上传 JPG/PNG/GIF 图片")
        
        # 转换为 Base64
        image_base64 = f"data:{file.content_type};base64,{base64.b64encode(content).decode('utf-8')}"
        
        # 调用分析接口
        analyze_request = AnalyzeWoundImageRequest(
            session_id=session_id,
            image_base64=image_base64
        )
        
        return await analyze_wound_image(analyze_request)
        
    except Exception as e:
        return error_response(code="40003", msg=f"文件处理失败: {str(e)}")
