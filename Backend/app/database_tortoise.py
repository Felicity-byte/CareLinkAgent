"""Tortoise-ORM数据库依赖（兼容性别名）"""
from tortoise import Tortoise

async def get_db():
    """获取数据库会话的依赖（兼容性别名）"""
    yield Tortoise