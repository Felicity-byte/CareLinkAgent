from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import ValidationError
import uuid
from app.database_tortoise import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserBind, UserLoginResponse
from app.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    success_response,
    error_response
)

router = APIRouter(tags=["用户模块"])


@router.post("/register")
async def register(
    phone_number: str = Form(..., min_length=11, max_length=11, description="手机号"),
    password: str = Form(..., min_length=6, max_length=72, description="密码，至少6位，最多72字节"),
    db = Depends(get_db)
):
    """用户注册

    支持 application/json 和 multipart/form-data 两种格式

    表单字段:
    - phone_number: 手机号（11位，1开头）
    - password: 密码（至少6位）
    """
    try:
        # 验证手机号格式
        import re
        if not re.match(r'^1[3-9]\d{9}$', phone_number):
            return error_response(code="10001", msg="手机号格式不正确")

        # 检查手机号是否已存在
        existing_user = await User.filter(
            phone_number=phone_number,
            deleted_at__isnull=True
        ).first()

        if existing_user:
            return error_response(code="10002", msg="手机号已被注册")

        # 创建新用户
        hashed_password = get_password_hash(password)
        new_user = await User.create(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            password=hashed_password,
            username=f"默认用户{phone_number}"
        )

        return success_response(msg="注册成功")
    except Exception as e:
        return error_response(code="10001", msg=f"注册失败: {str(e)}")


@router.post("/login")
async def login(
    phone_number: str = Form(..., min_length=11, max_length=11, description="手机号"),
    password: str = Form(..., min_length=6, max_length=72, description="密码"),
    db = Depends(get_db)
):
    """用户登录

    支持 application/json 和 multipart/form-data 两种格式

    表单字段:
    - phone_number: 手机号
    - password: 密码
    """
    # 验证手机号格式
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone_number):
        return error_response(code="10001", msg="手机号格式不正确")

    # 查找用户
    user = await User.filter(
        phone_number=phone_number,
        deleted_at__isnull=True
    ).first()

    if not user or not verify_password(password, user.password):
        return error_response(code="10003", msg="手机号或密码错误")

    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.id, "type": "user"}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "type": "user"}
    )

    return success_response(
        msg="登录成功",
        data={
            "token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "username": user.username,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
                "deleted_at": user.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None
            }
        }
    )


@router.get("/info")
async def get_user_info(
    user_id: str = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取用户信息"""
    # 如果没有提供user_id，使用当前用户ID
    target_user_id = user_id if user_id else current_user["user_id"]

    user = await User.filter(
        id=target_user_id,
        deleted_at__isnull=True
    ).first()

    if not user:
        return error_response(code="10004", msg="用户不存在")

    user_info = {
        "id": user.id,
        "phone_number": user.phone_number,
        "username": user.username,
        "gender": user.gender,
        "birth": user.birth,
        "ethnicity": user.ethnicity,
        "origin": user.origin,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
        "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
        "deleted_at": user.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None
    }

    return success_response(data=user_info)


@router.post("/bind")
async def bind_identity(
    username: str = Form(..., description="姓名"),
    gender: str = Form(..., description="性别"),
    birth: str = Form(..., description="出生年月日"),
    ethnicity: str = Form(..., description="民族"),
    origin: str = Form(..., description="籍贯"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """绑定身份证信息

    支持form-data和JSON两种格式
    """
    user = await User.filter(
        id=current_user["user_id"],
        deleted_at__isnull=True
    ).first()

    if not user:
        return error_response(code="10004", msg="用户不存在")

    # 更新用户信息
    await user.update_from_dict({
        "username": username,
        "gender": gender,
        "birth": birth,
        "ethnicity": ethnicity,
        "origin": origin
    })
    await user.save()

    return success_response(msg="绑定成功")


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

        user_id = payload.get("sub")
        user_type = payload.get("type", "user")

        if user_type == "user":
            user = await User.filter(id=user_id, deleted_at__isnull=True).first()
            if not user:
                return error_response(code="10004", msg="用户不存在")
        else:
            return error_response(code="10005", msg="无效的刷新令牌")

        new_access_token = create_access_token(
            data={"sub": user_id, "type": user_type}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user_id, "type": user_type}
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