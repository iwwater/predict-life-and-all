"""Domain-specific interpretation rules for Bazi and multi-method analysis.

Extracted rules for specific life domains derived from classical principles:
- Wealth (财运): pattern matching for wealth indicators, timing rules
- Relationships (感情): spouse palace analysis, peach blossom indicators
- Health (健康): five-element-to-organ correspondence, weakness indicators
- Career (事业): career timing, transition indicators
"""

DOMAIN_RULES = {
    "wealth": {
        "name": "财运",
        "rules": [
            {
                "id": "w1",
                "condition": "财星得月令且日主身强",
                "condition_detail": {"财星_count": (">=", 2), "strength_score": (">=", 65)},
                "interpretation": "身强财旺，能任财官。财运基础扎实，适合主动求财。",
                "timing": "行食伤运或财运时爆发力最强",
                "source": "三命通会·卷六·论财",
                "confidence": 85,
            },
            {
                "id": "w2",
                "condition": "财多身弱",
                "condition_detail": {"财星_count": (">=", 3), "strength_score": ("<=", 45)},
                "interpretation": "富屋贫人：财虽多但身弱不胜财，看得到拿不到。宜守不宜攻。",
                "timing": "行印比运扶身时方可求财",
                "source": "渊海子平·论用神",
                "confidence": 80,
            },
            {
                "id": "w3",
                "condition": "食伤生财格局",
                "condition_detail": {"食伤_count": (">=", 2), "财星_count": (">=", 2)},
                "interpretation": "食伤生财，以技艺/创意/口才生财。宜发挥专长，技术致富型。",
                "timing": "食伤旺年和财运年均有利",
                "source": "三命通会·卷六",
                "confidence": 82,
            },
            {
                "id": "w4",
                "condition": "财星被比劫克制",
                "condition_detail": {"财星_count": (">=", 1), "比劫_count": (">=", 3)},
                "interpretation": "比劫夺财，易破财、合伙不利、资金被分薄。理财需保守。",
                "timing": "官杀运可制比劫护财",
                "source": "渊海子平·论十神",
                "confidence": 78,
            },
            {
                "id": "w5",
                "condition": "偏财透干且有金舆",
                "condition_detail": {"偏财_透干": True, "shensha": "金舆"},
                "interpretation": "偏财透干加金舆星照，横财运佳、易有意外之财、投资眼光准。",
                "timing": "偏财运年机会最大",
                "source": "三命通会+神煞",
                "confidence": 75,
            },
        ],
    },
    "relationship": {
        "name": "感情/婚姻",
        "rules": [
            {
                "id": "r1",
                "condition": "日支桃花",
                "condition_detail": {"日柱": "桃花"},
                "interpretation": "日坐桃花，配偶外貌出众、婚姻感情丰富但需防桃花劫。",
                "timing": "桃花流年感情机会多",
                "source": "渊海子平·论神煞",
                "confidence": 78,
            },
            {
                "id": "r2",
                "condition": "日支被冲",
                "condition_detail": {"日支_冲": True},
                "interpretation": "日支逢冲，婚姻宫不稳，感情易波动、晚婚为宜。",
                "timing": "冲合之年婚恋变化大",
                "source": "渊海子平·卷二·论太岁",
                "confidence": 82,
            },
            {
                "id": "r3",
                "condition": "男命财星不显",
                "condition_detail": {"gender": "male", "财星_count": ("<=", 0)},
                "interpretation": "男命财星不显，姻缘较晚或不顺。需大运流年引动。",
                "timing": "行财运或财年有婚恋机会",
                "source": "三命通会·六亲论",
                "confidence": 75,
            },
            {
                "id": "r4",
                "condition": "女命官杀混杂",
                "condition_detail": {"gender": "female", "官杀_count": (">=", 2)},
                "interpretation": "女命官杀混杂，感情选择多但易纠结，需明辨。",
                "timing": "去官留杀或去杀留官之年为定缘时机",
                "source": "渊海子平·论女命",
                "confidence": 80,
            },
            {
                "id": "r5",
                "condition": "孤辰寡宿入命",
                "condition_detail": {"shensha": ["孤辰", "寡宿"]},
                "interpretation": "孤辰寡宿入命，亲密关系建立较慢、宜晚婚、需主动经营感情。",
                "timing": "桃花年可缓和孤寡之性",
                "source": "神煞体系",
                "confidence": 72,
            },
        ],
    },
    "health": {
        "name": "健康",
        "rules": [
            {
                "id": "h1",
                "condition": "金弱",
                "condition_detail": {"elements.metal": ("<=", 0.5)},
                "interpretation": "金弱对应肺与大肠系统，易有呼吸系统敏感、皮肤问题。宜白色食物养肺。",
                "advice": "秋季养生重点，多食银耳、百合、梨",
                "source": "黄帝内经+五行对应",
                "confidence": 85,
            },
            {
                "id": "h2",
                "condition": "木过旺",
                "condition_detail": {"elements.wood": (">=", 4.0)},
                "interpretation": "木过旺对应肝胆，易肝火旺、情绪急躁。宜绿色食物疏肝理气。",
                "advice": "春季注意情绪管理，多运动疏散",
                "source": "黄帝内经+五行对应",
                "confidence": 85,
            },
            {
                "id": "h3",
                "condition": "火弱",
                "condition_detail": {"elements.fire": ("<=", 0.5)},
                "interpretation": "火弱对应心与小肠，易心血不足、畏寒怕冷。宜红色食物温补心阳。",
                "advice": "夏季适当户外活动，补充阳气",
                "source": "黄帝内经+五行对应",
                "confidence": 85,
            },
            {
                "id": "h4",
                "condition": "水过旺",
                "condition_detail": {"elements.water": (">=", 4.0)},
                "interpretation": "水过旺对应肾与膀胱，易水肿、寒湿体质。宜黑色食物补肾利水。",
                "advice": "冬季注意保暖，避免寒凉食物",
                "source": "黄帝内经+五行对应",
                "confidence": 85,
            },
            {
                "id": "h5",
                "condition": "土弱",
                "condition_detail": {"elements.earth": ("<=", 0.5)},
                "interpretation": "土弱对应脾胃，易消化不良、吸收差。宜黄色食物健脾养胃。",
                "advice": "注意饮食规律，少食多餐",
                "source": "黄帝内经+五行对应",
                "confidence": 85,
            },
        ],
    },
    "career": {
        "name": "事业/职业",
        "rules": [
            {
                "id": "c1",
                "condition": "官印相生",
                "condition_detail": {"官星_count": (">=", 2), "印星_count": (">=", 2)},
                "interpretation": "官印相生，体制内发展顺利、易获升迁。稳扎稳打型事业路线。",
                "timing": "官运和印运是晋升窗口期",
                "source": "三命通会·论正官+论印绶",
                "confidence": 85,
            },
            {
                "id": "c2",
                "condition": "食伤生财",
                "condition_detail": {"食伤_count": (">=", 2), "财星_count": (">=", 2)},
                "interpretation": "食伤生财，适合创业或自由职业。以技能变现，宜市场导向型工作。",
                "timing": "食伤运创业黄金期",
                "source": "三命通会·论食神+论财",
                "confidence": 82,
            },
            {
                "id": "c3",
                "condition": "驿马逢财或官",
                "condition_detail": {"shensha": "驿马", "财星_count": (">=", 1)},
                "interpretation": "驿马带财，动中求财型。适合出差多、跨地域工作或国际业务。",
                "timing": "驿马流年适合跳槽或外派",
                "source": "神煞体系",
                "confidence": 75,
            },
            {
                "id": "c4",
                "condition": "七杀得制化",
                "condition_detail": {"七杀_count": (">=", 1), "食伤_count": (">=", 1)},
                "interpretation": "食神制杀，英雄独压万人。适合竞争性强的高压行业。",
                "timing": "食伤运职业突破最大",
                "source": "三命通会·论七杀",
                "confidence": 80,
            },
            {
                "id": "c5",
                "condition": "大运交脱期",
                "condition_detail": {"换运": True},
                "interpretation": "正逢大运交接期，事业方向可能有较大调整。宜顺势而为。",
                "timing": "换运前后1-2年为调整期",
                "source": "三命通会·论大运",
                "confidence": 72,
            },
        ],
    },
}


def get_domain_rules(domain: str) -> dict | None:
    """Get all rules for a specific domain.

    Args:
        domain: One of "wealth", "relationship", "health", "career"

    Returns:
        {name: ..., rules: [...]} or None
    """
    return DOMAIN_RULES.get(domain)


def check_rules(chart, domain: str) -> list[dict]:
    """Check which domain rules apply to a given chart.

    Currently returns all rules with a match confidence indicator.
    Future versions will do automatic condition matching.

    Args:
        chart: ChartResult or dict with raw data
        domain: Domain key

    Returns:
        List of matching rules with applicability notes
    """
    domain_data = DOMAIN_RULES.get(domain)
    if not domain_data:
        return []

    raw = chart.raw if hasattr(chart, "raw") else chart.get("raw", {})
    elements = (
        chart.normalized.get("elements", {})
        if hasattr(chart, "normalized")
        else chart.get("normalized", {}).get("elements", {})
    )

    matches = []
    for rule in domain_data["rules"]:
        applicability = _evaluate_condition(rule["condition_detail"], raw, elements)
        matches.append({
            **rule,
            "applicable": applicability > 0,
            "applicability_score": applicability,
        })

    return sorted(matches, key=lambda x: x["applicability_score"], reverse=True)


def _evaluate_condition(condition: dict, raw: dict, elements: dict) -> float:
    """Simple condition evaluator. Returns 0-100 applicability score.

    This is a basic scorer. For production use, replace with proper fuzzy matching.
    """
    score = 0
    total_checks = len(condition)
    if total_checks == 0:
        return 50

    for key, (op, value) in condition.items():
        if key.startswith("elements."):
            elem = key.split(".")[1]
            actual = elements.get(elem, 0)
            if op == ">=" and actual >= value:
                score += 1
            elif op == "<=" and actual <= value:
                score += 1
            elif op == ">" and actual > value:
                score += 1
            elif op == "<" and actual < value:
                score += 1
        elif key == "shensha":
            shensha_data = raw.get("shensha", {})
            stars = shensha_data.get("stars", [])
            star_names = {s["star"] for s in stars}
            target = value if isinstance(value, list) else [value]
            if any(t in star_names for t in target):
                score += 1
        elif key.endswith("_count"):
            god_key = key.replace("_count", "")
            counts = raw.get("seasonal_strength_reference", {}).get("ten_god_counts", {})
            actual = counts.get(god_key, 0)
            if op == ">=" and actual >= value:
                score += 1
            elif op == "<=" and actual <= value:
                score += 1

    return round(score / total_checks * 100, 1)
