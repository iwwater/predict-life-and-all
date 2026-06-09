"""Classical text rule extraction.

Extracts structured rules from existing reference texts (渊海子平, 滴天髓, 三命通会,
增删卜易, 梅花易数, 沈氏玄空学, 黄帝宅经, Ptolemy_Tetrabiblos).

These rules can be injected into LLM prompts to improve interpretation accuracy
with sourced classical wisdom.
"""

# ── Structured Rules Extracted from Classical Texts ─────────────────────────
# Format: {id, condition, conclusion, source, category, confidence}

CLASSICAL_RULES = [
    # ── 渊海子平 ──
    {
        "id": "yhz_001",
        "category": "命理基础",
        "condition": "日主旺",
        "conclusion": "日主旺则能任财官，宜克宜泄。身强者事业上有担当力，能承受压力。",
        "source": "渊海子平·卷一·论日主",
        "confidence": 90,
    },
    {
        "id": "yhz_002",
        "category": "命理基础",
        "condition": "日主弱",
        "conclusion": "日主弱则财官为祸，宜生宜扶。身弱者需借他人之力，不宜独当一面。",
        "source": "渊海子平·卷一·论日主",
        "confidence": 90,
    },
    {
        "id": "yhz_003",
        "category": "用神",
        "condition": "用神有力",
        "conclusion": "用神有力则命格高，人生层次较高，关键节点能抓住机会。",
        "source": "渊海子平·卷一·论用神",
        "confidence": 85,
    },
    {
        "id": "yhz_004",
        "category": "用神",
        "condition": "用神无力",
        "conclusion": "用神无力则命格平，虽有志向但力量不足，需借大运提振。",
        "source": "渊海子平·卷一·论用神",
        "confidence": 85,
    },
    {
        "id": "yhz_005",
        "category": "十神",
        "condition": "正官有气",
        "conclusion": "正官者克我而有情也，为官禄之星。正官格宜身旺，得印绶护卫则为贵格。",
        "source": "渊海子平·卷一·论十神",
        "confidence": 88,
    },
    {
        "id": "yhz_006",
        "category": "十神",
        "condition": "七杀得制",
        "conclusion": "七杀者克我而无情也，为权柄之星。制化得当即掌权柄。",
        "source": "渊海子平·卷一·论十神",
        "confidence": 88,
    },
    {
        "id": "yhz_007",
        "category": "大运",
        "condition": "阳男阴女顺行",
        "conclusion": "阳年男命、阴年女命大运顺排。阳男阴女顺行，阴男阳女逆行。以节气为界三日为一岁。",
        "source": "渊海子平·卷二·论大运",
        "confidence": 95,
    },
    {
        "id": "yhz_008",
        "category": "流年",
        "condition": "太岁为君",
        "conclusion": "流年为太岁，为一年之主宰。太岁不可犯，与大运原局天克地冲当防变化。",
        "source": "渊海子平·卷二·论太岁",
        "confidence": 90,
    },
    {
        "id": "yhz_009",
        "category": "五行",
        "condition": "金主义",
        "conclusion": "金主义，金旺之人重原则、有决断力、刚毅果敢。金弱则优柔寡断。",
        "source": "渊海子平·卷三·论五行",
        "confidence": 85,
    },
    {
        "id": "yhz_010",
        "category": "五行",
        "condition": "木主仁",
        "conclusion": "木主仁，木旺之人有仁爱之心、创造力和成长性。木弱则缺乏进取心。",
        "source": "渊海子平·卷三·论五行",
        "confidence": 85,
    },

    # ── 滴天髓 ──
    {
        "id": "dts_001",
        "category": "命理总纲",
        "condition": "三元万法",
        "conclusion": "欲识三元万法宗，先观帝载与神功。理解命理需从天、地、人三元入手。",
        "source": "滴天髓·上篇·天道",
        "confidence": 88,
    },
    {
        "id": "dts_002",
        "category": "命理总纲",
        "condition": "五气偏全",
        "conclusion": "五气偏全定吉凶。五行之气的偏全决定了吉凶祸福，平衡为贵。",
        "source": "滴天髓·上篇·天道",
        "confidence": 90,
    },
    {
        "id": "dts_003",
        "category": "体用",
        "condition": "道有体用",
        "conclusion": "道有体用，不可以一端论也，要在扶之抑之得其宜。命理分析需要辩证看待。",
        "source": "滴天髓·上篇·体用",
        "confidence": 90,
    },
    {
        "id": "dts_004",
        "category": "配合",
        "condition": "干支配合",
        "conclusion": "配合干支仔细详，定人祸福与灾祥。干支配合需仔细分析。",
        "source": "滴天髓·上篇·配合",
        "confidence": 85,
    },
    {
        "id": "dts_005",
        "category": "六亲",
        "condition": "夫妻姻缘",
        "conclusion": "夫妻姻缘宿世来，喜神有意傍天财。婚姻感情之根基与财星(男)官星(女)密切相关。",
        "source": "滴天髓·下篇·六亲论",
        "confidence": 82,
    },

    # ── 三命通会 ──
    {
        "id": "smth_001",
        "category": "格局",
        "condition": "正官格",
        "conclusion": "正官为六格之首，喜印绶以卫之，忌伤官以伤之。正官格宜身旺。",
        "source": "三命通会·卷四·论正官",
        "confidence": 92,
    },
    {
        "id": "smth_002",
        "category": "格局",
        "condition": "七杀格",
        "conclusion": "杀印相生文武兼备。食神制杀英雄独压万人。杀无制则小人之辈。",
        "source": "三命通会·卷五·论七杀",
        "confidence": 92,
    },
    {
        "id": "smth_003",
        "category": "财运",
        "condition": "财格",
        "conclusion": "财为养命之源。财宜藏，藏则丰厚；不宜露，露则浮荡。财格喜身旺。",
        "source": "三命通会·卷六·论财",
        "confidence": 90,
    },
    {
        "id": "smth_004",
        "category": "财运",
        "condition": "身弱财旺",
        "conclusion": "身弱财旺，反为富屋贫人。看似有财实则难守。",
        "source": "三命通会·卷六·论财",
        "confidence": 88,
    },
    {
        "id": "smth_005",
        "category": "学术",
        "condition": "印格",
        "conclusion": "印多变枭，夺食为灾。印旺身强何劳印绶，印轻身弱必须印扶。",
        "source": "三命通会·卷七·论印绶",
        "confidence": 90,
    },
    {
        "id": "smth_006",
        "category": "大运",
        "condition": "运助用神",
        "conclusion": "行运之要以用神为宗。运助用神则吉，运克用神则凶。大运重地支，流年重天干。",
        "source": "三命通会·卷九·论大运",
        "confidence": 95,
    },

    # ── 增删卜易 (六爻) ──
    {
        "id": "zsby_001",
        "category": "六爻",
        "condition": "用神",
        "conclusion": "用神者，事之主也。六爻预测以用神为核心，用神旺相则事成有望。",
        "source": "增删卜易·论用神",
        "confidence": 90,
    },

    # ── 梅花易数 ──
    {
        "id": "mhys_001",
        "category": "梅花",
        "condition": "体用",
        "conclusion": "体卦为己，用卦为事。体克用诸事吉，用克体诸事凶。体生用有耗失，用生体有进益。",
        "source": "梅花易数·体用生克",
        "confidence": 88,
    },

    # ── 黄帝宅经 (风水) ──
    {
        "id": "hdzj_001",
        "category": "风水",
        "condition": "宅以形势为身体",
        "conclusion": "宅以形势为身体，以泉水为血脉，以土地为皮肉，以草木为毛发。",
        "source": "黄帝宅经",
        "confidence": 85,
    },

    # ── Ptolemy Tetrabiblos (Western) ──
    {
        "id": "pt_001",
        "category": "占星",
        "condition": "行星力量",
        "conclusion": "行星在自身宫位和擢升位置时力量最强，在陷落位置时力量最弱。",
        "source": "Ptolemy Tetrabiblos·Book I",
        "confidence": 88,
    },
]


def get_classical_rules(category: str = None, min_confidence: int = 0) -> list[dict]:
    """Get classical rules, optionally filtered by category and confidence.

    Args:
        category: Filter by category (e.g., "命理基础", "财运", "格局")
        min_confidence: Minimum confidence score (0-100)

    Returns:
        List of matching rules
    """
    rules = CLASSICAL_RULES
    if category:
        rules = [r for r in rules if r["category"] == category]
    if min_confidence:
        rules = [r for r in rules if r["confidence"] >= min_confidence]
    return rules


def extract_rules_for_chart(chart, max_rules: int = 5) -> list[dict]:
    """Extract the most relevant classical rules for a given chart.

    Uses keyword matching against chart data to find applicable rules.
    Fallback: returns highest-confidence rules across all categories.

    Args:
        chart: ChartResult with raw data
        max_rules: Maximum rules to return

    Returns:
        List of applicable classical rules for LLM prompt injection
    """
    raw = chart.raw if hasattr(chart, "raw") else {}
    chart_text = str(raw).lower()

    # Simple keyword-based matching
    scored = []
    for rule in CLASSICAL_RULES:
        confidence = rule["confidence"]
        # Check for keyword matches in chart data
        category_words = {
            "命理基础": ["日主", "旺", "弱", "身强", "身弱"],
            "财运": ["财", "财富", "money"],
            "格局": ["官", "杀", "印", "格", "pattern"],
            "大运": ["运", "流年", "timeline"],
            "五行": ["金", "木", "水", "火", "土", "element"],
            "六亲": ["姻缘", "夫妻", "感情", "配偶"],
        }
        boost = 0
        for word in category_words.get(rule["category"], []):
            if word in chart_text:
                boost = min(boost + 3, 15)
        scored.append((rule, confidence + boost))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:max_rules]]
