"""P0-2 收口回归: CORS 白名单 / 烧钱端点限流 / 可选 API Key / 422 不回显输入。

这些测试都通过临时改环境变量来验证, 不依赖部署形态 —— 默认(无 env)保持开发友好,
设置了 env 才收紧。
"""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

import server.main as main_module
from server import security


@pytest.fixture()
def client():
    security.reset_rate_limits_for_tests()
    return TestClient(main_module.app)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYSTIC_RATE_LIMIT_PER_MIN", "MYSTIC_API_KEY", "MYSTIC_CORS_ORIGINS"):
        monkeypatch.delenv(key, raising=False)
    security.reset_rate_limits_for_tests()
    yield
    security.reset_rate_limits_for_tests()


# ── CORS 来源可配置 ──────────────────────────────────────────────────────────

def test_cors_origins_default_open_for_dev(monkeypatch):
    monkeypatch.delenv("MYSTIC_CORS_ORIGINS", raising=False)
    assert security.cors_origins() == ["*"]


def test_cors_origins_whitelist_from_env(monkeypatch):
    monkeypatch.setenv("MYSTIC_CORS_ORIGINS", "https://a.example, https://b.example ,")
    assert security.cors_origins() == ["https://a.example", "https://b.example"]


# ── 限流 ────────────────────────────────────────────────────────────────────

def test_rate_limit_off_by_default(client):
    for _ in range(30):
        assert client.get("/health").status_code == 200


def test_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setenv("MYSTIC_RATE_LIMIT_PER_MIN", "2")
    security.reset_rate_limits_for_tests()
    payload = {"question": "我今年适合换工作吗", "birth": {"year": 1990, "month": 6, "day": 15, "hour": 8}}
    codes = [client.post("/api/reading", json=payload).status_code for _ in range(3)]
    # 前两次放行(可能是 200/422, 但不是 429), 第三次被拦
    assert 429 not in codes[:2], codes
    assert codes[2] == 429
    blocked = client.post("/api/reading", json=payload)
    assert blocked.headers.get("Retry-After")
    assert blocked.json()["limit"] == 2


def test_rate_limit_does_not_block_cheap_get(client, monkeypatch):
    monkeypatch.setenv("MYSTIC_RATE_LIMIT_PER_MIN", "1")
    security.reset_rate_limits_for_tests()
    payload = {"question": "测试问题", "birth": {"year": 1990, "month": 6, "day": 15, "hour": 8}}
    assert client.post("/api/reading", json=payload).status_code != 429
    assert client.post("/api/reading", json=payload).status_code == 429
    # 排盘/元数据这类不烧钱的 GET 仍然放行
    for _ in range(5):
        assert client.get("/api/methods").status_code == 200


# ── 可选 API Key ────────────────────────────────────────────────────────────

def test_api_key_disabled_by_default(client):
    assert client.post("/api/cases", json={"question": "默认不需要 key"}).status_code in (200, 201)


def test_api_key_required_for_writes_when_configured(client, monkeypatch):
    monkeypatch.setenv("MYSTIC_API_KEY", "s3cret")
    denied = client.post("/api/cases", json={"question": "没有 key"})
    assert denied.status_code == 401
    assert denied.json()["detail"]
    ok = client.post(
        "/api/cases",
        json={"question": "带 key 的写入"},
        headers={"X-API-Key": "s3cret"},
    )
    assert ok.status_code in (200, 201)
    # GET 不受影响(公开只读)
    assert client.get("/api/methods").status_code == 200


def test_api_key_wrong_value_rejected(client, monkeypatch):
    monkeypatch.setenv("MYSTIC_API_KEY", "s3cret")
    resp = client.post("/api/cases", json={"question": "错 key"}, headers={"X-API-Key": "nope"})
    assert resp.status_code == 401


# ── 422 不回显用户输入 ──────────────────────────────────────────────────────

def test_validation_error_does_not_echo_input(client):
    resp = client.post("/api/compute", json={"method": "bazi", "birth": {"year": "not-a-year"}})
    assert resp.status_code == 422
    body = resp.text
    assert "input_value" not in body
    assert "not-a-year" not in body
    payload = resp.json()
    assert isinstance(payload["detail"], list)
    assert payload["detail"][0]["loc"]


# ── case store 有界 + 会过期 ────────────────────────────────────────────────

def test_case_store_respects_cap(client, monkeypatch):
    import server.api.cases as cases_api

    monkeypatch.setattr(cases_api, "_MAX_CASES", 3)
    monkeypatch.setattr(cases_api, "_CASE_TTL_SECONDS", 3600.0)
    cases_api._CASES.clear()
    cases_api._IDEMPOTENCY_INDEX.clear()
    cases_api._VERSION_BY_PARENT.clear()
    cases_api._RESULTS.clear()

    for i in range(6):
        r = client.post("/api/cases", json={"question": f"第 {i} 个问题", "goal": "career"}, params={"idempotent": False})
        assert r.status_code in (200, 201)

    assert len(cases_api._CASES) <= 3
    assert len(cases_api._CASES) == 3


def test_case_store_evicts_expired(monkeypatch):
    import server.api.cases as cases_api

    monkeypatch.setattr(cases_api, "_MAX_CASES", 100)
    monkeypatch.setattr(cases_api, "_CASE_TTL_SECONDS", 3600.0)
    cases_api._CASES.clear()
    cases_api._IDEMPOTENCY_INDEX.clear()
    cases_api._VERSION_BY_PARENT.clear()

    client = TestClient(main_module.app)
    resp = client.post("/api/cases", json={"question": "会过期的 case"})
    assert resp.status_code in (200, 201)
    assert cases_api._CASES, "case 应该先被创建"

    # TTL 归零后再裁剪一次: 所有记录立即过期
    monkeypatch.setattr(cases_api, "_CASE_TTL_SECONDS", 0.0)
    cases_api._prune_store()
    assert cases_api._CASES == {}
    assert cases_api._IDEMPOTENCY_INDEX == {}
