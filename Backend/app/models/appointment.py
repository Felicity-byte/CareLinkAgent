"""预约模型"""
from tortoise import fields
from tortoise.models import Model


class Appointment(Model):
    """预约表"""
    id = fields.IntField(pk=True, description="预约ID")
    patient_id = fields.CharField(max_length=36, description="患者ID")
    doctor_id = fields.CharField(max_length=36, null=True, description="医生ID")
    appointment_type = fields.CharField(max_length=20, description="预约类型")
    appointment_date = fields.DateField(description="预约日期")
    appointment_time = fields.TimeField(description="预约时间")
    status = fields.CharField(max_length=20, description="状态")
    reason = fields.TextField(description="预约原因")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "appointment"

    def __str__(self):
        return f"Appointment({self.id}, {self.patient_id})"