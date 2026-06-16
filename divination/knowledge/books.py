"""古籍推荐书单 — 每种术法推荐核心典籍。

按优先级分三档：
  ★★★ 必修（体系奠基，入门必读）
  ★★  进阶（深化理解，核心篇章）
  ★   拓展（补充视野，专题研究）

字段说明：
  title      书名
  dynasty    朝代
  author     作者
  priority   优先级 1=foundational, 2=advanced, 3=supplemental
  difficulty 易读性: beginner / intermediate / advanced
  description 一句话描述
  key_chapters 核心篇章（与 engine 对应的判断逻辑最相关）
  book_file   docs/ 目录下的实际文件（若有）
  url        在线资源链接（若有）
  notes      补充说明
"""
from __future__ import annotations

BOOK_CATALOG: dict[str, list[dict]] = {
    # ═══ 八字（四柱） ═══════════════════════════════════════════════════════════
    "bazi": [
        {
            "title": "渊海子平",
            "dynasty": "宋",
            "author": "徐子平",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "子平八字体系奠基之作，五言独步、玄机赋为核心篇章",
            "key_chapters": ["五言独步", "玄机赋", "论十神", "相心赋", "格局篇"],
            "relevant_rules": ["yhz_001", "yhz_002", "yhz_003", "yhz_004"],
            "notes": "原典已散佚，现有传本为明人掇拾重编；判断以原文能否贯穿命盘为选取标准",
        },
        {
            "title": "滴天髓",
            "dynasty": "明",
            "author": "刘基（诚意伯）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "用神理论体系完整，体用论为分析框架核心，对日元旺衰判断最精",
            "key_chapters": ["天道·体用", "六亲论", "配合篇", "天元", "人道"],
            "relevant_rules": ["dts_001", "dts_002", "dts_003", "dts_004", "dts_005"],
            "notes": "分为天道/地道/人道三篇；原文中'道有体用，不可以一端论'为判断总纲",
        },
        {
            "title": "三命通会",
            "dynasty": "明",
            "author": "万明英",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "格局论、正官七杀论述最为精要；兼论大运、流年",
            "key_chapters": ["卷六·论正官", "卷七·论七杀", "论财", "论印绶", "论大运", "论流年"],
            "relevant_rules": ["smth_001", "smth_002", "smth_003"],
            "notes": "共十二卷，本书收录核心格局；'格局'为判断命局层次的核心框架",
        },
        {
            "title": "子平基础概要",
            "dynasty": "现代",
            "author": "梁湘润",
            "priority": 2,
            "difficulty": "beginner",
            "description": "现代子平入门经典，概念清晰，适合建立框架",
            "key_chapters": ["用神取法", "格局总论", "大运流年"],
            "relevant_rules": [],
            "notes": "非古籍，为现代教学用书；可作为系统学习的第一本",
        },
        {
            "title": "穷通宝鉴",
            "dynasty": "明",
            "author": "徐乐吾",
            "priority": 2,
            "difficulty": "advanced",
            "description": "调候用神体系完整；寒暖燥湿为判断核心",
            "key_chapters": ["调候总纲", "寒暖燥湿", "十天干配十二宫"],
            "relevant_rules": [],
            "notes": "在子平体系外另立调候一脉；适合气候/地域相关判断",
        },
        {
            "title": "御定卜筮精蕴",
            "dynasty": "清",
            "author": "康熙皇帝",
            "priority": 3,
            "difficulty": "intermediate",
            "description": "六爻古籍集成，含六亲、世应、卦象判断",
            "key_chapters": ["六亲章", "世应章", "卦象章"],
            "relevant_rules": [],
            "notes": "原为六爻经典，部分内容可参照于八字六亲判断",
        },
    ],

    # ═══ 紫微斗数 ══════════════════════════════════════════════════════════════
    "ziwei": [
        {
            "title": "紫微斗数全书",
            "dynasty": "明",
            "author": "不详（或托名陈抟）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "紫微斗数体系最古的完整文本；斗数四化派源头",
            "key_chapters": ["星曜篇", "四化篇", "行限篇", "身宫篇"],
            "relevant_rules": [],
            "notes": "现有传本有多系统混合；需以'星曜为主、四化为用'为判读框架",
        },
        {
            "title": "飞星紫微斗数全书",
            "dynasty": "现代",
            "author": "顾祥弘",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "现代飞星派代表作；强调星曜组合与宫位联动",
            "key_chapters": ["星曜组合", "飞星诀", "行运篇"],
            "relevant_rules": [],
            "notes": "现代体系中较完整的一本；有PDF在docs/目录",
        },
        {
            "title": "斗数微经",
            "dynasty": "清",
            "author": "不详",
            "priority": 2,
            "difficulty": "advanced",
            "description": "清代斗数重要注本；对星曜性情与格局有精微论述",
            "key_chapters": ["星性篇", "格局篇", "行限篇"],
            "relevant_rules": [],
            "notes": "较难找，可作进阶研读",
        },
    ],

    # ═══ 大六壬 ════════════════════════════════════════════════════════════════
    "liuren": [
        {
            "title": "大六壬指南",
            "dynasty": "清",
            "author": "陈公献",
            "priority": 1,
            "difficulty": "advanced",
            "description": "九宗门体系完整，是六壬入门和进阶的核心文本",
            "key_chapters": ["九宗门章", "贼克章", "比用章", "涉害章", "昴星章", "伏吟返吟章"],
            "relevant_rules": ["dlr_001", "dlr_002", "dlr_003", "dlr_004", "dlr_005"],
            "notes": "全书分上下两卷；判断以九宗门为框架，课体为判断核心",
        },
        {
            "title": "大六壬大全",
            "dynasty": "清",
            "author": "不祥",
            "priority": 2,
            "difficulty": "advanced",
            "description": "六壬文献集成；含完整的神煞体系与贵人起法",
            "key_chapters": ["神煞篇", "贵人起法", "月将章"],
            "relevant_rules": [],
            "notes": "是神煞判断的重要依据；与八字神煞体系相互参照",
        },
        {
            "title": "六壬金口诀",
            "dynasty": "不祥",
            "author": "不祥",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "六壬另一重要分支；与大雪壬指南并称'六壬双壁'",
            "key_chapters": ["起课章", "判断章", "三传章"],
            "relevant_rules": [],
            "notes": "判断方式与指南略有不同，可作比较研究",
        },
        {
            "title": "大六壬通天银河棹",
            "dynasty": "清",
            "author": "不祥",
            "priority": 3,
            "difficulty": "advanced",
            "description": "六壬古籍珍本；收藏于书格等古籍网站",
            "key_chapters": ["通天篇", "银河棹"],
            "relevant_rules": [],
            "notes": "书格(shuge.org)有高清扫描版；可作专题研究",
        },
    ],

    # ═══ 六爻（纳甲筮法） ══════════════════════════════════════════════════════
    "liuyao": [
        {
            "title": "增删卜易",
            "dynasty": "清",
            "author": "野鹤老人",
            "priority": 1,
            "difficulty": "beginner",
            "description": "六爻入门最流行经典；用神理论为核心",
            "key_chapters": ["论用神", "论旺衰", "世应章", "六亲章", "卦象章"],
            "relevant_rules": ["zsby_001", "zsby_002"],
            "notes": "判断以'用神旺衰'为根本；全书贯穿'用神旺则吉，用神衰则凶'",
        },
        {
            "title": "卜筮正宗",
            "dynasty": "清",
            "author": "王洪绪",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "六爻进阶必备；系统论述六亲、世应、卦象",
            "key_chapters": ["六亲论", "世应论", "卦象论", "进神退神"],
            "relevant_rules": [],
            "notes": "是'用神+世应+动变'三维判断框架的完整阐述",
        },
        {
            "title": "易冒",
            "dynasty": "清",
            "author": "不祥",
            "priority": 2,
            "difficulty": "advanced",
            "description": "六爻进阶古籍；对卦象、动变、应期有精微论述",
            "key_chapters": ["卦象篇", "动变篇", "应期篇"],
            "relevant_rules": [],
            "notes": "重点在'卦象与动变'如何共同指向判断",
        },
        {
            "title": "火珠林",
            "dynasty": "唐",
            "author": "不祥",
            "priority": 3,
            "difficulty": "advanced",
            "description": "六爻最古源头；是'纳甲'体系的早期文献",
            "key_chapters": ["纳甲章", "起卦章"],
            "relevant_rules": [],
            "notes": "唐代原典；现代六爻实为宋明以后在火珠林基础上的发展",
        },
    ],

    # ═══ 奇门遁甲 ══════════════════════════════════════════════════════════════
    "qimen": [
        {
            "title": "烟波钓叟歌",
            "dynasty": "宋",
            "author": "赵普（一说）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "奇门遁甲核心歌诀；'奇门遁甲'体系的理论源头",
            "key_chapters": ["天盘篇", "地盘篇", "人盘篇", "神盘篇"],
            "relevant_rules": [],
            "notes": "原文为七言歌诀；判断以'九宫'为框架结合三奇六仪",
        },
        {
            "title": "高岛易断",
            "dynasty": "日本·明治",
            "author": "高岛吞象",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "奇门与易理结合的典范；现代奇门应用最广的参考文献",
            "key_chapters": ["九宫篇", "三奇篇", "八门篇", "八神篇"],
            "relevant_rules": [],
            "notes": "有9卷PDF版；在dalazy.com等资料站有收录",
        },
        {
            "title": "奇门遁甲全书",
            "dynasty": "不祥",
            "author": "不祥",
            "priority": 2,
            "difficulty": "advanced",
            "description": "奇门遁甲系统古籍；含完整的起局与判断方法",
            "key_chapters": ["起局章", "判断章", "三奇六仪", "八门九星"],
            "relevant_rules": [],
            "notes": "书格(shuge.org)有扫描版",
        },
        {
            "title": "御定卜筮精蕴",
            "dynasty": "清",
            "author": "康熙皇帝",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "奇门部分对判断框架有精要论述",
            "key_chapters": ["奇门章", "九宫章"],
            "relevant_rules": [],
            "notes": "与六爻共用同一书名；判断需结合具体上下文",
        },
    ],

    # ═══ 风水（八宅/玄空） ══════════════════════════════════════════════════════
    "fengshui": [
        {
            "title": "黄帝宅经",
            "dynasty": "汉（后人托名）",
            "author": "不祥",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "形势派风水源头；与阳宅风水理论体系相承",
            "key_chapters": ["形势篇", "宅形篇", "门路篇"],
            "relevant_rules": ["hdzj_001"],
            "notes": "传统风水分为形法/理气两大派；本书为形势派核心",
        },
        {
            "title": "杨公风水地理",
            "dynasty": "唐",
            "author": "杨筠松（救贫）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "理气派风水核心；'分金'、'立向'为实操关键",
            "key_chapters": ["分金篇", "立向篇", "水法篇", "龙脉篇"],
            "relevant_rules": [],
            "notes": "在xueyizone.com等有视频教程和PDF；'杨公地理'为业内公认正统",
        },
        {
            "title": "玄空飞星",
            "dynasty": "清",
            "author": "不祥",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "玄空理气核心；以九宫飞星判断旺衰吉凶",
            "key_chapters": ["飞星篇", "运盘篇", "山向篇"],
            "relevant_rules": [],
            "notes": "玄空飞星是现代阳宅风水最流行的判断体系",
        },
        {
            "title": "八宅明镜",
            "dynasty": "明",
            "author": "不祥",
            "priority": 2,
            "difficulty": "beginner",
            "description": "八宅派体系完整；'东四宅/西四宅'为判断核心",
            "key_chapters": ["东西四宅", "命卦篇", "八门配卦"],
            "relevant_rules": [],
            "notes": "是八宅风水入门最清晰的古籍；与现代八宅判断框架最接近",
        },
    ],

    # ═══ 西方占星 ══════════════════════════════════════════════════════════════
    "western": [
        {
            "title": "Tetrabiblos",
            "dynasty": "古罗马（托勒密）",
            "author": "Claudius Ptolemy",
            "priority": 1,
            "difficulty": "advanced",
            "description": "西方占星学开山之作；奠定了星座/行星/宫位的判断框架",
            "key_chapters": ["Book I: The Principles", "Book II: Genitures", "Book III: Matters Relating to Countries", "Book IV: Countries and Regions"],
            "relevant_rules": ["pt_001"],
            "notes": "有英译本；是唯一进入CLASSICAL_RULES的西方文献",
        },
        {
            "title": "晴明师徒占星课",
            "dynasty": "现代",
            "author": "不祥",
            "priority": 2,
            "difficulty": "beginner",
            "description": "现代西方占星入门；行星、星座、宫位三元体系",
            "key_chapters": ["行星篇", "星座篇", "宫位篇", "相位篇"],
            "relevant_rules": [],
            "notes": "现代占星判断以'行星+星座+宫位'三维为基础",
        },
    ],

    # ═══ 合盘/关系 ══════════════════════════════════════════════════════════════
    "hepan": [
        {
            "title": "星盘合参",
            "dynasty": "现代",
            "author": "不祥",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "西方占星合盘经典；介绍相位、合盘、synastry判断",
            "key_chapters": ["相位篇", "合盘篇", "Synastry篇"],
            "relevant_rules": [],
            "notes": "是合盘判断的主要文献；可与八字合盘对照",
        },
        {
            "title": "八字合婚集成",
            "dynasty": "现代",
            "author": "不祥",
            "priority": 2,
            "difficulty": "beginner",
            "description": "传统八字合婚应用手册；含年柱纳音、日柱天干合化",
            "key_chapters": ["纳音合婚", "天干合化", "地支六合三合"],
            "relevant_rules": [],
            "notes": "传统合婚判断维度；可与现代合盘方法互为补充",
        },
    ],

    # ═══ 塔罗 ════════════════════════════════════════════════════════════════
    "tarot": [
        {
            "title": "韦特塔罗词典",
            "dynasty": "现代",
            "author": "A.E. Waite / Pamela Colman Smith",
            "priority": 1,
            "difficulty": "beginner",
            "description": "RWS体系原型；78张牌图像与关键词定义",
            "key_chapters": ["大阿卡纳", "小阿卡纳四牌组", "凯尔特十字"],
            "relevant_rules": [],
            "notes": "是本引擎RWS塔罗的数据来源；关键词来自公有领域诠释",
        },
        {
            "title": "塔罗葵花宝典",
            "dynasty": "现代",
            "author": "向日葵（蔡桑妮）",
            "priority": 2,
            "difficulty": "beginner",
            "description": "中文塔罗入门经典；适合建立RWS直觉体系",
            "key_chapters": ["牌义详解", "牌阵篇", "逆位解读"],
            "relevant_rules": [],
            "notes": "有PDF在docs/目录；是中文语境最广的塔罗教材",
        },
    ],
}


def get_books_for_method(method: str, max_priority: int = 1) -> list[dict]:
    """返回指定术法的推荐书单。

    Args:
        method: 术法标识，如 "bazi", "liuren"
        max_priority: 只返回 priority <= max_priority 的书（默认1=foundational）
    """
    books = BOOK_CATALOG.get(method, [])
    return [b for b in books if b["priority"] <= max_priority]


def get_all_books() -> dict[str, list[dict]]:
    """返回全部书单。"""
    return BOOK_CATALOG
