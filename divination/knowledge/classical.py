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
        "passage": "日干旺甚无依，若不为僧即道。得时能铸千金铁，失令难鎔一寸金。",
        "source": "渊海子平·五言独步",
        "confidence": 90,
    },
    {
        "id": "yhz_002",
        "category": "命理基础",
        "condition": "日主弱",
        "conclusion": "日主弱则财官为祸，宜生宜扶。身弱者需借他人之力，不宜独当一面。",
        "passage": "失令俱为衰论，身弱须用印比扶助。",
        "source": "渊海子平·玄机赋",
        "confidence": 90,
    },
    {
        "id": "yhz_003",
        "category": "用神",
        "condition": "用神有力",
        "conclusion": "用神有力则命格高，人生层次较高，关键节点能抓住机会。",
        "passage": "有病方为贵，无伤不是奇；格中如去病，财禄两相随。",
        "source": "渊海子平·五言独步",
        "confidence": 85,
    },
    {
        "id": "yhz_004",
        "category": "用神",
        "condition": "用神无力",
        "conclusion": "用神无力则命格平，虽有志向但力量不足，需借大运提振。",
        "passage": "有病方为贵，无伤不是奇；格中如去病，财禄两相随。",
        "source": "渊海子平·五言独步",
        "confidence": 85,
    },
    {
        "id": "yhz_005",
        "category": "十神",
        "condition": "正官有气",
        "conclusion": "正官者克我而有情也，为官禄之星。正官格宜身旺，得印绶护卫则为贵格。",
        "passage": "正官者，克我而有情也，为官禄之星。逢官看财，逢财看杀。",
        "source": "渊海子平·卷一·论十神",
        "confidence": 88,
    },
    {
        "id": "yhz_006",
        "category": "十神",
        "condition": "七杀得制",
        "conclusion": "七杀者克我而无情也，为权柄之星。制化得当即掌权柄。",
        "passage": "七杀者，克我而无情也，为权柄之星。制化得当，人不敢欺。",
        "source": "渊海子平·卷一·论十神",
        "confidence": 88,
    },
    {
        "id": "yhz_007",
        "category": "大运",
        "condition": "阳男阴女顺行",
        "conclusion": "阳年男命、阴年女命大运顺排。阳男阴女顺行，阴男阳女逆行。以节气为界三日为一岁。",
        "passage": "阳男阴女顺行，阴男阳女逆行。以节气为界，三日为一岁。",
        "source": "渊海子平·卷二·论大运",
        "confidence": 95,
    },
    {
        "id": "yhz_008",
        "category": "流年",
        "condition": "太岁为君",
        "conclusion": "流年为太岁，为一年之主宰。太岁不可犯，与大运原局天克地冲当防变化。",
        "passage": "太岁为君，为一年之主宰。太岁不可犯，天克地冲当防变化。",
        "source": "渊海子平·卷二·论太岁",
        "confidence": 90,
    },
    {
        "id": "yhz_009",
        "category": "十神心性",
        "condition": "七杀",
        "conclusion": "七杀势压三公，喜酒色而偏争好斗、爱轩昂而扶弱欺强，性急如虎。",
        "passage": "偏官七杀，势压三公，喜酒色而偏争好斗、爱轩昂而扶弱欺强、情性如虎、急躁如风。",
        "source": "渊海子平·相心赋",
        "confidence": 88,
    },
    {
        "id": "yhz_010",
        "category": "十神心性",
        "condition": "伤官",
        "conclusion": "伤官伤尽，多艺多能，使心机而傲物气高，多才傲物。",
        "passage": "伤官伤尽，多艺多能，使心机而傲物气高。",
        "source": "渊海子平·相心赋",
        "confidence": 85,
    },
    {
        "id": "yhz_011",
        "category": "十神心性",
        "condition": "印绶",
        "conclusion": "印绶主多智慧、丰身自在心慈。",
        "passage": "印绶主多智慧、丰身自在心慈。",
        "source": "渊海子平·相心赋",
        "confidence": 85,
    },
    {
        "id": "yhz_012",
        "category": "十神心性",
        "condition": "食神",
        "conclusion": "食神善能饮食、体厚而喜謌歌。",
        "passage": "食神善能饮食、体厚而喜謌歌。",
        "source": "渊海子平·相心赋",
        "confidence": 85,
    },
    {
        "id": "yhz_013",
        "category": "十神心性",
        "condition": "正财偏财",
        "conclusion": "正财偏财露，轻财好义，好说是非，嗜酒贪花。",
        "passage": "正财偏财露，轻财好义，好说是非，嗜酒贪花。",
        "source": "渊海子平·相心赋",
        "confidence": 82,
    },
    {
        "id": "yhz_014",
        "category": "用神",
        "condition": "用神不可损伤",
        "conclusion": "用神是命局关键，受损则吉事变凶。官星不可伤，财星不可劫，印星不可破，食神不可夺，禄神不可冲。",
        "passage": "用之为官，不可伤。用之为财，不可劫。用之为印，不可破。用之食神，不可破。用之为禄，不可冲。",
        "source": "渊海子平·论八字撮要法",
        "confidence": 92,
    },

    # ── 滴天髓 ──
    {
        "id": "dts_001",
        "category": "命理总纲",
        "condition": "三元万法",
        "conclusion": "欲识三元万法宗，先观帝载与神功。理解命理需从天、地、人三元入手。",
        "passage": "欲识三元万法宗，先观帝载与神功。",
        "source": "滴天髓·上篇·天道",
        "confidence": 88,
    },
    {
        "id": "dts_002",
        "category": "命理总纲",
        "condition": "五气偏全",
        "conclusion": "五气偏全定吉凶。五行之气的偏全决定了吉凶祸福，平衡为贵。",
        "passage": "五气偏全定吉凶。",
        "source": "滴天髓·上篇·天道",
        "confidence": 90,
    },
    {
        "id": "dts_003",
        "category": "体用",
        "condition": "道有体用",
        "conclusion": "道有体用，不可以一端论也，要在扶之抑之得其宜。命理分析需要辩证看待。",
        "passage": "道有体用，不可以一端论也，要在扶之抑之得其宜。",
        "source": "滴天髓·上篇·体用",
        "confidence": 90,
    },
    {
        "id": "dts_004",
        "category": "体用",
        "condition": "体用真确",
        "conclusion": "体用之用与用神之用有分别，须斟酌体用真确，取其最要紧者为用神。",
        "passage": "体用之用，与用神之用，有分别。必須斟酌体用真確，而取其最要緊者為用神。",
        "source": "滴天髓·上篇·体用论",
        "confidence": 90,
    },
    {
        "id": "dts_005",
        "category": "六亲",
        "condition": "夫妻姻缘",
        "conclusion": "夫妻姻缘宿世来，喜神有意傍天财。婚姻感情之根基与财星(男)官星(女)密切相关。",
        "passage": "夫妻姻缘宿世来，喜神有意傍天财。",
        "source": "滴天髓·下篇·六亲论",
        "confidence": 82,
    },
    {
        "id": "dts_006",
        "category": "配合",
        "condition": "干支配合",
        "conclusion": "配合干支仔细详，定人祸福与灾祥。干支配合需仔细分析。",
        "passage": "配合干支仔細詳，定人禍福與災祥。",
        "source": "滴天髓·上篇·配合",
        "confidence": 85,
    },
    {
        "id": "dts_007",
        "category": "命理总纲",
        "condition": "日主为天元",
        "conclusion": "日干为天元，地支为地元，支中所藏为人元；三元齐备为贵。",
        "passage": "日干為天元，地支為地元，支中所為人元。",
        "source": "滴天髓·天道地道人道章",
        "confidence": 88,
    },

    # ── 三命通会 ──
    {
        "id": "smth_001",
        "category": "格局",
        "condition": "正官格",
        "conclusion": "正官为六格之首，喜印绶以卫之，忌伤官以伤之。正官格宜身旺。",
        "passage": "正气官星用月支，喜逢财印到年时，破害冲空俱不犯，富贵双全报尔知。",
        "source": "三命通会·卷五·论正官",
        "confidence": 92,
    },
    {
        "id": "smth_002",
        "category": "格局",
        "condition": "七杀格",
        "conclusion": "杀印相生文武兼备。食神制杀英雄独压万人。杀无制则小人之辈。",
        "passage": "杀印相生文武兼备。食神制杀英雄独压万人。杀无制则小人之辈。",
        "source": "三命通会·卷五·论七杀",
        "confidence": 92,
    },
    {
        "id": "smth_003",
        "category": "格局",
        "condition": "七杀无制",
        "conclusion": "七杀有制为偏官，无制为七煞；身弱则夭。",
        "passage": "甲见庚为七煞，有制谓之偏官，无制谓之七煞。",
        "source": "三命通会·卷五·论七杀",
        "confidence": 90,
    },
    {
        "id": "smth_004",
        "category": "财运",
        "condition": "财格",
        "conclusion": "财为养命之源。财宜藏，藏则丰厚；不宜露，露则浮荡。财格喜身旺。",
        "passage": "正财者，乃甲见己、乙见戊之例。受我克制，为我之妻...故财要得时乘旺，不偏正混乱。",
        "source": "三命通会·卷六·论财",
        "confidence": 90,
    },
    {
        "id": "smth_005",
        "category": "财运",
        "condition": "身弱财旺",
        "conclusion": "身弱财旺，反为富屋贫人。看似有财实则难守。",
        "passage": "身弱财旺，反为富屋贫人。",
        "source": "三命通会·卷六·论财",
        "confidence": 88,
    },
    {
        "id": "smth_006",
        "category": "学术",
        "condition": "印格",
        "conclusion": "印多变枭，夺食为灾。印旺身强何劳印绶，印轻身弱必须印扶。",
        "passage": "印绶者，乃五行生我之名...能护我官星，使无伤克...忌财星，以财能破印。",
        "source": "三命通会·卷七·论印绶",
        "confidence": 90,
    },
    {
        "id": "smth_007",
        "category": "学术",
        "condition": "正印居月令",
        "conclusion": "正印居月令者，决不可见财；若居年时，月令见财只用财格。",
        "passage": "正印居月令者，决不可见财，若居年时，月令见财只用财格。",
        "source": "三命通会·卷七·论印绶",
        "confidence": 88,
    },
    {
        "id": "smth_008",
        "category": "大运",
        "condition": "运助用神",
        "conclusion": "行运之要以用神为宗。运助用神则吉，运克用神则凶。大运重地支，流年重天干。",
        "passage": "行运之要以用神为宗。运助用神则吉，运克用神则凶。大运重地支，流年重天干。",
        "source": "三命通会·卷九·论大运",
        "confidence": 95,
    },
    {
        "id": "smth_009",
        "category": "财运",
        "condition": "弃命从财",
        "conclusion": "弃命从财者，须要会财，若逢根气，命损无猜。",
        "passage": "弃命从财，须要会财，若逢根气，命损无猜。",
        "source": "三命通会·卷六·论财",
        "confidence": 85,
    },

    # ── 大六壬 ──
    {
        "id": "dlr_001",
        "category": "大六壬",
        "condition": "九宗门优先顺序",
        "conclusion": "九宗门判断顺序：贼克>比用>涉害>遥克>昴星；伏吟/返吟/八专/别责为特殊课式。",
        "passage": "九宗门者：一贼克，二比用，三涉害，四遥克，五昴星，六伏吟，七返吟，八别责，九八专。先取贼克，无贼克比用，多克涉害，无克遥克昴星，伏吟返吟八专别责。",
        "source": "大六壬指南·卷一·九宗门章",
        "confidence": 95,
    },
    {
        "id": "dlr_002",
        "category": "大六壬",
        "condition": "贼克法",
        "conclusion": "贼克：四课中仅一课有克，取此课上神为初传。事速可成。",
        "passage": "贼克为初传者，以课中有克者为用也。先取贼克，如无贼克则用比用。",
        "source": "大六壬指南·卷一",
        "confidence": 92,
    },
    {
        "id": "dlr_003",
        "category": "大六壬",
        "condition": "比用法",
        "conclusion": "比用：多课同时有克，取与日干五行相同（比和）之课上神为初传。",
        "passage": "多克无贼克，比用于日干，取与日干比和者为用。",
        "source": "大六壬指南·卷一",
        "confidence": 92,
    },
    {
        "id": "dlr_004",
        "category": "大六壬",
        "condition": "涉害法",
        "conclusion": "涉害：多课同时有克且与日干均无比和关系，涉地盘归家最深（克方最多）者为用。涉深则灾重。",
        "passage": "涉害者，地盘深处有克者为用，涉深则灾重。",
        "source": "大六壬指南·卷一",
        "confidence": 90,
    },
    {
        "id": "dlr_005",
        "category": "大六壬",
        "condition": "遥克法",
        "conclusion": "遥克：四课无克，取四课上神遥克日干者为初传。隔位难成，事多阻碍。",
        "passage": "四课无克，遥克日干者用之，隔位难得，事多阻碍。",
        "source": "大六壬指南·卷一",
        "confidence": 90,
    },
    {
        "id": "dlr_006",
        "category": "大六壬",
        "condition": "昴星法",
        "conclusion": "昴星：四课无克且无遥克日干，取从魁（酉）发用。虎视眈眈，事有阴私牵绊。",
        "passage": "四课无克，取从魁（酉）发用，昴星虎视，事有阴私。",
        "source": "大六壬指南·卷一",
        "confidence": 90,
    },
    {
        "id": "dlr_007",
        "category": "大六壬",
        "condition": "伏吟法",
        "conclusion": "伏吟：三传皆临地盘本位，天盘地支同位，事不举，人不动，静止不动。",
        "passage": "伏吟者，三传皆临地盘本位，月将加时归本宫，事不动，人不迁。",
        "source": "大六壬指南·卷一",
        "confidence": 92,
    },
    {
        "id": "dlr_008",
        "category": "大六壬",
        "condition": "返吟法",
        "conclusion": "返吟：三传皆冲地盘，客来反复，谋事难成。",
        "passage": "返吟者，三传皆冲地盘，来去反复，谋事难成。",
        "source": "大六壬指南·卷一",
        "confidence": 92,
    },
    {
        "id": "dlr_009",
        "category": "大六壬",
        "condition": "别责法",
        "conclusion": "别责：八专课中，干支同位无克，取日干寄宫上神为初传。事须别图，另辟蹊径。",
        "passage": "别责者，干支同位，取日干寄宫上神为初传，事须别图。",
        "source": "大六壬指南·卷一",
        "confidence": 88,
    },
    {
        "id": "dlr_010",
        "category": "大六壬",
        "condition": "八专法",
        "conclusion": "八专：干支同课无克，五行归一，事专断刚决。",
        "passage": "八专者，干支同课无克，五行归一，事专断。",
        "source": "大六壬指南·卷一",
        "confidence": 88,
    },
    {
        "id": "dlr_011",
        "category": "大六壬",
        "condition": "月将起法",
        "conclusion": "月将按24节气中气定。雨水过亥登明用事，春分过戌河魁用事，谷雨过酉从魁用事，小满过申传送用事，夏至过未小吉用事，大暑过午胜光用事，处暑过巳太乙用事，秋分过辰天罡用事，霜降过卯太冲用事，小雪过寅功曹用事，冬至关丑大吉用事，大寒过子神后用事。",
        "passage": "月将乃太阳过宫之位，以中气定之。雨水过亥登明用事，春分过戌河魁用事...大寒过子神后用事。",
        "source": "大六壬大全·卷一",
        "confidence": 95,
    },
    {
        "id": "dlr_012",
        "category": "大六壬",
        "condition": "贵人起法",
        "conclusion": "贵人起法：甲戊庚日丑未，乙己日子申，丙丁日亥酉，壬癸日卯巳，辛日午寅。昼贵在阳支，夜贵在阴支。贵人在亥子丑寅卯辰则顺排，在巳午未申酉戌则逆排。",
        "passage": "甲戊庚牛羊（丑未），乙己鼠猴（子申），丙丁猪鸡（亥酉），壬癸兔蛇（卯巳），辛马虎（午寅）。",
        "source": "大六壬大全·卷一",
        "confidence": 95,
    },

    # ── 增删卜易 (六爻) ──
    {
        "id": "zsby_001",
        "category": "六爻",
        "condition": "用神",
        "conclusion": "用神者，事之主也。六爻预测以用神为核心，用神旺相则事成有望。",
        "passage": "用神者，事之主也。",
        "source": "增删卜易·论用神",
        "confidence": 90,
    },
    {
        "id": "zsby_002",
        "category": "六爻",
        "condition": "用神旺衰",
        "conclusion": "用神旺相或得日月生扶为吉；用神休囚或被刑冲克害为凶。",
        "passage": "用神旺相，或得日月生扶者吉；休囚或被刑冲克害者凶。",
        "source": "增删卜易·论旺衰",
        "confidence": 88,
    },

    # ── 梅花易数 ──
    {
        "id": "mhys_001",
        "category": "梅花",
        "condition": "体用",
        "conclusion": "体卦为己，用卦为事。体克用诸事吉，用克体诸事凶。体生用有耗失，用生体有进益。",
        "passage": "体克用诸事吉，用克体诸事凶。体生用有耗失，用生体有进益。",
        "source": "梅花易数·体用生克",
        "confidence": 88,
    },

    # ── 黄帝宅经 (风水) ──
    {
        "id": "hdzj_001",
        "category": "风水",
        "condition": "宅以形势为身体",
        "conclusion": "宅以形势为身体，以泉水为血脉，以土地为皮肉，以草木为毛发。",
        "passage": "宅以形势为身体，以泉水为血脉，以土地为皮肉，以草木为毛发。",
        "source": "黄帝宅经",
        "confidence": 85,
    },

    # ── Ptolemy Tetrabiblos (Western) ──
    {
        "id": "pt_001",
        "category": "占星",
        "condition": "行星力量",
        "conclusion": "行星在自身宫位和擢升位置时力量最强，在陷落位置时力量最弱。",
        "passage": "Planets are most powerful in their own signs and in their exaltation, weakest in their fall.",
        "source": "Ptolemy Tetrabiblos·Book I",
        "confidence": 88,
    },

    # ══════════════════════════════════════════════════════════════
    # Phase E: 渊海子平·十神心性篇（新增）
    # 原文：十神诗歌 — 形容十种十神对应的心性/行为模式
    # ══════════════════════════════════════════════════════════════
    {
        "id": "yhz_010",
        "category": "十神心性",
        "condition": "正官格或日主见正官",
        "conclusion": "正官心性：为人端方，重名讲义，责任心强，有领导力。",
        "passage": "正官：为人端方，重名讲义，有主宰之心。",
        "source": "渊海子平·十神心性篇",
        "confidence": 88,
    },
    {
        "id": "yhz_011",
        "category": "十神心性",
        "condition": "七杀格或日主见七杀",
        "conclusion": "七放心性：为人刚暴，嫉妒心强，逞强好胜，有威严。",
        "passage": "七杀：刚强果断，嫉妒他人，有威仪。",
        "source": "渊海子平·十神心性篇",
        "confidence": 85,
    },
    {
        "id": "yhz_012",
        "category": "十神心性",
        "condition": "正印格或日主见正印",
        "conclusion": "印绊心性：为人慈和，容忍心强，善于思考，好学不倦。",
        "passage": "印绊：慈和乐善，容忍含蓄，智慧深沉。",
        "source": "渊海子平·十神心性篇",
        "confidence": 86,
    },
    {
        "id": "yhz_013",
        "category": "十神心性",
        "condition": "偏印格或日主见偏印",
        "conclusion": "偏印（枭神）心性：为人孤独，嫉妒心重，寡言固执，疑虑多端。",
        "passage": "偏印（枭神）：孤独固执，嫉妒是非，疑虑多端。",
        "source": "渊海子平·十神心性篇",
        "confidence": 83,
    },
    {
        "id": "yhz_014",
        "category": "十神心性",
        "condition": "食神格或日主见食神",
        "conclusion": "食神心性：为人谦和，心宽体胖，好饮食，乐天知命。",
        "passage": "食神：谦和自足，心宽体胖，乐善好施。",
        "source": "渊海子平·十神心性篇",
        "confidence": 86,
    },
    {
        "id": "yhz_015",
        "category": "十神心性",
        "condition": "伤官格或日主见伤官",
        "conclusion": "伤官心性：为人傲气，才高八斗，多谋少成，叛逆性强。",
        "passage": "伤官：傲气峥嵘，多才少成，叛逆权谋。",
        "source": "渊海子平·十神心性篇",
        "confidence": 84,
    },
    {
        "id": "yhz_016",
        "category": "十神心性",
        "condition": "正财格或日主见正财",
        "conclusion": "正财心性：为人勤俭，理财有方，踏实保守，物质欲强。",
        "passage": "正财：勤俭持家，踏实保守，理财有方。",
        "source": "渊海子平·十神心性篇",
        "confidence": 85,
    },
    {
        "id": "yhz_017",
        "category": "十神心性",
        "condition": "偏财格或日主见偏财",
        "conclusion": "偏财心性：为人豪爽，好义轻财，投机取巧，理财快进快出。",
        "passage": "偏财：豪爽好义，轻财投机，理财快出。",
        "source": "渊海子平·十神心性篇",
        "confidence": 84,
    },
    {
        "id": "yhz_018",
        "category": "十神心性",
        "condition": "比肩格或日主见比肩",
        "conclusion": "比肩心性：为人自信，独立自助，人际平等，固执己见。",
        "passage": "比肩：独立自助，自信固执，等分财物。",
        "source": "渊海子平·十神心性篇",
        "confidence": 83,
    },
    {
        "id": "yhz_019",
        "category": "十神心性",
        "condition": "劫财格或日主见劫财",
        "conclusion": "劫财心性：为人冲动，争强好斗，投机冒险，破财纠纷。",
        "passage": "劫财：冲动好斗，投机冒险，破财纠纷。",
        "source": "渊海子平·十神心性篇",
        "confidence": 82,
    },

    # ══════════════════════════════════════════════════════════════
    # Phase E: 滴天髓·体用篇（新增）
    # 原文：《滴天髓》天道·体用章 — 判断总纲
    # ══════════════════════════════════════════════════════════════
    {
        "id": "dts_006",
        "category": "命理基础",
        "condition": "判断总纲",
        "conclusion": "道有体用，不可以一端论。判断日元旺衰为先，扶之抑之得其宜。",
        "passage": "道有体用，不可以一端论也，要在扶之抑之得其宜。",
        "source": "滴天髓·上篇·体用",
        "confidence": 95,
    },
    {
        "id": "dts_007",
        "category": "命理基础",
        "condition": "日主过旺无依",
        "conclusion": "日主旺甚无依，不为僧即道——日元过旺无克泄者为孤独之命。",
        "passage": "日主旺甚无依，若不为僧即道。得时能铸千金铁，失令难熔一寸金。",
        "source": "滴天髓·上篇·体用",
        "confidence": 90,
    },
    {
        "id": "dts_008",
        "category": "命理基础",
        "condition": "日元过弱无根",
        "conclusion": "日元过弱无根，衰至极则为从势，需从其势而不断其本。",
        "passage": "日主过弱无根，衰无可衰，则从其势而贵。",
        "source": "滴天髓·上篇·体用",
        "confidence": 90,
    },
    {
        "id": "dts_009",
        "category": "命理基础",
        "condition": "日元中和",
        "conclusion": "日元中和，非富非贵之命，必以运来催发；中和偏枯皆需运来成就。",
        "passage": "日元中和，非富非贵；偏枯以运补之，中和以运催之。",
        "source": "滴天髓·上篇·体用",
        "confidence": 88,
    },

    # ══════════════════════════════════════════════════════════════
    # Phase E: 渊海子平·五言独步（新增）
    # ══════════════════════════════════════════════════════════════
    {
        "id": "yhz_020",
        "category": "命理基础",
        "condition": "日主旺相",
        "conclusion": "日主旺相，能任财官。身旺者事业上有担当力，能承受压力。",
        "passage": "日干旺甚无依，若不为僧即道。得时能铸千金铁，失令难熔一寸金。",
        "source": "渊海子平·五言独步",
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
            "十神心性": ["七杀", "伤官", "印绶", "食神", "正财", "偏财", "正官"],
            "大六壬": ["六壬", "课式", "三传", "四课", "月将", "贵人", "贼克", "比用", "涉害", "昴星", "伏吟", "返吟", "别责", "八专"],
            "六爻": ["六爻", "用神", "卦", "世应"],
            "梅花": ["梅花", "体用", "卦象"],
            "风水": ["风水", "宅", "形势", "方位"],
            "占星": ["占星", "行星", "宫位", "相位"],
        }
        boost = 0
        for word in category_words.get(rule["category"], []):
            if word in chart_text:
                boost = min(boost + 3, 15)
        scored.append((rule, confidence + boost))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:max_rules]]
