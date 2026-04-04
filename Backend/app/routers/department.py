from fastapi import APIRouter, Depends
from app.database_tortoise import get_db
from app.models.doctor import Doctor
from app.utils import (
    get_current_user,
    success_response,
    error_response
)

router = APIRouter(tags=["科室模块"])


@router.get("")
async def get_departments(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取所有科室"""
    doctors = await Doctor.filter(deleted_at__isnull=True).all()
    department_names = set(doctor.department_id for doctor in doctors if doctor.department_id)
    data = [
        {"department_name": name, "department_id": name}
        for name in sorted(department_names)
    ]
    return success_response(data=data)