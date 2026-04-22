"""Tortoise-ORM模型"""
from app.models.user import User
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.chat_record import ChatRecord
from app.models.ai_diagnosis_report import AIDiagnosisReport
from app.models.appointment import Appointment
from app.models.visit_record import VisitRecord
from app.models.medical_image import MedicalImage
from app.models.surgery_record import SurgeryRecord
from app.models.ai_chat_session import AIChatSession, AIChatMessage

__all__ = [
    "User",
    "Doctor",
    "Department",
    "ChatRecord",
    "AIDiagnosisReport",
    "Appointment",
    "VisitRecord",
    "MedicalImage",
    "SurgeryRecord",
    "AIChatSession",
    "AIChatMessage"
]