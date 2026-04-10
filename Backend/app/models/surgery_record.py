"""手术记录模型"""
from tortoise import fields
from tortoise.models import Model


class SurgeryRecord(Model):
    """手术记录表"""
    id = fields.IntField(pk=True, description="手术记录ID")
    patient_id = fields.CharField(max_length=36, description="患者ID")
    doctor_id = fields.CharField(max_length=36, null=True, description="主刀医生ID")
    surgery_name = fields.CharField(max_length=200, description="手术名称")
    surgery_date = fields.DateField(description="手术日期")
    hospital = fields.CharField(max_length=200, null=True, description="手术医院")
    surgery_type = fields.CharField(max_length=50, null=True, description="手术类型")
    anesthesia_method = fields.CharField(max_length=100, null=True, description="麻醉方式")
    surgery_duration = fields.IntField(null=True, description="手术时长(分钟)")
    pre_diagnosis = fields.TextField(null=True, description="术前诊断")
    notes = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "surgery_records"

    def __str__(self):
        return f"SurgeryRecord({self.id}, {self.surgery_name})"
