"""西方占星合盘 (Synastry) 引擎。

功能:
- 比较两个西方占星星盘
- 宫位叠加: Person A 的行星落在 Person B 的宫位
- 跨盘相位: A 与 B 的行星间相位
- 组合中点盘: Composite Chart (中点法)
- 合盘评分: sun-moon, venus-mars, ascendant 连接等
"""
from datetime import date

from .. import astro_math as am
from ..contracts import Birth, ChartResult
from .western import _PLANETS

# ═══════════════════════════════════════════════════════════════
# 合盘专用: 行星组合权重
# ═══════════════════════════════════════════════════════════════
# 某些行星组合在 synastry 中特别重要
_SYNASTRY_PAIR_WEIGHTS = {
    # 核心关系指标 (high weight)
    ("太阳", "月亮"): 10, ("月亮", "太阳"): 10,
    ("太阳", "太阳"): 8,
    ("月亮", "月亮"): 8,
    ("金星", "火星"): 10, ("火星", "金星"): 10,
    ("太阳", "金星"): 7, ("金星", "太阳"): 7,
    ("月亮", "金星"): 6, ("金星", "月亮"): 6,
    # 沟通与心智
    ("水星", "水星"): 6,
    ("水星", "月亮"): 5, ("月亮", "水星"): 5,
    ("水星", "金星"): 5, ("金星", "水星"): 5,
    # 稳定性与承诺
    ("土星", "月亮"): 7, ("月亮", "土星"): 7,
    ("土星", "金星"): 8, ("金星", "土星"): 8,
    ("土星", "太阳"): 6, ("太阳", "土星"): 6,
    # 激情与深度
    ("火星", "月亮"): 6, ("月亮", "火星"): 6,
    ("太阳", "火星"): 5, ("火星", "太阳"): 5,
    ("冥王星", "金星"): 8, ("金星", "冥王星"): 8,
    ("冥王星", "月亮"): 7, ("月亮", "冥王星"): 7,
    # 梦想与灵性
    ("海王星", "金星"): 5, ("金星", "海王星"): 5,
    ("海王星", "月亮"): 5, ("月亮", "海王星"): 5,
    # 木星 — 扩张与幸运
    ("木星", "太阳"): 6, ("太阳", "木星"): 6,
    ("木星", "金星"): 7, ("金星", "木星"): 7,
    ("木星", "月亮"): 6, ("月亮", "木星"): 6,
    # 天王星 — 兴奋与不稳定
    ("天王星", "金星"): 5, ("金星", "天王星"): 5,
    ("天王星", "月亮"): 5, ("月亮", "天王星"): 5,
}

_DEFAULT_WEIGHT = 2


def _pair_weight(name_a: str, name_b: str) -> int:
    """获取一对行星在合盘中的重要性权重。"""
    return _SYNASTRY_PAIR_WEIGHTS.get((name_a, name_b), _DEFAULT_WEIGHT)


# ═══════════════════════════════════════════════════════════════
# House Overlay
# ═══════════════════════════════════════════════════════════════
_HOUSE_MEANINGS = {
    1: "自我、外表、第一印象",
    2: "价值、物质、安全感",
    3: "沟通、学习、日常交流",
    4: "家庭、根基、内心深处",
    5: "恋爱、创造、快乐",
    6: "工作、健康、日常服务",
    7: "伴侣关系、一对一合作",
    8: "深度连接、共享资源、转化",
    9: "理念、旅行、扩张",
    10: "事业、公众形象、目标",
    11: "友谊、社群、理想",
    12: "潜意识、灵性、隐秘",
}


def _compute_overlays(planets_a: dict, planets_b: dict,
                      asc_idx_a: int | None, asc_idx_b: int | None) -> dict:
    """计算 A 的行星落在 B 的宫位,以及 B 的行星落在 A 的宫位。"""
    a_in_b_houses = {}
    b_in_a_houses = {}

    if asc_idx_b is not None:
        for name, data in planets_a.items():
            lon = data.get("lon", 0)
            sign_idx = int(lon // 30)
            house = ((sign_idx - asc_idx_b) % 12) + 1
            a_in_b_houses[name] = {
                "house": house,
                "house_meaning": _HOUSE_MEANINGS.get(house, ""),
                "planet_sign": data.get("sign_name_zh", ""),
            }

    if asc_idx_a is not None:
        for name, data in planets_b.items():
            lon = data.get("lon", 0)
            sign_idx = int(lon // 30)
            house = ((sign_idx - asc_idx_a) % 12) + 1
            b_in_a_houses[name] = {
                "house": house,
                "house_meaning": _HOUSE_MEANINGS.get(house, ""),
                "planet_sign": data.get("sign_name_zh", ""),
            }

    return {"a_in_b": a_in_b_houses, "b_in_a": b_in_a_houses}


# ═══════════════════════════════════════════════════════════════
# Cross Aspects
# ═══════════════════════════════════════════════════════════════
_ASPECT_ORBS = {
    "合": 8, "冲": 8, "拱": 6, "刑": 6, "六合": 4,
}

_ASPECT_SCORE = {
    "合": 3, "拱": 2, "六合": 2, "冲": -1, "刑": -1,
}

_ASPECT_LABELS = {
    "合": ("融合", "两股能量合为一体,强烈而直接"),
    "拱": ("和谐", "自然流动,相互支持,轻松愉悦"),
    "六合": ("机遇", "温和的吸引力,需要主动激活"),
    "冲": ("张力", "对立但互补——吸引与排斥共存"),
    "刑": ("摩擦", "成长的摩擦,需要持续的调适"),
}


def _cross_aspects(positions_a: dict, positions_b: dict) -> list:
    """计算两个盘之间的所有跨盘相位。"""
    aspects = []
    for name_a, lon_a in positions_a.items():
        for name_b, lon_b in positions_b.items():
            diff = abs(lon_a - lon_b) % 360
            if diff > 180:
                diff = 360 - diff

            for aspect_name, orb in _ASPECT_ORBS.items():
                target = {
                    "合": 0, "六合": 60, "刑": 90, "拱": 120, "冲": 180,
                }[aspect_name]
                actual_orb = abs(diff - target)
                if actual_orb <= orb:
                    weight = _pair_weight(name_a, name_b)
                    aspects.append({
                        "planet_a": name_a,
                        "planet_b": name_b,
                        "aspect": aspect_name,
                        "aspect_label": _ASPECT_LABELS[aspect_name][0],
                        "aspect_note": _ASPECT_LABELS[aspect_name][1],
                        "orb": round(actual_orb, 2),
                        "diff": round(diff, 2),
                        "score_contribution": _ASPECT_SCORE.get(aspect_name, 0) * weight / 3,
                        "weight": weight,
                    })
    # Sort by absolute score contribution (most impactful first)
    aspects.sort(key=lambda x: abs(x["score_contribution"]), reverse=True)
    return aspects


# ═══════════════════════════════════════════════════════════════
# Composite Chart (中点法)
# ═══════════════════════════════════════════════════════════════
def _composite_midpoint(positions_a: dict, positions_b: dict) -> dict:
    """计算组合中点盘。"""
    composite = {}
    for name in set(list(positions_a.keys()) + list(positions_b.keys())):
        la = positions_a.get(name)
        lb = positions_b.get(name)
        if la is not None and lb is not None:
            # 中点: 注意跨越 0° 的情况
            diff = abs(la - lb) % 360
            if diff > 180:
                midpoint = ((la + lb) / 2 + 180) % 360
            else:
                midpoint = (la + lb) / 2 % 360
            composite[name] = {
                "lon": round(midpoint, 4),
                **am.sign_of(midpoint),
            }
    return composite


# ═══════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════
def _score_synastry(cross_aspects: list, overlays: dict,
                     composite: dict, asc_a: dict | None, asc_b: dict | None) -> dict:
    """综合评分 (0-100)。"""
    breakdown = {}

    # 1. 跨盘相位 (50%)
    aspect_score = 0.0
    max_possible = 0.0
    for a in cross_aspects:
        contribution = a.get("score_contribution", 0)
        aspect_score += contribution
        max_possible += abs(a.get("score_contribution", 0)) if contribution else 0

    if max_possible > 0:
        # Normalize: shift negative to 0-50 range based on ratio
        normalized = 25 + (aspect_score / max_possible) * 25
        normalized = max(0, min(50, normalized))
    else:
        normalized = 25

    breakdown["cross_aspects"] = {
        "score": round(normalized, 1),
        "max": 50,
        "raw_score": round(aspect_score, 2),
        "aspect_count": len(cross_aspects),
    }

    # 2. 宫位叠加 (25%)
    overlay_score = 0
    romantic_houses = {5, 7, 8}
    supportive_houses = {2, 4, 11}
    challenging_houses = {6, 12}

    a_in_b = overlays.get("a_in_b", {})
    b_in_a = overlays.get("b_in_a", {})

    for planet_name, overlay in {**a_in_b, **b_in_a}.items():
        h = overlay.get("house", 0)
        if planet_name in ("太阳", "月亮", "金星", "火星"):
            if h in romantic_houses:
                overlay_score += 3
            elif h in supportive_houses:
                overlay_score += 2
            elif h in challenging_houses:
                overlay_score += 1
        else:
            if h in romantic_houses:
                overlay_score += 1.5
            elif h in supportive_houses:
                overlay_score += 1

    overlay_score = min(25, overlay_score + 5)
    breakdown["house_overlays"] = {
        "score": round(overlay_score, 1),
        "max": 25,
        "significant_overlays": [
            {"planet": p, "house": o.get("house"), "meaning": o.get("house_meaning", "")}
            for p, o in a_in_b.items()
            if o.get("house") in romantic_houses
        ],
    }

    # 3. 上升-上升 / 上升-行星连接 (15%)
    asc_score = 0
    asc_connections = []

    if asc_a and asc_b:
        asc_lon_a = asc_a.get("lon", 0)
        asc_lon_b = asc_b.get("lon", 0)
        diff = abs(asc_lon_a - asc_lon_b) % 360
        if diff > 180:
            diff = 360 - diff

        if diff < 8:
            asc_score += 8
            asc_connections.append("上升合相——强烈的第一印象吸引")
        elif diff < 60 + 4 and diff > 60 - 4:
            asc_score += 5
            asc_connections.append("上升六合——温和的默契")
        elif diff < 120 + 6 and diff > 120 - 6:
            asc_score += 6
            asc_connections.append("上升拱相——自然和谐的连接")
        elif diff < 90 + 6 and diff > 90 - 6:
            asc_score += 2
            asc_connections.append("上升刑相——初始摩擦,但可能有强烈吸引")

    # Sun-Ascendant, Moon-Ascendant connections
    if asc_a:
        asc_lon_a = asc_a.get("lon", 0)
        # B's Sun/Moon on A's Asc
        for planet_name in ("太阳", "月亮", "金星"):
            b_pos = None
            for cn, data in overlays.get("b_in_a", {}).items():
                if cn == planet_name:
                    b_pos = overlays["b_in_a"][cn]
                    break
            if b_pos and b_pos.get("house") in (1, 7):
                asc_score += 3
                asc_connections.append(f"B的{planet_name}在A的第{b_pos['house']}宫——重要个人连接")

    if asc_b:
        asc_lon_b = asc_b.get("lon", 0)
        for planet_name in ("太阳", "月亮", "金星"):
            a_pos = None
            for cn, data in overlays.get("a_in_b", {}).items():
                if cn == planet_name:
                    a_pos = overlays["a_in_b"][cn]
                    break
            if a_pos and a_pos.get("house") in (1, 7):
                asc_score += 3
                asc_connections.append(f"A的{planet_name}在B的第{a_pos['house']}宫——重要个人连接")

    asc_score = min(15, asc_score)
    breakdown["ascendant_connections"] = {
        "score": round(asc_score, 1),
        "max": 15,
        "connections": asc_connections,
    }

    # 4. 日月连接 (10%)
    sun_moon_score = 0
    sun_moon_aspects = [a for a in cross_aspects
                        if {a["planet_a"], a["planet_b"]} in (
                            {"太阳", "月亮"}, {"太阳"}, {"月亮"})]
    for a in sun_moon_aspects:
        if a["aspect"] in ("合", "拱"):
            sun_moon_score += 4
        elif a["aspect"] == "六合":
            sun_moon_score += 3
        elif a["aspect"] == "冲":
            sun_moon_score += 2

    sun_moon_score = min(10, sun_moon_score)
    breakdown["sun_moon"] = {
        "score": round(sun_moon_score, 1),
        "max": 10,
        "aspects": [f"{a['planet_a']}-{a['planet_b']} {a['aspect_label']}" for a in sun_moon_aspects],
    }

    total = sum(b["score"] for b in breakdown.values())
    return {
        "compatibility_score": round(total, 1),
        "breakdown": breakdown,
    }


# ═══════════════════════════════════════════════════════════════
# 解读
# ═══════════════════════════════════════════════════════════════
def _interpret(score: float) -> dict:
    if score >= 80:
        level = "灵魂伴侣级"
        desc = "星盘之间有着罕见的多重和谐连接。日月、金火相位优美,宫位叠加互相激活重要领域。这种组合在人群中比例很低,珍惜这份连接。"
    elif score >= 65:
        level = "高度和谐"
        desc = "两人星盘配合良好,在多个关键维度上产生共振。关系发展有稳固的占星基础,但仍需日常沟通来维系。"
    elif score >= 50:
        level = "良好匹配"
        desc = "有较多正向连接,也有需要磨合的地方。这是一种健康的关系基础——既有舒适感也有成长空间。"
    elif score >= 40:
        level = "中等契合"
        desc = "有一些和谐相位,也存在明显的张力。这段关系会带来成长,但需要双方有意识地去理解和包容对方的差异。"
    elif score >= 30:
        level = "挑战型"
        desc = "星盘间存在较多硬相位和张力。这不是说关系不可能成功,而是需要更多的觉察、沟通和妥协。这种关系往往带来最深的人生功课。"
    else:
        level = "需要觉察"
        desc = "双方星盘连接较少,可能需要更多时间在日常相处中建立联结。占星不是判决书——真实的关系远比星盘复杂。"
    return {"level": level, "description": desc}


# ═══════════════════════════════════════════════════════════════
# 主计算函数
# ═══════════════════════════════════════════════════════════════
def compute(birth_a: Birth, birth_b: Birth) -> ChartResult:
    """计算两个人的西方占星合盘 (Synastry)。"""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from skyfield.api import load

    ts = load.timescale()
    eph = load("de421.bsp")
    earth = eph["earth"]

    dt_a = datetime(birth_a.year, birth_a.month, birth_a.day,
                     birth_a.hour, birth_a.minute, tzinfo=ZoneInfo(birth_a.tz))
    dt_b = datetime(birth_b.year, birth_b.month, birth_b.day,
                     birth_b.hour, birth_b.minute, tzinfo=ZoneInfo(birth_b.tz))

    t_a = ts.from_datetime(dt_a)
    t_b = ts.from_datetime(dt_b)

    # ── Person A 行星位置 ──
    positions_a = {}
    for cn, key in _PLANETS.items():
        try:
            astrometric = earth.at(t_a).observe(eph[key]).apparent()
            lon, _, _ = astrometric.ecliptic_latlon()
            positions_a[cn] = lon.degrees % 360
        except Exception:
            pass

    # ── Person B 行星位置 ──
    positions_b = {}
    for cn, key in _PLANETS.items():
        try:
            astrometric = earth.at(t_b).observe(eph[key]).apparent()
            lon, _, _ = astrometric.ecliptic_latlon()
            positions_b[cn] = lon.degrees % 360
        except Exception:
            pass

    # ── 行星数据 (含星座) ──
    planets_a = {cn: {"lon": lon, **am.sign_of(lon)} for cn, lon in positions_a.items()}
    planets_b = {cn: {"lon": lon, **am.sign_of(lon)} for cn, lon in positions_b.items()}

    # ── 上升 ──
    asc_a, asc_idx_a = None, None
    asc_b, asc_idx_b = None, None
    if birth_a.lat is not None and birth_a.lng is not None:
        gst_a = t_a.gmst
        lst_a = (gst_a * 15 + birth_a.lng) % 360
        asc_lon_a = am.ascendant(lst_a, birth_a.lat)
        asc_a = {"lon": asc_lon_a, **am.sign_of(asc_lon_a)} if asc_lon_a else None
        asc_idx_a = int(asc_lon_a // 30) if asc_lon_a else None

    if birth_b.lat is not None and birth_b.lng is not None:
        gst_b = t_b.gmst
        lst_b = (gst_b * 15 + birth_b.lng) % 360
        asc_lon_b = am.ascendant(lst_b, birth_b.lat)
        asc_b = {"lon": asc_lon_b, **am.sign_of(asc_lon_b)} if asc_lon_b else None
        asc_idx_b = int(asc_lon_b // 30) if asc_lon_b else None

    # ── 计算 ──
    overlays = _compute_overlays(planets_a, planets_b, asc_idx_a, asc_idx_b)
    cross = _cross_aspects(positions_a, positions_b)
    composite = _composite_midpoint(positions_a, positions_b)

    # 复合盘自身的相位
    comp_aspects = am.find_aspects(
        {name: data["lon"] for name, data in composite.items()}
    )

    scoring = _score_synastry(cross, overlays, composite, asc_a, asc_b)
    interpretation = _interpret(scoring["compatibility_score"])

    return ChartResult(
        method="synastry",
        school="west",
        engine="skyfield+synastry+composite",
        normalized={
            "elements": {},
            "timeline": [],
            "note": "合盘分析不映射五行元素,以 synastry 评分、跨盘相位和宫位叠加为归一化指标",
        },
        raw={
            "computed_at": date.today().isoformat(),
            "rule_version": "v1",
            "planets_a": planets_a,
            "planets_b": planets_b,
            "ascendant_a": asc_a,
            "ascendant_b": asc_b,
            "overlays": overlays,
            "cross_aspects": cross,
            "composite_chart": composite,
            "composite_aspects": comp_aspects,
            "scoring": scoring,
            "interpretation": interpretation,
            "calculation_basis": {
                "method": "western_synastry",
                "mode": "compatibility",
                "rule_version": "v1",
                "calendar_source": "skyfield + de421.bsp",
                "features": [
                    "跨盘相位 (cross aspects) with weighted pair importance",
                    "宫位叠加 (house overlays) — A's planets in B's houses & vice versa",
                    "组合中点盘 (composite chart by midpoint method)",
                    "上升连接 (ascendant-ascendant, planet-ascendant)",
                    "日月连接专项评分",
                    "加权综合评分 (0-100)",
                ],
                "planet_count_a": len(positions_a),
                "planet_count_b": len(positions_b),
                "limits": [
                    "使用 de421.bsp 星历,三王星在部分年份可能缺失",
                    "组合盘仅使用中点法,不含 Davison 关系盘",
                    "宫位叠加基于整宫制 (whole sign)",
                    "未包含小行星 (婚神/谷神等)",
                ],
            },
        },
    )


# ═══════════════════════════════════════════════════════════════
# 便捷函数: 从已有 chart raw 数据计算
# ═══════════════════════════════════════════════════════════════
def compute_from_charts(chart1_raw: dict, chart2_raw: dict) -> dict:
    """从已计算的两个西方占星盘 raw 数据中提取并计算合盘。

    用于不需要重新加载星历的场景(已有 chart 数据)。
    """
    positions_a = {}
    positions_b = {}
    planets_a = {}
    planets_b = {}

    for cn, data in chart1_raw.get("planets", {}).items():
        lon = data.get("lon", 0)
        positions_a[cn] = lon
        planets_a[cn] = {"lon": lon, **data}

    for cn, data in chart2_raw.get("planets", {}).items():
        lon = data.get("lon", 0)
        positions_b[cn] = lon
        planets_b[cn] = {"lon": lon, **data}

    asc_a = chart1_raw.get("ascendant")
    asc_b = chart2_raw.get("ascendant")
    asc_idx_a = chart1_raw.get("ascendant_sign_idx")
    asc_idx_b = chart2_raw.get("ascendant_sign_idx")

    overlays = _compute_overlays(planets_a, planets_b, asc_idx_a, asc_idx_b)
    cross = _cross_aspects(positions_a, positions_b)
    composite = _composite_midpoint(positions_a, positions_b)

    scoring = _score_synastry(cross, overlays, composite, asc_a, asc_b)
    interpretation = _interpret(scoring["compatibility_score"])

    return {
        "overlays": overlays,
        "cross_aspects": cross,
        "composite_chart": composite,
        "scoring": scoring,
        "interpretation": interpretation,
    }
