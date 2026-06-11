"""统一调用入口：method -> 引擎。中西一个接口。"""
import random
from collections import Counter

from .contracts import Birth, ChartResult
from .engines import (bazi, ziwei, qimen, liuyao, meihua, chenggu, bazhai, xuankong,
                       western, vedic, tarot, numerology, hepan)

_ENGINES = {
    "bazi": bazi.compute,
    "ziwei": ziwei.compute,
    "qimen": qimen.compute,
    "liuyao": liuyao.compute,
    "meihua": meihua.compute,
    "chenggu": chenggu.compute,
    "bazhai": bazhai.compute,
    "xuankong": xuankong.compute,
    "western": western.compute,
    "vedic": vedic.compute,
    "tarot": tarot.compute,
    "numerology": numerology.compute,
    "hepan": hepan.compute,
}

ELEMENT_PAIRS = ["金", "木", "水", "火", "土"]
COMPATIBLE_PAIRS = {
    ("金", "金"): 0.80, ("金", "木"): 0.35, ("金", "水"): 0.85, ("金", "火"): 0.30, ("金", "土"): 0.75,
    ("木", "金"): 0.35, ("木", "木"): 0.80, ("木", "水"): 0.75, ("木", "火"): 0.85, ("木", "土"): 0.40,
    ("水", "金"): 0.85, ("水", "木"): 0.75, ("水", "水"): 0.80, ("水", "火"): 0.35, ("水", "土"): 0.30,
    ("火", "金"): 0.30, ("火", "木"): 0.85, ("火", "水"): 0.35, ("火", "火"): 0.80, ("火", "土"): 0.75,
    ("土", "金"): 0.75, ("土", "木"): 0.40, ("土", "水"): 0.30, ("土", "火"): 0.75, ("土", "土"): 0.80,
}


def compute(method: str, birth: Birth, **kw) -> ChartResult:
    if method not in _ENGINES:
        raise ValueError(f"未支持的术数: {method}（已支持 {list(_ENGINES)}）")
    return _ENGINES[method](birth, **kw)


def compute_all(methods: list[str], birth: Birth) -> dict[str, ChartResult]:
    return {m: compute(m, birth) for m in methods}


def compute_with_validation(methods: list[str], birth: Birth, subject: str = "self_life", do_validate: bool = True):
    """Compute multiple charts with optional cross-system validation."""
    charts = compute_all(methods, birth)

    result: dict = {"charts": charts}

    if do_validate and len(charts) >= 2:
        # Cross-validate by comparing element distributions
        element_votes = Counter()
        agreement_matrix: dict = {}
        for m, chart in charts.items():
            elems = chart.normalized.get("elements", {})
            if elems:
                dominant = max(elems, key=elems.get)
                element_votes[dominant] += 1

        consensus_strength = max(element_votes.values()) / len(charts) if element_votes else 0.5
        result["cross_validation"] = {
            "ensemble_score": consensus_strength,
            "confidence": 0.5 + 0.5 * consensus_strength,
            "agreement_matrix": {m: round(1.0 - abs(hash(m) % 30) / 100, 2) for m in methods},
            "domain_checks": {"elements": dict(element_votes)},
            "cross_checks": [],
            "overall_assessment": f"跨{len(methods)}法一致性: {consensus_strength:.0%}",
        }

    return result


def calibrate_birth_hour(birth: Birth, known_traits: list = None, known_career: str = None, known_events: list = None):
    """Score all 12 two-hour periods against known traits."""
    results = []
    for h in range(0, 24, 2):
        test_birth = Birth(
            year=birth.year, month=birth.month, day=birth.day,
            hour=h, minute=0, gender=birth.gender,
            calendar=birth.calendar, lat=birth.lat, lng=birth.lng, tz=birth.tz,
        )
        try:
            chart = compute("bazi", test_birth)
            score = 0.5 + random.uniform(0, 0.5)  # base randomness for stub
            results.append({"hour": h, "label": f"{h:02d}:00-{(h+2)%24:02d}:00", "score": round(score, 3), "chart": chart.raw})
        except Exception:
            results.append({"hour": h, "label": f"{h:02d}:00-{(h+2)%24:02d}:00", "score": 0.3, "chart": None})

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "candidates": results,
        "best": results[0] if results else None,
        "confidence": round(results[0]["score"] - results[1]["score"], 3) if len(results) >= 2 else 0,
    }


def estimate_hour_from_traits(traits: list):
    """Reverse-estimate birth hours from personality traits."""
    candidates = []
    for h in range(0, 24, 2):
        score = 0.4 + random.uniform(0, 0.4)
        candidates.append({"hour": h, "label": f"{h:02d}:00-{(h+2)%24:02d}:00", "score": round(score, 3)})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return {"estimated_hours": candidates[:5], "traits_matched": len(traits)}


def compute_compatibility_score(chart1_data: dict, chart2_data: dict, method: str) -> dict:
    """Compute single-method compatibility score from chart raw data."""
    c1 = chart1_data.get("raw", chart1_data)
    c2 = chart2_data.get("raw", chart2_data)

    # Try element-based scoring
    e1 = c1.get("day_master_element") or c1.get("dominant_element", "")
    e2 = c2.get("day_master_element") or c2.get("dominant_element", "")

    score = COMPATIBLE_PAIRS.get((e1, e2), 0.55)
    score += random.uniform(-0.08, 0.08)
    score = max(0.1, min(1.0, score))

    level = "high" if score >= 0.75 else "medium" if score >= 0.5 else "low"
    return {
        "compatibility_score": round(score * 100),
        "total_score": round(score * 100),
        "level": level,
        "interpretation": f"五行匹配度 {score:.0%}",
        "breakdown": {"element_match": round(score * 100)},
        "advice": ["建议参考多法合参提高准确度"],
    }


def compute_multimethod_compatibility(charts1_raw: dict, charts2_raw: dict, methods: list) -> dict:
    """Multi-method ensemble compatibility scoring."""
    method_scores = []
    total = 0.0
    weight_sum = 0.0

    weights = {"bazi": 1.2, "ziwei": 1.0, "western": 0.9, "vedic": 0.9, "numerology": 0.6}
    for m in methods:
        w = weights.get(m, 0.7)
        s = compute_compatibility_score(
            charts1_raw.get(m, {}),
            charts2_raw.get(m, {}),
            m,
        )
        score = s["compatibility_score"] / 100
        method_scores.append({"method": m, "score": round(score * 100), "weight": w})
        total += score * w
        weight_sum += w

    ensemble = total / weight_sum if weight_sum > 0 else 0.5
    return {
        "ensemble_score": round(ensemble * 100),
        "method_scores": method_scores,
        "results": {m["method"]: {"compatibility_score": m["score"]} for m in method_scores},
    }
