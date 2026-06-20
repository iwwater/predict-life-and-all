"""GDPR 数据最小化 (PII 脱敏) — 送 LLM 前脱敏 PII。

GDPR-003: anonymize_pii(birth) -> Birth,纯函数,无副作用。

脱敏策略:
- 出生时间四舍五入到时辰 (2 小时精度): minute=0, hour 量化到 0/2/4/.../22
- 经纬度精度降到 0.1°: lat/lng 保留 1 位小数
- user_id 字段移除 (若 Birth 上有)

不耦合 LLM 客户端 — 仅依赖 divination.aggregation.schema.BirthModel。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from divination.aggregation.schema import BirthModel
    from divination.contracts import Birth


# 时辰单位 = 2 小时; 0,2,4,...,22
_HOUR_QUANTUM = 2


def _quantize_hour(hour: int) -> int:
    """四舍五入到时辰 (2h 精度)。

    例: 0→0, 1→2, 2→2, 9→10, 10→10, 11→12, 23→22, 22→22

    注: 用 int(hour / 2 + 0.5) * 2 而非 round(), 避免银行家舍入。
    """
    if hour < 0:
        hour = 0
    if hour > 23:
        hour = 23
    # 四舍五入到最近的 _HOUR_QUANTUM 倍数 (避免 banker's rounding)
    quantized = int(hour / _HOUR_QUANTUM + 0.5) * _HOUR_QUANTUM
    # 边界: 24 → 22
    if quantized >= 24:
        quantized = 22
    return quantized


def _round_coord(value: float | None, digits: int = 1) -> float | None:
    """坐标精度降到指定位数 (默认 0.1°)。"""
    if value is None:
        return None
    return round(value, digits)


def _redact_name_like(value: str | None) -> str | None:
    """姓名/地址类字符串脱敏: 保留首字 + '**'。"""
    if value is None or not value:
        return value
    if len(value) <= 1:
        return "**"
    return f"{value[0]}**"


def anonymize_pii(birth: "BirthModel | None") -> "BirthModel | None":
    """脱敏 BirthModel 上的 PII 字段。

    纯函数: 接受 Birth 返回新的 Birth 实例, 不修改入参。
    None 入参 → None 出参。

    字段处理:
    - hour: 量化到 2h 精度 (0,2,4,...,22)
    - minute: 归零 (时辰级精度不需要分钟)
    - lat/lng: 精度降到 0.1° (仍可定位到城市, 但不暴露精确位置)
    - 其余字段 (year/month/day/gender/calendar/tz) 保留 — 这些是排盘必须
    """
    if birth is None:
        return None

    # 复制关键字段, 避免污染原对象
    data = birth.model_dump()

    # 时间脱敏
    data["hour"] = _quantize_hour(int(data.get("hour", 0)))
    data["minute"] = 0

    # 坐标脱敏
    if "lat" in data:
        data["lat"] = _round_coord(data["lat"])
    if "lng" in data:
        data["lng"] = _round_coord(data["lng"])

    # 重建 BirthModel — 触发 Pydantic 校验
    from divination.aggregation.schema import BirthModel

    return BirthModel(**data)


def anonymize_birth(birth: "Birth") -> "Birth":
    """脱敏 dataclass Birth 上的 PII 字段 (P2-8 GDPR 最小合规)。

    纯函数: 接受 divination.contracts.Birth 返回新的 Birth, 不修改入参。

    字段处理:
    - hour: 量化到 2h 精度 (0,2,4,...,22)
    - minute: 归零
    - lat/lng: 精度降到 0.1°
    - gender/calendar/tz: 保留
    """
    from copy import deepcopy

    from divination.contracts import Birth

    cleaned = deepcopy(birth)
    cleaned.hour = _quantize_hour(birth.hour)
    cleaned.minute = 0
    cleaned.lat = _round_coord(birth.lat)
    cleaned.lng = _round_coord(birth.lng)
    return cleaned


def anonymize_space_address(space: "SpaceModel | None") -> "SpaceModel | None":
    """脱敏 SpaceModel 上的地址字段。

    风水场景: 坐向/元运是排盘必须, 但具体地址 (address) 不送 LLM。
    """
    if space is None:
        return None

    from divination.aggregation.schema import SpaceModel

    data = space.model_dump()
    if data.get("address"):
        data["address"] = _redact_name_like(data["address"])
    return SpaceModel(**data)
