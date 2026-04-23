from fastapi import APIRouter, Depends, Form
from datetime import date, time
from app.database_tortoise import get_db
from app.models.appointment import Appointment
from app.models.user import User
from app.models.doctor import Doctor
from app.models.department import Department
from app.utils import (
    get_current_user,
    get_current_doctor,
    success_response,
    error_response
)

router = APIRouter(tags=["预约模块"])


def format_time(t):
    """将 time 或 timedelta 对象格式化为 HH:MM 字符串"""
    if t is None:
        return None
    if isinstance(t, time):
        return t.strftime("%H:%M")
    # timedelta: seconds since midnight
    total_seconds = int(t.total_seconds()) if hasattr(t, 'total_seconds') else t.seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


@router.get("/doctors")
async def list_doctors(
    db = Depends(get_db)
):
    """获取所有医生列表（供患者预约时选择）"""
    doctors = await Doctor.filter(status="active").all()
    result = []
    for doc in doctors:
        dept_name = None
        if doc.department_id:
            dept = await Department.filter(id=doc.department_id).first()
            if dept:
                dept_name = dept.name
        result.append({
            "id": doc.id,
            "name": doc.username,
            "title": doc.title,
            "department_id": doc.department_id,
            "department_name": dept_name
        })
    return success_response(data=result)


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
            "time": format_time(apt.appointment_time),
            "status": apt.status,
            "type": apt.appointment_type,
            "appointment_type": apt.appointment_type,
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
        "appointment_time": format_time(appointment.appointment_time),
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


@router.get("/doctor/list")
async def doctor_list_appointments(
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """医生获取所有预约列表"""
    appointments = await Appointment.all().order_by("-appointment_date", "-appointment_time")

    result = []
    for apt in appointments:
        patient = await User.filter(id=apt.patient_id).first()
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

        # 如果预约没有指定医生但有患者，尝试从患者的负责医生获取科室
        if not doctor_name and patient and patient.responsible_doctor_id:
            doctor = await Doctor.filter(id=patient.responsible_doctor_id).first()
            if doctor:
                doctor_name = doctor.username
                if not department_name and doctor.department_id:
                    dept = await Department.filter(id=doctor.department_id).first()
                    if dept:
                        department_name = dept.name

        result.append({
            "id": str(apt.id),
            "patient_id": apt.patient_id,
            "patient_name": patient.username if patient else "未知患者",
            "patient_phone": patient.phone_number if patient else "",
            "department": department_name or "待分配",
            "doctor": doctor_name or "待分配",
            "date": apt.appointment_date.isoformat() if apt.appointment_date else None,
            "time": format_time(apt.appointment_time),
            "status": apt.status,
            "appointment_type": apt.appointment_type,
            "reason": apt.reason,
            "created_at": apt.created_at.isoformat() if apt.created_at else None
        })

    return success_response(data={"appointments": result})


@router.post("/doctor/invite")
async def doctor_invite_appointment(
    patient_id: str = Form(..., description="患者ID"),
    appointment_date: str = Form(..., description="预约日期 YYYY-MM-DD"),
    appointment_time: str = Form(..., description="预约时间 HH:MM"),
    reason: str = Form(..., description="预约原因"),
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """医生创建预约邀请"""
    try:
        apt_date = date.fromisoformat(appointment_date)
        hour, minute = map(int, appointment_time.split(":"))
        apt_time = time(hour, minute)
    except ValueError as e:
        return error_response(code="40001", msg=f"日期或时间格式错误: {str(e)}")

    patient = await User.filter(id=patient_id).first()
    if not patient:
        return error_response(code="40002", msg="患者不存在")

    appointment = await Appointment.create(
        patient_id=patient_id,
        doctor_id=current_doctor.get("user_id"),
        appointment_type="doctor",
        appointment_date=apt_date,
        appointment_time=apt_time,
        status="pending",
        reason=reason
    )

    return success_response(msg="邀请已发送", data={
        "id": str(appointment.id),
        "appointment_date": appointment.appointment_date.isoformat(),
        "appointment_time": format_time(appointment.appointment_time),
        "status": appointment.status
    })


@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str = Form(..., description="目标状态: confirmed/cancelled/completed"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """更新预约状态（医生/患者共用）"""
    if status not in ("confirmed", "cancelled", "completed"):
        return error_response(code="40001", msg="无效的状态值")

    appointment = await Appointment.filter(id=appointment_id).first()
    if not appointment:
        return error_response(code="40002", msg="预约不存在")

    if appointment.status == "cancelled":
        return error_response(code="40003", msg="预约已取消，无法修改")
    if appointment.status == "completed":
        return error_response(code="40004", msg="预约已完成，无法修改")

    appointment.status = status
    await appointment.save()

    return success_response(msg=f"预约状态已更新为 {status}", data={
        "id": str(appointment.id),
        "status": appointment.status
    })
