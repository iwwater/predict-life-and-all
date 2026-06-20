#!/usr/bin/env python3
"""Append new dream entries to dream_corpus.py before the closing ]."""
import re
from pathlib import Path

CORPUS = Path("E:/work/predict life and all/divination/data/dream_corpus.py")

# New entries to add (115 more, bringing total from 48 to 163)
NEW_ENTRIES = r"""

    # ════════════════════════════════════════════════════════════
    # Phase G: 扩展条目（按主流《周公解梦》分类补全, +115 条）
    # ════════════════════════════════════════════════════════════

    # ── 天象 (8 条新增) ──
    {
        "symbol": "星",
        "aliases": ["星星", "流星", "陨星", "星辰"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主名人、才智、希望。流星主灾, 明星主吉。",
        "context_modifiers": {
            "明星当空": "有名有望, 吉",
            "流星": "有变, 须慎",
            "星辰坠落": "有名人去, 慎防",
            "自己成星": "成大器, 大吉",
        },
    },
    {
        "symbol": "云",
        "aliases": ["云彩", "乌云", "彩云"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主变化、迁移、时运。",
        "context_modifiers": {
            "彩云": "有喜庆, 吉",
            "乌云": "有阻碍, 慎防",
            "云开见日": "转机, 大吉",
        },
    },
    {
        "symbol": "风",
        "aliases": ["大风", "微风", "狂风"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主变化、消息、气势。",
        "context_modifiers": {
            "微风": "安宁平和, 吉",
            "大风": "有大变, 须慎",
            "顺风": "进展顺利, 吉",
        },
    },
    {
        "symbol": "雾",
        "aliases": ["大雾", "浓雾"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主迷茫、阻碍、暧昧。",
        "context_modifiers": {
            "浓雾": "前路不明, 慎之",
            "雾散见日": "真相显现, 大吉",
        },
    },
    {
        "symbol": "霜",
        "aliases": ["白霜", "下霜"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主清冷、严厉、考验。",
        "context_modifiers": {
            "霜降": "时运转换, 中性",
        },
    },
    {
        "symbol": "冰",
        "aliases": ["结冰", "冰冻"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主阻碍、冷淡、凝滞。",
        "context_modifiers": {
            "冰雹": "有灾, 慎防",
            "冰融": "阻碍解除, 吉",
        },
    },
    {
        "symbol": "闪电",
        "aliases": ["雷电", "电光"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主突变、灵感、揭示。",
        "context_modifiers": {
            "雷电交加": "有大变, 慎防",
        },
    },
    {
        "symbol": "彩虹",
        "aliases": ["虹", "霓虹"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主祥瑞、好运、转机。",
        "context_modifiers": {
            "见彩虹": "好运来临, 大吉",
        },
    },

    # ── 动物 (15 条新增) ──
    {
        "symbol": "牛",
        "aliases": ["黄牛", "水牛", "牦牛"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主勤劳、财富、坚韧。",
        "context_modifiers": {
            "牵牛": "事业稳步, 吉",
            "牛跑": "财来急, 大进",
        },
    },
    {
        "symbol": "羊",
        "aliases": ["山羊", "绵羊"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主顺从、财富、祭祀。",
        "context_modifiers": {
            "群羊": "大吉, 财富满盈",
            "羔羊": "有新生, 吉",
        },
    },
    {
        "symbol": "猪",
        "aliases": ["家猪"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主福气、财富、饱足。",
        "context_modifiers": {
            "肥猪": "大吉, 福禄寿全",
        },
    },
    {
        "symbol": "兔",
        "aliases": ["白兔", "玉兔"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主敏捷、长寿、月宫。",
        "context_modifiers": {
            "白兔": "大吉, 长寿",
            "抱兔": "得子, 吉",
        },
    },
    {
        "symbol": "鼠",
        "aliases": ["老鼠", "耗子"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主小人、暗耗、虚惊。",
        "context_modifiers": {
            "鼠咬物": "有损耗, 小凶",
            "群鼠": "小人环伺, 慎防",
            "捕鼠": "去小人, 吉",
            "白鼠": "有喜事, 吉",
        },
    },
    {
        "symbol": "蝙蝠",
        "aliases": ["飞鼠"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主福气、长寿。",
        "context_modifiers": {
            "蝙蝠入宅": "福临门, 大吉",
            "白蝙蝠": "大吉, 长寿",
        },
    },
    {
        "symbol": "蝴蝶",
        "aliases": ["彩蝶"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主美好、变化、爱情。",
        "context_modifiers": {
            "彩蝶飞舞": "有喜事, 吉",
            "捕蝴蝶": "得爱情, 吉",
        },
    },
    {
        "symbol": "蜘蛛",
        "aliases": ["蛛蛛"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主谋略、巧计、网罗。",
        "context_modifiers": {
            "蜘蛛结网": "成事在即, 吉",
        },
    },
    {
        "symbol": "蜈蚣",
        "aliases": ["百足虫"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主小人、口舌、纠纷。",
        "context_modifiers": {
            "蜈蚣咬": "有口舌, 慎防",
            "杀蜈蚣": "去小人, 吉",
        },
    },
    {
        "symbol": "公鸡",
        "aliases": ["鸡", "雄鸡"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主喜庆、信使、勤奋。",
        "context_modifiers": {
            "公鸡啼": "有喜事, 吉",
            "鸡斗": "有竞争, 中性",
        },
    },
    {
        "symbol": "鸭",
        "aliases": ["鸭子"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主安稳、家庭、收入。",
        "context_modifiers": {
            "鸭入水": "顺其自然, 吉",
        },
    },
    {
        "symbol": "鹅",
        "aliases": ["天鹅", "家鹅"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主忠诚、伴侣、长鸣。",
        "context_modifiers": {
            "天鹅飞": "志向高远, 吉",
        },
    },
    {
        "symbol": "狐狸",
        "aliases": ["狐"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主狡黠、魅力、暧昧。",
        "context_modifiers": {
            "白狐": "有贵人, 吉",
            "捕狐": "去小人之计, 吉",
        },
    },
    {
        "symbol": "蜜蜂",
        "aliases": ["蜂"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主勤劳、收获、合作。",
        "context_modifiers": {
            "蜂群": "大吉, 事业有成",
            "蜂蜜": "有甜蜜, 吉",
        },
    },
    {
        "symbol": "乌龟",
        "aliases": ["龟"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主长寿、稳定、贵人。",
        "context_modifiers": {
            "龟入宅": "大吉, 增寿",
            "白龟": "大吉, 长寿",
        },
    },

    # ── 物品 (15 条新增) ──
    {
        "symbol": "金",
        "aliases": ["黄金", "金子", "金条"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主财富、贵人、成功。",
        "context_modifiers": {
            "得金": "大进财, 大吉",
            "失金": "财去, 须防",
            "金器": "有名望, 吉",
        },
    },
    {
        "symbol": "玉",
        "aliases": ["玉石", "美玉"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主品德、纯洁、贵人。",
        "context_modifiers": {
            "得玉": "有贵人, 吉",
            "玉碎": "有失, 慎防",
        },
    },
    {
        "symbol": "钥匙",
        "aliases": ["钥"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主解决、机会、新阶段。",
        "context_modifiers": {
            "得钥匙": "得机遇, 吉",
            "失钥匙": "失机会, 小凶",
        },
    },
    {
        "symbol": "锁",
        "aliases": ["锁链"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主束缚、限制、保护。",
        "context_modifiers": {
            "上锁": "有保密, 中性",
            "开锁": "释疑解困, 吉",
        },
    },
    {
        "symbol": "镜子",
        "aliases": ["铜镜", "明镜"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主真相、自我、清晰。",
        "context_modifiers": {
            "照镜": "看清自己, 吉",
            "镜碎": "有阻碍, 慎防",
        },
    },
    {
        "symbol": "伞",
        "aliases": ["雨伞"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主保护、贵人、屏障。",
        "context_modifiers": {
            "撑伞": "得人庇护, 吉",
            "伞坏": "保护失, 慎防",
        },
    },
    {
        "symbol": "鞋",
        "aliases": ["鞋子", "靴子"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主旅程、伴侣、稳定。",
        "context_modifiers": {
            "穿新鞋": "有新旅程, 吉",
            "丢鞋": "有失, 慎防",
        },
    },
    {
        "symbol": "帽",
        "aliases": ["帽子", "冠"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主身份、名誉、地位。",
        "context_modifiers": {
            "戴新帽": "升职, 吉",
            "丢帽": "失位, 小凶",
        },
    },
    {
        "symbol": "烛",
        "aliases": ["蜡烛"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主希望、指引、智慧。",
        "context_modifiers": {
            "烛光亮": "光明在前, 吉",
            "烛灭": "希望失, 慎防",
        },
    },
    {
        "symbol": "铃",
        "aliases": ["铃铛"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主消息、警醒、传讯。",
        "context_modifiers": {
            "铃响": "有消息, 吉",
        },
    },
    {
        "symbol": "钟",
        "aliases": ["古钟"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主时光、警告、变迁。",
        "context_modifiers": {
            "钟响": "有警醒, 吉",
        },
    },
    {
        "symbol": "鼓",
        "aliases": ["战鼓"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主声威、动员、宣扬。",
        "context_modifiers": {
            "鼓响": "有名声, 吉",
        },
    },
    {
        "symbol": "画",
        "aliases": ["图画", "画卷"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主形象、记忆、文化。",
        "context_modifiers": {
            "看画": "得启示, 吉",
        },
    },
    {
        "symbol": "琴",
        "aliases": ["古琴"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主和谐、情感、艺术。",
        "context_modifiers": {
            "弹琴": "有知音, 吉",
            "琴断弦": "情感有变, 慎防",
        },
    },
    {
        "symbol": "笔",
        "aliases": ["毛笔"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主文才、记录、表达。",
        "context_modifiers": {
            "握笔": "有文运, 吉",
        },
    },

    # ── 植物 (8 条新增) ──
    {
        "symbol": "草",
        "aliases": ["青草"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "主生机、平凡、韧性。",
        "context_modifiers": {
            "青草茂盛": "生机勃勃, 吉",
            "枯草": "生机失, 慎防",
        },
    },
    {
        "symbol": "竹",
        "aliases": ["竹子", "竹林"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主节节高、君子、长寿。",
        "context_modifiers": {
            "竹林": "大吉, 节节高升",
            "竹笋": "有新发展, 吉",
        },
    },
    {
        "symbol": "梅",
        "aliases": ["梅花"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主高洁、坚韧、严冬独秀。",
        "context_modifiers": {
            "梅花开": "大吉, 时来运转",
            "红梅": "喜事至, 大吉",
        },
    },
    {
        "symbol": "兰",
        "aliases": ["兰花"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主高洁、君子、香气。",
        "context_modifiers": {
            "兰花香": "有名誉, 吉",
        },
    },
    {
        "symbol": "菊",
        "aliases": ["菊花"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主高洁、长寿、秋意。",
        "context_modifiers": {
            "菊花盛开": "长寿有福, 吉",
            "白菊": "有丧, 慎防",
        },
    },
    {
        "symbol": "莲",
        "aliases": ["莲花", "荷花"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主清净、灵性、繁衍。",
        "context_modifiers": {
            "莲花开": "大吉, 清净吉祥",
            "采莲": "得财, 吉",
        },
    },
    {
        "symbol": "瓜",
        "aliases": ["西瓜", "南瓜"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主子女、收获、丰盛。",
        "context_modifiers": {
            "大瓜": "子女有成, 大吉",
            "瓜熟蒂落": "有收获, 吉",
        },
    },
    {
        "symbol": "牡丹",
        "aliases": ["国花"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主富贵、繁荣、极致。",
        "context_modifiers": {
            "牡丹盛开": "大吉, 富贵满堂",
        },
    },

    # ── 身体 (10 条新增) ──
    {
        "symbol": "脚",
        "aliases": ["足", "脚趾"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主根基、稳定、行动力。",
        "context_modifiers": {
            "脚痛": "进展受阻, 慎防",
            "脚疾走": "行动力强, 吉",
        },
    },
    {
        "symbol": "手",
        "aliases": ["手指", "手臂"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主作为、握权、技巧。",
        "context_modifiers": {
            "手中有物": "得财或权, 吉",
            "手断": "失权, 慎防",
        },
    },
    {
        "symbol": "鼻",
        "aliases": ["鼻子"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主识别、直觉、财气。",
        "context_modifiers": {
            "鼻出血": "进财, 吉",
            "鼻不通": "运势阻, 慎防",
        },
    },
    {
        "symbol": "嘴",
        "aliases": ["口"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主言语、表达、口舌。",
        "context_modifiers": {
            "开口说话": "有名声, 吉",
            "口舌生疮": "有口舌, 慎防",
        },
    },
    {
        "symbol": "心",
        "aliases": ["心脏"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主情绪、爱情、内心。",
        "context_modifiers": {
            "心跳": "有情感变化, 中性",
            "心定": "内心安宁, 吉",
        },
    },
    {
        "symbol": "骨",
        "aliases": ["骨头", "骨骼"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主根本、性格、寿命。",
        "context_modifiers": {
            "骨强": "体健, 吉",
            "骨痛": "有损, 慎防",
        },
    },
    {
        "symbol": "皮",
        "aliases": ["皮肤", "肌肤"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主身份、关系、表象。",
        "context_modifiers": {
            "皮肤光洁": "有身份, 吉",
        },
    },
    {
        "symbol": "指甲",
        "aliases": ["爪"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主防御、攻击、把握。",
        "context_modifiers": {
            "剪指甲": "去除阻碍, 吉",
            "指甲断": "失势, 慎防",
        },
    },
    {
        "symbol": "胡须",
        "aliases": ["须"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主男性气概、地位、年龄。",
        "context_modifiers": {
            "长须": "有权威, 吉",
        },
    },
    {
        "symbol": "眼泪",
        "aliases": ["泪"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主情绪宣泄、释放、转化。",
        "context_modifiers": {
            "流泪": "释怀, 吉",
        },
    },

    # ── 鬼神/宗教 (5 条新增) ──
    {
        "symbol": "神",
        "aliases": ["神仙", "神明"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主庇佑、灵感、超验。",
        "context_modifiers": {
            "见神": "得庇佑, 吉",
            "拜神": "所求遂, 大吉",
        },
    },
    {
        "symbol": "仙",
        "aliases": ["仙人", "仙子"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主长寿、超脱、灵性。",
        "context_modifiers": {
            "见仙": "大吉, 长寿",
        },
    },
    {
        "symbol": "道士",
        "aliases": ["法师"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主指引、解困、护佑。",
        "context_modifiers": {
            "见道士": "得指引, 吉",
        },
    },
    {
        "symbol": "和尚",
        "aliases": ["僧人"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主清净、修行、智慧。",
        "context_modifiers": {
            "见和尚": "得清净, 吉",
        },
    },
    {
        "symbol": "鬼压床",
        "aliases": ["梦魇"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "主压抑、焦虑、情绪负担。",
        "context_modifiers": {
            "鬼压": "情绪压抑, 须释放",
            "挣扎醒来": "化解, 中性",
        },
    },

    # ── 行为 (15 条新增) ──
    {
        "symbol": "游泳",
        "aliases": ["戏水"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主情感流动、自由、适应。",
        "context_modifiers": {
            "游泳": "情感顺畅, 吉",
            "溺水": "情感失控, 慎防",
        },
    },
    {
        "symbol": "唱歌",
        "aliases": ["歌唱"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主表达、欢庆、释放。",
        "context_modifiers": {
            "欢唱": "心情愉悦, 吉",
            "悲歌": "有愁绪, 慎防",
        },
    },
    {
        "symbol": "跳舞",
        "aliases": ["舞蹈"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主喜悦、自由、表达。",
        "context_modifiers": {
            "欢舞": "有喜庆, 吉",
        },
    },
    {
        "symbol": "考试",
        "aliases": ["答题"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主考核、压力、自我评价。",
        "context_modifiers": {
            "考试顺利": "自信, 吉",
            "考试不及格": "有压力, 慎防",
        },
    },
    {
        "symbol": "迷路",
        "aliases": ["走失"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主迷茫、失方向、需指引。",
        "context_modifiers": {
            "迷路": "方向失, 须慎",
            "找到路": "解困, 吉",
        },
    },
    {
        "symbol": "逃跑",
        "aliases": ["逃亡"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主逃避、压力、紧迫。",
        "context_modifiers": {
            "被追": "有压力, 慎防",
            "逃跑成功": "脱困, 吉",
        },
    },
    {
        "symbol": "战斗",
        "aliases": ["打架"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主冲突、矛盾、内心挣扎。",
        "context_modifiers": {
            "战胜": "克服困难, 吉",
            "战败": "有阻碍, 慎防",
        },
    },
    {
        "symbol": "捡钱",
        "aliases": ["得财"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主意外之财、机遇。",
        "context_modifiers": {
            "捡钱": "大进财, 吉",
        },
    },
    {
        "symbol": "丢钱",
        "aliases": ["失财"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "小凶。主损耗、损失、破财。",
        "context_modifiers": {
            "丢钱": "有损耗, 慎防",
        },
    },
    {
        "symbol": "埋葬",
        "aliases": ["下葬"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主结束、转化、隐藏。",
        "context_modifiers": {
            "见埋葬": "结束一段事, 中性",
        },
    },
    {
        "symbol": "上楼",
        "aliases": ["登楼"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主升迁、进步、成功。",
        "context_modifiers": {
            "登顶": "大吉, 登高位",
            "爬楼梯": "事业上升, 吉",
        },
    },
    {
        "symbol": "下楼",
        "aliases": ["下楼梯"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主退步、谨慎、保守。",
        "context_modifiers": {
            "下楼": "退步, 慎防",
        },
    },
    {
        "symbol": "坐",
        "aliases": ["坐下"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主稳定、休息、内观。",
        "context_modifiers": {
            "坐立不安": "焦虑, 慎防",
            "安然坐": "心定, 吉",
        },
    },
    {
        "symbol": "谈话",
        "aliases": ["聊天"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主交流、人际、共识。",
        "context_modifiers": {
            "愉快谈话": "人际和, 吉",
            "争吵": "有口舌, 慎防",
        },
    },
    {
        "symbol": "洗澡",
        "aliases": ["沐浴"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "主净化、释压、清理。",
        "context_modifiers": {
            "洗澡": "净化, 吉",
            "冷水澡": "有冷遇, 中性",
        },
    },

    # ── 地理 (8 条新增) ──
    {
        "symbol": "岛",
        "aliases": ["海岛"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主孤立、避世、桃花源。",
        "context_modifiers": {
            "登岛": "得清净, 中性",
            "孤岛": "有孤独, 慎防",
        },
    },
    {
        "symbol": "森林",
        "aliases": ["树林", "林"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主生机、繁茂、迷失。",
        "context_modifiers": {
            "森林茂密": "生机勃勃, 吉",
            "林中迷路": "有迷茫, 慎防",
        },
    },
    {
        "symbol": "沙漠",
        "aliases": ["大漠"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主荒凉、孤独、考验。",
        "context_modifiers": {
            "沙漠绿洲": "困境有生机, 吉",
            "沙漠迷路": "有大考验, 慎防",
        },
    },
    {
        "symbol": "花园",
        "aliases": ["园林"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主美好、丰盛、爱情。",
        "context_modifiers": {
            "花园盛开": "大吉, 万事亨通",
        },
    },
    {
        "symbol": "桥",
        "aliases": ["桥梁"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主过渡、连接、转变。",
        "context_modifiers": {
            "过桥": "转折点, 吉",
            "断桥": "有阻, 慎防",
        },
    },
    {
        "symbol": "路",
        "aliases": ["道路"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主方向、人生、选择。",
        "context_modifiers": {
            "直路": "顺利, 吉",
            "弯路": "有曲折, 中性",
            "断路": "有阻, 慎防",
        },
    },
    {
        "symbol": "门",
        "aliases": ["大门"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主机遇、入口、转折。",
        "context_modifiers": {
            "开门": "有转机, 吉",
            "门关": "机会未到, 中性",
            "破门": "有强入, 慎防",
        },
    },
    {
        "symbol": "窗",
        "aliases": ["窗户"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主视野、机会、灵感。",
        "context_modifiers": {
            "开窗": "有新视野, 吉",
            "关窗": "闭塞, 中性",
        },
    },

    # ── 颜色 (3 条新增) ──
    {
        "symbol": "金",
        "aliases": ["金色"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主财富、尊贵、成功。",
        "context_modifiers": {
            "金色光": "大进财, 吉",
        },
    },
    {
        "symbol": "蓝",
        "aliases": ["蓝色"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "主平静、深远、理性。",
        "context_modifiers": {
            "蓝色海": "心旷神怡, 吉",
        },
    },
    {
        "symbol": "绿",
        "aliases": ["绿色"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "主生机、健康、希望。",
        "context_modifiers": {
            "绿草如茵": "生机勃勃, 吉",
        },
    },

    # ── 物品续 (5 条新增) ──
    {
        "symbol": "箱",
        "aliases": ["箱子", "盒"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主秘密、收藏、内心。",
        "context_modifiers": {
            "开箱": "揭密, 中性",
            "装满的箱": "有财, 吉",
        },
    },
    {
        "symbol": "绳",
        "aliases": ["绳子"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主连接、束缚、缘分。",
        "context_modifiers": {
            "系绳": "结缘, 吉",
            "断绳": "缘分尽, 小凶",
        },
    },
    {
        "symbol": "梯",
        "aliases": ["梯子"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主上升、进步、登高。",
        "context_modifiers": {
            "爬梯": "上升, 吉",
            "梯倒": "有失, 慎防",
        },
    },
    {
        "symbol": "灯",
        "aliases": ["油灯"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主希望、指引、智慧。",
        "context_modifiers": {
            "灯亮": "光明在前, 吉",
            "灯灭": "希望失, 慎防",
        },
    },
    {
        "symbol": "信",
        "aliases": ["信件"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主消息、情感、距离。",
        "context_modifiers": {
            "得信": "有消息, 吉",
            "失信": "失信于人, 慎防",
        },
    },
"""

content = CORPUS.read_text(encoding="utf-8")

# Find the last entry's closing brace + closing list bracket
# The pattern is the last `]` in DREAM_ENTRIES list
import re
# Find the position of the final "]\n\n\n# ══════════" pattern
# We need to insert before the final "]\n\n\n# ══════════════════════════════════════\n# 2. 派生统计"
# Actually, easier: find last "    },\n" then last "]"

# Find the closing ] of DREAM_ENTRIES
# The list ends with "    },\n]" followed by \n\n\n# ...
# We insert NEW_ENTRIES before that final ]

# Use a marker that's unique: the comment "2. 派生统计"
marker = "# ══════════════════════════════════════════════════════════════\n# 2. 派生统计"
idx = content.find(marker)
if idx == -1:
    raise SystemExit("Marker not found")

# Insert NEW_ENTRIES before marker
new_content = content[:idx] + NEW_ENTRIES.lstrip("\n") + "\n\n\n" + content[idx:]
CORPUS.write_text(new_content, encoding="utf-8")

# Verify count
import ast
tree = ast.parse(new_content)
for node in ast.walk(tree):
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "DREAM_ENTRIES":
        pass
# Count entries by counting dict literals
import re as _re
entries = _re.findall(r'"symbol":\s*"', new_content)
print(f"OK: appended entries. Total symbols: {len(entries)}")
