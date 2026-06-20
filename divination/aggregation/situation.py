"""Sprint 1.3 — 境限装配: 把"人事时地境限"装成统一 SituationContext。

7 维 (中文传统咨询框架, 兼顾现实约束):
  人: 求测者本人 (person)
  事: 事件 (event) — goal 派生的 event_type, 紧急度
  时: 时间窗口 (time) — horizon, deadline, urgency
  地: 空间 (space) — sitting, period, address
  境: 现实条件 (condition) — cash, contract, health, dependents, backup
  限: 资质/约束 (limit) — qualification, has_dependents, has_backup
  法: 术法选择 (method) — selected methods + options

设计原则:
  - 字段缺失 → 显式 None, 不抛错 (降级不阻断)
  - 缺数据维度入 degraded_dims, 报告层可见
  - 维度间用 dict 通信 (供 LLM prompt 序列化)
  - 7 维独立可空, 业务方按需取
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .schema import BirthModel, ReadingRequest, RealityConstraints, SpaceModel

# ── 7 维度子模型 ──────────────────────────────────────────────────────────

class PersonContext(BaseModel):
    """人 — 求测者本人。"""
    birth: BirthModel | None = None
    gender: Literal["male", "female", "unspecified"] | None = None
    age_years: int | None = None  # 派生, 需 birth.year + 当前年
    is_present: bool = True  # False = 仅为"代问"他人 (Sprint 1.7 扩展)


class CounterpartContext(BaseModel):
    """对方 — 关系/合盘场景。"""
    birth: BirthModel | None = None
    gender: Literal["male", "female", "unspecified"] | None = None
    relationship: str | None = None  # "男朋友"/"配偶"/"合作伙伴" 等
    age_years: int | None = None


class EventContext(BaseModel):
    """事 — 事件类型 + 紧急度。"""
    event_type: str | None = None  # 派生的 goal: career/wealth/relationship/...
    urgency: Literal["critical", "high", "medium", "low", "none"] | None = None
    primary_concern: str | None = None
    question: str | None = None
    is_about_self: bool = True


class TimeContext(BaseModel):
    """时 — 时间窗口。"""
    horizon: Literal["now", "short_term", "medium_term", "long_term", "open"] | None = None
    deadline: str | None = None  # ISO 日期 或 自由描述
    is_deadline_hard: bool = False  # True=外部期限, False=软性
    cycles: list[str] = Field(default_factory=list)  # ["流月", "流年", "大限"]


class SpaceContext(BaseModel):
    """地 — 空间。"""
    sitting: str | None = None  # 子/午/.../兼向
    period: int | None = None  # 元运
    construction_year: int | None = None
    address: str | None = None
    current_city: str | None = None
    target_city: str | None = None


class ConditionContext(BaseModel):
    """境 — 现实条件。"""
    cash_reserve_months: int | None = None
    has_formal_contract: bool | None = None
    commute_tolerance: Literal["accept", "negotiable", "reject"] | None = None
    health_status: Literal["good", "fair", "poor"] | None = None
    has_qualification: bool | None = None
    has_dependents: bool | None = None
    has_backup_plan: bool | None = None


class MethodContext(BaseModel):
    """法 — 术法选择。"""
    selected_methods: list[str] = Field(default_factory=list)
    method_options: dict[str, Any] = Field(default_factory=dict)
    is_user_specified: bool = False  # True=用户指定, False=系统默认


class SituationContext(BaseModel):
    """7 维境限总装。"""
    person: PersonContext = Field(default_factory=PersonContext)
    counterpart: CounterpartContext | None = None
    event: EventContext = Field(default_factory=EventContext)
    time: TimeContext = Field(default_factory=TimeContext)
    space: SpaceContext = Field(default_factory=SpaceContext)
    condition: ConditionContext = Field(default_factory=ConditionContext)
    method: MethodContext = Field(default_factory=MethodContext)
    degraded_dims: list[str] = Field(default_factory=list)
    context_answers: dict[str, Any] = Field(default_factory=dict)


# ── 装配入口 ──────────────────────────────────────────────────────────────

def build_situation(
    request: ReadingRequest,
    intent: dict[str, Any] | None = None,
    context_answers: dict[str, Any] | None = None,
) -> SituationContext:
    """从 ReadingRequest + intent + 用户答的追问 → 统一 SituationContext。

    Args:
        request: 主入口请求 (含 birth/space/constraints)
        intent: classify_intent() 返回的 dict
        context_answers: 追问答案 dict

    Returns:
        SituationContext — 7 维全装, 缺的入 degraded_dims
    """
    ctx_answers = context_answers or {}
    intent = intent or {}

    # ── 1. person ──
    person = _build_person(request.birth)

    # ── 2. counterpart (合盘/关系 才有) ──
    counterpart = _build_counterpart(request.target_birth, ctx_answers) if request.target_birth else None
    if intent.get("goal") in ("compatibility", "relationship") and not counterpart:
        counterpart = CounterpartContext(relationship=ctx_answers.get("relationship_status"))

    # ── 3. event ──
    event = _build_event(intent, request.question, ctx_answers)

    # ── 4. time ──
    time_ctx = _build_time(intent, ctx_answers, request.method_options or {})

    # ── 5. space ──
    space = _build_space(request.space, ctx_answers)

    # ── 6. condition ──
    condition = _build_condition(request.constraints, ctx_answers)

    # ── 7. method ──
    method = _build_method(request.methods, request.method_options)

    sit = SituationContext(
        person=person,
        counterpart=counterpart,
        event=event,
        time=time_ctx,
        space=space,
        condition=condition,
        method=method,
        context_answers=ctx_answers,
    )

    # 计算 degraded_dims
    sit.degraded_dims = _detect_degraded(sit)
    return sit


# ── 子装配函数 ────────────────────────────────────────────────────────────

def _build_person(birth: BirthModel | None) -> PersonContext:
    if birth is None:
        return PersonContext(is_present=False)
    return PersonContext(
        birth=birth,
        gender=birth.gender,
        is_present=True,
    )


def _build_counterpart(
    target_birth: BirthModel | None,
    ctx_answers: dict[str, Any],
) -> CounterpartContext | None:
    if target_birth is None:
        return None
    return CounterpartContext(
        birth=target_birth,
        gender=target_birth.gender,
        relationship=ctx_answers.get("relationship_type"),
    )


def _build_event(
    intent: dict[str, Any],
    question: str,
    ctx_answers: dict[str, Any],
) -> EventContext:
    goal = intent.get("goal", "general_life")
    urgency = _urgency_from_answers(ctx_answers)
    return EventContext(
        event_type=goal,
        urgency=urgency,
        primary_concern=ctx_answers.get("primary_concern"),
        question=question,
        is_about_self=True,
    )


def _urgency_from_answers(answers: dict[str, Any]) -> str:
    """从追问答案推断 urgency。"""
    u = answers.get("urgency", "")
    if not u:
        return "medium"
    mapping = {
        "<1 周": "critical", "1-4 周": "high",
        "1-3 月": "medium", "3-12 月": "low", "不急": "none",
    }
    if u in mapping:
        return mapping[u]
    # 兜底: 含"周"→ high, 含"月"→ medium, 含"年"→ low
    if "周" in u:
        return "high"
    if "月" in u:
        return "medium"
    if "年" in u:
        return "low"
    return "medium"


def _build_time(
    intent: dict[str, Any],
    ctx_answers: dict[str, Any],
    method_options: dict[str, Any],
) -> TimeContext:
    goal = intent.get("goal", "general_life")
    horizon = _horizon_from_goal(goal)
    deadline = ctx_answers.get("deadline")
    # 软期限关键词: 含"没期限/不急/软性/无" → is_hard=False
    soft_markers = ("没期限", "不急", "软性", "无", "软性期限")
    is_hard = bool(
        deadline
        and not any(m in str(deadline) for m in soft_markers)
    )

    # 周期标签: daily/monthly/yearly 各自只看该周期
    cycles: list[str] = []
    if goal == "daily":
        cycles = ["日运"]
    elif goal == "monthly":
        cycles = ["流月"]
    elif goal == "yearly":
        cycles = ["流年", "大限"]
    elif goal == "general_life":
        cycles = ["本命", "大限", "流年"]
    else:
        cycles = ["本命", "当前周期"]

    return TimeContext(
        horizon=horizon,
        deadline=deadline,
        is_deadline_hard=is_hard,
        cycles=cycles,
    )


def _horizon_from_goal(goal: str) -> str:
    mapping = {
        "daily": "now", "monthly": "short_term", "yearly": "medium_term",
        "decision": "short_term", "timing": "short_term",
        "career": "medium_term", "wealth": "medium_term",
        "relationship": "medium_term", "compatibility": "long_term",
        "general_life": "long_term", "fengshui": "long_term",
        "health_reflection": "medium_term",
    }
    return mapping.get(goal, "medium_term")


def _build_space(
    space: SpaceModel | None,
    ctx_answers: dict[str, Any],
) -> SpaceContext:
    if space is None:
        # 用 answer 兜底
        return SpaceContext(
            current_city=ctx_answers.get("current_city"),
            target_city=ctx_answers.get("target_city"),
        )
    return SpaceContext(
        sitting=space.sitting,
        period=space.period,
        construction_year=space.construction_year,
        address=space.address,
    )


def _build_condition(
    constraints: RealityConstraints | None,
    ctx_answers: dict[str, Any],
) -> ConditionContext:
    if constraints is None:
        return ConditionContext(
            cash_reserve_months=ctx_answers.get("cash_reserve_months"),
        )
    return ConditionContext(
        cash_reserve_months=constraints.cash_reserve_months,
        has_formal_contract=constraints.has_formal_contract,
        commute_tolerance=constraints.commute_tolerance,
        health_status=constraints.health_status,
        has_qualification=constraints.has_qualification,
        has_dependents=constraints.has_dependents,
        has_backup_plan=constraints.has_backup_plan,
    )


def _build_method(
    methods: list[str] | None,
    method_options: dict[str, Any] | None,
) -> MethodContext:
    opts = method_options or {}
    return MethodContext(
        selected_methods=list(methods) if methods else [],
        method_options=opts,
        is_user_specified=bool(methods),
    )


# ── 降级检测 ──────────────────────────────────────────────────────────────

def _detect_degraded(sit: SituationContext) -> list[str]:
    """哪些维度缺失关键数据 → 入 degraded_dims。"""
    degraded: list[str] = []

    if not sit.person.birth:
        degraded.append("person.birth")

    # counterpart: 必须存在且有 birth 才是"就绪" (Sprint 1.3 升级)
    if sit.event.event_type in ("compatibility", "relationship"):
        if sit.counterpart is None or sit.counterpart.birth is None:
            degraded.append("counterpart")

    if sit.event.event_type == "fengshui" and not sit.space.sitting:
        degraded.append("space.sitting")

    if sit.event.urgency is None:
        degraded.append("event.urgency")

    return degraded


# ── 查询接口 ──────────────────────────────────────────────────────────────

def is_ready(sit: SituationContext) -> bool:
    """situation 是否"就绪" — 即无 degraded_dims。"""
    return len(sit.degraded_dims) == 0


def missing_dims(sit: SituationContext) -> list[str]:
    """便捷: 取 degraded_dims。"""
    return list(sit.degraded_dims)


def to_summary(sit: SituationContext) -> dict[str, Any]:
    """压缩成 dict 摘要 (供 LLM prompt / 日志)。"""
    return {
        "person": {
            "has_birth": sit.person.birth is not None,
            "gender": sit.person.gender,
        },
        "counterpart": {
            "has_birth": sit.counterpart is not None and sit.counterpart.birth is not None,
            "relationship": sit.counterpart.relationship if sit.counterpart else None,
        },
        "event": {
            "type": sit.event.event_type,
            "urgency": sit.event.urgency,
            "concern": sit.event.primary_concern,
        },
        "time": {
            "horizon": sit.time.horizon,
            "deadline": sit.time.deadline,
            "is_hard": sit.time.is_deadline_hard,
            "cycles": sit.time.cycles,
        },
        "space": {
            "sitting": sit.space.sitting,
            "period": sit.space.period,
            "current_city": sit.space.current_city,
        },
        "condition_filled": _condition_filled_count(sit.condition),
        "method": {
            "is_user_specified": sit.method.is_user_specified,
            "count": len(sit.method.selected_methods),
        },
        "degraded_dims": sit.degraded_dims,
    }


def _condition_filled_count(cond: ConditionContext) -> int:
    """ConditionContext 实际填了几个字段。"""
    n = 0
    for v in [
        cond.cash_reserve_months, cond.has_formal_contract,
        cond.commute_tolerance, cond.health_status,
        cond.has_qualification, cond.has_dependents,
        cond.has_backup_plan,
    ]:
        if v is not None:
            n += 1
    return n
