from fastapi import APIRouter, Depends, HTTPException, Query, Form
from tortoise.exceptions import DoesNotExist
import uuid
from app.database_tortoise import get_db
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.user import User
from app.models.ai_diagnosis_report import AIDiagnosisReport
from app.schemas.doctor import DoctorLogin, DoctorReport
from app.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_doctor,
    success_response,
    error_response
)

router = APIRouter(tags=["医生模块"])


@router.post("/register")
async def doctor_register(
    phone_number: str = Form(..., description="手机号"),
    password: str = Form(..., description="密码"),
    username: str = Form(..., description="姓名"),
    department_id: str = Form(..., description="科室ID"),
    db = Depends(get_db)
):
    """医生注册"""
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone_number):
        return error_response(code="30001", msg="手机号格式不正确")

    if len(password) < 6:
        return error_response(code="30002", msg="密码至少6位")

    existing_doctor = await Doctor.filter(
        phone_number=phone_number,
        deleted_at__isnull=True
    ).first()

    if existing_doctor:
        return error_response(code="30003", msg="该手机号已注册")

    try:
        department = await Department.get(id=department_id, deleted_at__isnull=True)
    except DoesNotExist:
        return error_response(code="30004", msg="科室不存在")

    hashed_password = get_password_hash(password)

    doctor = await Doctor.create(
        id=str(uuid.uuid4()),
        phone_number=phone_number,
        password=hashed_password,
        username=username,
        department=department
    )

    return success_response(msg="注册成功", data={
        "id": doctor.id,
        "username": doctor.username,
        "phone_number": doctor.phone_number
    })


@router.post("/login")
async def doctor_login(
    phone_number: str = Form(..., description="手机号"),
    password: str = Form(..., description="密码"),
    db = Depends(get_db)
):
    """医生登录"""
    doctor = await Doctor.filter(
        phone_number=phone_number,
        deleted_at__isnull=True
    ).first()

    if not doctor or not verify_password(password, doctor.password):
        return error_response(code="10003", msg="手机号或密码错误")

    await doctor.fetch_related("department")

    access_token = create_access_token(
        data={"sub": doctor.id, "type": "doctor"}
    )
    refresh_token = create_refresh_token(
        data={"sub": doctor.id, "type": "doctor"}
    )

    department_name = doctor.department.name if doctor.department else None

    return success_response(
        msg="登录成功",
        data={
            "token": access_token,
            "refresh_token": refresh_token,
            "doctor": {
                "id": doctor.id,
                "username": doctor.username,
                "department_id": doctor.department.id if doctor.department else None,
                "department_name": department_name,
                "title": doctor.title,
                "created_at": doctor.created_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.created_at else None,
                "updated_at": doctor.updated_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.updated_at else None,
                "deleted_at": doctor.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if doctor.deleted_at else None
            }
        }
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str = Form(..., description="刷新令牌"),
    db = Depends(get_db)
):
    """刷新访问令牌"""
    from jose import jwt
    from config import settings

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("token_type") != "refresh":
            return error_response(code="10005", msg="无效的刷新令牌")

        doctor_id = payload.get("sub")
        user_type = payload.get("type", "doctor")

        if user_type == "doctor":
            doctor = await Doctor.filter(id=doctor_id, deleted_at__isnull=True).first()
            if not doctor:
                return error_response(code="10004", msg="医生不存在")
        else:
            return error_response(code="10005", msg="无效的刷新令牌")

        new_access_token = create_access_token(
            data={"sub": doctor_id, "type": user_type}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": doctor_id, "type": user_type}
        )

        return success_response(
            msg="刷新成功",
            data={
                "token": new_access_token,
                "refresh_token": new_refresh_token
            }
        )
    except Exception:
        return error_response(code="10005", msg="刷新令牌已过期")


@router.post("/patient/register")
async def register_patient(
    phone_number: str = Form(..., description="患者手机号"),
    password: str = Form(..., description="密码"),
    username: str = Form(..., description="患者姓名"),
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """医生为患者注册账号"""
    import re

    if not re.match(r'^1[3-9]\d{9}$', phone_number):
        return error_response(code="30001", msg="手机号格式不正确")

    if len(password) < 6:
        return error_response(code="30002", msg="密码至少6位")

    existing_user = await User.filter(
        phone_number=phone_number,
        deleted_at__isnull=True
    ).first()

    if existing_user:
        return error_response(code="30003", msg="该手机号已注册")

    hashed_password = get_password_hash(password)

    new_user = await User.create(
        id=str(uuid.uuid4()),
        phone_number=phone_number,
        password=hashed_password,
        username=username,
        responsible_doctor_id=current_doctor["user_id"]
    )

    return success_response(msg="患者注册成功", data={
        "id": new_user.id,
        "username": new_user.username,
        "phone_number": new_user.phone_number
    })


@router.post("/patient/bind")
async def bind_patient(
    phone_number: str = Form(..., description="患者手机号"),
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """医生绑定已有患者"""
    user = await User.filter(
        phone_number=phone_number,
        deleted_at__isnull=True
    ).first()

    if not user:
        return error_response(code="10004", msg="患者不存在")

    if user.responsible_doctor_id:
        return error_response(code="30005", msg="该患者已绑定其他医生")

    user.responsible_doctor_id = current_doctor["user_id"]
    await user.save()

    return success_response(msg="绑定成功")


@router.get("/patients")
async def list_patients(
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """获取当前医生的所有患者"""
    patients = await User.filter(
        responsible_doctor_id=current_doctor["user_id"],
        deleted_at__isnull=True
    ).all()

    patient_list = []
    for p in patients:
        patient_list.append({
            "id": p.id,
            "username": p.username,
            "phone_number": p.phone_number,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None
        })

    return success_response(data=patient_list)


@router.post("/report")
async def submit_diagnosis_report(
    record_id: str = Form(..., description="记录ID"),
    text: str = Form(..., description="诊断内容"),
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """医生提交诊断报告"""
    from datetime import datetime
    
    report = await AIDiagnosisReport.filter(id=record_id).first()
    
    if not report:
        return error_response(code="40001", msg="诊断记录不存在")
    
    report.suggestions = text
    report.doctor_id = current_doctor["user_id"]
    report.report_status = "reviewed"
    report.reviewed_at = datetime.now()
    await report.save()
    
    return success_response(msg="诊断报告提交成功", data={
        "id": report.id,
        "status": report.report_status
    })


@router.get("/summary/{record_id}")
async def get_patient_summary(
    record_id: str,
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """获取患者诊断详情"""
    report = await AIDiagnosisReport.filter(id=record_id).first()
    
    if not report:
        return error_response(code="40001", msg="诊断记录不存在")
    
    patient = await User.filter(id=report.patient_id).first()
    
    return success_response(data={
        "record_id": report.id,
        "patient": {
            "id": patient.id if patient else None,
            "username": patient.username if patient else None,
            "phone_number": patient.phone_number if patient else None
        },
        "chief_complaint": report.chief_complaint,
        "symptoms": report.symptoms,
        "possible_diagnosis": report.possible_diagnosis,
        "suggestions": report.suggestions,
        "severity": report.severity,
        "status": report.report_status,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None
    })