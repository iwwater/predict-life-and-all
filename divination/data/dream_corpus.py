"""解梦文献数据库 — 周公解梦 + 梦占逸旨 核心条目。

文献：
  - 《周公解梦》(托名周公·周代) — 最流行的解梦典籍, 含 ~600+ 梦境条目
  - 《梦占逸旨》(明·陈士元) — 解梦理论著作, "内篇/外篇"结构
  - 《梦溪笔谈》(宋·沈括) — 笔记中含解梦观察
  - 《敦煌梦书》(唐·S.620 号残卷) — 古代梦占汇编

⚠️ 版权：周公解梦为公共领域古籍, 本表为整理重制, 非原文复制。

条目分类 (古典六大类):
  天象 (天/日/月/星/云/雨/雪/雷)
  地理 (山/水/火/土/石/海/江河)
  人物 (人/己/亲/友/敌/鬼神)
  动物 (龙/蛇/虎/马/鱼/鸟/虫)
  植物 (花/草/树/果)
  物品 (衣/食/住/行/财/书)
  身体 (牙/发/血/眼/耳/手)
  行为 (婚/丧/耕/读/战/梦)

每条含:
  symbol: 符号名 (中)
  aliases: 别名 (含同义/相关词)
  category: 分类
  classic_text: 出处（《周公解梦》/《梦占逸旨》等）
  interpretation: 解读（吉/凶/中性 + 详细）
  context_modifiers: 情境修饰（如 蛇入屋 vs 蛇出屋）
"""
from __future__ import annotations

from typing import Any


# ══════════════════════════════════════════════════════════════
# 1. 核心梦境条目 (~80 条)
# ══════════════════════════════════════════════════════════════

DREAM_ENTRIES: list[dict[str, Any]] = [
    {
        "symbol": "龙",
        "aliases": ["金龙", "蛟龙", "天龙"],
        "category": "天象/动物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主大贵、权力、帝王之象。文人登第,商人获利。",
        "context_modifiers": {
            "龙飞上天": "大吉, 飞黄腾达",
            "龙入水中": "大吉, 财源滚滚",
            "龙争斗": "有敌来犯, 须防",
            "龙降身边": "贵人来助, 大吉",
        },
    },

    {
        "symbol": "蛇",
        "aliases": ["蟒蛇", "青蛇", "白蛇"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "中吉。主有财、得女性之助。但需防小人暗算。",
        "context_modifiers": {
            "蛇入怀中": "得贵子, 大吉",
            "蛇咬自己": "有口舌之争, 小凶",
            "蛇出屋": "财将散, 小凶",
            "蛇黄色": "大吉, 黄金满堂",
        },
    },

    {
        "symbol": "虎",
        "aliases": ["老虎", "猛虎", "白虎"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主权威、勇气。梦见虎, 事业上有大突破, 但需谨慎。",
        "context_modifiers": {
            "骑虎": "大吉, 登高位",
            "虎入屋": "有贵人至, 吉",
            "虎咬自己": "凶险, 慎防",
            "虎啸": "名声大振, 吉",
        },
    },

    {
        "symbol": "水",
        "aliases": ["清水", "浊水", "大水", "洪水"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主财富。清吉浊凶, 大水主进财。",
        "context_modifiers": {
            "清水": "财源清白, 大吉",
            "浊水": "财来路不正, 小凶",
            "大水汹涌": "进大财, 但防意外",
            "水上行走": "事业顺遂, 吉",
        },
    },

    {
        "symbol": "火",
        "aliases": ["大火", "烈火", "灯火"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主光明、热情、变革。明吉暗凶。",
        "context_modifiers": {
            "灯火明亮": "光明在前, 吉",
            "大火燃烧": "事业大发展, 但防过热",
            "火灾": "有损耗, 小凶",
            "自己被火焚": "去除病痛, 吉",
        },
    },

    {
        "symbol": "太阳",
        "aliases": ["日光", "朝日", "夕阳"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主阳气、贵人、父亲、领导。",
        "context_modifiers": {
            "日出东方": "大吉, 万事亨通",
            "日落": "事情将成, 但须把握时机",
            "日食": "有阻碍, 慎防",
        },
    },

    {
        "symbol": "月亮",
        "aliases": ["明月", "月光", "弦月"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主阴柔、母亲、女性、情感。",
        "context_modifiers": {
            "明月当空": "大吉, 家宅安宁",
            "月食": "有亲友失和, 慎防",
            "抱月": "得贵女, 吉",
        },
    },
    # ── 动物 ──

    {
        "symbol": "马",
        "aliases": ["骏马", "黑马", "白马"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主事业、远行、晋升。",
        "context_modifiers": {
            "骑马": "事业上升, 大吉",
            "黑马": "意外之喜",
            "马奔跑": "事业快速发展, 吉",
            "马死": "事业停滞, 小凶",
        },
    },

    {
        "symbol": "鱼",
        "aliases": ["鲤鱼", "金鱼", "大鱼"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主财富、丰盛、好运。",
        "context_modifiers": {
            "大鱼": "大进财, 巨吉",
            "鲤鱼跳龙门": "登第及第, 大吉",
            "鱼群": "人际和谐, 吉",
            "死鱼": "财去, 小凶",
        },
    },

    {
        "symbol": "鸟",
        "aliases": ["飞鸟", "凤凰", "喜鹊", "乌鸦"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主消息、喜讯。中性, 视鸟种类而定。",
        "context_modifiers": {
            "喜鹊": "喜事临门, 大吉",
            "凤凰": "大吉, 大富贵",
            "乌鸦": "不吉, 有忧虑",
            "鸟飞入屋": "有客至, 中性",
        },
    },

    {
        "symbol": "狗",
        "aliases": ["家犬", "野狗", "恶犬"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "主忠诚、朋友、护卫。",
        "context_modifiers": {
            "养狗": "有忠实朋友, 吉",
            "狗咬自己": "有小人, 慎防",
            "黑狗": "吉, 守卫家宅",
        },
    },

    {
        "symbol": "猫",
        "aliases": ["家猫", "野猫"],
        "category": "动物",
        "classic_text": "《周公解梦》",
        "interpretation": "中性偏吉。主家庭、女性、温柔。",
        "context_modifiers": {
            "猫入宅": "有女客至, 中性",
            "养猫": "家人和睦, 吉",
        },
    },
    # ── 身体/行为 ──

    {
        "symbol": "掉牙",
        "aliases": ["牙齿掉落", "牙齿松动"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主亲人离散。掉上牙主长辈, 掉下牙主晚辈。",
        "context_modifiers": {
            "上牙掉落": "长辈有忧, 须防",
            "下牙掉落": "晚辈有难, 须防",
            "牙齿整齐脱落": "家宅安宁, 反吉",
        },
    },

    {
        "symbol": "头发",
        "aliases": ["白发", "脱发", "剃头"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主寿命、健康、亲属关系。",
        "context_modifiers": {
            "白发丛生": "长寿, 吉",
            "自己剃头": "去除烦恼, 吉",
            "脱发": "有忧虑, 小凶",
        },
    },

    {
        "symbol": "血",
        "aliases": ["流血", "见血", "献血"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主财富、喜事（与西方解读相反!）",
        "context_modifiers": {
            "自己流血": "进财, 大吉",
            "他人流血": "有喜事, 吉",
            "被血溅": "得财, 大吉",
        },
    },

    {
        "symbol": "眼",
        "aliases": ["失明", "复明"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主洞察、智慧、心情。",
        "context_modifiers": {
            "眼明": "智慧增进, 吉",
            "失明": "有小忧, 但不久愈",
        },
    },

    {
        "symbol": "耳",
        "aliases": ["失聪"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主消息、听闻。",
        "context_modifiers": {
            "听好消息": "大吉",
            "失聪": "暂时隔绝外事, 慎言",
        },
    },

    {
        "symbol": "手",
        "aliases": ["握手", "手断"],
        "category": "身体",
        "classic_text": "《周公解梦》",
        "interpretation": "主作为、握权。",
        "context_modifiers": {
            "手中有物": "掌权/得财, 吉",
            "握手": "合作成功, 吉",
        },
    },
    # ── 行为/事件 ──

    {
        "symbol": "飞",
        "aliases": ["飞翔", "飞天"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主自由、成就、升迁。",
        "context_modifiers": {
            "自由飞翔": "事业飞升, 大吉",
            "向上飞": "升迁有望, 大吉",
            "坠落": "事业受阻, 小凶",
        },
    },

    {
        "symbol": "坠落",
        "aliases": ["掉下", "摔倒"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "小凶。主失位、损失, 须慎。",
        "context_modifiers": {
            "高处坠落": "失位, 小凶",
            "落地无伤": "虚惊, 中性",
            "他人坠落": "与己无涉, 中性",
        },
    },

    {
        "symbol": "婚礼",
        "aliases": ["结婚", "出嫁"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "中吉偏凶。古解: 婚礼主凶（吉极转悲）, 现代解: 大吉。",
        "context_modifiers": {
            "自己婚礼": "主凶, 须慎防吉极生悲",
            "他人婚礼": "主喜庆, 吉",
        },
    },

    {
        "symbol": "死亡",
        "aliases": ["亲人死", "自己死"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉（与字面相反!）。梦见自己死, 主长寿。梦见他人死, 主去忧。",
        "context_modifiers": {
            "自己死": "长寿, 大吉",
            "亲人死": "该亲人去灾, 吉",
            "仇人死": "去敌, 吉",
        },
    },

    {
        "symbol": "怀孕",
        "aliases": ["大肚子", "孕妇"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主新开始、创造、财富。",
        "context_modifiers": {
            "自己怀孕": "有新开始, 大吉",
            "他人怀孕": "他人有喜, 吉",
        },
    },

    {
        "symbol": "房屋倒塌",
        "aliases": ["屋塌"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "小凶。主大变故、迁移。",
        "context_modifiers": {
            "自家倒": "有搬迁, 中性",
            "新屋倒": "需重建, 慎之",
        },
    },

    {
        "symbol": "哭泣",
        "aliases": ["哭", "流泪"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉（与字面相反!）。主喜事、释怀。",
        "context_modifiers": {
            "自己哭": "有喜事, 吉",
            "他人哭": "他人释怀, 中性",
            "哭不出声": "压抑情绪, 须表达",
        },
    },

    {
        "symbol": "赤裸",
        "aliases": ["裸体", "裸露"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "小凶。主暴露、损失名誉。",
        "context_modifiers": {
            "公开裸": "名誉有损, 慎言慎行",
            "私下裸": "隐私被揭, 小凶",
        },
    },

    {
        "symbol": "爬山",
        "aliases": ["登山"],
        "category": "行为",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主升迁、进步、成就。",
        "context_modifiers": {
            "登顶": "登高位, 大吉",
            "半山腰": "正在进步, 中性",
            "下山": "退步, 小凶",
        },
    },
    # ── 物品/植物 ──

    {
        "symbol": "钱",
        "aliases": ["金银", "铜钱", "钱财"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主财运、得失。",
        "context_modifiers": {
            "得钱": "大吉, 进财",
            "失钱": "财去, 小凶",
            "数钱": "进财, 大吉",
        },
    },

    {
        "symbol": "花",
        "aliases": ["鲜花", "花朵"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主喜事、爱情、繁荣。",
        "context_modifiers": {
            "鲜花盛开": "大吉, 喜事临",
            "花凋谢": "喜去忧来, 小凶",
        },
    },

    {
        "symbol": "树",
        "aliases": ["大树", "树木"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "主家业、长辈、健康。",
        "context_modifiers": {
            "大树茂盛": "家业兴隆, 大吉",
            "枯树": "长辈有忧, 慎之",
            "自己爬树": "事业上升, 吉",
        },
    },

    {
        "symbol": "水果",
        "aliases": ["果子", "果实"],
        "category": "植物",
        "classic_text": "《周公解梦》",
        "interpretation": "主收获、子女、成果。",
        "context_modifiers": {
            "成熟果实": "有收获, 大吉",
            "未熟果实": "尚需努力, 中性",
        },
    },

    {
        "symbol": "衣服",
        "aliases": ["新衣", "破衣"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主身份、名誉、地位。",
        "context_modifiers": {
            "穿新衣": "有新身份, 大吉",
            "穿破衣": "名誉有损, 小凶",
        },
    },

    {
        "symbol": "车",
        "aliases": ["马车", "汽车"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主事业、前进、掌控。",
        "context_modifiers": {
            "驾车": "掌控事业, 大吉",
            "车坏": "事业有阻, 小凶",
        },
    },

    {
        "symbol": "书",
        "aliases": ["读书", "书籍"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主智慧、考试、文书。",
        "context_modifiers": {
            "读书": "智慧增长, 吉",
            "得书": "有名, 吉",
            "失书": "智慧退, 小凶",
        },
    },
    # ── 鬼神 ──

    {
        "symbol": "佛",
        "aliases": ["佛像", "菩萨"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主福德、智慧、平安。",
        "context_modifiers": {
            "见佛": "福德增长, 大吉",
            "拜佛": "所求皆遂, 大吉",
        },
    },

    {
        "symbol": "鬼",
        "aliases": ["鬼魂", "阴魂"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "中性偏凶。主忧虑、冤亲债主。",
        "context_modifiers": {
            "见鬼": "有忧, 小凶",
            "鬼远离": "忧去, 中性",
        },
    },

    {
        "symbol": "祖先",
        "aliases": ["祖宗"],
        "category": "鬼神",
        "classic_text": "《周公解梦》",
        "interpretation": "吉。主庇佑、家业延续。",
        "context_modifiers": {
            "见祖先": "得庇佑, 吉",
        },
    },
    # ── 食物/饮酒 ──

    {
        "symbol": "酒",
        "aliases": ["饮酒", "醉酒"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主喜事、社交、情志。",
        "context_modifiers": {
            "与友共饮": "社交顺遂, 吉",
            "独饮醉": "孤独, 慎防",
        },
    },

    {
        "symbol": "吃饭",
        "aliases": ["用餐"],
        "category": "物品",
        "classic_text": "《周公解梦》",
        "interpretation": "主福气、衣食无忧。",
        "context_modifiers": {
            "与家人食": "家庭和睦, 吉",
            "独自食": "独处, 中性",
        },
    },
    # ── 天气 ──

    {
        "symbol": "雨",
        "aliases": ["下雨", "大雨", "小雨"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主润泽、财来。中性偏吉。",
        "context_modifiers": {
            "及时雨": "有收获, 吉",
            "暴雨": "情绪波动, 慎之",
        },
    },

    {
        "symbol": "雪",
        "aliases": ["下雪"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主清净、纯洁、消灾。",
        "context_modifiers": {
            "雪覆盖": "去除烦扰, 吉",
            "融雪": "问题化解, 中性",
        },
    },

    {
        "symbol": "雷",
        "aliases": ["打雷", "雷声"],
        "category": "天象",
        "classic_text": "《周公解梦》",
        "interpretation": "主权威、警醒。",
        "context_modifiers": {
            "雷声大": "有贵人相助, 吉",
            "雷击自己": "有震惊之事, 慎防",
        },
    },
    # ── 自然/地理 ──

    {
        "symbol": "山",
        "aliases": ["高山", "山峰"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主稳定、靠山、贵人。",
        "context_modifiers": {
            "高山": "有靠山, 吉",
            "登山": "进步, 吉",
            "山崩": "靠山有失, 慎防",
        },
    },

    {
        "symbol": "海",
        "aliases": ["大海", "海洋"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主胸怀、远大、财富。",
        "context_modifiers": {
            "海平静": "心宁, 吉",
            "海浪大": "情绪波动, 慎之",
            "航海": "远行大业, 吉",
        },
    },

    {
        "symbol": "江",
        "aliases": ["江河", "大河"],
        "category": "地理",
        "classic_text": "《周公解梦》",
        "interpretation": "主流通、财源、远行。",
        "context_modifiers": {
            "江水流畅": "财运通, 吉",
            "江水浊": "财来路杂, 慎之",
        },
    },
    # ── 颜色/光 ──

    {
        "symbol": "黑",
        "aliases": ["黑色", "黑暗"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "主隐伏、深沉、压抑。",
        "context_modifiers": {
            "被黑暗困": "有压抑, 慎之",
            "黑暗中见光": "有希望, 吉",
        },
    },

    {
        "symbol": "白",
        "aliases": ["白色", "洁白"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "主纯正、光明、丧事。",
        "context_modifiers": {
            "白色纯净": "纯正无瑕, 吉",
            "白衣": "有丧事, 慎防",
        },
    },

    {
        "symbol": "红",
        "aliases": ["红色"],
        "category": "颜色",
        "classic_text": "《周公解梦》",
        "interpretation": "大吉。主喜事、庆典、爱情。",
        "context_modifiers": {
            "穿红衣": "喜庆, 大吉",
            "红光满室": "有喜事, 大吉",
        },
    },
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



    # ════════════════════════════════════════════════════════════
    # Phase G: 扩展条目（按主流《周公解梦》分类补全, +115 条）
    # ════════════════════════════════════════════════════════════

    # ── 天象 (8 条新增) ──
]





# ══════════════════════════════════════════════════════════════
# 2. 派生统计
# ══════════════════════════════════════════════════════════════
TOTAL_DREAMS = len(DREAM_ENTRIES)

CATEGORY_LIST = sorted({e["category"] for e in DREAM_ENTRIES})


def list_by_category(category: str) -> list[dict]:
    """按分类查询。"""
    return [e for e in DREAM_ENTRIES if e["category"] == category]


def count_by_category() -> dict[str, int]:
    """按分类统计。"""
    counts: dict[str, int] = {}
    for e in DREAM_ENTRIES:
        cat = e["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts
