"""科室模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class Department(Model):
    """科室表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="科室ID")
    name = fields.CharField(max_length=100, unique=True, description="科室名称")
    code = fields.CharField(max_length=50, unique=True, description="科室代码")
    description = fields.TextField(null=True, description="科室描述")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        table = "departments"

    def __str__(self):
        return f"Department({self.id}, {self.name})"
