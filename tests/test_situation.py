"""Sprint 1.3 — situation 境限装配测试。

覆盖:
- 7 维度都建得出来
- 字段缺失 → None, 不抛
- degraded_dims 标记正确
- to_summary 压缩后含 7 维关键信息
- is_ready / missing_dims 接口
- context_answers → time.urgency / event.concern / condition.cash 注入
- 时间 horizon 按 goal 派生
"""
from __future__ import annotations

import pytest

from divination.aggregation.intent import classify_intent
from divination.aggregation.situation import (
    SituationContext,
    build_situation,
    is_ready,
    missing_dims,
    to_summary,
)
from divination.aggregation.schema import BirthModel, ReadingRequest, RealityConstraints, SpaceModel


# ── 7 维度子模型存在 ─────────────────────────────────────────────────

class TestSevenDims:
    """7 维度都装配。"""

    def test_all_seven_dims_present(self):
        req = ReadingRequest(question="我该换工作吗")
        sit = build_situation(req)
        assert isinstance(sit, SituationContext)
        assert sit.person is not None
        assert sit.event is not None
        assert sit.time is not None
        assert sit.space is not None
        assert sit.condition is not None
        assert sit.method is not None
        # counterpart 可空 (无 target_birth)
        assert sit.counterpart is None

    def test_person_with_birth(self):
        req = ReadingRequest(
            question="我该换工作吗",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req)
        assert sit.person.birth is not None
        assert sit.person.is_present is True
        assert sit.person.gender == "unspecified"  # default


# ── 字段缺失降级 ───────────────────────────────────────────────────────

class TestDegradedDims:
    """字段缺失 → degraded_dims 标记。"""

    def test_no_birth_marks_degraded(self):
        req = ReadingRequest(question="整体运势")  # 无 birth
        sit = build_situation(req)
        assert "person.birth" in sit.degraded_dims

    def test_relationship_without_target_marks_counterpart(self):
        req = ReadingRequest(
            question="我和他的姻缘",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        intent = {"goal": "relationship"}
        sit = build_situation(req, intent=intent)
        assert "counterpart" in sit.degraded_dims

    def test_fengshui_without_sitting_marks_space(self):
        req = ReadingRequest(
            question="房子风水",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        intent = {"goal": "fengshui"}
        sit = build_situation(req, intent=intent)
        assert "space.sitting" in sit.degraded_dims

    def test_fully_loaded_is_ready(self):
        req = ReadingRequest(
            question="我该换工作吗",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
            space=SpaceModel(sitting="子", period=8, construction_year=2010),
            constraints=RealityConstraints(
                cash_reserve_months=6, has_formal_contract=True,
                health_status="good", has_qualification=True,
            ),
        )
        sit = build_situation(req)
        assert is_ready(sit)
        assert missing_dims(sit) == []


# ── context_answers 注入 ─────────────────────────────────────────────

class TestContextAnswersInjection:
    """用户答的追问 → 自动注入对应维度。"""

    def test_urgency_injection(self):
        req = ReadingRequest(
            question="我该不该辞职",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        intent = {"goal": "decision"}
        sit = build_situation(
            req, intent=intent,
            context_answers={"urgency": "<1 周"},
        )
        assert sit.event.urgency == "critical"

    def test_deadline_injection(self):
        req = ReadingRequest(
            question="什么时候能结婚",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        intent = {"goal": "timing"}
        sit = build_situation(
            req, intent=intent,
            context_answers={"deadline": "有明确截止 (如合同/签证)"},
        )
        assert sit.time.deadline is not None
        assert sit.time.is_deadline_hard is True

    def test_no_deadline_means_soft(self):
        req = ReadingRequest(
            question="什么时候能结婚",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(
            req, intent={"goal": "timing"},
            context_answers={"deadline": "没期限, 想知道'最佳'"},
        )
        assert sit.time.is_deadline_hard is False

    def test_cash_reserve_fallback(self):
        """无 constraints 但 context_answers 有 cash_reserve_months → 注入。"""
        req = ReadingRequest(
            question="我该换工作吗",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(
            req,
            context_answers={"cash_reserve_months": 3},
        )
        assert sit.condition.cash_reserve_months == 3


# ── time horizon 按 goal 派生 ───────────────────────────────────────

class TestTimeHorizon:
    @pytest.mark.parametrize("goal,expected", [
        ("daily", "now"),
        ("monthly", "short_term"),
        ("yearly", "medium_term"),
        ("decision", "short_term"),
        ("timing", "short_term"),
        ("career", "medium_term"),
        ("wealth", "medium_term"),
        ("general_life", "long_term"),
        ("compatibility", "long_term"),
    ])
    def test_horizon_mapping(self, goal, expected):
        req = ReadingRequest(
            question=f"测{goal}",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": goal})
        assert sit.time.horizon == expected

    def test_cycles_for_daily(self):
        req = ReadingRequest(
            question="今日运势",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": "daily"})
        assert "日运" in sit.time.cycles

    def test_cycles_for_yearly(self):
        req = ReadingRequest(
            question="今年运势",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": "yearly"})
        assert "流年" in sit.time.cycles


# ── to_summary 压缩 ─────────────────────────────────────────────────

class TestToSummary:
    def test_summary_keys(self):
        req = ReadingRequest(
            question="我该换工作吗",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": "career"})
        s = to_summary(sit)
        assert "person" in s
        assert "event" in s
        assert "time" in s
        assert "space" in s
        assert "condition_filled" in s
        assert "method" in s
        assert "degraded_dims" in s

    def test_summary_event_type(self):
        req = ReadingRequest(
            question="财运",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": "wealth"})
        s = to_summary(sit)
        assert s["event"]["type"] == "wealth"

    def test_summary_condition_filled_count(self):
        req = ReadingRequest(
            question="我该换工作吗",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
            constraints=RealityConstraints(
                cash_reserve_months=6, has_formal_contract=True,
            ),
        )
        sit = build_situation(req)
        s = to_summary(sit)
        assert s["condition_filled"] == 2


# ── counterpart 装配 ───────────────────────────────────────────────

class TestCounterpart:
    def test_target_birth_builds_counterpart(self):
        req = ReadingRequest(
            question="我俩合不合",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
            target_birth=BirthModel(year=1992, month=3, day=20, hour=10, minute=0),
        )
        sit = build_situation(req, intent={"goal": "compatibility"})
        assert sit.counterpart is not None
        assert sit.counterpart.birth is not None
        assert "counterpart" not in sit.degraded_dims

    def test_no_target_birth_no_counterpart(self):
        req = ReadingRequest(
            question="整体运势",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req, intent={"goal": "general_life"})
        assert sit.counterpart is None


# ── Method 装配 ────────────────────────────────────────────────────

class TestMethod:
    def test_user_specified(self):
        req = ReadingRequest(
            question="整体运势",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
            methods=["bazi_v2", "ziwei"],
        )
        sit = build_situation(req)
        assert sit.method.is_user_specified is True
        assert set(sit.method.selected_methods) == {"bazi_v2", "ziwei"}

    def test_default_no_methods(self):
        req = ReadingRequest(
            question="整体运势",
            birth=BirthModel(year=1990, month=6, day=15, hour=8, minute=30),
        )
        sit = build_situation(req)
        assert sit.method.is_user_specified is False
        assert sit.method.selected_methods == []
