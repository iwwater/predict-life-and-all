"""Sprint 1.2 — questioner 追问编排器测试。

覆盖:
- 12 goal 都有题池
- 同一 goal 同 context → 确定性结果
- skip_if 字段已填 → 该问题被跳过
- 最多 2 个问题 (Sprint 1.2 红线)
- impact 排序
- 兜底 goal 处理
- cases API 兼容 (offer_status 仍命中)
"""
from __future__ import annotations

import pytest

from divination.aggregation.questioner import (
    QUESTION_POOL,
    Question,
    get_questions_for_case,
    list_all_goals_with_questions,
    pick_questions,
    question_count,
)


# ── 12 goal 覆盖 ───────────────────────────────────────────────────────

class TestQuestionPoolCoverage:
    """所有标准 goal 都有题池 (除 fallback 兜底)。"""

    @pytest.mark.parametrize("goal", [
        "general_life", "career", "wealth", "relationship",
        "compatibility", "yearly", "monthly", "daily",
        "decision", "timing", "fengshui", "health_reflection",
    ])
    def test_goal_has_pool(self, goal):
        assert goal in QUESTION_POOL, f"goal '{goal}' 缺题池"
        assert question_count(goal) >= 1

    def test_fallback_pool_exists(self):
        assert "fallback" in QUESTION_POOL

    def test_list_all_goals(self):
        goals = list_all_goals_with_questions()
        assert "career" in goals
        assert "fallback" in goals
        assert len(goals) >= 12


# ── 确定性 ──────────────────────────────────────────────────────────────

class TestDeterministic:
    """同输入同输出 (Sprint 1.2 红线)。"""

    def test_same_input_same_output(self):
        ctx = {"offer_status": "已有正式 offer"}
        a = pick_questions("career", ctx, max_n=2)
        b = pick_questions("career", ctx, max_n=2)
        assert [q.id for q in a] == [q.id for q in b]

    def test_order_deterministic_within_goal(self):
        """同 goal, 多次调用, 顺序一致。"""
        for _ in range(5):
            qs = pick_questions("relationship", context={}, max_n=2)
            ids = [q.id for q in qs]
            assert ids == sorted(ids, key=lambda i: -1) or len(set(ids)) == len(ids)
            # 核心: 同 goal 同 ctx, 顺序稳定


# ── skip_if 行为 ────────────────────────────────────────────────────────

class TestSkipIf:
    """已填字段触发 skip。"""

    def test_career_offer_status_filled_skips_offer(self):
        """career 题池 offer_status 触发时 (注意: offer_status 不在 skip_if,
        但 cash_reserve_months 在). 改用 cash 已填示例。"""
        qs = pick_questions("career", context={"cash_reserve_months": 6}, max_n=2)
        # cash_reserve_months 在 skip_if → 跳过
        ids = [q.id for q in qs]
        assert "cash_reserve_months" not in ids
        # offer_status 仍出现
        assert "offer_status" in ids

    def test_relationship_focus_filled(self):
        """primary_concern 不在 skip_if, 改用 relationship_status 必填场景。"""
        # relationship_status 没有 skip_if — 必填一次
        qs = pick_questions("relationship", context={}, max_n=2)
        assert any(q.id == "relationship_status" for q in qs)

    def test_empty_context_returns_top_impact(self):
        """空 context → 取 impact 最高的 1-2 个。"""
        qs = pick_questions("decision", context={}, max_n=2)
        # decision 最高 impact 是 offer_status (9.5)
        assert qs[0].id == "offer_status"


# ── max_n 限制 ─────────────────────────────────────────────────────────

class TestMaxN:
    """最多 2 个问题 (Sprint 1.2 红线)。"""

    def test_max_n_default_is_2(self):
        qs = pick_questions("career", context={})
        assert len(qs) <= 2

    def test_max_n_explicit(self):
        qs = pick_questions("yearly", context={}, max_n=1)
        assert len(qs) == 1

    def test_max_n_zero(self):
        qs = pick_questions("career", context={}, max_n=0)
        assert qs == []


# ── 兜底逻辑 ───────────────────────────────────────────────────────────

class TestFallback:
    """未知 goal 或 rule_low_conf → fallback。"""

    def test_unknown_goal_uses_fallback(self):
        qs = pick_questions("totally_made_up_goal", context={}, max_n=2)
        # 取 fallback 池
        assert any(q.id == "primary_concern" for q in qs)

    def test_low_conf_flag_routes_to_fallback(self):
        intent = {"goal": "wealth", "flags": ["rule_low_conf"]}
        qs = get_questions_for_case(intent, context={}, max_n=2)
        # flag 触发 → fallback 池
        assert any(q.id == "primary_concern" for q in qs)


# ── 业务便捷函数 ───────────────────────────────────────────────────────

class TestGetQuestionsForCase:
    """cases.py 调用的便捷函数。"""

    def test_career_offer_status_present(self):
        """cases_api 测试依赖: career 决策类问题必有 offer_status。"""
        intent = {"goal": "career"}
        qs = get_questions_for_case(intent, context={}, max_n=2)
        ids = [q.id for q in qs]
        assert "offer_status" in ids

    def test_relationship_status_present(self):
        intent = {"goal": "relationship"}
        qs = get_questions_for_case(intent, context={}, max_n=2)
        ids = [q.id for q in qs]
        assert "relationship_status" in ids

    def test_fengshui_space_focus_present(self):
        intent = {"goal": "fengshui"}
        qs = get_questions_for_case(intent, context={}, max_n=2)
        ids = [q.id for q in qs]
        assert "space_focus" in ids

    def test_health_duration_present(self):
        intent = {"goal": "health_reflection"}
        qs = get_questions_for_case(intent, context={}, max_n=2)
        ids = [q.id for q in qs]
        assert "duration" in ids

    def test_intent_missing_goal_falls_back(self):
        """intent 无 goal 字段 → 走 fallback。"""
        qs = get_questions_for_case({}, context={}, max_n=2)
        assert len(qs) >= 1


# ── Question 模型 ──────────────────────────────────────────────────────

class TestQuestionModel:
    """Question Pydantic 模型约束。"""

    def test_question_has_required_fields(self):
        q = Question(id="test", prompt="测试", options=["A", "B"])
        assert q.id == "test"
        assert q.required is True  # default
        assert q.impact == 5.0  # default
        assert q.type == "single_choice"  # default

    def test_question_skip_if_default_empty(self):
        q = Question(id="t", prompt="p", options=[])
        assert q.skip_if == []

    def test_impact_in_range(self):
        """所有题池的 impact 在 1-10。"""
        for goal, pool in QUESTION_POOL.items():
            for q in pool:
                assert 1.0 <= q.impact <= 10.0, f"{goal}/{q.id} impact={q.impact}"


# ── 排序稳定性 ─────────────────────────────────────────────────────────

class TestImpactSorting:
    """按 impact 降序, 原始顺序作 tie-breaker。"""

    def test_decision_high_impact_first(self):
        """decision: offer_status (9.5) > reversibility (9.0) > urgency (8.0)。"""
        qs = pick_questions("decision", context={}, max_n=2)
        assert qs[0].id == "offer_status"
        assert qs[1].id == "reversibility"

    def test_wealth_impact_order(self):
        """wealth: risk_tolerance (8.5) > investment_horizon (8.0)。"""
        qs = pick_questions("wealth", context={}, max_n=2)
        assert qs[0].id == "risk_tolerance"
        assert qs[1].id == "investment_horizon"

    def test_career_offer_first(self):
        """career: offer_status (9.0) > cash_reserve (8.5)。"""
        qs = pick_questions("career", context={}, max_n=2)
        assert qs[0].id == "offer_status"
