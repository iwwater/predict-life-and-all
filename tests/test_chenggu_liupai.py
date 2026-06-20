"""Tests for 称骨流派差异表 (divination/data/chenggu_liupai.py).

覆盖: 流派数量 + 差异条目数 + 分类 + 查询 + 数据完整性
至少 4 项.
"""
from __future__ import annotations

import pytest

from divination.data.chenggu_liupai import (
    BONE_WEIGHT_DIFFS,
    BoneWeightDiff,
    SCHOOLS,
    ChengguSchool,
    get_categories,
    get_diff_count,
    get_diffs_by_category,
    get_school_count,
    get_school_names,
    get_total_impact,
)


# ── 1. 流派完整性 ──────────────────────────────────────────
def test_liupai_school_count_at_least_4():
    """至少 4 个流派."""
    n = get_school_count()
    assert n >= 4, f"当前 {n} 流派, 期望 >= 4"


def test_liupai_core_schools_present():
    """袁天罡主流流派必须存在."""
    names = get_school_names()
    assert any("袁天罡" in n for n in names), "缺失袁天罡主流流派"


# ── 2. 差异条目 ────────────────────────────────────────────
def test_liupai_diff_count_at_least_10():
    """至少 10 项骨重差异."""
    n = get_diff_count()
    assert n >= 10, f"当前 {n} 项, 期望 >= 10"


def test_liupai_categories_coverage():
    """分类覆盖年柱/月柱/日柱/时柱/规则/解读."""
    cats = get_categories()
    expected = {"年柱", "月柱", "日柱", "时柱", "规则", "解读"}
    missing = expected - set(cats)
    assert not missing, f"缺失分类: {missing}"


def test_liupai_each_diff_has_valid_fields():
    """每条差异有非空字段."""
    for d in BONE_WEIGHT_DIFFS:
        assert d.label
        assert d.category
        assert d.mainstream
        assert d.alternative
        assert d.alt_school


def test_liupai_school_dataclass_frozen():
    """ChengguSchool dataclass 为 frozen."""
    for s in SCHOOLS.values():
        with pytest.raises(Exception):
            s.name = "test"  # type: ignore


def test_liupai_diffs_by_category():
    """按分类筛选正确."""
    nian = get_diffs_by_category("年柱")
    yue = get_diffs_by_category("月柱")
    assert len(nian) >= 2, f"年柱差异至少 2 项, 当前 {len(nian)}"
    assert len(yue) >= 2, f"月柱差异至少 2 项, 当前 {len(yue)}"


def test_liupai_total_impact_positive():
    """总影响 > 0."""
    imp = get_total_impact()
    assert imp > 0
