"""AI Hour Calibration Tool — 时辰校准引擎

Based on 剑桥图灵子's BV1Jo7o6GEUa:
"你的命盘可能是错的？我做了个AI时辰校准工具，在解决排盘幻觉基础上，
 生成多个命盘来匹配！"

When birth hour is unknown or uncertain, this engine:
1. Generates all 12 two-hour period charts (子丑寅卯辰巳午未申酉戌亥)
2. Extracts discriminative features from each
3. Matches against known life facts (career, personality, events)
4. Scores and ranks each possible hour
5. Returns the most likely hour(s) with confidence levels

This directly solves the "hallucination" problem in AI fortune-telling
by treating unknown birth time as a calibration problem rather than
guessing or fabricating results.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Optional
from ..contracts import Birth, ChartResult


# ── Two-Hour Periods (时柱地支) ─────────────────────────────────────────────

HOUR_BRANCHES = [
    ("子", 23, 1, "深夜·水旺·智谋"),
    ("丑", 1, 3, "凌晨·土旺·沉稳"),
    ("寅", 3, 5, "黎明·木旺·开创"),
    ("卯", 5, 7, "清晨·木旺·仁爱"),
    ("辰", 7, 9, "早间·土旺·厚德"),
    ("巳", 9, 11, "上午·火旺·热情"),
    ("午", 11, 13, "正午·火旺·光明"),
    ("未", 13, 15, "午后·土旺·包容"),
    ("申", 15, 17, "下午·金旺·果决"),
    ("酉", 17, 19, "傍晚·金旺·精致"),
    ("戌", 19, 21, "晚间·土旺·忠诚"),
    ("亥", 21, 23, "深夜·水旺·智慧"),
]

# Hour branch → traits expected
HOUR_TRAITS = {
    "子": {"wisdom": 0.8, "social": 0.5, "introvert": 0.6, "nocturnal": 0.9},
    "丑": {"patient": 0.8, "steady": 0.9, "hardworking": 0.7, "conservative": 0.6},
    "寅": {"leader": 0.8, "pioneer": 0.9, "assertive": 0.7, "ambitious": 0.8},
    "卯": {"gentle": 0.8, "kind": 0.7, "artistic": 0.6, "flexible": 0.7},
    "辰": {"stable": 0.7, "practical": 0.6, "managerial": 0.7, "protective": 0.6},
    "巳": {"passionate": 0.8, "expressive": 0.7, "charismatic": 0.8, "social": 0.7},
    "午": {"bright": 0.8, "energetic": 0.9, "public": 0.7, "generous": 0.6},
    "未": {"nurturing": 0.7, "patient": 0.6, "collector": 0.7, "kind": 0.8},
    "申": {"decisive": 0.8, "sharp": 0.7, "analytical": 0.8, "mobile": 0.7},
    "酉": {"refined": 0.8, "meticulous": 0.7, "aesthetic": 0.8, "eloquent": 0.7},
    "戌": {"loyal": 0.8, "protective": 0.7, "principled": 0.7, "dutiful": 0.6},
    "亥": {"wise": 0.7, "intuitive": 0.8, "deep": 0.7, "creative": 0.7},
}

# Known personality traits → possible hour branches
TRAIT_TO_HOURS = {}
for branch, traits in HOUR_TRAITS.items():
    for trait, score in traits.items():
        if score >= 0.7:
            if trait not in TRAIT_TO_HOURS:
                TRAIT_TO_HOURS[trait] = []
            TRAIT_TO_HOURS[trait].append((branch, score))


# Career → likely elements (for matching)
CAREER_ELEMENT_PREF = {
    "technology": ("金", "水"),
    "engineering": ("金", "土"),
    "finance": ("水", "金"),
    "education": ("木", "金"),
    "medicine": ("木", "火"),
    "law": ("金", "火"),
    "politics": ("火", "土"),
    "military": ("金", "火"),
    "arts": ("木", "火"),
    "business": ("水", "土"),
    "sales": ("火", "水"),
    "service": ("土", "火"),
    "research": ("金", "水"),
    "agriculture": ("土", "木"),
    "sports": ("火", "金"),
    "media": ("火", "木"),
    "spirituality": ("水", "木"),
}


# ── Core Calibration ────────────────────────────────────────────────────────

@dataclass
class HourCandidate:
    """A single birth hour candidate with its computed chart and score."""
    branch: str
    hour: int
    traits: str
    chart: dict
    score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)
    match_details: list = field(default_factory=list)


@dataclass
class CalibrationResult:
    """Complete hour calibration result."""
    candidates: list  # list[HourCandidate] sorted by score descending
    best_hour: Optional[str] = None
    best_confidence: float = 0.0
    top_3: list = field(default_factory=list)
    analysis: str = ""
    recommendation: str = ""


def calibrate(birth: Birth,
              known_traits: Optional[list] = None,
              known_career: Optional[str] = None,
              known_events: Optional[list] = None,
              compute_fn=None) -> CalibrationResult:
    """Calibrate birth hour by generating and scoring all 12 possibilities.

    Args:
        birth: Birth data with unknown/placeholder hour
        known_traits: List of known personality traits (e.g. ["leader", "analytical"])
        known_career: Known career field (e.g. "technology", "finance")
        known_events: List of known life events with years for timing match
        compute_fn: Function to compute bazi chart, defaults to bazi_v2

    Returns:
        CalibrationResult with ranked hour candidates
    """
    if compute_fn is None:
        from . import bazi_v2
        compute_fn = bazi_v2.compute

    candidates = []

    for branch, start_h, end_h, traits_desc in HOUR_BRANCHES:
        # Use midpoint hour for calculation
        mid_hour = start_h if start_h < 23 else 0

        # Create birth with this hour
        test_birth = Birth(
            year=birth.year, month=birth.month, day=birth.day,
            hour=mid_hour, minute=0,
            gender=birth.gender, calendar=birth.calendar,
            lat=birth.lat, lng=birth.lng, tz=birth.tz,
            mode=birth.mode or "natal", subject=birth.subject or "self_life",
        )

        try:
            chart = compute_fn(test_birth)
            chart_dict = chart.to_dict() if hasattr(chart, 'to_dict') else {"raw": chart.raw}
        except Exception:
            chart_dict = {"error": "computation failed"}

        candidates.append(HourCandidate(
            branch=branch,
            hour=mid_hour,
            traits=traits_desc,
            chart=chart_dict,
        ))

    # Score each candidate
    for c in candidates:
        score, breakdown, details = _score_candidate(
            c, known_traits or [], known_career, known_events or []
        )
        c.score = score
        c.score_breakdown = breakdown
        c.match_details = details

    # Sort by score descending
    candidates.sort(key=lambda c: c.score, reverse=True)

    # Build result
    if candidates:
        best = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None

        # Normalize scores
        max_score = best.score if best.score > 0 else 1
        best_confidence = round(best.score / max_score * 100, 1)
        if second and second.score > 0:
            best_confidence = round(best.score / (best.score + second.score) * 100, 1)

        top_3 = [
            {"branch": c.branch, "hour": c.hour, "score": round(c.score, 1),
             "traits": c.traits, "details": c.match_details[:3]}
            for c in candidates[:3]
        ]

        analysis = _generate_calibration_analysis(candidates[:3])

        recommendation = (
            f"最可能的出生时辰为{best.branch}时({best.hour:02d}:00前后)，"
            f"置信度{best_confidence:.0f}%。"
        )
        if best_confidence < 60:
            recommendation += (
                f"建议同时参考{best.branch}时和第二候选"
                f"{candidates[1].branch}时({candidates[1].hour:02d}:00)的命盘。"
            )

    else:
        best = None
        best_confidence = 0.0
        top_3 = []
        analysis = "无法完成时辰校准，请检查输入数据。"
        recommendation = "请提供更多已知信息（性格特征、职业领域、人生大事年份）以提高校准准确度。"

    return CalibrationResult(
        candidates=candidates,
        best_hour=best.branch if best else None,
        best_confidence=best_confidence,
        top_3=top_3,
        analysis=analysis,
        recommendation=recommendation,
    )


def _score_candidate(c: HourCandidate,
                     known_traits: list,
                     known_career: Optional[str] = None,
                     known_events: Optional[list] = None) -> tuple:
    """Score a single hour candidate against known facts.

    Returns (score, breakdown, details).
    """
    score = 0.0
    breakdown = {}
    details = []

    # 1. Trait matching (40% weight)
    trait_score = 0.0
    if known_traits:
        hour_traits = HOUR_TRAITS.get(c.branch, {})
        matches = 0
        total = len(known_traits)
        for trait in known_traits:
            trait_lower = trait.lower()
            # Check exact match in hour traits
            for ht, hs in hour_traits.items():
                if trait_lower in ht or ht in trait_lower:
                    trait_score += hs
                    matches += 1
                    details.append(f"性格特征「{trait}」与{c.branch}时特质「{ht}」匹配(匹配度{hs:.0%})")
                    break
        if matches > 0:
            trait_score = trait_score / total * 40
    else:
        trait_score = 20  # Neutral baseline
    score += trait_score
    breakdown["trait_match"] = round(trait_score, 1)

    # 2. Career/Element matching (30% weight)
    career_score = 0.0
    if known_career:
        pref_elements = CAREER_ELEMENT_PREF.get(known_career.lower(), ())
        if pref_elements:
            raw = c.chart.get("raw", {})
            elements = raw.get("elements", {})
            day_master_element = (raw.get("day_master", "") or "")[:1]

            # Check if preferred elements are strong
            total_el = sum(elements.values()) if elements else 1
            for el in pref_elements:
                career_score += elements.get(el, 0) / total_el * 15

            # Bonus if day master is in preferred element
            if day_master_element in pref_elements:
                career_score += 10
                details.append(f"日主五行{day_master_element}符合{known_career}领域的五行偏好")

            career_score = min(30, career_score)
    else:
        career_score = 15  # Neutral baseline
    score += career_score
    breakdown["career_match"] = round(career_score, 1)

    # 3. Structure quality (20% weight)
    raw = c.chart.get("raw", {})
    struct_score = 0.0

    yong_score = raw.get("yong_shen_quality", {}).get("score", 50)
    struct_score += yong_score / 100 * 10

    pattern = raw.get("pattern", {})
    if pattern.get("pattern"):
        struct_score += 5  # Clear pattern is good

    shensha = raw.get("shensha", {})
    notable = shensha.get("summary", {}).get("notable", [])
    struct_score += min(5, len(notable) * 1.0)

    score += struct_score
    breakdown["structure_quality"] = round(struct_score, 1)

    # 4. Hour pillar traits self-consistency (10% weight)
    hour_score = 0.0
    hour_traits = HOUR_TRAITS.get(c.branch, {})
    hour_score += sum(hour_traits.values()) / len(hour_traits) * 5 if hour_traits else 5
    score += hour_score
    breakdown["hour_traits"] = round(hour_score, 1)

    return score, breakdown, details


def _generate_calibration_analysis(top_3: list) -> str:
    """Generate human-readable analysis of calibration results."""
    if not top_3:
        return "无足够数据进行时辰校准分析。"

    lines = ["时辰校准分析（共评估12个时辰）：", ""]

    for i, c in enumerate(top_3):
        if isinstance(c, dict):
            branch = c["branch"]
            hour = c["hour"]
            score = c["score"]
            traits = c.get("traits", "")
            details = c.get("details", [])
        else:
            branch = c.branch
            hour = c.hour
            score = c.score
            traits = c.traits
            details = c.match_details

        lines.append(f"{i+1}. {branch}时({hour:02d}:00前后) — 综合评分{score}")
        lines.append(f"   {traits}")
        if details:
            for d in details[:3]:
                lines.append(f"   ✓ {d}")

    # Score gap analysis
    if len(top_3) >= 2:
        s0 = top_3[0].score if hasattr(top_3[0], 'score') else top_3[0]["score"]
        s1 = top_3[1].score if hasattr(top_3[1], 'score') else top_3[1]["score"]
        gap = s0 - s1
        pct = gap / max(1, s0) * 100
        branch0 = top_3[0].branch if hasattr(top_3[0], 'branch') else top_3[0]["branch"]
        lines.append("")
        if pct > 20:
            lines.append(f"首选时辰({branch0}时)与次选差距显著({pct:.0f}%)，可信度较高。")
        elif pct > 10:
            lines.append(f"首选与次选有一定差距({pct:.0f}%)，建议以首选时辰为主。")
        else:
            lines.append(f"首选与次选差距较小({pct:.0f}%)，建议同时参考两者。")

    return "\n".join(lines)


# ── Quick Hour Estimation ───────────────────────────────────────────────────

def quick_estimate(birth: Birth, compute_fn=None) -> dict:
    """Quick hour estimation without known facts — purely structure-based.

    Useful when user has no known facts to match against.
    Ranks hours by chart quality (pattern clarity, yong shen quality, flow).
    """
    result = calibrate(birth, compute_fn=compute_fn)
    return {
        "best_hour": result.best_hour,
        "best_confidence": result.best_confidence,
        "top_3": result.top_3,
        "note": "此结果为纯结构评分，未参考已知人生事实。提供更多信息可大幅提高准确度。",
    }


def estimate_from_traits(traits: list, compute_fn=None) -> dict:
    """Reverse-calibrate: given personality traits, suggest most likely hours.

    This is useful for the "what might my birth hour be?" question
    when the user knows their personality but not their birth time.
    """
    hour_scores = {}
    for trait in traits:
        trait_lower = trait.lower()
        matches = TRAIT_TO_HOURS.get(trait_lower, [])
        for branch, score in matches:
            hour_scores[branch] = hour_scores.get(branch, 0) + score

    # Normalize
    sorted_hours = sorted(hour_scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "top_hours": [
            {"branch": b, "score": round(s, 2),
             "traits": HOUR_TRAITS.get(b, {}).get("traits", "")}
            for b, s in sorted_hours[:5]
        ],
        "note": "此为基于性格特征反向推算的可能出生时辰，仅供参考。建议结合具体出生时间校准。",
    }
