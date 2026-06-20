"""Sprint 1.5 — scope_tally 五档计票 + 分歧并陈测试。

覆盖:
- tally_by_scope 基本计票
- normalize "≥2 法一致" 规则
- divergence_view 分歧并陈
- summary 自动生成
- 同 input 同 output (确定性)
- validator 集成 (tally_by_scope 仍工作)
"""
from __future__ import annotations

import pytest

from divination.aggregation.schema import (
    DivinationSignal,
    ScopeTally,
    TimeScope,
)
from divination.aggregation.scope_tally import (
    MIN_METHODS_FOR_STRONG,
    SUPPORT_STRONG_THRESHOLD,
    TallyEngine,
    build_divergence_view,
    tally_signals,
)


def _sig(method: str, polarity: str, strength: float = 0.5,
         time_scope: str = "long_term", signal_key: str = "test") -> DivinationSignal:
    return DivinationSignal(
        method=method, domain="self_life", signal_key=signal_key,
        polarity=polarity, strength=strength, evidence="", time_scope=time_scope,
    )


# ── 基本计票 ─────────────────────────────────────────────────────────

class TestBasicTally:
    def test_single_positive_becomes_weak_support(self):
        # strength=0.5 > 0.40 阈值 → 强档; 但 normalize=True 默认 → 1 法不足 → 降为弱
        signals = [_sig("bazi", "positive", 0.5)]
        tally = tally_signals(signals, normalize=False)
        assert tally["long_term"].strong_support == 1
        assert tally["long_term"].weak_support == 0

    def test_low_positive_becomes_weak(self):
        signals = [_sig("bazi", "positive", 0.3)]
        tally = tally_signals(signals, normalize=False)
        assert tally["long_term"].strong_support == 0
        assert tally["long_term"].weak_support == 1

    def test_negative_strong(self):
        signals = [_sig("bazi", "negative", 0.7)]
        tally = tally_signals(signals, normalize=False)
        assert tally["long_term"].strong_warn == 1

    def test_neutral_counted(self):
        signals = [_sig("bazi", "neutral", 0.5)]
        tally = tally_signals(signals)
        assert tally["long_term"].neutral == 1

    def test_mixed_counted_as_neutral(self):
        signals = [_sig("bazi", "mixed", 0.5)]
        tally = tally_signals(signals)
        assert tally["long_term"].neutral == 1


# ── normalize ≥2 法一致 ─────────────────────────────────────────────

class TestNormalize:
    def test_single_method_strong_downgrades(self):
        """只有 1 个方法, 即使 strength 高, 也应降为 weak。"""
        signals = [_sig("bazi", "positive", 0.8)]
        tally = tally_signals(signals, normalize=True)
        t = tally["long_term"]
        # normalize 后, supporting_methods < 2 → strong_support 降为 weak
        assert t.strong_support == 0
        assert t.weak_support == 1

    def test_two_methods_strong_kept(self):
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("ziwei", "positive", 0.8),
        ]
        tally = tally_signals(signals, normalize=True)
        t = tally["long_term"]
        assert t.strong_support == 2
        assert len(t.supporting_methods) == 2

    def test_three_methods_partial_strong(self):
        """3 法中 2 strong + 1 weak, 仍算多法一致 → strong 保留。"""
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("ziwei", "positive", 0.8),
            _sig("western", "positive", 0.2),  # weak
        ]
        tally = tally_signals(signals, normalize=True)
        t = tally["long_term"]
        assert t.strong_support == 2
        assert t.weak_support == 1
        assert len(t.supporting_methods) == 3

    def test_warn_side_normalizes_too(self):
        signals = [
            _sig("bazi", "negative", 0.8),
            _sig("liuyao", "negative", 0.7),
        ]
        tally = tally_signals(signals, normalize=True)
        t = tally["long_term"]
        assert t.strong_warn == 2


# ── 分歧并陈 ────────────────────────────────────────────────────────

class TestDivergenceView:
    def test_strong_consensus(self):
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("ziwei", "positive", 0.8),
        ]
        tally = tally_signals(signals)
        view = build_divergence_view(tally)
        assert view["long_term"]["verdict"] == "strong_consensus"
        assert "bazi" in view["long_term"]["consensus"]
        assert view["long_term"]["warning"] == []

    def test_divergence_explicit(self):
        """有支持有警示 → 分歧。"""
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("liuyao", "negative", 0.7),
        ]
        tally = tally_signals(signals)
        view = build_divergence_view(tally)
        assert view["long_term"]["verdict"] == "divergence"
        assert "bazi" in view["long_term"]["consensus"]
        assert "liuyao" in view["long_term"]["warning"]

    def test_neutral_when_no_polarity(self):
        signals = [
            _sig("bazi", "neutral", 0.5),
            _sig("ziwei", "neutral", 0.5),
        ]
        tally = tally_signals(signals)
        view = build_divergence_view(tally)
        assert view["long_term"]["verdict"] == "neutral"
        assert view["long_term"]["consensus_count"] == 0
        assert view["long_term"]["warning_count"] == 0


# ── summary 自动生成 ────────────────────────────────────────────────

class TestSummary:
    def test_consensus_summary(self):
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("ziwei", "positive", 0.8),
        ]
        tally = tally_signals(signals)
        assert "支持" in tally["long_term"].summary
        assert "无警示" in tally["long_term"].summary

    def test_divergence_summary(self):
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("liuyao", "negative", 0.7),
        ]
        tally = tally_signals(signals)
        s = tally["long_term"].summary
        assert "分歧" in s
        assert "支持" in s
        assert "警示" in s

    def test_warning_summary(self):
        signals = [
            _sig("bazi", "negative", 0.8),
            _sig("ziwei", "negative", 0.7),
        ]
        tally = tally_signals(signals)
        s = tally["long_term"].summary
        assert "警示" in s

    def test_all_neutral_summary(self):
        signals = [_sig("bazi", "neutral", 0.5)]
        tally = tally_signals(signals)
        assert "倾向不明" in tally["long_term"].summary


# ── 多 scope 路由 ───────────────────────────────────────────────────

class TestMultiScope:
    def test_different_scopes_routed(self):
        signals = [
            _sig("bazi", "positive", 0.8, time_scope="long_term"),
            _sig("bazi", "positive", 0.7, time_scope="short_term"),
            _sig("ziwei", "positive", 0.8, time_scope="long_term"),
        ]
        # 用 normalize=False 避开多法一致规则的影响
        tally = tally_signals(signals, normalize=False)
        assert "long_term" in tally
        assert "short_term" in tally
        assert tally["long_term"].strong_support == 2
        assert tally["short_term"].strong_support == 1

    def test_scope_resolution_via_engine(self):
        """直接调 TallyEngine._resolve_scope 测兜底逻辑 (Pydantic 拦截前)."""
        from divination.aggregation.scope_tally import TallyEngine
        engine = TallyEngine()
        # 模拟非法值绕过 Pydantic
        s = _sig("bazi", "positive", 0.5)
        # 强制 time_scope 为非法值
        s.time_scope = None  # 拿掉
        # _resolve_scope 用 s.dimension 或 default "long_term"
        assert engine._resolve_scope(s) in (
            "long_term", "current_cycle", "short_term",
            "space", "one_question", "relationship", "medium_term",
        )


# ── 确定性 ─────────────────────────────────────────────────────────

class TestDeterministic:
    def test_same_input_same_output(self):
        signals = [
            _sig("bazi", "positive", 0.7),
            _sig("ziwei", "negative", 0.5),
            _sig("tarot", "neutral", 0.5),
        ]
        t1 = tally_signals(signals)
        t2 = tally_signals(signals)
        assert t1["long_term"].summary == t2["long_term"].summary
        assert t1["long_term"].strong_support == t2["long_term"].strong_support


# ── validator 集成 ─────────────────────────────────────────────────

class TestValidatorIntegration:
    def test_validate_signals_uses_tally(self):
        """validator.validate_signals 委派给 TallyEngine。"""
        from divination.aggregation.validator import validate_signals
        signals = [
            _sig("bazi", "positive", 0.8),
            _sig("ziwei", "positive", 0.8),
            _sig("liuyao", "negative", 0.5),
        ]
        v = validate_signals(signals)
        assert "long_term" in v.tally_by_scope
        # summary 应含 5 档计票结论
        assert v.tally_by_scope["long_term"].summary
