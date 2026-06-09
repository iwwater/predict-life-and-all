"""POST /api/compute - unified chart endpoint with mode/subject options."""
import logging
import time
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from divination import Birth
from divination.meta import method_meta
from divination.router import _ENGINES, compute_with_validation, calibrate_birth_hour, estimate_hour_from_traits, compute_compatibility_score, compute_multimethod_compatibility

router = APIRouter()
log = logging.getLogger("chart")


class BirthModel(BaseModel):
    year: int = Field(..., ge=1500, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: Literal["male", "female", "unspecified"] = "unspecified"
    calendar: Literal["gregorian", "lunar"] = "gregorian"
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False


class ComputeRequest(BaseModel):
    method: str
    birth: BirthModel
    options: dict = Field(default_factory=dict)


ALLOWED_OPTIONS = {
    "mode",
    "subject",
    "spread",
    "seed",
    "question",
    "tosses",
    "period",
    "sitting",
    "construction_year",
    "method_inputs",
    "father_zodiac",
    "mother_zodiac",
    "name",
    "full_name",
    # Multi-method orchestration (accepted but not used by single-method compute)
    "methods",
    "modeByMethod",
}


@router.post("/compute")
def compute_endpoint(body: ComputeRequest):
    if body.method not in _ENGINES:
        raise HTTPException(404, f"unsupported method: {body.method}")

    meta = method_meta(body.method)
    options = dict(body.options or {})
    method_inputs = options.pop("method_inputs", {}) or {}
    if not isinstance(method_inputs, dict):
        raise HTTPException(422, "options.method_inputs must be an object")
    options.update(method_inputs)

    unknown = set(options) - ALLOWED_OPTIONS
    if unknown:
        raise HTTPException(422, f"unsupported option(s): {sorted(unknown)}")

    mode = options.get("mode") or meta.get("default_mode")
    if mode not in meta.get("modes", []):
        raise HTTPException(422, f"unsupported mode for {body.method}: {mode}")
    options["mode"] = mode
    options.setdefault("subject", (meta.get("subjects") or [None])[0])

    # Validate spread if provided and method supports spreads
    if "spread" in options:
        spread = options["spread"]
        # Lenormand and Tarot are the two methods with custom spread systems
        if body.method in ("tarot", "lenormand"):
            try:
                from divination.engines.tarot import SPREADS as TAROT_SPREADS, ALIASES as TAROT_ALIASES
                if spread not in TAROT_SPREADS and spread not in TAROT_ALIASES:
                    if body.method == "lenormand":
                        from divination.engines.lenormand import SPREADS as LEN_SPREADS
                        if spread not in LEN_SPREADS:
                            raise HTTPException(422, f"unsupported spread for {body.method}: {spread}")
            except ImportError:
                pass  # engine not available, skip validation

    b = body.birth
    birth = Birth(
        year=b.year,
        month=b.month,
        day=b.day,
        hour=b.hour,
        minute=b.minute,
        gender=b.gender,
        calendar=b.calendar,
        lat=b.lat,
        lng=b.lng,
        tz=b.tz,
        is_leap_month=b.is_leap_month,
    )
    for key, value in options.items():
        if key in ALLOWED_OPTIONS:
            setattr(birth, key, value)

    t0 = time.perf_counter()
    try:
        result = _ENGINES[body.method](birth)
    except Exception as e:
        log.exception("compute failed: %s/%s", body.method, e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    dt_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "method": result.method,
        "school": result.school,
        "engine": result.engine,
        "normalized": result.normalized,
        "raw": result.raw,
        "elapsed_ms": dt_ms,
    }


# ── Advanced Multi-Method Endpoints ──────────────────────────────────────────

class MultiComputeRequest(BaseModel):
    methods: list = Field(..., min_length=1, max_length=5)
    birth: BirthModel
    subject: str = "self_life"
    do_validate: bool = True


class HourCalibrateRequest(BaseModel):
    birth: BirthModel
    known_traits: Optional[list] = None
    known_career: Optional[str] = None
    known_events: Optional[list] = None


class TraitEstimateRequest(BaseModel):
    traits: list = Field(..., min_length=1)


class CompatibilityRequest(BaseModel):
    chart1_birth: BirthModel
    chart2_birth: BirthModel
    method: str = "bazi_v2"
    methods: Optional[list] = None  # multi-method: ["bazi_v2", "western"]
    subject: str = "relationship"


@router.post("/compute/multi")
def compute_multi_endpoint(body: MultiComputeRequest):
    """Compute multiple charts with cross-system validation.

    Returns charts + cross-validation for higher accuracy.
    This is the recommended endpoint for multi-method analysis.
    """
    unknown = [m for m in body.methods if m not in _ENGINES]
    if unknown:
        raise HTTPException(422, f"unsupported method(s): {unknown}")

    b = body.birth
    birth = Birth(
        year=b.year, month=b.month, day=b.day,
        hour=b.hour, minute=b.minute,
        gender=b.gender, calendar=b.calendar,
        lat=b.lat, lng=b.lng, tz=b.tz,
    )

    t0 = time.perf_counter()
    try:
        result = compute_with_validation(
            body.methods, birth, body.subject, body.do_validate
        )
    except Exception as e:
        log.exception("multi compute failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    dt_ms = int((time.perf_counter() - t0) * 1000)

    # Serialize charts
    serialized_charts = {}
    for m, chart in result.get("charts", {}).items():
        serialized_charts[m] = {
            "method": chart.method,
            "school": chart.school,
            "engine": chart.engine,
            "normalized": chart.normalized,
            "raw": chart.raw,
        }

    response = {
        "charts": serialized_charts,
        "elapsed_ms": dt_ms,
    }

    if "cross_validation" in result:
        response["cross_validation"] = result["cross_validation"]
    if "peach_blossom" in result:
        response["peach_blossom"] = result["peach_blossom"]
    if "relationship_timing" in result:
        response["relationship_timing"] = result["relationship_timing"]
    if "fate_modification" in result:
        response["fate_modification"] = result["fate_modification"]

    return response


@router.post("/calibrate/hour")
def calibrate_hour_endpoint(body: HourCalibrateRequest):
    """Calibrate uncertain birth hour by scoring all 12 possibilities.

    Generates 12 charts (one per two-hour period) and matches them
    against known life facts to determine the most likely birth hour.
    """
    b = body.birth
    birth = Birth(
        year=b.year, month=b.month, day=b.day,
        hour=b.hour, minute=b.minute,
        gender=b.gender, calendar=b.calendar,
        lat=b.lat, lng=b.lng, tz=b.tz,
    )

    t0 = time.perf_counter()
    try:
        result = calibrate_birth_hour(
            birth, body.known_traits, body.known_career, body.known_events
        )
    except Exception as e:
        log.exception("hour calibration failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    dt_ms = int((time.perf_counter() - t0) * 1000)

    result["elapsed_ms"] = dt_ms
    return result


@router.post("/estimate/traits")
def estimate_traits_endpoint(body: TraitEstimateRequest):
    """Reverse-estimate likely birth hours from personality traits.

    Given known personality traits, suggest which birth hours
    are most consistent with those traits.
    """
    try:
        result = estimate_hour_from_traits(body.traits)
    except Exception as e:
        log.exception("trait estimation failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    return result


@router.post("/compatibility")
def compatibility_endpoint(body: CompatibilityRequest):
    """Compute relationship compatibility between two birth charts.

    Supports single-method (bazi_v2 or western) and multi-method
    (e.g., ["bazi_v2", "western"]) with weighted ensemble scoring.
    """
    b1 = body.chart1_birth
    b2 = body.chart2_birth
    birth1 = Birth(
        year=b1.year, month=b1.month, day=b1.day,
        hour=b1.hour, minute=b1.minute,
        gender=b1.gender, calendar=b1.calendar,
        lat=b1.lat, lng=b1.lng, tz=b1.tz,
    )
    birth2 = Birth(
        year=b2.year, month=b2.month, day=b2.day,
        hour=b2.hour, minute=b2.minute,
        gender=b2.gender, calendar=b2.calendar,
        lat=b2.lat, lng=b2.lng, tz=b2.tz,
    )

    t0 = time.perf_counter()

    # Multi-method compatibility
    if body.methods and len(body.methods) >= 2:
        try:
            charts1 = {}
            charts2 = {}
            for m in body.methods:
                if m not in _ENGINES:
                    continue
                try:
                    charts1[m] = _ENGINES[m](birth1)
                    charts2[m] = _ENGINES[m](birth2)
                except Exception:
                    pass

            result = compute_multimethod_compatibility(
                {m: c.raw for m, c in charts1.items()},
                {m: c.raw for m, c in charts2.items()},
                body.methods,
            )
        except Exception as e:
            log.exception("multi-method compatibility failed: %s", e)
            raise HTTPException(500, f"{type(e).__name__}: {e}")
    else:
        # Single-method compatibility
        method = body.method
        if method not in _ENGINES:
            raise HTTPException(422, f"unsupported method: {method}")

        try:
            chart1 = _ENGINES[method](birth1)
            chart2 = _ENGINES[method](birth2)
            result = compute_compatibility_score(
                {"raw": chart1.raw}, {"raw": chart2.raw}, method
            )
        except Exception as e:
            log.exception("compatibility compute failed: %s", e)
            raise HTTPException(500, f"{type(e).__name__}: {e}")

    dt_ms = int((time.perf_counter() - t0) * 1000)
    result["elapsed_ms"] = dt_ms
    return result
