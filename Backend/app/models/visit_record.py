"""复查记录模型"""
from tortoise import fields
from tortoise.models import Model


class VisitRecord(Model):
    """复查记录表"""
    id = fields.IntField(pk=True, description="复查记录ID")
    patient_id = fields.CharField(max_length=36, description="患者ID")
    doctor_id = fields.CharField(max_length=36, description="医生ID")
    visit_date = fields.DateField(description="复查日期")
    visit_type = fields.CharField(max_length=50, description="复查类型")
    diagnosis = fields.TextField(description="诊断结果")
    prescription = fields.TextField(description="处方")
    notes = fields.TextField(description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "visit_records"

    def __str__(self):
        return f"VisitRecord({self.id}, {self.patient_id})"