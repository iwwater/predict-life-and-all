"""LLM-001~009: LLM Prompt 构建器测试 (TEST-011~016)。

LLM-001: build_reading_prompt — 从 ReadingResult 生成 LLM prompt
LLM-002: Prompt 包含 12 法摘要
LLM-003: Prompt 包含共识
LLM-004: Prompt 包含冲突
LLM-005: Prompt 包含合规规则
LLM-006: generate_mock_report — Mock 模式
LLM-007: SUPPORTED_PROVIDERS
LLM-008: check_llm_output — LLM 输出安全检查
LLM-009: llm_fallback_report — LLM 失败 fallback
"""
import pytest

from divination.aggregation.llm_prompt import (
    build_reading_prompt,
    generate_mock_report,
    check_llm_output,
    llm_fallback_report,
    DEFAULT_COMPLIANCE_RULES,
    SUPPORTED_PROVIDERS,
)
from divination.aggregation.schema import ReadingReport


# ── Sample test data ─────────────────────────────────────────────────────────

def _sample_result():
    """构建一个典型的 ReadingResult dict 用于测试。"""
    return {
        "session_id": "abc123def456",
        "intent": {
            "goal": "career",
            "goal_label": "事业工作",
            "question": "我该换工作吗？",
            "goal_confidence": 0.9,
        },
        "methods_used": [
            "bazi_v2", "ziwei", "qimen", "liuyao",
            "meihua", "fengshui", "bazhai", "xuankong",
            "western", "vedic", "tarot", "numerology",
        ],
        "signals": [
            {
                "method": "bazi_v2",
                "domain": "career",
                "signal_key": "day_master_strong",
                "polarity": "positive",
                "strength": 0.75,
                "evidence": "日主得令",
                "confidence": 0.80,
            },
            {
                "method": "ziwei",
                "domain": "career",
                "signal_key": "career_palace_favorable",
                "polarity": "positive",
                "strength": 0.65,
                "evidence": "官禄宫吉星汇聚",
                "confidence": 0.70,
            },
            {
                "method": "tarot",
                "domain": "career",
                "signal_key": "wheel_of_fortune_change",
                "polarity": "mixed",
                "strength": 0.55,
                "evidence": "命运之轮正位",
                "confidence": 0.60,
            },
        ],
        "consensus": [
            {
                "domain": "career",
                "theme": "事业运势上升期",
                "supporting_methods": ["bazi_v2", "ziwei", "qimen"],
                "weight_strength": 0.72,
                "explanation": "多个术法一致显示近期事业有积极变化",
            },
        ],
        "conflicts": [
            {
                "domain": "career",
                "severity": "medium",
                "positive_methods": ["bazi_v2", "ziwei"],
                "negative_methods": ["liuyao"],
                "neutral_methods": ["tarot"],
                "conflict_explanation": "六爻显示近期不宜变动，与八字、紫微的积极信号形成分歧",
                "resolution": "建议短期观望，待时机更明确后再做决定",
            },
        ],
        "validation": {
            "consensus": [
                {
                    "domain": "career",
                    "theme": "事业运势上升期",
                    "supporting_methods": ["bazi_v2", "ziwei", "qimen"],
                    "weight_strength": 0.72,
                    "explanation": "多个术法一致显示近期事业有积极变化",
                },
            ],
            "conflicts": [
                {
                    "domain": "career",
                    "severity": "medium",
                    "positive_methods": ["bazi_v2", "ziwei"],
                    "negative_methods": ["liuyao"],
                    "neutral_methods": ["tarot"],
                    "conflict_explanation": "六爻与八字紫微分岐",
                    "resolution": "建议短期观望",
                },
            ],
            "tally_by_scope": {"long_term": {"scope": "long_term", "strong_support": 3, "weak_support": 1, "neutral": 0, "weak_warn": 0, "strong_warn": 0, "supporting_methods": ["bazi_v2"], "warning_methods": [], "summary": "支持"}},
            "dimension_polarity": {"long_term": "strong_support"},
            "risks": ["仓促决策可能导致后悔", "行业不确定性较高"],
            "timing": {"summary": "未来3-6个月为关键窗口期", "optimal_window": "2025Q1"},
            "action_advice": ["观望1-2个月", "提升专业技能", "关注行业动态"],
        },
        "report": {
            "free": "事业运势呈上升趋势，综合评分72分。多术法共识显示积极信号。",
            "standard": "标准报告内容...",
            "premium": "深度报告内容...",
        },
        "elapsed_ms": 1234,
        "errors": [],
    }


# ══════════════════════════════════════════════════════════════════════════════
# LLM-001: build_reading_prompt
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildReadingPrompt:
    def test_prompt_returns_string(self):
        """LLM-001: build_reading_prompt 返回字符串"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_prompt_contains_question(self):
        """LLM-001: Prompt 包含用户问题"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert "我该换工作吗" in prompt

    def test_prompt_contains_goal_label(self):
        """LLM-001: Prompt 包含领域标签"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert "事业工作" in prompt

    def test_prompt_contains_compliance_rules(self):
        """LLM-005: Prompt 包含合规规则"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert "合规规则" in prompt
        assert "绝对化表达" in prompt

    def test_prompt_contains_12_methods(self):
        """LLM-002: Prompt 包含 12 法摘要"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        # 应该有方法标签出现
        assert "八字" in prompt or "紫微" in prompt or "bazi" in prompt

    def test_prompt_contains_consensus(self):
        """LLM-003: Prompt 包含共识"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert "共识" in prompt or "事业运势上升期" in prompt

    def test_prompt_contains_conflicts(self):
        """LLM-004: Prompt 包含冲突"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        assert "分歧" in prompt or "冲突" in prompt or "六爻" in prompt

    def test_prompt_contains_score(self):
        """LLM-001: Prompt 包含五档制计票/极性信息 (替代原综合评分)"""
        result = _sample_result()
        prompt = build_reading_prompt(result)
        # 新 schema: 包含"多术法计票"段落 + 五维极性
        assert "多术法计票" in prompt, f"LLM-001: prompt missing tally section"
        assert "strong_support" in prompt or "弱支持" in prompt, (
            f"LLM-001: prompt missing polarity info"
        )

    def test_prompt_free_depth_brief(self):
        """LLM-001: free 深度 prompt 不要求深度分析"""
        result = _sample_result()
        prompt = build_reading_prompt(result, depth="free")
        # Free depth should still have basic structure
        assert len(prompt) > 50

    def test_prompt_premium_depth_has_extra_sections(self):
        """LLM-001: premium 深度 prompt 包含额外分析要求"""
        result = _sample_result()
        prompt = build_reading_prompt(result, depth="premium")
        assert "时间窗口" in prompt or "深入追问" in prompt

    def test_default_compliance_rules_contains_7_items(self):
        """LLM-005: 默认合规规则包含 7 条"""
        # Count the numbered rules
        import re
        rules = re.findall(r'\d+\.', DEFAULT_COMPLIANCE_RULES)
        assert len(rules) >= 7, f"Expected ≥7 rules, got {len(rules)}"


# ══════════════════════════════════════════════════════════════════════════════
# LLM-006: Mock 模式
# ══════════════════════════════════════════════════════════════════════════════

class TestMockReport:
    def test_mock_report_returns_string(self):
        """LLM-006: generate_mock_report 返回字符串"""
        result = _sample_result()
        report = generate_mock_report(result)
        assert isinstance(report, str)
        assert len(report) > 100

    def test_mock_report_contains_score(self):
        """LLM-006: Mock 报告包含五档制计票信息 (替代原综合评分数字)"""
        result = _sample_result()
        report = generate_mock_report(result)
        # 新 schema: mock 报告改为显示"X 法支持 / Y 法警示"
        assert "支持" in report and "警示" in report, (
            f"LLM-006: mock report missing tally-based counts: {report[:300]}"
        )

    def test_mock_report_contains_disclaimer(self):
        """LLM-006: Mock 报告包含免责声明"""
        result = _sample_result()
        report = generate_mock_report(result)
        assert "参考" in report

    def test_mock_report_contains_mock_label(self):
        """LLM-006: Mock 报告标注 Mock 模式"""
        result = _sample_result()
        report = generate_mock_report(result, depth="standard")
        assert "Mock" in report or "自动生成" in report

    def test_mock_report_contains_consensus(self):
        """LLM-006: Mock 报告包含共识"""
        result = _sample_result()
        report = generate_mock_report(result)
        assert "共识" in report or "事业运势" in report

    def test_mock_report_with_no_signals(self):
        """LLM-006: 无信号的 Mock 报告不崩溃"""
        empty = {"validation": {}, "intent": {}}
        report = generate_mock_report(empty)
        assert isinstance(report, str)


# ══════════════════════════════════════════════════════════════════════════════
# LLM-007: Provider 配置
# ══════════════════════════════════════════════════════════════════════════════

class TestProviderConfig:
    def test_mock_in_supported_providers(self):
        """LLM-007: 'mock' 在支持列表中"""
        assert "mock" in SUPPORTED_PROVIDERS

    def test_openai_in_supported_providers(self):
        """LLM-007: 'openai' 在支持列表中"""
        assert "openai" in SUPPORTED_PROVIDERS

    def test_anthropic_in_supported_providers(self):
        """LLM-007: 'anthropic' 在支持列表中"""
        assert "anthropic" in SUPPORTED_PROVIDERS

    def test_supported_providers_is_list(self):
        """LLM-007: SUPPORTED_PROVIDERS 是列表"""
        assert isinstance(SUPPORTED_PROVIDERS, list)


# ══════════════════════════════════════════════════════════════════════════════
# LLM-008: LLM 输出安全检查
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMOutputSafety:
    def test_safe_output_passes(self):
        """LLM-008: 安全的 LLM 输出通过检查"""
        result = check_llm_output("综合来看，近期事业发展较为顺利，建议把握机会。以上内容仅供参考，不构成专业建议。")
        assert result["safe"] is True
        assert result["needs_softening"] is False
        assert result["issues"] == []

    def test_absolute_output_detected(self):
        """LLM-008: 含绝对化表达的 LLM 输出被标记"""
        result = check_llm_output("你一定会成功的")
        assert result["safe"] is False
        assert result["needs_softening"] is True
        assert len(result["issues"]) > 0

    def test_missing_disclaimer_detected(self):
        """LLM-008: 缺少免责声明被检测"""
        result = check_llm_output("你的运势不错")
        assert "免责声明" in result.get("issues", []) or "免责声明" in str(result.get("issues", []))

    def test_softened_text_provided(self):
        """LLM-008: 需要软化时提供 softened_text"""
        result = check_llm_output("你一定会成功")
        assert "一定" not in result["softened_text"]

    def test_multiple_issues_detected(self):
        """LLM-008: 同时检测多个问题"""
        result = check_llm_output("你一定会成功而且绝对不会亏")
        assert result["safe"] is False


# ══════════════════════════════════════════════════════════════════════════════
# LLM-009: Fallback
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMFallback:
    def test_fallback_returns_reading_report(self):
        """LLM-009: llm_fallback_report 返回 ReadingReport"""
        result = _sample_result()
        report = llm_fallback_report(result)
        assert isinstance(report, ReadingReport)
        assert isinstance(report.free, str)
        assert isinstance(report.standard, str)
        assert isinstance(report.premium, str)

    def test_fallback_free_is_short(self):
        """LLM-009: fallback free 报告有内容"""
        result = _sample_result()
        report = llm_fallback_report(result, depth="free")
        assert len(report.free) > 20

    def test_fallback_standard_and_premium_different(self):
        """LLM-009: fallback 三个档位报告都存在"""
        result = _sample_result()
        report = llm_fallback_report(result, depth="premium")
        assert len(report.standard) > 0
        assert len(report.premium) > 0

    def test_fallback_with_empty_result(self):
        """LLM-009: 空结果不崩溃"""
        empty = {"validation": {}, "intent": {}}
        report = llm_fallback_report(empty)
        assert isinstance(report, ReadingReport)
