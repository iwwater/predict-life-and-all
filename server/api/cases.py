"""Event-case API for one-question, one-cast review flow.

This module intentionally stores user-created event cases, not celebrity cases.
It is a Phase 1 vertical slice: in-memory storage for local demo/test, with a
stable API shape that can later be backed by a database.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from divination.aggregation.intent import classify_intent
from divination.aggregation.questioner import get_questions_for_case
from divination.aggregation.reading_service import run_reading
from divination.aggregation.schema import BirthModel, ReadingRequest, ReadingResult, SpaceModel

router = APIRouter()


CaseStatus = Literal["draft", "context_ready", "officially_cast"]


class MinimalQuestion(BaseModel):
    id: str
    prompt: str
    options: list[str]
    required: bool = True


class CaseCreateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    goal: str | None = None
    birth: BirthModel | None = None
    subject: str | None = None
    target: str | None = None
    time_horizon: str | None = None
    location: str | None = None
    current_city: str | None = None


class CaseContextRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    birth: BirthModel | None = None
    space: SpaceModel | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)


class CaseCastRequest(BaseModel):
    depth: Literal["free", "standard", "premium"] = "standard"
    methods: list[str] | None = None
    method_options: dict[str, Any] | None = None


class CaseVersionRequest(BaseModel):
    question: str | None = Field(None, min_length=1, max_length=2000)
    changed_condition: str = Field(..., min_length=1, max_length=500)
    context_updates: dict[str, Any] = Field(default_factory=dict)


class EventCase(BaseModel):
    case_id: str
    parent_case_id: str | None = None
    event_type: str
    question: str
    subject: str | None = None
    target: str | None = None
    time_horizon: str | None = None
    location: str | None = None
    status: CaseStatus = "draft"
    version: int = 1
    intent: dict[str, Any] = Field(default_factory=dict)
    minimal_questions: list[MinimalQuestion] = Field(default_factory=list)
    birth: BirthModel | None = None
    space: SpaceModel | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    result_session_id: str | None = None
    selected_version: int | None = Field(
        None, description="Sprint 1.7: 用户显式选定的版本号, 优先于 latest"
    )
    idempotency_key: str | None = Field(
        None, description="Sprint 1.7: 创建时的幂等键 (hash(birth+question))"
    )
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class CastResponse(BaseModel):
    case: EventCase
    result: ReadingResult
    idempotent: bool = True


_CASES: dict[str, EventCase] = {}
_RESULTS: dict[str, ReadingResult] = {}
_CAST_BY_KEY: dict[tuple[str, str], str] = {}
_VERSION_BY_PARENT: dict[str, list[str]] = {}  # parent_case_id -> [case_id, ...]
_IDEMPOTENCY_INDEX: dict[str, str] = {}  # idempotency_key -> case_id


def _new_case_id() -> str:
    return f"case_{uuid.uuid4().hex[:12]}"


def _compute_idempotency_key(
    question: str, birth: BirthModel | None, goal: str | None,
) -> str:
    """Sprint 1.7: 同 (question + birth + goal) → 同 case。

    不可逆: 不含上下文/约束 (那些在 /context 阶段填, 不可作幂等键)。
    """
    import hashlib
    parts = [
        question.strip(),
        goal or "",
        str(birth.year) if birth else "",
        str(birth.month) if birth else "",
        str(birth.day) if birth else "",
        str(birth.hour) if birth else "",
        str(birth.minute) if birth else "",
        birth.gender if birth else "",
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _touch(case: EventCase) -> EventCase:
    case.updated_at = time.time()
    _CASES[case.case_id] = case
    return case


def _get_case(case_id: str) -> EventCase:
    case = _CASES.get(case_id)
    if not case:
        raise HTTPException(404, f"case not found: {case_id}")
    return case


def _minimal_questions(intent: dict[str, Any], context: dict[str, Any]) -> list[MinimalQuestion]:
    """Sprint 1.2: 委托给 questioner.pick_questions() 声明式题池。

    保留 _minimal_questions 名字 (cases_api 测试依赖),
    内部用 questioner 模块计算后转 MinimalQuestion。
    """
    qs = get_questions_for_case(intent=intent, context=context, max_n=2)
    return [
        MinimalQuestion(
            id=q.id,
            prompt=q.prompt,
            options=list(q.options),
            required=q.required,
        )
        for q in qs
    ]


def _case_context_for_reading(case: EventCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "version": case.version,
        "event_type": case.event_type,
        "question": case.question,
        "subject": case.subject,
        "target": case.target,
        "time_horizon": case.time_horizon,
        "location": case.location,
        "context": case.context,
        "constraints": case.constraints,
    }


@router.get("/cases", response_model=list[EventCase])
def list_cases():
    return sorted(_CASES.values(), key=lambda c: c.created_at, reverse=True)


@router.post("/cases", response_model=EventCase)
def create_case(body: CaseCreateRequest, idempotent: bool = True):
    """创建 case。Sprint 1.7: 同 (question+birth+goal) → 幂等返回同 case。

    Args:
        body: 创建请求
        idempotent: True (默认) → 同输入复用同 case; False → 强制新建

    Returns:
        EventCase — 既存的或新建
    """
    intent = classify_intent(body.question, body.goal)
    context = {"question": body.question}
    if body.current_city:
        context["current_city"] = body.current_city

    # Sprint 1.7: 幂等查找
    idem_key = _compute_idempotency_key(body.question, body.birth, body.goal)
    if idempotent and idem_key in _IDEMPOTENCY_INDEX:
        existing_id = _IDEMPOTENCY_INDEX[idem_key]
        existing = _CASES.get(existing_id)
        if existing is not None and existing.status != "officially_cast":
            # 未 cast, 复用 (允许 client 在 /context 阶段补全后再 cast)
            return _touch(existing)
        # 已 cast, 不复用 — 提示 client 用 versions 创建新版本
        if existing is not None:
            return _touch(existing)

    case = EventCase(
        case_id=_new_case_id(),
        event_type=intent["goal"],
        question=body.question,
        subject=body.subject,
        target=body.target,
        time_horizon=body.time_horizon,
        location=body.location,
        intent=intent,
        birth=body.birth,
        context=context,
        idempotency_key=idem_key,
    )
    case.minimal_questions = _minimal_questions(intent, context)
    _IDEMPOTENCY_INDEX[idem_key] = case.case_id
    # Sprint 1.7: 初始化版本索引
    _VERSION_BY_PARENT.setdefault(case.case_id, [case.case_id])
    return _touch(case)


@router.post("/cases/{case_id}/context", response_model=EventCase)
def update_case_context(case_id: str, body: CaseContextRequest):
    case = _get_case(case_id)
    if case.status == "officially_cast":
        raise HTTPException(409, "case already has a fixed result; create a new version for changed conditions")

    case.context.update(body.answers)
    case.constraints.update(body.constraints)
    if body.birth:
        case.birth = body.birth
    if body.space:
        case.space = body.space
    case.minimal_questions = _minimal_questions(case.intent, case.context)
    if not case.minimal_questions:
        case.status = "context_ready"
    return _touch(case)


@router.post("/cases/{case_id}/cast", response_model=CastResponse)
async def cast_case(
    case_id: str,
    body: CaseCastRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    case = _get_case(case_id)
    key = (case_id, idempotency_key)

    if key in _CAST_BY_KEY:
        result_id = _CAST_BY_KEY[key]
        return CastResponse(case=case, result=_RESULTS[result_id], idempotent=True)

    if case.result_session_id:
        _CAST_BY_KEY[key] = case.result_session_id
        return CastResponse(case=case, result=_RESULTS[case.result_session_id], idempotent=True)

    request = ReadingRequest(
        goal=case.event_type,
        question=case.question,
        birth=case.birth,
        space=case.space,
        method_options={
            **(body.method_options or {}),
            "event_case": _case_context_for_reading(case),
        },
        methods=body.methods,
        depth=body.depth,
    )
    result = await run_reading(request)

    case.status = "officially_cast"
    case.result_session_id = result.session_id
    _RESULTS[result.session_id] = result
    _CAST_BY_KEY[key] = result.session_id
    _touch(case)
    return CastResponse(case=case, result=result, idempotent=False)


@router.post("/cases/{case_id}/versions", response_model=EventCase)
def create_case_version(case_id: str, body: CaseVersionRequest):
    parent = _get_case(case_id)
    context = {**parent.context, **body.context_updates, "changed_condition": body.changed_condition}
    question = body.question or parent.question
    intent = classify_intent(question, parent.event_type)
    # Sprint 1.7: version 按 root case 的版本链顺序递增
    root_id = case_id
    existing_versions = _VERSION_BY_PARENT.get(root_id, [root_id])
    next_version = len(existing_versions) + 1
    child = EventCase(
        case_id=_new_case_id(),
        parent_case_id=parent.case_id,
        event_type=intent["goal"],
        question=question,
        subject=parent.subject,
        target=parent.target,
        time_horizon=parent.time_horizon,
        location=parent.location,
        version=next_version,
        intent=intent,
        birth=parent.birth,
        space=parent.space,
        context=context,
        constraints=parent.constraints.copy(),
    )
    child.minimal_questions = _minimal_questions(intent, context)
    if not child.minimal_questions:
        child.status = "context_ready"
    # Sprint 1.7: 跟踪版本关系
    _VERSION_BY_PARENT.setdefault(root_id, [root_id]).append(child.case_id)
    return _touch(child)


# ── Sprint 1.7 新增端点 ────────────────────────────────────────────────

@router.get("/cases/{case_id}/versions", response_model=list[EventCase])
def list_case_versions(case_id: str):
    """列出 case 的所有版本 (含 parent)。"""
    case_ids = _VERSION_BY_PARENT.get(case_id, [case_id])
    return [_CASES[cid] for cid in case_ids if cid in _CASES]


@router.post("/cases/{case_id}/versions/{version}/select", response_model=EventCase)
def select_case_version(case_id: str, version: int):
    """Sprint 1.7: 用户显式选定某版本, 后续 /result 优先返回此版本。

    注: case_id 是 parent 根 case 的 ID。version 1 = parent, 2+ = 子版本。
    """
    root = _get_case(case_id)
    version_ids = _VERSION_BY_PARENT.get(root.case_id, [root.case_id])
    if version < 1 or version > len(version_ids):
        raise HTTPException(404, f"version {version} not found for case {case_id}")
    target = _CASES[version_ids[version - 1]]
    if target.status != "officially_cast":
        raise HTTPException(409, f"version {version} has no fixed result yet")
    root.selected_version = version
    return _touch(root)


@router.get("/cases/{case_id}/result", response_model=CastResponse)
def get_case_result(case_id: str):
    """Sprint 1.7: 优先 selected_version, 否则取 latest (含子版本)。"""
    case = _get_case(case_id)
    version_ids = _VERSION_BY_PARENT.get(case.case_id, [case.case_id])

    # 1. selected_version 优先
    if case.selected_version is not None:
        if case.selected_version < 1 or case.selected_version > len(version_ids):
            raise HTTPException(404, f"selected version {case.selected_version} not found")
        target = _CASES[version_ids[case.selected_version - 1]]
        if not target.result_session_id:
            raise HTTPException(404, "selected version has no result yet")
        return CastResponse(case=case, result=_RESULTS[target.result_session_id], idempotent=True)

    # 2. 否则: 从最后一个版本倒序找有 result 的
    for vid in reversed(version_ids):
        v = _CASES.get(vid)
        if v and v.result_session_id:
            return CastResponse(case=case, result=_RESULTS[v.result_session_id], idempotent=True)

    raise HTTPException(404, "case has no fixed result yet")


def _reset_store_for_tests() -> None:
    _CASES.clear()
    _RESULTS.clear()
    _CAST_BY_KEY.clear()
