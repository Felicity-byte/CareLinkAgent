"""AI聊天会话模型"""
import uuid
from tortoise import fields
from tortoise.models import Model


class AIChatSession(Model):
    """AI聊天会话表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="会话ID")
    user_id = fields.CharField(max_length=36, description="用户ID")
    title = fields.CharField(max_length=100, null=True, description="会话标题")
    surgery_type = fields.CharField(max_length=100, null=True, description="手术类型")
    status = fields.CharField(max_length=20, default="active", description="状态: active/completed")
    message_count = fields.IntField(default=0, description="消息数量")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "ai_chat_sessions"

    def __str__(self):
        return f"AIChatSession({self.id}, {self.title})"


class AIChatMessage(Model):
    """AI聊天消息表"""
    id = fields.CharField(max_length=36, pk=True, default_factory=lambda: str(uuid.uuid4()), description="消息ID")
    session_id = fields.CharField(max_length=36, description="会话ID")
    role = fields.CharField(max_length=20, description="角色: user/ai")
    content = fields.TextField(description="消息内容")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "ai_chat_messages"

    def __str__(self):
        return f"AIChatMessage({self.id}, {self.role})"
