from pydantic_settings import BaseSettings
from typing import List
from urllib.parse import urlparse


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置 (MySQL) - 使用DATABASE_URL
    DATABASE_URL: str

    # 调试模式
    DEBUG: bool = False

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
    GLM_4V_API_KEY: str = ""
    AI_SERVICE_HOST: str = "127.0.0.1:50053"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context):
        """启动时校验关键配置"""
        warnings = []
        if self.DATABASE_URL in (None, "mysql+pymysql://root:your_password@localhost:3306/medimeow_db"):
            warnings.append("DATABASE_URL 未修改，使用了默认值")
        if self.SECRET_KEY in (None, "", "your-secret-key-here-change-in-production", "change-this-to-a-random-secret-key"):
            warnings.append("SECRET_KEY 未修改，使用了默认/弱密钥")
        if not self.GLM_API_KEY:
            warnings.append("GLM_API_KEY 未配置")
        if warnings:
            import sys
            for w in warnings:
                print(f"[配置警告] {w}")
            if not self.DEBUG:
                print("[严重] 生产环境存在未配置的安全项，请检查 .env 文件")
                sys.exit(1)

    def get_origins_list(self) -> List[str]:
        """获取CORS允许的源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    def get_db_config(self) -> dict:
        """从DATABASE_URL解析数据库配置"""
        parsed = urlparse(self.DATABASE_URL)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") or "",
        }


settings = Settings()
