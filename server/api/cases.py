"""Event-case API for one-question, one-cast review flow.

This module intentionally stores user-created event cases, not celebrity cases.
It is a Phase 1 vertical slice: in-memory storage for local demo/test, with a
stable API shape that can later be backed by a database.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from divination.aggregation.intent import classify_intent
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
    goal: Optional[str] = None
    birth: Optional[BirthModel] = None
    subject: Optional[str] = None
    target: Optional[str] = None
    time_horizon: Optional[str] = None
    location: Optional[str] = None
    current_city: Optional[str] = None


class CaseContextRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    birth: Optional[BirthModel] = None
    space: Optional[SpaceModel] = None
    constraints: dict[str, Any] = Field(default_factory=dict)


class CaseCastRequest(BaseModel):
    depth: Literal["free", "standard", "premium"] = "standard"
    methods: Optional[list[str]] = None
    method_options: Optional[dict[str, Any]] = None


class CaseVersionRequest(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=2000)
    changed_condition: str = Field(..., min_length=1, max_length=500)
    context_updates: dict[str, Any] = Field(default_factory=dict)


class EventCase(BaseModel):
    case_id: str
    parent_case_id: Optional[str] = None
    event_type: str
    question: str
    subject: Optional[str] = None
    target: Optional[str] = None
    time_horizon: Optional[str] = None
    location: Optional[str] = None
    status: CaseStatus = "draft"
    version: int = 1
    intent: dict[str, Any] = Field(default_factory=dict)
    minimal_questions: list[MinimalQuestion] = Field(default_factory=list)
    birth: Optional[BirthModel] = None
    space: Optional[SpaceModel] = None
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    result_session_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class CastResponse(BaseModel):
    case: EventCase
    result: ReadingResult
    idempotent: bool = True


_CASES: dict[str, EventCase] = {}
_RESULTS: dict[str, ReadingResult] = {}
_CAST_BY_KEY: dict[tuple[str, str], str] = {}


def _new_case_id() -> str:
    return f"case_{uuid.uuid4().hex[:12]}"


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
    goal = intent.get("goal", "general_life")
    questions: list[MinimalQuestion] = []

    def missing(key: str) -> bool:
        return key not in context or context.get(key) in (None, "")

    if goal in {"career", "decision"} and missing("offer_status"):
        questions.append(MinimalQuestion(
            id="offer_status",
            prompt="是否已有明确的新机会或 offer？",
            options=["已有正式 offer", "只有口头机会", "还没有"],
        ))
    if goal == "career" and ("创业" in context.get("question", "")) and missing("venture_mode"):
        questions.append(MinimalQuestion(
            id="venture_mode",
            prompt="准备兼职尝试还是直接全职？",
            options=["兼职尝试", "直接全职", "还不确定"],
        ))
    if goal == "relationship" and missing("relationship_status"):
        questions.append(MinimalQuestion(
            id="relationship_status",
            prompt="你们目前是什么关系？",
            options=["交往中", "暧昧", "分开后", "已婚", "其他"],
        ))
    if goal == "fengshui" and missing("space_focus"):
        questions.append(MinimalQuestion(
            id="space_focus",
            prompt="你主要想看什么？",
            options=["居住", "睡眠", "财运", "工作", "关系"],
        ))

    return questions[:2]


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
def create_case(body: CaseCreateRequest):
    intent = classify_intent(body.question, body.goal)
    context = {"question": body.question}
    if body.current_city:
        context["current_city"] = body.current_city

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
    )
    case.minimal_questions = _minimal_questions(intent, context)
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


@router.get("/cases/{case_id}/result", response_model=CastResponse)
def get_case_result(case_id: str):
    case = _get_case(case_id)
    if not case.result_session_id:
        raise HTTPException(404, "case has no fixed result yet")
    return CastResponse(case=case, result=_RESULTS[case.result_session_id], idempotent=True)


@router.post("/cases/{case_id}/versions", response_model=EventCase)
def create_case_version(case_id: str, body: CaseVersionRequest):
    parent = _get_case(case_id)
    context = {**parent.context, **body.context_updates, "changed_condition": body.changed_condition}
    question = body.question or parent.question
    intent = classify_intent(question, parent.event_type)
    child = EventCase(
        case_id=_new_case_id(),
        parent_case_id=parent.case_id,
        event_type=intent["goal"],
        question=question,
        subject=parent.subject,
        target=parent.target,
        time_horizon=parent.time_horizon,
        location=parent.location,
        version=parent.version + 1,
        intent=intent,
        birth=parent.birth,
        space=parent.space,
        context=context,
        constraints=parent.constraints.copy(),
    )
    child.minimal_questions = _minimal_questions(intent, context)
    if not child.minimal_questions:
        child.status = "context_ready"
    return _touch(child)


def _reset_store_for_tests() -> None:
    _CASES.clear()
    _RESULTS.clear()
    _CAST_BY_KEY.clear()
