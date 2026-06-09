"""统一调用入口:method -> 引擎。中西一个接口。"""
from .contracts import Birth, ChartResult
from .engines import (
    bazi, bazi_v2, ziwei, qimen, western, vedic,
    liuyao, meihua, chenggu, bazhai, xuankong, tarot, numerology,
    lenormand, liuren, tieban, synastry,
    cross_validator, hour_calibrator,
)
from .knowledge import (
    generate_fate_modification_plan,
    compute_peach_blossom_index,
    compute_relationship_timing,
    compute_compatibility,
)

_ENGINES = {
    "bazi":       bazi.compute,
    "bazi_v2":    bazi_v2.compute,
    "ziwei":      ziwei.compute,
    "qimen":      qimen.compute,
    "western":    western.compute,
    "vedic":      vedic.compute,
    "liuyao":     liuyao.compute,
    "meihua":     meihua.compute,
    "chenggu":    chenggu.compute,
    "bazhai":     bazhai.compute,
    "xuankong":   xuankong.compute,
    "tarot":      tarot.compute,
    "numerology": numerology.compute,
    "lenormand":  lenormand.compute,
    "liuren":     liuren.compute,
    "tieban":     tieban.compute,
    "synastry":   synastry.compute,  # requires two births, handled via compatibility endpoint
}

# ── Enhanced Compute (with cross-validation and v2 features) ────────────────

def compute(method: str, birth: Birth) -> ChartResult:
    """Compute a single chart."""
    if method not in _ENGINES:
        raise ValueError(f"未支持的术数: {method}(已支持 {list(_ENGINES)})")
    return _ENGINES[method](birth)


def compute_with_validation(methods: list, birth: Birth,
                            subject: str = "self_life",
                            validate: bool = True) -> dict:
    """Compute multiple charts with cross-system validation.

    This is the preferred entry point for multi-method analysis.
    Returns charts + cross-validation results for higher accuracy.

    Args:
        methods: List of method names (e.g. ["bazi_v2", "ziwei", "western"])
        birth: Birth data
        subject: Life domain (self_life, career, wealth, relationship, health)
        validate: Whether to run cross-validation

    Returns:
        {
            "charts": {method: ChartResult},
            "cross_validation": EnsembleResult if validate,
            "peach_blossom": PeachBlossomIndex if bazi_v2 in methods,
            "fate_modification": ModificationPlan if bazi_v2 in methods,
        }
    """
    # Compute all charts
    charts = {}
    for m in methods:
        if m in _ENGINES:
            charts[m] = _ENGINES[m](birth)

    result = {"charts": charts}

    # Cross-system validation
    if validate and len(charts) >= 2:
        chart_list = list(charts.values())
        result["cross_validation"] = cross_validator.validate_charts(chart_list, subject)

    # Enhanced features for bazi_v2
    if "bazi_v2" in charts:
        raw = charts["bazi_v2"].raw

        # Peach blossom index
        result["peach_blossom"] = compute_peach_blossom_index(raw)

        # Relationship timing
        result["relationship_timing"] = compute_relationship_timing(raw)

        # Fate modification plan
        result["fate_modification"] = generate_fate_modification_plan(charts["bazi_v2"])

    return result


def calibrate_birth_hour(birth: Birth,
                         known_traits: list = None,
                         known_career: str = None,
                         known_events: list = None) -> dict:
    """Calibrate uncertain birth hour.

    Generates all 12 two-hour period charts and scores them against
    known life facts to determine the most likely birth hour.
    """
    result = hour_calibrator.calibrate(
        birth, known_traits, known_career, known_events,
        compute_fn=bazi_v2.compute,
    )
    return {
        "best_hour": result.best_hour,
        "best_confidence": result.best_confidence,
        "top_3": result.top_3,
        "analysis": result.analysis,
        "recommendation": result.recommendation,
    }


def estimate_hour_from_traits(traits: list) -> dict:
    """Given personality traits, suggest most likely birth hours."""
    return hour_calibrator.estimate_from_traits(traits)


def compute_compatibility_score(chart1: dict, chart2: dict, method: str = "bazi_v2") -> dict:
    """Compute relationship compatibility between two charts.

    Args:
        chart1: First chart raw data
        chart2: Second chart raw data
        method: Method to use (bazi_v2, western, or multi)
    """
    if method in ("western", "synastry"):
        return synastry.compute_from_charts(chart1, chart2)
    return compute_compatibility(chart1, chart2)


def compute_multimethod_compatibility(charts1: dict, charts2: dict,
                                       methods: list = None) -> dict:
    """Compute compatibility using multiple methods and merge results.

    Args:
        charts1: {method: ChartResult} for person A
        charts2: {method: ChartResult} for person B
        methods: list of method names to use (default: all available)
    """
    if methods is None:
        methods = [m for m in charts1 if m in charts2]

    results = {}
    scores = []

    for m in methods:
        try:
            c1 = charts1[m]
            c2 = charts2[m]
            r1 = c1.raw if hasattr(c1, 'raw') else c1.get('raw', c1)
            r2 = c2.raw if hasattr(c2, 'raw') else c2.get('raw', c2)

            if m in ("western", "synastry"):
                result = synastry.compute_from_charts(r1, r2)
                results["western_synastry"] = result
                if result.get("scoring", {}).get("compatibility_score"):
                    scores.append({
                        "method": "western_synastry",
                        "score": result["scoring"]["compatibility_score"],
                        "weight": 0.4,
                    })
            elif m in ("bazi_v2", "bazi"):
                result = compute_compatibility(r1, r2)
                results["bazi"] = result
                if result.get("compatibility_score"):
                    scores.append({
                        "method": "bazi",
                        "score": result["compatibility_score"],
                        "weight": 0.6,
                    })
        except Exception:
            pass

    # Weighted ensemble score
    if scores:
        total_weight = sum(s["weight"] for s in scores)
        if total_weight > 0:
            ensemble = sum(s["score"] * s["weight"] for s in scores) / total_weight
        else:
            ensemble = sum(s["score"] for s in scores) / len(scores)
    else:
        ensemble = 50

    return {
        "ensemble_score": round(ensemble, 1),
        "method_scores": scores,
        "results": results,
    }


# ── Legacy API (backward compatible) ────────────────────────────────────────

def compute_all(methods, birth: Birth) -> dict:
    """Compute multiple charts (legacy API — use compute_with_validation)."""
    return {m: compute(m, birth) for m in methods}


def supported_methods() -> list:
    return list(_ENGINES)


def compute(method: str, birth: Birth) -> ChartResult:
    if method not in _ENGINES:
        raise ValueError(f"未支持的术数: {method}(已支持 {list(_ENGINES)})")
    return _ENGINES[method](birth)


def compute_all(methods, birth: Birth) -> dict:
    return {m: compute(m, birth) for m in methods}


def supported_methods() -> list:
    return list(_ENGINES)
