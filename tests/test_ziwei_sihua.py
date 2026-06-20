"""Tests for 紫微飞星四化 (divination/data/ziwei_sihua.py)

来源：docs/CLASSICAL_SOURCES.md §2 紫微斗数
文献：《飞星紫微斗数全书》《紫微斗数全书》《斗数微经》
"""
from __future__ import annotations

import pytest

from divination.data.ziwei_sihua import (
    ALL_SIHUA_STARS,
    FEIXING_SIHUA_RULES,
    NATAL_SIHUA,
    PALACE_NAMES,
    SIHUA_MEANINGS,
    get_natal_sihua,
    get_palace_sihua_count,
    get_sihua_meaning,
    get_star_sihua_in_year,
    get_stars_with_sihua,
    judge_palace_sihua,
)


# ── 1. 10 天干四化完整性 ──────────────────────────────
def test_natal_sihua_all_ten_gans():
    """10 天干全覆盖（甲乙丙丁戊己庚辛壬癸）。"""
    required = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
    assert set(NATAL_SIHUA.keys()) == required


def test_natal_sihua_each_has_four():
    """每一天干必须含 禄/权/科/忌 四化。"""
    required = {"禄", "权", "科", "忌"}
    for gan, t in NATAL_SIHUA.items():
        assert set(t.keys()) == required, f"{gan}: {set(t.keys())}"


def test_natal_sihua_classical_jia():
    """甲年经典四化: 禄-廉贞 权-破军 科-武曲 忌-太阳。"""
    t = NATAL_SIHUA["甲"]
    assert t["禄"] == "廉贞"
    assert t["权"] == "破军"
    assert t["科"] == "武曲"
    assert t["忌"] == "太阳"


def test_natal_sihua_classical_yi():
    """乙年经典四化: 禄-天机 权-天梁 科-紫微 忌-太阴。"""
    t = NATAL_SIHUA["乙"]
    assert t["禄"] == "天机"
    assert t["权"] == "天梁"
    assert t["科"] == "紫微"
    assert t["忌"] == "太阴"


def test_natal_sihua_classical_ren():
    """壬年经典四化: 禄-天梁 权-紫微 科-左辅 忌-武曲。"""
    t = NATAL_SIHUA["壬"]
    assert t["禄"] == "天梁"
    assert t["权"] == "紫微"
    assert t["科"] == "左辅"
    assert t["忌"] == "武曲"


# ── 2. 星曜覆盖 ─────────────────────────────────────
def test_all_sihua_stars_collected():
    """ALL_SIHUA_STARS 应至少含 14 主星 + 4 辅星。"""
    assert len(ALL_SIHUA_STARS) >= 14


def test_each_hua_has_ten_stars():
    """每化至少触发 10 星（10 天干各触发 1）。"""
    for hua in ["禄", "权", "科", "忌"]:
        stars = get_stars_with_sihua(hua)
        assert len(stars) == 10, f"化{hua}: {len(stars)} 星"


def test_query_classic_jia_lian_zhen():
    """甲年生人: 廉贞化禄。"""
    assert get_star_sihua_in_year("甲", "廉贞") == "禄"


def test_query_classic_yi_tian_ji():
    """乙年生人: 天机化禄。"""
    assert get_star_sihua_in_year("乙", "天机") == "禄"


def test_query_unknown_star():
    """未在四化表中的星曜 → None。"""
    assert get_star_sihua_in_year("甲", "紫微") is None


def test_query_invalid_gan():
    """非法天干 → None。"""
    assert get_star_sihua_in_year("X", "廉贞") is None


# ── 3. 四化含义 ─────────────────────────────────────
def test_sihua_meanings_categories():
    """四化含义表必须含 4 个类型。"""
    required = {"化禄", "化权", "化科", "化忌"}
    assert set(SIHUA_MEANINGS.keys()) == required


def test_sihua_meaning_classic_jia_lian_zheng():
    """廉贞化禄 = 偏财/桃花/人缘。"""
    m = get_sihua_meaning("化禄", "廉贞")
    assert "偏财" in m or "人缘" in m or "桃花" in m


def test_sihua_meaning_classic_ren_zi_wei():
    """壬年生人紫微化权 = 帝王之权。"""
    m = get_sihua_meaning("化权", "紫微")
    assert "帝" in m or "权" in m


def test_sihua_meaning_unknown_star():
    """未记录的化星 → 返回通用格式。"""
    m = get_sihua_meaning("化禄", "未知星")
    assert "化禄" in m or "未知" in m


# ── 4. 宫位判断 ────────────────────────────────────
def test_palace_names_twelve():
    """PALACE_NAMES 必须含 12 宫（紫微标准 12 宫）。"""
    assert len(PALACE_NAMES) == 12
    assert "命宫" in PALACE_NAMES
    assert "财帛宫" in PALACE_NAMES


def test_palace_double_lu_da_ji():
    """化禄 ≥ 2 且无化忌 = 大吉。"""
    r = judge_palace_sihua("财帛宫", {"禄": 2, "权": 0, "科": 0, "忌": 0})
    assert r["luck"] == "大吉"


def test_palace_double_ji_da_xiong():
    """化忌 ≥ 2 且无化禄 = 大凶。"""
    r = judge_palace_sihua("夫妻宫", {"禄": 0, "权": 0, "科": 0, "忌": 2})
    assert r["luck"] == "大凶"


def test_palace_lu_ji_xiongzhongdaiji():
    """化禄 + 化忌同宫 = 凶中带吉。"""
    r = judge_palace_sihua("命宫", {"禄": 1, "权": 0, "科": 0, "忌": 1})
    assert r["luck"] == "凶中带吉"


def test_palace_lu_quan_ji():
    """化禄 + 化权 = 吉（名利双收）。"""
    r = judge_palace_sihua("官禄宫", {"禄": 1, "权": 1, "科": 0, "忌": 0})
    assert r["luck"] == "吉"


def test_palace_ke_quan_ji():
    """化科 + 化权 = 吉（名权双收）。"""
    r = judge_palace_sihua("官禄宫", {"禄": 0, "权": 1, "科": 1, "忌": 0})
    assert r["luck"] == "吉"


def test_palace_single_lu_xiaoji():
    """单化禄 = 吉。"""
    r = judge_palace_sihua("财帛宫", {"禄": 1, "权": 0, "科": 0, "忌": 0})
    assert r["luck"] == "吉"


def test_palace_single_ji_xiaoxiong():
    """单化忌 = 小凶。"""
    r = judge_palace_sihua("疾厄宫", {"禄": 0, "权": 0, "科": 0, "忌": 1})
    assert r["luck"] == "小凶"


def test_palace_no_sihua_ping():
    """无四化 = 平。"""
    r = judge_palace_sihua("兄弟宫", {"禄": 0, "权": 0, "科": 0, "忌": 0})
    assert r["luck"] == "平"


def test_palace_judge_has_palace_name():
    """判断结果必须含 palace 字段。"""
    r = judge_palace_sihua("命宫", {"禄": 1, "权": 0, "科": 0, "忌": 0})
    assert r["palace"] == "命宫"


# ── 5. 宫位主星四化计数 ────────────────────────────
def test_count_palace_sihua_no_trigger():
    """无四化星 → 全 0。"""
    counts = get_palace_sihua_count(["紫微", "天府"], "甲")
    # 甲年: 禄-廉贞 权-破军 科-武曲 忌-太阳, 紫微天府不在其中
    assert counts == {"禄": 0, "权": 0, "科": 0, "忌": 0}


def test_count_palace_sihua_jia_with_lian_zheng():
    """甲年生人 + 廉贞入宫 → 禄 + 1。"""
    counts = get_palace_sihua_count(["廉贞", "天府"], "甲")
    assert counts["禄"] == 1


def test_count_palace_sihua_multiple():
    """甲年生人 + 多颗化星同宫。"""
    counts = get_palace_sihua_count(["廉贞", "破军", "武曲", "太阳"], "甲")
    assert counts["禄"] == 1
    assert counts["权"] == 1
    assert counts["科"] == 1
    assert counts["忌"] == 1


def test_count_palace_sihua_invalid_gan():
    """非法年干 → 全 0。"""
    counts = get_palace_sihua_count(["廉贞"], "X")
    assert counts == {"禄": 0, "权": 0, "科": 0, "忌": 0}


# ── 6. 飞星派规则 ──────────────────────────────────
def test_feixing_rules_present():
    """飞星派规则表必须含核心条目。"""
    assert "飞星派核心理念" in FEIXING_SIHUA_RULES
    assert "大限四化" in FEIXING_SIHUA_RULES
    assert "流年四化" in FEIXING_SIHUA_RULES
    assert "忌入对宫" in FEIXING_SIHUA_RULES
