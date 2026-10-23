"""Cross-System Ensemble Validator — 多系统交叉验证引擎

Based on techniques from 剑桥图灵子's videos:
- BV1ubArzxEp4: Combined Bazi×Ziwei×Western for relationship (94k views)
- BV1MAVp62EbT: Competition-grade accuracy through multi-model ensemble
- BV1Wm1sB4Ex8: Solving hallucination through cross-validation

Core principle: When multiple divination systems independently agree on a
conclusion, confidence increases. When they disagree, it surfaces the need
for deeper analysis rather than fabricating false certainty.

Architecture:
  Feature Extraction → Agreement Scoring → Confidence-Weighted Ensemble
"""

from dataclasses import dataclass, field

from ..contracts import ChartResult

# ── Five Element Constants ──────────────────────────────────────────────────

WUXING = ("木", "火", "土", "金", "水")

# Element generation cycle: 木生火 火生土 土生金 金生水 水生木
GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
GENERATED_BY = {v: k for k, v in GENERATE.items()}

# Element restriction cycle: 木克土 土克水 水克火 火克金 金克木
RESTRICT = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
RESTRICTED_BY = {v: k for k, v in RESTRICT.items()}

# Element → body organ (for health cross-reference)
ELEMENT_ORGANS = {
    "木": ("肝", "胆"),
    "火": ("心", "小肠"),
    "土": ("脾", "胃"),
    "金": ("肺", "大肠"),
    "水": ("肾", "膀胱"),
}

# ── Domain Weights per System ──────────────────────────────────────────────
# How much weight each system carries for different life domains.
# Based on classical understanding: Bazi excels at life patterns/wealth,
# Ziwei excels at relationships/palaces, Western excels at psychology.

SYSTEM_DOMAIN_WEIGHTS = {
    "bazi_v2": {
        "self_life": 0.85, "career": 0.80, "wealth": 0.85,
        "relationship": 0.60, "health": 0.65, "annual_luck": 0.80,
    },
    "bazi": {
        "self_life": 0.75, "career": 0.70, "wealth": 0.75,
        "relationship": 0.50, "health": 0.55, "annual_luck": 0.70,
    },
    "ziwei": {
        "self_life": 0.80, "career": 0.75, "wealth": 0.70,
        "relationship": 0.80, "health": 0.75, "annual_luck": 0.75,
    },
    "western": {
        "self_life": 0.75, "career": 0.60, "wealth": 0.40,
        "relationship": 0.80, "health": 0.55, "annual_luck": 0.50,
    },
    "vedic": {
        "self_life": 0.70, "career": 0.55, "wealth": 0.45,
        "relationship": 0.65, "health": 0.60, "annual_luck": 0.55,
    },
    "qimen": {
        "decision": 0.90, "wealth": 0.75, "career": 0.70,
        "lost_item": 0.85,
    },
    "liuyao": {
        "decision": 0.85, "wealth": 0.75, "career": 0.70,
        "relationship": 0.70,
    },
    "numerology": {
        "self_life": 0.55,
    },
}


def _safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dicts."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, {})
    return d if d != {} else default


# 引擎内部用英文五行键 (wood/fire/earth/metal/water), 交叉验证用中文五行。
ELEMENT_EN2ZH = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}

# 天干 → 五行 (日主取五行用)
_GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}


def _as_zh_elements(elements) -> dict:
    """把 elements 字典的键统一成中文五行, 丢掉无法映射的键。

    bazi_v2 的 elements_total / elements_visible 是英文字典,
    bazi(v1) 与部分归一化结果已经是中文键; 两种都收。
    """
    if not isinstance(elements, dict):
        return {}
    out: dict = {}
    for key, value in elements.items():
        if not isinstance(value, (int, float)):
            continue
        zh = ELEMENT_EN2ZH.get(str(key).lower(), key if key in WUXING else None)
        if zh:
            out[zh] = out.get(zh, 0.0) + float(value)
    return out


def _pillar_text(pillar) -> str:
    """pillars 的每一柱可能是 "辛亥" 字符串, 也可能是 {ganzhi/stem/branch...} 字典。"""
    if isinstance(pillar, str):
        return pillar
    if isinstance(pillar, dict):
        for key in ("ganzhi", "pillar", "text", "value"):
            value = pillar.get(key)
            if isinstance(value, str) and len(value) >= 2:
                return value
        gan = pillar.get("gan") or pillar.get("heavenly_stem") or ""
        zhi = pillar.get("zhi") or pillar.get("earthly_branch") or ""
        if gan and zhi:
            return f"{gan}{zhi}"
    return ""


def _strip_suffix(name: str, *suffixes: str) -> str:
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


# ── Feature Extraction ──────────────────────────────────────────────────────

def extract_bazi_features(raw: dict) -> dict:
    """Extract standardized features from Bazi/Bazi_v2 chart.

    同时兼容两代引擎的 raw 结构:
      - v1 只有 pillars/day_master/horoscope, 没有 elements/pattern;
      - v2 的五行是 elements_total / elements_visible (英文键), 用神在
        yong_shen.primary_zh, 格局是 pattern.pattern 字符串。
    """
    feats = {}
    day_master = raw.get("day_master", "") or ""
    feats["day_master"] = day_master
    # day_master 可能只是天干 "辛", 也可能带五行 "辛金"
    feats["day_master_element"] = (
        _GAN_WUXING.get(day_master[:1], "")
        or next((c for c in day_master if c in WUXING), "")
    )

    elements = _as_zh_elements(
        raw.get("elements")
        or raw.get("elements_total")
        or raw.get("elements_visible")
        or {}
    )
    feats["dominant_element"] = max(elements, key=elements.get) if elements else ""
    feats["weak_element"] = min(elements, key=elements.get) if elements else ""
    feats["element_balance"] = elements

    strength = raw.get("strength_score")
    feats["strength_score"] = strength if isinstance(strength, (int, float)) else 50

    pattern = raw.get("pattern", {})
    if isinstance(pattern, str):
        feats["pattern"] = pattern
        feats["pattern_category"] = ""
    else:
        feats["pattern"] = pattern.get("pattern", "")
        feats["pattern_category"] = pattern.get("category", "")

    yong_shen = raw.get("yong_shen", {})
    primary_zh = yong_shen.get("primary_zh") if isinstance(yong_shen, dict) else None
    if isinstance(primary_zh, (list, tuple)):
        feats["yong_shen"] = "、".join(str(x) for x in primary_zh)
    elif isinstance(yong_shen, dict):
        feats["yong_shen"] = yong_shen.get("yong_shen", "")
    else:
        feats["yong_shen"] = str(yong_shen or "")
    feats["yong_shen_level"] = (
        yong_shen.get("level", "中等") if isinstance(yong_shen, dict) else "中等"
    )
    quality = raw.get("yong_shen_quality")
    feats["yong_shen_score"] = (
        quality.get("score", 50) if isinstance(quality, dict) else 50
    )

    shensha = raw.get("shensha", {})
    stars = shensha.get("stars", []) if isinstance(shensha, dict) else []
    if isinstance(stars, list):
        feats["benefic_stars"] = [s.get("star", "") for s in stars
                                  if isinstance(s, dict) and s.get("category") == "吉"]
        feats["malefic_stars"] = [s.get("star", "") for s in stars
                                  if isinstance(s, dict) and s.get("category") == "凶"]
    elif isinstance(stars, dict):
        feats["benefic_stars"] = [k for k, v in stars.items()
                                  if isinstance(v, dict) and v.get("category") == "吉"]
        feats["malefic_stars"] = [k for k, v in stars.items()
                                  if isinstance(v, dict) and v.get("category") == "凶"]
    else:
        feats["benefic_stars"] = []
        feats["malefic_stars"] = []
    summary = shensha.get("summary", {}) if isinstance(shensha, dict) else {}
    feats["notable_stars"] = summary.get("notable", []) if isinstance(summary, dict) else []

    flow = raw.get("element_flow", {})
    if isinstance(flow, dict):
        feats["flow_balance"] = flow.get("balance_score", 50)
        feats["flow_interpretation"] = flow.get("interpretation", "")
    else:
        feats["flow_balance"] = 50
        feats["flow_interpretation"] = ""

    # Career indicators
    feats["career_elements"] = _detect_dominant(elements, threshold=0.15)
    feats["wealth_elements"] = _detect_dominant(elements, threshold=0.15)

    # Relationship indicators: 日支即配偶宫
    pillars = raw.get("pillars", {})
    day_pillar = _pillar_text(pillars.get("day")) if isinstance(pillars, dict) else ""
    feats["spouse_palace"] = day_pillar[1] if len(day_pillar) >= 2 else ""
    feats["pillars_text"] = (
        {k: _pillar_text(v) for k, v in pillars.items()} if isinstance(pillars, dict) else {}
    )

    return feats


def extract_ziwei_features(raw: dict) -> dict:
    """Extract standardized features from Ziwei chart.

    紫微引擎的宫名是 "命宫/官禄/财帛/夫妻" (不带"宫"字后缀, 命宫除外),
    这里统一按去掉后缀的名字查表; 五行局在 five_elements (如 "土五局")。
    """
    feats = {}

    palaces = raw.get("palaces", [])
    palace_map = {}
    for p in palaces:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", ""))
        palace_map[name] = p
        palace_map.setdefault(_strip_suffix(name, "宫"), p)
        major = p.get("major_stars", []) or []
        minor = p.get("minor_stars", []) or []
        feats[f"palace_{name}_stars"] = list(major) + list(minor)

    def _palace(*names):
        for n in names:
            if n in palace_map:
                return palace_map[n]
        return {}

    def _major(p):
        stars = p.get("major_stars", []) if isinstance(p, dict) else []
        return list(stars or [])

    # Ming palace analysis
    ming = _palace("命宫", "命")
    feats["ming_stars"] = _major(ming)
    five_elements = raw.get("five_elements", "") or raw.get("five_elements_class", "")
    feats["ming_element"] = (
        next((c for c in str(five_elements) if c in WUXING), "")
        if five_elements else ""
    )

    # Career palace
    feats["career_stars"] = _major(_palace("官禄宫", "官禄"))

    # Wealth palace
    feats["wealth_stars"] = _major(_palace("财帛宫", "财帛"))

    # Spouse palace
    feats["spouse_stars"] = _major(_palace("夫妻宫", "夫妻"))

    # Four transformations (v2 raw: four_transformations / four_transformations_enriched)
    feats["sihua"] = (
        raw.get("sihua")
        or raw.get("four_transformations")
        or {}
    )

    # Body/Ming lord
    feats["soul"] = raw.get("soul", "")
    feats["body"] = raw.get("body", "")

    return feats


def extract_western_features(raw: dict) -> dict:
    """Extract standardized features from Western astrology chart.

    西方引擎的 planets 每项已带 element (风/火/土/水), sign 形如 "双子" (无"座"),
    aspects 的 aspect 是 "刑相/冲相/合相/拱相/六合相"。
    """
    feats = {}

    planets = raw.get("planets", {})
    if not isinstance(planets, dict):
        planets = {}
    feats["sun_sign"] = _safe_get(planets, "太阳", "sign", default="")
    feats["moon_sign"] = _safe_get(planets, "月亮", "sign", default="")
    ascendant = raw.get("ascendant")
    if isinstance(ascendant, dict):
        feats["ascendant"] = ascendant.get("sign", "")
    else:
        feats["ascendant"] = str(ascendant or "")

    # Element distribution in Western (fire/earth/air/water)
    sign_elements: dict = {}
    for planet, data in planets.items():
        if not isinstance(data, dict):
            continue
        element = data.get("element") or _western_sign_element(str(data.get("sign", "")))
        if not element:
            continue
        sign_elements[element] = sign_elements.get(element, 0.0) + _planet_weight(planet)

    feats["western_elements"] = sign_elements
    feats["dominant_western_element"] = (
        max(sign_elements, key=sign_elements.get) if sign_elements else ""
    )

    def _aspect_name(item) -> str:
        name = str(item.get("aspect", ""))
        return name[:-1] if name.endswith("相") else name

    aspects = raw.get("aspects", [])
    if not isinstance(aspects, list):
        aspects = []
    normalised = [
        {"a": a.get("a"), "b": a.get("b"), "aspect": _aspect_name(a),
         "orb": a.get("orb"), "angle": a.get("angle")}
        for a in aspects if isinstance(a, dict)
    ]
    # 中文占星术语: 冲=对分(180°)、刑=四分(90°)、三合=三分(120°)、六合=六分(60°)
    # 部分引擎输出带"相"后缀(已由 _aspect_name 去掉), 这里三套写法都认
    hard_names = {"冲", "对分", "刑", "四分"}
    soft_names = {"合", "拱", "三合", "三分", "六合", "六分", "半合"}
    feats["major_aspects"] = [
        a for a in normalised if a["aspect"] in (hard_names | soft_names)
    ]
    feats["hard_aspects"] = len([a for a in normalised if a["aspect"] in hard_names])
    feats["soft_aspects"] = len([a for a in normalised if a["aspect"] in soft_names])

    return feats


def _western_sign_element(sign: str) -> str:
    """Map Western zodiac sign to element (接受 "双子" 与 "双子座" 两种写法)."""
    sign = _strip_suffix(str(sign or ""), "座")
    fire = {"白羊", "狮子", "射手"}
    earth = {"金牛", "处女", "摩羯"}
    air = {"双子", "天秤", "水瓶"}
    water = {"巨蟹", "天蝎", "双鱼"}
    if sign in fire: return "火"
    if sign in earth: return "土"
    if sign in air: return "风"
    if sign in water: return "水"
    return ""


def _planet_weight(planet: str) -> float:
    """Weight for planet importance."""
    return {"太阳": 1.0, "月亮": 1.0, "水星": 0.5, "金星": 0.7,
            "火星": 0.7, "木星": 0.8, "土星": 0.8}.get(planet, 0.3)


def _detect_dominant(elements: dict, threshold: float = 0.15) -> list:
    """Find dominant elements above threshold ratio."""
    if not elements:
        return []
    total = sum(elements.values())
    if total == 0:
        return []
    return [k for k, v in elements.items() if v / total > threshold]


# ── Agreement Scoring ───────────────────────────────────────────────────────

@dataclass
class CrossCheck:
    """A single cross-system check result."""
    domain: str
    systems_checked: list
    agree: bool
    confidence: float        # 0-100
    detail: str
    evidence: dict = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """Complete cross-system ensemble output."""
    cross_checks: list  # list of CrossCheck
    overall_confidence: float  # 0-100
    agreement_matrix: dict  # system → system → agreement_score
    domains: dict  # domain → {agreement, confidence, details}
    recommendations: list
    raw_features: dict


def compute_ensemble(charts: list[ChartResult], subject: str = "self_life") -> EnsembleResult:
    """Run cross-system ensemble validation on multiple charts.

    Args:
        charts: List of ChartResult from different divination methods
        subject: The life domain being analyzed

    Returns:
        EnsembleResult with cross-checks and confidence scores
    """
    if len(charts) < 2:
        return EnsembleResult(
            cross_checks=[],
            overall_confidence=50.0,
            agreement_matrix={},
            domains={"note": "需要至少两种术数进行交叉验证"},
            recommendations=["建议使用两种以上术数进行合参"],
            raw_features={},
        )

    # Step 1: Extract standardized features from each system
    features = {}
    system_names = []
    for chart in charts:
        method = chart.method
        system_names.append(method)
        raw = chart.raw

        if method in ("bazi", "bazi_v2"):
            features[method] = extract_bazi_features(raw)
        elif method == "ziwei":
            features[method] = extract_ziwei_features(raw)
        elif method == "western":
            features[method] = extract_western_features(raw)
        elif method == "vedic":
            features[method] = extract_western_features(raw)  # Similar structure
        else:
            features[method] = {"note": f"{method} feature extraction not yet implemented"}

    # Step 2: Run domain-specific cross-checks
    cross_checks = []

    if "bazi_v2" in features or "bazi" in features:
        cross_checks.extend(_check_self_life(features, system_names))
        cross_checks.extend(_check_career(features, system_names))
        cross_checks.extend(_check_wealth(features, system_names))
        cross_checks.extend(_check_relationship(features, system_names))
        cross_checks.extend(_check_health(features, system_names))
        cross_checks.extend(_check_timing(features, system_names))

    if "ziwei" in features and "bazi_v2" in features:
        cross_checks.extend(_cross_check_bazi_ziwei(features))

    if "western" in features and "bazi_v2" in features:
        cross_checks.extend(_cross_check_bazi_western(features))

    # Step 3: Compute agreement matrix
    agreement_matrix = _compute_agreement_matrix(features, system_names)

    # Step 4: Compute overall confidence
    domain_results = {}
    for check in cross_checks:
        if check.domain not in domain_results:
            domain_results[check.domain] = {"checks": [], "avg_confidence": 0}
        domain_results[check.domain]["checks"].append(check)

    for domain, data in domain_results.items():
        checks = data["checks"]
        data["avg_confidence"] = sum(c.confidence for c in checks) / len(checks) if checks else 0
        data["agree_count"] = sum(1 for c in checks if c.agree)
        data["total_count"] = len(checks)
        data["agreement_ratio"] = data["agree_count"] / data["total_count"] if data["total_count"] else 0

    # Overall = weighted by domain weights
    overall = _compute_overall_confidence(cross_checks, system_names, subject)

    # Step 5: Generate recommendations
    recommendations = _generate_recommendations(cross_checks, overall, features)

    return EnsembleResult(
        cross_checks=cross_checks,
        overall_confidence=overall,
        agreement_matrix=agreement_matrix,
        domains=domain_results,
        recommendations=recommendations,
        raw_features=features,
    )


# ── Domain Checks ────────────────────────────────────────────────────────────

def _check_self_life(features: dict, systems: list) -> list:
    """Check self-life / personality pattern agreement."""
    checks = []

    # Element dominance agreement
    bazi_feat = features.get("bazi_v2") or features.get("bazi")
    ziwei_feat = features.get("ziwei")
    western_feat = features.get("western")

    if bazi_feat and ziwei_feat:
        bazi_dom = bazi_feat.get("dominant_element", "")
        ziwei_ming = ziwei_feat.get("ming_element", "")

        if bazi_dom and ziwei_ming:
            agree = bazi_dom == ziwei_ming or _elements_compatible(bazi_dom, ziwei_ming)
            conf = 75 if bazi_dom == ziwei_ming else 60 if agree else 40
            evidence = {"bazi_dominant": bazi_dom, "ziwei_ming_element": ziwei_ming}
            checks.append(CrossCheck(
                domain="self_life",
                systems_checked=["bazi_v2", "ziwei"],
                agree=agree,
                confidence=conf,
                detail=f"八字日主五行{bazi_dom}与紫微命宫五行{ziwei_ming}"
                        f"{'一致' if bazi_dom == ziwei_ming else '相生' if agree else '不一致'}",
                evidence=evidence,
            ))

    # Strength / life force agreement
    if bazi_feat and ziwei_feat:
        bazi_strength = bazi_feat.get("strength_score", 50)
        ming_stars = ziwei_feat.get("ming_stars", [])
        strong_stars = {"紫微", "天府", "太阳", "武曲", "七杀", "破军", "贪狼"}
        # Extract star name from dict if needed (ziwei stars are {name, mutagen?})
        _ming_star_names = [s.get("name", s) if isinstance(s, dict) else s for s in ming_stars]
        ziwei_strong = any(n in strong_stars for n in _ming_star_names)

        bazi_is_strong = bazi_strength > 55
        agree = bazi_is_strong == ziwei_strong
        conf = 65 if agree else 45
        checks.append(CrossCheck(
            domain="self_life",
            systems_checked=["bazi_v2", "ziwei"],
            agree=agree,
            confidence=conf,
            detail=f"八字身{'强' if bazi_is_strong else '弱'}({bazi_strength}分)与紫微命宫"
                    f"{'强势星曜' if ziwei_strong else '柔和星曜'}"
                    f"{'一致' if agree else '不一致'}",
        ))

    # Pattern → life theme
    if bazi_feat:
        pattern = bazi_feat.get("pattern", "")
        pattern_category = bazi_feat.get("pattern_category", "")
        checks.append(CrossCheck(
            domain="self_life",
            systems_checked=["bazi_v2"],
            agree=True,
            confidence=70,
            detail=f"格局「{pattern}」({pattern_category or '待定'}类)",
            evidence={"pattern": pattern},
        ))

    return checks


def _check_career(features: dict, systems: list) -> list:
    """Career domain cross-checks."""
    checks = []
    bazi_feat = features.get("bazi_v2") or features.get("bazi")
    ziwei_feat = features.get("ziwei")

    if not bazi_feat:
        return checks

    # 用神 → career direction
    yong_shen = bazi_feat.get("yong_shen", "")
    yong_score = bazi_feat.get("yong_shen_score", 50)

    career_stars_strong = False
    if ziwei_feat:
        ziwei_career = ziwei_feat.get("career_stars", [])
        career_stars = {"紫微", "天府", "天相", "太阳", "武曲", "七杀", "破军"}
        _career_star_names = [s.get("name", s) if isinstance(s, dict) else s for s in ziwei_career]
        career_stars_strong = any(n in career_stars for n in _career_star_names)

    # Cross-check career direction
    if ziwei_feat:
        ziwei_career = ziwei_feat.get("career_stars", [])
        checks.append(CrossCheck(
            domain="career",
            systems_checked=["bazi_v2", "ziwei"],
            agree=career_stars_strong and yong_score > 40,
            confidence=65,
            detail=f"用神{yong_shen}(质量{yong_score}分)与紫微官禄宫星曜"
                    f"{'强势' if career_stars_strong else '一般'}",
            evidence={"yong_shen": yong_shen, "career_stars": ziwei_career},
        ))

    # Career timing
    checks.append(CrossCheck(
        domain="career",
        systems_checked=["bazi_v2"],
        agree=True,
        confidence=60,
        detail=f"用神质量{yong_score}/100"
              f"{'，事业运较好' if yong_score > 60 else '，需待时运' if yong_score > 35 else '，建议保守发展'}",
    ))

    return checks


def _check_wealth(features: dict, systems: list) -> list:
    """Wealth domain cross-checks."""
    checks = []
    bazi_feat = features.get("bazi_v2") or features.get("bazi")

    if not bazi_feat:
        return checks

    elements = bazi_feat.get("element_balance", {})
    yong_shen = bazi_feat.get("yong_shen", "")

    # Wealth element check: 财星 = day master restricts
    day_master_el = bazi_feat.get("day_master_element", "")
    wealth_element = RESTRICT.get(day_master_el, "")

    wealth_score = elements.get(wealth_element, 0) / sum(elements.values()) * 100 if elements else 50

    checks.append(CrossCheck(
        domain="wealth",
        systems_checked=["bazi_v2"],
        agree=True,
        confidence=min(85, wealth_score + 20),
        detail=f"财星{wealth_element}占比{wealth_score:.0f}%"
              f"{'，财运较好' if wealth_score > 25 else '，财运中等' if wealth_score > 15 else '，财运需后天努力'}",
        evidence={"wealth_element": wealth_element, "wealth_ratio": wealth_score},
    ))

    return checks


def _check_relationship(features: dict, systems: list) -> list:
    """Relationship domain cross-checks."""
    checks = []
    bazi_feat = features.get("bazi_v2") or features.get("bazi")
    ziwei_feat = features.get("ziwei")

    if bazi_feat:
        # Check spouse palace
        spouse_palace = bazi_feat.get("spouse_palace", "")
        notable = bazi_feat.get("notable_stars", [])

        has_peach = any("桃花" in s or "红鸾" in s or "天喜" in s for s in notable)
        has_lonely = any("孤辰" in s or "寡宿" in s for s in notable)

        # Peach blossom indicator
        if has_peach:
            checks.append(CrossCheck(
                domain="relationship",
                systems_checked=["bazi_v2"],
                agree=True,
                confidence=70,
                detail="命带桃花/红鸾/天喜，异性缘较好，感情机会多",
                evidence={"peach_blossom": True},
            ))
        elif has_lonely:
            checks.append(CrossCheck(
                domain="relationship",
                systems_checked=["bazi_v2"],
                agree=True,
                confidence=65,
                detail="命带孤辰/寡宿，感情上偏独立，建议主动社交",
                evidence={"lonely_star": True},
            ))

    # Cross-check with Ziwei
    if bazi_feat and ziwei_feat:
        fuqi_stars = ziwei_feat.get("spouse_stars", [])
        _fuqi_star_names = [s.get("name", s) if isinstance(s, dict) else s for s in fuqi_stars]
        baike_taohua = any("桃花" in s or "红鸾" in s for s in bazi_feat.get("notable_stars", []))

        ziwei_good_relationship = any(s in _fuqi_star_names for s in
                                       ("天同", "太阴", "廉贞", "天相", "紫微"))
        ziwei_challenging = any(s in _fuqi_star_names for s in
                                 ("七杀", "破军", "贪狼", "巨门"))

        if baike_taohua and ziwei_good_relationship:
            checks.append(CrossCheck(
                domain="relationship",
                systems_checked=["bazi_v2", "ziwei"],
                agree=True,
                confidence=80,
                detail="八字与紫微一致显示感情运较好：命带桃花且夫妻宫吉星",
                evidence={"bazi_peach": True, "ziwei_good": True},
            ))

    return checks


def _organ_advice(element: str) -> str:
    """Get health advice string for weak element."""
    mapping = {
        "木": "肝胆",
        "火": "心脑血管",
        "土": "脾胃消化",
        "金": "呼吸系统",
        "水": "肾脏泌尿",
    }
    return mapping.get(element, "身体")


def _check_health(features: dict, systems: list) -> list:
    """Health domain cross-checks."""
    checks = []
    bazi_feat = features.get("bazi_v2") or features.get("bazi")

    if not bazi_feat:
        return checks

    elements = bazi_feat.get("element_balance", {})
    weak_el = bazi_feat.get("weak_element", "")

    if weak_el and weak_el in ELEMENT_ORGANS:
        organs = ELEMENT_ORGANS[weak_el]
        checks.append(CrossCheck(
            domain="health",
            systems_checked=["bazi_v2"],
            agree=True,
            confidence=60,
            detail=f"五行{weak_el}偏弱，对应{organs[0]}/{organs[1]}，"
                   + "建议注意" + _organ_advice(weak_el) + "方面的保养",
            evidence={"weak_element": weak_el, "organs": organs},
        ))

    return checks


def _check_timing(features: dict, systems: list) -> list:
    """Timing/luck cycle cross-checks."""
    checks = []
    bazi_feat = features.get("bazi_v2") or features.get("bazi")

    if not bazi_feat:
        return checks

    flow_score = bazi_feat.get("flow_balance", 50)
    yong_score = bazi_feat.get("yong_shen_score", 50)

    checks.append(CrossCheck(
        domain="timing",
        systems_checked=["bazi_v2"],
        agree=True,
        confidence=min(80, (flow_score + yong_score) / 2 + 10),
        detail=f"五行流转评分{flow_score}，用神质量{yong_score}。" +
               ("命局流通有情，运势较为顺畅" if flow_score > 60
                else "命局有阻滞，需待运助" if flow_score < 40
                else "命局中平，随运起伏"),
    ))

    return checks


def _cross_check_bazi_ziwei(features: dict) -> list:
    """Specialized cross-checks between Bazi and Ziwei."""
    checks = []
    bazi = features.get("bazi_v2") or features.get("bazi", {})
    ziwei = features.get("ziwei", {})

    # Ming lord vs day master
    soul = ziwei.get("soul", "")
    body = ziwei.get("body", "")
    day_master = bazi.get("day_master", "")

    if soul and day_master:
        checks.append(CrossCheck(
            domain="self_life",
            systems_checked=["bazi_v2", "ziwei"],
            agree=True,
            confidence=70,
            detail=f"八字日主{day_master}，紫微命主{soul}身主{body}，"
                   f"两套体系可相互印证命格特质",
            evidence={"day_master": day_master, "soul": soul, "body": body},
        ))

    return checks


def _cross_check_bazi_western(features: dict) -> list:
    """Specialized cross-checks between Bazi and Western astrology."""
    checks = []
    bazi = features.get("bazi_v2") or features.get("bazi", {})
    western = features.get("western", {})

    # Element mapping: Bazi Wu Xing → Western elements
    bazi_dom = bazi.get("dominant_element", "")
    west_dom = western.get("dominant_western_element", "")

    # Mapping between systems
    wuxing_to_western = {"木": "风", "火": "火", "土": "土", "金": "土", "水": "水"}

    if bazi_dom and west_dom:
        mapped = wuxing_to_western.get(bazi_dom, "")
        agree = mapped == west_dom
        checks.append(CrossCheck(
            domain="self_life",
            systems_checked=["bazi_v2", "western"],
            agree=agree,
            confidence=60 if agree else 40,
            detail=f"八字主导五行{bazi_dom}(对应西方{mapped})与星盘主导元素{west_dom}"
                   f"{'一致' if agree else '不一致，需进一步分析'}",
            evidence={"bazi_dominant": bazi_dom, "western_dominant": west_dom, "mapped": mapped},
        ))

    # Sun sign vs day master
    sun_sign = western.get("sun_sign", "")
    if sun_sign and bazi.get("day_master"):
        checks.append(CrossCheck(
            domain="self_life",
            systems_checked=["bazi_v2", "western"],
            agree=True,
            confidence=65,
            detail=f"八字日主{bazi['day_master']}与西方太阳星座{sun_sign}，"
                   f"从不同维度揭示性格核心",
            evidence={"day_master": bazi["day_master"], "sun_sign": sun_sign},
        ))

    return checks


# ── Agreement Matrix ────────────────────────────────────────────────────────

def _compute_agreement_matrix(features: dict, systems: list) -> dict:
    """Compute pairwise agreement between all systems."""
    matrix = {}
    for i, s1 in enumerate(systems):
        matrix[s1] = {}
        for j, s2 in enumerate(systems):
            if i == j:
                matrix[s1][s2] = 1.0
            elif j < i:
                # Mirror
                matrix[s1][s2] = matrix[s2][s1]
            else:
                matrix[s1][s2] = _pairwise_agreement(features.get(s1, {}),
                                                      features.get(s2, {}),
                                                      s1, s2)
    return matrix


def _pairwise_agreement(f1: dict, f2: dict, method1: str, method2: str) -> float:
    """Compute agreement score between two systems (0-1)."""
    score = 0.0
    count = 0

    # Compare element-based features
    if "dominant_element" in f1 and "dominant_element" in f2:
        count += 1
        if f1["dominant_element"] == f2["dominant_element"]:
            score += 1.0
        elif _elements_compatible(f1["dominant_element"], f2["dominant_element"]):
            score += 0.5

    # Compare strength scores
    s1 = f1.get("strength_score", 50)
    s2 = f2.get("strength_score", 50) if "strength_score" in f2 else 50
    count += 1
    diff = abs(s1 - s2)
    score += max(0, 1 - diff / 100)

    return score / count if count > 0 else 0.5


def _elements_compatible(el1: str, el2: str) -> bool:
    """Check if two elements are in a compatible relationship."""
    return (GENERATE.get(el1) == el2 or GENERATE.get(el2) == el1)


# ── Overall Confidence ──────────────────────────────────────────────────────

def _compute_overall_confidence(checks: list, systems: list, subject: str) -> float:
    """Compute overall ensemble confidence weighted by domain relevance."""
    if not checks:
        return 50.0

    total_weight = 0
    weighted_conf = 0

    for check in checks:
        # Get domain weight for each system used
        system_weight = 0
        for sys in check.systems_checked:
            dw = SYSTEM_DOMAIN_WEIGHTS.get(sys, {})
            system_weight += dw.get(check.domain, 0.5)
        system_weight /= len(check.systems_checked) if check.systems_checked else 1

        weighted_conf += check.confidence * system_weight
        total_weight += system_weight

    if total_weight == 0:
        return 50.0

    # Log-scale to avoid extremes
    raw = weighted_conf / total_weight

    # Bonus for multi-system participation
    system_bonus = min(10, len(systems) * 3)
    raw = min(95, raw + system_bonus)

    return round(raw, 1)


# ── Recommendations ──────────────────────────────────────────────────────────

def _generate_recommendations(checks: list, overall: float, features: dict) -> list:
    """Generate actionable recommendations from ensemble results."""
    recs = []

    # Confidence-based
    if overall >= 75:
        recs.append({
            "level": "strong",
            "text": "多系统交叉验证一致，分析结果可信度较高",
            "action": "可基于此分析做重要决策参考",
        })
    elif overall >= 55:
        recs.append({
            "level": "moderate",
            "text": "多系统基本一致，部分领域存在分歧",
            "action": "重点关注多系统一致的部分，分歧领域建议单独深入",
        })
    else:
        recs.append({
            "level": "weak",
            "text": "多系统存在分歧，建议更深入的单系统分析",
            "action": "建议分别从各系统角度理解，并结合实际情况判断",
        })

    # System-specific
    bazi_feat = features.get("bazi_v2") or features.get("bazi", {})
    if bazi_feat:
        yong = bazi_feat.get("yong_shen", "")
        if yong:
            recs.append({
                "level": "info",
                "text": f"用神为{yong}，宜补{yong}五行",
                "action": f"可在生活中多接触与{yong}相关的事物（颜色、方位、行业等）",
            })

    # Disagreement handling
    disagree_count = sum(1 for c in checks if not c.agree)
    if disagree_count > 0:
        recs.append({
            "level": "note",
            "text": f"发现{disagree_count}处系统间不一致，这些领域建议谨慎解读",
            "action": "不一致不一定是错误，可能是不同维度视角，可结合现实情况判断",
        })

    return recs


# ── Public API ───────────────────────────────────────────────────────────────

def validate_charts(charts: list[ChartResult], subject: str = "self_life") -> dict:
    """Run cross-validation and return serializable results.

    This is the main public function. Call it with charts from multiple
    divination systems to get cross-validated results.

    Returns dict suitable for API response.
    输出 polarity 改用 DimensionPolarity 五档枚举(替代 0-100 连续 confidence_level),
    与聚合层 Sprint 0.1 的"档位制"红线保持一致。
    """
    from ..aggregation.schema import DimensionPolarity
    ensemble = compute_ensemble(charts, subject)

    # 五档极性映射(从内部 0-100 overall_confidence 派生)
    oc = ensemble.overall_confidence
    if oc >= 75:
        polarity = DimensionPolarity.STRONG_SUPPORT.value
    elif oc >= 60:
        polarity = DimensionPolarity.WEAK_SUPPORT.value
    elif oc >= 40:
        polarity = DimensionPolarity.NEUTRAL.value
    elif oc >= 25:
        polarity = DimensionPolarity.WEAK_WARN.value
    else:
        polarity = DimensionPolarity.STRONG_WARN.value

    return {
        "method": "cross_validator",
        "systems_checked": len(charts),
        "dimension_polarity": polarity,
        "agreement_ratio": (
            sum(1 for c in ensemble.cross_checks if c.agree) /
            max(1, len(ensemble.cross_checks))
        ),
        "cross_checks": [
            {
                "domain": c.domain,
                "systems": c.systems_checked,
                "agree": c.agree,
                "confidence": c.confidence,
                "detail": c.detail,
            }
            for c in ensemble.cross_checks
        ],
        "domains": {
            d: {
                "avg_confidence": v["avg_confidence"],
                "agreement_ratio": v.get("agreement_ratio", 0),
                "checks_count": v.get("total_count", 0),
            }
            for d, v in ensemble.domains.items()
        },
        "recommendations": ensemble.recommendations,
    }
