from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_creator
from datetime import datetime
import uuid


class MedicalImage(models.Model):
    """医疗图片记录表"""
    
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    session_id = fields.CharField(max_length=36, index=True)
    file_path = fields.CharField(max_length=500, description="相对路径")
    file_name = fields.CharField(max_length=200, null=True)
    file_size = fields.IntField(null=True)
    upload_time = fields.DatetimeField(auto_now_add=True)
    image_type = fields.CharField(max_length=50, default="wound", description="图片类型: wound/medical_record")
    analysis_result = fields.JSONField(null=True, description="图片分析结果JSON")
    
    class Meta:
        table = "medical_images"
        description = "医疗图片记录表"
    
    def __str__(self):
        return f"MedicalImage({self.file_name})"


# Pydantic Schema
MedicalImage_Pydantic = pydantic_creator(
    "medical_image",
    MedicalImage,
    exclude=["id"],
    compute=["upload_time"]
)


class MedicalImageInSchema:
    """创建图片记录的输入Schema"""
    session_id: str
    file_path: str
    file_name: str = None
    file_size: int = None
    image_type: str = "wound"
    analysis_result: dict = None


class MedicalImageOutSchema:
    """图片记录输出Schema"""
    id: str
    session_id: str
    file_path: str
    file_name: str = None
    file_size: int = None
    upload_time: datetime = None
    image_type: str = "wound"
    analysis_result: dict = None
