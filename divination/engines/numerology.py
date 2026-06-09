"""数字命理 —— 生命灵数(Pythagorean / 西式) 完整版。

核心数字:
- Life Path (生命路径): 从生日计算,一生主题
- Destiny / Expression (命运/表达数): 从全名计算,天赋与潜能
- Soul Urge / Heart's Desire (灵魂驱力): 从名字元音计算,内在渴望
- Personality (人格数): 从名字辅音计算,外在形象
- Birthday (生日数): 从出生日计算,次要与天赋
- Maturity (成熟数): Life Path + Destiny,中年后展现

周期数字:
- Personal Year (流年数): 当年主题
- Personal Month (流月数): 当月焦点

算法: 把生日数字逐位相加,反复求和到 1-9 或 11/22/33(主数)。
名字数字: A=1, B=2, ... Z=26 → 逐位相加 → 归约。
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Optional

from ..contracts import Birth, ChartResult

# ═══════════════════════════════════════════════════════════════
# 字母 → 数字映射 (Pythagorean)
# ═══════════════════════════════════════════════════════════════
_LETTER_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8,
}

_VOWELS = set('AEIOU')
# Y 在元音/辅音判断中: 当 Y 是唯一元音时当作元音,否则当辅音


def _is_vowel(ch: str, has_other_vowels: bool) -> bool:
    """判断字母是否为元音。Y 特殊处理。"""
    if ch in _VOWELS:
        return True
    if ch == 'Y':
        return not has_other_vowels
    return False


def _name_to_number(name: str) -> int:
    """将名字转换为数字(全字母求和后归约)。"""
    total = 0
    for ch in name.upper():
        if ch in _LETTER_VALUES:
            total += _LETTER_VALUES[ch]
    return _reduce(total)


def _name_vowels_number(name: str) -> int:
    """将名字中的元音转换为数字。"""
    upper = name.upper()
    # 先检查是否有 AEIOU 元音
    has_other = any(ch in _VOWELS for ch in upper)
    total = 0
    for ch in upper:
        if ch in _LETTER_VALUES and _is_vowel(ch, has_other):
            total += _LETTER_VALUES[ch]
    return _reduce(total) if total > 0 else 0


def _name_consonants_number(name: str) -> int:
    """将名字中的辅音转换为数字。"""
    upper = name.upper()
    has_other = any(ch in _VOWELS for ch in upper)
    total = 0
    for ch in upper:
        if ch in _LETTER_VALUES and not _is_vowel(ch, has_other):
            total += _LETTER_VALUES[ch]
    return _reduce(total) if total > 0 else 0


def _reduce(n: int) -> int:
    """归约到 1-9 或主数 11/22/33。"""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def _sum_digits(n: int) -> int:
    """逐位求和(不归约到个位,用于中间计算)。"""
    return sum(int(d) for d in str(n))


# ═══════════════════════════════════════════════════════════════
# 数字含义(完整版)
# ═══════════════════════════════════════════════════════════════
NUMBER_MEANINGS = {
    1: {
        "title": "开创者",
        "keywords": ["独立", "领导力", "开创", "原创", "自信"],
        "strength": "天生的领导者,具有强烈的独立精神和创造力。你适合开创事业,走自己的路。",
        "challenge": "需要避免过于独断或自我中心。学会合作与倾听是成长的關鍵。",
        "element": "火",
        "planet": "太阳",
        "color": "红/金",
        "career": ["企业家", "管理者", "发明家", "独立艺术家", "军人"],
    },
    2: {
        "title": "调解者",
        "keywords": ["合作", "敏感", "平衡", "外交", "耐心"],
        "strength": "天生具有敏锐的直觉和协作能力。你是优秀的调解者和团队纽带。",
        "challenge": "需要避免过度依赖他人或回避冲突。学会独立决策是成长的關鍵。",
        "element": "水",
        "planet": "月亮",
        "color": "橙/奶油",
        "career": ["外交官", "心理咨询师", "教师", "人力资源", "艺术家"],
    },
    3: {
        "title": "表达者",
        "keywords": ["创意", "社交", "表达", "乐观", "灵感"],
        "strength": "天生的沟通者和创造者,具有感染力的表达和社交天赋。",
        "challenge": "需要避免分散精力或流于表面。学会专注和深度是成长的關鍵。",
        "element": "火",
        "planet": "木星",
        "color": "黄/金",
        "career": ["作家", "演员", "演说家", "设计师", "营销"],
    },
    4: {
        "title": "建设者",
        "keywords": ["稳定", "秩序", "务实", "勤奋", "可靠"],
        "strength": "天生的建设者,脚踏实地,具有非凡的耐力和组织能力。",
        "challenge": "需要避免过于僵化或固执。学会灵活变通是成长的關鍵。",
        "element": "土",
        "planet": "天王星",
        "color": "绿/棕",
        "career": ["工程师", "会计师", "建筑师", "项目经理", "工匠"],
    },
    5: {
        "title": "自由者",
        "keywords": ["自由", "变化", "冒险", "适应", "多元"],
        "strength": "天生的冒险家,适应力极强,热爱自由和新鲜体验。",
        "challenge": "需要避免逃避责任或过度放纵。学会承诺和扎根是成长的關鍵。",
        "element": "风",
        "planet": "水星",
        "color": "蓝/青",
        "career": ["旅行家", "记者", "销售", "自由职业", "演艺"],
    },
    6: {
        "title": "守护者",
        "keywords": ["责任", "爱", "服务", "和谐", "关怀"],
        "strength": "天生的照料者,具有强烈的责任感和无条件的爱。你是家庭和社区的守护者。",
        "challenge": "需要避免过度牺牲或控制他人。学会放手和界限是成长的關鍵。",
        "element": "土",
        "planet": "金星",
        "color": "靛/粉",
        "career": ["医生", "教师", "社会工作者", "顾问", "护理"],
    },
    7: {
        "title": "求道者",
        "keywords": ["内省", "智慧", "分析", "灵性", "真理"],
        "strength": "天生的思想家和求道者,具有深刻的洞察力和分析能力。",
        "challenge": "需要避免过度孤立或怀疑一切。学会信任和连接是成长的關鍵。",
        "element": "水",
        "planet": "海王星",
        "color": "紫/银",
        "career": ["科学家", "哲学家", "研究员", "分析师", "灵性导师"],
    },
    8: {
        "title": "成就者",
        "keywords": ["权力", "物质", "组织", "成就", "权威"],
        "strength": "天生的管理者和成就者,具有卓越的执行力和商业头脑。",
        "challenge": "需要避免物质主义或滥用权力。学会平衡精神与物质是成长的關鍵。",
        "element": "土",
        "planet": "土星",
        "color": "深蓝/黑",
        "career": ["CEO", "金融家", "律师", "政治家", "企业家"],
    },
    9: {
        "title": "人道者",
        "keywords": ["慈悲", "圆满", "智慧", "奉献", "全球"],
        "strength": "天生的博爱者和智者,具有宽广的胸怀和全球视野。",
        "challenge": "需要避免过度理想化或不切实际。学会落地和珍惜当下是成长的關鍵。",
        "element": "火",
        "planet": "火星",
        "color": "金/白",
        "career": ["慈善家", "艺术家", "导师", "医生", "公益组织者"],
    },
    11: {
        "title": "启灵者(主数)",
        "keywords": ["直觉", "灵性", "启迪", "敏感", "远见"],
        "strength": "主数 11 — 具有超凡直觉和灵性天赋。你是光之使者,能感知常人看不到的维度。",
        "challenge": "需要避免神经紧张或逃避现实。学会接地和管理敏感能量是成长的關鍵。",
        "element": "水",
        "planet": "月亮/海王星",
        "color": "银/白",
        "career": ["灵性导师", "艺术家", "发明家", "治疗师", "哲学家"],
    },
    22: {
        "title": "大师建设者(主数)",
        "keywords": ["大愿景", "建造", "务实灵性", "影响力", "传承"],
        "strength": "主数 22 — 最具力量的主数。能将宏大愿景落地为现实,兼具理想与实践。",
        "challenge": "需要避免被压力压垮或眼高手低。学会分步执行和自我照顾是成长的關鍵。",
        "element": "土",
        "planet": "土星/天王星",
        "color": "金/紫",
        "career": ["建筑师", "外交家", "环境学家", "大企业家", "改革者"],
    },
    33: {
        "title": "大师教师(主数)",
        "keywords": ["无私之爱", "教导", "疗愈", "牺牲", "升华"],
        "strength": "主数 33 — 最稀有。以无条件的爱和智慧教导与疗愈众生。",
        "challenge": "需要避免过度牺牲自我或被情绪淹没。学会设立界限和自我滋养是成长的關鍵。",
        "element": "水",
        "planet": "海王星/木星",
        "color": "紫/金",
        "career": ["灵性领袖", "教育家", "治疗师", "艺术家", "社会改革者"],
    },
}


def _number_profile(n: int) -> dict:
    """获取数字的完整含义资料。"""
    m = NUMBER_MEANINGS.get(n)
    if m:
        return {
            "number": n,
            "is_master": n in (11, 22, 33),
            **m,
        }
    # fallback: 继续归约
    reduced = _reduce(n)
    m2 = NUMBER_MEANINGS.get(reduced, NUMBER_MEANINGS[1])
    return {
        "number": n,
        "reduced_to": reduced,
        "is_master": False,
        **m2,
    }


# ═══════════════════════════════════════════════════════════════
# 核心数字计算
# ═══════════════════════════════════════════════════════════════

def _compute_life_path(b: Birth) -> dict:
    """生命路径数 — 从完整生日计算。"""
    s = f"{b.year}{b.month:02d}{b.day:02d}"
    total = sum(int(d) for d in s)
    life_path = _reduce(total)
    return {
        "life_path": life_path,
        "birth_sum": total,
        "formula": f"{b.year} + {b.month} + {b.day} = {total} → {life_path}",
    }


def _compute_birthday(b: Birth) -> dict:
    """生日数 — 从出生日(仅日)计算。"""
    n = _reduce(b.day)
    return {
        "birthday_number": n,
        "formula": f"出生日 {b.day} → {n}",
    }


def _compute_personal_year(b: Birth, target_date: date = None) -> dict:
    """个人流年数 — (出生月+日 + 目标年份) 归约。"""
    if target_date is None:
        target_date = date.today()
    s = f"{b.month:02d}{b.day:02d}{target_date.year}"
    total = sum(int(d) for d in s)
    n = _reduce(total)
    return {
        "personal_year": n,
        "personal_year_for": target_date.year,
        "formula": f"({b.month:02d} + {b.day:02d} + {target_date.year}) = {total} → {n}",
    }


def _compute_personal_month(b: Birth, target_date: date = None) -> dict:
    """个人流月数 — 个人流年数 + 当前月份。"""
    if target_date is None:
        target_date = date.today()
    py = _compute_personal_year(b, target_date)
    py_num = py["personal_year"]
    total = py_num + target_date.month
    n = _reduce(total)
    return {
        "personal_month": n,
        "personal_month_for": f"{target_date.year}-{target_date.month:02d}",
        "formula": f"流年 {py_num} + {target_date.month}月 = {total} → {n}",
    }


def _compute_destiny(name: str) -> dict:
    """命运数(表达数) — 从全名所有字母计算。"""
    total = 0
    breakdown = []
    for ch in name.upper():
        if ch in _LETTER_VALUES:
            v = _LETTER_VALUES[ch]
            total += v
            breakdown.append(f"{ch}={v}")
    n = _reduce(total)
    return {
        "destiny_number": n,
        "destiny_raw": total,
        "formula": f"{' + '.join(breakdown)} = {total} → {n}",
    }


def _compute_soul_urge(name: str) -> dict:
    """灵魂驱力数 — 从名字中的元音计算。"""
    upper = name.upper()
    has_other = any(ch in _VOWELS for ch in upper)
    total = 0
    breakdown = []
    for ch in upper:
        if ch in _LETTER_VALUES and _is_vowel(ch, has_other):
            v = _LETTER_VALUES[ch]
            total += v
            breakdown.append(f"{ch}={v}")
    n = _reduce(total) if total > 0 else 0
    return {
        "soul_urge_number": n,
        "soul_urge_raw": total,
        "vowels_used": breakdown,
        "formula": f"{' + '.join(breakdown)} = {total} → {n}" if breakdown else "无元音数据",
    }


def _compute_personality(name: str) -> dict:
    """人格数 — 从名字中的辅音计算。"""
    upper = name.upper()
    has_other = any(ch in _VOWELS for ch in upper)
    total = 0
    breakdown = []
    for ch in upper:
        if ch in _LETTER_VALUES and not _is_vowel(ch, has_other):
            v = _LETTER_VALUES[ch]
            total += v
            breakdown.append(f"{ch}={v}")
    n = _reduce(total) if total > 0 else 0
    return {
        "personality_number": n,
        "personality_raw": total,
        "consonants_used": breakdown,
        "formula": f"{' + '.join(breakdown)} = {total} → {n}" if breakdown else "无辅音数据",
    }


def _compute_maturity(life_path: int, destiny: int) -> dict:
    """成熟数 — Life Path + Destiny。"""
    if not destiny:
        return {}
    total = life_path + destiny
    n = _reduce(total)
    return {
        "maturity_number": n,
        "formula": f"生命路径 {life_path} + 命运数 {destiny} = {total} → {n}",
    }


# ═══════════════════════════════════════════════════════════════
# 主计算函数
# ═══════════════════════════════════════════════════════════════

def compute(b: Birth) -> ChartResult:
    # 核心数字(仅需生日)
    lp = _compute_life_path(b)
    bd = _compute_birthday(b)
    py = _compute_personal_year(b)
    pm = _compute_personal_month(b)

    life_path = lp["life_path"]
    life_path_profile = _number_profile(life_path)

    # 名字相关数字(如果提供了名字)
    # 从 question 或 birth 的属性中获取名字
    name = getattr(b, 'name', None) or getattr(b, 'full_name', None)
    destiny = {}
    soul_urge = {}
    personality = {}
    maturity = {}

    if name and isinstance(name, str) and name.strip():
        name = name.strip()
        destiny = _compute_destiny(name)
        soul_urge = _compute_soul_urge(name)
        personality = _compute_personality(name)
        maturity = _compute_maturity(
            life_path,
            destiny.get("destiny_number", 0),
        )

    # 构建所有核心数字列表
    core_numbers = [
        {
            "name": "生命路径 (Life Path)",
            "name_en": "Life Path",
            "number": lp["life_path"],
            "is_master": lp["life_path"] in (11, 22, 33),
            "meaning": _number_profile(lp["life_path"]),
            "importance": "primary",
            "description": "一生最重要的数字,代表你的核心本质和人生课题。",
        },
        {
            "name": "生日数 (Birthday)",
            "name_en": "Birthday",
            "number": bd["birthday_number"],
            "is_master": bd["birthday_number"] in (11, 22, 33),
            "meaning": _number_profile(bd["birthday_number"]),
            "importance": "secondary",
            "description": "次要与特殊天赋,是在生命路径下的补充能力。",
        },
    ]

    if destiny:
        core_numbers.append({
            "name": "命运数 (Destiny/Expression)",
            "name_en": "Destiny",
            "number": destiny["destiny_number"],
            "is_master": destiny["destiny_number"] in (11, 22, 33),
            "meaning": _number_profile(destiny["destiny_number"]),
            "importance": "primary",
            "description": "来自你的名字,代表天赋潜能和此生的使命方向。",
        })
    if soul_urge and soul_urge.get("soul_urge_number", 0) > 0:
        core_numbers.append({
            "name": "灵魂驱力 (Soul Urge)",
            "name_en": "Soul Urge",
            "number": soul_urge["soul_urge_number"],
            "is_master": soul_urge["soul_urge_number"] in (11, 22, 33),
            "meaning": _number_profile(soul_urge["soul_urge_number"]),
            "importance": "primary",
            "description": "来自名字的元音,揭示你内心真正的渴望和动机。",
        })
    if personality and personality.get("personality_number", 0) > 0:
        core_numbers.append({
            "name": "人格数 (Personality)",
            "name_en": "Personality",
            "number": personality["personality_number"],
            "is_master": personality["personality_number"] in (11, 22, 33),
            "meaning": _number_profile(personality["personality_number"]),
            "importance": "secondary",
            "description": "来自名字的辅音,代表你在他人眼中的形象和第一印象。",
        })
    if maturity:
        core_numbers.append({
            "name": "成熟数 (Maturity)",
            "name_en": "Maturity",
            "number": maturity["maturity_number"],
            "is_master": maturity["maturity_number"] in (11, 22, 33),
            "meaning": _number_profile(maturity["maturity_number"]),
            "importance": "secondary",
            "description": "Life Path + Destiny,代表中年后逐渐展现的成熟力量。",
        })

    # 周期数字
    cycle_numbers = [
        {
            "name": "个人流年 (Personal Year)",
            "name_en": "Personal Year",
            "number": py["personal_year"],
            "year": py["personal_year_for"],
            "meaning": _number_profile(py["personal_year"]),
            "description": f"{py['personal_year_for']}年的主题能量,提示这一年的重点方向。",
        },
        {
            "name": "个人流月 (Personal Month)",
            "name_en": "Personal Month",
            "number": pm["personal_month"],
            "month": pm["personal_month_for"],
            "meaning": _number_profile(pm["personal_month"]),
            "description": f"{pm['personal_month_for']}的月度焦点,在流年大背景下细化当月行动。",
        },
    ]

    # 构建解读
    primary_number = life_path_profile
    primary_meaning = primary_number.get("strength", "")
    primary_challenge = primary_number.get("challenge", "")

    summary = (
        f"你的生命路径数为 {life_path}「{primary_number.get('title', '')}」——"
        f"{primary_meaning}"
    )

    return ChartResult(
        method="numerology",
        school="west",
        engine="self+pythagoras+v2",
        normalized={
            "elements": {},
            "timeline": [],
            "note": "数字命理不映射五行元素,以核心数字(core_numbers)和周期数字(cycle_numbers)为归一化指标",
        },
        raw={
            "rule_version": "v2",
            "life_path": life_path,
            "life_path_profile": life_path_profile,
            "birth_sum": lp["birth_sum"],
            "core_numbers": core_numbers,
            "cycle_numbers": cycle_numbers,
            "has_name_data": bool(name),
            "name_provided": name if name else None,
            "birthday_number": bd,
            "personal_year": py,
            "personal_month": pm,
            "destiny": destiny,
            "soul_urge": soul_urge,
            "personality": personality,
            "maturity": maturity,
            "calculation_basis": {
                "method": "numerology_pythagorean",
                "mode": "life_path",
                "rule_version": "v2",
                "input_source": "birth date (YYYYMMDD)" + (" + full name" if name else ""),
                "rule": "Pythagorean digit reduction, master numbers 11/22/33 preserved",
                "core_numbers_computed": len(core_numbers),
                "scope": (
                    "完整数字命理: Life Path, Birthday, "
                    + ("Destiny, Soul Urge, Personality, Maturity, " if name else "")
                    + "Personal Year, Personal Month"
                ),
                "limits": [
                    "名字仅支持英文(中文姓名数字转换体系不同,待实现)",
                    "Personal Year/Month 使用简化数学公式",
                    "未展开 Pinnacles/Challenges/Karmic Debt 等进阶分析",
                    "未包含 Essence/Transit 等动态周期",
                ] if name else [
                    "未提供名字,无法计算 Destiny/Soul Urge/Personality/Maturity 等名字相关数字",
                    "名字仅支持英文(中文姓名数字转换待实现)",
                    "Personal Year/Month 使用简化数学公式",
                    "未展开 Pinnacles/Challenges/Karmic Debt 等进阶分析",
                ],
            },
        },
    )
