"""AI诊断报告模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class AIDiagnosisReport(Model):
    """AI诊断报告表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="诊断报告ID")
    patient_id = fields.CharField(max_length=36, description="患者ID")
    chat_id = fields.CharField(max_length=36, description="聊天ID")
    chief_complaint = fields.TextField(description="主诉")
    symptoms = fields.TextField(description="症状")
    possible_diagnosis = fields.TextField(description="可能的诊断")
    suggestions = fields.TextField(description="建议")
    severity = fields.CharField(max_length=20, description="严重程度")
    report_status = fields.CharField(max_length=20, description="报告状态")
    detail = fields.TextField(null=True, description="完整结构化报告JSON")
    doctor_id = fields.CharField(max_length=36, null=True, description="医生ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    reviewed_at = fields.DatetimeField(null=True, description="审核时间")

    class Meta:
        table = "ai_diagnosis_report"

    def __str__(self):
        return f"AIDiagnosisReport({self.id}, {self.patient_id})"