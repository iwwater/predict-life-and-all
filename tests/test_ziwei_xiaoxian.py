"""Tests for 紫微小限数据 (divination/data/ziwei_xiaoxian.py).

覆盖: 数据完整性 + 12生肖起宫 + 计算逻辑 + 查表/公式 + 边界
至少 7 项.
"""
from __future__ import annotations

import pytest

from divination.data.ziwei_xiaoxian import (
    GENDER_DIRECTION,
    PALACE_NAMES,
    XIAOXIAN_RULES,
    ZODIAC_START_PALACE,
    ZODIAC_NAMES,
    XiaoxianRule,
    compute_12_year_cycle,
    compute_xiaoxian_palace,
    compute_xiaoxian_palace_name,
    get_all_zodiac_starts,
    get_partial_count,
    lookup_rule,
)


# ── 1. 数据完整性 ──────────────────────────────────────────
def test_xiaoxian_zodiac_count_is_12():
    """12 生肖全部有起宫映射."""
    assert len(ZODIAC_START_PALACE) == 12


def test_xiaoxian_partial_count_at_least_60():
    """Partial 录入 >= 60 项 (6 生肖 × 男女 × 前5年 = 60)."""
    n = get_partial_count()
    assert n >= 60, f"当前 {n} 项, 期望 >= 60"


def test_xiaoxian_palace_names_count_12():
    """12 宫名称全部存在."""
    assert len(PALACE_NAMES) == 12


def test_xiaoxian_zodiac_names_count_12():
    """12 生肖中文名全部存在."""
    assert len(ZODIAC_NAMES) == 12


# ── 2. 计算逻辑 ────────────────────────────────────────────
def test_xiaoxian_compute_male_zi_age1():
    """男性 子年生 1 岁 → 命宫 (0)."""
    idx = compute_xiaoxian_palace("子", 1, "male")
    assert idx == 0
    assert compute_xiaoxian_palace_name("子", 1, "male") == "命宫"


def test_xiaoxian_compute_male_zi_age12():
    """男性 子年生 12 岁 → 父母宫 (11)."""
    idx = compute_xiaoxian_palace("子", 12, "male")
    assert idx == 11


def test_xiaoxian_compute_female_zi_age1():
    """女性 子年生 1 岁 → 命宫 (0)."""
    idx = compute_xiaoxian_palace("子", 1, "female")
    assert idx == 0


def test_xiaoxian_compute_female_zi_age2():
    """女性 子年生 2 岁 逆行 → 父母宫 (11)."""
    idx = compute_xiaoxian_palace("子", 2, "female")
    assert idx == 11


def test_xiaoxian_compute_male_chou_age1():
    """男性 丑年生 1 岁 → 兄弟宫 (1)."""
    idx = compute_xiaoxian_palace("丑", 1, "male")
    assert idx == 1


def test_xiaoxian_compute_male_yin_age25():
    """男性 寅年生 25 岁 验证循环."""
    idx = compute_xiaoxian_palace("寅", 25, "male")
    # 寅→起宫 2, 25 岁 → (2 + 24) % 12 = 26 % 12 = 2 (夫妻宫)
    assert idx == 2


def test_xiaoxian_compute_female_hai_age38():
    """女性 亥年生 38 岁 逆行验证."""
    idx = compute_xiaoxian_palace("亥", 38, "female")
    # 亥→起宫 11, 38 岁 → (11 + 37*(-1)) % 12 = (11-37) % 12 = -26 % 12 = 10
    assert idx == 10


# ── 3. 12 年周期 ───────────────────────────────────────────
def test_xiaoxian_12_year_cycle_male_zi():
    """男性 子年 12 年周期: 依次 0, 1, 2, ..., 11."""
    cycle = compute_12_year_cycle("子", "male")
    assert cycle == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


def test_xiaoxian_12_year_cycle_female_zi():
    """女性 子年 12 年周期: 逆行 0, 11, 10, ..., 1."""
    cycle = compute_12_year_cycle("子", "female")
    assert cycle == [0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]


# ── 4. 查表 / lookup_rule ──────────────────────────────────
def test_xiaoxian_lookup_rule_partial():
    """查表命中 60 项 partial 之一 (子年男性 1 岁)."""
    rule = lookup_rule("子", 1, "male")
    assert isinstance(rule, XiaoxianRule)
    assert rule.birth_zhi == "子"
    assert rule.age == 1
    assert rule.palace_idx == 0
    assert rule.palace_name == "命宫"


def test_xiaoxian_lookup_rule_fallback():
    """未录入规则 (未羊) → 公式 fallback."""
    rule = lookup_rule("未", 50, "female")
    assert isinstance(rule, XiaoxianRule)
    assert rule.birth_zhi == "未"
    assert rule.age == 50


def test_xiaoxian_all_zodiac_starts():
    """所有生肖起宫正确."""
    starts = get_all_zodiac_starts()
    assert starts["子"] == 0
    assert starts["丑"] == 1
    assert starts["亥"] == 11


# ── 5. 边界条件 ────────────────────────────────────────────
def test_xiaoxian_invalid_zhi_raises():
    """非法地支应抛出 ValueError."""
    with pytest.raises(ValueError, match="无效出生年支"):
        compute_xiaoxian_palace("猫", 1)


def test_xiaoxian_invalid_age_raises():
    """虚岁 < 1 应抛出 ValueError."""
    with pytest.raises(ValueError, match="虚岁必须 >= 1"):
        compute_xiaoxian_palace("子", 0)


def test_xiaoxian_invalid_gender_raises():
    """非法性别应抛出 ValueError."""
    with pytest.raises(ValueError, match="无效性别"):
        compute_xiaoxian_palace("子", 1, "other")


def test_xiaoxian_dataclass_frozen():
    """XiaoxianRule dataclass 为 frozen."""
    rule = lookup_rule("子", 1, "male")
    with pytest.raises(Exception):
        rule.palace_idx = 99  # type: ignore
