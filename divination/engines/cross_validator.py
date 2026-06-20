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


# ── Feature Extraction ──────────────────────────────────────────────────────

def extract_bazi_features(raw: dict) -> dict:
    """Extract standardized features from Bazi/Bazi_v2 chart."""
    feats = {}
    feats["day_master"] = raw.get("day_master", "")
    feats["day_master_element"] = raw.get("day_master", "")[0] if raw.get("day_master") else ""

    elements = raw.get("elements", {})
    feats["dominant_element"] = max(elements, key=elements.get) if elements else ""
    feats["weak_element"] = min(elements, key=elements.get) if elements else ""
    feats["element_balance"] = elements

    feats["strength_score"] = raw.get("strength_score", 50)

    pattern = raw.get("pattern", {})
    feats["pattern"] = pattern.get("pattern", "")
    feats["pattern_category"] = pattern.get("category", "")

    yong_shen = raw.get("yong_shen", {})
    feats["yong_shen"] = yong_shen.get("yong_shen", "")
    feats["yong_shen_level"] = yong_shen.get("level", "中等")
    feats["yong_shen_score"] = raw.get("yong_shen_quality", {}).get("score", 50)

    shensha = raw.get("shensha", {})
    stars = shensha.get("stars", [])
    if isinstance(stars, list):
        feats["benefic_stars"] = [s.get("star", "") for s in stars
                                  if isinstance(s, dict) and s.get("category") == "吉"]
        feats["malefic_stars"] = [s.get("star", "") for s in stars
                                  if isinstance(s, dict) and s.get("category") == "凶"]
    else:
        feats["benefic_stars"] = [k for k, v in stars.items()
                                  if isinstance(v, dict) and v.get("category") == "吉"]
        feats["malefic_stars"] = [k for k, v in stars.items()
                                  if isinstance(v, dict) and v.get("category") == "凶"]
    feats["notable_stars"] = shensha.get("summary", {}).get("notable", [])

    flow = raw.get("element_flow", {})
    feats["flow_balance"] = flow.get("balance_score", 50)
    feats["flow_interpretation"] = flow.get("interpretation", "")

    # Career indicators
    feats["career_elements"] = _detect_dominant(elements, threshold=0.15)
    feats["wealth_elements"] = _detect_dominant(elements, threshold=0.15)

    # Relationship indicators
    pillars = raw.get("pillars", {})
    feats["spouse_palace"] = pillars.get("day", "")[1] if pillars.get("day") else ""

    return feats


def extract_ziwei_features(raw: dict) -> dict:
    """Extract standardized features from Ziwei chart."""
    feats = {}

    palaces = raw.get("palaces", [])
    palace_map = {}
    for p in palaces:
        name = p.get("name", "")
        palace_map[name] = p
        major = p.get("major_stars", [])
        minor = p.get("minor_stars", [])
        feats[f"palace_{name}_stars"] = major + minor

    # Ming palace analysis
    ming = palace_map.get("命宫", {})
    feats["ming_stars"] = ming.get("major_stars", [])
    feats["ming_element"] = ming.get("element", "")

    # Career palace
    guanlu = palace_map.get("官禄宫", {})
    feats["career_stars"] = guanlu.get("major_stars", [])

    # Wealth palace
    caibo = palace_map.get("财帛宫", {})
    feats["wealth_stars"] = caibo.get("major_stars", [])

    # Spouse palace
    fuqi = palace_map.get("夫妻宫", {})
    feats["spouse_stars"] = fuqi.get("major_stars", [])

    # Four transformations
    feats["sihua"] = raw.get("sihua", {})

    # Body/Ming lord
    feats["soul"] = raw.get("soul", "")
    feats["body"] = raw.get("body", "")

    return feats


def extract_western_features(raw: dict) -> dict:
    """Extract standardized features from Western astrology chart."""
    feats = {}

    planets = raw.get("planets", {})
    feats["sun_sign"] = _safe_get(planets, "太阳", "sign", default="")
    feats["moon_sign"] = _safe_get(planets, "月亮", "sign", default="")
    feats["ascendant"] = raw.get("ascendant", {}).get("sign", "")

    # Element distribution in Western (fire/earth/air/water)
    sign_elements = {}
    for planet, data in planets.items():
        if isinstance(data, dict):
            sign = data.get("sign", "")
            element = _western_sign_element(sign)
            sign_elements[element] = sign_elements.get(element, 0) + _planet_weight(planet)

    feats["western_elements"] = sign_elements
    feats["dominant_western_element"] = max(sign_elements, key=sign_elements.get) if sign_elements else ""

    # Aspects
    aspects = raw.get("aspects", [])
    feats["major_aspects"] = [a for a in aspects
                              if isinstance(a, dict) and a.get("aspect") in
                              ("合", "冲", "刑", "拱", "六合")]
    feats["hard_aspects"] = len([a for a in aspects
                                  if isinstance(a, dict) and a.get("aspect") in ("冲", "刑")])
    feats["soft_aspects"] = len([a for a in aspects
                                  if isinstance(a, dict) and a.get("aspect") in ("合", "拱", "六合")])

    return feats


def _western_sign_element(sign: str) -> str:
    """Map Western zodiac sign to element."""
    fire = {"白羊座", "狮子座", "射手座"}
    earth = {"金牛座", "处女座", "摩羯座"}
    air = {"双子座", "天秤座", "水瓶座"}
    water = {"巨蟹座", "天蝎座", "双鱼座"}
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
