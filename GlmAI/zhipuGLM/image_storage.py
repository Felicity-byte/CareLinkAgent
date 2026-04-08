import os
import base64
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ImageStorage:
    """图片本地存储管理器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化图片存储管理器
        
        Args:
            base_path: 存储根目录，默认为 GlmAI/storage/medical_images
        """
        if base_path is None:
            current_dir = Path(__file__).parent.parent
            self.base_path = current_dir / "storage" / "medical_images"
        else:
            self.base_path = Path(base_path)
        
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, image_base64: str, session_id: str, image_type: str = "wound") -> Dict[str, Any]:
        """
        保存图片到本地
        
        Args:
            image_base64: Base64编码的图片数据
            session_id: 会话ID
            image_type: 图片类型（wound/medical_record）
            
        Returns:
            包含相对路径、绝对路径、文件名的字典
            
        Raises:
            ValueError: 图片数据无效
            OSError: 存储失败（权限不足、磁盘空间不足等）
        """
        if not image_base64 or not isinstance(image_base64, str):
            raise ValueError("无效的图片数据")
        
        # 解码base64数据
        try:
            # 处理带前缀的base64 (data:image/jpeg;base64,...)
            if ',' in image_base64:
                image_base64 = image_base64.split(',', 1)[1]
            
            image_data = base64.b64decode(image_base64)
            
            if len(image_data) == 0:
                raise ValueError("解码后的图片数据为空")
                
        except Exception as e:
            raise ValueError(f"Base64解码失败: {str(e)}")
        
        # 检查文件大小限制 (10MB)
        max_size = 10 * 1024 * 1024
        if len(image_data) > max_size:
            raise ValueError(f"图片大小超过限制 ({len(image_data)} > {max_size} bytes)")
        
        # 按日期创建子目录
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_path = self.base_path / date_str
        date_path.mkdir(exist_ok=True)
        
        # 按会话创建子目录
        session_path = date_path / f"session_{session_id}"
        session_path.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = session_path / filename
        
        # 写入文件
        try:
            with open(file_path, 'wb') as f:
                f.write(image_data)
        except PermissionError:
            raise OSError(f"没有写入权限: {file_path}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                raise OSError("磁盘空间不足")
            raise OSError(f"存储图片失败: {str(e)}")
        
        # 获取文件信息
        file_size = file_path.stat().st_size
        
        return {
            "url": str(file_path.relative_to(self.base_path)).replace('\\', '/'),
            "absolute_path": str(file_path.absolute()),
            "filename": filename,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat(),
            "image_type": image_type
        }
    
    def get_image_path(self, relative_url: str) -> Optional[Path]:
        """
        根据相对路径获取完整路径
        
        Args:
            relative_url: 相对路径
            
        Returns:
            完整路径或None
        """
        file_path = self.base_path / relative_url.replace('/', os.sep)
        return file_path if file_path.exists() else None
    
    def delete_image(self, relative_url: str) -> bool:
        """
        删除图片
        
        Args:
            relative_url: 相对路径
            
        Returns:
            是否删除成功
        """
        file_path = self.get_image_path(relative_url)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def check_disk_space(self, required_bytes: int) -> bool:
        """
        检查磁盘是否有足够空间
        
        Args:
            required_bytes: 需要的字节数
            
        Returns:
            是否有足够空间
        """
        import shutil
        disk_usage = shutil.disk_usage(self.base_path)
        return disk_usage.free >= required_bytes
    
    def get_session_images(self, session_id: str) -> list:
        """
        获取指定会话的所有图片
        
        Args:
            session_id: 会话ID
            
        Returns:
            图片信息列表
        """
        images = []
        session_pattern = f"session_{session_id}"
        
        for date_dir in self.base_path.iterdir():
            if date_dir.is_dir():
                session_dir = date_dir / session_pattern
                if session_dir.exists() and session_dir.is_dir():
                    for img_file in session_dir.iterdir():
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            images.append({
                                "url": str(img_file.relative_to(self.base_path)).replace('\\', '/'),
                                "absolute_path": str(img_file.absolute()),
                                "filename": img_file.name,
                                "file_size": img_file.stat().st_size,
                                "upload_time": datetime.fromtimestamp(img_file.stat().st_ctime).isoformat()
                            })
        
        return images


# 全局实例
_global_image_storage: Optional[ImageStorage] = None


def get_image_storage() -> ImageStorage:
    """获取全局图片存储实例"""
    global _global_image_storage
    if _global_image_storage is None:
        _global_image_storage = ImageStorage()
    return _global_image_storage
