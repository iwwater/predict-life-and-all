"""Tests for 西方占星进阶点 (divination/data/western_arabic_parts.py)

来源：docs/CLASSICAL_SOURCES.md §7 西方占星
文献：Tetrabiblos (Arabic Parts), The Inner Sky (Lilith)
"""
from __future__ import annotations

import pytest

from divination.data.western_arabic_parts import (
    ARABIC_PARTS,
    LILITH_IN_SIGNS,
    PART_NAME_ALIASES,
    _is_day_chart,
    compute_all_main_lots,
    compute_arabic_part,
    compute_lilith,
)


# ── 1. Black Moon Lilith ─────────────────────────────────
def test_lilith_returns_full_dict():
    """compute_lilith 返回完整字段。"""
    r = compute_lilith(2026, 6, 18)
    required = {"lilith_lon", "lilith_sign", "computation", "retrograde", "orbit_period_years"}
    assert required <= set(r.keys())


def test_lilith_longitude_range():
    """Lilith 黄经必须 0-360。"""
    for y, m, d in [(2026, 6, 18), (1990, 5, 15), (2000, 1, 1)]:
        r = compute_lilith(y, m, d)
        assert 0 <= r["lilith_lon"] < 360


def test_lilith_retrograde():
    """Lilith 永远逆行 (作为远地点)。"""
    r = compute_lilith(2026, 6, 18)
    assert r["retrograde"] is True


def test_lilith_orbit_period():
    """轨道周期约 8.85 年（实测约 8 年 11 月）。"""
    r = compute_lilith(2026, 6, 18)
    assert 8.5 < r["orbit_period_years"] < 9.5


def test_lilith_known_2026():
    """2026-06-18 Lilith 位置应在巨蟹附近。"""
    r = compute_lilith(2026, 6, 18)
    # 90° 左右
    assert 80 < r["lilith_lon"] < 100, f"2026-06-18 Lilith 位置 {r['lilith_lon']}° 偏离预期"


def test_lilith_12_signs():
    """LILITH_IN_SIGNS 必须 12 星座全覆盖。"""
    required = {"白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
                "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"}
    assert required <= set(LILITH_IN_SIGNS.keys())


def test_lilith_sign_meaning_not_empty():
    """每星座 Lilith 含义非空。"""
    for sign, meaning in LILITH_IN_SIGNS.items():
        assert len(meaning) > 5, f"{sign}: 含义过短"


# ── 2. Arabic Parts 表 ────────────────────────────────
def test_arabic_parts_count():
    """7 个核心 Lots。"""
    assert len(ARABIC_PARTS) == 7


def test_arabic_parts_required_fields():
    """每个 Lot 必须含 name, formula_day, formula_night, meaning。"""
    required = {"name", "formula_day", "formula_night", "meaning"}
    for p in ARABIC_PARTS:
        missing = required - set(p.keys())
        assert not missing, f"{p.get('name')} 缺失: {missing}"


def test_part_name_aliases():
    """中英文别名映射必须 7 个。"""
    assert len(PART_NAME_ALIASES) >= 14  # 7 中文 + 7 英文


def test_part_name_aliases_classical():
    """经典别名: 福点 / 灵点 / 爱点 等。"""
    assert PART_NAME_ALIASES["福点"] == "Lot of Fortune"
    assert PART_NAME_ALIASES["灵点"] == "Lot of Spirit"
    assert PART_NAME_ALIASES["婚姻点"] == "Lot of Marriage"


# ── 3. 日生 vs 夜生判断 ─────────────────────────────
def test_is_day_chart_sun_1st_house():
    """太阳第 1 宫 → 日生 (1-6 宫为日生)。"""
    assert _is_day_chart(1) is True


def test_is_day_chart_sun_6th_house():
    """太阳第 6 宫 → 日生（边界）。"""
    assert _is_day_chart(6) is True


def test_is_day_chart_sun_7th_house():
    """太阳第 7 宫 → 夜生（7-12 宫为夜生）。"""
    assert _is_day_chart(7) is False


def test_is_day_chart_sun_12th_house():
    """太阳第 12 宫 → 夜生。"""
    assert _is_day_chart(12) is False


# ── 4. 单 Lot 计算 ──────────────────────────────────
def test_lot_of_fortune_day():
    """福点日生公式: ASC + Moon - Sun = 120 + 180 - 90 = 210°。"""
    r = compute_arabic_part("Lot of Fortune", asc_lon=120.0,
                            planet_lon=180.0, sun_lon=90.0, is_day=True)
    assert r["lot_lon"] == 210.0
    assert r["is_day_chart"] is True
    assert "ASC + Moon - Sun" in r["formula_used"]


def test_lot_of_fortune_night():
    """福点夜生公式: ASC + Sun - Moon = 120 + 90 - 180 = 30°。"""
    r = compute_arabic_part("Lot of Fortune", asc_lon=120.0,
                            planet_lon=180.0, sun_lon=90.0, is_day=False)
    assert r["lot_lon"] == 30.0
    assert r["is_day_chart"] is False
    assert "ASC + Sun - Moon" in r["formula_used"]


def test_lot_normalize():
    """Lot 黄经规范化到 0-360（即使公式结果为负）。"""
    r = compute_arabic_part("Lot of Fortune", asc_lon=10.0,
                            planet_lon=10.0, sun_lon=90.0, is_day=True)
    # 10 + 10 - 90 = -70, normalize → 290
    assert r["lot_lon"] == 290.0


def test_lot_chinese_alias():
    """中文别名查询: "福点" = "Lot of Fortune"。"""
    r = compute_arabic_part("福点", asc_lon=120.0,
                            planet_lon=180.0, sun_lon=90.0, is_day=True)
    assert r["part_name"] == "Lot of Fortune"
    assert r["part_name_cn"] == "福点"


def test_lot_unknown_name():
    """未知 Lot 名称 → ValueError。"""
    with pytest.raises(ValueError, match="未知 Lot"):
        compute_arabic_part("Lot of Wealth", asc_lon=120.0,
                            planet_lon=180.0, sun_lon=90.0, is_day=True)


def test_lot_eros():
    """爱点日生公式: ASC + Venus - Sun。"""
    r = compute_arabic_part("Lot of Eros", asc_lon=120.0,
                            planet_lon=110.0, sun_lon=90.0, is_day=True)
    # 120 + 110 - 90 = 140°
    assert r["lot_lon"] == 140.0


def test_lot_courage():
    """勇气点日生公式: ASC + Mars - Sun。"""
    r = compute_arabic_part("Lot of Courage", asc_lon=120.0,
                            planet_lon=200.0, sun_lon=90.0, is_day=True)
    # 120 + 200 - 90 = 230°
    assert r["lot_lon"] == 230.0


# ── 5. 批量计算 ───────────────────────────────────────
def test_compute_all_main_lots_count():
    """批量计算返回 7 个 Lot。"""
    lots = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=10
    )
    assert len(lots) == 7


def test_compute_all_lots_returns_chinese_names():
    """每个 Lot 都应有中文名。"""
    lots = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=10
    )
    cn_names = {lot["part_name_cn"] for lot in lots}
    assert "福点" in cn_names
    assert "灵点" in cn_names
    assert "婚姻点" in cn_names


def test_compute_all_lots_signs():
    """每个 Lot 都应有星座标记。"""
    lots = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=10
    )
    for lot in lots:
        assert "lot_sign" in lot
        assert lot["lot_sign"] in {"白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
                                     "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"}


def test_compute_all_lots_day_night_flag():
    """批量计算应正确传递日/夜生标志。"""
    # 太阳第 4 宫 → 日生 (1-6 = 日生)
    lots_day = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=4
    )
    assert all(lot["is_day_chart"] for lot in lots_day)

    # 太阳第 8 宫 → 夜生 (7-12 = 夜生)
    lots_night = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=8
    )
    assert all(not lot["is_day_chart"] for lot in lots_night)


def test_compute_all_lots_formulas_used():
    """每个 Lot 都应有 formula_used 字段。"""
    lots = compute_all_main_lots(
        asc_lon=120.0, sun_lon=90.0,
        moon_lon=180.0, mercury_lon=85.0,
        venus_lon=110.0, mars_lon=200.0,
        jupiter_lon=60.0, saturn_lon=300.0,
        sun_house=10
    )
    for lot in lots:
        assert "formula_used" in lot
        assert "ASC" in lot["formula_used"]
