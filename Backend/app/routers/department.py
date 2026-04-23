from fastapi import APIRouter, Depends, HTTPException
from tortoise.exceptions import DoesNotExist
from app.database_tortoise import get_db
from app.models.department import Department
from app.utils import success_response, error_response, get_current_doctor

router = APIRouter(tags=["科室模块"])


@router.get("/list")
async def list_departments(
    db = Depends(get_db)
):
    """获取所有科室列表"""
    try:
        departments = await Department.filter(
            deleted_at__isnull=True
        ).order_by("name")
        
        dept_list = [
            {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "description": dept.description
            }
            for dept in departments
        ]
        
        return success_response(data=dept_list)
    except Exception as e:
        return error_response(code="20001", msg=f"获取科室列表失败: {str(e)}")


@router.get("/{dept_id}")
async def get_department(
    dept_id: str,
    db = Depends(get_db)
):
    """获取单个科室信息"""
    try:
        dept = await Department.get(id=dept_id, deleted_at__isnull=True)
        return success_response(data={
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description
        })
    except DoesNotExist:
        return error_response(code="20002", msg="科室不存在")


@router.post("/create")
async def create_department(
    name: str,
    code: str,
    description: str = None,
    current_doctor: dict = Depends(get_current_doctor),
    db = Depends(get_db)
):
    """创建科室"""
    try:
        existing = await Department.filter(code=code, deleted_at__isnull=True).first()
        if existing:
            return error_response(code="20003", msg="科室代码已存在")
        
        dept = await Department.create(
            name=name,
            code=code,
            description=description
        )
        
        return success_response(msg="科室创建成功", data={
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description
        })
    except Exception as e:
        return error_response(code="20001", msg=f"创建科室失败: {str(e)}")
