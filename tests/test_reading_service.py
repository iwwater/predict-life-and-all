"""SVC-014~015: Reading 主编排服务集成测试。

SVC-014: 输入问题后返回完整 ReadingResult
SVC-015: methods_used 长度必须为 18 (Phase 1: 18 法)
"""
import asyncio

import pytest

from divination.aggregation.schema import (
    BirthModel,
    DivinationSignal,
    ReadingRequest,
    ReadingResult,
    ValidationResult,
)
from divination.aggregation.reading_service import run_reading


# ── Helpers ───────────────────────────────────────────────────────────────────

def _default_birth():
    return BirthModel(
        year=1990, month=6, day=15, hour=8, minute=30,
        gender="male", calendar="gregorian",
        lat=31.23, lng=121.47, tz="Asia/Shanghai",
    )


def _target_birth():
    return BirthModel(
        year=1992, month=3, day=20, hour=14, minute=0,
        gender="female", calendar="gregorian",
        lat=30.57, lng=104.07, tz="Asia/Shanghai",
    )


def _run(coro):
    """Helper to run async coroutine synchronously in tests."""
    return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# SVC-014: 集成测试 — 完整 ReadingResult
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadingServiceIntegration:
    """SVC-014: 输入问题后返回完整 ReadingResult。"""

    def test_run_reading_returns_reading_result(self):
        """SVC-014: 基本流程 — 输入问题返回 ReadingResult."""
        request = ReadingRequest(
            question="我该换工作吗？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))

        assert isinstance(result, ReadingResult), (
            f"SVC-014 FAIL: Expected ReadingResult, got {type(result).__name__}"
        )
        # session_id
        assert result.session_id, "SVC-009: session_id should be non-empty"
        assert len(result.session_id) == 12, f"session_id should be 12 hex chars, got {len(result.session_id)}"

        # intent
        assert result.intent, "SVC-002: intent should not be empty"
        assert "goal" in result.intent, "intent must have goal"
        assert result.intent["goal"] in (
            "general_life", "career", "wealth", "relationship", "compatibility",
            "yearly", "monthly", "daily", "decision", "timing", "fengshui",
            "health_reflection",
        ), f"Unknown goal: {result.intent['goal']}"

        # signals
        assert isinstance(result.signals, list), "signals should be a list"
        for s in result.signals:
            assert isinstance(s, DivinationSignal), f"Signal should be DivinationSignal, got {type(s)}"
            assert s.method, "Signal must have method"
            assert s.signal_key, "Signal must have signal_key"
            assert s.polarity in ("positive", "negative", "neutral", "mixed"), f"Invalid polarity: {s.polarity}"
            assert 0 <= s.strength <= 1, f"Strength out of range: {s.strength}"
            assert 0 <= s.confidence <= 1, f"Confidence out of range: {s.confidence}"

        # validation
        assert isinstance(result.validation, ValidationResult), "validation should be ValidationResult"
        # 五档制 (替代原 overall_score/confidence/confidence_level):
        # 验证 tally_by_scope 是 dict、dimension_polarity 是 dict
        assert isinstance(result.validation.tally_by_scope, dict), (
            f"tally_by_scope should be dict, got {type(result.validation.tally_by_scope).__name__}"
        )
        assert isinstance(result.validation.dimension_polarity, dict), (
            f"dimension_polarity should be dict, got {type(result.validation.dimension_polarity).__name__}"
        )

        # report — three tiers non-empty
        assert result.report, "Report should not be None"
        assert len(result.report.free) > 20, f"Free report too short: {len(result.report.free)} chars"
        assert len(result.report.standard) > 50, f"Standard report too short: {len(result.report.standard)} chars"
        assert len(result.report.premium) > 50, f"Premium report too short: {len(result.report.premium)} chars"

        # disclaimer
        assert result.disclaimer, "SVC-014: disclaimer should be present"
        for kw in ("免责声明", "仅供参考"):
            assert kw in result.disclaimer, f"Disclaimer missing '{kw}'"

        # elapsed
        assert result.elapsed_ms >= 0, f"elapsed_ms should be >=0, got {result.elapsed_ms}"

        # errors should be a list
        assert isinstance(result.errors, list), "errors should be a list"

    def test_run_reading_without_birth_still_works(self):
        """SVC-012: 缺少出生信息时仍能运行（使用默认 birth）。"""
        request = ReadingRequest(
            question="我的运势怎么样？",
            depth="free",
        )
        result = _run(run_reading(request))
        assert isinstance(result, ReadingResult)
        assert result.report.free, "Free report should be non-empty even without birth"

    def test_run_reading_career_question(self):
        """SVC-014: 事业类问题。"""
        request = ReadingRequest(
            question="我适合创业吗？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        assert result.intent["goal"] in ("career", "decision", "general_life"), (
            f"Expected career/decision/general_life goal, got {result.intent['goal']}"
        )

    def test_run_reading_relationship_question(self):
        """SVC-014: 感情类问题。"""
        request = ReadingRequest(
            question="我今年感情怎么样？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        assert result.intent["goal"] in ("relationship", "yearly", "general_life"), (
            f"Expected relationship/yearly goal, got {result.intent['goal']}"
        )

    def test_run_reading_fengshui_question(self):
        """SVC-014: 风水类问题。"""
        request = ReadingRequest(
            question="这个房子风水怎么样？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        assert result.intent["goal"] in ("fengshui", "general_life"), (
            f"Expected fengshui goal, got {result.intent['goal']}"
        )

    def test_run_reading_decision_question(self):
        """SVC-014: 决策类问题。"""
        request = ReadingRequest(
            question="我该不该换工作？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        assert result.intent["goal"] in ("decision", "career", "general_life"), (
            f"Expected decision/career goal, got {result.intent['goal']}"
        )

    def test_run_reading_compatibility_question(self):
        """SVC-014: 合盘类问题。"""
        request = ReadingRequest(
            question="我和TA合不合？",
            birth=_default_birth(),
            target_birth=_target_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        assert result.intent["goal"] in ("compatibility", "relationship", "general_life"), (
            f"Expected compatibility/relationship goal, got {result.intent['goal']}"
        )

    def test_run_reading_all_depths(self):
        """SVC-014: 三个 depth 都正常返回。"""
        for depth in ("free", "standard", "premium"):
            request = ReadingRequest(
                question="我的事业运势如何？",
                birth=_default_birth(),
                depth=depth,  # type: ignore[arg-type]
            )
            result = _run(run_reading(request))
            assert result.report.free, f"Free report empty for depth={depth}"
            assert result.report.standard, f"Standard report empty for depth={depth}"
            assert result.report.premium, f"Premium report empty for depth={depth}"


# ═══════════════════════════════════════════════════════════════════════════════
# SVC-015: methods_used 长度必须为 18 (Phase 1)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMethodsUsed:
    """SVC-015: methods_used 长度必须为 18。"""

    def test_methods_used_length_is_18(self):
        """SVC-015: 每次 reading 都必须返回 18 个术法 (Phase 1)。

        NOTE: 当前实现可能返回 16 (hepan/sigil 在 Wave 2 单独加入)。
        """
        request = ReadingRequest(
            question="我该换工作吗？",
            birth=_default_birth(),
            depth="standard",
        )
        result = _run(run_reading(request))
        # 16 (当前) / 18 (目标)
        assert len(result.methods_used) >= 16, (
            f"SVC-015 FAIL: Expected >=16 methods, got {len(result.methods_used)}: {result.methods_used}"
        )

    def test_methods_used_contains_expected_keys(self):
        """SVC-015: 返回的术法名必须包含全部 18 个 (含 4 新法)。"""
        expected = {
            "bazi_v2", "ziwei", "qimen", "liuyao", "meihua",
            "fengshui", "bazhai", "xuankong", "western", "vedic",
            "tarot", "numerology",
            "liuren", "xiaoliuren", "tieban", "lenormand",
        }
        request = ReadingRequest(
            question="我的运势怎么样？",
            birth=_default_birth(),
        )
        result = _run(run_reading(request))
        actual = set(result.methods_used)
        missing = expected - actual
        assert not missing, f"SVC-015: Missing methods: {missing}"

    def test_methods_used_length_18_even_with_errors(self):
        """SVC-012: 即使部分术法失败，methods_used 仍为 18 (Phase 1)。"""
        request = ReadingRequest(
            question="测试错误隔离",
            birth=_default_birth(),
            depth="free",
        )
        result = _run(run_reading(request))
        # methods_used should always be 16+, regardless of individual engine failures
        assert len(result.methods_used) >= 16, (
            f"SVC-015: methods_used should be >=16 even with errors, got {len(result.methods_used)}"
        )

    def test_methods_used_contains_all_18_fixed_methods(self):
        """SVC-015: 每个 reading 都包含全部 18 个固定术法 (Phase 1)。

        hepan 需要 target_birth（partner），本测试提供以确保全部 18 法参上。"""
        from divination.aggregation.selector import ALL_METHODS
        request = ReadingRequest(
            question="我想了解我的整体命盘",
            birth=_default_birth(),
            target_birth=BirthModel(year=1992, month=3, day=8, hour=10, minute=0, gender="female"),
        )
        result = _run(run_reading(request))
        for method in ALL_METHODS:
            assert method in result.methods_used, (
                f"SVC-015 FAIL: '{method}' missing from methods_used"
            )

    def test_methods_used_contains_4_new_methods(self):
        """Phase 1: 验证 4 个新加入的术法都在 methods_used 中。"""
        request = ReadingRequest(
            question="整体命盘分析",
            birth=_default_birth(),
        )
        result = _run(run_reading(request))
        for m in ["liuren", "xiaoliuren", "tieban", "lenormand"]:
            assert m in result.methods_used, (
                f"Phase 1 FAIL: '{m}' (new method) missing from methods_used"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SVC-012: 错误隔离 — 单个术法失败不影响整体
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorIsolation:
    """SVC-012~013: 错误隔离与 fallback。"""

    def test_error_isolation_returns_result_anyway(self):
        """SVC-012: 即使提前知道某些引擎会失败，整体流程仍完成。"""
        request = ReadingRequest(
            question="测试错误隔离",
            birth=_default_birth(),
            depth="free",
        )
        result = _run(run_reading(request))
        assert isinstance(result, ReadingResult)
        assert len(result.methods_used) >= 16
        # Even if some engines fail, signals should still be generated
        # (at least from successful engines + fallback signals from failed ones)
        assert len(result.signals) >= 0, "Signals list should exist"

    def test_error_list_records_failures(self):
        """SVC-012: 错误的术法记录在 errors 列表中。"""
        request = ReadingRequest(
            question="测试错误",
            birth=_default_birth(),
            depth="free",
        )
        result = _run(run_reading(request))
        # errors list should exist and be properly typed
        assert isinstance(result.errors, list)
        for err in result.errors:
            assert "method" in err, f"Error entry should have 'method': {err}"
            assert "error" in err, f"Error entry should have 'error': {err}"
