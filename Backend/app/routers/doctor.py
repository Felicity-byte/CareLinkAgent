from fastapi import APIRouter, Depends, HTTPException, Query
from app.database_tortoise import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorLogin, DoctorReport
from app.utils import (
    verify_password,
    create_access_token,
    get_current_doctor,
    success_response,
    error_response
)

router = APIRouter(tags=["医生模块"])


@router.post("/login")
async def doctor_login(
    username: str = Query(..., description="医生用户名"),
    password: str = Query(..., description="密码"),
    db = Depends(get_db)
):
    """医生登录"""
    doctor = await Doctor.filter(
        username=username,
        deleted_at__isnull=True
    ).first()

    if not doctor or not verify_password(password, doctor.password):
        return error_response(code="10003", msg="用户名或密码错误")

    access_token = create_access_token(
        data={"sub": doctor.id, "type": "doctor"}
    )

    return success_response(
        msg="登录成功",
        data={
            "token": access_token,
            "doctor": {
                "id": doctor.id,
                "username": doctor.username,
                "department_name": doctor.department_id,
                "created_at": doctor.created_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.created_at else None,
                "updated_at": doctor.updated_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.updated_at else None,
                "deleted_at": doctor.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.deleted_at else None
            }
        }
    )