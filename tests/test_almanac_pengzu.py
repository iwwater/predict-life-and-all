"""Tests for 彭祖百忌 完整表 (divination/data/almanac_pengzu.py)

来源：docs/CLASSICAL_SOURCES.md §13 老黄历·择日
文献：《协纪辨方书》《玉匣记》《择吉会要》
"""
from __future__ import annotations

import pytest

from divination.data.almanac_pengzu import (
    BRANCH_TABOOS,
    STEM_TABOOS,
    TOTAL_BRANCH_TABOOS,
    TOTAL_STEM_TABOOS,
    TOTAL_TABOO_CATEGORIES,
    get_category_distribution,
    get_severity_distribution,
    get_taboo,
    get_taboo_summary,
    verify_against_lunar_python,
)


# ── 1. 基础完整性 ─────────────────────────────────────────
def test_total_taboo_categories_22():
    """彭祖百忌 22 类 = 10 天干 + 12 地支。"""
    assert TOTAL_TABOO_CATEGORIES == 22
    assert TOTAL_STEM_TABOOS == 10
    assert TOTAL_BRANCH_TABOOS == 12


def test_stem_taboo_all_ten():
    """10 天干全覆盖 (甲乙丙丁戊己庚辛壬癸)。"""
    required = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
    assert set(STEM_TABOOS.keys()) == required


def test_branch_taboo_all_twelve():
    """12 地支全覆盖 (子丑寅卯辰巳午未申酉戌亥)。"""
    required = {"子", "丑", "寅", "卯", "辰", "巳",
                "午", "未", "申", "酉", "戌", "亥"}
    assert set(BRANCH_TABOOS.keys()) == required


# ── 2. 字段完整性 ─────────────────────────────────────────
def test_stem_taboo_required_fields():
    """每条天干忌必须含: stem, taboo_action, consequence, full_text。"""
    required = {"stem", "taboo_action", "consequence", "full_text"}
    for stem, t in STEM_TABOOS.items():
        missing = required - set(t.keys())
        assert not missing, f"天干 {stem} 缺失字段: {missing}"


def test_branch_taboo_required_fields():
    """每条地支忌必须含: branch, taboo_action, consequence, full_text。"""
    required = {"branch", "taboo_action", "consequence", "full_text"}
    for zhi, t in BRANCH_TABOOS.items():
        missing = required - set(t.keys())
        assert not missing, f"地支 {zhi} 缺失字段: {missing}"


def test_severity_valid_values():
    """严重等级必须是高/中/低 之一。"""
    valid = {"高", "中", "低"}
    for t in list(STEM_TABOOS.values()) + list(BRANCH_TABOOS.values()):
        assert t.get("severity") in valid, f"{t.get('full_text')}: severity={t.get('severity')}"


# ── 3. 与古籍经典一致 ─────────────────────────────────────
def test_jia_no_open_warehouse():
    """甲不开仓,财物耗散（《协纪辨方书》经典条目）。"""
    assert STEM_TABOOS["甲"]["taboo_action"] == "开仓"
    assert "耗散" in STEM_TABOOS["甲"]["consequence"]


def test_gui_no_litigation():
    """癸不词讼,理弱敌强。"""
    assert STEM_TABOOS["癸"]["taboo_action"] == "词讼"
    assert "敌强" in STEM_TABOOS["癸"]["consequence"]


def test_hai_no_marriage():
    """亥不嫁娶,不利新郎。"""
    assert BRANCH_TABOOS["亥"]["taboo_action"] == "嫁娶"
    assert "新郎" in BRANCH_TABOOS["亥"]["consequence"]


def test_chen_no_crying():
    """辰不哭泣,亲人不祥。"""
    assert BRANCH_TABOOS["辰"]["taboo_action"] == "哭泣"
    assert "亲人" in BRANCH_TABOOS["辰"]["consequence"]


# ── 4. 查询函数 ──────────────────────────────────────────
def test_get_taboo_ji_hai():
    """癸亥日: 干=癸忌词讼, 支=亥忌嫁娶。"""
    t = get_taboo("癸", "亥")
    assert t["stem_taboo"]["full_text"] == "癸不词讼,理弱敌强"
    assert t["branch_taboo"]["full_text"] == "亥不嫁娶,不利新郎"


def test_get_taboo_summary_format():
    """摘要格式: 'X忌...; Y忌...' (干忌 + 支忌,以分号分隔)。"""
    s = get_taboo_summary("甲", "子")
    assert "甲" in s and "开仓" in s
    assert "子" in s and "问卜" in s
    assert "；" in s


def test_get_taboo_invalid_stem():
    """非法天干应返回空 dict (非崩溃)。"""
    t = get_taboo("X", "子")
    assert t["stem_taboo"] == {}
    assert t["branch_taboo"]["full_text"] == "子不问卜,自惹祸殃"


def test_get_taboo_invalid_branch():
    """非法地支应返回空 dict。"""
    t = get_taboo("甲", "X")
    assert t["stem_taboo"]["full_text"] == "甲不开仓,财物耗散"
    assert t["branch_taboo"] == {}


# ── 5. 统计 ─────────────────────────────────────────────
def test_severity_distribution_sums_to_22():
    """严重等级分布总和 = 22。"""
    dist = get_severity_distribution()
    assert sum(dist.values()) == 22


def test_category_distribution_covers_life():
    """类目分布必须覆盖至少 5 类。"""
    dist = get_category_distribution()
    assert len(dist) >= 5


# ── 6. 与 lunar-python 对照验证 ──────────────────────────
def test_verify_jia_zi_matches_lunar_python():
    """甲子日: 与 lunar-python 输出完全一致。"""
    result = verify_against_lunar_python("甲", "子")
    if "error" not in result:
        assert result["stem_match"], f"天干不匹配: {result}"
        assert result["branch_match"], f"地支不匹配: {result}"


def test_verify_gui_hai_matches_lunar_python():
    """癸亥日: 与 lunar-python 输出完全一致。"""
    result = verify_against_lunar_python("癸", "亥")
    if "error" not in result:
        assert result["stem_match"]
        assert result["branch_match"]


def test_verify_ji_mao_matches_lunar_python():
    """己卯日: 与 lunar-python 输出完全一致。"""
    result = verify_against_lunar_python("己", "卯")
    if "error" not in result:
        assert result["stem_match"]
        assert result["branch_match"]
