"""Tests for 梅花易数 深化 (divination/engines/meihua.py)

深化项 (Sprint 3.x):
1. 错卦 (阴阳互变)
2. 综卦 (上下颠倒)
3. 卦气旺衰 (基于月令)
4. 八卦万物类象
5. 数字起卦模式
6. 综合解读
7. evidence_sources
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines import meihua
from divination.engines.meihua import (
    TRIGRAM_ATTRIBUTES,
    _cuo_gua,
    _five_hexagrams,
    _gua_attributes,
    _gua_qi_wang_shuai,
    _qigua_number,
    _qigua_time,
    _zong_gua,
    compute,
)


# ── 1. 错卦 (阴阳互变) ─────────────────────────────────────
def test_cuo_gua_inverts_all_lines():
    """错卦: 每爻 1↔0, 6 爻全变."""
    # 乾 111111 → 坤 000000
    assert _cuo_gua([1, 1, 1, 1, 1, 1]) == [0, 0, 0, 0, 0, 0]
    # 坎 010010 → 离 101101
    assert _cuo_gua([0, 1, 0, 0, 1, 0]) == [1, 0, 1, 1, 0, 1]
    # 混合
    assert _cuo_gua([1, 0, 1, 0, 1, 0]) == [0, 1, 0, 1, 0, 1]


def test_cuo_gua_is_self_inverse():
    """对错卦再取错卦 = 还原 (互为反函数)。"""
    lines = [1, 0, 1, 0, 1, 1]
    assert _cuo_gua(_cuo_gua(lines)) == lines


def test_five_hexagrams_cuo_present():
    """5 卦系统必须包含错卦。"""
    five = _five_hexagrams("乾", "坤", 3)
    assert "错卦" in five
    assert five["错卦"]["name"]  # 非空


# ── 2. 综卦 (上下颠倒) ─────────────────────────────────────
def test_zong_gua_reverses_order():
    """综卦: 爻序 1→6, 2→5, 3→4 (list(reversed))。"""
    assert _zong_gua([1, 2, 3, 4, 5, 6]) == [6, 5, 4, 3, 2, 1]
    assert _zong_gua([1, 0, 1, 0, 1, 0]) == [0, 1, 0, 1, 0, 1]
    assert _zong_gua([0, 0, 0, 0, 0, 0]) == [0, 0, 0, 0, 0, 0]


def test_zong_gua_is_self_inverse():
    """对综卦再取综卦 = 还原。"""
    lines = [1, 0, 1, 1, 0, 1]
    assert _zong_gua(_zong_gua(lines)) == lines


def test_five_hexagrams_zong_present():
    """5 卦系统必须包含综卦。"""
    five = _five_hexagrams("乾", "坤", 3)
    assert "综卦" in five
    assert five["综卦"]["name"]


# ── 3. 卦气旺衰 (月令) ─────────────────────────────────────
def test_wang_shuai_quarter_year():
    """春季 (寅月) 木旺"""
    res = _gua_qi_wang_shuai("震", "寅")  # 震属木
    assert res["五行"] == "木"
    assert res["状态"] == "旺"
    assert res["旺衰"] == "旺相"


def test_wang_shuai_wang_in_season():
    """夏季 (午月) 火旺, 木相"""
    res = _gua_qi_wang_shuai("离", "午")
    assert res["五行"] == "火"
    assert res["状态"] == "旺"
    assert res["旺衰"] == "旺相"


def test_wang_shuai_xiu_qiu_off_season():
    """冬季 (子月) 火死, 火处休囚。"""
    res = _gua_qi_wang_shuai("离", "子")  # 子月水旺, 火被克
    assert res["五行"] == "火"
    assert res["旺衰"] in ("休囚", "中平")


def test_wang_shuai_xiang_when_season_shengs():
    """木生火: 寅月木当令, 离火得木生 → 相"""
    res = _gua_qi_wang_shuai("离", "寅")
    assert res["五行"] == "火"
    assert res["状态"] == "相"


# ── 4. 八卦万物类象 ─────────────────────────────────────────
def test_all_eight_trigrams_have_attributes():
    """八卦万物类象必须覆盖全部 8 卦。"""
    required = {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"}
    assert required.issubset(set(TRIGRAM_ATTRIBUTES.keys()))


def test_qian_attributes_classical():
    """乾卦万物类象（《说卦传》'乾为天,为父,为金,为玉...'）"""
    q = _gua_attributes("乾")
    assert q["自然"] == "天"
    assert q["五行"] == "金"
    assert "父" in q["人物"]
    assert "马" in q["类象"]


def test_kun_attributes_classical():
    """坤卦万物类象（《说卦传》'坤为地,为母,为布,为牛...'）"""
    k = _gua_attributes("坤")
    assert k["自然"] == "地"
    assert k["五行"] == "土"
    assert "母" in k["人物"]
    assert "牛" in k["类象"]


def test_li_attributes_eyes_fire():
    """离卦: 火/目/中女（《说卦传》）"""
    l = _gua_attributes("离")
    assert "目" in l["身体"]
    assert l["五行"] == "火"


def test_kan_attributes_water_ears():
    """坎卦: 水/耳/中男"""
    k = _gua_attributes("坎")
    assert "耳" in k["身体"]
    assert k["五行"] == "水"


# ── 5. 数字起卦模式 ─────────────────────────────────────────
def test_qigua_number_basic():
    """数字起卦: n1=9(1→乾), n2=9(1→乾), n3=6"""
    r = _qigua_number(9, 9, 6)  # 9%8=1 → 乾
    assert r["up"] == "乾"
    assert r["low"] == "乾"
    assert r["moving"] == 6


def test_qigua_number_modulo_8():
    """数字取模 8 (余 0 取 8)"""
    # n1=17 → 17%8=1 → 乾, n2=25 → 25%8=1 → 乾
    r = _qigua_number(17, 25, None)
    assert r["up"] == "乾"
    assert r["low"] == "乾"
    # 动爻 = (17+25)%6 = 42%6 = 0 → 6
    assert r["moving"] == 6


def test_qigua_number_modulo_6():
    """动爻取模 6 (余 0 取 6)"""
    r = _qigua_number(10, 2, None)  # (10+2)%6 = 12%6 = 0 → 6
    assert r["moving"] == 6


def test_compute_number_mode():
    """compute() 支持 mode='number'"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b, mode="number", n1=10, n2=20, n3=3)
    assert r.method == "meihua"
    raw = r.raw
    assert "数字起卦" in raw["起卦方式"]
    assert raw["五卦系统"]["动爻"] == 3


def test_compute_time_mode_default():
    """compute() 默认 mode='time'"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=30)
    r = compute(b)
    assert r.method == "meihua"
    assert "时间起卦" in r.raw["起卦方式"]


# ── 6. 综合解读 + evidence_sources ──────────────────────────
def test_comprehensive_narrative_includes_5_gua():
    """综合解读文本必须包含 5 卦 (本/互/变/错/综)。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    narr = r.raw["综合解读"]
    for key in ("本卦", "互卦", "变卦", "错卦", "综卦"):
        assert key in narr


def test_evidence_sources_classical():
    """evidence_sources 必须引用《梅花易数》。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    sources = r.raw["evidence_sources"]
    assert any("梅花易数" in s for s in sources)
    assert any("邵雍" in s for s in sources)


def test_raw_contains_all_systems():
    """raw 必须包含 5 卦系统 + 断法 + 卦气 + 万物类象。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    raw = r.raw
    for key in ("五卦系统", "断法", "卦气旺衰", "万物类象"):
        assert key in raw, f"raw 缺少 {key}"
    assert "本卦" in raw["五卦系统"]
    assert "错卦" in raw["五卦系统"]
    assert "综卦" in raw["五卦系统"]


def test_judgement_ti_yong_present():
    """断法必须包含体卦、用卦、体用关系、总断。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    r = compute(b)
    j = r.raw["断法"]
    assert "体卦" in j
    assert "用卦" in j
    assert "体用关系" in j
    assert "总断" in j
    assert j["体用关系"] in ("生出(泄)", "比和", "克出", "生入(被生)", "克入(被克)")


def test_compute_invalid_mode_raises():
    """不支持的 mode 应该 raise ValueError。"""
    b = Birth(year=1990, month=5, day=15, hour=10, minute=0)
    with pytest.raises(ValueError, match="mode"):
        compute(b, mode="unknown")


def test_5_hexagrams_5_names():
    """5 卦系统返回 5 个卦名 (本/互/变/错/综)。"""
    five = _five_hexagrams("乾", "坤", 3)
    assert all(five[k]["name"] for k in ("本卦", "互卦", "变卦", "错卦", "综卦"))


def test_time_qigua_returns_valid():
    """时间起卦返回合法数据。"""
    r = _qigua_time(1990, 5, 15, 10, 30)
    assert r["up"] in {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"}
    assert r["low"] in {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"}
    assert 1 <= r["moving"] <= 6
    assert r["month_zhi"] in {"子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"}