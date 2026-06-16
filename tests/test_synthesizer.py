"""REP-012~014: 报告生成器单元测试。

REP-012: free/standard/premium 三档报告都非空
REP-013: 标准版必须出现 18 个术法摘要 (Phase 1)
REP-014: 每份报告必须包含免责声明
"""
import pytest

from divination.aggregation.schema import (
    ConflictItem,
    ConsensusItem,
    DivinationSignal,
    ReadingReport,
    ValidationResult,
)
from divination.aggregation.synthesizer import (
    DISCLAIMER,
    synthesize_report,
    _generate_headline,
    _build_free,
    _build_standard,
    _build_premium,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sig(method="bazi_v2", domain="career", signal_key="career_stability",
         polarity="positive", strength=0.7, confidence=0.6, evidence="", advice=None):
    return DivinationSignal(
        method=method, domain=domain, signal_key=signal_key,
        polarity=polarity, strength=strength, confidence=confidence,
        evidence=evidence or f"{method} evidence",
        advice=advice,
    )


# Phase 1: 18 法全部纳入 (方案 §二十一)
ALL_18_METHODS = [
    "bazi_v2", "ziwei", "qimen", "liuyao", "meihua",
    "fengshui", "bazhai", "xuankong", "western", "vedic",
    "tarot", "numerology",
    "liuren", "xiaoliuren", "tieban", "lenormand",
    "hepan", "sigil",
]

SAMPLE_INTENT = {
    "goal": "career",
    "goal_label": "事业工作",
    "goal_confidence": 0.85,
    "goal_source": "classified",
    "sub_goals": ["career", "wealth"],
    "domain_scores": {"career": 1.0, "wealth": 0.4},
    "question": "我该换工作吗",
}

SAMPLE_CONSENSUS = [
    ConsensusItem(
        domain="career",
        theme="事业发展有利",
        supporting_methods=["bazi_v2", "ziwei", "western"],
        weight_strength=78,
        explanation="3种术法一致显示事业发展有利",
    )
]

SAMPLE_CONFLICT = ConflictItem(
    domain="career",
    severity="medium",
    positive_methods=["bazi_v2", "ziwei"],
    negative_methods=["qimen", "meihua"],
    neutral_methods=["liuyao"],
    conflict_explanation="career领域存在分歧",
    resolution="可在bazi_v2支持的方向上推进，同时留意qimen提示的关注点",
)


# ── Generate 18-method signals with at least one per method ───────────────────

def _make_18_method_signals():
    """每个术法至少产生一条信号 (Phase 1: 18 法)。"""
    signals = []
    # Distribute signals across methods
    domains = ["career", "wealth", "relationship", "self_life", "timing", "decision"]
    for i, method in enumerate(ALL_18_METHODS):
        domain = domains[i % len(domains)]
        signals.append(_sig(method, domain, "career_stability", "positive", 0.6, 0.5))
    return signals


# 向后兼容别名 (旧测试可能仍引用)
_make_12_method_signals = _make_18_method_signals


# ═══════════════════════════════════════════════════════════════════════════════
# REP-012: 三档报告都非空
# ═══════════════════════════════════════════════════════════════════════════════

class TestThreeTierReportsExist:
    """REP-012: free/standard/premium 三档报告都非空。"""

    def test_all_three_tiers_non_empty(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            conflicts=[SAMPLE_CONFLICT],
            overall_score=68.0,
            confidence=70.0,
            confidence_level="medium_high",
            risks=["career领域存在较强负面信号，建议谨慎对待"],
            timing={"summary": "时机信号中性"},
            action_advice=["可积极关注career领域", "建议谨慎决策"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)

        assert len(report.free) > 20, f"REP-012: free report too short ({len(report.free)} chars)"
        assert len(report.standard) > 100, f"REP-012: standard report too short ({len(report.standard)} chars)"
        assert len(report.premium) > 100, f"REP-012: premium report too short ({len(report.premium)} chars)"

    def test_free_report_contains_headline(self):
        """REP-002: free 报告第一段必须是 headline。"""
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            overall_score=68,
            confidence=70,
            confidence_level="medium_high",
            action_advice=["建议稳定发展"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "综合评分" in report.free, f"REP-002: free report missing headline with score"
        assert "速览" in report.free, f"Free report should have a quick overview title"

    def test_free_report_has_3_suggestions(self):
        """REP-003: free report 包含最多 3 条建议。"""
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            overall_score=68,
            confidence=70,
            confidence_level="medium_high",
            action_advice=["建议A", "建议B", "建议C", "建议D", "建议E"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "建议" in report.free
        # Count numbered suggestions
        numbered = [line for line in report.free.split("\n") if line.strip().startswith(("1.", "2.", "3."))]
        assert 1 <= len(numbered) <= 3, f"Expected 1-3 suggestions, got {len(numbered)}"


# ═══════════════════════════════════════════════════════════════════════════════
# REP-013: 18 法摘要完整
# ═══════════════════════════════════════════════════════════════════════════════

class Test12MethodSummary:
    """REP-013: 标准版必须出现 18 个术法摘要 (Phase 1)。"""

    def test_standard_contains_all_18_methods(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            conflicts=[SAMPLE_CONFLICT],
            overall_score=68,
            confidence=70,
            confidence_level="medium_high",
            action_advice=["建议谨慎决策"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        for method in ALL_18_METHODS:
            assert method in report.standard, (
                f"REP-013 FAIL: '{method}' not found in standard report"
            )

    def test_standard_contains_method_summary_section(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        # 摘要 section 标题兼容 12 / 18 — 接受两种写法
        assert ("12术法依据摘要" in report.standard or "18术法依据摘要" in report.standard), (
            f"REP-006: standard report missing method summary section"
        )

    def test_standard_contains_consensus_section(self):
        """REP-007: 标准版包含多法共识段落。"""
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "多术法共识" in report.standard, f"REP-007: missing consensus section"

    def test_standard_contains_conflict_section(self):
        """REP-008: 标准版包含多法冲突段落。"""
        signals = _make_18_method_signals()
        validation = ValidationResult(
            conflicts=[SAMPLE_CONFLICT],
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "术法分歧" in report.standard, f"REP-008: missing conflict section"


# ═══════════════════════════════════════════════════════════════════════════════
# REP-014: 免责声明
# ═══════════════════════════════════════════════════════════════════════════════

class TestDisclaimer:
    """REP-014: 每份报告必须包含免责声明。"""

    DISCLAIMER_KEYWORDS = ["免责声明", "仅供参考", "不构成"]

    def test_free_has_disclaimer(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        for kw in self.DISCLAIMER_KEYWORDS:
            assert kw in report.free, f"REP-014: FREE report missing '{kw}'"

    def test_standard_has_disclaimer(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        for kw in self.DISCLAIMER_KEYWORDS:
            assert kw in report.standard, f"REP-014: STANDARD report missing '{kw}'"

    def test_premium_has_disclaimer(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        for kw in self.DISCLAIMER_KEYWORDS:
            assert kw in report.premium, f"REP-014: PREMIUM report missing '{kw}'"


# ═══════════════════════════════════════════════════════════════════════════════
# REP-002: Headline
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeadline:
    def test_headline_contains_score(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        validation = ValidationResult(
            overall_score=72, confidence=68, confidence_level="medium_high",
        )
        headline = _generate_headline(signals, validation, "事业工作", "我该换工作吗")
        assert "72" in headline or "综合评分" in headline

    def test_headline_mentions_question_context(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        validation = ValidationResult(
            overall_score=55, confidence=50, confidence_level="medium",
        )
        headline = _generate_headline(signals, validation, "事业工作", "我该换工作吗")
        assert "我该换工作吗" in headline, f"Headline should mention question: {headline}"

    def test_headline_uses_cautious_language(self):
        """REP-009: 风险提醒使用谨慎表达，禁止绝对化。"""
        signals = [
            _sig("bazi_v2", "career", "career_pressure", "negative", 0.9, 0.8),
            _sig("ziwei", "career", "career_pressure", "negative", 0.85, 0.8),
        ]
        validation = ValidationResult(
            overall_score=30, confidence=45, confidence_level="low",
        )
        headline = _generate_headline(signals, validation, "事业工作", "我该换工作吗")
        # Must NOT contain absolute language
        forbidden = ["一定", "必然", "肯定", "绝对", "不可能"]
        for word in forbidden:
            assert word not in headline, f"REP-009: headline contains forbidden absolute word: '{word}'"


# ═══════════════════════════════════════════════════════════════════════════════
# REP-005: Premium details
# ═══════════════════════════════════════════════════════════════════════════════

class TestPremiumReport:
    def test_premium_contains_heatmap(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            consensus=SAMPLE_CONSENSUS,
            conflicts=[SAMPLE_CONFLICT],
            overall_score=68, confidence=70, confidence_level="medium_high",
            risks=["风险A", "风险B"],
            timing={"short_term_signals": 3, "medium_term_signals": 1, "long_term_signals": 2,
                    "timing_signals_count": 2, "favorable_count": 1, "unfavorable_count": 0,
                    "summary": "时机较有利"},
            action_advice=["建议A", "建议B"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "热力图" in report.premium, f"REP-005: premium missing heatmap"
        assert "贡献度排名" in report.premium, f"REP-005: premium missing contribution ranking"

    def test_premium_contains_risk_breakdown(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            conflicts=[SAMPLE_CONFLICT],
            overall_score=68, confidence=70, confidence_level="medium_high",
            risks=["风险A", "风险B"],
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "风险深度拆解" in report.premium, f"REP-005: premium missing risk breakdown"

    def test_premium_contains_followup_context(self):
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["建议"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        assert "追问上下文" in report.premium, f"REP-005: premium missing follow-up context"


# ═══════════════════════════════════════════════════════════════════════════════
# REP-010: Action advice language
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdviceLanguage:
    def test_advice_uses_suggestive_not_mandatory_language(self):
        """REP-010: 行动建议使用可执行建议，不做强制命令。"""
        signals = _make_18_method_signals()
        validation = ValidationResult(
            overall_score=68, confidence=70, confidence_level="medium_high",
            action_advice=["你必须辞职", "建议在当前岗位积累经验后再考虑变动"],
        )
        report = synthesize_report(signals, validation, SAMPLE_INTENT, ALL_18_METHODS)
        # "建议" should appear in at least one advice
        assert "建议" in report.standard or "可" in report.standard, (
            f"REP-010: advice should use suggestive language"
        )
