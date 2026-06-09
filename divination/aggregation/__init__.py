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
from .intent import classify, classify_intent, GOAL_TYPES, GOAL_LABELS
from .normalizer import normalize, normalize_all
from .reading_service import run_reading
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
    # ── 验证 ──
    "validate",
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
