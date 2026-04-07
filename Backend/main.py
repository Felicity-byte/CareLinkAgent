from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
from config import settings
from database import TORTOISE_ORM
from app.routers import (
    user_router,
    doctor_router,
    department_router
)
from app.utils.response import error_response
from tortoise import Tortoise

app = FastAPI(
    title="MediMeow Backend API",
    description="智能医疗预诊系统后端API",
    version="1.0.0",
)


@app.get("/migrate")
async def migrate():
    """数据库迁移接口"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()
    return {"msg": "迁移完成"}

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    await Tortoise.init(config=TORTOISE_ORM)
    if settings.DEBUG:
        await Tortoise.generate_schemas()
    print("数据库连接已初始化")


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理数据库连接"""
    await Tortoise.close_connections()
    print("数据库连接已关闭")


# 注册路由
# Vite代理会去掉 /api 前缀，所以这里用 /user, /doctor, /department
app.include_router(user_router, prefix="/user", tags=["用户"])
app.include_router(doctor_router, prefix="/doctor", tags=["医生"])
app.include_router(department_router, prefix="/department", tags=["科室"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(code=str(exc.status_code), msg=exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(code="422", msg=str(exc))


@app.get("/")
async def root():
    return {"message": "MediMeow Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "MediMeow Backend"}