"""医生模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class Doctor(Model):
    """医生表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="医生ID")
    username = fields.CharField(max_length=100, description="医生姓名")
    password = fields.CharField(max_length=255, description="密码")
    department_id = fields.CharField(max_length=100, description="科室名称")
    title = fields.CharField(max_length=50, null=True, description="职称")
    phone_number = fields.CharField(max_length=20, null=True, description="手机号")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    avatar_url = fields.CharField(max_length=500, null=True, description="头像URL")
    description = fields.TextField(null=True, description="医生简介")
    status = fields.CharField(max_length=20, default="active", description="状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        table = "doctors"

    def __str__(self):
        return f"Doctor({self.id}, {self.username})"