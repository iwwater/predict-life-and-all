"""聚合模块 — 12 术法统一调度、交叉验证、报告生成。

BE-001: 聚合模块

提供的公共接口:
  - classify_intent(question, goal) → dict  意图分类 (INT-001)
  - select_methods(goal) → [{method, label, tier}]  术法选择 (SEL-002)
  - run_reading(request) → ReadingResult  主入口
  - normalize(chart) → list[Signal]      单术法标准化
  - normalize_all(charts) → list[Signal] 全部标准化
  - validate(signals, intent) → ValidationResult  交叉验证
  - generate(signals, validation, ...) → ReadingReport  报告生成
"""
from .intent import GOAL_LABELS, GOAL_TYPES, classify, classify_intent
from .llm_prompt import (
    DEFAULT_COMPLIANCE_RULES,
    build_reading_prompt,
    check_llm_output,
    generate_mock_report,
    llm_fallback_report,
)
from .normalizer import normalize, normalize_all
from .questioner import (
    Question,
    get_questions_for_case,
    list_all_goals_with_questions,
    pick_questions,
    question_count,
)
from .reading_service import run_reading
from .situation import (
    ConditionContext,
    CounterpartContext,
    EventContext,
    MethodContext,
    PersonContext,
    SituationContext,
    SpaceContext,
    TimeContext,
    build_situation,
    is_ready,
    missing_dims,
    to_summary,
)
from .safety import (
    CRISIS_KEYWORDS,
    CRISIS_RESPONSE,
    DISCLAIMER as SAFETY_DISCLAIMER,
    PRIVACY_NOTICE,
    check_input_safety,
    check_output_safety,
    sanitize_birth_for_log,
    sanitize_for_log,
)
from .schema import (
    BirthModel,
    ConflictItem,
    ConsensusItem,
    DivinationSignal,
    ReadingReport,
    ReadingRequest,
    ReadingResult,
    SpaceModel,
    ValidationResult,
)
from .selector import (
    ALL_METHODS,
    FIXED_12_METHODS,
    get_method_names,
    get_primary_methods,
    get_tier_for_method,
    select_methods,
)
from .synthesizer import DISCLAIMER, generate
from .validator import validate

__all__ = [
    # ── 意图分类 ──
    "classify_intent",
    "classify",  # 向后兼容
    "GOAL_TYPES",
    "GOAL_LABELS",
    # ── 术法选择 ──
    "select_methods",
    "ALL_METHODS",
    "FIXED_12_METHODS",  # 向后兼容
    "get_method_names",
    "get_primary_methods",
    "get_tier_for_method",
    # ── 主入口 ──
    "run_reading",
    # ── 标准化 ──
    "normalize",
    "normalize_all",
    # ── 追问 ──
    "Question",
    "pick_questions",
    "get_questions_for_case",
    "list_all_goals_with_questions",
    "question_count",
    # ── 境限 ──
    "PersonContext",
    "CounterpartContext",
    "EventContext",
    "TimeContext",
    "SpaceContext",
    "ConditionContext",
    "MethodContext",
    "SituationContext",
    "build_situation",
    "is_ready",
    "missing_dims",
    "to_summary",
    # ── 验证 ──
    "validate",
    # ── 安全 ──
    "check_input_safety",
    "check_output_safety",
    "sanitize_for_log",
    "sanitize_birth_for_log",
    "CRISIS_KEYWORDS",
    "CRISIS_RESPONSE",
    "PRIVACY_NOTICE",
    "SAFETY_DISCLAIMER",
    # ── LLM Prompt ──
    "build_reading_prompt",
    "generate_mock_report",
    "check_llm_output",
    "llm_fallback_report",
    "DEFAULT_COMPLIANCE_RULES",
    # ── 报告 ──
    "generate",
    "DISCLAIMER",
    # ── 数据模型 ──
    "ReadingRequest",
    "ReadingResult",
    "ReadingReport",
    "DivinationSignal",
    "ConsensusItem",
    "ConflictItem",
    "ValidationResult",
    "BirthModel",
    "SpaceModel",
]
