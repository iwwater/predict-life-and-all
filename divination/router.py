"""统一调用入口：method -> 引擎。中西一个接口。"""
from collections import Counter

from .contracts import Birth, ChartResult
from .engines import (
    bazhai,
    bazi,
    bazi_v2,
    chenggu,
    fengshui,
    hepan,
    lenormand,
    liuren,
    liuyao,
    meihua,
    numerology,
    qian,
    qimen,
    shicao,
    tarot,
    tieban,
    vedic,
    western,
    xiaoliuren,
    xuankong,
    ziwei,
)
from .wuxing import GAN_WX

_ENGINES = {
    "bazi": bazi.compute,
    "bazi_v2": bazi_v2.compute,
    "ziwei": ziwei.compute,
    "qimen": qimen.compute,
    "liuyao": liuyao.compute,
    "shicao": shicao.compute,
    "meihua": meihua.compute,
    "chenggu": chenggu.compute,
    "bazhai": bazhai.compute,
    "fengshui": fengshui.compute,
    "xuankong": xuankong.compute,
    "western": western.compute,
    "vedic": vedic.compute,
    "tarot": tarot.compute,
    "numerology": numerology.compute,
    "qian": qian.compute,
    "hepan": hepan.compute,
    "liuren": liuren.compute,
    "lenormand": lenormand.compute,
    "tieban": tieban.compute,
    "xiaoliuren": xiaoliuren.compute,
}

ELEMENT_PAIRS = ["金", "木", "水", "火", "土"]
COMPATIBLE_PAIRS = {
    ("金", "金"): 0.80,
    ("金", "木"): 0.35,
    ("金", "水"): 0.85,
    ("金", "火"): 0.30,
    ("金", "土"): 0.75,
    ("木", "金"): 0.35,
    ("木", "木"): 0.80,
    ("木", "水"): 0.75,
    ("木", "火"): 0.85,
    ("木", "土"): 0.40,
    ("水", "金"): 0.85,
    ("水", "木"): 0.75,
    ("水", "水"): 0.80,
    ("水", "火"): 0.35,
    ("水", "土"): 0.30,
    ("火", "金"): 0.30,
    ("火", "木"): 0.85,
    ("火", "水"): 0.35,
    ("火", "火"): 0.80,
    ("火", "土"): 0.75,
    ("土", "金"): 0.75,
    ("土", "木"): 0.40,
    ("土", "水"): 0.30,
    ("土", "火"): 0.75,
    ("土", "土"): 0.80,
}


from .cache import CacheKey, get_cache


def _birth_to_tuple(birth: Birth) -> tuple:
    """Birth → hashable tuple for cache key."""
    return (birth.year, birth.month, birth.day, birth.hour, birth.minute,
            birth.gender, round(birth.lat or 0, 1), round(birth.lng or 0, 1), birth.tz or "")


def compute(method: str, birth: Birth, **kw) -> ChartResult:
    if method not in _ENGINES:
        raise ValueError(f"未支持的术数: {method}（已支持 {list(_ENGINES)}）")
    cache = get_cache()
    ck = CacheKey(method=method, birth_tuple=_birth_to_tuple(birth), extra=tuple(sorted(kw.items())))
    key = ck.to_hash()
    cached = cache.get(key)
    if cached is not None:
        result = ChartResult(method=method,
                             school=cached.get("school", "east"),
                             engine=cached.get("engine", "self"),
                             raw=cached.get("raw", {}),
                             normalized=cached.get("normalized", {}))
        return result
    result = _ENGINES[method](birth, **kw)
    result.method = method
    cache.set(key, {"raw": getattr(result, "raw", {}),
                     "normalized": getattr(result, "normalized", {}),
                     "school": getattr(result, "school", "east"),
                     "engine": getattr(result, "engine", "self")}, ttl_seconds=3600)
    return result


def compute_all(methods: list[str], birth: Birth) -> dict[str, ChartResult]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import logging
    logger = logging.getLogger(__name__)
    results: dict[str, ChartResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(len(methods), 8))) as ex:
        futures = {ex.submit(compute, m, birth): m for m in methods}
        for fut in as_completed(futures):
            method = futures[fut]
            try:
                results[method] = fut.result()
            except Exception as e:
                logger.warning(f"compute_all: {method} failed: {e}")
    return {m: results.get(m) for m in methods}


# 各引擎 normalized.elements 键名不统一（bazi 系用英文 wood/metal，western 用中文但含
# 四元素"风"），统一映射到中文五行后再比较；无法诚实映射的键不参与共识。
_ELEMENT_EN2ZH = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
_WUXING = ("金", "木", "水", "火", "土")


def _dominant_wuxing(chart: ChartResult | None) -> str | None:
    """取单盘最旺五行（统一到中文五行；取不到或不可比返回 None）。

    bazi 系在 normalized.elements；紫微没有元素分布, 但 raw.five_elements 是五行局
    （"土五局"），这是一个真实可比的五行信号, 用它兜底。
    """
    if chart is None:
        return None
    els = chart.normalized.get("elements") or {}
    if isinstance(els, dict) and els:
        top = max(els, key=els.get)
        zh = _ELEMENT_EN2ZH.get(top, top)
        # 最旺项本身必须是五行之一才承认（西方四元素里的"风"不属于五行）
        if zh in _WUXING:
            return zh
    five_elements = chart.raw.get("five_elements")
    if isinstance(five_elements, str):
        zh = next((c for c in five_elements if c in _WUXING), None)
        if zh:
            return zh
    return None


def compute_with_validation(methods: list[str], birth: Birth, subject: str = "self_life", do_validate: bool = True):
    """Compute multiple charts with optional cross-system validation.

    ensemble_score 是 0-100 的"多系统支持度"(前端进度条与百分数直接消费):
      有 ≥2 个盘时取 cross_validator 的置信度加权总分;
      不足 2 个盘时不制造高分, 直接 0 并在 overall_assessment 里说明原因。
    agreement_matrix 仍是逐法的"最旺五行与其余可比法一致的比例", 没有可比数据的法记 None。
    引擎计算失败时该法 chart 为 None, 跳过而不是崩溃。
    """
    charts = compute_all(methods, birth)
    result: dict = {"charts": charts}

    if do_validate:
        dominant = {m: _dominant_wuxing(c) for m, c in charts.items()}
        comparable = {m: e for m, e in dominant.items() if e}
        element_votes = Counter(comparable.values())
        n = len(comparable)
        # 交叉共识需要 ≥2 个可比系统；单法或零法时不存在"交叉"，不给 1.0 这种
        # 自我印证的满分。
        consensus_strength = (max(element_votes.values()) / n) if n >= 2 else 0.0

        agreement_matrix: dict = {}
        for m in methods:
            if m not in comparable or n < 2:
                agreement_matrix[m] = None
            else:
                others = [e for mm, e in comparable.items() if mm != m]
                agreement_matrix[m] = round(
                    sum(1 for e in others if e == comparable[m]) / len(others), 2
                )

        ok = sum(1 for c in charts.values() if c is not None)
        valid_charts = [c for c in charts.values() if c is not None]

        ensemble_score = 0
        domain_checks: dict = {}
        cross_checks: list = []
        recommendations: list = []
        element_note = (
            f"跨{n}法五行共识 {consensus_strength:.0%}"
            if n >= 2
            else ("仅1法有可比五行数据" if n == 1 else "无可比较的五行数据")
        )
        assessment = f"{element_note}（{ok}/{len(methods)} 法计算成功）"

        # 真正的多系统交叉验证: 逐域(本命/事业/财富/感情/健康/时机)比对两两系统是否一致
        if len(valid_charts) >= 2:
            try:
                from .engines.cross_validator import compute_ensemble

                ensemble = compute_ensemble(valid_charts, subject)
            except Exception as exc:  # 交叉验证是增强项, 失败不能连累主流程
                logger.warning("compute_with_validation: 交叉验证失败: %s", exc)
                ensemble = None
            if ensemble is not None:
                ensemble_score = round(float(ensemble.overall_confidence))
                domain_checks = {
                    domain: {
                        "confidence": round(float(info.get("avg_confidence", 0)), 1),
                        "agreement": round(float(info.get("agreement_ratio", 0)), 2),
                        "checks": int(info.get("total_count", 0)),
                    }
                    for domain, info in (ensemble.domains or {}).items()
                }
                cross_checks = [
                    {
                        "domain": c.domain,
                        "systems": list(c.systems_checked),
                        "agree": bool(c.agree),
                        "confidence": round(float(c.confidence), 1),
                        "detail": c.detail,
                    }
                    for c in ensemble.cross_checks
                ]
                recommendations = list(ensemble.recommendations or [])
                agree_count = sum(1 for c in ensemble.cross_checks if c.agree)
                assessment = (
                    f"{len(valid_charts)} 系统交叉验证一致度 {ensemble_score}%"
                    f"（{len(cross_checks)} 项域级校验, {agree_count} 项结论一致）；"
                    f"五行层面: {element_note}（{ok}/{len(methods)} 法计算成功）"
                )

        result["cross_validation"] = {
            "ensemble_score": ensemble_score,
            "confidence": round(ensemble_score / 100, 2),
            "agreement_matrix": agreement_matrix,
            "domain_checks": domain_checks,
            "cross_checks": cross_checks,
            "recommendations": recommendations,
            "element_votes": dict(element_votes),
            "systems_checked": [c.method for c in valid_charts],
            "chart_count": ok,
            "overall_assessment": assessment,
        }

    return result


def estimate_hour_from_traits(traits: list):
    """Reverse-estimate likely birth hours from personality traits."""
    trait_keywords = {
        0: ["开拓", "新生", "领导", "敢闯"],
        2: ["勤勉", "务实", "积累", "储蓄"],
        4: ["文采", "思辨", "谋划", "学术"],
        6: ["表达", "传播", "火光", "礼仪"],
        8: ["仁爱", "协调", "审美", "艺术"],
        10: ["行动", "执行", "开创", "勇敢"],
        12: ["养育", "农业", "踏实", "仓储"],
        14: ["刚毅", "决断", "正义", "严肃"],
        16: ["柔和", "慈善", "生长", "宗教"],
        18: ["智慧", "玄学", "修缮", "流动"],
        20: ["秩序", "管理", "法律", "公正"],
        22: ["柔顺", "谋划", "母性", "物流"],
    }
    candidates = []
    trait_text = " ".join(str(t) for t in traits)
    for h in range(0, 24, 2):
        keywords = trait_keywords.get(h, [])
        match_count = sum(1 for kw in keywords if kw in trait_text)
        score = max(0.3, min(0.9, 0.5 + match_count * 0.05))
        candidates.append({"hour": h, "label": f"{h:02d}:00-{(h + 2) % 24:02d}:00", "score": round(score, 3)})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return {"estimated_hours": candidates[:5], "traits_matched": len(traits)}


def _extract_element(raw: dict) -> str:
    """从引擎 raw 中提取代表五行（真实数据；取不到返回空串，绝不默认编造）。

    优先级：日主天干 → 五行局（紫微）→ 显式元素键。
    """
    dm = raw.get("day_master", "")
    if isinstance(dm, str) and dm[:1] in GAN_WX:
        return GAN_WX[dm[:1]]
    cls = raw.get("five_elements_class", "")
    if isinstance(cls, str) and cls[:1] in _WUXING:
        return cls[:1]
    e = raw.get("day_master_element") or raw.get("dominant_element") or ""
    if isinstance(e, str) and e[:1] in _WUXING:
        return e[:1]
    return ""


def compute_compatibility_score(chart1_data: dict, chart2_data: dict, method: str) -> dict:
    """Compute single-method compatibility score from chart raw data.

    只在有真实五行数据时打分；数据不足时显式返回 insufficient_data，
    不再回退到常数 55。
    """
    c1 = chart1_data.get("raw", chart1_data)
    c2 = chart2_data.get("raw", chart2_data)
    e1 = _extract_element(c1)
    e2 = _extract_element(c2)

    if not e1 or not e2:
        return {
            "compatibility_score": None,
            "total_score": None,
            "level": "insufficient_data",
            "interpretation": f"{method} 盘面缺少可比较的五行数据，无法给出匹配度",
            "breakdown": {},
            "advice": ["建议改用八字（bazi_v2）或西方合盘（synastry）等有完整数据的方法"],
        }

    score = max(0.1, min(1.0, COMPATIBLE_PAIRS.get((e1, e2), 0.55)))
    level = "high" if score >= 0.75 else "medium" if score >= 0.5 else "low"
    return {
        "compatibility_score": round(score * 100),
        "total_score": round(score * 100),
        "level": level,
        "interpretation": f"日主五行 {e1}×{e2}，五行匹配度 {score:.0%}",
        "breakdown": {
            "elements": {
                "score": round(score * 100),
                "max": 100,
                "detail": f"日主五行 {e1} × {e2}",
            }
        },
        "advice": ["五行匹配只是合参维度之一，建议结合 synastry 跨盘相位综合看"],
    }
