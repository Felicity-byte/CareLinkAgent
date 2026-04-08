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
    department_router,
    wound_router,
    appointment_router
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
    if not settings.DEBUG:
        return error_response(code="403", msg="生产环境禁止执行迁移", status_code=403)
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()
    return {"msg": "迁移完成"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup():
    await Tortoise.init(config=TORTOISE_ORM)
    if settings.DEBUG:
        await Tortoise.generate_schemas()
    print("\n" + "="*50, flush=True)
    print("  后端服务启动成功!", flush=True)
    print("="*50, flush=True)
    print(f"  API 地址:  http://localhost:8000", flush=True)
    print(f"  API 文档:  http://localhost:8000/docs", flush=True)
    print(f"  健康检查:  http://localhost:8000/health", flush=True)
    print("="*50 + "\n", flush=True)


@app.on_event("shutdown")
async def shutdown():
    await Tortoise.close_connections()
    print("数据库连接已关闭")


app.include_router(user_router, prefix="/user", tags=["用户"])
app.include_router(doctor_router, prefix="/doctor", tags=["医生"])
app.include_router(department_router, prefix="/department", tags=["科室"])
app.include_router(wound_router, prefix="/wound", tags=["伤口分析"])
app.include_router(appointment_router, prefix="/appointments", tags=["预约"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "base": {"code": str(exc.status_code), "msg": exc.detail},
            "data": None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "base": {"code": "422", "msg": "请求参数验证失败"},
            "data": None
        }
    )


@app.get("/")
async def root():
    return {"message": "MediMeow Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "MediMeow Backend"}
