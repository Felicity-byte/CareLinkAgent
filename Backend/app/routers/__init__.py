from app.routers.user import router as user_router
from app.routers.doctor import router as doctor_router
from app.routers.department import router as department_router
from app.routers.wound import router as wound_router
from app.routers.appointment import router as appointment_router

__all__ = [
    "user_router",
    "doctor_router",
    "department_router",
    "wound_router",
    "appointment_router"
]
