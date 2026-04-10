import sys
import os
import time
import threading
from typing import Generator, Optional, List, Dict
from datetime import datetime

from zhipuai import ZhipuAI

sys.path.insert(0, os.path.dirname(__file__))

import config.config as config
import prompts.prompts as prompts
import rag.rag_core as rag_core
import session_manager as session_mgr
from knowledge.zhipu_knowledge import zhipu_knowledge, initialize_zhipu_knowledge

GLOBAL_CLIENT: Optional[ZhipuAI] = None
GLOBAL_POST_SURGERY_RAG = None
GLOBAL_ZHIPU_KNOWLEDGE = None
_rag_loaded = False
_rag_loading = False
_rag_lock = threading.Lock()

MAX_RETRIES = 3
RETRY_DELAY = 1.0


def _background_load_rag():
    """后台线程：异步加载RAG向量数据库"""
    global GLOBAL_POST_SURGERY_RAG, _rag_loaded, _rag_loading
    
    print("--- [BACKGROUND] 开始后台加载RAG向量数据库 ---")
    start_time = datetime.now()
    
    try:
        GLOBAL_POST_SURGERY_RAG = rag_core.build_post_surgery_rag_index()
        load_duration = (datetime.now() - start_time).total_seconds()
        
        with _rag_lock:
            _rag_loaded = True
            _rag_loading = False
        
        if GLOBAL_POST_SURGERY_RAG:
            print(f"--- [OK] RAG向量数据库后台加载成功! 耗时: {load_duration:.2f}秒 ---")
        else:
            print(f"--- [WARNING] RAG向量数据库加载返回空结果 (耗时: {load_duration:.2f}秒) ---")
            
    except Exception as e:
        load_duration = (datetime.now() - start_time).total_seconds()
        with _rag_lock:
            _rag_loaded = True  # 标记为已尝试，避免重复尝试
            _rag_loading = False
        print(f"--- [ERROR] RAG向量数据库后台加载失败 (耗时: {load_duration:.2f}秒): {e} ---")
        import traceback
        traceback.print_exc()


def _init_zhipu_knowledge_with_timeout(timeout=30):
    """带超时的智谱知识库初始化"""
    result = [None]
    error = [None]
    
    def _worker():
        try:
            result[0] = initialize_zhipu_knowledge()
        except Exception as e:
            error[0] = e
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    
    if t.is_alive():
        print(f"  [WARNING] 智谱知识库初始化超时（{timeout}秒），跳过")
        return None
    
    if error[0]:
        print(f"  [WARNING] 智谱知识库初始化失败: {error[0]}")
        return None
    
    return result[0]


def initialize_service():
    """服务初始化函数"""
    global GLOBAL_CLIENT, GLOBAL_POST_SURGERY_RAG, GLOBAL_ZHIPU_KNOWLEDGE
    
    print("\n" + "="*60)
    print("  AI 服务启动流程")
    print("="*60)
    
    try:
        # Step 1: 初始化智谱客户端
        print("\n[Step 1/5] 正在初始化智谱AI客户端...")
        api_key = os.environ.get("GLM_API_KEY")
        if not api_key:
            print("  [WARNING] 未找到 GLM_API_KEY 环境变量")
            print("  [INFO] AI服务将以降级模式运行（仅基础功能可用）")
            GLOBAL_CLIENT = None
        else:
            GLOBAL_CLIENT = ZhipuAI(api_key=api_key)
            print("  [OK] 智谱AI客户端初始化成功")
        
        # Step 2: 启动后台加载本地 RAG（术后护理文档）
        print("\n[Step 2/5] 设置术后护理文档向量数据库（后台预加载）...")
        global GLOBAL_POST_SURGERY_RAG, _rag_loaded, _rag_loading
        GLOBAL_POST_SURGERY_RAG = None
        _rag_loaded = False
        _rag_loading = True
        
        # 启动后台线程预加载RAG
        rag_thread = threading.Thread(target=_background_load_rag, daemon=True, name="RAG-Loader")
        rag_thread.start()
        print("  [OK] 向量数据库正在后台加载（不影响服务器启动）")
        
        # Step 3: 初始化智谱知识库（带超时保护）
        print("\n[Step 3/5] 正在初始化智谱知识库...")
        GLOBAL_ZHIPU_KNOWLEDGE = _init_zhipu_knowledge_with_timeout(timeout=30)
        if GLOBAL_ZHIPU_KNOWLEDGE and GLOBAL_ZHIPU_KNOWLEDGE.is_available:
            print("  [OK] 智谱知识库初始化成功")
        else:
            print("  [WARNING] 智谱知识库不可用，将使用LLM自身知识")
        
        # Step 4: 初始化会话管理器
        print("\n[Step 4/5] 正在初始化会话管理器...")
        print("  [OK] 会话管理器就绪")
        
        # Step 5: 初始化伤口分析服务
        print("\n[Step 5/5] 正在初始化伤口分析服务...")
        try:
            from wound_analysis import initialize_wound_service
            # 优先使用 GLM_4V_API_KEY，否则使用 GLM_API_KEY
            api_key_4v = os.environ.get("GLM_4V_API_KEY") or os.environ.get("GLM_API_KEY")
            initialize_wound_service(api_key_4v=api_key_4v)
            print("  [OK] 伤口分析服务初始化完成")
        except Exception as e:
            print(f"  [WARNING] 伤口分析服务初始化失败: {e}")
            print("         图片分析功能将不可用")
        
        print("\n" + "="*60)
        print("  AI 服务初始化完成!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def hybrid_retrieve(query: str, surgery_type: str = None) -> tuple:
    """
    混合检索：本地 RAG + 智谱知识库 + LLM 自身知识
    
    Returns:
        (retrieved_context: str, source: str)
        source 可以是 "local_rag", "zhipu_knowledge", 或 "llm_only"
    """
    global GLOBAL_POST_SURGERY_RAG, _rag_loaded, _rag_loading
    
    # 1. 本地 RAG 检索（术后护理文档）- 智能等待机制
    if surgery_type:
        if _rag_loaded:
            # 情况A：已加载完成，直接使用
            pass
        elif _rag_loading:
            # 情况B：正在后台加载中，智能等待（最多10秒）
            print("--- [WAIT] RAG向量数据库正在后台加载，等待完成... ---")
            wait_start = datetime.now()
            max_wait_seconds = 10
            
            while _rag_loading:
                elapsed = (datetime.now() - wait_start).total_seconds()
                if elapsed > max_wait_seconds:
                    print(f"--- [TIMEOUT] 等待RAG加载超时 ({max_wait_seconds}秒)，跳过本地检索 ---")
                    break
                time.sleep(0.1)  # 每100ms检查一次
            
            if not GLOBAL_POST_SURGERY_RAG:
                print("--- [INFO] RAG未就绪，使用其他知识源 ---")
        else:
            # 情况C：未加载且不在加载中（可能之前加载失败），尝试重新加载
            print("--- [RETRY] 尝试重新加载本地RAG向量数据库 ---")
            try:
                GLOBAL_POST_SURGERY_RAG = rag_core.build_post_surgery_rag_index()
                with _rag_lock:
                    _rag_loaded = True
                if GLOBAL_POST_SURGERY_RAG:
                    print("--- [OK] 本地RAG向量数据库重新加载成功 ---")
                else:
                    print("--- [WARNING] 本地RAG向量数据库重新加载失败 ---")
            except Exception as e:
                with _rag_lock:
                    _rag_loaded = True
                print(f"--- [ERROR] 本地RAG向量数据库重新加载失败: {e} ---")
    
    if GLOBAL_POST_SURGERY_RAG and surgery_type:
        local_docs = rag_core.retrieve_by_surgery_type(
            GLOBAL_POST_SURGERY_RAG, 
            query, 
            surgery_type=surgery_type,
            top_k=5
        )
        if local_docs:
            context = rag_core.format_retrieved_context(local_docs)
            return context, "local_rag"
    
    # 2. 智谱知识库检索（普通疾病文档）
    if GLOBAL_ZHIPU_KNOWLEDGE and GLOBAL_ZHIPU_KNOWLEDGE.is_available:
        zhipu_results = GLOBAL_ZHIPU_KNOWLEDGE.retrieve(query, top_k=5)
        if zhipu_results:
            context_parts = []
            for i, item in enumerate(zhipu_results[:5], 1):
                context_parts.append(f"[参考文档{i}]")
                context_parts.append(item.get("content", ""))
                context_parts.append("")
            return "\n".join(context_parts), "zhipu_knowledge"
    
    # 3. 无相关文档，由 LLM 自身知识生成
    return "", "llm_only"


def detect_emergency(message: str) -> tuple:
    """
    检测危急情况
    
    Returns:
        (is_emergency: bool, matched_keywords: list)
    """
    matched = []
    message_lower = message.lower()
    
    for keyword in prompts.EMERGENCY_KEYWORDS:
        if keyword in message_lower or keyword in message:
            matched.append(keyword)
    
    return len(matched) > 0, matched


def extract_symptoms(message: str) -> List[str]:
    """
    从消息中提取症状关键词
    
    Returns:
        症状列表
    """
    symptoms = []
    message_lower = message.lower()
    
    for category, keywords in prompts.SYMPTOM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower or keyword in message:
                if category not in symptoms:
                    symptoms.append(category)
                break
    
    return symptoms


def create_session(patient_id: str, patient_name: str, surgery_date: str, surgery_type: str = None) -> dict:
    """创建会话"""
    session = session_mgr.session_manager.create_session(
        patient_id, patient_name, surgery_date
    )
    
    if surgery_type:
        print(f"[DEBUG] 设置手术类型: {surgery_type}")
        session.set_surgery_type(surgery_type)
        print(f"[DEBUG] 会话状态: {session.status}, 手术类型: {session.surgery_type}")

    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "welcome_message": prompts.WELCOME_PROMPT
    }


def is_image_message(message: str) -> bool:
    """检测消息是否为 Base64 编码的图片"""
    if not message or not isinstance(message, str):
        return False
    if len(message) < 100:
        return False
    if message.startswith("data:image/") or message.startswith("iVBOR") or message.startswith("/9j/"):
        return True
    try:
        if "," in message:
            potential_base64 = message.split(",", 1)[1]
            if len(potential_base64) > 100:
                import base64
                base64.b64decode(potential_base64[:100])
                return True
    except Exception:
        pass
    return False


def get_image_base64_from_message(message: str) -> str:
    """从消息中提取 Base64 图片数据"""
    if "data:image/" in message and ";base64," in message:
        return message.split(";base64,", 1)[1]
    if "," in message:
        return message.split(",", 1)[1]
    return message


def process_wound_image(session_id: str, image_base64: str) -> dict:
    """处理伤口图片（独立于对话流）"""
    try:
        from wound_analysis import get_wound_analysis_service
        wound_service = get_wound_analysis_service()
        return wound_service.process_patient_image(session_id, image_base64)
    except Exception as e:
        print(f"[ERROR] 处理伤口图片失败: {str(e)}")
        return {
            "success": False,
            "error": f"处理伤口图片失败: {str(e)}",
            "need_confirmation": False
        }


def process_wound_answers(session_id: str, user_answers: dict) -> dict:
    """处理患者对伤口问题的回答"""
    try:
        from wound_analysis import get_wound_analysis_service
        wound_service = get_wound_analysis_service()
        return wound_service.process_patient_answers(session_id, user_answers)
    except Exception as e:
        print(f"[ERROR] 处理伤口回答失败: {str(e)}")
        return {
            "success": False,
            "error": f"处理伤口回答失败: {str(e)}"
        }


def chat_stream(session_id: str, message: str, is_end: bool = False, image_base64: str = None) -> Generator[dict, None, None]:
    """流式对话"""
    session = session_mgr.session_manager.get_session(session_id)
    if not session:
        yield {
            "content": "会话不存在或已过期，请重新开始",
            "is_final": True,
            "reference": ""
        }
        return

    if image_base64 and is_image_message(image_base64):
        wound_result = process_wound_image(session_id, image_base64)
        if wound_result.get("success"):
            if wound_result.get("need_confirmation"):
                questions = wound_result.get("questions", [])
                if questions:
                    question_texts = []
                    for i, q in enumerate(questions, 1):
                        question_texts.append(f"{i}. {q.get('question', '')}")
                    questions_prompt = "\n".join(question_texts)

                    response_text = f"我已经收到您上传的图片，正在分析中。\n\n根据图片分析，我需要向您确认几个问题：\n{questions_prompt}\n\n请您回答以上问题，帮助我更准确地评估您的伤口情况。"

                    session.add_message("patient", f"[上传了伤口图片]")
                    session.add_message("ai", response_text)

                    yield {
                        "content": response_text,
                        "is_final": False,
                        "reference": "",
                        "wound_pending": True,
                        "image_url": wound_result.get("image_url", "")
                    }

                    yield {
                        "content": "",
                        "is_final": True,
                        "reference": ""
                    }
                    return
            else:
                response_text = "感谢您上传图片。根据分析结果：\n\n" + wound_result.get("invalid_reason", "无法识别该图片")

                session.add_message("patient", f"[上传了伤口图片: {wound_result.get('invalid_reason', '无效图片')}]")
                session.add_message("ai", response_text)

                yield {
                    "content": response_text,
                    "is_final": True,
                    "reference": "",
                    "wound_invalid": True,
                    "invalid_reason": wound_result.get("invalid_reason", "")
                }
                return
        else:
            error_msg = wound_result.get("error", "图片处理失败")
            yield {
                "content": f"图片处理失败：{error_msg}",
                "is_final": True,
                "reference": "",
                "error": error_msg
            }
            return

    session.add_message("patient", message)
    
    print(f"[DEBUG] 会话状态: {session.status}, 手术类型: {session.surgery_type}")

    if session.status == session_mgr.SessionStatus.WAITING_SURGERY:
        surgery_type = extract_surgery_type(message)
        if surgery_type:
            session.set_surgery_type(surgery_type)

            response_text = prompts.SURGERY_CONFIRMED_PROMPT.format(
                SurgeryType=surgery_type
            )

            session.add_message("ai", response_text)

            yield {
                "content": response_text,
                "is_final": False,
                "reference": ""
            }
        else:
            response_text = "抱歉，我没有识别出您说的手术类型。请告诉我您做的是什么手术？例如：阑尾切除手术、胆囊切除术等。"

            session.add_message("ai", response_text)

            yield {
                "content": response_text,
                "is_final": False,
                "reference": ""
            }

        yield {
            "content": "",
            "is_final": True,
            "reference": ""
        }
        return

    if session.status == session_mgr.SessionStatus.WAITING_SURGERY_CONFIRM:
        if is_surgery_confirmed(message):
            session.confirm_surgery()
            
            response_text = prompts.SURGERY_CONFIRMED_PROMPT.format(
                SurgeryType=session.surgery_type
            )
            
            session.add_message("ai", response_text)
            
            yield {
                "content": response_text,
                "is_final": False,
                "reference": ""
            }
        else:
            response_text = "好的，请告诉我您实际做的是什么手术？例如：阑尾切除手术、胆囊切除术等。"
            session.status = session_mgr.SessionStatus.WAITING_SURGERY
            session.surgery_type = None
            
            session.add_message("ai", response_text)
            
            yield {
                "content": response_text,
                "is_final": False,
                "reference": ""
            }
        
        yield {
            "content": "",
            "is_final": True,
            "reference": ""
        }
        return

    if is_end or should_end_conversation(session):
        yield from end_chat_stream(session)
        return

    yield from normal_chat_stream(session, message)


def extract_surgery_type(text: str) -> Optional[str]:
    """从文本中提取手术类型"""
    common_surgeries = [
        "阑尾切除", "胆囊切除", "甲状腺切除", "乳腺手术",
        "疝气修补", "子宫切除", "剖宫产", "关节置换",
        "心脏搭桥", "骨折固定", "痔疮手术", "鼻窦手术"
    ]
    
    text_lower = text.lower()
    for surgery in common_surgeries:
        if surgery in text or surgery.replace("手术", "") in text_lower:
            return surgery + "手术"
    
    return None


CONFIRM_KEYWORDS = ["对", "是", "对的", "是的", "没错", "正确", "确认", "没错", "嗯", "好的", "ok", "OK"]

def is_surgery_confirmed(text: str) -> bool:
    """检测患者是否确认手术信息"""
    text = text.strip().lower()
    print(f"[DEBUG] 检测确认关键词, 文本: '{text}'")
    for keyword in CONFIRM_KEYWORDS:
        if keyword.lower() in text:
            print(f"[DEBUG] 匹配到关键词: '{keyword}'")
            return True
    print(f"[DEBUG] 未匹配到确认关键词")
    return False


def should_end_conversation(session) -> bool:
    """判断是否应该结束对话"""
    msg_count = len([m for m in session.conversation if m.role == "patient"])
    return msg_count >= 8  # 至少8轮对话后可以结束


def normal_chat_stream(session, message: str) -> Generator[dict, None, None]:
    """正常对话流程 - 混合检索 + LLM 流式回复"""
    
    is_emergency, emergency_keywords = detect_emergency(message)
    detected_symptoms = extract_symptoms(message)
    
    print(f"[DEBUG] 检测到症状: {detected_symptoms}")
    
    if is_emergency:
        print(f"[WARNING] 检测到危急情况: {emergency_keywords}")
        emergency_response = prompts.EMERGENCY_RESPONSE_TEMPLATE.format(
            symptoms="、".join(emergency_keywords)
        )
        session.add_message("ai", emergency_response)
        
        yield {
            "content": emergency_response,
            "is_final": True,
            "reference": "",
            "is_emergency": True
        }
        return
    
    retrieved_context, source = hybrid_retrieve(
        message, 
        surgery_type=session.surgery_type
    )
    
    system_prompt = prompts.CHAT_SYSTEM_PROMPT.format(
        surgery_type=session.surgery_type or "未知",
        surgery_date=session.surgery_date
    )
    
    if retrieved_context:
        user_content = prompts.RAG_CONTEXT_TEMPLATE.format(
            retrieved_context=retrieved_context
        ) + f"\n\n患者问题：{message}"
    else:
        user_content = message
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    full_response = ""
    last_error = None
    
    for retry in range(MAX_RETRIES):
        try:
            response = GLOBAL_CLIENT.chat.completions.create(
                model="glm-4.7-flash",
                messages=messages,
                temperature=config.TEMPERATURE if config.TEMPERATURE > 0 else 0.7,
                max_tokens=config.MAX_TOKENS,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    yield {
                        "content": content,
                        "is_final": False,
                        "reference": retrieved_context[:100] if retrieved_context else ""
                    }
            
            if full_response:
                break
            else:
                print(f"[WARNING] 第{retry + 1}次尝试返回空响应，准备重试...")
                time.sleep(RETRY_DELAY)
                
        except Exception as e:
            last_error = e
            print(f"[ERROR] 第{retry + 1}次调用失败: {str(e)}")
            if retry < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    if not full_response:
        error_msg = f"AI服务调用失败，已重试{MAX_RETRIES}次"
        if last_error:
            error_msg += f"，最后错误: {str(last_error)}"
        print(f"[ERROR] {error_msg}")
        
        yield {
            "content": "[ERROR:SERVICE_BUSY]",
            "is_final": True,
            "reference": "",
            "error": "SERVICE_BUSY",
            "error_message": error_msg
        }
        return
    
    session.add_message("ai", full_response)
    
    yield {
        "content": "",
        "is_final": True,
        "reference": "",
        "detected_symptoms": detected_symptoms
    }


def end_chat_stream(session) -> Generator[dict, None, None]:
    """结束对话并生成病历"""
    report = generate_medical_report(session)
    
    session_mgr.session_manager.end_session(session.session_id)
    
    yield {
        "content": "感谢您的配合！我已为您生成了随访报告。",
        "is_final": True,
        "reference": "",
        "report": report
    }


def generate_medical_report(session) -> dict:
    """生成结构化病历"""
    
    if not session or not session.conversation:
        print(f"[WARNING] 会话 {session.session_id if session else 'None'} 无消息记录")
        return {
            "session_id": session.session_id if session else "unknown",
            "report_text": "无法生成报告：会话无消息记录",
            "status": "ERROR",
            "error": "NO_CONVERSATION"
        }
    
    conversation_history = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in session.conversation
    ])
    
    print(f"[DEBUG] 会话 {session.session_id} 共有 {len(session.conversation)} 条消息")
    
    prompt = prompts.MEDICAL_REPORT_PROMPT.format(
        conversation_history=conversation_history,
        patient_name=session.patient_name,
        surgery_type=session.surgery_type or "未知",
        surgery_date=session.surgery_date
    )
    
    all_symptoms = []
    for msg in session.conversation:
        if msg.role == "patient":
            symptoms = extract_symptoms(msg.content)
            all_symptoms.extend(symptoms)
    all_symptoms = list(set(all_symptoms))
    
    report_text = None
    last_error = None
    
    for retry in range(MAX_RETRIES):
        try:
            response = GLOBAL_CLIENT.chat.completions.create(
                model="glm-4.7-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=config.MAX_TOKENS,
                stream=False
            )
            
            report_text = response.choices[0].message.content
            
            if report_text and len(report_text) > 50:
                break
            else:
                print(f"[WARNING] 第{retry + 1}次病历生成返回内容过短，准备重试...")
                time.sleep(RETRY_DELAY)
                
        except Exception as e:
            last_error = e
            print(f"[ERROR] 第{retry + 1}次病历生成失败: {str(e)}")
            if retry < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    if not report_text:
        error_msg = f"病历生成失败，已重试{MAX_RETRIES}次"
        if last_error:
            error_msg += f"，最后错误: {str(last_error)}"
        print(f"[ERROR] {error_msg}")
        
        return {
            "session_id": session.session_id,
            "report_text": error_msg,
            "status": "ERROR",
            "error": "GENERATION_FAILED"
        }
    
    print(f"[OK] 会话 {session.session_id} 病历生成成功，长度: {len(report_text)}")
    
    return {
        "session_id": session.session_id,
        "report_text": report_text,
        "status": "SUCCESS",
        "detected_symptoms": all_symptoms,
        "conversation_count": len(session.conversation)
    }


def get_session_history(session_id: str) -> Optional[dict]:
    """获取会话历史"""
    return session_mgr.session_manager.get_session_history(session_id)


def end_session(session_id: str) -> Optional[dict]:
    """结束会话并返回病历"""
    session = session_mgr.session_manager.end_session(session_id)
    if not session:
        return None
    
    report = generate_medical_report(session)
    
    return {
        "report": report,
        "status": "COMPLETED"
    }
