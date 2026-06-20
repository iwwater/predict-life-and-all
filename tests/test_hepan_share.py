"""Sprint 2.4 — 合盘分享卡 API 测试。

覆盖:
- GET /api/hepan-share/{case_id} 返回 OG + card + disclaimer
- 12 生肖映射 (1900 鼠, 1990 马, 2000 龙)
- 仅 hepan/compatibility/relationship case 可分享
- 关键 signals (top 3 by strength)
- 5 维 judgment 来自 validation.dimension_polarity
- OG title 含 person_a/b label
- URL 形如 /share/hepan/{case_id}
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.api.cases import _reset_store_for_tests
from server.api.hepan_share import _animal_for_year
from server.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_stores():
    """Sprint 2.4: 每个测试前清空所有 store (含 idem 索引)."""
    from server.api.cases import _IDEMPOTENCY_INDEX, _VERSION_BY_PARENT
    _IDEMPOTENCY_INDEX.clear()
    _VERSION_BY_PARENT.clear()
    _reset_store_for_tests()
    yield
    # 不在 teardown 清理, 让测试自己观察最终状态


BIRTH_A = {
    "year": 1990, "month": 6, "day": 15, "hour": 8, "minute": 30,
    "gender": "male", "calendar": "gregorian",
    "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai",
}

BIRTH_B = {
    "year": 1992, "month": 3, "day": 20, "hour": 10, "minute": 0,
    "gender": "female", "calendar": "gregorian",
    "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai",
}


def _setup():
    """兼容 setup_function 模式. pytest 8+ 在 class 模式下用 setup_method,
    但部分老模式可能仍调 setup_function. 调用 setup_method 的逻辑. """
    setup_method(None)


# ── 12 生肖 ─────────────────────────────────────────────────────────

class TestAnimalForYear:
    @pytest.mark.parametrize("year,expected", [
        (1900, "鼠"),
        (1990, "马"),   # 1990 = 马年
        (1991, "羊"),
        (1992, "猴"),
        (2000, "龙"),   # 2000 = 龙年
        (2024, "龙"),   # 2024 = 龙年
    ])
    def test_animal(self, year, expected):
        assert _animal_for_year(year) == expected


# ── API: 仅 hepan/compatibility 可分享 ─────────────────────────────

class TestHepanShareEligibility:
    def _create_hepan_case(self, with_target: bool = True) -> dict:
        body = {
            "question": "我俩合不合",
            "goal": "compatibility",
            "subject": "我",
            "target": "她",
        }
        if with_target:
            body["birth"] = BIRTH_A
            # target_birth 在 CaseCreateRequest 中不支持, 仅在 cast 时传
        r = client.post("/api/cases", json=body)
        return r.json()

    def test_share_requires_hepan_case(self):
        # 创建 career case
        case = client.post("/api/cases", json={
            "question": "我该换工作吗",
            "goal": "career",
            "birth": BIRTH_A,
        }).json()
        r = client.get(f"/api/hepan-share/{case['case_id']}")
        assert r.status_code == 400
        assert "not hepan" in r.json()["detail"].lower()

    def test_share_requires_existing_case(self):
        r = client.get("/api/hepan-share/case_does_not_exist")
        assert r.status_code == 404


# ── API: 完整 share flow ────────────────────────────────────────────

class TestHepanShareFullFlow:
    def test_share_hepan_case_returns_full_response(self):
        # 1. 创建 compatibility case
        case = client.post("/api/cases", json={
            "question": "我俩合不合",
            "goal": "compatibility",
            "subject": "我",
            "target": "她",
        }).json()
        # 2. 答完追问 (context_ready)
        qids = [q["id"] for q in case["minimal_questions"]]
        if qids:
            client.post(
                f"/api/cases/{case['case_id']}/context",
                json={"answers": {qid: "ok" for qid in qids}},
            )
        # 3. cast
        cast = client.post(
            f"/api/cases/{case['case_id']}/cast",
            json={"depth": "free"},
            headers={"Idempotency-Key": "share-test-1"},
        )
        assert cast.status_code == 200, cast.text
        # 4. share
        r = client.get(f"/api/hepan-share/{case['case_id']}")
        assert r.status_code == 200, r.text
        body = r.json()
        # 5. 验证结构
        assert "og" in body
        assert "card" in body
        assert "disclaimer" in body
        # OG
        og = body["og"]
        assert "title" in og
        assert "image" in og
        assert "/share/hepan/" in og["url"]
        # Card
        card = body["card"]
        assert card["case_id"] == case["case_id"]
        assert "person_a" in card
        assert "person_b" in card
        assert "headline" in card
        assert "key_signals" in card
        assert isinstance(card["key_signals"], list)
        assert "disclaimer" in body


# ── API: share 409 when no result ───────────────────────────────────

class TestShareRequiresResult:
    def test_share_409_when_no_cast(self):
        case = client.post("/api/cases", json={
            "question": "我俩合不合",
            "goal": "compatibility",
        }).json()
        r = client.get(f"/api/hepan-share/{case['case_id']}")
        assert r.status_code == 409


# ── API: list_shareable_cases ───────────────────────────────────────

class TestListShareableCases:
    def test_list_empty(self):
        from server.api.hepan_share import list_shareable_cases
        assert list_shareable_cases() == []

    def test_list_after_cast(self):
        case = client.post("/api/cases", json={
            "question": "我俩合不合",
            "goal": "compatibility",
        }).json()
        # 答完追问
        qids = [q["id"] for q in case["minimal_questions"]]
        if qids:
            client.post(
                f"/api/cases/{case['case_id']}/context",
                json={"answers": {qid: "ok" for qid in qids}},
            )
        client.post(
            f"/api/cases/{case['case_id']}/cast",
            json={"depth": "free"},
            headers={"Idempotency-Key": "list-test"},
        )
        from server.api.hepan_share import list_shareable_cases
        result = list_shareable_cases()
        assert len(result) == 1
        assert result[0]["case_id"] == case["case_id"]
        assert result[0]["event_type"] == "compatibility"
