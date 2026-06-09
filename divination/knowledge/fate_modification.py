"""Fate Modification Advisor — 改命引擎

Based on 剑桥图灵子's BV1r8RSB7ER7 (21k views):
"算准有个屁用？教你怎么改！前数据科学家+华尔街分析师带你读懂命运。"

Core philosophy: Fortune-telling without actionable modification advice is
incomplete. This module moves beyond prediction to provide:

1. Mutable vs Fixed Pattern Identification
   - What CAN be changed (attitude, choices, timing) vs what IS fixed (birth chart)

2. Five-Element Balancing Strategies
   - Practical remedies for element deficiencies

3. Timing-Based Action Windows
   - When to act and when to wait based on luck cycles

4. Domain-Specific Modifications
   - Career, wealth, relationship, health — each with targeted strategies

The approach: Not "changing fate" in a superstitious sense, but understanding
the energetic patterns and making informed choices about timing, direction,
and lifestyle adjustments — much like a weather forecast helps you decide
when to bring an umbrella.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import math


# ── Five Element Remedies ────────────────────────────────────────────────────

WUXING = ("木", "火", "土", "金", "水")

# Generation cycle
GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# Restriction cycle
RESTRICT = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# Element → practical remedies
ELEMENT_REMEDIES = {
    "木": {
        "colors": ["绿色", "青色", "翠色"],
        "directions": ["东方", "东南"],
        "foods": ["绿色蔬菜", "豆类", "酸味食物"],
        "activities": ["园艺", "徒步", "户外活动", "早起"],
        "materials": ["木质家具", "植物", "花卉"],
        "careers": ["教育", "医疗", "环保", "出版", "文化"],
        "season_strength": "春季(寅卯辰月)木旺，为最佳行动期",
        "music": "角音（相当于mi）",
        "organs_to_care": ["肝", "胆"],
        "mindset": "培养仁爱之心和创造力，像树木一样扎根成长",
    },
    "火": {
        "colors": ["红色", "紫色", "橙色"],
        "directions": ["南方"],
        "foods": ["红色食物", "辛辣食物", "苦味食物"],
        "activities": ["演讲", "表演", "社交", "运动"],
        "materials": ["蜡烛", "灯光", "红色装饰"],
        "careers": ["科技", "能源", "娱乐", "餐饮", "传媒"],
        "season_strength": "夏季(巳午未月)火旺，为最佳行动期",
        "music": "徵音（相当于sol）",
        "organs_to_care": ["心", "小肠"],
        "mindset": "培养热情和礼仪，像火一样温暖他人",
    },
    "土": {
        "colors": ["黄色", "棕色", "米色"],
        "directions": ["中央", "西南", "东北"],
        "foods": ["根茎类", "谷物", "甜味食物", "黄色食物"],
        "activities": ["瑜伽", "冥想", "园艺", "收藏"],
        "materials": ["陶瓷", "石材", "黄玉", "水晶"],
        "careers": ["房地产", "金融", "管理", "咨询", "农业"],
        "season_strength": "四季末(辰戌丑未月)土旺，为最佳行动期",
        "music": "宫音（相当于do）",
        "organs_to_care": ["脾", "胃"],
        "mindset": "培养诚信和包容，像大地一样承载万物",
    },
    "金": {
        "colors": ["白色", "金色", "银色"],
        "directions": ["西方", "西北"],
        "foods": ["白色食物", "辛辣食物", "禽肉"],
        "activities": ["整理", "规划", "精进技能", "书法"],
        "materials": ["金属饰品", "白色布料", "玉石"],
        "careers": ["金融", "法律", "军事", "工程", "精密制造"],
        "season_strength": "秋季(申酉戌月)金旺，为最佳行动期",
        "music": "商音（相当于re）",
        "organs_to_care": ["肺", "大肠"],
        "mindset": "培养决断力和正义感，像金属一样坚韧精纯",
    },
    "水": {
        "colors": ["黑色", "蓝色", "深灰色"],
        "directions": ["北方"],
        "foods": ["黑色食物", "海产品", "咸味食物"],
        "activities": ["阅读", "写作", "反思", "游泳"],
        "materials": ["水景", "玻璃", "镜子", "黑色装饰"],
        "careers": ["研究", "咨询", "艺术", "外交", "交通物流"],
        "season_strength": "冬季(亥子丑月)水旺，为最佳行动期",
        "music": "羽音（相当于la）",
        "organs_to_care": ["肾", "膀胱"],
        "mindset": "培养智慧和灵动，像水一样顺势而为",
    },
}


# ── Element Deficiency Detection ─────────────────────────────────────────────

def _detect_deficiencies(elements: dict) -> list[dict]:
    """Detect deficient elements and their severity."""
    total = sum(elements.values())
    if total == 0:
        return []

    avg = total / 5
    deficiencies = []

    for el in WUXING:
        val = elements.get(el, 0)
        ratio = val / avg
        if ratio < 0.5:
            deficiencies.append({
                "element": el,
                "severity": "严重" if ratio < 0.3 else "中度",
                "ratio": round(ratio, 2),
                "absolute": val,
                "remedy": ELEMENT_REMEDIES.get(el, {}),
            })
        elif ratio < 0.7:
            deficiencies.append({
                "element": el,
                "severity": "轻度",
                "ratio": round(ratio, 2),
                "absolute": val,
                "remedy": ELEMENT_REMEDIES.get(el, {}),
            })

    return deficiencies


def _detect_excesses(elements: dict) -> list[dict]:
    """Detect excessive elements that may cause imbalance."""
    total = sum(elements.values())
    if total == 0:
        return []

    avg = total / 5
    excesses = []

    for el in WUXING:
        val = elements.get(el, 0)
        ratio = val / avg
        if ratio > 1.5:
            # To reduce an excess, strengthen what it generates (drain)
            # and what restricts it
            drain_element = GENERATE.get(el, "")
            restrict_element = RESTRICTED_BY.get(el, "")
            excesses.append({
                "element": el,
                "severity": "严重" if ratio > 2.0 else "中度",
                "ratio": round(ratio, 2),
                "drain_with": drain_element,
                "drain_remedy": ELEMENT_REMEDIES.get(drain_element, {}),
                "restrict_with": restrict_element,
                "restrict_remedy": ELEMENT_REMEDIES.get(restrict_element, {}),
            })

    return excesses


# ── Timing-Based Action Windows ──────────────────────────────────────────────

def _compute_action_windows(yong_shen: dict, elements: dict,
                            timeline: list) -> list[dict]:
    """Identify favorable and unfavorable timing for key actions.

    Based on 大运 (10-year luck cycles) and 用神 analysis.
    """
    windows = []

    yong_elements = yong_shen.get("yong_shen_elements", [])
    ji_elements = yong_shen.get("ji_shen_elements", [])

    for period in (timeline or [])[:6]:  # First 6 luck periods
        label = period.get("label", "")
        score = period.get("score", 50) if period.get("score") is not None else 50

        # Determine if this period favors the yong shen
        # Simplified: check if period heavenly stem or earthly branch
        # aligns with favorable elements
        is_favorable = False
        for ye in yong_elements:
            if ye and ye in label:
                is_favorable = True
                break

        is_unfavorable = False
        for je in ji_elements:
            if je and je in label:
                is_unfavorable = True
                break

        if is_favorable:
            rec = "此运利发展，可积极行动，尤其适合"
            actions = []
            if "财" in yong_shen.get("yong_shen", ""):
                actions.append("投资理财")
            if "官" in yong_shen.get("yong_shen", ""):
                actions.append("仕途晋升")
            if "印" in yong_shen.get("yong_shen", ""):
                actions.append("学习深造")
            if "食" in yong_shen.get("yong_shen", ""):
                actions.append("创意创业")
            if "比" in yong_shen.get("yong_shen", ""):
                actions.append("合作发展")
            rec += "、".join(actions[:3]) if actions else "稳健发展"
        elif is_unfavorable:
            rec = "此运宜守不宜攻，建议低调积累，避免重大决策。可多关注"
            # Recommend what to do during unfavorable periods
            weak_els = _detect_deficiencies(elements)
            if weak_els:
                rec += f"补{weak_els[0]['element']}（{weak_els[0]['remedy'].get('activities', ['修身养性'])[0]}）"
            else:
                rec += "学习提升和内在修养"
        else:
            rec = "此运中平，可按部就班，稳中求进"

        windows.append({
            "period": label,
            "score": score,
            "favorable": is_favorable,
            "unfavorable": is_unfavorable,
            "recommendation": rec,
        })

    return windows


# ── Career Modification ─────────────────────────────────────────────────────

def _career_modifications(pattern: dict, yong_shen: dict, elements: dict) -> list[dict]:
    """Career-specific modification strategies."""
    mods = []

    yong = yong_shen.get("yong_shen", "")
    yong_el = yong_shen.get("yong_shen_elements", [])

    # Career direction based on 用神
    if yong_el:
        primary_el = yong_el[0]
        remedy = ELEMENT_REMEDIES.get(primary_el, {})
        if remedy.get("careers"):
            mods.append({
                "domain": "career",
                "type": "direction",
                "title": "职业方向建议",
                "detail": f"用神为{primary_el}，适合从事：{'、'.join(remedy['careers'][:5])}",
                "action": f"在当前行业无法变动时，可优先选择{'、'.join(remedy['directions'][:2])}"
                          f"方位的公司或办公位",
            })

    # Pattern-based career strategy
    pattern_name = pattern.get("pattern", "")
    if "官" in pattern_name:
        mods.append({
            "domain": "career",
            "type": "strategy",
            "title": "官格发展策略",
            "detail": "官格宜走正途，适合体制内、大企业等规范环境",
            "action": "注重规则和层级，积累资历和人脉",
        })
    elif "财" in pattern_name:
        mods.append({
            "domain": "career",
            "type": "strategy",
            "title": "财格发展策略",
            "detail": "财格善于经营创收，可向商业、投资方向发展",
            "action": "关注市场需求，善用资源整合能力",
        })
    elif "印" in pattern_name:
        mods.append({
            "domain": "career",
            "type": "strategy",
            "title": "印格发展策略",
            "detail": "印格适合学术、研究、教育领域",
            "action": "深耕专业领域，积累学术声誉",
        })
    elif "食" in pattern_name or "伤" in pattern_name:
        mods.append({
            "domain": "career",
            "type": "strategy",
            "title": "食伤格发展策略",
            "detail": "食伤格富有创意和表达力，适合创意行业、自由职业",
            "action": "发挥创造力，建立个人品牌",
        })

    return mods


# ── Relationship Modifications ───────────────────────────────────────────────

def _relationship_modifications(shensha: dict, elements: dict) -> list[dict]:
    """Relationship-specific modification strategies."""
    mods = []

    notable = shensha.get("summary", {}).get("notable", [])
    stars = shensha.get("stars", {})

    # Peach blossom handling
    has_taohua = any("桃花" in s for s in notable)
    has_hongluan = any("红鸾" in s for s in notable)
    has_guchen = any("孤辰" in s for s in notable)
    has_guasu = any("寡宿" in s for s in notable)

    if has_taohua:
        mods.append({
            "domain": "relationship",
            "type": "awareness",
            "title": "桃花运管理",
            "detail": "命带桃花星，异性缘旺，但需注意桃花的质量而非数量",
            "action": "利用好人缘拓展社交圈，但保持辨别力，避免烂桃花",
        })

    if has_hongluan:
        mods.append({
            "domain": "relationship",
            "type": "timing",
            "title": "红鸾星动",
            "detail": "红鸾星主婚恋喜庆，大运流年逢之宜把握姻缘机会",
            "action": "在红鸾星被引动的年份，主动参与社交，增加遇见正缘的机会",
        })

    if has_guchen or has_guasu:
        mods.append({
            "domain": "relationship",
            "type": "mitigation",
            "title": "孤寡星化解",
            "detail": f"命带{'孤辰' if has_guchen else ''}{'寡宿' if has_guasu else ''}，"
                     f"在感情上容易感到孤独或遇人不淑",
            "action": "主动打破社交舒适区，培养共同兴趣，避免过度独立。"
                     "可养宠物或多参与团体活动来化解孤星之气",
        })

    # Element-based relationship advice
    day_master_el = elements.get("day_master_element", "")
    if day_master_el:
        # For relationships, look at spouse star element
        wealth_el = RESTRICT.get(day_master_el, "")  # 财星
        if wealth_el:
            remedy = ELEMENT_REMEDIES.get(wealth_el, {})
            mods.append({
                "domain": "relationship",
                "type": "attraction",
                "title": "增强吸引力",
                "detail": f"财星({wealth_el})为配偶星，增强{wealth_el}五行可提升感情运",
                "action": f"多穿{remedy.get('colors', [''])[0]}色，"
                         f"往{remedy.get('directions', [''])[0]}方发展社交",
            })

    return mods


# ── Health Modifications ─────────────────────────────────────────────────────

def _health_modifications(elements: dict) -> list[dict]:
    """Health-specific modification strategies based on five elements."""
    mods = []

    deficiencies = _detect_deficiencies(elements)

    for d in deficiencies:
        el = d["element"]
        remedy = ELEMENT_REMEDIES.get(el, {})
        organs = remedy.get("organs_to_care", [])
        mods.append({
            "domain": "health",
            "type": "prevention",
            "title": f"{el}元素{d['severity']}不足的调理",
            "detail": f"五行{el}偏弱({d['ratio']:.1f}x)，对应{'/'.join(organs)}"
                     f"需特别关注",
            "action": (
                f"饮食：多食{'、'.join(remedy.get('foods', [])[:3])}。"
                f"起居：{remedy.get('season_strength', '')}多注意保养。"
                f"运动：{'、'.join(remedy.get('activities', [])[:2])}有益。"
            ),
        })

    # Excess elements
    excesses = _detect_excesses(elements)
    for e in excesses:
        el = e["element"]
        organs = ELEMENT_REMEDIES.get(el, {}).get("organs_to_care", [])
        mods.append({
            "domain": "health",
            "type": "balance",
            "title": f"{el}元素{e['severity']}过旺的平衡",
            "detail": f"五行{el}过旺({e['ratio']:.1f}x)，{'/'.join(organs)}"
                     f"负担较重",
            "action": (
                f"建议通过强化{e['drain_with']}({'/'.join(ELEMENT_REMEDIES.get(e['drain_with'], {}).get('activities', []))})"
                f"来宣泄过旺的{el}之气"
            ),
        })

    return mods


# ── Main API ─────────────────────────────────────────────────────────────────

@dataclass
class ModificationPlan:
    """Complete fate modification plan."""
    mutable_patterns: list[dict]     # What can be changed
    fixed_patterns: list[dict]       # What is inherent and should be understood
    element_remedies: list[dict]     # Element balancing strategies
    action_windows: list[dict]       # Timing-based action windows
    career_advice: list[dict]        # Career modifications
    relationship_advice: list[dict]  # Relationship modifications
    health_advice: list[dict]        # Health modifications
    daily_practices: list[dict]      # Daily actionable practices
    summary: str


def generate_plan(chart_result, known_facts: Optional[dict] = None) -> dict:
    """Generate a comprehensive fate modification plan from chart data.

    Args:
        chart_result: The computed chart (dict or ChartResult)
        known_facts: Optional dict of known facts for personalization

    Returns:
        Dict with full modification plan
    """
    # Extract data from chart result
    if hasattr(chart_result, 'raw'):
        raw = chart_result.raw
    elif isinstance(chart_result, dict):
        raw = chart_result.get("raw", chart_result)
    else:
        raw = chart_result

    pattern = raw.get("pattern", {})
    yong_shen = raw.get("yong_shen", {})
    shensha = raw.get("shensha", {})
    elements = raw.get("elements", {})
    flow = raw.get("element_flow", {})
    timeline = raw.get("timeline", [])
    day_master = raw.get("day_master", "")

    # 1. Mutable vs Fixed
    mutable = _identify_mutable(raw)
    fixed = _identify_fixed(raw)

    # 2. Element remedies
    deficiencies = _detect_deficiencies(elements)
    excesses = _detect_excesses(elements)

    element_remedies = []
    for d in deficiencies:
        remedy = ELEMENT_REMEDIES.get(d["element"], {})
        element_remedies.append({
            "element": d["element"],
            "severity": d["severity"],
            "type": "deficiency",
            "colors": remedy.get("colors", []),
            "directions": remedy.get("directions", []),
            "foods": remedy.get("foods", []),
            "activities": remedy.get("activities", []),
            "mindset": remedy.get("mindset", ""),
            "best_season": remedy.get("season_strength", ""),
        })
    for e in excesses:
        element_remedies.append({
            "element": e["element"],
            "severity": e["severity"],
            "type": "excess",
            "drain_via": e["drain_with"],
            "restrict_via": e["restrict_with"],
            "advice": f"通过强化{e['drain_with']}来宣泄过旺的{e['element']}",
        })

    # 3. Action windows
    action_windows = _compute_action_windows(yong_shen, elements,
                                              timeline or raw.get("timeline", []))

    # 4. Domain-specific
    career_advice = _career_modifications(pattern, yong_shen, elements)
    relationship_advice = _relationship_modifications(shensha, elements)
    health_advice = _health_modifications(elements)

    # 5. Daily practices
    daily_practices = _generate_daily_practices(yong_shen, elements, shensha)

    # 6. Summary
    summary = _generate_summary(
        pattern, yong_shen, deficiencies, excesses,
        mutable, fixed
    )

    return {
        "mutable_patterns": mutable,
        "fixed_patterns": fixed,
        "element_remedies": element_remedies,
        "action_windows": action_windows,
        "career_advice": career_advice,
        "relationship_advice": relationship_advice,
        "health_advice": health_advice,
        "daily_practices": daily_practices,
        "summary": summary,
    }


def _identify_mutable(raw: dict) -> list[dict]:
    """Identify aspects of the chart that can be modified."""
    mutable = []

    yong_shen = raw.get("yong_shen", {})
    yong = yong_shen.get("yong_shen", "")

    if yong:
        mutable.append({
            "aspect": "用神补益",
            "description": f"可通过后天努力补充{yong}五行的力量",
            "how": f"选择与{yong}相关的职业、方位、色彩来增强运势",
            "difficulty": "easy",
        })

    mutable.append({
        "aspect": "职业方向",
        "description": "职业选择有较大的调整空间",
        "how": "根据格局特点和用神喜忌选择适合的行业",
        "difficulty": "moderate",
    })

    mutable.append({
        "aspect": "人际关系",
        "description": "社交圈子和关系模式可以主动调整",
        "how": "有意识地接触能补益自身五行的朋友和伴侣",
        "difficulty": "moderate",
    })

    mutable.append({
        "aspect": "居住方位",
        "description": "居住和工作的方位可以调整",
        "how": "根据命卦和用神五行选择有利方位",
        "difficulty": "moderate",
    })

    mutable.append({
        "aspect": "心态习惯",
        "description": "心态和习惯是可塑的",
        "how": "根据格局特点调整思维方式和行为模式",
        "difficulty": "easy",
    })

    return mutable


def _identify_fixed(raw: dict) -> list[dict]:
    """Identify aspects that are inherent to the birth chart."""
    fixed = []

    pattern = raw.get("pattern", {})
    day_master = raw.get("day_master", "")

    fixed.append({
        "aspect": "出生时间",
        "description": "出生年月日时不可更改，命盘大框架已定",
        "understanding": "这不是宿命论，而是说你的能量结构已定，关键在于如何运用",
    })

    if pattern.get("pattern"):
        fixed.append({
            "aspect": "命格类型",
            "description": f"格局「{pattern['pattern']}」决定核心特质倾向",
            "understanding": "格局如性格底色，知道自己是什么类型，才能更好地发挥优势",
        })

    if day_master:
        fixed.append({
            "aspect": "日主五行",
            "description": f"日主{day_master}是不可变更的本命能量",
            "understanding": "了解自己的核心能量特质，顺势而为而非逆势而行",
        })

    return fixed


def _generate_daily_practices(yong_shen: dict, elements: dict,
                              shensha: dict) -> list[dict]:
    """Generate daily actionable practices."""
    practices = []

    yong_els = yong_shen.get("yong_shen_elements", [])

    # Morning routine based on 用神
    if yong_els:
        el = yong_els[0]
        remedy = ELEMENT_REMEDIES.get(el, {})
        practices.append({
            "time": "早晨",
            "practice": f"面向{remedy.get('directions', ['东'])[0]}方深呼吸5分钟",
            "benefit": f"吸纳{el}气，强壮用神",
            "duration": "5-10分钟/天",
        })
        practices.append({
            "time": "全天",
            "practice": f"多穿{remedy.get('colors', [''])[0]}色系衣服",
            "benefit": f"以{el}之色调谐自身气场",
            "duration": "日常",
        })

    # Evening practice
    practices.append({
        "time": "晚间",
        "practice": "睡前记录今日三件感恩之事",
        "benefit": "培养正能量心态，改善命局中心理层面的偏枯",
        "duration": "5分钟/天",
    })

    # Element-specific
    weaknesses = _detect_deficiencies(elements)
    for d in weaknesses[:2]:
        el = d["element"]
        remedy = ELEMENT_REMEDIES.get(el, {})
        practices.append({
            "time": "每周",
            "practice": f"安排{'、'.join(remedy.get('activities', [])[:2])}活动",
            "benefit": f"补充{el}元素能量",
            "duration": "1-2小时/周",
        })

    return practices


def _generate_summary(pattern: dict, yong_shen: dict,
                      deficiencies: list, excesses: list,
                      mutable: list, fixed: list) -> str:
    """Generate overall modification summary."""
    lines = ["【改运总纲】", ""]

    # Core insight
    yong = yong_shen.get("yong_shen", "")
    if yong:
        lines.append(f"命局用神为{yong}，此为改运之枢纽。")
        lines.append(f"一切调整皆围绕强化{yong}的五行力量展开。")
        lines.append("")

    # What to do
    lines.append("## 可改之处（主动作为）")
    for m in mutable[:5]:
        lines.append(f"- {m['aspect']}: {m['how']}")
    lines.append("")

    # What to accept
    lines.append("## 既定之处（顺势而为）")
    for f in fixed[:3]:
        lines.append(f"- {f['aspect']}: {f['understanding']}")
    lines.append("")

    # Element guidance
    if deficiencies:
        lines.append("## 五行补益")
        for d in deficiencies[:2]:
            lines.append(f"- 补{d['element']}({d['severity']}不足): "
                        f"{ELEMENT_REMEDIES.get(d['element'], {}).get('mindset', '')}")

    if excesses:
        lines.append("## 五行平衡")
        for e in excesses[:2]:
            lines.append(f"- 化{e['element']}({e['severity']}过旺): "
                        f"以{e['drain_with']}宣泄")

    lines.append("")
    lines.append("命由天定，运由己造。知命不是为了认命，而是为了更好地用命。")

    return "\n".join(lines)
