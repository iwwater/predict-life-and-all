"""options 必须真的传给引擎 —— 否则前端选的名字/牌阵/掷币数全被静默丢弃。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from divination.engines.tarot import SPREADS
from server.main import app

BIRTH = {
    "year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0,
    "gender": "unspecified", "calendar": "gregorian", "tz": "Asia/Shanghai",
}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _post(client, method, options):
    r = client.post("/api/compute", json={"method": method, "birth": BIRTH, "options": options})
    return r.status_code, r.json()


def test_tarot_spread_reaches_engine(client):
    """不同牌阵必须出不同盘面 (以前 options 被丢弃, 永远默认牌阵)。"""
    got = {}
    for spread in ("single", "three_card", "celtic_cross"):
        st, body = _post(client, "tarot", {"mode": "tarot_spread", "spread": spread, "question": "测试", "seed": 7})
        assert st == 200, body
        got[spread] = body["raw"]["牌阵名称"]
    assert len(set(got.values())) == 3, got
    assert got["single"] == SPREADS["single"]["名称"]


def test_numerology_name_reaches_engine(client):
    """填了姓名就该算出命运数 (以前 name 被丢弃, 永远只有生命灵数)。"""
    st, body = _post(client, "numerology", {"mode": "life_path", "name": "Zhang San"})
    assert st == 200, body
    raw = body["raw"]
    assert raw["life_path"]["number"] >= 1
    assert "destiny" in raw and raw["destiny"]["number"] >= 1
    assert "soul_urge" in raw and raw["soul_urge"]["number"] >= 1


def test_numerology_destiny_mode_primary(client):
    st, body = _post(client, "numerology", {"mode": "destiny", "name": "Zhang San"})
    assert st == 200, body
    assert body["raw"]["mode"] == "destiny"
    assert body["raw"]["primary"]["label"] == "命运数"
    assert body["raw"]["primary"]["number"] == body["raw"]["destiny"]["number"]


def test_numerology_mode_requires_name(client):
    """destiny/soul_urge 没有姓名时明确 422, 而不是假装算出一个 0。"""
    st, body = _post(client, "numerology", {"mode": "destiny"})
    assert st == 422
    assert "name" in str(body["detail"])


def test_numerology_chinese_name_falls_back(client):
    """中文名没有拉丁字母: 不伪造命运数, 给出备注并回落到生命灵数。"""
    st, body = _post(client, "numerology", {"mode": "destiny", "name": "张三"})
    assert st == 200, body
    raw = body["raw"]
    assert "destiny" not in raw
    assert raw["primary"]["label"] == "生命灵数"
    assert "备注" in raw


def test_unknown_option_still_rejected(client):
    st, _ = _post(client, "numerology", {"mode": "life_path", "definitely_not_an_option": 1})
    assert st == 422


def test_xuankong_period_passthrough(client):
    """玄空的运期以前也被丢弃, 现在应影响盘面。"""
    st1, a = _post(client, "xuankong", {"mode": "residential_xuankong", "period": 8, "sitting": "子"})
    st2, b = _post(client, "xuankong", {"mode": "residential_xuankong", "period": 9, "sitting": "子"})
    assert st1 == st2 == 200
    assert a["raw"] != b["raw"]
