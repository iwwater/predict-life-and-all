"""Relationship Timing & Peach Blossom Engine — 桃花/婚恋时机引擎

Based on 剑桥图灵子's videos:
- BV1yQW1zmEmB: AI 八字桃花指数 (52k views)
- BV1ubArzxEp4: Combined Bazi×Ziwei×Western for relationship (94k views)
- BV19K44z7EPm: 八字合婚 (marriage compatibility)

Core features:
1. Peach Blossom Index (桃花指数) — quantitative relationship luck scoring
2. Timing windows — when relationship opportunities are strongest
3. Compatibility scoring — between two charts
4. Single-status analysis — understanding one's relationship patterns
"""



# ── Helpers ──────────────────────────────────────────────────────────────────

def _has_star(stars, name: str) -> bool:
    """Check if a star is present (works with list or dict format)."""
    if isinstance(stars, list):
        return any(s.get("star", "") == name for s in stars if isinstance(s, dict))
    elif isinstance(stars, dict):
        return name in stars
    return False


def _get_star(stars, name: str) -> dict:
    """Get a star's data (works with list or dict format)."""
    if isinstance(stars, list):
        for s in stars:
            if isinstance(s, dict) and s.get("star", "") == name:
                return s
    elif isinstance(stars, dict):
        return stars.get(name, {})
    return {}


# ── Peach Blossom Constants ─────────────────────────────────────────────────

# 桃花星 lookup: 寅午戌→卯, 申子辰→酉, 亥卯未→子, 巳酉丑→午
TAOHUA_BRANCH = {
    "寅": "卯", "午": "卯", "戌": "卯",  # 火局 → 卯
    "申": "酉", "子": "酉", "辰": "酉",  # 水局 → 酉
    "亥": "卯", "卯": "子", "未": "子",  # 木局 → 子 (fix: 亥卯未→子)
    "巳": "午", "酉": "午", "丑": "午",  # 金局 → 午
}

# 红鸾 lookup: 子→卯 丑→寅 寅→丑 卯→子 辰→亥 巳→戌 午→酉 未→申 申→未 酉→午 戌→巳 亥→辰
HONGLUAN = {
    "子": "卯", "丑": "寅", "寅": "丑", "卯": "子",
    "辰": "亥", "巳": "戌", "午": "酉", "未": "申",
    "申": "未", "酉": "午", "戌": "巳", "亥": "辰",
}

# 天喜 lookup (opposite of 红鸾): 子→酉 丑→申 寅→未 卯→午 辰→巳 巳→辰 午→卯 未→寅 申→丑 酉→子 戌→亥 亥→戌
TIANXI = {
    "子": "酉", "丑": "申", "寅": "未", "卯": "午",
    "辰": "巳", "巳": "辰", "午": "卯", "未": "寅",
    "申": "丑", "酉": "子", "戌": "亥", "亥": "戌",
}

# Day pillar branches that indicate peach blossom tendencies
TAOHUA_DAY_BRANCHES = {"卯", "午", "酉", "子"}

# Ziwei stars related to relationships
ZIWEI_RELATIONSHIP_STARS = {
    "positive": {"天同", "太阴", "廉贞", "天相", "紫微", "天府", "天梁", "文昌"},
    "challenging": {"七杀", "破军", "贪狼", "巨门", "火星", "铃星", "擎羊", "陀罗"},
    "romantic": {"贪狼", "廉贞", "天同", "太阴"},
    "marriage": {"天相", "紫微", "天府", "天梁"},
}


# ── Peach Blossom Index ─────────────────────────────────────────────────────

def compute_peach_blossom_index(raw: dict) -> dict:
    """Compute a 0-100 Peach Blossom (romance luck) index.

    Components:
    - 桃花/红鸾/天喜 stars (35%)
    - Day branch (20%)
    - Spouse palace quality (20%)
    - Element balance for relationships (15%)
    - Shensha indicators (10%)
    """
    score = 0.0
    breakdown = {}

    # 1. Direct peach blossom stars (35 points max)
    shensha = raw.get("shensha", {})
    stars = shensha.get("stars", {})
    notable = shensha.get("summary", {}).get("notable", [])

    star_score = 0
    details = []

    if _has_star(stars, "桃花"):
        star_score += 25
        details.append("命带桃花星(25分)")
    elif "桃花" in str(notable):
        star_score += 15
        details.append("命局见桃花(15分)")

    if _has_star(stars, "红鸾"):
        star_score += 8
        details.append("命带红鸾星(8分)")

    if _has_star(stars, "天喜"):
        star_score += 5
        details.append("命带天喜星(5分)")

    star_score = min(35, star_score)
    score += star_score
    breakdown["star_score"] = {"score": star_score, "max": 35, "details": details}

    # 2. Day branch (20 points max)
    pillars = raw.get("pillars", {})
    day_branch = (pillars.get("day", "") or "")[1:2]
    day_score = 0

    if day_branch in TAOHUA_DAY_BRANCHES:
        day_score = 20
        details = [f"日支{day_branch}为桃花位(20分)"]
    else:
        # Check if day branch brings peach blossom via 三合
        yb = (pillars.get("year", "") or "")[1:2]
        mb = (pillars.get("month", "") or "")[1:2]
        for b in [yb, mb]:
            taohua_b = TAOHUA_BRANCH.get(b, "")
            if taohua_b == day_branch:
                day_score += 10
                details = [f"日支{day_branch}为年/月桃花位(10分)"]
                break

        if day_score == 0:
            day_score = 5  # baseline
            details = [f"日支{day_branch}非桃花位(5分基础)"]

    score += day_score
    breakdown["day_branch"] = {"score": day_score, "max": 20, "details": details}

    # 3. Spouse palace quality (20 points max)
    spouse_score = 0
    s_details = []

    # Check if spouse palace (日支) has favorable shensha
    if day_branch:
        # 天乙贵人 in spouse palace is very good
        tianyi = _get_star(stars, "天乙贵人")
        if isinstance(tianyi, dict):
            tianyi_branches = tianyi.get("branches", [])
            if day_branch in tianyi_branches:
                spouse_score += 10
                s_details.append("日坐天乙贵人(10分)")

        # 文昌 in spouse palace = educated/intellectual partner
        wenchang = _get_star(stars, "文昌")
        if isinstance(wenchang, dict):
            wc_branches = wenchang.get("branches", [])
            if day_branch in wc_branches:
                spouse_score += 5
                s_details.append("日坐文昌星(5分)")

        spouse_score = min(20, spouse_score + 5)  # 5 baseline
        s_details.append(f"日支{day_branch}配偶宫基础(5分)")

    score += spouse_score
    breakdown["spouse_palace"] = {"score": spouse_score, "max": 20, "details": s_details}

    # 4. Element balance for relationships (15 points max)
    elements = raw.get("elements", {})
    day_master = raw.get("day_master", "")
    day_master_el = day_master[:1] if day_master else ""

    # 配偶星 = 财星 for male, 官星 for female
    # Simplified: check if wealth/official element is balanced
    el_score = 0
    if day_master_el:
        # 财星 (wealth star) element
        wealth_el = _restrict_element(day_master_el)
        wealth_val = elements.get(wealth_el, 0)
        total = sum(elements.values()) if elements else 1
        wealth_ratio = wealth_val / total

        if 0.1 <= wealth_ratio <= 0.3:
            el_score = 15
            e_details = [f"财星{wealth_el}均衡({wealth_ratio:.0%})，配偶缘佳(15分)"]
        elif 0.05 <= wealth_ratio <= 0.1 or 0.3 <= wealth_ratio <= 0.4:
            el_score = 10
            e_details = [f"财星{wealth_el}适中({wealth_ratio:.0%})，配偶缘可(10分)"]
        elif wealth_ratio > 0.4:
            el_score = 7
            e_details = [f"财星{wealth_el}过旺({wealth_ratio:.0%})，桃花多但需甄别(7分)"]
        else:
            el_score = 5
            e_details = [f"财星{wealth_el}偏弱({wealth_ratio:.0%})，需主动争取(5分)"]
    else:
        el_score = 8
        e_details = ["五行基本均衡(8分)"]

    score += el_score
    breakdown["element_balance"] = {"score": el_score, "max": 15, "details": e_details}

    # 5. Shensha indicators (10 points max)
    shensha_score = 0
    sh_details = []

    # 孤辰寡宿 = penalty
    if _has_star(stars, "孤辰") or _has_star(stars, "寡宿"):
        shensha_score -= 5
        sh_details.append("命带孤辰/寡宿(-5分)")
    else:
        shensha_score += 2
        sh_details.append("无孤寡星(2分)")

    # 华盖 = neutral/slightly negative for romance
    if _has_star(stars, "华盖"):
        shensha_score -= 2
        sh_details.append("命带华盖，感情上偏清高(-2分)")

    # 驿马 = can bring relationship from afar
    if _has_star(stars, "驿马"):
        shensha_score += 3
        sh_details.append("命带驿马，异地/远方姻缘(3分)")

    shensha_score = max(0, min(10, shensha_score + 5))
    score += shensha_score
    breakdown["shensha_indicators"] = {"score": shensha_score, "max": 10, "details": sh_details}

    # Normalize and interpret
    score = max(0, min(100, score))
    level = _score_level(score)

    return {
        "index": round(score, 1),
        "level": level,
        "interpretation": _interpret_peach_blossom(score, level),
        "breakdown": breakdown,
    }


def _score_level(score: float) -> str:
    if score >= 70:
        return "桃花旺盛"
    elif score >= 55:
        return "桃花较好"
    elif score >= 40:
        return "桃花中等"
    elif score >= 25:
        return "桃花偏弱"
    else:
        return "桃花较弱"


def _interpret_peach_blossom(score: float, level: str) -> str:
    interpretations = {
        "桃花旺盛": (
            "桃花运非常旺盛，异性缘好，感情机会多。但桃花多不等于正缘好，"
            "需要注意桃花质量。建议在大运流年配合时认真选择，避免陷入多角关系。"
            "旺桃花带来的优势是选择面广，劣势是容易眼花缭乱。"
        ),
        "桃花较好": (
            "桃花运不错，在适婚年龄容易遇到合适的对象。感情发展较为顺利，"
            "不属于一见钟情型，但相处久了容易产生好感。建议多参与社交活动，"
            "拓展交友圈。"
        ),
        "桃花中等": (
            "桃花运中等偏上，需要一定的主动和耐心。正缘通常来得不早不晚，"
            "建议不要焦虑，利用这段时间提升自己。好的感情会在你准备好的时候出现。"
        ),
        "桃花偏弱": (
            "桃花运偏弱，在感情上可能感到不太顺利。但这不代表没有好姻缘，"
            "而是需要更多主动和用心经营。建议通过社交圈拓展和兴趣活动来增加机会。"
            "偏弱的桃花往往来得慢但走得稳。"
        ),
        "桃花较弱": (
            "桃花运较弱，婚恋可能较晚。但这不一定是坏事——晚婚者往往更成熟，"
            "婚姻也更稳定。建议专注于自我提升，当你的个人魅力提升后，"
            "好的缘分自然会来。命带孤寡星者可通过养宠物、参与公益活动来化解。"
        ),
    }
    return interpretations.get(level, "桃花运需具体分析。")


# ── Timing Windows ───────────────────────────────────────────────────────────

def compute_relationship_timing(raw: dict, timeline: list | None = None) -> dict:
    """Identify best timing windows for relationships.

    Returns ranked periods with relationship opportunity scores.
    """
    if timeline is None:
        timeline = raw.get("timeline", [])

    pillars = raw.get("pillars", {})
    year_branch = (pillars.get("year", "") or "")[1:2]
    day_master = raw.get("day_master", "")

    # Compute peach blossom branch based on year branch
    taohua_ref = year_branch
    if taohua_ref in ("寅", "午", "戌"):
        taohua_branch = "卯"
    elif taohua_ref in ("申", "子", "辰"):
        taohua_branch = "酉"
    elif taohua_ref in ("亥", "卯", "未"):
        taohua_branch = "子"
    else:  # 巳酉丑
        taohua_branch = "午"

    hongluan_branch = HONGLUAN.get(year_branch, "")
    tianxi_branch = TIANXI.get(year_branch, "")

    windows = []
    for period in (timeline or [])[:8]:
        label = period.get("label", "")
        score = period.get("score", 50) if period.get("score") is not None else 50

        # Check if period branch hits peach blossom / hongluan / tianxi
        period_branch = label[-1:] if label else ""

        triggers = []
        bonus = 0

        if period_branch == taohua_branch:
            triggers.append("桃花")
            bonus += 20
        if period_branch == hongluan_branch:
            triggers.append("红鸾")
            bonus += 25
        if period_branch == tianxi_branch:
            triggers.append("天喜")
            bonus += 20

        # Period element matching spouse star
        if day_master:
            day_el = day_master[:1]
            wealth_el = _restrict_element(day_el)
            period_stem = label[:1] if label else ""

            # Check if period stem matches wealth element
            stem_elements = {
                "甲": "木", "乙": "木", "丙": "火", "丁": "火",
                "戊": "土", "己": "土", "庚": "金", "辛": "金",
                "壬": "水", "癸": "水",
            }
            period_el = stem_elements.get(period_stem, "")
            if period_el == wealth_el:
                triggers.append("配偶星现")
                bonus += 15

        relation_score = min(100, score + bonus)

        windows.append({
            "period": label,
            "base_score": score,
            "relationship_score": relation_score,
            "triggers": triggers,
            "is_prime_time": relation_score >= 80 or len(triggers) >= 2,
            "recommendation": _timing_recommendation(relation_score, triggers),
        })

    # Sort by relationship score
    windows.sort(key=lambda w: w["relationship_score"], reverse=True)

    return {
        "peach_blossom_branch": taohua_branch,
        "hongluan_branch": hongluan_branch,
        "tianxi_branch": tianxi_branch,
        "timing_windows": windows,
        "prime_windows": [w for w in windows if w["is_prime_time"]],
    }


def _timing_recommendation(score: float, triggers: list) -> str:
    if score >= 85:
        return "★★★★★ 绝佳时机！此运感情运极旺，建议积极把握"
    elif score >= 70:
        return "★★★★ 良机！桃花运好，适合发展感情关系"
    elif score >= 60:
        return "★★★ 可期！感情运平稳，适合稳定发展"
    elif score >= 45:
        return "★★ 一般！感情平淡期，可专注自我提升"
    else:
        return "★ 低潮！感情运弱，不宜强求，宜修身养性"


# ── Compatibility Scoring ────────────────────────────────────────────────────

def compute_compatibility(chart1: dict, chart2: dict) -> dict:
    """Compute compatibility score between two charts.

    Components:
    - Day master compatibility (30%)
    - Element interaction (25%)
    - Branch relationship (20%)
    - Shensha complementarity (15%)
    - Pattern complementarity (10%)
    """
    r1 = chart1.get("raw", chart1)
    r2 = chart2.get("raw", chart2)

    score = 0.0
    breakdown = {}

    # 1. Day master compatibility (30 points)
    dm1 = r1.get("day_master", "")
    dm2 = r2.get("day_master", "")

    day_score = _day_master_compatibility(dm1, dm2)
    score += day_score
    breakdown["day_master"] = {
        "score": day_score, "max": 30,
        "detail": f"{dm1} vs {dm2}: {_day_master_desc(day_score)}",
    }

    # 2. Element interaction (25 points)
    el1 = r1.get("elements", {})
    el2 = r2.get("elements", {})

    el_score = _element_compatibility(el1, el2)
    score += el_score
    breakdown["elements"] = {
        "score": el_score, "max": 25,
        "detail": _element_compat_desc(el_score),
    }

    # 3. Branch relationship (20 points)
    pillars1 = r1.get("pillars", {})
    pillars2 = r2.get("pillars", {})

    branch_score = _branch_compatibility(pillars1, pillars2)
    score += branch_score
    breakdown["branches"] = {
        "score": branch_score, "max": 20,
        "detail": f"地支关系评分：{branch_score}/20",
    }

    # 4. Shensha complementarity (15 points)
    s1 = r1.get("shensha", {})
    s2 = r2.get("shensha", {})

    shensha_score = _shensha_complementarity(s1, s2)
    score += shensha_score
    breakdown["shensha"] = {
        "score": shensha_score, "max": 15,
        "detail": f"神煞互补评分：{shensha_score}/15",
    }

    # 5. Pattern complementarity (10 points)
    p1 = r1.get("pattern", {})
    p2 = r2.get("pattern", {})

    pattern_score = _pattern_complementarity(p1, p2)
    score += pattern_score
    breakdown["pattern"] = {
        "score": pattern_score, "max": 10,
        "detail": f"格局互补性：{pattern_score}/10",
    }

    score = max(0, min(100, score))

    return {
        "compatibility_score": round(score, 1),
        "level": _compat_level(score),
        "interpretation": _compat_interpretation(score),
        "breakdown": breakdown,
        "advice": _compat_advice(score, breakdown),
    }


def _day_master_compatibility(dm1: str, dm2: str) -> float:
    """Score day master compatibility based on five element interaction."""
    el1 = dm1[:1] if dm1 else ""
    el2 = dm2[:1] if dm2 else ""

    if not el1 or not el2:
        return 15  # neutral

    # Generation (相生) = best
    gen_chain = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    if gen_chain.get(el1) == el2:
        return 28  # el1 generates el2 — very good
    if gen_chain.get(el2) == el1:
        return 25  # el2 generates el1 — good

    # Same element (比和) = good
    if el1 == el2:
        return 22

    # Restriction (相克) = challenging
    res_chain = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if res_chain.get(el1) == el2:
        return 10  # el1 restricts el2 — challenging
    if res_chain.get(el2) == el1:
        return 12  # el2 restricts el1 — challenging

    return 15  # neutral


def _day_master_desc(score: float) -> str:
    if score >= 25:
        return "相生，非常和谐"
    elif score >= 20:
        return "比和，互相理解"
    elif score >= 12:
        return "一般，需磨合"
    else:
        return "相克，容易冲突"


def _element_compatibility(el1: dict, el2: dict) -> float:
    """How well the five element distributions complement each other."""
    score = 0.0

    total1 = sum(el1.values()) if el1 else 1
    total2 = sum(el2.values()) if el2 else 1

    for el in ("木", "火", "土", "金", "水"):
        v1 = el1.get(el, 0) / total1
        v2 = el2.get(el, 0) / total2

        # Complementary: one's weak element is other's strong element
        diff = abs(v1 - v2)
        score += (1 - diff) * 5  # Max 5 per element

    return min(25, score)


def _element_compat_desc(score: float) -> str:
    if score >= 20:
        return "五行互补性强"
    elif score >= 14:
        return "五行基本和谐"
    else:
        return "五行互补较弱"


def _branch_compatibility(p1: dict, p2: dict) -> float:
    """Score based on earthly branch relationships."""
    score = 10  # baseline

    day_b1 = (p1.get("day", "") or "")[1:2]
    day_b2 = (p2.get("day", "") or "")[1:2]

    # Six combinations (六合)
    liuhe = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅",
             "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰",
             "巳": "申", "申": "巳", "午": "未", "未": "午"}
    if liuhe.get(day_b1) == day_b2:
        score += 8  # Day branches in 六合

    # Three harmony groups (三合)
    sanhe_groups = [{"申", "子", "辰"}, {"寅", "午", "戌"},
                    {"亥", "卯", "未"}, {"巳", "酉", "丑"}]
    for grp in sanhe_groups:
        if {day_b1, day_b2}.issubset(grp) and day_b1 != day_b2:
            score += 5

    # Branch restrictions (相冲/相刑/相害) = penalty
    chong = {"子": "午", "午": "子", "丑": "未", "未": "丑",
             "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
             "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
    if chong.get(day_b1) == day_b2:
        score -= 5  # 六冲

    return max(0, min(20, score))


def _shensha_complementarity(s1: dict, s2: dict) -> float:
    """Score based on shensha complementarity."""
    score = 7.5  # baseline

    stars1 = s1.get("stars", {})
    stars2 = s2.get("stars", {})
    notable1 = s1.get("summary", {}).get("notable", [])
    notable2 = s2.get("summary", {}).get("notable", [])

    # One has 孤辰, other has 寡宿 → not complementary
    if (_has_star(stars1, "孤辰") and _has_star(stars2, "寡宿")) or \
       (_has_star(stars1, "寡宿") and _has_star(stars2, "孤辰")):
        score -= 3

    # Both have 天乙贵人 → good
    if _has_star(stars1, "天乙贵人") and _has_star(stars2, "天乙贵人"):
        score += 3

    # One has 桃花, other has stable earth → complement
    has_taohua_1 = "桃花" in str(notable1)
    has_taohua_2 = "桃花" in str(notable2)
    if has_taohua_1 != has_taohua_2:  # One has, one doesn't
        score += 2  # Complementary dynamic

    return max(0, min(15, score))


def _pattern_complementarity(p1: dict, p2: dict) -> float:
    """Score based on pattern/grid complementarity."""
    score = 5  # baseline

    pat1 = p1.get("pattern", "")
    pat2 = p2.get("pattern", "")

    # Complementary patterns
    complements = {
        "正官格": ("正印格", "财格"),
        "七杀格": ("正印格", "食神格"),
        "财格": ("正官格", "食神格"),
        "印格": ("正官格", "七杀格", "食神格"),
        "食神格": ("七杀格", "财格"),
    }

    for k, vs in complements.items():
        if k in pat1 and any(v in pat2 for v in vs):
            score += 3
        if k in pat2 and any(v in pat1 for v in vs):
            score += 3

    return max(0, min(10, score))


def _compat_level(score: float) -> str:
    if score >= 75:
        return "天作之合"
    elif score >= 60:
        return "佳偶天成"
    elif score >= 50:
        return "中上之配"
    elif score >= 40:
        return "中等姻缘"
    elif score >= 30:
        return "多有磨合"
    else:
        return "需要慎重"


def _compat_interpretation(score: float) -> str:
    return {
        "天作之合": (
            "从八字结构看，两人五行互补、日主相生，配合度非常高。"
            "这种组合往往一见如故，相处自然和谐。建议在关系顺利时也不要忽视沟通。"
        ),
        "佳偶天成": (
            "两人八字配合良好，在很多重要维度上互补。关系发展顺利的可能性大，"
            "但也需要在具体事务上相互磨合。整体而言是很好的组合。"
        ),
        "中上之配": (
            "配合度中上，有好的一面也有需要磨合的地方。建议重点发挥互补优势，"
            "同时注意在容易产生分歧的方面多加沟通。这种组合需要用心经营。"
        ),
        "中等姻缘": (
            "八字配合度中等，有好有坏。这不是说不能在一起，而是需要双方更多的"
            "包容和理解。如果能找到合适的相处方式，这种关系也能长久。"
        ),
        "多有磨合": (
            "两人八字结构有一定冲突，在一起需要较多的磨合和妥协。"
            "建议在重要决策前充分沟通，了解彼此的根本差异。"
            "如果双方都愿意为关系付出，困难也是可以克服的。"
        ),
        "需要慎重": (
            "八字配合度偏低，五行和日主方面存在较明显的冲突。"
            "不是绝对不行，但需要非常清醒地认识彼此的差异，"
            "并做好长期磨合的心理准备。建议多维度考察，不急于做决定。"
        ),
    }.get(_compat_level(score), "需要具体分析双方的八字配合情况。")


def _compat_advice(score: float, breakdown: dict) -> list[str]:
    advice = []
    for key, data in breakdown.items():
        if key == "day_master" and data["score"] < 15:
            advice.append("日主五行相克，建议培养共同兴趣来增进默契")
        if key == "branches" and data["score"] < 10:
            advice.append("日支存在冲克，在重大决策上需特别沟通")
        if key == "shensha" and data["score"] < 8:
            advice.append("神煞配合度偏低，建议关注双方的现实相处感受")
    if not advice:
        advice.append("整体配合良好，继续保持现有的沟通方式")
    return advice


# ── Helpers ──────────────────────────────────────────────────────────────────

def _restrict_element(el: str) -> str:
    """Get what element this one restricts (克)."""
    mapping = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    return mapping.get(el, "")


def _generate_element(el: str) -> str:
    """Get what element this one generates (生)."""
    mapping = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    return mapping.get(el, "")
