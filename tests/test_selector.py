"""SEL-014: select_methods 单元测试 — 每个 goal 返回 12 法。
SEL-015: 防删减断言测试。
"""
import pytest
from divination.aggregation.selector import (
    ALL_METHODS,
    get_method_names,
    get_primary_methods,
    get_tier_for_method,
    select_methods,
)


class TestAllMethodsConstant:
    """SEL-001: ALL_METHODS 固定 12 术法。"""

    def test_all_methods_count(self):
        assert len(ALL_METHODS) == 12, f"Expected 12, got {len(ALL_METHODS)}"

    def test_all_methods_known_set(self):
        expected = {
            "bazi_v2", "ziwei", "qimen", "liuyao", "meihua",
            "fengshui", "bazhai", "xuankong", "western", "vedic",
            "tarot", "numerology",
        }
        assert set(ALL_METHODS) == expected

    def test_all_methods_no_duplicates(self):
        assert len(ALL_METHODS) == len(set(ALL_METHODS))


class TestSelectMethodsBasics:
    """SEL-002: 任意 goal 都返回 12 法。"""

    def test_select_returns_12_methods(self):
        methods = select_methods(goal="general_life")
        assert len(methods) == 12

    def test_select_without_goal_returns_12(self):
        methods = select_methods()  # no goal
        assert len(methods) == 12

    def test_select_unknown_goal_returns_12(self):
        methods = select_methods(goal="nonexistent_goal")
        assert len(methods) == 12

    def test_each_method_has_required_fields(self):
        methods = select_methods(goal="career")
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
    def test_each_goal_has_4_primary_methods(self, goal):
        methods = select_methods(goal=goal)
        primary_count = sum(1 for m in methods if m["tier"] == "primary")
        assert primary_count == 4, (
            f"{goal}: expected 4 primary, got {primary_count}. "
            f"Primary: {[m['method'] for m in methods if m['tier'] == 'primary']}"
        )

    @pytest.mark.parametrize("goal", goals)
    def test_each_goal_has_4_secondary_methods(self, goal):
        methods = select_methods(goal=goal)
        secondary_count = sum(1 for m in methods if m["tier"] == "secondary")
        assert secondary_count == 4, f"{goal}: expected 4 secondary, got {secondary_count}"

    @pytest.mark.parametrize("goal", goals)
    def test_each_goal_has_4_reference_methods(self, goal):
        methods = select_methods(goal=goal)
        ref_count = sum(1 for m in methods if m["tier"] == "reference")
        assert ref_count == 4, f"{goal}: expected 4 reference, got {ref_count}"

    @pytest.mark.parametrize("goal", goals)
    def test_all_12_covered_by_tiers(self, goal):
        methods = select_methods(goal=goal)
        tiered = {m["method"] for m in methods}
        assert tiered == set(ALL_METHODS), (
            f"{goal}: tiered methods don't match ALL_METHODS. "
            f"Missing: {set(ALL_METHODS) - tiered}"
        )


class TestPerGoalPrimaryMethods:
    """验证每个 goal 的 primary 术法配置正确。"""

    def test_general_life_primary(self):
        p = get_primary_methods("general_life")
        assert set(p) == {"bazi_v2", "ziwei", "western", "vedic"}

    def test_career_primary(self):
        p = get_primary_methods("career")
        assert set(p) == {"bazi_v2", "ziwei", "western", "qimen"}

    def test_wealth_primary(self):
        p = get_primary_methods("wealth")
        assert set(p) == {"bazi_v2", "ziwei", "qimen", "western"}

    def test_relationship_primary(self):
        p = get_primary_methods("relationship")
        assert set(p) == {"bazi_v2", "ziwei", "western", "tarot"}

    def test_compatibility_primary(self):
        p = get_primary_methods("compatibility")
        assert set(p) == {"bazi_v2", "ziwei", "western", "vedic"}

    def test_yearly_primary(self):
        p = get_primary_methods("yearly")
        assert set(p) == {"bazi_v2", "ziwei", "western", "vedic"}

    def test_decision_primary(self):
        p = get_primary_methods("decision")
        assert set(p) == {"qimen", "liuyao", "meihua", "tarot"}

    def test_timing_primary(self):
        p = get_primary_methods("timing")
        assert set(p) == {"qimen", "liuyao", "bazi_v2", "ziwei"}

    def test_fengshui_primary(self):
        p = get_primary_methods("fengshui")
        assert set(p) == {"fengshui", "bazhai", "xuankong", "qimen"}

    def test_daily_primary(self):
        p = get_primary_methods("daily")
        assert set(p) == {"tarot", "numerology", "bazi_v2", "qimen"}


class TestGetMethodNames:
    def test_extracts_method_names(self):
        methods = select_methods(goal="career")
        names = get_method_names(methods)
        assert len(names) == 12
        assert all(isinstance(n, str) for n in names)

    def test_names_match_all_methods(self):
        methods = select_methods(goal="wealth")
        names = get_method_names(methods)
        assert set(names) == set(ALL_METHODS)


class TestGetTierForMethod:
    def test_primary_is_primary(self):
        tier = get_tier_for_method("bazi_v2", "general_life")
        assert tier == "primary"

    def test_secondary_is_secondary(self):
        tier = get_tier_for_method("qimen", "general_life")
        assert tier == "secondary"

    def test_reference_is_reference(self):
        tier = get_tier_for_method("fengshui", "general_life")
        assert tier == "reference"


class TestAntiDeletion:
    """SEL-015: 如果少于 12 个术法直接报错。"""

    def test_less_than_12_user_methods_still_returns_12(self):
        """即使只指定 3 个术法，也填充到 12 法。"""
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei", "western"],
        )
        assert len(methods) == 12, (
            f"SEL-015 FAIL: only {len(methods)} methods returned!"
        )

    def test_specified_methods_are_in_result(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei"],
        )
        names = get_method_names(methods)
        assert "bazi_v2" in names
        assert "ziwei" in names

    def test_all_12_present_in_user_override(self):
        """验证填充后的 12 法包含所有 ALL_METHODS。"""
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2"],
        )
        names = get_method_names(methods)
        assert set(names) == set(ALL_METHODS)


class TestUserMethodOverride:
    """用户指定子集的行为。"""

    def test_user_specified_primary_keeps_tier(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "ziwei"],
        )
        bazi = next(m for m in methods if m["method"] == "bazi_v2")
        assert bazi["tier"] == "primary"

    def test_invalid_user_methods_are_filtered(self):
        methods = select_methods(
            goal="career",
            user_methods=["bazi_v2", "not_a_method", "also_fake"],
        )
        # should still have 12 valid methods
        names = get_method_names(methods)
        assert "not_a_method" not in names
        assert "also_fake" not in names
        assert len(names) == 12
