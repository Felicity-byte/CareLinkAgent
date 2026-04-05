"""聊天记录模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class ChatRecord(Model):
    """聊天记录表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="聊天记录ID")
    user_id = fields.CharField(max_length=36, description="用户ID")
    doctor_id = fields.CharField(max_length=36, null=True, description="医生ID")
    message = fields.TextField(description="消息内容")
    role = fields.CharField(max_length=20, description="角色")
    chat_session_id = fields.CharField(max_length=36, description="聊天会话ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "chat_records"

    def __str__(self):
        return f"ChatRecord({self.id}, {self.role})"