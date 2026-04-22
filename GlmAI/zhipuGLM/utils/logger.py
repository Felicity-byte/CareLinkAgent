import logging
import sys
import os
from datetime import datetime
from typing import Optional
import json

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'patient_id'):
            log_data['patient_id'] = record.patient_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'error'):
            log_data['error'] = record.error
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        extra_info = ""
        if hasattr(record, 'session_id'):
            extra_info += f" [session:{record.session_id[:8]}]"
        if hasattr(record, 'duration'):
            extra_info += f" [{record.duration:.3f}s]"
            
        return f"{timestamp} {color}[{record.levelname}]{self.RESET} {record.name}{extra_info}: {record.getMessage()}"


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, f"{name}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    return logger


class AILogger:
    """AI服务专用日志记录器"""
    
    def __init__(self, name: str = "ai_service"):
        self.logger = setup_logger(name)
        
    def session_created(self, session_id: str, patient_id: str, patient_name: str):
        """记录会话创建"""
        record = self.logger.info(
            f"Session created for patient: {patient_name}",
            extra={'session_id': session_id, 'patient_id': patient_id}
        )
        
    def chat_request(self, session_id: str, message: str, message_len: int):
        """记录聊天请求"""
        self.logger.debug(
            f"Chat request received, message length: {message_len}",
            extra={'session_id': session_id}
        )
        
    def chat_response(self, session_id: str, duration: float, tokens: int = None):
        """记录聊天响应"""
        extra = {'session_id': session_id, 'duration': duration}
        if tokens:
            extra['tokens'] = tokens
        self.logger.info(
            f"Chat response completed in {duration:.3f}s",
            extra=extra
        )
        
    def rag_retrieve(self, query: str, source: str, duration: float, doc_count: int):
        """记录RAG检索"""
        self.logger.debug(
            f"RAG retrieved {doc_count} docs from {source} in {duration:.3f}s",
            extra={'duration': duration}
        )
        
    def emergency_detected(self, session_id: str, keywords: list):
        """记录危急情况检测"""
        self.logger.warning(
            f"Emergency keywords detected: {keywords}",
            extra={'session_id': session_id}
        )
        
    def error(self, session_id: str, error_type: str, error_msg: str, exc_info=None):
        """记录错误"""
        self.logger.error(
            f"[{error_type}] {error_msg}",
            extra={'session_id': session_id, 'error': error_type},
            exc_info=exc_info
        )
        
    def session_ended(self, session_id: str, duration: float, message_count: int):
        """记录会话结束"""
        self.logger.info(
            f"Session ended, {message_count} messages exchanged",
            extra={'session_id': session_id, 'duration': duration}
        )
        
    def llm_call(self, model: str, duration: float, success: bool):
        """记录LLM调用"""
        status = "success" if success else "failed"
        self.logger.debug(
            f"LLM call to {model} {status} in {duration:.3f}s",
            extra={'duration': duration}
        )


ai_logger = AILogger()
