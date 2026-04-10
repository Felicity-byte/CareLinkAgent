import sys
import os
import time

os.environ["PYTHONUNBUFFERED"] = "1"

if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleOutputCP(65001)
    kernel32.SetConsoleCP(65001)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

import grpc
from concurrent import futures
from dotenv import load_dotenv

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zhipuGLM"))

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)
print(f"--- 已加载环境变量文件: {env_path} ---")
print(f"--- GLM_API_KEY: {'已配置' if os.environ.get('GLM_API_KEY') else '未配置'} ---")

import connect.medical_ai_pb2 as medical_ai_pb2
import connect.medical_ai_pb2_grpc as medical_ai_grpc

from zhipuGLM import service as ai_service
from zhipuGLM import wound_analysis
import json


class PostSurgeryFollowUpServicer(medical_ai_grpc.PostSurgeryFollowUpServiceServicer):
    """术后随访 AI 服务实现"""
    
    def CreateSession(self, request, context):
        """创建会话"""
        try:
            result = ai_service.create_session(
                patient_id=request.patient_id,
                patient_name=request.patient_name,
                surgery_date=request.surgery_date,
                surgery_type=request.surgery_type
            )
            
            return medical_ai_pb2.CreateSessionResponse(
                session_id=result["session_id"],
                created_at=result["created_at"],
                welcome_message=result["welcome_message"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return medical_ai_pb2.CreateSessionResponse()
    
    def Chat(self, request_iterator, context):
        """流式对话"""
        session_id = None
        
        for request in request_iterator:
            if not session_id:
                session_id = request.session_id
            
            for response_chunk in ai_service.chat_stream(
                session_id=session_id,
                message=request.message,
                is_end=request.is_end
            ):
                yield medical_ai_pb2.ChatResponse(
                    content=response_chunk["content"],
                    is_final=response_chunk["is_final"],
                    reference=response_chunk["reference"]
                )
    
    def EndSession(self, request, context):
        """结束会话，返回病历"""
        try:
            result = ai_service.end_session(request.session_id)
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("会话不存在")
                return medical_ai_pb2.EndSessionResponse()
            
            report_data = result.get("report", {})
            
            # 构建 MedicalReport
            patient_info = medical_ai_pb2.PatientInfo(
                name="",
                gender="",
                age=0,
                surgery_type="",
                surgery_date="",
                doctor_name=""
            )
            
            surgery_status = medical_ai_pb2.PostSurgeryStatus(
                wound_healing="",
                temperature="",
                appetite="",
                activity=""
            )
            
            past_history = medical_ai_pb2.PastHistory(
                allergy="",
                chronic_disease="",
                medication=""
            )
            
            ai_analysis = medical_ai_pb2.AIAnalysis(
                health_advice=report_data.get("report_text", "")[:500] if report_data else "",
                alert_flag=False,
                alert_reason=""
            )
            
            doctor_advice = medical_ai_pb2.DoctorAdvice(
                medical_advice="",
                followup_items="",
                next_visit_date="",
                need_followup=False
            )
            
            session_info = medical_ai_pb2.SessionInfo(
                conversation_rounds=0,
                submitted_at=""
            )
            
            medical_report = medical_ai_pb2.MedicalReport(
                patient=patient_info,
                chief_complaint="术后随访报告",
                present_illness=report_data.get("report_text", ""),
                surgery_status=surgery_status,
                past_history=past_history,
                ai_analysis=ai_analysis,
                doctor_advice=doctor_advice,
                session_info=session_info
            )
            
            return medical_ai_pb2.EndSessionResponse(
                report=medical_report,
                status=result.get("status", "COMPLETED")
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return medical_ai_pb2.EndSessionResponse()
    
    def GetSessionHistory(self, request, context):
        """获取对话历史"""
        try:
            history = ai_service.get_session_history(request.session_id)
            
            if not history:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("会话不存在")
                return medical_ai_pb2.GetSessionHistoryResponse()
            
            # 构建消息列表
            messages = []
            for msg in history.get("messages", []):
                messages.append(medical_ai_pb2.ChatMessage(
                    role=msg.get("role", ""),
                    content=msg.get("content", ""),
                    timestamp=msg.get("timestamp", "")
                ))
            
            return medical_ai_pb2.GetSessionHistoryResponse(
                session_id=history["session_id"],
                surgery_type=history.get("surgery_type", ""),
                messages=messages,
                created_at=history.get("created_at", ""),
                ended_at=history.get("ended_at", ""),
                status=history.get("status", "")
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return medical_ai_pb2.GetSessionHistoryResponse()
    
    def AnalyzeWoundImage(self, request, context):
        """分析伤口图片"""
        try:
            wound_service = wound_analysis.get_wound_analysis_service()
            
            result = wound_service.process_patient_image(
                session_id=request.session_id,
                image_base64=request.image_base64
            )
            
            if not result.get("success"):
                return medical_ai_pb2.AnalyzeWoundImageResponse(
                    success=False,
                    error=result.get("error", "分析失败"),
                    need_confirmation=False
                )
            
            # 构建初步发现
            preliminary = result.get("preliminary_findings", {})
            preliminary_msg = medical_ai_pb2.PreliminaryAnalysis(
                suspected_body_part=preliminary.get("suspected_body_part", ""),
                suspected_body_part_confidence=preliminary.get("suspected_body_part_confidence", "低"),
                visible_features=preliminary.get("visible_features", []),
                uncertain_items=preliminary.get("uncertain_items", [])
            )
            
            # 构建确认问题列表
            questions = []
            for q in result.get("questions", []):
                questions.append(medical_ai_pb2.ConfirmQuestion(
                    question=q.get("question", ""),
                    reason=q.get("reason", "")
                ))
            
            return medical_ai_pb2.AnalyzeWoundImageResponse(
                success=True,
                need_confirmation=result.get("need_confirmation", False),
                image_valid=result.get("image_valid", True),
                invalid_reason=result.get("invalid_reason", ""),
                image_url=result.get("image_url", ""),
                questions=questions,
                preliminary_findings=preliminary_msg,
                created_at=result.get("created_at", "")
            )
            
        except Exception as e:
            print(f"[ERROR] AnalyzeWoundImage 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return medical_ai_pb2.AnalyzeWoundImageResponse(
                success=False,
                error=str(e),
                need_confirmation=False
            )
    
    def ProcessPatientAnswers(self, request, context):
        """处理患者回答"""
        try:
            wound_service = wound_analysis.get_wound_analysis_service()
            
            # 转换 map 为 dict
            user_answers = dict(request.answers)
            
            result = wound_service.process_patient_answers(
                session_id=request.session_id,
                user_answers=user_answers
            )
            
            if not result.get("success"):
                return medical_ai_pb2.ProcessPatientAnswersResponse(
                    success=False,
                    error=result.get("error", "处理失败")
                )
            
            # 构建伤口评估结果
            wa = result.get("wound_assessment", {})
            wound_detail = wa.get("wound_assessment", {})
            
            wound_detail_msg = medical_ai_pb2.WoundAssessmentDetail(
                location=wound_detail.get("location", ""),
                onset_time=wound_detail.get("onset_time", ""),
                pain_score=wound_detail.get("pain_score", ""),
                pain_description=wound_detail.get("pain_description", ""),
                appearance=wound_detail.get("appearance", ""),
                exudate=wound_detail.get("exudate", "无法判断"),
                surrounding_skin=wound_detail.get("surrounding_skin", "正常"),
                inflammation_signs=wound_detail.get("inflammation_signs", [])
            )
            
            wound_result = medical_ai_pb2.WoundAssessmentResult(
                confirmed_body_part=wa.get("confirmed_body_part", ""),
                wound_assessment=wound_detail_msg,
                healing_status=wa.get("healing_status", "无法判断"),
                risk_alerts=wa.get("risk_alerts", []),
                recommendation=wa.get("recommendation", ""),
                missing_info=wa.get("missing_info", ""),
                suggest_next_question=wa.get("suggest_next_question", "")
            )
            
            # 构建图片信息
            img_info = result.get("image_info", {})
            analysis_summary = img_info.get("analysis", {})
            
            analysis_msg = medical_ai_pb2.ImageAnalysisSummary(
                confirmed_body_part=analysis_summary.get("confirmed_body_part", ""),
                healing_status=analysis_summary.get("healing_status", ""),
                risk_alerts=analysis_summary.get("risk_alerts", [])
            )
            
            image_msg = medical_ai_pb2.ImageInfo(
                url=img_info.get("url", ""),
                upload_time=img_info.get("upload_time", ""),
                image_type=img_info.get("image_type", "伤口照片"),
                analysis=analysis_msg
            )
            
            # 序列化最终报告为 JSON
            final_report_json = json.dumps(result.get("final_report", {}), ensure_ascii=False)
            
            return medical_ai_pb2.ProcessPatientAnswersResponse(
                success=True,
                wound_assessment=wound_result,
                image_info=image_msg,
                final_report_json=final_report_json
            )
            
        except Exception as e:
            print(f"[ERROR] ProcessPatientAnswers 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return medical_ai_pb2.ProcessPatientAnswersResponse(
                success=False,
                error=str(e)
            )


import os
import signal
import subprocess
import time


def kill_process_on_port(port: int):
    """终止占用指定端口的进程"""
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['powershell', '-Command', 
                 f'Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess'],
                capture_output=True,
                text=True,
                timeout=10
            )
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                pid = pid.strip()
                if pid and pid.isdigit():
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"--- 已终止占用端口 {port} 的进程 (PID: {pid}) ---")
                        time.sleep(1)
                    except (ProcessLookupError, ValueError, PermissionError):
                        pass
    except subprocess.TimeoutExpired:
        print(f"--- 清理端口 {port} 超时，跳过 ---")
    except Exception as e:
        print(f"--- 清理端口时出错: {e} ---")


def serve():
    """启动 gRPC 服务器"""
    port = 50053
    health_port = 50054
    
    print("\n" + "="*60)
    print("  术后随访AI服务启动器")
    print("="*60)
    
    # Step 1: 清理端口
    print("\n[Step 1/3] 检查端口占用情况...")
    kill_process_on_port(port)
    print(f"  [OK] 端口 {port} 已就绪")
    
    # Step 2: 初始化AI服务
    print("\n[Step 2/3] 初始化AI服务组件...")
    ai_service.initialize_service()
    
    # Step 3: 启动gRPC服务器
    print("\n[Step 3/3] 启动gRPC服务器...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    medical_ai_grpc.add_PostSurgeryFollowUpServiceServicer_to_server(
        PostSurgeryFollowUpServicer(), server
    )
    
    server.add_insecure_port(f"[::]:{port}")
    
    print(f"  [OK] gRPC服务器配置完成，端口: {port}")
    
    server.start()

    # 启动 HTTP 健康检查服务
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"AI-gRPC","port":50053}')
        def log_message(self, format, *args):
            pass

    try:
        health_server = HTTPServer(("0.0.0.0", health_port), HealthHandler)
        health_thread = threading.Thread(target=health_server.serve_forever, daemon=True)
        health_thread.start()
        print(f"  [OK] 健康检查服务已启动: http://localhost:{health_port}")
    except Exception as e:
        print(f"  [WARNING] 健康检查服务启动失败: {e}")
    
    print("\n" + "="*60)
    print(f"  AI服务启动成功!")
    print(f"  gRPC端口: {port}")
    print(f"  健康检查: http://localhost:{health_port}")
    print("  按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("  正在关闭AI服务...")
        print("="*60)
        server.stop(grace=5)
        print("\n[OK] AI服务已安全关闭")


if __name__ == "__main__":
    serve()
