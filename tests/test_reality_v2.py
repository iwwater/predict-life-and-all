"""Sprint 1.6 — reality 声明式 + 安全转介测试。

覆盖:
- CONSTRAINT_RULES 各 rule 触发
- requires_signal 修饰
- SAFETY_REFERRALS 关键词扫描
- 优先级 high > medium > low
- list_active_rules() / check_safety_referral() 公共 API
- 向后兼容: RealityResult 字段完整
"""
from __future__ import annotations

import pytest

from divination.aggregation.reality import (
    CONSTRAINT_RULES,
    SAFETY_REFERRALS,
    ConstraintRule,
    RealityConstraintEngine,
    check_safety_referral,
    list_active_rules,
)
from divination.aggregation.schema import DivinationSignal, RealityConstraints


def _sig(domain: str, polarity: str, strength: float = 0.7,
         method: str = "bazi_v2") -> DivinationSignal:
    return DivinationSignal(
        method=method, domain=domain, signal_key="test",
        polarity=polarity, strength=strength, evidence="", time_scope="long_term",
    )


# ── 规则触发 ─────────────────────────────────────────────────────────

class TestConstraintRules:
    """声明式规则触发测试。"""

    def test_cash_severe_shortage(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(cash_reserve_months=0)
        # 给正向 career 信号, requires_signal 满足
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert any(w.rule_id == "cash_severe_shortage" for w in r.warnings)

    def test_cash_low(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(cash_reserve_months=2)
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert any(w.rule_id == "cash_low" for w in r.warnings)
        assert any(w.severity == "medium" for w in r.warnings if w.rule_id == "cash_low")

    def test_cash_high_no_warning(self):
        """现金充裕 → 不警告。"""
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(cash_reserve_months=12)
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert not any("cash" in w.rule_id for w in r.warnings if w.rule_id)

    def test_contract_only_verbal(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(has_formal_contract=False)
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert any(w.rule_id == "contract_only_verbal" for w in r.warnings)

    def test_health_poor_high(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(health_status="poor")
        r = engine.evaluate([], constraints)
        assert any(w.rule_id == "health_poor" and w.severity == "high" for w in r.warnings)

    def test_health_fair_medium(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(health_status="fair")
        r = engine.evaluate([], constraints)
        assert any(w.rule_id == "health_fair" and w.severity == "medium" for w in r.warnings)

    def test_no_constraints_no_warnings(self):
        engine = RealityConstraintEngine()
        r = engine.evaluate([], None)
        assert r.warnings == []
        assert r.has_warnings is False


# ── requires_signal 修饰 ───────────────────────────────────────────

class TestRequiresSignal:
    """requires_signal 限制: 命理信号不匹配时, 规则不触发。"""

    def test_cash_low_requires_career_positive(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(cash_reserve_months=2)
        # 无 career 正向信号 → cash_low 不触发
        signals = [_sig("health", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert not any(w.rule_id == "cash_low" for w in r.warnings)

    def test_cash_low_triggers_with_career_positive(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(cash_reserve_months=2)
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        assert any(w.rule_id == "cash_low" for w in r.warnings)


# ── 安全转介 ────────────────────────────────────────────────────────

class TestSafetyReferral:
    """健康/法财/法律关键词 → 自动转介。"""

    def test_medical_keyword_triggers_referral(self):
        engine = RealityConstraintEngine()
        r = engine.evaluate(
            signals=[],
            constraints=None,
            question="我的癌症能治好吗",
        )
        assert "medical_downgrade" in r.safety_flags
        assert any("医疗" in m for m in r.safety_messages)

    def test_investment_keyword_triggers_referral(self):
        engine = RealityConstraintEngine()
        r = engine.evaluate(
            signals=[],
            constraints=None,
            question="全仓梭哈某只股票",
        )
        assert "investment_downgrade" in r.safety_flags

    def test_legal_keyword_triggers_referral(self):
        engine = RealityConstraintEngine()
        r = engine.evaluate(
            signals=[],
            constraints=None,
            question="我能不能离婚",
        )
        assert "legal_downgrade" in r.safety_flags

    def test_no_keyword_no_referral(self):
        engine = RealityConstraintEngine()
        r = engine.evaluate(
            signals=[],
            constraints=None,
            question="我该换工作吗",
        )
        assert r.safety_flags == []
        assert r.safety_messages == []

    def test_multiple_referrals_combined(self):
        """一个问题同时含医疗+投资 → 两个 flag。"""
        engine = RealityConstraintEngine()
        r = engine.evaluate(
            signals=[],
            constraints=None,
            question="重病后全仓梭哈",
        )
        assert "medical_downgrade" in r.safety_flags
        assert "investment_downgrade" in r.safety_flags


# ── check_safety_referral 便捷 API ─────────────────────────────────

class TestCheckSafetyReferral:
    def test_returns_flags(self):
        flags = check_safety_referral("我的癌症能治好吗")
        assert "medical_downgrade" in flags

    def test_no_keyword_empty_list(self):
        flags = check_safety_referral("我该换工作吗")
        assert flags == []

    def test_dedup(self):
        """同一 referral 多关键词, 只加 1 次。"""
        flags = check_safety_referral("癌症 肿瘤 绝症")
        # 多次匹配 medical_downgrade → 只 1 个
        assert flags.count("medical_downgrade") == 1


# ── 优先级 high > medium > low ─────────────────────────────────────

class TestPriorityOrder:
    def test_adjusted_advice_high_first(self):
        engine = RealityConstraintEngine()
        constraints = RealityConstraints(
            cash_reserve_months=0,        # → cash_severe_shortage (high)
            has_qualification=False,      # → qualification_missing (medium)
        )
        signals = [_sig("career", "positive", 0.7)]
        r = engine.evaluate(signals, constraints)
        # high 应在 medium 之前
        advice = r.adjusted_advice
        if len(advice) >= 2:
            # 第一条应来自 high warning
            high_advice = next((w.signal_adjusted for w in r.warnings if w.severity == "high"), None)
            assert advice[0] == high_advice


# ── 公共 API ────────────────────────────────────────────────────────

class TestPublicAPI:
    def test_list_active_rules(self):
        rules = list_active_rules()
        assert len(rules) >= 5
        for r in rules:
            assert "id" in r
            assert "field" in r
            assert "severity" in r

    def test_engine_has_evaluate(self):
        engine = RealityConstraintEngine()
        assert hasattr(engine, "evaluate")

    def test_safety_referrals_defined(self):
        assert len(SAFETY_REFERRALS) == 3  # medical / investment / legal

    def test_constraint_rules_have_unique_ids(self):
        ids = [r.id for r in CONSTRAINT_RULES]
        assert len(ids) == len(set(ids)), f"重复 ID: {[i for i in ids if ids.count(i) > 1]}"
