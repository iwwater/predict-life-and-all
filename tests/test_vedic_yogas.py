"""Tests for 吠陀 Yogas (divination/data/vedic_yogas.py)

来源：docs/CLASSICAL_SOURCES.md §8 吠陀占星
文献：Brihat Parashara Hora Shastra, Phaladeepika, Brihat Jataka
"""
from __future__ import annotations

import pytest

from divination.data.vedic_yogas import (
    PLANET_DEBIL_SIGN,
    PLANET_EXALT_SIGN,
    PLANET_OWN_SIGNS,
    SIGN_CN,
    YOGAS,
    check_budhaditya,
    check_gaja_kesari,
    check_kemadruma,
    check_mangal_dosha,
    check_pancha_mahapurusha,
    get_yoga_count,
    list_yogas_by_category,
    list_yogas_by_rarity,
)


# ── 1. 行星庙旺表 ─────────────────────────────────
def test_own_signs_all_planets():
    """7 主星 + 罗睺/计都 = 9 项。"""
    assert len(PLANET_OWN_SIGNS) == 9


def test_sun_owns_leo():
    """太阳守狮子。"""
    assert PLANET_OWN_SIGNS["太阳"] == [4]  # 狮子 idx=4


def test_mars_owns_aries_and_scorpio():
    """火星守白羊 + 天蝎。"""
    assert PLANET_OWN_SIGNS["火星"] == [0, 7]


def test_jupiter_owns_sagittarius_and_pisces():
    """木星守射手 + 双鱼。"""
    assert PLANET_OWN_SIGNS["木星"] == [8, 11]


def test_exalt_signs_classical():
    """入庙经典对应（太阳白羊 / 月亮金牛 / 火星摩羯 / 木星巨蟹）。"""
    assert PLANET_EXALT_SIGN["太阳"] == 0
    assert PLANET_EXALT_SIGN["月亮"] == 1
    assert PLANET_EXALT_SIGN["火星"] == 9
    assert PLANET_EXALT_SIGN["木星"] == 3


def test_debil_signs_opposite_to_exalt():
    """落陷 = 入庙对宫 (180°)。"""
    for planet in ["太阳", "月亮", "火星", "水星", "木星", "金星", "土星"]:
        exalt = PLANET_EXALT_SIGN[planet]
        debil = PLANET_DEBIL_SIGN[planet]
        diff = (debil - exalt) % 12
        assert diff == 6, f"{planet}: 入庙 {exalt}, 落陷 {debil}, 应相差 6 宫"


def test_sign_cn_12():
    """12 星座中文全覆盖。"""
    assert len(SIGN_CN) == 12
    assert SIGN_CN[0] == "白羊"
    assert SIGN_CN[11] == "双鱼"


# ── 2. Yogas 表完整性 ─────────────────────────────────
def test_yogas_count_at_least_20():
    """至少 20 种常见 Yogas。"""
    assert len(YOGAS) >= 20


def test_yoga_required_fields():
    """每条 Yoga 必须含 name, category, condition, meaning。"""
    required = {"name", "category", "condition", "meaning"}
    for i, y in enumerate(YOGAS):
        missing = required - set(y.keys())
        assert not missing, f"Yoga #{i} ({y.get('name')}) 缺失: {missing}"


def test_yogas_cover_main_categories():
    """覆盖核心分类。"""
    cats = {y["category"] for y in YOGAS}
    required = {"权力", "财富", "伟人", "智慧"}
    missing = required - cats
    assert not missing, f"核心分类缺失: {missing}"


def test_pancha_mahapurusha_all_five():
    """五大伟人瑜伽必须全有。"""
    names = {y["name"] for y in YOGAS}
    required = {
        "Ruchaka Yoga (战神瑜伽)",
        "Bhadra Yoga (贤者瑜伽)",
        "Hamsa Yoga (天鹅瑜伽)",
        "Malavya Yoga (莲花瑜伽)",
        "Sasa Yoga (兔瑜伽)",
    }
    missing = required - names
    assert not missing, f"五大伟人瑜伽缺失: {missing}"


def test_classical_gaja_kesari_present():
    """象-狮瑜伽必须存在。"""
    names = {y["name"] for y in YOGAS}
    assert "Gaja Kesari Yoga (象-狮瑜伽)" in names


def test_classical_budhaditya_present():
    """水日瑜伽必须存在。"""
    names = {y["name"] for y in YOGAS}
    assert "Budhaditya Yoga (水日瑜伽)" in names


# ── 3. Pancha Mahapurusha 检查 ───────────────────────
def test_panch_mahapurusha_mars_in_aries_kendra():
    """火星白羊第 1 宫 → Ruchaka。"""
    result = check_pancha_mahapurusha("火星", 0, 1)
    assert result == "Ruchaka Yoga (战神瑜伽)"


def test_panch_mahapurusha_jupiter_in_sagittarius_kendra():
    """木星射手第 4 宫 → Hamsa。"""
    result = check_pancha_mahapurusha("木星", 8, 4)
    assert result == "Hamsa Yoga (天鹅瑜伽)"


def test_panch_mahapurusha_venus_exalted_kendra():
    """金星入庙双鱼第 10 宫 → Malavya。"""
    result = check_pancha_mahapurusha("金星", 11, 10)
    assert result == "Malavya Yoga (莲花瑜伽)"


def test_panch_mahapurusha_mars_in_aries_not_kendra():
    """火星白羊但非 Kendra 宫 → 无。"""
    result = check_pancha_mahapurusha("火星", 0, 2)
    assert result is None


def test_panch_mahapurusha_mars_in_cancer():
    """火星巨蟹 (落陷) → 无 Pancha Mahapurusha。"""
    # 火星落陷在巨蟹, 但不在 own signs (白羊/天蝎)
    result = check_pancha_mahapurusha("火星", 3, 1)
    assert result is None


def test_panch_mahapurusha_sun_leo_kendra():
    """太阳狮子第 1 宫 → 无 (太阳不在 Pancha 中)。"""
    # 注: 太阳不在五大伟人之列（只有火水木金土 5 星）
    result = check_pancha_mahapurusha("太阳", 4, 1)
    assert result is None


# ── 4. Gaja Kesari Yoga ─────────────────────────────
def test_gaja_kesari_same_sign_kendra():
    """月亮木星同白羊 + Kendra → True。"""
    assert check_gaja_kesari(0, 0, 1) is True


def test_gaja_kesari_opposite_kendra():
    """月亮白羊木星天秤 (对望) + Kendra → True。"""
    assert check_gaja_kesari(0, 6, 7) is True


def test_gaja_kesari_same_sign_not_kendra():
    """月亮木星同宫但非 Kendra → False。"""
    assert check_gaja_kesari(0, 0, 2) is False


def test_gaja_kesari_jupiter_debilitated():
    """木星落陷 → False (即使其他条件满足)。"""
    # 木星落陷摩羯 (idx 9)
    assert check_gaja_kesari(0, 9, 4) is False


def test_gaja_kesari_not_conjunction_or_opposition():
    """月亮木星差 90° (刑) → False。"""
    assert check_gaja_kesari(0, 3, 1) is False


# ── 5. Budhaditya Yoga ─────────────────────────────
def test_budhaditya_within_orb():
    """水星太阳同宫, 度数差 1° → True。"""
    assert check_budhaditya(0, 5.0, 0, 6.0) is True


def test_budhaditya_outside_orb():
    """水星太阳同宫, 度数差 5° → False (超过 3° 容许度)。"""
    assert check_budhaditya(0, 5.0, 0, 10.0) is False


def test_budhaditya_different_signs():
    """水星太阳不同宫 → False。"""
    assert check_budhaditya(0, 5.0, 1, 10.0) is False


# ── 6. Mangal Dosha ────────────────────────────────
def test_mangal_dosha_houses_trigger():
    """火星位于第 1/2/4/7/8/12 宫 → True。"""
    for h in [1, 2, 4, 7, 8, 12]:
        assert check_mangal_dosha(h) is True, f"第 {h} 宫 应触发火星煞"


def test_mangal_dosha_houses_safe():
    """火星位于第 3/5/6/9/10/11 宫 → False。"""
    for h in [3, 5, 6, 9, 10, 11]:
        assert check_mangal_dosha(h) is False, f"第 {h} 宫 不应触发火星煞"


# ── 7. Kemadruma Yoga ─────────────────────────────
def test_kemadruma_alone():
    """月亮孤悬, 周围 4 宫无行星 → True。"""
    # 月亮在 0, 周围 (10, 11, 1, 2) 必须无任何行星
    # 所以所有其他行星必须远离,例如在 4/5/6/7/8/9
    planets = {"太阳": 4, "水星": 5, "金星": 6}
    assert check_kemadruma(0, planets) is True


def test_kemadruma_with_neighbor():
    """月亮邻宫有行星 → False。"""
    # 水星在 11 (月亮的 -1 宫, 即 23 时位但 mod 12 = 11)
    planets = {"太阳": 4, "水星": 11}
    assert check_kemadruma(0, planets) is False


def test_kemadruma_rahu_or_ketu_counts():
    """罗睺/计都也应计入（传统上计入孤月判断）。"""
    # 罗睺在 1 (月亮的 +1 宫)
    planets = {"罗睺": 1}
    assert check_kemadruma(0, planets) is False


# ── 8. Yogas 查询 ────────────────────────────────
def test_list_by_category_wealth():
    """财富类 Yogas 至少 3 种。"""
    wealth = list_yogas_by_category("财富")
    assert len(wealth) >= 3


def test_list_by_rarity_rare():
    """稀有 Yogas 至少 5 种。"""
    rare = list_yogas_by_rarity("稀有")
    assert len(rare) >= 5


def test_get_yoga_count_total():
    """get_yoga_count 总和 = YOGAS 长度。"""
    counts = get_yoga_count()
    assert sum(counts.values()) == len(YOGAS)
