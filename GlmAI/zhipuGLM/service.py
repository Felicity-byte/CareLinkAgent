import sys
import os
import time
import threading
from typing import Generator, Optional
from datetime import datetime

from zhipuai import ZhipuAI

# 导入模块
sys.path.insert(0, os.path.dirname(__file__))

import config.config as config
import prompts.prompts as prompts
import rag.rag_core as rag_core
import session_manager as session_mgr
from knowledge.zhipu_knowledge import zhipu_knowledge, initialize_zhipu_knowledge

# ==========================
# 全局依赖
# ==========================
GLOBAL_CLIENT: Optional[ZhipuAI] = None
GLOBAL_POST_SURGERY_RAG = None  # 术后护理文档 RAG
GLOBAL_ZHIPU_KNOWLEDGE = None    # 智谱知识库
_rag_loaded = False              # RAG是否已加载完成
_rag_loading = False             # RAG是否正在加载中
_rag_lock = threading.Lock()     # RAG加载锁，防止并发重复加载


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


def initialize_service():
    """服务初始化函数"""
    global GLOBAL_CLIENT, GLOBAL_POST_SURGERY_RAG, GLOBAL_ZHIPU_KNOWLEDGE
    
    print("\n" + "="*60)
    print("  AI 服务启动流程")
    print("="*60)
    
    try:
        # Step 1: 初始化智谱客户端
        print("\n[Step 1/4] 正在初始化智谱AI客户端...")
        api_key = os.environ.get("GLM_API_KEY")
        if not api_key:
            print("  [ERROR] 未找到 GLM_API_KEY 环境变量")
            raise ValueError("GLM_API_KEY 环境变量未设置")
        GLOBAL_CLIENT = ZhipuAI(api_key=api_key)
        print("  [OK] 智谱AI客户端初始化成功")
        
        # Step 2: 启动后台加载本地 RAG（术后护理文档）
        print("\n[Step 2/4] 设置术后护理文档向量数据库（后台预加载）...")
        GLOBAL_POST_SURGERY_RAG = None
        _rag_loaded = False
        _rag_loading = True
        
        # 启动后台线程预加载RAG
        rag_thread = threading.Thread(target=_background_load_rag, daemon=True, name="RAG-Loader")
        rag_thread.start()
        print("  [OK] 向量数据库正在后台加载（不影响服务器启动）")
        
        # Step 3: 初始化智谱知识库
        print("\n[Step 3/4] 正在初始化智谱知识库...")
        GLOBAL_ZHIPU_KNOWLEDGE = initialize_zhipu_knowledge()
        if GLOBAL_ZHIPU_KNOWLEDGE and GLOBAL_ZHIPU_KNOWLEDGE.is_available:
            print("  [OK] 智谱知识库初始化成功")
        else:
            print("  [WARNING] 智谱知识库不可用，将使用LLM自身知识")
        
        # Step 4: 初始化会话管理器
        print("\n[Step 4/4] 正在初始化会话管理器...")
        print("  [OK] 会话管理器就绪")
        
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


def create_session(patient_id: str, patient_name: str, surgery_date: str) -> dict:
    """创建会话"""
    session = session_mgr.session_manager.create_session(
        patient_id, patient_name, surgery_date
    )
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "welcome_message": prompts.WELCOME_PROMPT
    }


def chat_stream(session_id: str, message: str, is_end: bool = False) -> Generator[dict, None, None]:
    """流式对话"""
    session = session_mgr.session_manager.get_session(session_id)
    if not session:
        yield {
            "content": "会话不存在或已过期，请重新开始",
            "is_final": True,
            "reference": ""
        }
        return
    
    # 记录患者消息
    session.add_message("patient", message)
    
    # 阶段1：确认手术类型
    if session.status == session_mgr.SessionStatus.WAITING_SURGERY:
        # 尝试识别手术类型
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
        return
    
    # 阶段2-3：症状收集 / 结束对话
    if is_end or should_end_conversation(session):
        yield from end_chat_stream(session)
        return
    
    # 正常对话流程 - 混合检索 + LLM 回复
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


def should_end_conversation(session) -> bool:
    """判断是否应该结束对话"""
    msg_count = len([m for m in session.conversation if m.role == "patient"])
    return msg_count >= 8  # 至少8轮对话后可以结束


def normal_chat_stream(session, message: str) -> Generator[dict, None, None]:
    """正常对话流程 - 混合检索 + LLM 流式回复"""
    # 混合检索
    retrieved_context, source = hybrid_retrieve(
        message, 
        surgery_type=session.surgery_type
    )
    
    # 构建系统提示词
    system_prompt = prompts.CHAT_SYSTEM_PROMPT.format(
        surgery_type=session.surgery_type or "未知",
        surgery_date=session.surgery_date
    )
    
    # 如果有检索到的文档，添加到上下文
    if retrieved_context:
        user_content = prompts.RAG_CONTEXT_TEMPLATE.format(
            retrieved_context=retrieved_context
        ) + f"\n\n患者问题：{message}"
    else:
        user_content = message
    
    # 调用 LLM 流式生成
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        full_response = ""
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
        
        if not full_response:
            yield {
                "content": "[ERROR:SERVICE_BUSY]",
                "is_final": True,
                "reference": "",
                "error": "SERVICE_BUSY",
                "error_message": "AI服务繁忙，请稍后重试"
            }
            print("[警告] AI返回空响应，可能是API速率限制")
            return
        
        session.add_message("ai", full_response)
        
        yield {
            "content": "",
            "is_final": True,
            "reference": ""
        }
        
    except Exception as e:
        error_msg = f"AI 服务出错: {str(e)}"
        print(f"[错误] {error_msg}")
        yield {
            "content": f"[ERROR:API_ERROR] {error_msg}",
            "is_final": True,
            "reference": "",
            "error": "API_ERROR",
            "error_message": error_msg
        }


def end_chat_stream(session) -> Generator[dict, None, None]:
    """结束对话并生成病历"""
    # 生成结构化病历
    report = generate_medical_report(session)
    
    # 结束会话
    session_mgr.session_manager.end_session(session.session_id)
    
    yield {
        "content": "感谢您的配合！我已为您生成了随访报告。",
        "is_final": True,
        "reference": ""
    }


def generate_medical_report(session) -> dict:
    """生成结构化病历"""
    conversation_history = "\n".join([
        f"{msg.role}: {msg.content}" 
        for msg in session.conversation
    ])
    
    prompt = prompts.MEDICAL_REPORT_PROMPT.format(
        conversation_history=conversation_history,
        patient_name=session.patient_name,
        surgery_type=session.surgery_type or "未知",
        surgery_date=session.surgery_date
    )
    
    try:
        response = GLOBAL_CLIENT.chat.completions.create(
            model="glm-4.7-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=config.MAX_TOKENS,
            stream=False
        )
        
        report_text = response.choices[0].message.content
        
        return {
            "session_id": session.session_id,
            "report_text": report_text,
            "status": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "session_id": session.session_id,
            "report_text": f"报告生成失败: {str(e)}",
            "status": "ERROR"
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
