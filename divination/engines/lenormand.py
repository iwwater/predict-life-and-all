"""Lenormand (雷诺曼) 36-card oracle engine.

与塔罗的关键区别:
- 36 张牌, 每张有确定的具体含义 (非心理原型)
- 无逆位 — 传统雷诺曼不使用逆位
- 牌义高度依赖邻近牌的修饰 (组合解读)
- Grand Tableau (全阵 36 张) 是雷诺曼的核心阵型
- 更偏向"日常占卜"而非心理探索

牌义来源: 传统 Petit Lenormand 体系 (1799), 融合法国/德国学派。
"""

import hashlib
from datetime import date

from ..contracts import Birth, ChartResult

# ═══════════════════════════════════════════════════════════════
# 1. 36-Card Lenormand Deck
# ═══════════════════════════════════════════════════════════════
# (编号, 牌名, 中文名, 花色, 核心含义, 扩展含义, 时间指示)

LENORMAND_DECK = [
    (1,  "Rider",       "骑士",   "♠9", "消息、来者、运动、新事物", "访客、快递、开始一段旅程、情况将动起来", "快速/即将"),
    (2,  "Clover",      "三叶草", "♦6", "幸运、小确幸、机会、乐观", "短暂的好运、抓住时机、第二张牌的机会", "短期/数日"),
    (3,  "Ship",        "船",     "♠10","旅程、远行、探索、过渡", "出国、搬迁、职业生涯变动、欲望/渴望", "中长期"),
    (4,  "House",       "房子",   "♥K", "家、稳定、安全、根基", "家庭事务、房地产、舒适区、传统", "长期/稳定"),
    (5,  "Tree",        "树",     "♥7", "健康、生长、扎根、因果", "生命力、慢性病/康复、家族树、耐心", "缓慢/持久"),
    (6,  "Clouds",      "云",     "♣K", "困惑、不明、阴霾、不确定", "焦虑、误解、一时的困境、云会散", "模糊/过渡"),
    (7,  "Snake",       "蛇",     "♣Q", "欺骗、复杂、聪明、绕路", "第三者、背叛、智慧、绕开障碍", "中期/迂回"),
    (8,  "Coffin",      "棺材",   "♦9", "结束、终结、放下、转型", "死亡(象征性的)、了结一件事、大休息", "终结/转折"),
    (9,  "Bouquet",     "花束",   "♠Q", "礼物、赞美、邀请、愉悦", "社交场合的愉快、收到花/礼、外表魅力", "当下/愉快"),
    (10, "Scythe",      "镰刀",   "♦J", "切割、决断、危险、收获", "骤然的结束、手术、果断行动、收割成果", "突然/瞬间"),
    (11, "Whip",        "鞭子",   "♣J", "冲突、重复、争论、纪律", "口角、来回拉扯、身体活动/运动、强迫症", "反复/持续"),
    (12, "Birds",       "鸟",     "♦7", "交谈、焦虑、沟通、流言", "电话/消息、紧张、一对伴侣、社交媒体的讯息", "短期/叽喳"),
    (13, "Child",       "小孩",   "♠J", "开始、天真、新阶段、小", "孩子、新项目启动、不成熟、纯真的视角", "新生/开始"),
    (14, "Fox",         "狐狸",   "♣9", "狡猾、警惕、自保、谋略", "职场政治、小心被利用、聪明地解决、误判", "中期/谨慎"),
    (15, "Bear",        "熊",     "♣10","力量、权威、保护、母亲", "老板/上级、财务力量、保护者、嫉妒/占有", "长期/强势"),
    (16, "Stars",       "星星",   "♥6", "希望、指引、清晰、目标", "梦想、电子/科技、网络、灵感闪烁", "缓慢明朗"),
    (17, "Stork",       "鹳",     "♥Q", "转变、搬迁、升级、新生", "搬家、换工作、怀孕/新成员、进步", "中期/转变"),
    (18, "Dog",         "狗",     "♥10","忠诚、朋友、信任、陪伴", "挚友/伴侣、可靠、无条件的支持、依赖", "长期/稳定"),
    (19, "Tower",       "高塔",   "♠6", "孤独、权威、界限、机构", "政府/大公司、独自、长寿、隔离、法院", "长期/孤立"),
    (20, "Garden",      "花园",   "♠8", "社交、公开、名声、圈子", "聚会、被人看见、社交媒体、公共场合", "中期/公开"),
    (21, "Mountain",    "山",     "♣8", "障碍、延迟、卡住、挑战", "巨大的阻力、需要毅力、不可逾越(暂时)", "缓慢/延迟"),
    (22, "Crossroads",  "十字路口","♦Q", "选择、岔路、多线、自由", "决定时刻、多选项、流浪/迷失、自由意志", "决策期"),
    (23, "Mice",        "老鼠",   "♣7", "侵蚀、损耗、偷窃、焦虑", "东西坏了/丢了、小人损耗、慢性压力、减少", "逐渐/侵蚀"),
    (24, "Heart",       "心",     "♥J", "爱、感情、仁慈、核心", "恋情、热爱的事业、修复关系、心脏/情感", "当下/情感"),
    (25, "Ring",        "戒指",   "♣A", "承诺、契约、循环、约定", "婚姻/订婚、合同、循环模式、业力", "长期/约定"),
    (26, "Book",        "书",     "♦10","秘密、知识、学习、隐藏", "研究、尚不知晓的事、教育/课程、项目", "学习期"),
    (27, "Letter",      "信",     "♠7", "消息、文件、证书、沟通", "邮件/短信、文凭、书面确认、新闻", "短期/送达"),
    (28, "Man",         "男人",   "♥A", "男性、主动方、阳性能量", "求测者若是男性则为此牌、丈夫/男友/父亲", "当下"),
    (29, "Woman",       "女人",   "♠A", "女性、接收方、阴性能量", "求测者若是女性则为此牌、妻子/女友/母亲", "当下"),
    (30, "Lily",        "百合",   "♠K", "平静、成熟、智慧、德行", "长者、性/感官、退休、冬日的宁静", "长期/缓慢"),
    (31, "Sun",         "太阳",   "♦A", "成功、活力、胜利、光明", "大奖、认可、幸福、温暖的能量", "当下/光明"),
    (32, "Moon",        "月亮",   "♥8", "名声、直觉、情感、周期", "荣誉/认可、创作、潜意识的讯息、周期", "月周期"),
    (33, "Key",         "钥匙",   "♦8", "开启、答案、重要、解锁", "解决方案、关键人物/事件、YES 的确信", "解锁时"),
    (34, "Fish",        "鱼",     "♦K", "财富、生意、流动、丰盛", "金钱/收入、现金流、自由职业、深层情感", "流动/持续"),
    (35, "Anchor",      "锚",     "♠9", "稳定、安全、坚持、不变", "长期工作、稳固的关系、不轻易动摇", "长期/稳固"),
    (36, "Cross",       "十字架", "♣6", "命运、功课、考验、信念", "命中注定的课题、宗教/灵性、负担的意义", "长期/命运"),
]

# Build lookup
LENORMAND_BY_NAME = {name_en: (num, name_en, zh, suit, core, extended, timing)
                     for num, name_en, zh, suit, core, extended, timing in LENORMAND_DECK}
LENORMAND_BY_NUM = {num: (name_en, zh, suit, core, extended, timing)
                    for num, name_en, zh, suit, core, extended, timing in LENORMAND_DECK}
LENORMAND_NAMES = [name_en for _, name_en, _, _, _, _, _ in LENORMAND_DECK]


# ═══════════════════════════════════════════════════════════════
# 2. Spread Definitions
# ═══════════════════════════════════════════════════════════════
SPREADS = {
    "single": {
        "name": "单张指引",
        "description": "一张牌快速回应一个具体问题或今日主题。",
        "card_count": 1,
        "subjects": ["lenormand_guidance", "decision"],
        "time_budget": "quick",
        "positions": ["核心讯息"],
    },
    "three_line": {
        "name": "三张线",
        "description": "过去→现在→未来或主题→展开→结果。雷诺曼最经典的快阵。",
        "card_count": 3,
        "subjects": ["decision", "lenormand_guidance", "career", "relationship"],
        "time_budget": "quick",
        "positions": ["左/过去/主题", "中/现在/展开", "右/未来/结果"],
    },
    "five_cross": {
        "name": "五张十字",
        "description": "中心牌是议题核心, 上下左右四张补充方向。适合中等深度议题。",
        "card_count": 5,
        "subjects": ["decision", "career", "relationship"],
        "time_budget": "reflective",
        "positions": ["上方/显意识", "左方/过去", "中心/核心", "右方/未来", "下方/潜意识"],
    },
    "nine_square": {
        "name": "九宫格",
        "description": "3×3 方阵, 从八个方向围绕核心牌展开全景。适合全面审视一个议题。",
        "card_count": 9,
        "subjects": ["career", "relationship", "self_life"],
        "time_budget": "reflective",
        "positions": [
            "左上/远因", "上/显意识", "右上/近未来",
            "左/过去", "中/核心", "右/未来",
            "左下/隐因", "下/潜意识", "右下/远期趋势",
        ],
    },
    "grand_tableau": {
        "name": "大桌阵 (Grand Tableau)",
        "description": "36 张全牌按 4×8+4 铺开——雷诺曼最完整的阵型。适合人生全貌或重大转折。",
        "card_count": 36,
        "subjects": ["self_life", "career", "relationship"],
        "time_budget": "deep",
        "positions": [],  # 动态生成
    },
}

ALIASES = {"three": "three_line", "five": "five_cross", "nine": "nine_square", "gt": "grand_tableau"}

# ═══════════════════════════════════════════════════════════════
# 3. Spread Recommendation
# ═══════════════════════════════════════════════════════════════
SPREAD_MATRIX = {
    "lenormand_guidance": {
        "default": "three_line",
        "by_budget": {"quick": "single", "reflective": "three_line", "deep": "nine_square"},
    },
    "decision": {
        "default": "three_line",
        "by_budget": {"quick": "three_line", "reflective": "five_cross", "deep": "nine_square"},
    },
    "career": {
        "default": "five_cross",
        "by_budget": {"quick": "three_line", "reflective": "five_cross", "deep": "grand_tableau"},
    },
    "relationship": {
        "default": "five_cross",
        "by_budget": {"quick": "three_line", "reflective": "five_cross", "deep": "nine_square"},
    },
    "self_life": {
        "default": "nine_square",
        "by_budget": {"quick": "three_line", "reflective": "nine_square", "deep": "grand_tableau"},
    },
}


def _default_spread(subject: str, time_budget: str = "reflective") -> str:
    matrix = SPREAD_MATRIX.get(subject)
    if matrix:
        if time_budget in matrix.get("by_budget", {}):
            return matrix["by_budget"][time_budget]
        return matrix["default"]
    return "three_line"


def recommend_spread(subject: str, time_budget: str = "reflective") -> dict:
    spread_key = _default_spread(subject, time_budget)
    spread = SPREADS.get(spread_key, SPREADS["three_line"])
    return {
        "subject": subject,
        "time_budget": time_budget,
        "spread": spread_key,
        "spread_name": spread["name"],
        "spread_description": spread.get("description", ""),
        "card_count": spread["card_count"],
    }


# ═══════════════════════════════════════════════════════════════
# 4. Card Combination Logic (核心: 雷诺曼的灵魂在"组合")
# ═══════════════════════════════════════════════════════════════
def _combo_meaning(card_a: dict, card_b: dict) -> str:
    """两张相邻牌的修饰关系: 第一张是名词(主题),第二张是形容词(修饰)。"""
    name_a = card_a["name"]
    name_b = card_b["name"]
    # 经典的雷诺曼组合规则: Rider + 某 = 某消息来了; 某 + Ship = 某的旅程; ...
    combos = {
        ("骑士", "三叶草"): "好消息即将到来",
        ("骑士", "云"): "消息模糊不清, 暂缓判断",
        ("骑士", "心"): "一个浪漫的邀约或表白在靠近",
        ("骑士", "信"): "一封重要的信件/邮件即将到达",
        ("船", "房子"): "搬迁或长途归家",
        ("船", "山"): "旅行受阻或延误",
        ("房子", "鹳"): "住所升级或搬家",
        ("房子", "老鼠"): "房屋有破损或漏财",
        ("树", "棺材"): "健康问题需要重视; 或一棵树正在死去",
        ("云", "太阳"): "迷雾即将散去, 真相浮现",
        ("蛇", "狐狸"): "复杂的欺骗或职场陷阱",
        ("蛇", "戒指"): "一段有毒的关系承诺",
        ("花束", "戒指"): "求婚或美好的合约",
        ("心", "戒指"): "婚姻或深度情感承诺",
        ("心", "信"): "一封情书或动人的消息",
        ("镰刀", "树"): "手术或切断一段根源",
        ("镰刀", "心"): "心碎或关系的突然结束",
        ("鞭子", "心"): "反复的情感冲突",
        ("鸟", "信"): "电话或社交媒体上的重要消息",
        ("狐狸", "鱼"): "财务上的聪明操作(或骗局)",
        ("熊", "鱼"): "强大的财务实力",
        ("星星", "钥匙"): "答案是 YES, 方向明确",
        ("鹳", "小孩"): "怀孕或新成员的到来",
        ("狗", "心"): "忠诚的爱情或挚友",
        ("高塔", "十字架"): "孤立的考验或机构性的负担",
        ("花园", "花束"): "公开的荣誉或社交上的成功",
        ("山", "钥匙"): "障碍将被解锁",
        ("老鼠", "鱼"): "财务上的损耗或小偷",
        ("十字路口", "星星"): "选择已被指引",
        ("太阳", "钥匙"): "毫无疑问的 YES, 巨大的成功",
        ("月亮", "星星"): "创意工作被认可, 名声上升",
        ("锚", "鱼"): "长期稳定的财富积累",
    }
    key = (name_a, name_b)
    if key in combos:
        return combos[key]
    # Fallback: basic description
    return f"{card_a.get('core', '')} + {card_b.get('core', '')}"


def _analyze_tableau(cards: list[dict]) -> dict:
    """分析牌阵: 组合解读、关键牌位置、阳性/阴性牌比例。"""
    positive_cards = {"三叶草", "花束", "星星", "太阳", "钥匙", "心", "狗", "房子", "花园", "鱼", "锚", "鹳", "小孩", "百合"}
    negative_cards = {"云", "蛇", "棺材", "镰刀", "鞭子", "狐狸", "山", "老鼠", "十字架"}

    pos_count = sum(1 for c in cards if c["name"] in positive_cards)
    neg_count = sum(1 for c in cards if c["name"] in negative_cards)
    neutral_count = len(cards) - pos_count - neg_count

    # Adjacent pair interactions
    pairs = []
    for i in range(len(cards) - 1):
        pairs.append({
            "card_a": cards[i]["name"],
            "card_b": cards[i + 1]["name"],
            "combined": _combo_meaning(cards[i], cards[i + 1]),
        })

    # Key card locations (if in Grand Tableau)
    key_cards = {}
    for i, c in enumerate(cards):
        if c["name"] in {"男人", "女人", "心", "戒指", "钥匙", "太阳", "十字架"}:
            key_cards[c["name"]] = {"position": i + 1, "row": (i // 8) + 1, "col": (i % 8) + 1}

    return {
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_count": neutral_count,
        "tone": "positive" if pos_count > neg_count else ("negative" if neg_count > pos_count else "neutral"),
        "pairs": pairs,
        "key_card_positions": key_cards,
    }


# ═══════════════════════════════════════════════════════════════
# 5. Grand Tableau (36 张全牌 9×4 方阵) — 数据驱动, 纯函数
# ═══════════════════════════════════════════════════════════════

# Grand Tableau 宫位定义: 9 列 × 4 行 = 36 位置 (1-indexed, 左→右, 上→下)
# 各宫位按传统 Grand Tableau 含义预设为查找表
_GT_HOUSE_MEANINGS: dict[int, str] = {
    1: "自我/求测者核心", 2: "财务/价值观", 3: "沟通/短途", 4: "家庭/根基",
    5: "恋情/创造力", 6: "日常工作/健康", 7: "伴侣/合作", 8: "共享资源/深层",
    9: "远行/信仰/高等心智",
    10: "事业/社会地位", 11: "群体/愿望", 12: "潜意识/隐秘",
    13: "新开始/自我层深层", 14: "金钱/资源深层", 15: "思想/信息深层",
    16: "家宅/房产深层", 17: "爱情/创造性深层", 18: "日常/服务深层",
    19: "伴侣/契约深层", 20: "隐秘/转换深层", 21: "哲学/远见深层",
    22: "事业方向/使命深层", 23: "社交圈/人际深层", 24: "业力/潜意识底层",
    25: "命运/关键转折", 26: "结局/定数", 27: "信息终局",
    28: "根基/家族业力", 29: "财务终局/遗产", 30: "思想终局/智慧",
    31: "家宅终局/归宿", 32: "情感终局/真爱", 33: "健康终局/养生",
    34: "合作终局/婚姻", 35: "深层终局/灵魂", 36: "命运终局/业果",
}

# 心智宫位: 位置1-18 (上半+中上, 代表意识/思维层面)
_GT_MIND_PALACE_POSITIONS: frozenset[int] = frozenset(range(1, 19))

# 基础宫位: 位置19-36 (下半, 代表潜意识/根基/业力层面)
_GT_FOUNDATION_PALACE_POSITIONS: frozenset[int] = frozenset(range(19, 37))

# 四角: 左上(1), 右上(9), 左下(28), 右下(36)
_GT_CORNERS: tuple[int, int, int, int] = (1, 9, 28, 36)

# 中心四张: 9×4 网格的几何中心周围 4 张
# 几何中心在 row 1.5 (0-indexed) 即 rows 1-2, col 4.0 即 cols 4-5
# 中心4 = 位置 (row1,col4)=pos14, (row1,col5)=pos15, (row2,col4)=pos23, (row2,col5)=pos24
_GT_CENTER_FOUR: tuple[int, int, int, int] = (14, 15, 23, 24)

# 十字轴: 中心行(row2=pos19-27) + 中心列(col5=pos5,14,23,32)
_GT_CROSS_ROW: frozenset[int] = frozenset(range(19, 28))   # 第三行
_GT_CROSS_COL: frozenset[int] = frozenset({5, 14, 23, 32})  # 第六列

# 宫位分组 — 数据驱动，纯查表
_GT_HOUSE_GROUPS: dict[str, frozenset[int]] = {
    "心智宫": _GT_MIND_PALACE_POSITIONS,
    "基础宫": _GT_FOUNDATION_PALACE_POSITIONS,
    "四角": frozenset(_GT_CORNERS),
    "中心": frozenset(_GT_CENTER_FOUR),
    "十字横轴": _GT_CROSS_ROW,
    "十字纵轴": _GT_CROSS_COL,
}


def _linear_to_row_col(pos_1indexed: int, cols: int = 9) -> tuple[int, int]:
    """将 1-indexed 位置转为 (row, col) 0-indexed。"""
    idx = pos_1indexed - 1
    return idx // cols, idx % cols


def _get_neighbors(pos_1indexed: int, rows: int = 4, cols: int = 9) -> dict[str, int | None]:
    """获取某位置的正交邻近位置 (上下左右)，纯函数查表。

    Returns:
        {"up": pos|None, "down": pos|None, "left": pos|None, "right": pos|None}
    """
    r, c = _linear_to_row_col(pos_1indexed, cols)
    neighbors: dict[str, int | None] = {}
    # 上
    neighbors["up"] = pos_1indexed - cols if r > 0 else None
    # 下
    neighbors["down"] = pos_1indexed + cols if r < rows - 1 else None
    # 左
    neighbors["left"] = pos_1indexed - 1 if c > 0 else None
    # 右
    neighbors["right"] = pos_1indexed + 1 if c < cols - 1 else None
    return neighbors


def _get_diagonal_neighbors(pos_1indexed: int, rows: int = 4, cols: int = 9) -> dict[str, int | None]:
    """获取对角线邻近位置。"""
    r, c = _linear_to_row_col(pos_1indexed, cols)
    diag: dict[str, int | None] = {}
    diag["ul"] = pos_1indexed - cols - 1 if r > 0 and c > 0 else None
    diag["ur"] = pos_1indexed - cols + 1 if r > 0 and c < cols - 1 else None
    diag["dl"] = pos_1indexed + cols - 1 if r < rows - 1 and c > 0 else None
    diag["dr"] = pos_1indexed + cols + 1 if r < rows - 1 and c < cols - 1 else None
    return diag


def _get_knights(pos_1indexed: int, rows: int = 4, cols: int = 9) -> list[int]:
    """获取骑士步位置 (L形: ±2行±1列 or ±1行±2列)。"""
    r, c = _linear_to_row_col(pos_1indexed, cols)
    moves = [
        (-2, -1), (-2, 1), (2, -1), (2, 1),
        (-1, -2), (-1, 2), (1, -2), (1, 2),
    ]
    positions: list[int] = []
    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            positions.append(nr * cols + nc + 1)  # back to 1-indexed
    return positions


def compute_grand_tableau(cards: list[dict]) -> dict:
    """计算 36 张全牌 Grand Tableau 的完整宫位分析。

    输入 36 张牌（按 9×4 方阵排列，行优先 1→36），返回：
      - grid: 9×4 阵列表 (list of 4 rows, each row 9 cards)
      - center_four: 中心四张牌的详情
      - corners: 四角牌的详情
      - mind_palace: 心智宫位 (上半 1-18 位置) 牌汇总
      - foundation_palace: 基础宫位 (下半 19-36 位置) 牌汇总
      - cross_analysis: 十字轴 (第三行 + 第六列) 分析
      - house_positions: 关键宫位牌映射 (significator, heart, ring 等)
      - adjacency_modifiers: 每张牌的邻近修饰关系
      - mansion_groups: 按宫位群组汇总 (心智/基础/四角/中心)
      - summary: 总览摘要

    纯函数，数据驱动，无 if-elif 堆叠。
    """
    if len(cards) != 36:
        return {"error": f"Grand Tableau requires 36 cards, got {len(cards)}"}

    # ── 构建 9×4 网格 ──
    # 行优先: pos 1-9=row0, 10-18=row1, 19-27=row2, 28-36=row3
    rows = 4
    cols = 9
    grid_rows = [cards[i * cols:(i + 1) * cols] for i in range(rows)]

    # 位置索引映射: pos_1indexed -> card
    card_by_pos: dict[int, dict] = {}
    for i, card in enumerate(cards):
        card_by_pos[i + 1] = card

    # ── 宫位含义映射 — 数据驱动查表 ──
    house_positions: dict[str, dict] = {}
    for pos, meaning in _GT_HOUSE_MEANINGS.items():
        card = card_by_pos.get(pos)
        if card:
            house_positions[str(pos)] = {
                "position": pos,
                "meaning": meaning,
                "card_name": card["name"],
                "card_name_zh": card.get("name_zh", ""),
                "row": (pos - 1) // cols + 1,
                "col": (pos - 1) % cols + 1,
            }

    # ── 中心四张 ──
    center_four = {
        "positions": list(_GT_CENTER_FOUR),
        "cards": [
            {
                "position": p,
                "name": card_by_pos[p]["name"] if p in card_by_pos else None,
                "name_zh": card_by_pos[p].get("name_zh", "") if p in card_by_pos else None,
                "row": (p - 1) // cols + 1,
                "col": (p - 1) % cols + 1,
            }
            for p in _GT_CENTER_FOUR
        ],
        "description": "中心四张代表当前最核心的议题和能量焦点",
    }

    # ── 四角 ──
    corner_labels = {1: "左上(过去/远因)", 9: "右上(远见/未来)", 28: "左下(根基/业力)", 36: "右下(结局/定数)"}
    corners = {
        "positions": list(_GT_CORNERS),
        "cards": [
            {
                "position": p,
                "label": corner_labels.get(p, ""),
                "name": card_by_pos[p]["name"] if p in card_by_pos else None,
                "name_zh": card_by_pos[p].get("name_zh", "") if p in card_by_pos else None,
            }
            for p in _GT_CORNERS
        ],
        "description": "四角勾勒全盘框架：左上过往→右上远见→左下根基→右下结局",
    }

    # ── 心智宫/基础宫 汇总 ──
    def _summarize_palace(positions: frozenset[int], label: str) -> dict:
        """汇总某宫位群组内的牌，数据驱动。"""
        cards_in = [card_by_pos[p] for p in sorted(positions) if p in card_by_pos]
        names = [c["name"] for c in cards_in]
        positive = {"三叶草", "花束", "星星", "太阳", "钥匙", "心", "狗", "房子", "花园", "鱼", "锚", "鹳", "小孩", "百合"}
        negative = {"云", "蛇", "棺材", "镰刀", "鞭子", "狐狸", "山", "老鼠", "十字架"}
        pos_count = sum(1 for n in names if n in positive)
        neg_count = sum(1 for n in names if n in negative)
        tone = "吉" if pos_count > neg_count else ("凶" if neg_count > pos_count else "平")
        return {
            "label": label,
            "positions": sorted(positions),
            "card_count": len(cards_in),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "tone": tone,
            "cards": names,
            "card_names_zh": [c.get("name_zh", "") for c in cards_in],
        }

    mind_palace = _summarize_palace(_GT_MIND_PALACE_POSITIONS, "心智宫(意识/思维层)")
    foundation_palace = _summarize_palace(_GT_FOUNDATION_PALACE_POSITIONS, "基础宫(潜意识/根基层)")

    # ── 十字轴分析 ──
    cross_row_cards = [card_by_pos[p] for p in sorted(_GT_CROSS_ROW) if p in card_by_pos]
    cross_col_cards = [card_by_pos[p] for p in sorted(_GT_CROSS_COL) if p in card_by_pos]
    cross_analysis = {
        "horizontal_axis": {
            "positions": sorted(_GT_CROSS_ROW),
            "cards": [c["name"] for c in cross_row_cards],
            "description": "横轴(第三行)代表当前生活主线和核心挑战",
        },
        "vertical_axis": {
            "positions": sorted(_GT_CROSS_COL),
            "cards": [c["name"] for c in cross_col_cards],
            "description": "纵轴(第六列)代表命运的纵贯线和深层趋势",
        },
    }

    # ── 关键牌位置 ──
    significant_cards = {"Man", "Woman", "Heart", "Ring", "Key", "Sun", "Cross", "Ship", "House", "Tree", "Anchor", "Fish"}
    key_positions: dict[str, dict] = {}
    for pos, card in card_by_pos.items():
        if card["name"] in significant_cards:
            key_positions[card["name"]] = {
                "position": pos,
                "row": (pos - 1) // cols + 1,
                "col": (pos - 1) % cols + 1,
                "name_zh": card.get("name_zh", ""),
            }

    # ── 邻近距离修饰 — 数据驱动 ──
    adjacency_modifiers: list[dict] = []
    for pos, card in card_by_pos.items():
        nbrs = _get_neighbors(pos)
        modifiers_for_card = {
            "position": pos,
            "card": card["name"],
            "card_zh": card.get("name_zh", ""),
            "neighbors": {},
        }
        for direction, nbr_pos in nbrs.items():
            if nbr_pos is not None and nbr_pos in card_by_pos:
                nbr = card_by_pos[nbr_pos]
                modifiers_for_card["neighbors"][direction] = {
                    "position": nbr_pos,
                    "name": nbr["name"],
                    "name_zh": nbr.get("name_zh", ""),
                    "combo": _combo_meaning(card, nbr),
                }
        # 也对角线邻
        diag = _get_diagonal_neighbors(pos)
        for direction, d_pos in diag.items():
            if d_pos is not None and d_pos in card_by_pos:
                d_nbr = card_by_pos[d_pos]
                modifiers_for_card["neighbors"][f"diag_{direction}"] = {
                    "position": d_pos,
                    "name": d_nbr["name"],
                    "name_zh": d_nbr.get("name_zh", ""),
                    "combo": _combo_meaning(card, d_nbr),
                }
        # 骑士步修饰
        knight_positions = _get_knights(pos)
        kn_mods: list[dict] = []
        for kp in knight_positions:
            if kp in card_by_pos:
                k_card = card_by_pos[kp]
                kn_mods.append({
                    "position": kp,
                    "name": k_card["name"],
                    "name_zh": k_card.get("name_zh", ""),
                    "combo": _combo_meaning(card, k_card),
                })
        if kn_mods:
            modifiers_for_card["knight_moves"] = kn_mods
        adjacency_modifiers.append(modifiers_for_card)

    # ── 宫位分组汇总 ──
    mansion_groups: dict[str, dict] = {}
    for group_name, positions in _GT_HOUSE_GROUPS.items():
        mansion_groups[group_name] = _summarize_palace(positions, group_name)

    # ── 总览摘要 ──
    # 求测者牌位置
    querent_pos = key_positions.get("男人") or key_positions.get("女人")
    querent_info = None
    if querent_pos:
        querent_info = {
            "card": "男人" if "男人" in key_positions else "女人",
            "position": querent_pos["position"],
            "row": querent_pos["row"],
            "col": querent_pos["col"],
        }

    summary = {
        "total_cards": 36,
        "layout": "9×4 Grand Tableau",
        "querent_card": querent_info,
        "central_theme": center_four["cards"],
        "corner_overview": [
            f'{c["label"]}: {c["name"]}' for c in corners["cards"]
        ],
        "mind_tone": mind_palace["tone"],
        "foundation_tone": foundation_palace["tone"],
        "overall_tone": "吉" if mind_palace["tone"] == "吉" and foundation_palace["tone"] == "吉"
        else ("凶" if mind_palace["tone"] == "凶" and foundation_palace["tone"] == "凶" else "平"),
    }

    return {
        "layout": "9×4 Grand Tableau (36 cards)",
        "grid": [[c["name"] for c in row] for row in grid_rows],
        "grid_zh": [[c.get("name_zh", "") for c in row] for row in grid_rows],
        "center_four": center_four,
        "corners": corners,
        "mind_palace": mind_palace,
        "foundation_palace": foundation_palace,
        "cross_analysis": cross_analysis,
        "key_positions": key_positions,
        "house_positions": house_positions,
        "adjacency_modifiers": adjacency_modifiers,
        "mansion_groups": mansion_groups,
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════
# 6. Main Compute
# ═══════════════════════════════════════════════════════════════
def compute(b: Birth) -> ChartResult:
    subject = getattr(b, "subject", None) or "lenormand_guidance"
    time_budget = getattr(b, "mode", None) or "reflective"
    if time_budget not in {"quick", "reflective", "deep"}:
        time_budget = "reflective"

    requested_spread = getattr(b, "spread", None)
    spread_key = ALIASES.get(requested_spread or "", requested_spread or _default_spread(subject, time_budget))
    if spread_key not in SPREADS:
        spread_key = _default_spread(subject, time_budget)
    spread = SPREADS[spread_key]

    # 雷诺曼传统不用逆位
    # Deterministic seed
    seed = getattr(b, "seed", None)
    question = getattr(b, "question", None)
    if seed is not None:
        seed_used = str(seed)
    elif question:
        # 方案 §十一: 用户给问题就用问题作 seed (确定性), 不再用 date.today()
        seed_used = f"lenormand|{question}"
    else:
        raise ValueError(
            "lenormand 需要 seed 或 question 用于确定性洗牌 "
            "(方案 §十一 'AI 不参与随机')。"
        )

    # 用 hashlib SHA-256 作种子, Fisher-Yates 洗牌
    digest = hashlib.sha256(seed_used.encode("utf-8")).digest()
    draw: list[str] = []
    pool = list(LENORMAND_NAMES)
    # 用 digest 字节按位决定 Fisher-Yates 洗牌
    for i in range(spread["card_count"]):
        if not pool:
            break
        byte_idx = i % (len(digest) // 4)
        n = int.from_bytes(digest[byte_idx*4:byte_idx*4+4], "big")
        idx = n % len(pool)
        draw.append(pool.pop(idx))

    # Build card data
    cards = []
    positions = spread.get("positions", [])
    for i, name in enumerate(draw):
        num, name_en, zh, suit, core, extended, timing = LENORMAND_BY_NAME[name]
        pos_name = positions[i] if i < len(positions) else f"牌位{i + 1}"
        cards.append({
            "position": pos_name,
            "index": i + 1,
            "num": num,
            "name": name,
            "name_en": name_en,
            "name_zh": zh,
            "suit": suit,
            "core_meaning": core,
            "extended_meaning": extended,
            "timing": timing,
            "orient": "—",  # 雷诺曼无逆位
        })

    analysis = _analyze_tableau(cards)

    # Grand Tableau 分析 (若为 36 张全阵)
    grand_tableau = compute_grand_tableau(cards) if spread_key == "grand_tableau" else None

    return ChartResult(
        method="lenormand",
        school="west",
        engine="random+lenormand-36+combo-analysis",
        normalized={"elements": {}, "timeline": []},
        raw={
            "computed_at": date.today().isoformat(),
            "mode": "lenormand_spread",
            "subject": subject,
            "spread": spread_key,
            "spread_name": spread["name"],
            "spread_description": spread.get("description", ""),
            "spread_schema": [
                {"position": p if isinstance(p, str) else p.get("name", ""),
                 "meaning": "" if isinstance(p, str) else p.get("meaning", "")}
                for p in (positions if positions else [f"牌位{i + 1}" for i in range(spread["card_count"])])
            ],
            "cards": cards,
            "analysis": analysis,
            "grand_tableau": grand_tableau,
            "deck_size": 36,
            "deck_type": "Petit Lenormand (36 cards)",
            "seed_used": seed_used,
            "rule_version": "v1",
            "calculation_basis": {
                "method": "lenormand",
                "draw_rule": "36-card Lenormand deck, no replacement, no reversals",
                "key_feature": "相邻牌组合解读 (card pairs)",
                "rule_version": "v1",
                "limits": [
                    "雷诺曼解读高度依赖邻近牌的修饰关系,单张牌义需结合上下文",
                    "Grand Tableau (36张) 包含极丰富的信息量,适合深入分析",
                    "传统雷诺曼不用逆位——牌的位置和邻近牌比正逆更重要",
                ],
            },
        },
    )
