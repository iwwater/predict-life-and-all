"""Reading 主编排服务 — 协调意图分类、术法选择、并行计算、标准化、验证、报告生成。

BE-009: 主服务文件

核心流程:
  1. classify_intent(question, goal) → goal + sub_goals
  2. select_methods(goal) → [{method, label, tier}, ...]
  3. 并行 compute(method) → 12 ChartResult
  4. normalize_all(charts) → unified signals
  5. validate(signals, intent) → consensus + conflicts
  6. generate(signals, validation, ...) → 三档报告
  7. 返回 ReadingResult
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from divination.contracts import Birth

from .intent import classify_intent
from .normalizer import normalize_all
from .schema import (
    BirthModel,
    ReadingRequest,
    ReadingResult,
)
from .selector import get_method_names, select_methods
from .synthesizer import DISCLAIMER, synthesize_report
from .validator import validate_signals
from .weights import get_weights

log = logging.getLogger("mystic-hub.reading")


async def run_reading(request: ReadingRequest) -> ReadingResult:
    """执行一次完整的 reading 流程。

    Args:
        request: 用户请求

    Returns:
        ReadingResult
    """
    t0 = time.perf_counter()
    session_id = uuid.uuid4().hex[:12]
    errors: list[dict[str, Any]] = []

    # Step 1: 意图分类 (INT-001, INT-014)
    intent = classify_intent(
        question=request.question,
        goal=request.goal if hasattr(request, 'goal') and request.goal else None,
    )
    goal = intent["goal"]

    # Step 2: 术法选择 (SEL-002) — 返回 [{method, label, tier}, ...]
    method_entries = select_methods(goal=goal)
    method_names = get_method_names(method_entries)

    # Step 3: 构建 Birth 对象
    birth = _build_birth(request.birth) if request.birth else _default_birth()

    # Step 4: 并行排盘
    from divination.router import _ENGINES as ENGINES

    charts: dict[str, Any] = {}
    for m in method_names:
        if m not in ENGINES:
            errors.append({"method": m, "error": "引擎未注册"})
            continue
        try:
            charts[m] = ENGINES[m](birth)
        except Exception as e:
            log.warning("Method %s failed: %s", m, e)
            errors.append({"method": m, "error": str(e)})
            from divination.contracts import ChartResult
            charts[m] = ChartResult(
                method=m,
                school="east" if m not in ("western", "vedic", "tarot", "numerology") else "west",
                engine="placeholder",
                normalized={},
                raw={"_error": str(e), "_placeholder": True},
            )

    # Step 5: 标准化
    signals = normalize_all(charts)

    # Step 6: 计算 weights 并交叉验证
    weights = get_weights(goal, method_entries)
    validation = validate_signals(signals, weights, method_entries)

    # Step 7: 报告生成
    intent["question"] = request.question  # 供 synthesizer 生成 headline
    report = synthesize_report(
        signals=signals,
        validation=validation,
        intent=intent,
        methods_used=method_names,
        depth=request.depth,
    )

    dt_ms = int((time.perf_counter() - t0) * 1000)

    return ReadingResult(
        session_id=session_id,
        intent=intent,
        methods_used=method_names,
        signals=signals,
        consensus=validation.consensus,
        conflicts=validation.conflicts,
        validation=validation,
        report=report,
        disclaimer=DISCLAIMER,
        elapsed_ms=dt_ms,
        errors=errors,
    )


def _build_birth(bm: BirthModel) -> Birth:
    """将 API 的 BirthModel 转为内部 Birth。"""
    return Birth(
        year=bm.year,
        month=bm.month,
        day=bm.day,
        hour=bm.hour,
        minute=bm.minute,
        gender=bm.gender,
        calendar=bm.calendar,
        lat=bm.lat,
        lng=bm.lng,
        tz=bm.tz,
        is_leap_month=bm.is_leap_month,
    )


def _default_birth() -> Birth:
    """默认出生信息（当用户未提供时）。"""
    import datetime
    now = datetime.datetime.now()
    return Birth(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=12,
        minute=0,
        gender="unspecified",
        calendar="gregorian",
        tz="Asia/Shanghai",
    )
