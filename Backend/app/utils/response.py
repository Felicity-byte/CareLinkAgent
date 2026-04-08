from typing import Optional, Any
from fastapi.responses import JSONResponse
from app.schemas.base import BaseResponse, ResponseWithData


def success_response(
    msg: str = "success",
    data: Optional[Any] = None
) -> dict:
    response = {
        "base": {
            "code": "10000",
            "msg": msg
        },
        "data": data
    }
    return response


def error_response(
    code: str = "10001",
    msg: str = "error",
    status_code: int = 200
) -> JSONResponse:
    content = {
        "base": {
            "code": code,
            "msg": msg
        },
        "data": None
    }
    return JSONResponse(status_code=status_code, content=content)
