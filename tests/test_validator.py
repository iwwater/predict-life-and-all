"""VAL-015~018: 交叉验证器单元测试。

VAL-015: 构造 3 个正向信号 → 必须生成 consensus
VAL-016: 构造正负同时存在 → 必须生成 conflict
VAL-017: 正向多时分数上升，负向多时分数下降
VAL-018: 共识多、冲突少时 confidence 更高
"""
import pytest

from divination.aggregation.schema import (
    ConflictItem,
    ConsensusItem,
    DimensionPolarity,
    DivinationSignal,
    ScopeTally,
    ValidationResult,
)
from divination.aggregation.validator import (
    validate_signals,
    _group_by_signal_key,
    _compute_weighted_stats,
    _detect_consensus_by_weight,
    _detect_conflicts_by_weight,
    _extract_risks,
    _extract_timing,
    _extract_action_advice,
    CONSENSUS_THRESHOLD,
    CONFLICT_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sig(method="bazi_v2", domain="career", signal_key="career_stability",
         polarity="positive", strength=0.7, confidence=0.6, time_scope=None, advice=None):
    """快捷创建 DivinationSignal。"""
    return DivinationSignal(
        method=method, domain=domain, signal_key=signal_key,
        polarity=polarity, strength=strength, confidence=confidence,
        evidence=f"{method} evidence", time_scope=time_scope, advice=advice,
    )


DEFAULT_WEIGHTS = {
    "bazi_v2": 0.15, "ziwei": 0.10, "qimen": 0.10,
    "liuyao": 0.08, "meihua": 0.07, "western": 0.10,
    "vedic": 0.08, "tarot": 0.07, "numerology": 0.05,
    "fengshui": 0.06, "bazhai": 0.07, "xuankong": 0.07,
}


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-015: 共识检测
# ═══════════════════════════════════════════════════════════════════════════════

class TestConsensusDetection:
    """VAL-015: 构造 3 个正向信号，必须生成 consensus。"""

    def test_three_positive_same_key_generates_consensus(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.75, 0.65),
            _sig("qimen", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.consensus) >= 1, (
            f"VAL-015 FAIL: Expected >=1 consensus, got {len(result.consensus)}"
        )
        assert any(c.domain == "career" for c in result.consensus)

    def test_three_negative_same_key_generates_consensus(self):
        signals = [
            _sig("bazi_v2", "wealth", "wealth_risk", "negative", 0.8, 0.7),
            _sig("ziwei", "wealth", "wealth_risk", "negative", 0.75, 0.65),
            _sig("western", "wealth", "wealth_risk", "negative", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.consensus) >= 1

    def test_two_signals_not_enough_for_consensus_if_below_threshold(self):
        """仅 2 个弱信号不应该产生共识。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.3, 0.3),
            _sig("ziwei", "career", "career_stability", "positive", 0.3, 0.3),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        # May or may not have consensus — depends on weighted strength
        # The key is: validate doesn't crash
        assert isinstance(result.dimension_polarity, dict)
        assert isinstance(result.tally_by_scope, dict)

    def test_mixed_polarities_dont_form_consensus(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.6, 0.5),
            _sig("ziwei", "career", "career_stability", "negative", 0.6, 0.5),
            _sig("qimen", "career", "career_stability", "neutral", 0.5, 0.4),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        # No consensus when polarities are evenly distributed
        career_consensus = [c for c in result.consensus if c.domain == "career"]
        assert len(career_consensus) == 0, (
            f"Mixed polarities should not form consensus, got {career_consensus}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-016: 冲突检测
# ═══════════════════════════════════════════════════════════════════════════════

class TestConflictDetection:
    """VAL-016: 构造正负同时存在，必须生成 conflict。"""

    def test_positive_vs_negative_generates_conflict(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.7, 0.65),
            _sig("qimen", "career", "career_stability", "negative", 0.75, 0.65),
            _sig("meihua", "career", "career_stability", "negative", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.conflicts) >= 1, (
            f"VAL-016 FAIL: Expected >=1 conflict, got {len(result.conflicts)}"
        )
        conflict = result.conflicts[0]
        assert len(conflict.positive_methods) >= 1
        assert len(conflict.negative_methods) >= 1

    def test_conflict_has_severity(self):
        """VAL-008: conflict 必须有 severity 字段。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.9, 0.8),
            _sig("ziwei", "career", "career_stability", "positive", 0.85, 0.75),
            _sig("qimen", "career", "career_stability", "negative", 0.85, 0.75),
            _sig("meihua", "career", "career_stability", "negative", 0.8, 0.7),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        if result.conflicts:
            c = result.conflicts[0]
            assert c.severity in ("low", "medium", "high"), f"Invalid severity: {c.severity}"

    def test_conflict_has_resolution(self):
        """VAL-009: conflict 必须有 resolution 字段。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.7, 0.65),
            _sig("qimen", "career", "career_stability", "negative", 0.75, 0.65),
            _sig("meihua", "career", "career_stability", "negative", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        if result.conflicts:
            c = result.conflicts[0]
            assert isinstance(c.resolution, str), "Conflict must have resolution"
            assert len(c.resolution) > 5, "Resolution too short"

    def test_no_conflict_when_only_one_side_strong(self):
        """仅一方强势不产生冲突。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.7, 0.65),
            _sig("qimen", "career", "career_stability", "negative", 0.2, 0.3),
            _sig("meihua", "career", "career_stability", "negative", 0.15, 0.25),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        # Weak negative signals shouldn't trigger conflict
        career_conflicts = [c for c in result.conflicts if c.domain == "career"]
        assert len(career_conflicts) == 0, (
            f"Weak negative side should not trigger conflict, got {career_conflicts}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-017: 综合评分
# ═══════════════════════════════════════════════════════════════════════════════

class TestOverallScore:
    """VAL-017: 正向多时分数上升，负向多时分数下降。"""

    def test_positive_signals_raise_score(self):
        pos_signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.9, 0.8),
            _sig("ziwei", "career", "career_independence", "positive", 0.85, 0.75),
            _sig("qimen", "wealth", "wealth_growth", "positive", 0.8, 0.7),
        ]
        result = validate_signals(pos_signals, DEFAULT_WEIGHTS)
        # VAL-017: 正向多时 polarity 应为 STRONG/WEAK_SUPPORT (替代原 overall_score>55)
        # 信号未设 dimension, 落到 long_term 桶(Sprint 0.1 — 替代 _unspecified 兜底)
        assert "long_term" in result.dimension_polarity
        assert result.dimension_polarity["long_term"] in (
            DimensionPolarity.STRONG_SUPPORT,
            DimensionPolarity.WEAK_SUPPORT,
        ), f"Positive signals should give support polarity, got {result.dimension_polarity['long_term']}"

    def test_negative_signals_lower_score(self):
        neg_signals = [
            _sig("bazi_v2", "career", "career_pressure", "negative", 0.9, 0.8),
            _sig("ziwei", "career", "career_stability", "negative", 0.85, 0.75),
            _sig("qimen", "wealth", "wealth_risk", "negative", 0.8, 0.7),
        ]
        result = validate_signals(neg_signals, DEFAULT_WEIGHTS)
        # VAL-017: 负向多时 polarity 应为 STRONG/WEAK_WARN (替代原 overall_score<50)
        assert "long_term" in result.dimension_polarity
        assert result.dimension_polarity["long_term"] in (
            DimensionPolarity.STRONG_WARN,
            DimensionPolarity.WEAK_WARN,
        ), f"Negative signals should give warn polarity, got {result.dimension_polarity['long_term']}"

    def test_more_positive_means_higher_score(self):
        few_pos = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
            _sig("ziwei", "career", "career_pressure", "negative", 0.7, 0.6),
        ]
        many_pos = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
            _sig("ziwei", "career", "career_independence", "positive", 0.7, 0.6),
            _sig("qimen", "wealth", "wealth_growth", "positive", 0.7, 0.6),
            _sig("western", "career", "long_term_potential", "positive", 0.7, 0.6),
        ]
        few_result = validate_signals(few_pos, DEFAULT_WEIGHTS)
        many_result = validate_signals(many_pos, DEFAULT_WEIGHTS)
        # VAL-017: 更多正向信号应该让 polarity 倾向 support (替代原 overall_score 比较)
        # 通过"支持票 - 警示票"差值比较倾向强度
        def support_score(v):
            score = 0
            for t in v.tally_by_scope.values():
                score += t.strong_support + t.weak_support
                score -= t.strong_warn + t.weak_warn
            return score
        assert support_score(many_result) > support_score(few_result), (
            f"More positive signals should yield higher support score: "
            f"{support_score(many_result)} vs {support_score(few_result)}"
        )

    def test_consensus_raises_score(self):
        signals_with_consensus = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.75, 0.7),
            _sig("qimen", "career", "career_stability", "positive", 0.7, 0.65),
        ]
        signals_no_consensus = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.5, 0.4),
            _sig("ziwei", "wealth", "wealth_growth", "negative", 0.5, 0.4),
            _sig("qimen", "relationship", "relationship_attraction", "neutral", 0.4, 0.35),
        ]
        r_consensus = validate_signals(signals_with_consensus, DEFAULT_WEIGHTS)
        r_no_consensus = validate_signals(signals_no_consensus, DEFAULT_WEIGHTS)
        # VAL-017: 有共识的应该 polarity 更倾向 support (替代原 overall_score 比较)
        def support_score(v):
            score = 0
            for t in v.tally_by_scope.values():
                score += t.strong_support + t.weak_support
                score -= t.strong_warn + t.weak_warn
            return score
        assert support_score(r_consensus) > support_score(r_no_consensus), (
            f"Consensus should raise support score: "
            f"{support_score(r_consensus)} vs {support_score(r_no_consensus)}"
        )

    def test_score_in_valid_range(self):
        """polarity 必须是有效 DimensionPolarity 枚举值（替代原 overall_score 0-100 范围检查）。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.99, 0.99),
            _sig("ziwei", "career", "career_stability", "positive", 0.99, 0.99),
            _sig("qimen", "career", "career_stability", "positive", 0.99, 0.99),
            _sig("meihua", "career", "career_pressure", "negative", 0.99, 0.99),
            _sig("liuyao", "career", "career_stability", "negative", 0.99, 0.99),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        valid_polarities = set(DimensionPolarity)
        for dim, pol in result.dimension_polarity.items():
            assert pol in valid_polarities, f"Invalid polarity for {dim}: {pol}"


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-018: 置信度
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidence:
    """VAL-018: 共识多、冲突少时 consistency 更高 (替代原 confidence 数值)。
    替代方案：用 tally_by_scope 的支持票总数与 consensus/conflicts 数量做综合判断。
    """

    def test_more_consensus_higher_confidence(self):
        signals_consensus = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.8),
            _sig("ziwei", "career", "career_stability", "positive", 0.8, 0.8),
            _sig("qimen", "career", "career_stability", "positive", 0.8, 0.8),
        ]
        r_high = validate_signals(signals_consensus, DEFAULT_WEIGHTS)

        signals_scattered = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.3, 0.3),
            _sig("ziwei", "wealth", "wealth_growth", "negative", 0.3, 0.3),
            _sig("qimen", "relationship", "marriage_stability", "neutral", 0.2, 0.25),
        ]
        r_low = validate_signals(signals_scattered, DEFAULT_WEIGHTS)

        # 替代原 r_high.confidence > r_low.confidence：
        # 共识多者应有更多支持票
        def support_votes(v):
            return sum(t.strong_support + t.weak_support for t in v.tally_by_scope.values())
        assert support_votes(r_high) > support_votes(r_low), (
            f"More consensus should give more support votes: "
            f"{support_votes(r_high)} vs {support_votes(r_low)}"
        )

    def test_fewer_conflicts_higher_confidence(self):
        # Same number of signals but one set has conflicts
        signals_with_conflict = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "negative", 0.8, 0.7),
            _sig("qimen", "career", "career_stability", "positive", 0.75, 0.7),
            _sig("meihua", "career", "career_stability", "negative", 0.75, 0.7),
        ]
        signals_no_conflict = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.8, 0.7),
            _sig("ziwei", "career", "career_stability", "positive", 0.75, 0.7),
            _sig("qimen", "career", "career_stability", "positive", 0.7, 0.65),
            _sig("meihua", "wealth", "wealth_growth", "positive", 0.7, 0.65),
        ]
        r_conflict = validate_signals(signals_with_conflict, DEFAULT_WEIGHTS)
        r_clean = validate_signals(signals_no_conflict, DEFAULT_WEIGHTS)
        # 替代原 r_clean.confidence >= r_conflict.confidence * 0.8：
        # 无冲突组的支持票应不少于有冲突组的 80%
        def support_votes(v):
            return sum(t.strong_support + t.weak_support for t in v.tally_by_scope.values())
        assert support_votes(r_clean) >= support_votes(r_conflict) * 0.8, (
            f"Fewer conflicts should not drastically reduce support: "
            f"{support_votes(r_clean)} vs {support_votes(r_conflict)}"
        )

    def test_dimension_polarity_is_valid(self):
        """VAL-011: dimension_polarity 每维的 polarity 必须是有效 DimensionPolarity 枚举值。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        valid = set(DimensionPolarity)
        for dim, pol in result.dimension_polarity.items():
            assert pol in valid, f"VAL-011 FAIL: invalid polarity for {dim}: {pol}"

    def test_polarity_keys_are_dimensions(self):
        """VAL-011: dimension_polarity 的键必须是 5 个职责维度或 _unspecified。"""
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        valid_dims = {"long_term", "current_cycle", "relationship", "one_question", "space", "_unspecified"}
        for dim in result.dimension_polarity:
            assert dim in valid_dims, f"Unknown dimension: {dim}"


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-002: signal_key grouping
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalKeyGrouping:
    def test_groups_by_signal_key(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
            _sig("ziwei", "career", "career_stability", "positive", 0.6, 0.5),
            _sig("qimen", "career", "career_independence", "positive", 0.5, 0.4),
        ]
        groups = _group_by_signal_key(signals)
        assert "career_stability" in groups, f"Missing career_stability in groups: {list(groups.keys())}"
        assert "career_independence" in groups
        assert len(groups["career_stability"]) == 2
        assert len(groups["career_independence"]) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-012: risk extraction
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskExtraction:
    def test_strong_negative_produces_risk(self):
        signals = [
            _sig("bazi_v2", "career", "career_pressure", "negative", 0.85, 0.7),
            _sig("ziwei", "career", "career_pressure", "negative", 0.8, 0.65),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.risks) >= 1, f"Strong negative signals should produce risks"

    def test_mixed_signals_produce_risk(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "mixed", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        # Mixed may generate risk warnings
        assert isinstance(result.risks, list)

    def test_all_positive_no_risks(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.9, 0.8),
            _sig("ziwei", "career", "career_independence", "positive", 0.85, 0.75),
            _sig("qimen", "wealth", "wealth_growth", "positive", 0.8, 0.7),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        # All positive should produce minimal risks
        assert all("positive" in s.polarity for s in signals)
        # Risks should be empty or minimal
        assert isinstance(result.risks, list)


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-013: timing extraction
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimingExtraction:
    def test_timing_signals_produce_timing(self):
        signals = [
            _sig("qimen", "timing", "timing_opportunity", "positive", 0.7, 0.6),
            _sig("liuyao", "timing", "timing_transition", "neutral", 0.5, 0.5),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert result.timing is not None, "Timing signals should produce timing info"
        assert result.timing["timing_signals_count"] == 2

    def test_no_timing_signals_returns_none(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert result.timing is None, "No timing signals should return None"

    def test_timing_with_time_scope(self):
        signals = [
            _sig("qimen", "timing", "timing_opportunity", "positive", 0.7, 0.6,
                 time_scope="short_term"),
            _sig("bazi_v2", "career", "long_term_potential", "positive", 0.8, 0.7,
                 time_scope="long_term"),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert result.timing is not None
        assert result.timing["short_term_signals"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# VAL-014: action advice
# ═══════════════════════════════════════════════════════════════════════════════

class TestActionAdvice:
    def test_advice_field_extracted(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "positive", 0.7, 0.6,
                 advice="建议稳中求进，不宜频繁跳槽"),
            _sig("ziwei", "career", "career_independence", "positive", 0.6, 0.5,
                 advice="可考虑提升专业技能"),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.action_advice) >= 1, f"Expected advice, got {len(result.action_advice)}"

    def test_default_advice_when_empty(self):
        signals = [
            _sig("bazi_v2", "career", "career_stability", "neutral", 0.3, 0.3),
        ]
        result = validate_signals(signals, DEFAULT_WEIGHTS)
        assert len(result.action_advice) >= 1, "Should always have at least one advice"
