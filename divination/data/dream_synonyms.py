"""解梦同义词扩展库 — 梦境符号的同义词/关联词映射。

文献：
  - 《周公解梦》(托名周公·周代) — 主数据源
  - 《梦占逸旨》(明·陈士元) — 解梦理论著作
  - 《梦溪笔谈》(宋·沈括) — 笔记中含解梦观察
  - 《说文解字》(汉·许慎) — 汉字源流, 同族词

设计:
  - 至少 50 组同义词簇
  - 每簇包含 canonical (主符号, 应对应 DREAM_ENTRIES 中的 symbol) + 多个变体
  - 同义词命中权重 0.5 (比 alias 0.7 略低)
  - 同义词命中时附加 evidence "同义词扩展命中"
"""
from __future__ import annotations


# ══════════════════════════════════════════════════════════════
# 1. 同义词簇 (canonical → [variants])
# ══════════════════════════════════════════════════════════════
# canonical 必须对应 dream_corpus.DREAM_ENTRIES 中的 symbol (主名) 或其常见 alias。
# 命中文本中任意 variant → 视为匹配 canonical 所在条目, 权重 0.5。

SYNONYM_GROUPS: dict[str, list[str]] = {
    # ── 1-10 龙蛇凤鸟 ──
    "龙": ["蛟", "蛟龙", "虬", "虬龙", "螭", "螭龙", "应龙", "青龙", "苍龙"],
    "蛇": ["蟒", "长虫", "虺", "蚺", "青蛇", "白蛇", "毒蛇"],
    "凤": ["凤凰", "凰", "凤鸟", "朱雀"],
    "鸟": ["雀", "飞禽", "羽族", "鸟儿"],
    "马": ["骏", "驹", "骐", "骥", "骅骝", "战马", "骏马"],
    "虎": ["猛虎", "老虎", "白虎", "於菟", "山君"],
    "鱼": ["鲤", "鲲", "鲸", "鲢", "鳝", "鱼儿"],
    "龟": ["乌龟", "玄武", "元龟", "神龟"],
    "兔": ["玉兔", "月兔", "兔子"],
    "鼠": ["耗子", "老鼠", "家鼠", "田鼠"],

    # ── 11-20 身体 ──
    "牙": ["齿", "牙齿", "皓齿", "槽牙", "门牙"],
    "发": ["头发", "毛发", "青丝", "鬓发", "华发", "银发"],
    "眼": ["眼睛", "目", "眸子", "双眸", "眼眸"],
    "耳": ["耳朵", "双耳", "听宫"],
    "手": ["手掌", "玉手", "纤手", "素手"],
    "脚": ["足", "脚掌", "双足", "玉足"],
    "鼻": ["鼻子", "玉鼻", "鼻梁"],
    "嘴": ["口", "嘴巴", "樱唇", "口唇"],
    "心": ["心脏", "心房", "心头", "心底", "心田"],
    "血": ["鲜血", "血液", "流血", "见血", "献血"],

    # ── 21-30 自然/地理 ──
    "水": ["江", "河", "海", "湖", "溪", "泉", "潭", "池", "潮", "浪", "汉", "水"],
    "火": ["焰", "火焰", "炉火", "烛火", "灯火", "篝火", "烈火"],
    "山": ["峰", "岭", "峦", "岳", "崇山", "峻岭", "山峰"],
    "海": ["大海", "海洋", "沧海", "碧海"],
    "江": ["江河", "川", "大河"],
    "树": ["木", "树木", "大树", "乔木", "古树"],
    "花": ["鲜花", "花朵", "繁花", "花儿"],
    "草": ["青草", "野草", "芳草", "绿草"],
    "石": ["石头", "岩石", "磐石", "矿石"],
    "沙": ["沙子", "砂砾", "尘沙"],

    # ── 31-40 天象 ──
    "太阳": ["日", "日光", "金乌", "旭日", "朝阳"],
    "月亮": ["月", "玉兔", "婵娟", "明月", "月光", "皓月"],
    "星": ["星星", "星辰", "星宿", "天星", "繁星"],
    "云": ["云彩", "彩云", "霞", "云霞", "云气"],
    "雨": ["雨水", "甘霖", "细雨", "大雨"],
    "雪": ["雪花", "白雪", "瑞雪", "飞雪"],
    "雷": ["雷霆", "雷声", "霹雳", "响雷"],
    "风": ["微风", "大风", "狂风", "清风"],
    "虹": ["彩虹", "霓虹", "长虹"],
    "电": ["闪电", "雷电", "电光"],

    # ── 41-50 物品/财富/食物 ──
    "金": ["金子", "黄金", "金条", "五金", "赤金"],
    "玉": ["玉石", "美玉", "翡翠", "璧", "璞玉"],
    "钱": ["金钱", "银钱", "铜钱", "银子", "银两", "货币"],
    "车": ["马车", "汽车", "轿车", "车子", "辇"],
    "船": ["舟", "船舶", "画舫", "小舟", "木船"],
    "房": ["房子", "房屋", "住宅", "宅", "楼宇"],
    "门": ["大门", "房门", "城门", "门户", "正门"],
    "窗": ["窗户", "窗口", "窗棂", "轩窗"],
    "灯": ["油灯", "灯光", "灯火", "烛灯", "灯笼"],
    "书": ["书本", "书籍", "经书", "典籍", "卷册"],

    # ── 51-55 行为/事件 ──
    "飞": ["飞翔", "飞天", "翱翔", "飞升"],
    "哭": ["哭泣", "啼哭", "流泪", "啼泣"],
    "死": ["死亡", "亡", "去世", "辞世", "过世"],
    "婚": ["婚礼", "结婚", "成亲", "出嫁", "嫁娶"],
    "孕": ["怀孕", "孕", "孕妇", "怀胎", "有喜"],

    # ── 56-60 颜色 ──
    "红": ["红色", "朱", "赤", "丹", "绯", "大红"],
    "白": ["白色", "皓", "素", "苍白", "雪白"],
    "黑": ["黑色", "玄", "墨", "乌", "黢"],
    "黄": ["黄色", "金黄", "鹅黄", "杏黄"],
    "蓝": ["蓝色", "碧", "靛蓝", "宝蓝"],

    # ── 61-65 鬼神/人物 ──
    "佛": ["佛祖", "佛陀", "如来", "菩萨", "佛像"],
    "鬼": ["鬼魂", "阴魂", "幽魂", "魂魄"],
    "神": ["神仙", "神明", "天神", "神灵"],
    "祖先": ["祖宗", "先人", "祖辈", "先祖"],
    "蛇入怀中": ["蛇入怀", "怀中进蛇", "蛇缠身"],  # context_modifier 同义
}


# ══════════════════════════════════════════════════════════════
# 2. 派生索引: 反向索引 variant → canonical
# ══════════════════════════════════════════════════════════════
_VARIANT_TO_CANONICAL: dict[str, str] = {}
for canonical, variants in SYNONYM_GROUPS.items():
    for v in variants:
        # 若 canonical 是 symbol 主名, 则 variant 映射到 canonical
        _VARIANT_TO_CANONICAL[v] = canonical


def get_canonical(variant: str) -> str | None:
    """返回某 variant 对应的 canonical (主符号)。"""
    return _VARIANT_TO_CANONICAL.get(variant)


def get_synonyms(canonical: str) -> list[str]:
    """返回某 canonical 的所有 variants。"""
    return SYNONYM_GROUPS.get(canonical, [])


def all_variants() -> set[str]:
    """返回所有 variants 集合。"""
    return set(_VARIANT_TO_CANONICAL.keys())


# ══════════════════════════════════════════════════════════════
# 3. 组合梦境 (symbol + symbol → 解读)
# ══════════════════════════════════════════════════════════════
# 文献依据: 周公解梦"龙入水"、梦占逸旨"梦之合"。

COMBO_INTERPRETATIONS: list[dict] = [
    {
        "triggers": [("龙", "水")],
        "name": "龙入水",
        "interpretation": "大吉, 主飞黄腾达, 财源滚滚",
        "evidence": "《周公解梦》: '龙入水中, 大吉, 财源滚滚'",
    },
    {
        "triggers": [("龙", "飞")],
        "name": "龙飞上天",
        "interpretation": "大吉, 主飞黄腾达, 登高位",
        "evidence": "《周公解梦》: '龙飞上天, 大吉, 飞黄腾达'",
    },
    {
        "triggers": [("鱼", "水")],
        "name": "鱼跃水中",
        "interpretation": "大吉, 主财运亨通",
        "evidence": "《周公解梦》: '鱼在水中, 主大进财'",
    },
    {
        "triggers": [("虎", "飞")],
        "name": "虎跃",
        "interpretation": "大吉, 主权威提升",
        "evidence": "《梦占逸旨》: '虎行空中, 主大权'",
    },
    {
        "triggers": [("蛇", "入怀中")],
        "name": "蛇入怀",
        "interpretation": "大吉, 主得贵子",
        "evidence": "《周公解梦》: '蛇入怀中, 得贵子, 大吉'",
    },
    {
        "triggers": [("金", "玉")],
        "name": "金玉满堂",
        "interpretation": "大吉, 主富贵双全",
        "evidence": "《周公解梦》: '金玉并见, 大富大贵'",
    },
    {
        "triggers": [("血", "流")],
        "name": "血流",
        "interpretation": "大吉, 主进财",
        "evidence": "《周公解梦》: '自己流血, 进财大吉'",
    },
    {
        "triggers": [("死", "自己")],
        "name": "自己死",
        "interpretation": "大吉, 主长寿",
        "evidence": "《周公解梦》: '梦见自己死, 主长寿大吉'",
    },
    {
        "triggers": [("哭", "笑")],
        "name": "哭笑交织",
        "interpretation": "中吉, 悲喜参半, 转机将至",
        "evidence": "《梦占逸旨》: '哭笑杂见, 悲喜相倚'",
    },
    {
        "triggers": [("花", "开")],
        "name": "花开",
        "interpretation": "大吉, 主喜事临门",
        "evidence": "《周公解梦》: '鲜花盛开, 大吉喜事临'",
    },
    {
        "triggers": [("飞", "上")],
        "name": "向上飞",
        "interpretation": "大吉, 主升迁有望",
        "evidence": "《周公解梦》: '向上飞, 升迁有望大吉'",
    },
    {
        "triggers": [("水", "大")],
        "name": "大水涌来",
        "interpretation": "中吉偏吉, 主进大财",
        "evidence": "《周公解梦》: '大水汹涌, 进大财, 但防意外'",
    },
]


def find_combo(symbols: set[str], text: str = "") -> list[dict]:
    """检测组合梦境。

    Args:
        symbols: 提取到的符号集合 (主符号名)
        text: 原始文本 (用于组合关键词匹配, 如 "飞上" → "飞" + "上")

    Returns:
        触发的组合解读列表
    """
    triggered = []
    for combo in COMBO_INTERPRETATIONS:
        for trigger_a, trigger_b in combo["triggers"]:
            # 主符号命中
            hit_a = trigger_a in symbols
            hit_b = trigger_b in symbols
            # 文本中包含 trigger_b (如 trigger_b = "飞", trigger_a = "龙")
            if not hit_b and trigger_b in text:
                hit_b = True
            if hit_a and hit_b:
                triggered.append(combo)
                break
    return triggered


# ══════════════════════════════════════════════════════════════
# 4. 情绪识别 (梦境的总体吉凶倾向)
# ══════════════════════════════════════════════════════════════
LUCK_KEYWORDS = {
    "大吉": ["大吉", "巨吉", "大富", "大贵", "极吉"],
    "吉": ["吉", "喜", "贵", "财", "升", "成"],
    "中性": ["中性", "平衡", "平", "顺"],
    "小凶": ["小凶", "慎防", "有忧", "慎", "防", "须慎"],
    "凶": ["凶", "灾", "败", "损", "失"],
}


def detect_emotion(text: str) -> dict:
    """识别梦境整体吉凶倾向 (基于关键词)。

    Returns:
        {
            "luck_tendency": "大吉" | "吉" | "中性" | "小凶" | "凶",
            "score": float,  # -1.0 ~ 1.0
            "evidence_keywords": list[str],
        }
    """
    score = 0.0
    evidence: list[str] = []
    for luck, kws in LUCK_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                evidence.append(kw)
                if luck == "大吉":
                    score += 1.0
                elif luck == "吉":
                    score += 0.5
                elif luck == "中性":
                    score += 0.0
                elif luck == "小凶":
                    score -= 0.5
                elif luck == "凶":
                    score -= 1.0
    # 归一化
    norm = max(min(score / 3.0, 1.0), -1.0) if evidence else 0.0
    if norm > 0.5:
        tendency = "大吉"
    elif norm > 0.1:
        tendency = "吉"
    elif norm < -0.5:
        tendency = "凶"
    elif norm < -0.1:
        tendency = "小凶"
    else:
        tendency = "中性"
    return {"luck_tendency": tendency, "score": round(norm, 3),
            "evidence_keywords": evidence}


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 解梦同义词扩展库 自检 ===\n")
    print(f"1. 同义词簇总数: {len(SYNONYM_GROUPS)}")
    print(f"   variants 总数: {len(_VARIANT_TO_CANONICAL)}")
    print(f"   组合解读数: {len(COMBO_INTERPRETATIONS)}")

    # 测试映射
    print("\n2. 变体 → canonical:")
    for v in ["蛟", "虬", "青蛇", "玉兔", "皓月", "翠"]:
        c = get_canonical(v)
        print(f"   {v} → {c}")

    # 测试组合
    print("\n3. 组合梦境检测:")
    combos = find_combo({"龙", "水"}, "我梦见一条龙在水中")
    for c in combos:
        print(f"   - {c['name']}: {c['interpretation']}")

    # 情绪识别
    print("\n4. 情绪识别测试:")
    for text in ["梦见大吉之象, 进财", "梦见血光之灾, 慎防", "梦见花开花落"]:
        e = detect_emotion(text)
        print(f"   '{text}' → {e['luck_tendency']} (score={e['score']}, kw={e['evidence_keywords']})")