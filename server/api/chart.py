"""POST /api/compute - unified chart endpoint with mode/subject options."""
import logging
import inspect
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from divination import Birth
from divination.engines.hour_calibrator import calibrate as calibrate_hour_engine
from divination.meta import method_meta
from divination.router import (
    _ENGINES,
    compute_compatibility_score,
    compute_with_validation,
    estimate_hour_from_traits,
)

router = APIRouter()
log = logging.getLogger("chart")


def _sanitize_numpy(obj):
    """递归把 numpy 标量/数组/容器转成原生 Python, 避免 FastAPI jsonable_encoder 500.

    FastAPI 的 jsonable_encoder 不识别 np.bool_ (尝试 iter/dict 都失败),
    会抛 "'numpy.bool_' object is not iterable" / "vars() argument must have __dict__ attribute".
    在出口处做一次清洗最稳妥 (一次性覆盖所有 engine).
    """
    try:
        import numpy as np
    except ImportError:
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_numpy(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return v if v == v else None  # NaN/Inf -> None
    if isinstance(obj, np.ndarray):
        return [_sanitize_numpy(v) for v in obj.tolist()]
    return obj


class BirthModel(BaseModel):
    year: int = Field(..., ge=1500, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: Literal["male", "female", "unspecified"] = "unspecified"
    calendar: Literal["gregorian", "lunar"] = "gregorian"
    lat: float | None = None
    lng: float | None = None
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
    "tarot_system",
    "qian_type",
    "qian_number",
    "tosses",
    "period",
    "sitting",
    "construction_year",
    "method_inputs",
    "father_zodiac",
    "mother_zodiac",
    "name",
    "full_name",
    # 姓名学 (numerology 三才五格)
    "surname",
    "given_name",
    "system",
    # 奇门 / 玄空 / 六爻 / 梅花等引擎的实际参数
    "pan_type",
    "pan_style",
    "zhi_run_method",
    "house_system",
    "facing_deg",
    "lineage",
    "question_keywords",
    "top_n",
    "n1",
    "n2",
    "n3",
    "lines",
    "query",
    "zi_hour",
    "client_seed",
    # Multi-method orchestration (accepted but not used by single-method compute)
    "methods",
    "modeByMethod",
}


# 模式级必需参数: 白名单式登记, 避免把 meta 里「推荐输入」当成硬性要求
_MODE_REQUIRED: dict[tuple[str, str], list[str]] = {
    ("numerology", "destiny"): ["name"],
    ("numerology", "soul_urge"): ["name"],
}


# 元数据里的 mode 名不一定等于引擎参数值 (如 meihua 的 time_qigua ↔ 引擎的 time)
_MODE_TRANSLATE: dict[tuple[str, str], str] = {
    ("meihua", "time_qigua"): "time",
    ("meihua", "number_qigua"): "number",
    ("meihua", "external_omen"): "external_omen",
}


def _engine_kwargs(engine, options: dict, method: str = "") -> dict:
    """按引擎签名挑出它能接受的具名参数。

    只传签名里显式声明的位置/关键字参数, 不吃 **kwargs 的引擎不会被塞垃圾。
    """
    try:
        params = inspect.signature(engine).parameters
    except (TypeError, ValueError):  # pragma: no cover - 内建/C 函数
        return {}
    kwargs = {}
    for key, value in options.items():
        p = params.get(key)
        if p is None or p.kind is inspect.Parameter.VAR_KEYWORD:
            continue
        if value is not None:
            kwargs[key] = value
    if "mode" in kwargs and (method, kwargs["mode"]) in _MODE_TRANSLATE:
        kwargs["mode"] = _MODE_TRANSLATE[(method, kwargs["mode"])]
    return kwargs


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

    # 只有「不给就一定算错」的输入才拦 (question 之类是可选的, 不能一刀切)
    required = _MODE_REQUIRED.get((body.method, mode)) or []
    missing = [k for k in required if not options.get(k) and not getattr(body.birth, k, None)]
    if missing:
        raise HTTPException(422, f"mode {mode} 需要参数: {', '.join(missing)}")

    # Validate spread if provided and method supports spreads
    if "spread" in options:
        spread = options["spread"]
        # Lenormand and Tarot are the two methods with custom spread systems
        if body.method in ("tarot", "lenormand"):
            try:
                from divination.engines.tarot import ALIASES as TAROT_ALIASES, SPREADS as TAROT_SPREADS
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

    # 引擎真正接受的具名参数 (options 以前只 setattr 到 Birth 上, 名字/牌阵/掷币数
    # 等参数被静默丢弃 —— 前端选了牌阵也永远出同一个默认牌阵)
    engine_kwargs = _engine_kwargs(_ENGINES[body.method], options, body.method)

    t0 = time.perf_counter()
    try:
        result = _ENGINES[body.method](birth, **engine_kwargs)
    except Exception as e:
        log.exception("compute failed: %s/%s", body.method, e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    dt_ms = int((time.perf_counter() - t0) * 1000)

    return _sanitize_numpy({
        "method": result.method,
        "school": result.school,
        "engine": result.engine,
        "normalized": result.normalized,
        "raw": result.raw,
        "elapsed_ms": dt_ms,
    })


# ── Advanced Multi-Method Endpoints ──────────────────────────────────────────

class MultiComputeRequest(BaseModel):
    methods: list = Field(..., min_length=1, max_length=5)
    birth: BirthModel
    subject: str = "self_life"
    do_validate: bool = True


class HourCalibrateRequest(BaseModel):
    birth: BirthModel
    known_traits: list | None = None
    known_career: str | None = None
    known_events: list | None = None


class TraitEstimateRequest(BaseModel):
    traits: list = Field(..., min_length=1)


class CompatibilityRequest(BaseModel):
    chart1_birth: BirthModel
    chart2_birth: BirthModel
    method: str = "bazi_v2"
    methods: list | None = None  # multi-method: ["bazi_v2", "western"]
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
        serialized_charts[m] = _sanitize_numpy({
            "method": chart.method,
            "school": chart.school,
            "engine": chart.engine,
            "normalized": chart.normalized,
            "raw": chart.raw,
        })

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
    """Calibrate uncertain birth hour by scoring all 12 two-hour periods.

    使用 engines/hour_calibrator 真实现：真太阳时 + 已知特质/职业/人生大事
    多维打分（trait 20% / career 15% / 用神 25% / 大运流年事件 25% / 结构 10%）。
    known_traits/known_career/known_events 真实参与打分排序。
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
        result = calibrate_hour_engine(
            birth, body.known_traits, body.known_career, body.known_events,
        )
    except Exception as e:
        log.exception("hour calibration failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    dt_ms = int((time.perf_counter() - t0) * 1000)

    def _candidate_payload(c) -> dict:
        raw = (c.chart or {}).get("raw", {}) or {}
        pattern = raw.get("pattern")
        return {
            "branch": c.branch,
            "hour": c.hour,
            "label": f"{c.hour:02d}:00-{(c.hour + 2) % 24:02d}:00",
            "traits": c.traits,
            "score": round(c.score, 1),
            "score_breakdown": c.score_breakdown,
            "match_details": c.match_details,
            "yong_shen_match": round(c.yong_shen_match, 2),
            "event_match_count": c.event_match_count,
            "chart_summary": {
                "pillars": raw.get("pillars"),
                "day_master": raw.get("day_master"),
                "strength_score": raw.get("strength_score"),
                "pattern": pattern.get("pattern") if isinstance(pattern, dict) else None,
            },
        }

    candidates = result.candidates or []
    payload = {
        "candidates": [_candidate_payload(c) for c in candidates],
        "best": _candidate_payload(candidates[0]) if candidates else None,
        "best_hour": result.best_hour,
        "best_confidence": result.best_confidence,
        "top_3": result.top_3,
        "analysis": result.analysis,
        "recommendation": result.recommendation,
        "true_solar_time_info": result.true_solar_time_info,
        "elapsed_ms": dt_ms,
    }
    return _sanitize_numpy(payload)


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


def _synastry_single_result(birth1: Birth, birth2: Birth) -> dict:
    """西方合盘：走真实 synastry 引擎（跨盘相位/宫位叠加/组合中点盘）。"""
    from divination.engines import synastry
    raw = synastry.compute(birth1, birth2).raw or {}
    scoring = raw.get("scoring", {}) or {}
    interp = raw.get("interpretation", {}) or {}
    return {
        "compatibility_score": scoring.get("compatibility_score"),
        "total_score": scoring.get("compatibility_score"),
        "level": interp.get("level"),
        "interpretation": interp.get("description"),
        "breakdown": scoring.get("breakdown", {}),
        "overlays": raw.get("overlays"),
        "cross_aspects": raw.get("cross_aspects"),
        "composite_chart": raw.get("composite_chart"),
        "scoring": scoring,
        "advice": [],
    }


def _compatibility_single(method: str, birth1: Birth, birth2: Birth) -> dict:
    if method == "western":
        return _synastry_single_result(birth1, birth2)
    chart1 = _ENGINES[method](birth1)
    chart2 = _ENGINES[method](birth2)
    return compute_compatibility_score({"raw": chart1.raw}, {"raw": chart2.raw}, method)


def _compatibility_multi(methods: list, birth1: Birth, birth2: Birth) -> dict:
    """多法合盘加权集成：只对产出真实评分的方法加权，跳过原因显式标注。"""
    weights = {"bazi": 1.2, "bazi_v2": 1.2, "ziwei": 1.0,
               "western": 0.9, "western_synastry": 0.9, "vedic": 0.9, "numerology": 0.6}
    results: dict = {}
    method_scores: list = []
    for m in methods:
        if m not in _ENGINES:
            method_scores.append({"method": m, "score": None,
                                  "weight": weights.get(m, 0.7), "skipped": "unsupported_method"})
            continue
        try:
            if m == "western":
                single = _synastry_single_result(birth1, birth2)
                display = "western_synastry"
                results[display] = single
            else:
                single = _compatibility_single(m, birth1, birth2)
                display = "bazi" if m.startswith("bazi") else m
                if single.get("compatibility_score") is None:
                    method_scores.append({"method": display, "score": None,
                                          "weight": weights.get(m, 0.7), "skipped": "insufficient_data"})
                    continue
                results[m] = single
            method_scores.append({"method": display, "score": single.get("compatibility_score"),
                                  "weight": weights.get(m, 0.7)})
        except Exception as e:
            log.warning("compatibility method %s failed: %s", m, e)
            method_scores.append({"method": m, "score": None,
                                  "weight": weights.get(m, 0.7), "skipped": "compute_failed"})

    scored = [ms for ms in method_scores if isinstance(ms.get("score"), (int, float))]
    if scored:
        w_sum = sum(ms["weight"] for ms in scored)
        ensemble = sum(ms["score"] * ms["weight"] for ms in scored) / w_sum if w_sum else None
    else:
        ensemble = None
    return {
        "ensemble_score": round(ensemble) if ensemble is not None else None,
        "method_scores": method_scores,
        "results": results,
        "ensemble_basis": (
            f"{len(scored)}/{len(methods)} 法真实评分加权"
            if scored else "无方法产出真实评分"
        ),
    }


@router.post("/compatibility")
def compatibility_endpoint(body: CompatibilityRequest):
    """Compute relationship compatibility between two birth charts.

    - method=bazi_v2：日主五行真实匹配打分（数据不足时显式 insufficient_data）
    - method=western：真实 synastry 引擎（跨盘相位/宫位叠加/组合盘）
    - methods=[...]：多法加权集成，results.western_synastry 携带合盘细节
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
    try:
        if body.methods and len(body.methods) >= 2:
            result = _compatibility_multi(body.methods, birth1, birth2)
        else:
            method = body.method
            if method not in _ENGINES:
                raise HTTPException(422, f"unsupported method: {method}")
            result = _compatibility_single(method, birth1, birth2)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("compatibility compute failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}") from e

    dt_ms = int((time.perf_counter() - t0) * 1000)
    result["elapsed_ms"] = dt_ms
    return _sanitize_numpy(result)


# ── 紫微 SVG 可视化 (GET /api/ziwei/svg) ──────────────────────────────
# 后端 divination/viz/ziwei_svg.py 的直出通道: 同参数同盘 → 可缓存、可 <img> 直引,
# 也天然规避了 inline SVG 注入的 XSS 面 (浏览器以 image 语义解析, 不执行脚本)。

_ZIWEI_SVG_STYLES = ("traditional", "wheel", "grid", "star_map")
_ZIWEI_SVG_SCOPES = ("natal", "decadal", "yearly", "monthly", "xiaoxian")


def _ziwei_svg_scope_title(scope: str) -> str:
    return {
        "natal": "紫微斗数 · 本命盘",
        "decadal": "紫微斗数 · 大限盘",
        "yearly": "紫微斗数 · 流年盘",
        "monthly": "紫微斗数 · 流月盘",
        "xiaoxian": "紫微斗数 · 小限盘",
    }.get(scope, "紫微斗数 · 本命盘")


@router.get("/ziwei/svg")
def ziwei_svg_endpoint(
    year: int = Query(..., ge=1500, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(12, ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    gender: str = Query("male", pattern="^(male|female|unspecified)$"),
    style: str = Query("traditional"),
    scope: str = Query("natal"),
    size: int = Query(720, ge=320, le=1080),
    age: int = Query(0, ge=0, le=130, description="虚岁; 0 = 按当前年自动推算 (仅 xiaoxian 用)"),
):
    """紫微盘 SVG 直出.

    style: traditional(经典方盘)/wheel(现代轮盘)/grid(宫位网格)/star_map(星曜地图)
    scope: natal(本命)/decadal(大限)/yearly(流年)/monthly(流月)/xiaoxian(小限)
           非 natal scope 固定用方盘布局 (带对应宫位高亮), style 参数忽略.
    """
    if "ziwei" not in _ENGINES:
        raise HTTPException(503, "ziwei engine unavailable")
    if style not in _ZIWEI_SVG_STYLES:
        raise HTTPException(422, f"unsupported style: {style} (valid: {list(_ZIWEI_SVG_STYLES)})")
    if scope not in _ZIWEI_SVG_SCOPES:
        raise HTTPException(422, f"unsupported scope: {scope} (valid: {list(_ZIWEI_SVG_SCOPES)})")
    try:
        from divination.viz import ziwei_svg
    except ImportError as e:  # pragma: no cover
        raise HTTPException(503, f"svg renderer unavailable: {e}")

    birth = Birth(
        year=year, month=month, day=day, hour=hour, minute=minute,
        gender=gender, calendar="gregorian", tz="Asia/Shanghai",
    )
    try:
        result = _ENGINES["ziwei"](birth)
    except Exception as e:
        log.exception("ziwei svg compute failed: %s", e)
        raise HTTPException(500, f"{type(e).__name__}: {e}")

    raw = _sanitize_numpy(getattr(result, "raw", None) or {})
    palaces = raw.get("palaces") or []
    if not palaces:
        raise HTTPException(422, "no palace data: check birth parameters")

    common = dict(
        soul=str(raw.get("soul") or ""),
        body=str(raw.get("body") or ""),
        five_elements=str(raw.get("five_elements") or ""),
        size=size,
    )
    gan_zhi = str(raw.get("gan_zhi") or "")

    if scope == "natal" and style != "traditional":
        # 盘型渲染器签名: (palaces, *, title, size) — 无 soul/body 参数
        render = {
            "wheel": ziwei_svg.render_modern_wheel,
            "grid": ziwei_svg.render_palace_grid,
            "star_map": ziwei_svg.render_star_map,
        }[style]
        svg = render(palaces, title=_ziwei_svg_scope_title("natal"), size=size)
    elif scope == "xiaoxian":
        # 虚岁: 未显式传 age 时按当前年推算 (出生当年 = 虚岁 1)
        if age <= 0:
            from datetime import date
            age = max(1, date.today().year - year + 1)
        # 出生年支: (year - 4) % 12 → 子..亥 (1984 = 甲子 → 子)
        birth_zhi = "子丑寅卯辰巳午未申酉戌亥"[(year - 4) % 12]
        svg = ziwei_svg.render_xiaoxian_chart(
            palaces, title=_ziwei_svg_scope_title(scope), gan_zhi=gan_zhi,
            birth_zhi=birth_zhi, age=age, gender=gender, **common,
        )
    else:
        render = {
            "natal": ziwei_svg.render_natal_chart,
            "decadal": ziwei_svg.render_decadal_chart,
            "yearly": ziwei_svg.render_yearly_chart,
            "monthly": ziwei_svg.render_monthly_chart,
        }[scope]
        svg = render(palaces, title=_ziwei_svg_scope_title(scope), gan_zhi=gan_zhi, **common)

    return Response(
        content=svg,
        media_type="image/svg+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )
