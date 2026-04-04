"""用户模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class User(Model):
    """用户表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="用户ID")
    phone_number = fields.CharField(max_length=20, unique=True, description="手机号")
    password = fields.CharField(max_length=255, description="密码")
    username = fields.CharField(max_length=100, null=True, description="用户姓名")
    gender = fields.CharField(max_length=10, null=True, description="性别")
    birth = fields.DateField(null=True, description="出生日期")
    ethnicity = fields.CharField(max_length=50, null=True, description="民族")
    origin = fields.CharField(max_length=100, null=True, description="籍贯")
    avatar_url = fields.CharField(max_length=500, null=True, description="头像URL")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        table = "users"

    def __str__(self):
        return f"User({self.id}, {self.phone_number})"