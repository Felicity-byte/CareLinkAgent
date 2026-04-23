import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings

# Magic bytes for common image formats
IMAGE_MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # WEBP starts with RIFF
}


def _detect_image_type(content: bytes):
    """Detect image type by magic bytes (not relying on content-type header)."""
    for magic, mime_type in IMAGE_MAGIC_BYTES.items():
        if content.startswith(magic):
            return mime_type
    return None


async def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    """
    保存上传的文件

    返回: (file_id, file_path, file_size)
    """
    # 验证文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 移回文件开头

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
        )

    # 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件ID和文件名
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename

    # 读取内容并验证
    content = await file.read()
    detected_type = _detect_image_type(content)
    if detected_type is None:
        raise HTTPException(status_code=400, detail="无法识别文件类型，只允许上传图片文件")

    # 异步保存文件
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    return file_id, str(file_path), file_size


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def get_file_path(file_id: str) -> str:
    """根据文件ID获取文件路径"""
    upload_dir = Path(settings.UPLOAD_DIR)
    # 查找匹配的文件
    for file_path in upload_dir.glob(f"{file_id}.*"):
        return str(file_path)
    raise HTTPException(status_code=404, detail="文件不存在")
