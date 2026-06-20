"""GDPR 最小合规测试 (P2-8) — 9+ 项。

覆盖:
- anonymize_birth 纯函数: Birth dataclass 脱敏
- anonymize_pii: BirthModel 脱敏 (已有功能, 回归测试)
- GET /api/users/me/data: 访问权端点
- POST /api/users/me/delete: 删除权端点
- 边界: None/lat/lng/0 hour
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from divination.contracts import Birth
from divination.interpret.anonymize import (
    _quantize_hour,
    _round_coord,
    _redact_name_like,
    anonymize_birth,
    anonymize_pii,
)
from server.main import app

client = TestClient(app)


# ── 测试数据 ──

FULL_BIRTH = Birth(
    year=1990, month=5, day=15, hour=8, minute=30,
    gender="male", calendar="gregorian",
    lat=31.2345, lng=121.4789, tz="Asia/Shanghai",
)

NO_COORDS_BIRTH = Birth(
    year=2000, month=1, day=1, hour=0, minute=0,
    gender="female", calendar="gregorian",
    lat=None, lng=None, tz="UTC",
)


# ═══════════════════════════════════════════════════════════════════════════════
# 单元测试: anonymize 内部函数
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuantizeHour:
    """_quantize_hour: 四舍五入到 2h 时辰。"""

    def test_quantize_zero_stays_zero(self):
        assert _quantize_hour(0) == 0

    def test_quantize_one_rounds_to_two(self):
        assert _quantize_hour(1) == 2

    def test_quantize_two_stays_two(self):
        assert _quantize_hour(2) == 2

    def test_quantize_eleven_rounds_to_twelve(self):
        assert _quantize_hour(11) == 12

    def test_quantize_twenty_three_rounds_to_twenty_two(self):
        """23 时 → 22 (边界, 24→22 clamp)"""
        assert _quantize_hour(23) == 22

    def test_quantize_twenty_two_stays_twenty_two(self):
        assert _quantize_hour(22) == 22

    def test_quantize_negative_clamps_to_zero(self):
        assert _quantize_hour(-5) == 0

    def test_quantize_above_23_clamps_to_22(self):
        assert _quantize_hour(99) == 22


class TestRoundCoord:
    """_round_coord: 坐标精度降至 0.1°。"""

    def test_round_coord_keeps_one_decimal(self):
        assert _round_coord(31.2345) == 31.2

    def test_round_coord_whole_number(self):
        assert _round_coord(121.0) == 121.0

    def test_round_coord_negative(self):
        assert _round_coord(-74.0123) == -74.0

    def test_round_coord_none_returns_none(self):
        assert _round_coord(None) is None

    def test_round_coord_custom_digits(self):
        assert _round_coord(31.2345, digits=2) == 31.23


class TestRedactNameLike:
    """_redact_name_like: 保留首字 + '**'。"""

    def test_redact_normal_name(self):
        assert _redact_name_like("张三丰") == "张**"

    def test_redact_two_chars(self):
        assert _redact_name_like("李四") == "李**"

    def test_redact_single_char(self):
        assert _redact_name_like("张") == "**"

    def test_redact_empty(self):
        assert _redact_name_like("") == ""

    def test_redact_none(self):
        assert _redact_name_like(None) is None

    def test_redact_english_name(self):
        assert _redact_name_like("Alice") == "A**"


# ═══════════════════════════════════════════════════════════════════════════════
# 单元测试: anonymize_birth (Birth dataclass)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnonymizeBirth:
    """anonymize_birth: Birth dataclass 脱敏 (P2-8 新增)。"""

    def test_anonymize_birth_quantizes_hour(self):
        result = anonymize_birth(FULL_BIRTH)
        assert result.hour == 8  # 8 在 8-9 区间保持 8
        assert result.minute == 0

    def test_anonymize_birth_rounds_coords(self):
        result = anonymize_birth(FULL_BIRTH)
        assert result.lat == 31.2
        assert result.lng == 121.5

    def test_anonymize_birth_preserves_year_month_day(self):
        result = anonymize_birth(FULL_BIRTH)
        assert result.year == 1990
        assert result.month == 5
        assert result.day == 15

    def test_anonymize_birth_preserves_gender_calendar_tz(self):
        result = anonymize_birth(FULL_BIRTH)
        assert result.gender == "male"
        assert result.calendar == "gregorian"
        assert result.tz == "Asia/Shanghai"

    def test_anonymize_birth_does_not_mutate_original(self):
        original_minute = FULL_BIRTH.minute
        original_lat = FULL_BIRTH.lat
        anonymize_birth(FULL_BIRTH)
        assert FULL_BIRTH.minute == original_minute
        assert FULL_BIRTH.lat == original_lat

    def test_anonymize_birth_handles_none_coords(self):
        result = anonymize_birth(NO_COORDS_BIRTH)
        assert result.lat is None
        assert result.lng is None

    def test_anonymize_birth_hour_one_rounds_to_two(self):
        b = Birth(year=2000, month=6, day=15, hour=1, minute=45,
                  gender="unspecified", calendar="gregorian",
                  lat=None, lng=None, tz="UTC")
        result = anonymize_birth(b)
        assert result.hour == 2
        assert result.minute == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 回归测试: anonymize_pii (BirthModel, 已有功能)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnonymizePii:
    """anonymize_pii: BirthModel Pydantic 脱敏 (已有功能回归)。"""

    def test_anonymize_pii_none_returns_none(self):
        assert anonymize_pii(None) is None

    def test_anonymize_pii_quantizes_birthmodel(self):
        from divination.aggregation.schema import BirthModel
        bm = BirthModel(year=1990, month=6, day=15, hour=9, minute=30,
                        gender="female", calendar="gregorian",
                        lat=31.234, lng=121.478, tz="Asia/Shanghai")
        result = anonymize_pii(bm)
        assert result is not None
        assert result.hour == 10  # 9 → 10
        assert result.minute == 0
        assert result.lat == 31.2
        assert result.lng == 121.5


# ═══════════════════════════════════════════════════════════════════════════════
# API 集成测试: /api/users/me/data 与 /api/users/me/delete
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersAPI:
    """GDPR 用户端点集成测试。"""

    def test_get_user_data_no_params(self):
        """GET /api/users/me/data 无参数返回说明。"""
        response = client.get("/api/users/me/data")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "data_retained" in data
        assert "retention_policy" in data
        assert "request_id" in data

    def test_get_user_data_with_birth_params(self):
        """GET /api/users/me/data 带出生参数返回脱敏数据。"""
        response = client.get("/api/users/me/data", params={
            "year": "1990", "month": "5", "day": "15",
            "hour": "9", "minute": "30",
            "gender": "male", "calendar": "gregorian",
            "lat": "31.234", "lng": "121.478",
            "tz": "Asia/Shanghai",
        })
        assert response.status_code == 200
        data = response.json()
        retained = data["data_retained"]
        assert retained["hour"] == 10  # 9 → 10, 量化到 2h
        assert retained["minute"] == 0
        assert retained["lat"] == 31.2
        assert retained["lng"] == 121.5
        assert retained["year"] == 1990
        assert retained["month"] == 5
        assert retained["day"] == 15
        assert retained["gender"] == "male"

    def test_get_user_data_with_invalid_params_graceful(self):
        """GET /api/users/me/data 无效参数不崩溃。"""
        response = client.get("/api/users/me/data", params={
            "year": "not_a_number",
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data

    def test_post_delete_user_data(self):
        """POST /api/users/me/delete 返回删除确认。"""
        response = client.post("/api/users/me/delete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert "deleted_fields" in data
        assert isinstance(data["deleted_fields"], list)
        assert len(data["deleted_fields"]) >= 1
        assert "message" in data
        assert "request_id" in data

    def test_delete_with_x_user_id_header(self):
        """POST /api/users/me/delete 带 X-User-Id 头返回相同 user_id。"""
        response = client.post(
            "/api/users/me/delete",
            headers={"X-User-Id": "test-user-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"

    def test_get_data_with_x_user_id_header(self):
        """GET /api/users/me/data 带 X-User-Id 头。"""
        response = client.get(
            "/api/users/me/data",
            headers={"X-User-Id": "test-user-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-456"

    def test_users_router_is_loaded(self):
        """确认 /api/users/me/data 端点已挂载。"""
        # 验证路由存在（404 vs 200）
        response = client.get("/api/users/me/data")
        assert response.status_code == 200
        # 确保不是 fallback
        assert response.json()["request_id"]

    def test_delete_is_idempotent(self):
        """多次调用 POST /api/users/me/delete 都返回相同状态。"""
        r1 = client.post("/api/users/me/delete").json()
        r2 = client.post("/api/users/me/delete").json()
        assert r1["status"] == r2["status"] == "deleted"
        assert r1["message"] == r2["message"]
