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
# 5. Main Compute
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
