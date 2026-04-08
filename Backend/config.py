from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置 (MySQL)
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DATABASE_URL: str

    # 调试模式
    DEBUG: bool = True

    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760

    # CORS配置
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # AI服务配置
    GLM_API_KEY: str
    GLM_4V_API_KEY: str = ""  # glm-4v-flash 图片分析 API Key
    AI_SERVICE_HOST: str = "127.0.0.1:50053"  # gRPC 服务端口（与 server.py 保持一致）

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_origins_list(self) -> List[str]:
        """获取CORS允许的源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()