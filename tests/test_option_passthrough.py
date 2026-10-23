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


# ── 六爻 / 灵签 / 奇门: mode 不再是装饰 ────────────────────────────────────

def test_liuyao_string_tosses_rejected(client):
    """字符串枚举 ("old_yin"...) 让引擎的 `t in (7,9)` 恒 False → 永远坤为地零动爻。

    这种请求必须 422 拒掉, 不能静默算一个错卦。
    """
    st, body = _post(client, "liuyao", {
        "mode": "manual_coin", "question": "测试",
        "tosses": ["old_yin", "young_yin", "young_yang", "old_yang", "young_yin", "young_yang"],
    })
    assert st == 422, body
    assert "tosses" in str(body["detail"])


def test_liuyao_manual_coin_int_tosses_move_yao(client):
    """int 掷币 [6,7,8,9,7,8]: 动爻必须在第 1、4 爻, 而不是全静坤为地。"""
    st, body = _post(client, "liuyao", {"mode": "manual_coin", "question": "测试", "tosses": [6, 7, 8, 9, 7, 8]})
    assert st == 200, body
    raw = body["raw"]
    assert raw["摇钱"] == [6, 7, 8, 9, 7, 8]
    assert raw["动爻"] == [1, 4]
    assert raw["本卦"] != "坤为地"
    assert raw["变卦"] is not None


def test_liuyao_number_qigua_requires_seed(client):
    st, _ = _post(client, "liuyao", {"mode": "number_qigua", "question": "测试"})
    assert st == 422


def test_qian_manual_number_requires_qian_number(client):
    """mode=manual_number 不给签号 → 422, 而不是静默变随机抽。"""
    st, _ = _post(client, "qian", {"mode": "manual_number", "question": "测试"})
    assert st == 422


def test_qimen_day_qimen_maps_to_pan_type(client):
    """day_qimen 是引擎真支持的盘型 (模拟层), mode 应映射成 pan_type=day。"""
    st, body = _post(client, "qimen", {"mode": "day_qimen", "question": "测试"})
    assert st == 200, body
    pan_info = body["raw"]["pan_info"]
    assert pan_info["pan_type"] == "day"
    assert pan_info.get("fallback_simulated") is True


def test_qimen_minute_qimen_rejected(client):
    """引擎没有刻家奇门, 谁再发 minute_qimen 就 422 —— 之前会静默出时家盘冒充。"""
    st, _ = _post(client, "qimen", {"mode": "minute_qimen", "question": "测试"})
    assert st == 422


def test_engine_valueerror_is_422_not_500(client):
    """引擎主动拒绝输入 (外应起卦字数不足) 是客户端问题, 不该是 500。"""
    st, body = _post(client, "meihua", {"mode": "external_omen", "question": "好"})
    assert st == 422, body
