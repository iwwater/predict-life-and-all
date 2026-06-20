# -*- coding: utf-8 -*-
"""Extended Knowledge API tests — 4 new endpoints.

覆盖:
  GET /api/knowledge/pengzu?day_ganzhi=癸亥
  GET /api/knowledge/xingming?surname=李&given_name=梓涵
  GET /api/knowledge/sihua?year_gan=甲
  GET /api/knowledge/pailong?sitting=壬&facing=丙&dragon=子
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


# ── 1. 彭祖百忌 ──────────────────────────────────────────────


def test_pengzu_valid_day():
    """GET /api/knowledge/pengzu?day_ganzhi=癸亥 → 200."""
    r = client.get("/api/knowledge/pengzu", params={"day_ganzhi": "癸亥"})
    assert r.status_code == 200
    body = r.json()
    assert body["day_gan"] == "癸"
    assert body["day_zhi"] == "亥"
    assert "癸不词讼" in body["stem_taboo"]["full_text"]
    assert "亥不嫁娶" in body["branch_taboo"]["full_text"]
    assert "理弱敌强" in body["summary"]


@pytest.mark.parametrize("day_ganzhi", ["甲子", "癸亥", "己卯", "壬午", "辛酉"])
def test_pengzu_canonical_5_days(day_ganzhi):
    """5 个已知日干支."""
    r = client.get("/api/knowledge/pengzu", params={"day_ganzhi": day_ganzhi})
    assert r.status_code == 200
    body = r.json()
    assert body["day_gan"] == day_ganzhi[0]
    assert body["day_zhi"] == day_ganzhi[1]
    # 摘要应同时含干忌 + 支忌
    assert body["summary"].count("；") >= 1


def test_pengzu_invalid_gan():
    """无效天干 → 422."""
    r = client.get("/api/knowledge/pengzu", params={"day_ganzhi": "X亥"})
    assert r.status_code == 422


def test_pengzu_invalid_zhi():
    """无效地支 → 422."""
    r = client.get("/api/knowledge/pengzu", params={"day_ganzhi": "癸X"})
    assert r.status_code == 422


def test_pengzu_too_short():
    """长度不足 → 422."""
    r = client.get("/api/knowledge/pengzu", params={"day_ganzhi": "甲"})
    assert r.status_code == 422


# ── 2. 三才五格 ──────────────────────────────────────────────


@pytest.mark.parametrize("surname,given", [
    ("李", "梓涵"), ("王", "宇轩"), ("陈", "静"),
    ("张", "嘉慧"), ("司马", "晓晗"),
])
def test_xingming_canonical_5_names(surname, given):
    """5 个已知姓名 → 200 + 完整五格."""
    r = client.get("/api/knowledge/xingming", params={"surname": surname, "given_name": given})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["surname"] == surname
    assert body["given_name"] == given
    for k in ("tiange", "renge", "dige", "waige", "zongge", "san_cai", "overall"):
        assert k in body, f"missing key: {k}"
    # 五格每一格应含 num/wuxing/luck/meaning
    for k in ("tiange", "renge", "dige", "waige", "zongge"):
        assert "num" in body[k]
        assert "wuxing" in body[k]
        assert "luck" in body[k]


def test_xingming_empty_surname():
    """姓氏为空 → 422."""
    r = client.get("/api/knowledge/xingming", params={"surname": "", "given_name": "梓涵"})
    assert r.status_code == 422


# ── 3. 紫微四化 ──────────────────────────────────────────────


@pytest.mark.parametrize("year_gan,lu_star", [
    ("甲", "廉贞"), ("乙", "天机"), ("壬", "天梁"),
    ("丁", "太阴"), ("癸", "破军"),
])
def test_sihua_canonical_5_gans(year_gan, lu_star):
    """5 个已知年干 → 200 + 禄位正确."""
    r = client.get("/api/knowledge/sihua", params={"year_gan": year_gan})
    assert r.status_code == 200
    body = r.json()
    assert body["year_gan"] == year_gan
    assert body["sihua"]["禄"] == lu_star
    assert "star_meanings" in body
    assert len(body["star_meanings"]) == 4  # 禄/权/科/忌 各一星


def test_sihua_invalid_gan():
    """无效天干 → 422."""
    r = client.get("/api/knowledge/sihua", params={"year_gan": "X"})
    assert r.status_code == 422


def test_sihua_too_long():
    """多于 1 字 → 422."""
    r = client.get("/api/knowledge/sihua", params={"year_gan": "甲子"})
    assert r.status_code == 422


# ── 4. 玄空排龙诀 ────────────────────────────────────────────


def test_pailong_valid():
    """GET /api/knowledge/pailong?sitting=壬&facing=丙&dragon=子 → 200."""
    r = client.get("/api/knowledge/pailong", params={"sitting": "壬", "facing": "丙", "dragon": "子"})
    assert r.status_code == 200
    body = r.json()
    assert body["sitting"] == "壬"
    assert body["facing"] == "丙"
    assert body["coming_dragon"] == "子"
    assert "luck" in body
    assert "pattern" in body
    assert "meaning" in body
    # 壬丙子 同属坎卦(壬,子)+离卦(丙,离) -> 不同卦
    assert body["sit_gua"] == "坎"
    assert body["fac_gua"] == "離"


def test_pailong_same_gua_pure():
    """坐山=子,向=午,来龙=子 同属坎/离/坎 → 一卦纯清? (子午不属同卦)."""
    r = client.get("/api/knowledge/pailong", params={"sitting": "子", "facing": "子", "dragon": "子"})
    assert r.status_code == 200
    body = r.json()
    assert body["same_gua_all"] is True
    assert body["yuan_long_match"] is True
    assert body["luck"] == "大吉"


def test_pailong_invalid_shan():
    """无效山 → 422."""
    r = client.get("/api/knowledge/pailong", params={"sitting": "X", "facing": "丙", "dragon": "子"})
    assert r.status_code == 422


def test_pailong_missing_param():
    """缺少参数 → 422."""
    r = client.get("/api/knowledge/pailong", params={"sitting": "壬", "facing": "丙"})
    assert r.status_code == 422


# ── 路由注册检查 ──────────────────────────────────────────────


def test_all_four_endpoints_registered():
    """All 4 new endpoints should be discoverable in the OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/knowledge/pengzu" in paths
    assert "/api/knowledge/xingming" in paths
    assert "/api/knowledge/sihua" in paths
    assert "/api/knowledge/pailong" in paths