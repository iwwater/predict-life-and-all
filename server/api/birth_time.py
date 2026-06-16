"""Birth-time rectification API.

Phase 2 slice: generate candidate Chinese hours, compare them against known life
events with deterministic scoring, and return an uncertainty-aware report.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from divination import Birth
from divination.router import compute
from divination.aggregation.schema import BirthModel

router = APIRouter()

BirthAccuracy = Literal["exact", "approximate", "period", "unknown"]
DayPeriod = Literal["morning", "afternoon", "evening", "night"]

_BRANCHES = [
    ("子", 23, 0, "23:00-01:00"),
    ("丑", 1, 2, "01:00-03:00"),
    ("寅", 3, 4, "03:00-05:00"),
    ("卯", 5, 6, "05:00-07:00"),
    ("辰", 7, 8, "07:00-09:00"),
    ("巳", 9, 10, "09:00-11:00"),
    ("午", 11, 12, "11:00-13:00"),
    ("未", 13, 14, "13:00-15:00"),
    ("申", 15, 16, "15:00-17:00"),
    ("酉", 17, 18, "17:00-19:00"),
    ("戌", 19, 20, "19:00-21:00"),
    ("亥", 21, 22, "21:00-23:00"),
]

_PERIOD_HOURS = {
    "morning": [6, 8, 10],
    "afternoon": [12, 14, 16],
    "evening": [18, 20, 22],
    "night": [0, 2, 4],
}

_EVENT_HINTS = {
    "education": {6, 8, 10},
    "career_start": {6, 8, 10},
    "career_change": {8, 10, 16},
    "move": {4, 6, 20},
    "relationship": {16, 18, 20},
    "marriage": {16, 18, 20},
    "family": {0, 2, 20},
    "finance": {8, 10, 12},
    "entrepreneurship": {8, 10, 12},
    "health": {0, 2, 4},
}


class HistoricalEvent(BaseModel):
    year: int = Field(..., ge=1500, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    category: Literal[
        "education",
        "career_start",
        "career_change",
        "move",
        "relationship",
        "marriage",
        "family",
        "finance",
        "entrepreneurship",
        "health",
        "other",
    ] = "other"
    description: Optional[str] = Field(None, max_length=300)


class RectifyRequest(BaseModel):
    birth: BirthModel
    birth_time_accuracy: BirthAccuracy = "unknown"
    approximate_hour: Optional[int] = Field(None, ge=0, le=23)
    day_period: Optional[DayPeriod] = None
    known_events: list[HistoricalEvent] = Field(default_factory=list, max_length=8)
    keep_top_n: int = Field(4, ge=1, le=12)


class RectifyCandidate(BaseModel):
    branch: str
    hour: int
    label: str
    score: float
    confidence: Literal["low", "medium", "high"]
    evidence: list[str]
    chart_summary: dict[str, Any] = Field(default_factory=dict)


class RectifyResponse(BaseModel):
    status: Literal["single_exact", "candidate_hours"]
    birth_time_accuracy: BirthAccuracy
    candidates: list[RectifyCandidate]
    best: Optional[RectifyCandidate]
    second: Optional[RectifyCandidate]
    confidence_level: Literal["low", "medium", "high"]
    next_question: Optional[dict[str, Any]] = None
    common_conclusions: list[str] = Field(default_factory=list)
    main_differences: list[str] = Field(default_factory=list)
    uncertainty_note: str
    elapsed_ms: int


def _hour_info(hour: int) -> tuple[str, int, int, str]:
    for item in _BRANCHES:
        if item[2] == hour:
            return item
    return _BRANCHES[((hour + 1) // 2) % 12]


def _candidate_hours(req: RectifyRequest) -> list[int]:
    if req.birth_time_accuracy == "exact":
        return [req.birth.hour]
    if req.birth_time_accuracy == "approximate":
        center = req.approximate_hour if req.approximate_hour is not None else req.birth.hour
        normalized = ((center + 1) // 2 * 2) % 24
        return sorted({(normalized - 2) % 24, normalized, (normalized + 2) % 24})
    if req.birth_time_accuracy == "period" and req.day_period:
        return _PERIOD_HOURS[req.day_period]
    return [item[2] for item in _BRANCHES]


def _stable_jitter(*parts: Any) -> float:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:6], 16) / 0xFFFFFF


def _birth_from_model(bm: BirthModel, hour: int) -> Birth:
    return Birth(
        year=bm.year,
        month=bm.month,
        day=bm.day,
        hour=hour,
        minute=0,
        gender=bm.gender,
        calendar=bm.calendar,
        lat=bm.lat,
        lng=bm.lng,
        tz=bm.tz,
        is_leap_month=bm.is_leap_month,
    )


def _chart_summary(birth: Birth) -> dict[str, Any]:
    try:
        chart = compute("bazi", birth)
        raw = chart.raw
        return {
            "pillars": raw.get("pillars", {}),
            "day_master": raw.get("day_master"),
            "strength": raw.get("断", {}).get("旺衰", {}).get("强弱"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _score_candidate(hour: int, req: RectifyRequest, summary: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.48
    evidence: list[str] = []
    branch = _hour_info(hour)[0]

    pillars = summary.get("pillars") or {}
    hour_pillar = pillars.get("hour")
    if hour_pillar:
        evidence.append(f"候选为{branch}时，八字时柱为{hour_pillar}")
        score += 0.04

    for event in req.known_events:
        preferred = _EVENT_HINTS.get(event.category, set())
        if hour in preferred:
            score += 0.11
            evidence.append(f"{event.year}年{event.category}事件与该时段匹配度较高")
        elif preferred:
            score += 0.03 * _stable_jitter(event.category, event.year, hour)
        else:
            score += 0.02 * _stable_jitter(event.description or "other", event.year, hour)

    if req.birth_time_accuracy == "approximate":
        center = req.approximate_hour if req.approximate_hour is not None else req.birth.hour
        distance = min((hour - center) % 24, (center - hour) % 24)
        score += max(0, 0.12 - distance * 0.03)
        evidence.append("用户提供了大概时辰，邻近候选优先")

    if req.birth_time_accuracy == "period" and req.day_period:
        score += 0.08
        evidence.append("候选位于用户提供的时间段内")

    score += 0.04 * _stable_jitter(req.birth.year, req.birth.month, req.birth.day, hour)
    return min(score, 0.96), evidence or ["资料较少，仅能给出低置信候选"]


def _confidence(score: float) -> Literal["low", "medium", "high"]:
    if score >= 0.76:
        return "high"
    if score >= 0.62:
        return "medium"
    return "low"


def _overall_confidence(candidates: list[RectifyCandidate]) -> Literal["low", "medium", "high"]:
    if len(candidates) <= 1:
        return "high"
    gap = candidates[0].score - candidates[1].score
    if gap >= 0.16:
        return "high"
    if gap >= 0.07:
        return "medium"
    return "low"


def _next_question(candidates: list[RectifyCandidate]) -> Optional[dict[str, Any]]:
    if len(candidates) < 2 or candidates[0].score - candidates[1].score >= 0.07:
        return None
    return {
        "prompt": f"{candidates[0].branch}时和{candidates[1].branch}时很接近。哪类事件更符合你的人生早期？",
        "options": ["升学/考试明显", "搬家/离乡明显", "家庭变化明显", "职业变化更明显"],
    }


@router.post("/birth-time/rectify", response_model=RectifyResponse)
def rectify_birth_time(body: RectifyRequest):
    t0 = time.perf_counter()
    hours = _candidate_hours(body)
    candidates: list[RectifyCandidate] = []

    for hour in hours:
        branch, _start, representative, label = _hour_info(hour)
        birth = _birth_from_model(body.birth, representative)
        summary = _chart_summary(birth)
        score, evidence = _score_candidate(representative, body, summary)
        candidates.append(RectifyCandidate(
            branch=branch,
            hour=representative,
            label=f"{branch}时 {label}",
            score=round(score, 3),
            confidence=_confidence(score),
            evidence=evidence[:4],
            chart_summary=summary,
        ))

    candidates.sort(key=lambda c: c.score, reverse=True)
    if body.birth_time_accuracy == "exact":
        candidates = candidates[:1]
    else:
        candidates = candidates[:body.keep_top_n]

    status: Literal["single_exact", "candidate_hours"] = "single_exact" if body.birth_time_accuracy == "exact" else "candidate_hours"
    confidence_level = _overall_confidence(candidates)
    best = candidates[0] if candidates else None
    second = candidates[1] if len(candidates) > 1 else None

    common = ["日柱与年月柱不随候选时辰变化，可作为共同基础"]
    differences = ["时柱、紫微命宫、上升点等依赖出生时辰，候选间可能明显不同"]
    if best and second:
        differences.append(f"当前最接近的两个候选为{best.branch}时与{second.branch}时")

    return RectifyResponse(
        status=status,
        birth_time_accuracy=body.birth_time_accuracy,
        candidates=candidates,
        best=best,
        second=second,
        confidence_level=confidence_level,
        next_question=_next_question(candidates),
        common_conclusions=common,
        main_differences=differences,
        uncertainty_note="校时结果用于缩小候选范围，不宣称绝对还原真实出生时间。资料越少，结论越应保守使用。",
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )
