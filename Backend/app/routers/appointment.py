from fastapi import APIRouter, Depends, Form
from datetime import date, time
from app.database_tortoise import get_db
from app.models.appointment import Appointment
from app.models.user import User
from app.models.doctor import Doctor
from app.models.department import Department
from app.utils import (
    get_current_user,
    success_response,
    error_response
)

router = APIRouter(tags=["预约模块"])


@router.get("")
async def list_appointments(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取当前患者的预约列表"""
    user_id = current_user.get("user_id")
    
    appointments = await Appointment.filter(
        patient_id=user_id
    ).order_by("-appointment_date", "-appointment_time")
    
    result = []
    for apt in appointments:
        doctor_name = None
        department_name = None
        
        if apt.doctor_id:
            doctor = await Doctor.filter(id=apt.doctor_id).first()
            if doctor:
                doctor_name = doctor.username
                if doctor.department_id:
                    dept = await Department.filter(id=doctor.department_id).first()
                    if dept:
                        department_name = dept.name
        
        result.append({
            "id": str(apt.id),
            "department": department_name or "待分配",
            "doctor": doctor_name or "待分配",
            "date": apt.appointment_date.isoformat() if apt.appointment_date else None,
            "time": apt.appointment_time.isoformat() if apt.appointment_time else None,
            "status": apt.status,
            "type": apt.appointment_type,
            "reason": apt.reason
        })
    
    return success_response(data={"appointments": result})


@router.post("")
async def create_appointment(
    appointment_type: str = Form(..., description="预约类型"),
    appointment_date: str = Form(..., description="预约日期 YYYY-MM-DD"),
    appointment_time: str = Form(..., description="预约时间 HH:MM"),
    reason: str = Form(..., description="预约原因"),
    doctor_id: str = Form(None, description="医生ID"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """创建预约"""
    user_id = current_user.get("user_id")
    
    try:
        apt_date = date.fromisoformat(appointment_date)
        hour, minute = map(int, appointment_time.split(":"))
        apt_time = time(hour, minute)
    except ValueError as e:
        return error_response(code="40001", msg=f"日期或时间格式错误: {str(e)}")
    
    appointment = await Appointment.create(
        patient_id=user_id,
        doctor_id=doctor_id,
        appointment_type=appointment_type,
        appointment_date=apt_date,
        appointment_time=apt_time,
        status="pending",
        reason=reason
    )
    
    return success_response(msg="预约创建成功", data={
        "id": str(appointment.id),
        "appointment_type": appointment.appointment_type,
        "appointment_date": appointment.appointment_date.isoformat(),
        "appointment_time": appointment.appointment_time.isoformat(),
        "status": appointment.status
    })


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """取消预约"""
    user_id = current_user.get("user_id")
    
    appointment = await Appointment.filter(
        id=appointment_id,
        patient_id=user_id
    ).first()
    
    if not appointment:
        return error_response(code="40002", msg="预约不存在")
    
    if appointment.status == "cancelled":
        return error_response(code="40003", msg="预约已取消")
    
    if appointment.status == "completed":
        return error_response(code="40004", msg="已完成的预约无法取消")
    
    appointment.status = "cancelled"
    await appointment.save()
    
    return success_response(msg="预约已取消")
