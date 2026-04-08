import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class SessionStatus(Enum):
    WAITING_SURGERY = "WAITING_SURGERY"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role  # "patient" 或 "ai"
        self.content = content
        self.timestamp = datetime.now().isoformat()

class Session:
    def __init__(self, patient_id: str, patient_name: str, surgery_date: str):
        self.session_id = str(uuid.uuid4())
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.surgery_date = surgery_date
        self.surgery_type: Optional[str] = None
        self.status = SessionStatus.WAITING_SURGERY
        self.conversation: List[ChatMessage] = []
        self.created_at = datetime.now().isoformat()
        self.ended_at: Optional[str] = None
        self.pending_image_analysis: Optional[Dict[str, Any]] = None
        self.uploaded_images: List[Dict[str, Any]] = []
        self.final_report: Optional[Dict[str, Any]] = None

    def add_message(self, role: str, content: str):
        message = ChatMessage(role, content)
        self.conversation.append(message)
        return message

    def set_pending_image_analysis(self, analysis_data: Dict[str, Any]):
        self.pending_image_analysis = analysis_data

    def get_pending_image_analysis(self) -> Optional[Dict[str, Any]]:
        return self.pending_image_analysis

    def clear_pending_image_analysis(self):
        self.pending_image_analysis = None

    def add_uploaded_image(self, image_info: Dict[str, Any]):
        self.uploaded_images.append(image_info)

    def get_uploaded_images(self) -> List[Dict[str, Any]]:
        return self.uploaded_images

    def set_final_report(self, report: Dict[str, Any]):
        self.final_report = report

    def get_final_report(self) -> Optional[Dict[str, Any]]:
        return self.final_report

    def set_surgery_type(self, surgery_type: str):
        self.surgery_type = surgery_type
        if self.status == SessionStatus.WAITING_SURGERY:
            self.status = SessionStatus.ACTIVE

    def complete(self):
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.now().isoformat()

    def cancel(self):
        self.status = SessionStatus.CANCELLED
        self.ended_at = datetime.now().isoformat()

    def get_history(self) -> List[Dict[str, Any]]:
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in self.conversation
        ]

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = 1800  # 30分钟超时

    def create_session(self, patient_id: str, patient_name: str, surgery_date: str) -> Session:
        session = Session(patient_id, patient_name, surgery_date)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if session and session.status in [SessionStatus.ACTIVE, SessionStatus.WAITING_SURGERY]:
            created_time = datetime.fromisoformat(session.created_at)
            if (datetime.now() - created_time).total_seconds() > self.session_timeout:
                session.cancel()
                return None
        return session

    def end_session(self, session_id: str) -> Optional[Session]:
        session = self.get_session(session_id)
        if session:
            session.complete()
        return session

    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "surgery_type": session.surgery_type or "",
            "messages": session.get_history(),
            "created_at": session.created_at,
            "ended_at": session.ended_at or "",
            "status": session.status.value
        }

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_ids = []
        
        for session_id, session in self.sessions.items():
            if session.status in [SessionStatus.ACTIVE, SessionStatus.WAITING_SURGERY]:
                created_time = datetime.fromisoformat(session.created_at)
                if (current_time - created_time).total_seconds() > self.session_timeout:
                    session.cancel()
                    expired_ids.append(session_id)
        
        for sid in expired_ids:
            del self.sessions[sid]
        
        return len(expired_ids)

# 全局会话管理器实例
session_manager = SessionManager()
