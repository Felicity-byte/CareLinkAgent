import uuid
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import sys

def safe_isoformat(dt: datetime = None) -> str:
    """安全地生成ISO格式时间字符串，兼容Windows"""
    if dt is None:
        dt = datetime.now()
    try:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    except Exception:
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def safe_parse_isoformat(iso_str: str) -> datetime:
    """安全地解析ISO格式时间字符串，兼容Windows"""
    if not iso_str:
        return datetime.now()
    try:
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1]
        if '.' in iso_str:
            return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(f"[WARNING] Failed to parse timestamp '{iso_str}': {e}")
        try:
            return datetime.fromisoformat(iso_str.replace('Z', ''))
        except Exception:
            return datetime.now()

class SessionStatus(Enum):
    WAITING_SURGERY = "WAITING_SURGERY"
    WAITING_SURGERY_CONFIRM = "WAITING_SURGERY_CONFIRM"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = safe_isoformat()

SESSION_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "session_store"
)


class Session:
    def __init__(self, patient_id: str, patient_name: str, surgery_date: str):
        self.session_id = str(uuid.uuid4())
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.surgery_date = surgery_date
        self.surgery_type: Optional[str] = None
        self.status = SessionStatus.WAITING_SURGERY
        self.conversation: List[ChatMessage] = []
        self.created_at = safe_isoformat()
        self.ended_at: Optional[str] = None
        self.pending_image_analysis: Optional[Dict[str, Any]] = None
        self.uploaded_images: List[Dict[str, Any]] = []
        self.final_report: Optional[Dict[str, Any]] = None
        self._dirty = True

    def to_dict(self) -> dict:
        """Serialize session to dict for persistence."""
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "surgery_date": self.surgery_date,
            "surgery_type": self.surgery_type,
            "status": self.status.value,
            "conversation": [{"role": m.role, "content": m.content, "timestamp": m.timestamp}
                            for m in self.conversation],
            "created_at": self.created_at,
            "ended_at": self.ended_at,
            "pending_image_analysis": self.pending_image_analysis,
            "uploaded_images": self.uploaded_images,
            "final_report": self.final_report,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Deserialize session from dict."""
        session = cls.__new__(cls)
        session.session_id = data["session_id"]
        session.patient_id = data["patient_id"]
        session.patient_name = data["patient_name"]
        session.surgery_date = data["surgery_date"]
        session.surgery_type = data.get("surgery_type")
        session.status = SessionStatus(data.get("status", SessionStatus.WAITING_SURGERY.value))
        session.conversation = []
        for m in data.get("conversation", []):
            msg = ChatMessage.__new__(ChatMessage)
            msg.role = m["role"]
            msg.content = m["content"]
            msg.timestamp = m.get("timestamp", safe_isoformat())
            session.conversation.append(msg)
        session.created_at = data.get("created_at", safe_isoformat())
        session.ended_at = data.get("ended_at")
        session.pending_image_analysis = data.get("pending_image_analysis")
        session.uploaded_images = data.get("uploaded_images", [])
        session.final_report = data.get("final_report")
        session._dirty = False
        return session

    def _persist_path(self) -> str:
        os.makedirs(SESSION_PERSIST_DIR, exist_ok=True)
        return os.path.join(SESSION_PERSIST_DIR, f"{self.session_id}.json")

    def save_to_disk(self):
        """Persist session to disk."""
        try:
            with open(self._persist_path(), "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            self._dirty = False
        except Exception as e:
            print(f"[WARNING] Failed to persist session {self.session_id}: {e}")

    def remove_from_disk(self):
        """Remove persisted session file."""
        try:
            path = self._persist_path()
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"[WARNING] Failed to remove session file {self.session_id}: {e}")

    def add_message(self, role: str, content: str):
        message = ChatMessage(role, content)
        self.conversation.append(message)
        self._dirty = True
        return message

    def set_pending_image_analysis(self, analysis_data: Dict[str, Any]):
        self.pending_image_analysis = analysis_data
        self.save_to_disk()

    def get_pending_image_analysis(self) -> Optional[Dict[str, Any]]:
        return self.pending_image_analysis

    def clear_pending_image_analysis(self):
        self.pending_image_analysis = None
        self.save_to_disk()

    def add_uploaded_image(self, image_info: Dict[str, Any]):
        self.uploaded_images.append(image_info)
        self.save_to_disk()

    def get_uploaded_images(self) -> List[Dict[str, Any]]:
        return self.uploaded_images

    def set_final_report(self, report: Dict[str, Any]):
        self.final_report = report
        self.save_to_disk()

    def get_final_report(self) -> Optional[Dict[str, Any]]:
        return self.final_report

    def set_surgery_type(self, surgery_type: str):
        self.surgery_type = surgery_type
        if self.status == SessionStatus.WAITING_SURGERY:
            self.status = SessionStatus.WAITING_SURGERY_CONFIRM
        self.save_to_disk()

    def confirm_surgery(self):
        if self.status == SessionStatus.WAITING_SURGERY_CONFIRM:
            self.status = SessionStatus.ACTIVE
        self.save_to_disk()

    def complete(self):
        self.status = SessionStatus.COMPLETED
        self.ended_at = safe_isoformat()
        self.save_to_disk()

    def cancel(self):
        self.status = SessionStatus.CANCELLED
        self.ended_at = safe_isoformat()
        self.remove_from_disk()

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

    def load_persisted_sessions(self):
        """Load all persisted sessions from disk on restart."""
        os.makedirs(SESSION_PERSIST_DIR, exist_ok=True)
        count = 0
        for filename in os.listdir(SESSION_PERSIST_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(SESSION_PERSIST_DIR, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    session = Session.from_dict(data)
                    self.sessions[session.session_id] = session
                    count += 1
                except Exception as e:
                    print(f"[WARNING] Failed to load session {filename}: {e}")
        if count > 0:
            print(f"--- [INFO] 已恢复 {count} 个持久化会话 ---")

    def create_session(self, patient_id: str, patient_name: str, surgery_date: str) -> Session:
        session = Session(patient_id, patient_name, surgery_date)
        self.sessions[session.session_id] = session
        session.save_to_disk()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if session and session.status in [SessionStatus.ACTIVE, SessionStatus.WAITING_SURGERY]:
            try:
                created_time = safe_parse_isoformat(session.created_at)
                if (datetime.now() - created_time).total_seconds() > self.session_timeout:
                    session.cancel()
                    session.remove_from_disk()
                    return None
            except Exception as e:
                print(f"[WARNING] Session timeout check failed: {e}")
        return session

    def end_session(self, session_id: str) -> Optional[Session]:
        session = self.get_session(session_id)
        if session:
            session.complete()
            session.save_to_disk()
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
                try:
                    created_time = safe_parse_isoformat(session.created_at)
                    if (current_time - created_time).total_seconds() > self.session_timeout:
                        session.cancel()
                        session.remove_from_disk()
                        expired_ids.append(session_id)
                except Exception as e:
                    print(f"[WARNING] Cleanup session {session_id} failed: {e}")

        for sid in expired_ids:
            del self.sessions[sid]

        return len(expired_ids)

# 全局会话管理器实例
session_manager = SessionManager()
