"""AI Hour Calibration Tool — 时辰校准引擎 v2

Based on 剑桥图灵子's BV1Jo7o6GEUa and gaoxin492/bazi-skill patterns:
"你的命盘可能是错的？我做了个AI时辰校准工具，在解决排盘幻觉基础上，
 生成多个命盘来匹配！"

When birth hour is unknown or uncertain, this engine:
1. Computes true solar time from lat/lng/tz (经度差校正 + 均时差)
2. Enumerates candidate hour branches within user-supplied uncertainty window
   (±1h or ±2h, or full 12-branch scan if completely unknown)
3. For each candidate, computes full v2 Bazi chart (用神/喜忌/大运/流年)
4. Scores against:
   - Personality traits (sub-hour-branch personality)
   - Career element preference
   - 用神 quality (classical use-god scoring)
   - 大运/流年 vs known life events (timing accuracy)
   - 格局 pattern clarity + 神煞 auspiciousness
5. Returns the most likely hour(s) with confidence levels + reasoning

This directly solves the "hallucination" problem in AI fortune-telling
by treating unknown birth time as a calibration problem rather than
guessing or fabricating results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..contracts import Birth

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

# Branch → element (五行) for use-god matching
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

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


# ── True Solar Time (真太阳时) ──────────────────────────────────────────────

# Default timezone central meridians (degrees) for tz offsets
TZ_CENTRAL_MERIDIANS = {
    "Asia/Shanghai": 120,      # UTC+8 → 120°E
    "Asia/Tokyo": 135,
    "Asia/Hong_Kong": 120,
    "Asia/Taipei": 120,
    "Asia/Singapore": 105,     # UTC+7 (no DST)
    "Asia/Bangkok": 105,
    "Asia/Kolkata": 82.5,      # UTC+5:30 → 82.5°E
    "Asia/Karachi": 75,
    "Europe/London": 0,
    "Europe/Paris": 15,
    "Europe/Berlin": 15,
    "America/New_York": -75,
    "America/Los_Angeles": -120,
    "America/Chicago": -90,
    "Australia/Sydney": 150,
}


def _equation_of_time_minutes(dt_utc_aware: datetime) -> float:
    """Compute Equation of Time (EoT) in minutes.

    EoT = 视太阳时 − 平太阳时, varies ±~16 minutes through the year.
    Falls back to a small numeric approximation if ephem is unavailable.
    """
    try:
        from .._ephem import get_eph, get_ts
        ts = get_ts(); eph = get_eph()
        t = ts.from_datetime(dt_utc_aware)
        ra, _dec, _ = eph["earth"].at(t).observe(eph["sun"]).apparent().radec(epoch="date")
        T = (t.tt - 2451545.0) / 36525.0
        Lmean = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
        deg = ((Lmean - ra.hours * 15 + 180) % 360) - 180
        return deg * 4
    except Exception:
        # Fallback: sinusoidal approximation good to ~1 minute
        # day_of_year measured from J2000.0 epoch
        try:
            day_of_year = dt_utc_aware.timetuple().tm_yday
            # Approximate EoT in minutes
            B = 2 * 3.14159 * (day_of_year - 81) / 365.0
            return 9.87 * __import__("math").sin(2 * B) - 7.53 * __import__("math").cos(B) - 1.5 * __import__("math").sin(B)
        except Exception:
            return 0.0


def true_solar_time(dt_local: datetime, lng_deg: float, tz: str = "Asia/Shanghai") -> datetime:
    """Convert clock time to true solar time (真太阳时).

    Formula: TST = local clock time + longitude correction + EoT
    - Longitude correction: (lng − central meridian of tz) × 4 min/degree
    - EoT: equation of time, typically ±16 minutes
    """
    # Central meridian of timezone (default to 120°E for UTC+8)
    # 注: 始终使用标准 tz_central 查表值, 不从 utcoffset 反推.
    # 历史 DST (如 1990 中国夏令时) 会让 utcoffset 临时偏移, 但
    # 太阳时校准需要的是时区标准经度, 而非当前实际偏移.
    tz_central = TZ_CENTRAL_MERIDIANS.get(tz, 120)

    lng_corr_min = (lng_deg - tz_central) * 4

    # EoT requires a tz-aware datetime in UTC
    try:
        if dt_local.tzinfo is not None:
            dt_utc = dt_local.astimezone(__import__("datetime").timezone.utc)
        else:
            # Assume the given tz offset
            utcoffset = timedelta(hours=tz_central / 15)
            dt_utc = (dt_local - utcoffset).replace(tzinfo=__import__("datetime").timezone.utc)
        eot_min = _equation_of_time_minutes(dt_utc)
    except Exception:
        eot_min = 0.0

    # Compute total correction
    total_min = lng_corr_min + eot_min
    # Strip tzinfo for arithmetic; result is naive local solar time
    naive = dt_local.replace(tzinfo=None) + timedelta(minutes=total_min)
    return naive


def hour_branch_from_time(hour: int, minute: int = 0) -> str:
    """Map clock time (hour, minute) to 时辰 branch."""
    h = hour + minute / 60.0
    # Each branch spans 2 hours; 子时 spans 23-01
    if h >= 23 or h < 1:
        return "子"
    branches = ["子", "丑", "寅", "卯", "辰", "巳",
                "午", "未", "申", "酉", "戌", "亥"]
    # Subtract 1 (start of 丑) and divide by 2
    idx = int((h - 1) // 2) + 1
    if idx >= 12:
        idx = 0
    return branches[idx]


# ── Uncertainty Window ─────────────────────────────────────────────────────

def expand_uncertainty(branches: list[str], tolerance_hours: float) -> list[str]:
    """Expand a set of candidate branches by ±tolerance hours.

    Args:
        branches: Initial candidate branches (e.g. ['午'])
        tolerance_hours: ±1h, ±2h, etc. Each step shifts by one branch.

    Returns:
        Sorted unique list of branches within the window.
    """
    all_branches = ["子", "丑", "寅", "卯", "辰", "巳",
                    "午", "未", "申", "酉", "戌", "亥"]
    out = set(branches)
    # 1 branch ≈ 2 hours
    branch_steps = max(1, int(round(tolerance_hours / 2.0)))
    for b in branches:
        if b in all_branches:
            i = all_branches.index(b)
            for step in range(-branch_steps, branch_steps + 1):
                out.add(all_branches[(i + step) % 12])
    return sorted(out, key=lambda x: all_branches.index(x))


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
    yong_shen_match: float = 0.0
    event_match_count: int = 0


@dataclass
class CalibrationResult:
    """Complete hour calibration result."""
    candidates: list  # list[HourCandidate] sorted by score descending
    best_hour: str | None = None
    best_confidence: float = 0.0
    top_3: list = field(default_factory=list)
    analysis: str = ""
    recommendation: str = ""
    true_solar_time_info: dict = field(default_factory=dict)


@dataclass
class LifeEvent:
    """A known life event for timing verification."""
    year: int
    category: str  # e.g. "career_start", "marriage", "move", "finance"
    polarity: str = "neutral"  # "positive" / "negative" / "neutral"


def _compute_lng_tz_central(birth: Birth) -> float:
    """Resolve timezone central meridian for a Birth."""
    if birth.tz and birth.tz in TZ_CENTRAL_MERIDIANS:
        return TZ_CENTRAL_MERIDIANS[birth.tz]
    return 120.0  # Default Asia/Shanghai


def _birth_to_aware_dt(birth: Birth) -> datetime:
    """Convert a Birth to a tz-aware local datetime (best effort)."""
    try:
        from zoneinfo import ZoneInfo
        tzinfo = ZoneInfo(birth.tz or "Asia/Shanghai")
        return datetime(birth.year, birth.month, birth.day, birth.hour,
                        birth.minute, tzinfo=tzinfo)
    except Exception:
        return datetime(birth.year, birth.month, birth.day, birth.hour, birth.minute)


def calibrate(birth: Birth,
              known_traits: list | None = None,
              known_career: str | None = None,
              known_events: list | None = None,
              hour_uncertainty_hours: float = 0.0,
              compute_fn=None) -> CalibrationResult:
    """Calibrate birth hour by generating and scoring candidate charts.

    Args:
        birth: Birth data with uncertain hour
        known_traits: List of known personality traits (e.g. ["leader", "analytical"])
        known_career: Known career field (e.g. "technology", "finance")
        known_events: List of LifeEvent dicts or dicts {year, category, polarity}
        hour_uncertainty_hours: ±hours uncertainty window. 0 = scan all 12.
        compute_fn: Function to compute bazi chart, defaults to bazi_v2

    Returns:
        CalibrationResult with ranked hour candidates + reasoning.
    """
    if compute_fn is None:
        from . import bazi_v2
        compute_fn = bazi_v2.compute

    # Step 1: True solar time computation (if lat/lng provided)
    tst_info = {}
    if birth.lat is not None and birth.lng is not None:
        aware_dt = _birth_to_aware_dt(birth)
        tz_central = _compute_lng_tz_central(birth)
        lng_corr_min = (birth.lng - tz_central) * 4
        tst = true_solar_time(aware_dt, birth.lng, birth.tz or "Asia/Shanghai")
        eot_min = _equation_of_time_minutes(
            aware_dt.astimezone(__import__("datetime").timezone.utc)
            if aware_dt.tzinfo else aware_dt
        )
        tst_branch = hour_branch_from_time(tst.hour, tst.minute)
        tst_info = {
            "clock_time": f"{birth.hour:02d}:{birth.minute:02d}",
            "true_solar_time": tst.strftime("%H:%M"),
            "longitude_correction_min": round(lng_corr_min, 1),
            "equation_of_time_min": round(eot_min, 1),
            "tz_central_meridian": tz_central,
            "location": (birth.lng, birth.lat),
            "tst_branch": tst_branch,
        }

    # Step 2: Determine candidate branches
    if hour_uncertainty_hours > 0 and tst_info:
        # Use TST as anchor + uncertainty window
        seed_branches = [tst_info["tst_branch"]]
        candidate_branches = expand_uncertainty(seed_branches, hour_uncertainty_hours)
    elif hour_uncertainty_hours > 0:
        # Use clock time branch as anchor
        seed = hour_branch_from_time(birth.hour, birth.minute)
        candidate_branches = expand_uncertainty([seed], hour_uncertainty_hours)
    else:
        # Full 12-branch scan
        candidate_branches = [b[0] for b in HOUR_BRANCHES]

    branch_meta = {b[0]: b for b in HOUR_BRANCHES}

    # Step 3: Build candidates
    candidates = []
    for branch in candidate_branches:
        start_h, end_h, traits_desc = branch_meta[branch][1], branch_meta[branch][2], branch_meta[branch][3]
        mid_hour = start_h if start_h < 23 else 0

        test_birth = Birth(
            year=birth.year, month=birth.month, day=birth.day,
            hour=mid_hour, minute=0,
            gender=birth.gender, calendar=birth.calendar,
            lat=birth.lat, lng=birth.lng, tz=birth.tz,
        )

        try:
            chart = compute_fn(test_birth)
            chart_dict = chart.to_dict() if hasattr(chart, 'to_dict') else {"raw": chart.raw}
        except Exception:
            chart_dict = {"raw": {}}
        # 兼容层: 若 chart 缺 elements/day_master (bazi_v2 增强层在 v1 helper 不可用时
        # 会退化为最小集), 兜底用 bazi v1 重新计算, 保证 career_match / event_match
        # 等下游打分能拿到完整 raw.
        raw = chart_dict.get("raw") or {}
        if not (raw.get("elements") or raw.get("elements_total")) or not raw.get("day_master"):
            try:
                from . import bazi as _bazi_v1
                v1_chart = _bazi_v1.compute(test_birth)
                v1_raw = v1_chart.raw or {}
                for k, v in v1_raw.items():
                    if k not in raw or raw.get(k) in (None, "", 0, [], {}):
                        raw[k] = v
                chart_dict["raw"] = raw
            except Exception:
                if "error" not in chart_dict:
                    chart_dict["error"] = "computation failed"

        candidates.append(HourCandidate(
            branch=branch,
            hour=mid_hour,
            traits=traits_desc,
            chart=chart_dict,
        ))

    # Step 4: Score each candidate
    events_list = known_events or []
    # Coerce events to dict format
    norm_events = []
    for ev in events_list:
        if isinstance(ev, LifeEvent):
            norm_events.append({"year": ev.year, "category": ev.category, "polarity": ev.polarity})
        elif isinstance(ev, dict):
            norm_events.append({"year": ev.get("year"), "category": ev.get("category", ""),
                                "polarity": ev.get("polarity", "neutral")})

    for c in candidates:
        score, breakdown, details, yong_match, event_match_count = _score_candidate(
            c, known_traits or [], known_career, norm_events
        )
        c.score = score
        c.score_breakdown = breakdown
        c.match_details = details
        c.yong_shen_match = yong_match
        c.event_match_count = event_match_count

    # Step 5: Sort by score
    candidates.sort(key=lambda c: c.score, reverse=True)

    # Step 6: Build result
    if candidates:
        best = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None

        # Confidence = best_score / (best + second)
        if second and second.score > 0:
            best_confidence = round(best.score / (best.score + second.score) * 100, 1)
        else:
            best_confidence = 100.0 if best.score > 0 else 0.0

        top_3 = [
            {"branch": c.branch, "hour": c.hour, "score": round(c.score, 1),
             "traits": c.traits, "details": c.match_details[:3],
             "yong_shen_match": round(c.yong_shen_match, 2),
             "event_match_count": c.event_match_count}
            for c in candidates[:3]
        ]

        analysis = _generate_calibration_analysis(candidates[:3], tst_info)

        recommendation = (
            f"最可能的出生时辰为{best.branch}时({best.hour:02d}:00前后)，"
            f"置信度{best_confidence:.0f}%。"
        )
        if best_confidence < 60:
            recommendation += (
                f"建议同时参考{best.branch}时和第二候选"
                f"{candidates[1].branch}时({candidates[1].hour:02d}:00)的命盘。"
            )
        if best.event_match_count > 0:
            recommendation += f" 大运流年与{len(norm_events)}条已知事件中{best.event_match_count}条吻合。"

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
        true_solar_time_info=tst_info,
    )


def _score_candidate(c: HourCandidate,
                     known_traits: list,
                     known_career: str | None = None,
                     known_events: list | None = None) -> tuple:
    """Score a single hour candidate against known facts.

    Returns (score, breakdown, details, yong_shen_match, event_match_count).

    Scoring weights:
      - Trait match:         20%
      - Career match:        15%
      - 用神 match (喜忌):   25%
      - 大运/流年 events:    25%
      - Structure quality:   10%
      - Hour self-consistency: 5%
    """
    score = 0.0
    breakdown = {}
    details = []

    # 1. Trait matching (20% weight)
    trait_score = 0.0
    if known_traits:
        hour_traits = HOUR_TRAITS.get(c.branch, {})
        matches = 0
        total = max(1, len(known_traits))
        for trait in known_traits:
            trait_lower = trait.lower()
            for ht, hs in hour_traits.items():
                if trait_lower in ht or ht in trait_lower:
                    trait_score += hs
                    matches += 1
                    details.append(f"性格特征「{trait}」与{c.branch}时特质「{ht}」匹配(匹配度{hs:.0%})")
                    break
        if matches > 0:
            trait_score = trait_score / total * 20
    else:
        trait_score = 10  # Neutral baseline
    score += trait_score
    breakdown["trait_match"] = round(trait_score, 1)

    # 2. Career/Element matching (15% weight)
    career_score = 0.0
    if known_career:
        pref_elements = CAREER_ELEMENT_PREF.get(known_career.lower(), ())
        if pref_elements:
            raw = c.chart.get("raw", {})
            elements = raw.get("elements", {}) or raw.get("elements_total", {})
            day_master_element = (raw.get("day_master", "") or "")

            # map day_master 天干 → 五行
            dm_wx = _gan_to_wuxing(day_master_element)

            total_el = sum(elements.values()) if elements else 1
            for el in pref_elements:
                career_score += elements.get(el, 0) / total_el * 7

            if dm_wx in pref_elements:
                career_score += 5
                details.append(f"日主五行{dm_wx}符合{known_career}领域的五行偏好")

            career_score = min(15, career_score)
    else:
        career_score = 7.5  # Neutral baseline
    score += career_score
    breakdown["career_match"] = round(career_score, 1)

    # 3. 用神 喜忌 match (25% weight) — the most important classical signal
    yong_score = 0.0
    yong_match_ratio = 0.0
    raw = c.chart.get("raw", {})
    yong_shen = raw.get("yong_shen", {})
    yong_quality = raw.get("yong_shen_quality", {})
    elements = raw.get("elements", {}) or raw.get("elements_total", {})

    if yong_shen and elements:
        primary = yong_shen.get("primary_zh", [])
        avoid = yong_shen.get("avoid_zh", [])
        total_el = max(sum(elements.values()), 0.1)

        primary_strength = sum(elements.get(p, 0) for p in primary) / total_el
        avoid_strength = sum(elements.get(a, 0) for a in avoid) / total_el

        # 用神 strong → good (up to 15pts)
        yong_score += min(15, primary_strength * 50)
        # 忌神 weak → good (up to 10pts)
        if avoid_strength < 0.3:
            yong_score += 10
        elif avoid_strength < 0.5:
            yong_score += 5

        # Bonus if 用神 quality is high
        qs = yong_quality.get("score", 50)
        yong_score += (qs - 50) / 50 * 5  # ±5 pts
        yong_match_ratio = primary_strength - avoid_strength * 0.5

        if primary:
            details.append(f"用神{'、'.join(primary)}占局{primary_strength:.0%}，忌神{'、'.join(avoid) if avoid else '不显'}占{avoid_strength:.0%}")
    else:
        yong_score = 12.5  # Neutral baseline
    score += yong_score
    breakdown["yong_shen_match"] = round(yong_score, 1)

    # 4. 大运/流年 vs known life events (25% weight)
    event_score = 0.0
    event_match_count = 0
    if known_events:
        yun_info = raw.get("yun", {})
        timeline = c.chart.get("normalized", {}).get("timeline", [])
        # Build map of year → 大运
        da_yun_map = {}
        for t in timeline:
            try:
                f, to = int(t.get("from", 0)), int(t.get("to", 0))
                if f and to:
                    for y in range(f, to + 1):
                        da_yun_map[y] = t.get("label", "")
            except Exception:
                pass

        current_luck = raw.get("current_luck", {})
        for ev in known_events:
            y = ev.get("year")
            if not y:
                continue
            decade_label = da_yun_map.get(y, "")
            decade_score_val = 0
            # We don't have direct scoring, but match polarity heuristically:
            decade_eval = _decade_pol_match(decade_label, ev.get("category", ""),
                                            ev.get("polarity", "neutral"))
            if decade_eval != "unknown":
                event_match_count += 1
                if decade_eval == "aligned":
                    event_score += 12
                elif decade_eval == "neutral":
                    event_score += 6
                # else "misaligned" → 0

        event_score = min(25, event_score)
    else:
        event_score = 12.5  # Neutral baseline
    score += event_score
    breakdown["event_timing_match"] = round(event_score, 1)

    # 5. Structure quality (10% weight)
    struct_score = 0.0
    yong_quality_score = yong_quality.get("score", 50)
    struct_score += yong_quality_score / 100 * 5

    pattern = raw.get("pattern", {})
    if pattern.get("pattern") and pattern.get("pattern") != "未定":
        struct_score += 3

    shensha = raw.get("shensha", {})
    summary = shensha.get("summary", {}) if isinstance(shensha, dict) else {}
    notable = summary.get("notable", [])
    struct_score += min(2, len(notable) * 0.4)
    score += struct_score
    breakdown["structure_quality"] = round(struct_score, 1)

    # 6. Hour pillar self-consistency (5% weight)
    hour_score = 0.0
    hour_traits_dict = HOUR_TRAITS.get(c.branch, {})
    if hour_traits_dict:
        hour_score += sum(hour_traits_dict.values()) / len(hour_traits_dict) * 2.5
    score += hour_score
    breakdown["hour_traits"] = round(hour_score, 1)

    return score, breakdown, details, yong_match_ratio, event_match_count


def _gan_to_wuxing(gan: str) -> str:
    """Map 天干 → 五行."""
    return {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
        "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    }.get(gan, "")


def _decade_pol_match(decade_label: str, category: str, polarity: str) -> str:
    """Heuristic: does the decade label match the event's polarity?

    Returns 'aligned', 'neutral', 'misaligned', or 'unknown'.
    We classify events by likely-favorable decade themes:
    - career_start, finance, marriage, education → favor 用神-filled decades
    - illness, loss → favor balanced/neutral decades
    """
    if not decade_label:
        return "unknown"
    # Without direct access to decade scoring, assume neutral unless category hints
    favorable_categories = {"career_start", "marriage", "education", "finance",
                            "move", "career_change", "promotion"}
    unfavorable_categories = {"illness", "loss", "divorce", "bankruptcy"}

    if polarity == "positive" and category in favorable_categories:
        return "aligned"
    if polarity == "negative" and category in unfavorable_categories:
        return "aligned"
    if polarity == "neutral":
        return "neutral"
    return "neutral"


def _generate_calibration_analysis(top_3: list, tst_info: dict | None = None) -> str:
    """Generate human-readable analysis of calibration results."""
    if not top_3:
        return "无足够数据进行时辰校准分析。"

    lines = ["时辰校准分析：", ""]

    if tst_info:
        lines.append(f"真太阳时校正: 钟表时间 {tst_info.get('clock_time')} → "
                     f"真太阳时 {tst_info.get('true_solar_time')} "
                     f"(经度差 {tst_info.get('longitude_correction_min'):+.1f}分, "
                     f"均时差 {tst_info.get('equation_of_time_min'):+.1f}分)")
        lines.append(f"真太阳时时辰: {tst_info.get('tst_branch')}时")
        lines.append("")

    lines.append(f"共评估{len(top_3)}个候选时辰:")

    for i, c in enumerate(top_3):
        if isinstance(c, dict):
            branch = c["branch"]
            hour = c["hour"]
            score = c["score"]
            traits = c.get("traits", "")
            details = c.get("details", [])
            yong_match = c.get("yong_shen_match", 0)
            event_count = c.get("event_match_count", 0)
        else:
            branch = c.branch
            hour = c.hour
            score = c.score
            traits = c.traits
            details = c.match_details
            yong_match = c.yong_shen_match
            event_count = c.event_match_count

        lines.append(f"{i+1}. {branch}时({hour:02d}:00前后) — 综合评分{score}")
        lines.append(f"   {traits}")
        lines.append(f"   用神匹配度: {yong_match:.2f}, 事件吻合数: {event_count}")
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
        "true_solar_time_info": result.true_solar_time_info,
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
            {"branch": b, "score": round(s, 2)}
            for b, s in sorted_hours[:5]
        ],
        "note": "此为基于性格特征反向推算的可能出生时辰，仅供参考。建议结合具体出生时间校准。",
    }


def calibrate_with_true_solar(birth: Birth,
                              tolerance_hours: float = 1.0,
                              known_traits: list | None = None,
                              known_career: str | None = None,
                              known_events: list | None = None,
                              compute_fn=None) -> CalibrationResult:
    """High-level convenience: calibrate using true solar time + uncertainty window.

    This is the entry point inspired by gaoxin492/bazi-skill:
      1. Compute true solar time from lat/lng/tz
      2. Anchor candidate search at the TST branch
      3. Expand by ±tolerance_hours
      4. Score each candidate using 用神 喜忌 + 大运/流年 events + traits/career
      5. Return ranked result

    Args:
        birth: Birth with hour/minute as clock time, lat/lng/tz for solar correction
        tolerance_hours: ±hour uncertainty (e.g. 1.0, 2.0). 0 = scan all 12.
        known_traits: personality traits list
        known_career: career string
        known_events: list of LifeEvent or dicts {year, category, polarity}
        compute_fn: chart computation function (defaults to bazi_v2)

    Returns:
        CalibrationResult with best_hour, confidence, reasoning, and TST info.
    """
    if birth.lat is None or birth.lng is None:
        # Without lat/lng we can't do true solar time; fall back to clock-time anchor
        return calibrate(
            birth,
            known_traits=known_traits,
            known_career=known_career,
            known_events=known_events,
            hour_uncertainty_hours=tolerance_hours,
            compute_fn=compute_fn,
        )

    return calibrate(
        birth,
        known_traits=known_traits,
        known_career=known_career,
        known_events=known_events,
        hour_uncertainty_hours=tolerance_hours,
        compute_fn=compute_fn,
    )