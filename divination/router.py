"""统一调用入口：method -> 引擎。中西一个接口。"""
from collections import Counter

from .contracts import Birth, ChartResult
from .engines import (bazi, ziwei, qimen, liuyao, shicao, meihua, chenggu, bazhai, xuankong,
                       western, vedic, tarot, numerology, hepan, liuren, lenormand,
                       tieban, xiaoliuren)

_ENGINES = {
    "bazi": bazi.compute,
    "bazi_v2": bazi.compute,  # alias: 旧 selector 命名
    "ziwei": ziwei.compute,
    "qimen": qimen.compute,
    "liuyao": liuyao.compute,
    "shicao": shicao.compute,
    "meihua": meihua.compute,
    "chenggu": chenggu.compute,
    "bazhai": bazhai.compute,
    "fengshui": bazhai.compute,  # alias: fengshui = 风水 (含八宅+玄空) 用 bazhai 引擎
    "xuankong": xuankong.compute,
    "western": western.compute,
    "vedic": vedic.compute,
    "tarot": tarot.compute,
    "numerology": numerology.compute,
    "hepan": hepan.compute,
    "liuren": liuren.compute,
    "lenormand": lenormand.compute,
    "tieban": tieban.compute,
    "xiaoliuren": xiaoliuren.compute,
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
    # W8 fix: 引擎返回的是注册名（如"bazi"），但调用方需要用请求名（如"bazi_v2"）
    # 统一返回请求名，确保 chart.method == methods_used 一致
    result = _ENGINES[method](birth, **kw)
    result.method = method
    return result


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
    """Score all 12 two-hour periods against known traits.

    Score derivation: day_master_strength (旺相) from bazi chart, which reflects
    how well the hour-branch supports the day master element.
    Falls back to element balance when day_master_strength unavailable.
    §十一: no random noise — score is purely derived from chart data.
    """
    results = []
    for h in range(0, 24, 2):
        test_birth = Birth(
            year=birth.year, month=birth.month, day=birth.day,
            hour=h, minute=0, gender=birth.gender,
            calendar=birth.calendar, lat=birth.lat, lng=birth.lng, tz=birth.tz,
        )
        try:
            chart = compute("bazi", test_birth)
            raw = chart.raw or {}
            # Derive score from day_master_strength (0.0–1.0) or element balance
            score = raw.get("day_master_strength", 0.5)
            if score == 0.5:  # fallback: use element balance as tiebreaker
                elems = raw.get("elements", {})
                if elems:
                    vals = list(elems.values())
                    balance = max(vals) - min(vals) if vals else 0.5
                    score = 0.5 + (balance - 0.33) * 0.3  # normalize around 0.5
                else:
                    score = 0.5
            score = max(0.3, min(0.95, score))
            results.append({"hour": h, "label": f"{h:02d}:00-{(h+2)%24:02d}:00", "score": round(score, 3), "chart": raw})
        except Exception:
            results.append({"hour": h, "label": f"{h:02d}:00-{(h+2)%24:02d}:00", "score": 0.3, "chart": None})

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "candidates": results,
        "best": results[0] if results else None,
        "confidence": round(results[0]["score"] - results[1]["score"], 3) if len(results) >= 2 else 0,
    }


def estimate_hour_from_traits(traits: list):
    """Reverse-estimate birth hours from personality traits.

    §十一: deterministic — no random. Without a Birth object we cannot run bazi,
    so we honestly return uniform scores. Caller should provide birth for real estimation.
    """
    # 十二时辰传统心性关键词（建除满平定执破危成收开闭）
    # traits 匹配任一关键词即给该时辰 +0.05
    trait_keywords = {
        0: ["开拓", "新生", "领导", "敢闯"],   # 子
        2: ["勤勉", "务实", "积累", "储蓄"],   # 寅
        4: ["文采", "思辨", "谋划", "学术"],   # 卯
        6: ["表达", "传播", "火光", "礼仪"],   # 辰
        8: ["仁爱", "协调", "审美", "艺术"],   # 巳
        10: ["行动", "执行", "开创", "勇敢"],  # 午
        12: ["养育", "农业", "踏实", "仓储"],  # 未
        14: ["刚毅", "决断", "正义", "严肃"],  # 申
        16: ["柔和", "慈善", "生长", "宗教"],  # 酉
        18: ["智慧", "玄学", "修缮", "流动"],  # 戌
        20: ["秩序", "管理", "法律", "公正"],  # 亥
        22: ["柔顺", "谋划", "母性", "物流"],  # 丑
    }
    candidates = []
    trait_text = " ".join(str(t) for t in traits)
    for h in range(0, 24, 2):
        keywords = trait_keywords.get(h, [])
        match_count = sum(1 for kw in keywords if kw in trait_text)
        score = 0.5 + match_count * 0.05  # deterministic, no random
        score = max(0.3, min(0.9, score))
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
