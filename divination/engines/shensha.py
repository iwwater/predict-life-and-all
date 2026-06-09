"""神煞 (Symbolic Stars) system for Ba Zi.

Computes classical symbolic stars from pillar data, using classical lookup tables.
These stars dramatically improve interpretation accuracy by adding crucial context
about talent, relationships, danger periods, and life themes.

References: 渊海子平, 三命通会, 协纪辨方书
"""

# ── Constants ──────────────────────────────────────────────────────────────

ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

GAN_NAMES = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 日干 → 天乙贵人 (两处取: 阳贵+阴贵)
# Format: {日干: [贵人支1, 贵人支2]}
TIANYI_GUI_REN = {
    "甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"],
    "丁": ["亥", "酉"], "戊": ["丑", "未"], "己": ["子", "申"],
    "庚": ["丑", "未"], "辛": ["午", "寅"], "壬": ["卯", "巳"],
    "癸": ["卯", "巳"],
}
# 年干/日干 → 天乙贵人 (alternative lookup used by some schools)
TIANYI_BY_DAY = TIANYI_GUI_REN

# 月支 → 天德贵人 (used by month branch)
# Format: {月支: 天干}
TIAN_DE = {
    "寅": "丁", "卯": "申", "辰": "壬", "巳": "辛",
    "午": "亥", "未": "甲", "申": "癸", "酉": "寅",
    "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚",
}

# 月支 → 月德贵人 (used by month branch)
YUE_DE = {
    "寅": "丙", "卯": "甲", "辰": "壬", "巳": "庚",
    "午": "丙", "未": "甲", "申": "壬", "酉": "庚",
    "戌": "丙", "亥": "甲", "子": "壬", "丑": "庚",
}

# 日干 → 文昌贵人
WEN_CHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉",
    "戊": "申", "己": "酉", "庚": "亥", "辛": "子",
    "壬": "寅", "癸": "卯",
}

# 日干 → 学堂 (文昌的对冲位)
XUE_TANG = {
    "甲": "亥", "乙": "子", "丙": "寅", "丁": "卯",
    "戊": "寅", "己": "卯", "庚": "巳", "辛": "午",
    "壬": "申", "癸": "酉",
}

# 日支/年支 → 桃花 (咸池)
# 寅午戌→卯, 申子辰→酉, 亥卯未→子, 巳酉丑→午
TAO_HUA_MAP = {
    "寅": "卯", "午": "卯", "戌": "卯",
    "申": "酉", "子": "酉", "辰": "酉",
    "亥": "子", "卯": "子", "未": "子",
    "巳": "午", "酉": "午", "丑": "午",
}

# 年支 → 红鸾
HONG_LUAN = {
    "子": "卯", "丑": "寅", "寅": "丑", "卯": "子",
    "辰": "亥", "巳": "戌", "午": "酉", "未": "申",
    "申": "未", "酉": "午", "戌": "巳", "亥": "辰",
}

# 年支 → 天喜 (红鸾的对冲位)
TIAN_XI = {
    "子": "酉", "丑": "申", "寅": "未", "卯": "午",
    "辰": "巳", "巳": "辰", "午": "卯", "未": "寅",
    "申": "丑", "酉": "子", "戌": "亥", "亥": "戌",
}

# 日支/年支 → 驿马
# 寅午戌→申, 申子辰→寅, 亥卯未→巳, 巳酉丑→亥
YI_MA_MAP = {
    "寅": "申", "午": "申", "戌": "申",
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "巳", "卯": "巳", "未": "巳",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

# 日支/年支 → 华盖
# 寅午戌→戌, 申子辰→辰, 亥卯未→未, 巳酉丑→丑
HUA_GAI_MAP = {
    "寅": "戌", "午": "戌", "戌": "戌",
    "申": "辰", "子": "辰", "辰": "辰",
    "亥": "未", "卯": "未", "未": "未",
    "巳": "丑", "酉": "丑", "丑": "丑",
}

# 日支/年支 → 将星
# 寅午戌→午, 申子辰→子, 亥卯未→卯, 巳酉丑→酉
JIANG_XING_MAP = {
    "寅": "午", "午": "午", "戌": "午",
    "申": "子", "子": "子", "辰": "子",
    "亥": "卯", "卯": "卯", "未": "卯",
    "巳": "酉", "酉": "酉", "丑": "酉",
}

# 日干 → 羊刃 (阳干帝旺位 / 阴干禄位)
YANG_REN = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
    "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
    "壬": "子", "癸": "亥",
}

# 年支 → 劫煞
JIE_SHA = {
    "子": "巳", "丑": "寅", "寅": "亥", "卯": "申",
    "辰": "巳", "巳": "寅", "午": "亥", "未": "申",
    "申": "巳", "酉": "寅", "戌": "亥", "亥": "申",
}

# 年支 → 灾煞 (劫煞的对冲)
ZAI_SHA = {
    "子": "午", "丑": "卯", "寅": "子", "卯": "酉",
    "辰": "午", "巳": "卯", "午": "子", "未": "酉",
    "申": "午", "酉": "卯", "戌": "子", "亥": "酉",
}

# 日支 → 空亡 (旬空)
# Each 旬 (10-day stem cycle) has 2 empty branches
XUN_KONG = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
    "乙丑": ["戌", "亥"], "乙亥": ["申", "酉"], "乙酉": ["午", "未"],
    "乙未": ["辰", "巳"], "乙巳": ["寅", "卯"], "乙卯": ["子", "丑"],
    "丙寅": ["戌", "亥"], "丙子": ["申", "酉"], "丙戌": ["午", "未"],
    "丙申": ["辰", "巳"], "丙午": ["寅", "卯"], "丙辰": ["子", "丑"],
    "丁卯": ["戌", "亥"], "丁丑": ["申", "酉"], "丁亥": ["午", "未"],
    "丁酉": ["辰", "巳"], "丁未": ["寅", "卯"], "丁巳": ["子", "丑"],
    "戊辰": ["戌", "亥"], "戊寅": ["申", "酉"], "戊子": ["午", "未"],
    "戊戌": ["辰", "巳"], "戊申": ["寅", "卯"], "戊午": ["子", "丑"],
    "己巳": ["戌", "亥"], "己卯": ["申", "酉"], "己丑": ["午", "未"],
    "己亥": ["辰", "巳"], "己酉": ["寅", "卯"], "己未": ["子", "丑"],
    "庚午": ["戌", "亥"], "庚辰": ["申", "酉"], "庚寅": ["午", "未"],
    "庚子": ["辰", "巳"], "庚戌": ["寅", "卯"], "庚申": ["子", "丑"],
    "辛未": ["戌", "亥"], "辛巳": ["申", "酉"], "辛卯": ["午", "未"],
    "辛丑": ["辰", "巳"], "辛亥": ["寅", "卯"], "辛酉": ["子", "丑"],
    "壬申": ["戌", "亥"], "壬午": ["申", "酉"], "壬辰": ["午", "未"],
    "壬寅": ["辰", "巳"], "壬子": ["寅", "卯"], "壬戌": ["子", "丑"],
    "癸酉": ["戌", "亥"], "癸未": ["申", "酉"], "癸巳": ["午", "未"],
    "癸卯": ["辰", "巳"], "癸丑": ["寅", "卯"], "癸亥": ["子", "丑"],
}

# 日干 → 魁罡 (only 4 combinations)
KUI_GANG_PAIRS = {
    "庚辰": "魁罡", "庚戌": "魁罡", "壬辰": "魁罡", "戊戌": "魁罡",
}

# 年支 → 金舆
JIN_YU = {
    "子": "寅", "丑": "亥", "寅": "申", "卯": "巳",
    "辰": "申", "巳": "巳", "午": "申", "未": "亥",
    "申": "寅", "酉": "亥", "戌": "寅", "亥": "巳",
}

# 年支/日支 → 孤辰 (前一位)
GU_CHEN = {
    "亥": "寅", "子": "寅", "丑": "寅",
    "寅": "巳", "卯": "巳", "辰": "巳",
    "巳": "申", "午": "申", "未": "申",
    "申": "亥", "酉": "亥", "戌": "亥",
}

# 年支/日支 → 寡宿 (后一位)
GUA_SU = {
    "亥": "戌", "子": "戌", "丑": "戌",
    "寅": "丑", "卯": "丑", "辰": "丑",
    "巳": "辰", "午": "辰", "未": "辰",
    "申": "未", "酉": "未", "戌": "未",
}


# ── Helper ──────────────────────────────────────────────────────────────────

def _zhi_at(pillars: dict, label: str) -> str:
    """Extract the branch (地支) from a pillar's 干支."""
    gz = pillars.get(label, "")
    if len(gz) >= 2:
        return gz[1]
    return ""


def _gan_at(pillars: dict, label: str) -> str:
    """Extract the stem (天干) from a pillar's 干支."""
    gz = pillars.get(label, "")
    if len(gz) >= 1:
        return gz[0]
    return ""


def _find_star_in_pillars(
    target_zhi: str,
    pillars: dict,
    pillars_order: list[str] = None,
) -> list[str]:
    """Return which pillars contain the target branch."""
    if pillars_order is None:
        pillars_order = ["year", "month", "day", "hour"]
    found = []
    for label in pillars_order:
        if _zhi_at(pillars, label) == target_zhi:
            found.append(label)
    return found


# ── Individual Star Computations ────────────────────────────────────────────

def compute_tianyi(day_gan: str, year_zhi: str, pillars: dict) -> list[dict]:
    """天乙贵人 — the most important benefic star. Uses day stem as primary."""
    results = []
    branches = TIANYI_GUI_REN.get(day_gan, [])
    for zhi in branches:
        for label in _find_star_in_pillars(zhi, pillars):
            results.append({
                "star": "天乙贵人",
                "category": "吉",
                "found_in": label,
                "branch": zhi,
                "meaning": (
                    "逢凶化吉之贵人星。主遇难有贵人相助、人际关系圆满。"
                    f"日干{day_gan}见{zhi}为贵人。"
                ),
                "score": 8,
            })
    return results


def compute_tiande(month_zhi: str, pillars: dict) -> list[dict]:
    """天德贵人 — month-based benefic star, strongest protection."""
    gan = TIAN_DE.get(month_zhi, "")
    if not gan:
        return []
    results = []
    for label in ["year", "month", "day", "hour"]:
        if _gan_at(pillars, label) == gan:
            results.append({
                "star": "天德贵人",
                "category": "吉",
                "found_in": label,
                "stem": gan,
                "meaning": (
                    f"上天的德泽。月{month_zhi}见天干{gan}为天德。"
                    "主一生少灾祸、福泽深厚、心地善良。"
                ),
                "score": 9,
            })
    return results


def compute_yuede(month_zhi: str, pillars: dict) -> list[dict]:
    """月德贵人 — month-based benefic star, complements 天德."""
    gan = YUE_DE.get(month_zhi, "")
    if not gan:
        return []
    results = []
    for label in ["year", "month", "day", "hour"]:
        if _gan_at(pillars, label) == gan:
            results.append({
                "star": "月德贵人",
                "category": "吉",
                "found_in": label,
                "stem": gan,
                "meaning": (
                    f"月亮的德泽。月{month_zhi}见天干{gan}为月德。"
                    "主人际关系顺遂、女命尤吉。"
                ),
                "score": 7,
            })
    return results


def compute_wenchang(day_gan: str, pillars: dict) -> list[dict]:
    """文昌贵人 — literary/academic talent star."""
    zhi = WEN_CHANG.get(day_gan, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "文昌贵人",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": f"文采出众、考试运佳。日干{day_gan}见{zhi}为文昌。主聪明好学、文笔出众。",
            "score": 6,
        })
    return results


def compute_xuetang(day_gan: str, pillars: dict) -> list[dict]:
    """学堂 — scholastic aptitude, complements 文昌."""
    zhi = XUE_TANG.get(day_gan, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "学堂",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": f"天生好学的根基。日干{day_gan}见{zhi}为学堂。主学业顺利、有学术天赋。",
            "score": 5,
        })
    return results


def compute_taohua(year_zhi: str, pillars: dict) -> list[dict]:
    """桃花(咸池) — romance/attraction star."""
    zhi = TAO_HUA_MAP.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "桃花",
            "star_alt": "咸池",
            "category": "中性",
            "found_in": label,
            "branch": zhi,
            "meaning": (
                f"年支{year_zhi}见{zhi}为桃花。主人缘好、有魅力、异性缘强。"
                f"在{label}柱: {'早年(年)' if label == 'year' else '中年(月)' if label == 'month' else '自身(日)' if label == 'day' else '晚年(时)'}桃花运。"
            ),
            "score": 3,
        })
    return results


def compute_hongluan(year_zhi: str, pillars: dict) -> list[dict]:
    """红鸾 — marriage/romance indicator."""
    zhi = HONG_LUAN.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "红鸾",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": f"年支{year_zhi}见{zhi}为红鸾。主正缘、婚庆、喜事临门。",
            "score": 5,
        })
    return results


def compute_tianxi(year_zhi: str, pillars: dict) -> list[dict]:
    """天喜 — complements 红鸾, joy indicator."""
    zhi = TIAN_XI.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "天喜",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": f"年支{year_zhi}见{zhi}为天喜。主喜庆、好运、添丁进口。",
            "score": 4,
        })
    return results


def compute_yima(year_zhi: str, pillars: dict) -> list[dict]:
    """驿马 — travel/movement/career change star."""
    zhi = YI_MA_MAP.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "驿马",
            "category": "中性",
            "found_in": label,
            "branch": zhi,
            "meaning": (
                f"年支{year_zhi}见{zhi}为驿马。主奔波、走动、迁移、职业变动。"
                "动中求财,宜从事外勤、交通、贸易等需移动之职业。"
            ),
            "score": 4,
        })
    return results


def compute_huagai(year_zhi: str, pillars: dict) -> list[dict]:
    """华盖 — artistic/spiritual/creative talent."""
    zhi = HUA_GAI_MAP.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "华盖",
            "category": "中性",
            "found_in": label,
            "branch": zhi,
            "meaning": (
                f"年支{year_zhi}见{zhi}为华盖。主艺术才华、宗教玄学天赋、"
                "特立独行。聪明而可能孤独。"
            ),
            "score": 5,
        })
    return results


def compute_jiangxing(year_zhi: str, pillars: dict) -> list[dict]:
    """将星 — leadership/authority star."""
    zhi = JIANG_XING_MAP.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "将星",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": (
                f"年支{year_zhi}见{zhi}为将星。主领导才能、掌控力强、"
                "适合管理岗位、军警、企业高管。"
            ),
            "score": 7,
        })
    return results


def compute_yangren(day_gan: str, pillars: dict) -> list[dict]:
    """羊刃 — the blade star, both power and danger."""
    zhi = YANG_REN.get(day_gan, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "羊刃",
            "category": "凶",
            "found_in": label,
            "branch": zhi,
            "meaning": (
                f"日干{day_gan}见{zhi}为羊刃(帝旺/禄位)。主性格刚烈果断、"
                "执行力强但易冲动。宜武职、外科等需要果断的行业。"
                "忌投资冒进,需防意外伤害或手术。"
            ),
            "score": -4,
        })
    return results


def compute_jiesha(year_zhi: str, pillars: dict) -> list[dict]:
    """劫煞 — robbery/disaster indicator."""
    zhi = JIE_SHA.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "劫煞",
            "category": "凶",
            "found_in": label,
            "branch": zhi,
            "meaning": f"年支{year_zhi}见{zhi}为劫煞。主波折、意外、人事纠纷。需防破财和意外。",
            "score": -5,
        })
    return results


def compute_zaisha(year_zhi: str, pillars: dict) -> list[dict]:
    """灾煞 — disaster indicator."""
    zhi = ZAI_SHA.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "灾煞",
            "category": "凶",
            "found_in": label,
            "branch": zhi,
            "meaning": f"年支{year_zhi}见{zhi}为灾煞。主突发灾难、疾病、官非。需特别注意安全。",
            "score": -6,
        })
    return results


def compute_xunkong(day_pillar_ganzhi: str, pillars: dict) -> list[dict]:
    """空亡 — void/emptiness based on 旬空 from day pillar."""
    if not day_pillar_ganzhi or len(day_pillar_ganzhi) < 2:
        return []
    # Find which 旬 group the day pillar falls in
    day_gan = day_pillar_ganzhi[0]
    day_zhi = day_pillar_ganzhi[1]
    # Use the standard lookup by full 干支
    kong_zhi_list = XUN_KONG.get(day_pillar_ganzhi, [])
    results = []
    for kong_zhi in kong_zhi_list:
        for label in _find_star_in_pillars(kong_zhi, pillars):
            results.append({
                "star": "空亡",
                "category": "凶",
                "found_in": label,
                "branch": kong_zhi,
                "meaning": (
                    f"日柱{day_pillar_ganzhi}所在旬空{zhi_list_str(kong_zhi_list)}。"
                    f"{label}柱落空亡: 该柱所代表的人事物易有不实、落空之感。"
                    "空亡亦代表玄学/宗教天赋。"
                ),
                "score": -3,
            })
    return results


def zhi_list_str(zhi_list: list[str]) -> str:
    return "、".join(zhi_list)


def compute_kuigang(day_ganzhi: str) -> list[dict]:
    """魁罡 — special star for 庚辰, 庚戌, 壬辰, 戊戌 day pillars."""
    star = KUI_GANG_PAIRS.get(day_ganzhi, "")
    if not star:
        return []
    return [{
        "star": "魁罡",
        "category": "中性",
        "found_in": "day",
        "ganzhi": day_ganzhi,
        "meaning": (
            f"日柱{day_ganzhi}为魁罡。主聪明果断、不怒自威、做事有魄力。"
            "天赋领导力但也可能过于刚强。女命魁罡多为女强人。"
        ),
        "score": 6,
    }]


def compute_jinyu(year_zhi: str, pillars: dict) -> list[dict]:
    """金舆 — golden carriage, wealth/vehicle star."""
    zhi = JIN_YU.get(year_zhi, "")
    if not zhi:
        return []
    results = []
    for label in _find_star_in_pillars(zhi, pillars):
        results.append({
            "star": "金舆",
            "category": "吉",
            "found_in": label,
            "branch": zhi,
            "meaning": f"年支{year_zhi}见{zhi}为金舆。主财运好、有车房之喜、出行顺利。",
            "score": 4,
        })
    return results


def compute_guchen_guasu(year_zhi: str, pillars: dict) -> list[dict]:
    """孤辰 + 寡宿 — loneliness indicators."""
    results = []
    gu_zhi = GU_CHEN.get(year_zhi, "")
    gua_zhi = GUA_SU.get(year_zhi, "")
    for label in _find_star_in_pillars(gu_zhi, pillars) if gu_zhi else []:
        results.append({
            "star": "孤辰",
            "category": "凶",
            "found_in": label,
            "branch": gu_zhi,
            "meaning": f"年支{year_zhi}见{gu_zhi}为孤辰。主性格独立、可能晚婚、人际疏离。宜培养社交。",
            "score": -2,
        })
    for label in _find_star_in_pillars(gua_zhi, pillars) if gua_zhi else []:
        results.append({
            "star": "寡宿",
            "category": "凶",
            "found_in": label,
            "branch": gua_zhi,
            "meaning": f"年支{year_zhi}见{gua_zhi}为寡宿。主性格孤僻、不善表达情感。宜培养亲密关系能力。",
            "score": -2,
        })
    return results


# ── Master Computation ─────────────────────────────────────────────────────

def compute_all(pillars: dict, day_master: str = None) -> dict:
    """Compute all applicable 神煞 for a Ba Zi chart.

    Args:
        pillars: {"year": "庚午", "month": "辛巳", "day": "庚辰", "hour": "庚辰"}
        day_master: The day stem (日干), e.g. "庚"

    Returns:
        {
            "stars": [ {star, category, found_in, branch/stem, meaning, score}, ... ],
            "summary": {
                "auspicious_count": N, "neutral_count": N, "inauspicious_count": N,
                "total_score": N,  # overall beneficence
                "notable": ["star1", "star2"],  # highest impact stars
            }
        }
    """
    if not pillars or len(pillars) < 4:
        return {"stars": [], "summary": {}}

    year_zhi = _zhi_at(pillars, "year")
    month_zhi = _zhi_at(pillars, "month")
    day_ganzhi = pillars.get("day", "")

    # Day master can be provided or extracted
    if not day_master:
        day_master = _gan_at(pillars, "day")

    all_stars = []

    # --- 吉神 (Auspicious) ---
    if day_master:
        all_stars.extend(compute_tianyi(day_master, year_zhi, pillars))
        all_stars.extend(compute_wenchang(day_master, pillars))
        all_stars.extend(compute_xuetang(day_master, pillars))
        all_stars.extend(compute_yangren(day_master, pillars))  # neutral/凶 in category
    if month_zhi:
        all_stars.extend(compute_tiande(month_zhi, pillars))
        all_stars.extend(compute_yuede(month_zhi, pillars))
    if year_zhi:
        all_stars.extend(compute_hongluan(year_zhi, pillars))
        all_stars.extend(compute_tianxi(year_zhi, pillars))
        all_stars.extend(compute_jiangxing(year_zhi, pillars))
        all_stars.extend(compute_jinyu(year_zhi, pillars))
        # 中性
        all_stars.extend(compute_taohua(year_zhi, pillars))
        all_stars.extend(compute_yima(year_zhi, pillars))
        all_stars.extend(compute_huagai(year_zhi, pillars))
        # 凶
        all_stars.extend(compute_jiesha(year_zhi, pillars))
        all_stars.extend(compute_zaisha(year_zhi, pillars))
        all_stars.extend(compute_guchen_guasu(year_zhi, pillars))
    if day_ganzhi:
        all_stars.extend(compute_xunkong(day_ganzhi, pillars))
        all_stars.extend(compute_kuigang(day_ganzhi))

    # Deduplicate by star name + pillar
    seen = set()
    unique = []
    for s in all_stars:
        key = (s["star"], s.get("found_in", ""))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    # Sort: high score first
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Summary
    auspicious = [s for s in unique if s["category"] == "吉"]
    neutral = [s for s in unique if s["category"] == "中性"]
    inauspicious = [s for s in unique if s["category"] == "凶"]
    total_score = sum(s.get("score", 0) for s in unique)
    notable = [s["star"] for s in unique if abs(s.get("score", 0)) >= 5]

    return {
        "stars": unique,
        "summary": {
            "total_count": len(unique),
            "auspicious_count": len(auspicious),
            "neutral_count": len(neutral),
            "inauspicious_count": len(inauspicious),
            "total_score": total_score,
            "notable": notable,
            "auspicious_stars": [s["star"] for s in auspicious],
            "inauspicious_stars": [s["star"] for s in inauspicious],
        },
    }
