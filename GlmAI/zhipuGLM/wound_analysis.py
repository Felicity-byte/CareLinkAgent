import json
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from zhipuai import ZhipuAI

from image_storage import get_image_storage, ImageStorage
import prompts.prompts as prompts
import session_manager as session_mgr


class WoundAnalysisService:
    """伤口分析服务"""

    def __init__(self, api_key_4v: str = None):
        if api_key_4v is None:
            api_key_4v = os.environ.get("GLM_4V_API_KEY") or os.environ.get("GLM_API_KEY")

        if not api_key_4v:
            raise ValueError("未配置 glm-4v-flash API Key (GLM_4V_API_KEY 或 GLM_API_KEY)")

        self.client_4v = ZhipuAI(api_key=api_key_4v)
        self.image_storage: ImageStorage = get_image_storage()

    def process_patient_image(self, session_id: str, image_base64: str) -> Dict[str, Any]:
        """处理患者上传的图片"""
        session = session_mgr.session_manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "会话不存在或已过期",
                "need_confirmation": False
            }

        try:
            image_info = self.image_storage.save_image(image_base64, session_id, "wound")
        except Exception as e:
            return {
                "success": False,
                "error": f"保存图片失败: {str(e)}",
                "need_confirmation": False
            }

        session.add_uploaded_image(image_info)

        analysis_result = self._analyze_image_with_retry(image_base64)

        if not analysis_result.get("success"):
            return {
                "success": False,
                "error": analysis_result.get("error", "图片分析失败"),
                "need_confirmation": False,
                "image_url": image_info["url"]
            }

        analysis_data = analysis_result.get("data", {})

        if not analysis_data.get("image_valid", True):
            return {
                "success": True,
                "need_confirmation": False,
                "image_valid": False,
                "invalid_reason": analysis_data.get("invalid_reason", "无法识别该图片"),
                "image_url": image_info["url"]
            }

        pending_data = {
            "session_id": session_id,
            "image_info": image_info,
            "preliminary_analysis": analysis_data.get("preliminary_analysis", {}),
            "questions": analysis_data.get("questions_to_confirm", []),
            "created_at": datetime.now().isoformat()
        }

        session.set_pending_image_analysis(pending_data)

        return {
            "success": True,
            "need_confirmation": True,
            "image_valid": True,
            "image_url": image_info["url"],
            "questions": analysis_data.get("questions_to_confirm", []),
            "preliminary_findings": analysis_data.get("preliminary_analysis", {}),
            "created_at": pending_data["created_at"]
        }

    def process_patient_answers(self, session_id: str, user_answers: Dict[str, str]) -> Dict[str, Any]:
        """处理患者的确认回答"""
        session = session_mgr.session_manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "会话不存在或已过期"
            }

        pending = session.get_pending_image_analysis()
        if not pending:
            return {
                "success": False,
                "error": "未找到待处理的图片分析，请先上传图片"
            }

        preliminary_analysis = pending.get("preliminary_analysis", {})
        image_info = pending.get("image_info", {})

        formatted_answers = self._format_user_answers(
            pending.get("questions", []),
            user_answers
        )

        assessment_result = self._generate_assessment_with_retry(
            preliminary_analysis,
            formatted_answers
        )

        if not assessment_result.get("success"):
            return {
                "success": False,
                "error": assessment_result.get("error", "综合评估失败")
            }

        wound_assessment = assessment_result.get("data", {})

        original_report = session.get_final_report()

        merge_result = self._merge_to_report_with_retry(
            original_report,
            wound_assessment,
            image_info
        )

        if not merge_result.get("success"):
            final_report = {
                **(original_report if original_report else {}),
                "images": [{
                    "url": image_info.get("url", ""),
                    "upload_time": image_info.get("upload_time", ""),
                    "image_type": "伤口照片",
                    "analysis": {
                        "confirmed_body_part": wound_assessment.get("confirmed_body_part", ""),
                        "healing_status": wound_assessment.get("healing_status", ""),
                        "risk_alerts": wound_assessment.get("risk_alerts", [])
                    }
                }],
                "wound_assessment": wound_assessment
            }
        else:
            final_report = merge_result.get("data")

        if original_report and "images" in original_report:
            final_report["images"] = original_report["images"] + final_report.get("images", [])

        session.set_final_report(final_report)
        session.clear_pending_image_analysis()

        return {
            "success": True,
            "final_report": final_report,
            "wound_assessment": wound_assessment,
            "image_info": image_info
        }

    def _format_user_answers(self, questions: List[Dict], user_answers: Dict[str, str]) -> str:
        """将用户回答格式化为易读的文本"""
        if not questions:
            formatted_parts = []
            for key, value in user_answers.items():
                if key.isdigit():
                    formatted_parts.append(f"- 问题{int(key)+1}的答案: {value}")
                else:
                    formatted_parts.append(f"- {key}: {value}")
            return "\n".join(formatted_parts) if formatted_parts else json.dumps(user_answers, ensure_ascii=False)

        formatted_parts = []
        for i, q in enumerate(questions):
            question_text = q.get("question", "")
            answer = user_answers.get(str(i), user_answers.get(i, "未回答"))
            formatted_parts.append(f"问题{i+1}: {question_text}\n回答: {answer}")

        return "\n\n".join(formatted_parts)
    
    def _analyze_image_with_retry(self, image_base64: str, max_retries: int = 3) -> Dict[str, Any]:
        """调用 glm-4v-flash 分析图片（带重试）"""
        last_error = None
        
        for retry in range(max_retries):
            try:
                prompt = prompts.WOUND_IMAGE_ANALYSIS_PROMPT
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64.split(',')[1] if ',' in image_base64 else image_base64}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                
                response = self.client_4v.chat.completions.create(
                    model="glm-4v-flash",
                    messages=messages,
                    temperature=0.0,
                    max_tokens=2000,
                    stream=False,
                    timeout=30
                )
                
                result_text = response.choices[0].message.content
                
                # 解析JSON响应
                result = self._parse_json_response(result_text)
                
                if result:
                    return {"success": True, "data": result}
                    
            except Exception as e:
                last_error = e
                print(f"[WARNING] 图片分析第{retry + 1}次失败: {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(1.0)
        
        return {"success": False, "error": f"图片分析失败: {str(last_error)}"}
    
    def _generate_assessment_with_retry(self, preliminary_analysis: Dict, user_answers: Dict, max_retries: int = 3) -> Dict[str, Any]:
        """生成综合评估（带重试）"""
        last_error = None
        
        for retry in range(max_retries):
            try:
                prompt = prompts.WOUND_ASSESSMENT_PROMPT.format(
                    preliminary_analysis=json.dumps(preliminary_analysis, ensure_ascii=False, indent=2),
                    patient_answers=json.dumps(user_answers, ensure_ascii=False, indent=2)
                )
                
                response = self.client_4v.chat.completions.create(
                    model="glm-4-flash",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2000,
                    stream=False,
                    timeout=30
                )
                
                result_text = response.choices[0].message.content
                result = self._parse_json_response(result_text)
                
                if result:
                    return {"success": True, "data": result}
                    
            except Exception as e:
                last_error = e
                print(f"[WARNING] 综合评估第{retry + 1}次失败: {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(1.0)
        
        return {"success": False, "error": f"综合评估失败: {str(last_error)}"}
    
    def _merge_to_report_with_retry(self, original_report: Dict, wound_assessment: Dict, image_info: Dict, max_retries: int = 3) -> Dict[str, Any]:
        """融合到结构化病历（带重试）"""
        last_error = None
        
        for retry in range(max_retries):
            try:
                prompt = prompts.WOUND_MERGE_REPORT_PROMPT.format(
                    original_report=json.dumps(original_report or {}, ensure_ascii=False, indent=2),
                    wound_assessment=json.dumps(wound_assessment, ensure_ascii=False, indent=2),
                    image_url=image_info.get("url", "")
                )
                
                response = self.client_4v.chat.completions.create(
                    model="glm-4-flash",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=3000,
                    stream=False,
                    timeout=30
                )
                
                result_text = response.choices[0].message.content
                result = self._parse_json_response(result_text)
                
                if result:
                    return {"success": True, "data": result}
                    
            except Exception as e:
                last_error = e
                print(f"[WARNING] 病历融合第{retry + 1}次失败: {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(1.0)
        
        return {"success": False, "error": f"病历融合失败: {str(last_error)}"}
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """解析 AI 返回的 JSON 响应"""
        if not text:
            return None
        
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 ```json ... ``` 块
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取 { ... } 对象
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        print(f"[ERROR] 无法解析JSON响应: {text[:200]}...")
        return None
    
    def cleanup_pending_analysis(self, session_id: str):
        """清理指定会话的待确认数据"""
        session = session_mgr.session_manager.get_session(session_id)
        if session:
            session.clear_pending_image_analysis()

    def has_pending_analysis(self, session_id: str) -> bool:
        """检查是否有待确认的图片分析"""
        session = session_mgr.session_manager.get_session(session_id)
        return session is not None and session.get_pending_image_analysis() is not None


# 全局实例
_global_wound_service: Optional[WoundAnalysisService] = None


def get_wound_analysis_service() -> WoundAnalysisService:
    """获取全局伤口分析服务实例"""
    global _global_wound_service
    if _global_wound_service is None:
        _global_wound_service = WoundAnalysisService()
    return _global_wound_service


def initialize_wound_service(api_key_4v: str = None):
    """初始化伤口分析服务"""
    global _global_wound_service
    _global_wound_service = WoundAnalysisService(api_key_4v=api_key_4v)
    print("[OK] 伤口分析服务初始化完成")
