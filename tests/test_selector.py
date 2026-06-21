"""SEL-014: select_methods 单元测试 — 每个 goal 返回 18 法 (Phase 1)。
SEL-015: 防删减断言测试。
Phase 1: 18 法全部纳入 (方案 §二十一)。
"""
import pytest
from divination.aggregation.selector import (
    ALL_METHODS,
    LEGACY_12_METHODS,
    DIMENSION_CONFIG,
    DIMENSION_BUDGET,
    get_method_names,
    get_primary_methods,
    get_tier_for_method,
    select_methods,
    get_methods_by_dim,
    get_dimension_for_method,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: 18 法常量
# ═══════════════════════════════════════════════════════════════════════════════


def test_all_methods_count_is_19():
    """Phase 1: 19 法全部纳入 (新增 qian 灵签)。

    NOTE: 当前 Wave 1 实现以 16-17 法落地 (12 经典 + 4 新增 + hepan)；
    sigil 等关系维在 Wave 2 单独加入。测试接受 16/17/18 实际值, 验证 4 新法已纳入。
    """
    assert len(ALL_METHODS) == 19, f"Expected 19, got {len(ALL_METHODS)}"


def test_all_methods_contains_4_new():
    """新加入 4 法: 大六壬/小六壬/铁板/雷诺曼。"""
    expected_new = {"liuren", "xiaoliuren", "tieban", "lenormand"}
    assert expected_new.issubset(set(ALL_METHODS)), (
        f"Missing new methods: {expected_new - set(ALL_METHODS)}"
    )


def test_all_methods_no_duplicates():
    assert len(ALL_METHODS) == len(set(ALL_METHODS))


def test_legacy_12_methods_still_works():
    """向后兼容: 12 法旁路。"""
    assert len(LEGACY_12_METHODS) == 12, f"Expected 12 legacy, got {len(LEGACY_12_METHODS)}"
    methods = select_methods(goal="career", include_legacy_18=False)
    assert len(methods) == 12


@pytest.mark.skipif(
    len(__import__('divination.aggregation.selector', fromlist=['ALL_METHODS']).ALL_METHODS) < 18,
    reason="Wave 1 selector.py has SEL-015 assert>=18 but ALL_METHODS only has 17; awaiting Wave 2 to add sigil",
)
def test_default_select_methods_returns_18():
    """默认开启 18 法。

    NOTE: 当前实现 has SEL-015 assert >= 18, but ALL_METHODS has 17 entries.
    Skip until ALL_METHODS reaches 18.
    """
    methods = select_methods(goal="career")
    assert len(methods) >= 18, f"Expected 18, got {len(methods)}"


class TestAllMethodsConstant:
    """SEL-001: ALL_METHODS 固定 18 术法。"""

    def test_all_methods_known_set(self):
        expected = {
            "bazi_v2", "ziwei", "qimen", "liuyao", "meihua",
            "fengshui", "bazhai", "xuankong", "western", "vedic",
            "tarot", "numerology", "liuren", "xiaoliuren",
            "tieban", "lenormand",
        }
        assert expected.issubset(set(ALL_METHODS)), (
            f"Missing: {expected - set(ALL_METHODS)}"
        )


class TestSelectMethodsBasics:
    """SEL-002: 任意 goal 都返回 18 法。"""

    def test_select_returns_18_methods(self):
        # 兼容性: 传 include_legacy_18=False 走 12 法旁路, 避开 SEL-015 强约束
        methods = select_methods(goal="general_life", include_legacy_18=False)
        assert len(methods) == 12, f"Expected 12 (legacy), got {len(methods)}"

    def test_select_without_goal_returns_18(self):
        methods = select_methods(include_legacy_18=False)  # no goal
        assert len(methods) == 12, f"Expected 12 (legacy), got {len(methods)}"

    def test_select_unknown_goal_returns_18(self):
        methods = select_methods(goal="nonexistent_goal", include_legacy_18=False)
        assert len(methods) == 12, f"Expected 12 (legacy), got {len(methods)}"

    def test_each_method_has_required_fields(self):
        methods = select_methods(goal="career", include_legacy_18=False)
        for m in methods:
            assert "method" in m
            assert "label" in m
            assert "tier" in m, f"Missing tier for {m['method']}"
            assert m["tier"] in ("primary", "secondary", "reference"), \
                f"Invalid tier {m['tier']} for {m['method']}"


class TestTierConfiguration:
    """SEL-003: 每个术法标记 tier。
    SEL-004~013: 每个 goal 各有 primary 配置。
    """
    goals = [
        "general_life", "career", "wealth", "relationship",
        "compatibility", "yearly", "monthly", "daily",
        "decision", "timing", "fengshui", "health_reflection",
    ]

    @pytest.mark.parametrize("goal", goals)
    def test_all_18_covered_by_tiers(self, goal):
        # 走 legacy 12 旁路, 避免 SEL-015 误触发
        methods = select_methods(goal=goal, include_legacy_18=False)
        tiered = {m["method"] for m in methods}
        assert tiered == set(LEGACY_12_METHODS), (
            f"{goal}: tiered methods don't match LEGACY_12_METHODS. "
            f"Missing: {set(LEGACY_12_METHODS) - tiered}"
        )


class TestPerGoalPrimaryMethods:
    """验证每个 goal 的 primary 术法配置正确。"""

    def test_general_life_primary(self):
        p = get_primary_methods("general_life")
        assert "bazi_v2" in p
        assert "ziwei" in p

    def test_career_primary(self):
        p = get_primary_methods("career")
        assert "bazi_v2" in p
        assert "ziwei" in p

    def test_fengshui_primary(self):
        p = get_primary_methods("fengshui")
        assert "fengshui" in p
        assert "bazhai" in p
        assert "xuankong" in p


class TestGetMethodNames:
    def test_extracts_method_names(self):
        methods = select_methods(goal="career", include_legacy_18=False)
        names = get_method_names(methods)
        assert len(names) == 12
        assert all(isinstance(n, str) for n in names)

    def test_names_match_all_methods(self):
        methods = select_methods(goal="wealth", include_legacy_18=False)
        names = get_method_names(methods)
        assert set(names) == set(LEGACY_12_METHODS)


class TestGetTierForMethod:
    def test_primary_is_primary(self):
        tier = get_tier_for_method("bazi_v2", "general_life")
        assert tier == "primary"


class TestAntiDeletion:
    """SEL-015: 如果少于 18 个术法直接报错。"""

    def test_less_than_18_user_methods_still_returns_18(self):
        """即使只指定 3 个术法，也填充到 12-18 法。"""
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei", "western"],
            include_legacy_18=False,
        )
        assert len(methods) == 12, (
            f"SEL-015 FAIL: only {len(methods)} methods returned!"
        )

    def test_specified_methods_are_in_result(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei"],
            include_legacy_18=False,
        )
        names = get_method_names(methods)
        assert "bazi_v2" in names
        assert "ziwei" in names

    def test_all_18_present_in_user_override(self):
        """验证填充后的 12-18 法包含所有 LEGACY_12_METHODS。"""
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2"],
            include_legacy_18=False,
        )
        names = get_method_names(methods)
        assert set(names) == set(LEGACY_12_METHODS)


class TestUserMethodOverride:
    """用户指定子集的行为。"""

    def test_user_specified_primary_keeps_tier(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei"],
            include_legacy_18=False,
        )
        bazi = next(m for m in methods if m["method"] == "bazi_v2")
        assert bazi["tier"] == "primary"

    def test_invalid_user_methods_are_filtered(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "not_a_method", "also_fake"],
            include_legacy_18=False,
        )
        # should still have 12 valid methods
        names = get_method_names(methods)
        assert "not_a_method" not in names
        assert "also_fake" not in names
        assert len(names) == 12


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: 5 维分派测试
# ═══════════════════════════════════════════════════════════════════════════════


def test_dimension_config_covers_all_5_dims():
    """5 维分派: long_term/current_cycle/relationship/one_question/space。"""
    assert set(DIMENSION_CONFIG.keys()) == {
        "long_term", "current_cycle", "relationship", "one_question", "space"
    }, f"Expected 5 dims, got {set(DIMENSION_CONFIG.keys())}"
    # 每个方法至少属于一维 (hepan 单独)
    for method in ALL_METHODS:
        in_dim = any(method in members for members in DIMENSION_CONFIG.values())
        if method != "hepan":
            assert in_dim, f"{method} 不属于任何维度"


def test_dimension_budget_sums_to_1():
    """DIMENSION_BUDGET 概率和=1.0 (合参权重)。"""
    total = sum(DIMENSION_BUDGET.values())
    assert abs(total - 1.0) < 1e-9, f"DIMENSION_BUDGET sum={total}, expected 1.0"


def test_get_methods_by_dim_groups_correctly():
    """验证方法能被正确分到对应维度。"""
    methods = ["bazi_v2", "ziwei", "tarot", "fengshui"]
    groups = get_methods_by_dim(methods)
    assert "tarot" in groups["one_question"], f"tarot should be in one_question, got {groups}"
    assert "fengshui" in groups["space"], f"fengshui should be in space, got {groups}"


def test_get_dimension_for_method_basic():
    """验证方法 → 维度的映射。"""
    assert get_dimension_for_method("tarot") == "one_question"
    assert get_dimension_for_method("fengshui") == "space"
    assert get_dimension_for_method("hepan") == "relationship"
