"""Tortoise-ORM数据库配置"""
from tortoise import Tortoise
from config import settings

db_config = settings.get_db_config()

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": db_config["host"],
                "port": db_config["port"],
                "user": db_config["user"],
                "password": db_config["password"],
                "database": db_config["database"],
                "minsize": 1,
                "maxsize": 5,
                "charset": "utf8mb4",
            }
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models",
                "aerich.models"
            ],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai"
}


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(config=TORTOISE_ORM)
    if settings.DEBUG:
        await Tortoise.generate_schemas()


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()
