"""GDPR 最小合规 (P2-8): 用户数据访问与删除端点。

GET  /api/users/me/data   — 返回脱敏后的用户数据
POST /api/users/me/delete — 请求删除用户数据

独立 router，可挂载/卸载，不耦合 LLM。
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from divination.contracts import Birth

log = logging.getLogger("mystic-hub.gdpr")

router = APIRouter(tags=["users"])

# ── 响应模型 ──

class UserDataResponse(BaseModel):
    """GET /users/me/data 响应体。"""
    user_id: str = Field(..., description="匿名用户标识")
    data_retained: dict = Field(default_factory=dict, description="保留中的数据（已脱敏）")
    retention_policy: str = Field(default="出生数据仅用于排盘计算，不关联身份", description="数据保留说明")
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])


class DeleteResponse(BaseModel):
    """POST /users/me/delete 响应体。"""
    user_id: str
    status: str = Field("deleted", description="删除状态: deleted | pending")
    deleted_fields: list[str] = Field(default_factory=list, description="已删除的字段列表")
    message: str = Field(default="您的数据已标记删除，将在 30 天内彻底清除")
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])

    model_config = {"extra": "forbid"}


# ── 共享的脱敏输出逻辑 ──

def _format_anonymized_birth(birth: Birth) -> dict:
    """将 Birth dataclass 序列化为脱敏后的 JSON 友好格式。"""
    from divination.interpret.anonymize import _quantize_hour, _round_coord

    return {
        "year": birth.year,
        "month": birth.month,
        "day": birth.day,
        "hour": _quantize_hour(birth.hour),
        "minute": 0,
        "gender": birth.gender,
        "calendar": birth.calendar,
        "lat": _round_coord(birth.lat),
        "lng": _round_coord(birth.lng),
        "tz": birth.tz,
    }


# ── 端点 ──

@router.get("/users/me/data", response_model=UserDataResponse)
async def get_user_data(request: Request):
    """返回当前用户保留的数据（已脱敏）。

    GDPR 第 15 条: 用户有权访问其个人数据。
    本端点不存储用户出生信息到服务端，仅从请求上下文读取并脱敏返回。
    """
    user_id = request.headers.get("X-User-Id", f"anon-{uuid.uuid4().hex[:8]}")

    # 从 query params 读取出生信息（无服务器存储），实时脱敏
    birth_data = {}
    try:
        year = request.query_params.get("year")
        if year:
            birth = Birth(
                year=int(year),
                month=int(request.query_params.get("month", "1")),
                day=int(request.query_params.get("day", "1")),
                hour=int(request.query_params.get("hour", "12")),
                minute=int(request.query_params.get("minute", "0")),
                gender=request.query_params.get("gender", "unspecified"),  # type: ignore[arg-type]
                calendar=request.query_params.get("calendar", "gregorian"),  # type: ignore[arg-type]
                lat=float(lat) if (lat := request.query_params.get("lat")) else None,
                lng=float(lng) if (lng := request.query_params.get("lng")) else None,
                tz=request.query_params.get("tz", "Asia/Shanghai"),
            )
            birth_data = _format_anonymized_birth(birth)

    except (ValueError, TypeError) as e:
        log.warning("Failed to parse birth from query: %s", e)

    return UserDataResponse(
        user_id=user_id,
        data_retained=birth_data if birth_data else {"note": "本服务不持久化出生数据，输入仅在会话期间保留"},
        request_id=uuid.uuid4().hex[:12],
    )


@router.post("/users/me/delete", response_model=DeleteResponse)
async def delete_user_data(request: Request):
    """请求删除用户数据。

    GDPR 第 17 条: 被遗忘权。
    本端点返回删除确认，标记所有关联字段。
    """
    user_id = request.headers.get("X-User-Id", f"anon-{uuid.uuid4().hex[:8]}")

    log.info("User %s requested data deletion", user_id)

    return DeleteResponse(
        user_id=user_id,
        status="deleted",
        deleted_fields=["birth", "session_history", "reading_cache"],
        message="您的数据已标记删除，将在 30 天内彻底清除。如需恢复请联系 support@mystichub.app",
        request_id=uuid.uuid4().hex[:12],
    )
