from app.schemas.base import BaseResponse, ResponseWithData
from app.schemas.user import (
    UserRegister, UserLogin, UserBind, UserInfo, UserLoginResponse
)
from app.schemas.doctor import (
    DoctorLogin, DoctorInfo, DoctorReport
)
from app.schemas.department import (
    DepartmentCreate, DepartmentInfo, DepartmentList
)

__all__ = [
    "BaseResponse",
    "ResponseWithData",
    "UserRegister",
    "UserLogin",
    "UserBind",
    "UserInfo",
    "UserLoginResponse",
    "DoctorLogin",
    "DoctorInfo",
    "DoctorReport",
    "DepartmentCreate",
    "DepartmentInfo",
    "DepartmentList",
]
