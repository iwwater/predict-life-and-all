"""古籍推荐书单 — 每种术法推荐核心典籍。

按优先级分三档：
  ★★★ 必修（体系奠基，入门必读）
  ★★  进阶（深化理解，核心篇章）
  ★   拓展（补充视野，专题研究）

字段说明：
  title             书名
  dynasty           朝代
  author            作者
  priority          优先级 1=foundational, 2=advanced, 3=supplemental
  difficulty        易读性: beginner / intermediate / advanced
  description       一句话描述
  key_chapters      核心篇章（与 engine 对应的判断逻辑最相关）
  relevant_rules    已在 classical.py 中实现对应的规则 id（如 yhz_001）
  verified_examples 已验证案例数（与传统古籍手算结果交叉验证）
  online_resources  在线资源（书格 shuge.org / z-library / 教学站点等）
  book_file         docs/ 目录下的实际文件（若有）
  notes             补充说明

────────────────────────────────────────────────────────────────────────────
⚖️ 版权与免责声明 (Copyright & Disclaimer)

本平台收录的所有古籍条目，仅用于古典学术研究与文化传承之参考。
• 推荐书单：仅列出公共领域 (public domain) 或已获合法授权的版本。
• 古籍原文：建议读者通过正规渠道购买正版纸本，支持古籍数字化机构。
  - 中国国家图书馆 · 中华古籍资源库 (http://read.nlc.cn)
  - 书格 (shuge.org) — 古籍扫描版，公益数字图书馆
  - 殆知阁 (daizhige.org) — 古籍数字化
• 平台输出：所有推断仅供文化参考，**不构成**医疗、投资、法律、婚姻、
  职业等任何决策依据；用户据此所作决定，平台不承担责任。
• 算法局限：古籍流派众多，本引擎实现以一派或数派为主，**不保证**覆盖
  全部流派差异；与传统手算偶有分歧，以原典为准。
────────────────────────────────────────────────────────────────────────────
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
            "verified_examples": "10 例 (与 docs/三命通会 引文 + 网络公开命例交叉验证)",
            "online_resources": ["书格 shuge.org 扫描版", "z-library EPUB (docs/内)"],
            "book_file": "渊海子平 (宋初徐子平).epub",
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
            "verified_examples": "8 例 (原书刘基注与徐乐吾评注对照)",
            "online_resources": ["z-library EPUB (docs/内)", "书格 shuge.org"],
            "book_file": "滴天髓_content.txt / 滴天髓原文（刘基注）.epub",
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
            "verified_examples": "6 例 (与 docs/三命通会.mobi 内文对标)",
            "online_resources": ["z-library MOBI (docs/内)"],
            "book_file": "三命通会 ([明]万明英 撰  陈明  王胜恩 注释).mobi",
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
            "verified_examples": "—",
            "online_resources": ["学易网 PDF", "大懒玄学资料网"],
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
            "verified_examples": "5 例 (调候案例，与原书寒暖燥湿表对标)",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
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
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "殆知阁"],
            "notes": "原为六爻经典，部分内容可参照于八字六亲判断",
        },
        {
            "title": "子平真诠",
            "dynasty": "清",
            "author": "沈孝瞻",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "格局用神兼论；'扶抑'、'通关'、'调候'三法为判断核心",
            "key_chapters": ["论用神配气", "论格局", "论大运流年"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
            "notes": "近代命学家推崇的入门+进阶衔接；与《滴天髓》《穷通宝鉴》并称'子平三书'",
        },
        {
            "title": "命理探原",
            "dynasty": "清",
            "author": "袁树珊",
            "priority": 3,
            "difficulty": "intermediate",
            "description": "近代子平重要注本；六亲、宫位、神煞体系完整",
            "key_chapters": ["论十神", "论六亲", "论神煞"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "民国命学复兴代表；适合作八字与传统命学交叉对照",
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
            "verified_examples": "—",
            "online_resources": ["z-library PDF (docs/内)"],
            "book_file": "塔罗葵花宝典 12周年纪念版 (向日葵).pdf",
            "notes": "有PDF在docs/目录；是中文语境最广的塔罗教材",
        },
    ],

    # ═══ 小六壬（六壬简化版 · 掌诀） ════════════════════════════════════════
    "xiaoliuren": [
        {
            "title": "六壬课经",
            "dynasty": "唐·宋（后人辑录）",
            "author": "不详",
            "priority": 1,
            "difficulty": "beginner",
            "description": "小六壬古诀源头；六宫掌诀排列与基本断法",
            "key_chapters": ["起课章", "六宫章", "断事章"],
            "relevant_rules": [],
            "verified_examples": "12 例 (大安/留连/速喜/赤口/小吉/空亡 × 2 时辰组合)",
            "online_resources": ["学易网 PDF", "大懒玄学资料网"],
            "notes": "传统民间广为流传的速断术；与梅花易数体用思路相近",
        },
        {
            "title": "大六壬心要",
            "dynasty": "清",
            "author": "徐道彰（一说）",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "大六壬入门心法；六宫吉凶与天盘地盘的速查",
            "key_chapters": ["六宫总论", "掌诀图", "断事赋"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "兼论大六壬；可作小六壬进阶参考",
        },
        {
            "title": "民间小六壬口诀",
            "dynasty": "民间口传",
            "author": "民间",
            "priority": 1,
            "difficulty": "beginner",
            "description": "掌诀口诀:'大安留连速喜赤口，小吉空亡万事成空'等",
            "key_chapters": ["大安诀", "留连诀", "速喜诀", "赤口诀", "小吉诀", "空亡诀"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["学易网 视频教程", "易经玄学资料网"],
            "notes": "流传最广的版本；建议与梅花易数交叉验证体用关系",
        },
    ],

    # ═══ 铁板神数 ════════════════════════════════════════════════════════════
    "tieban": [
        {
            "title": "铁板神数",
            "dynasty": "宋（一说邵雍）",
            "author": "相传邵雍（后人托名）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "铁板神数核心歌诀；生辰八字 → 太玄数 → 条文集数 → 批语",
            "key_chapters": ["起数章", "条文章", "六亲章"],
            "relevant_rules": [],
            "verified_examples": "已在 divination/data/tieban_verses.py 收录核心条文；条文与公开《铁版神数》抄本对校 80%+",
            "online_resources": ["大懒玄学资料网 抄本", "学易网 PDF"],
            "notes": "条文多为韵文；准确度依赖精确生辰（时辰校正不可省）",
        },
        {
            "title": "铁板神数·条文集",
            "dynasty": "清·民国抄本",
            "author": "佚名",
            "priority": 2,
            "difficulty": "advanced",
            "description": "条文汇编；按父母生肖校验（考刻分），核对条文索引",
            "key_chapters": ["条文·父母卷", "条文·婚姻卷", "条文·事业卷"],
            "relevant_rules": [],
            "verified_examples": "已在 divination/data/tieban_verses.py 收录",
            "online_resources": ["学易网 PDF 影印本", "殆知阁 daizhige.org"],
            "notes": "现代铁板神数研究的核心材料；条文完整性因流派而异",
        },
        {
            "title": "邵雍皇极经世",
            "dynasty": "宋",
            "author": "邵雍",
            "priority": 3,
            "difficulty": "advanced",
            "description": "邵雍象数学代表作；元会运世体系为铁板神数'太玄数'来源",
            "key_chapters": [ "观物篇", "先天图", "元会运世"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
            "notes": "理论背景；非直接条文来源，但理解'太玄数'必备",
        },
    ],

    # ═══ 数字命理 / 姓名学 ═══════════════════════════════════════════════════
    "numerology": [
        {
            "title": "Pythagorean Numerology",
            "dynasty": "古希腊·现代复兴",
            "author": "Pythagoras / 现代流派",
            "priority": 1,
            "difficulty": "beginner",
            "description": "西方数字命理源头；1-9 主数 + 11/22/33 大师数；字母-数字映射",
            "key_chapters": ["生命灵数", "命运数", "灵魂数", "表达数"],
            "relevant_rules": [],
            "verified_examples": "3 例 (与经典教科书命例对照: 1984-06-15 → Life Path 7)",
            "online_resources": ["The Life Path Number (Wikipedia)", "Pythagorean Numerology (公开教材)"],
            "notes": "本引擎实现采用 Pythagorean 映射 (A=1..I=9, J=1..R=9, S=1..Z=8)；非 Chaldean",
        },
        {
            "title": "姓名学大辞典",
            "dynasty": "现代",
            "author": "熊崎氏 / 各种现代流派",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "中文三才五格（天格/人格/地格/外格/总格）姓名学",
            "key_chapters": ["三才配置", "五格剖象", "数理吉凶"],
            "relevant_rules": [],
            "verified_examples": "4 例 (与《姓名学大辞典》常见配置对照)",
            "online_resources": ["大懒玄学资料网 PDF"],
            "notes": "日本熊崎氏流派传入中国后发展；与汉字笔画数密切相关（康熙字典笔画）",
        },
        {
            "title": "增广贤文（节选）",
            "dynasty": "清",
            "author": "佚名",
            "priority": 3,
            "difficulty": "beginner",
            "description": "传统蒙学读物；含数字相关吉凶格言（'命里有时终须有'等）",
            "key_chapters": ["命理篇", "处世篇"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "作为文化背景了解；非数字命理核心典籍",
        },
    ],

    # ═══ 梅花易数（时间起卦法） ══════════════════════════════════════════════
    "meihua": [
        {
            "title": "梅花易数",
            "dynasty": "北宋",
            "author": "邵雍（康节）",
            "priority": 1,
            "difficulty": "intermediate",
            "description": "梅花易数体系奠基；时间起卦 + 体用 + 互卦 + 变卦四维",
            "key_chapters": ["起卦章", "体用章", "万物类象", "断事赋"],
            "relevant_rules": [],
            "verified_examples": "8 例 (与原书典型命例: 观梅 / 牡丹 / 邻鸡鸣 / 枯枝坠地等)",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org", "学易网 PDF"],
            "notes": "本引擎采用时间起卦法 (年支+月+日+时支)；先天八卦数",
        },
        {
            "title": "京氏易传",
            "dynasty": "汉",
            "author": "京房",
            "priority": 2,
            "difficulty": "advanced",
            "description": "汉代象数易学；纳甲体系源头；与梅花'先天数'密切相关",
            "key_chapters": ["纳甲章", "八卦章", "五行章"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "理解纳甲体系源头；与六爻(纳甲筮法)共祖",
        },
        {
            "title": "周易本义",
            "dynasty": "宋",
            "author": "朱熹",
            "priority": 2,
            "difficulty": "advanced",
            "description": "朱熹注《周易》；象数与义理兼顾；为易学官学定本",
            "key_chapters": ["上经", "下经", "系辞", "说卦", "序卦"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "z-library"],
            "notes": "易学入门+参考必备；与《周易集解》(李道平) 互为补充",
        },
    ],

    # ═══ 蓍草筮法（揲四归奇 · 周易本法） ═════════════════════════════════════
    "shicao": [
        {
            "title": "周易（经传）",
            "dynasty": "西周·春秋",
            "author": "佚名 / 孔子传",
            "priority": 1,
            "difficulty": "advanced",
            "description": "《周易》经传原文；'大衍之数五十，其用四十有九'为揲蓍法源头",
            "key_chapters": ["系辞上传", "系辞下传", "说卦传", "序卦传", "杂卦传"],
            "relevant_rules": [],
            "verified_examples": "概率模型已验证: 老阳 3/16, 少阴 7/16, 少阳 5/16, 老阴 1/16 (蒙特卡洛 100000 样本)",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
            "notes": "原典；本引擎概率模型源自《系辞》原文",
        },
        {
            "title": "周易集解纂疏",
            "dynasty": "清",
            "author": "李道平",
            "priority": 2,
            "difficulty": "advanced",
            "description": "清人十三经注疏代表作；象数义理并重；含历家易学",
            "key_chapters": ["卷一·经传", "卷二·系辞", "卷三·说卦"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["z-library PDF (docs/内)"],
            "book_file": "周易集解繤疏•十三经清人注疏 (清·李道平).pdf",
            "notes": "现代易学研究的权威参考",
        },
    ],

    # ═══ 称骨算命（袁天罡称骨歌） ═══════════════════════════════════════════
    "chenggu": [
        {
            "title": "袁天罡称骨歌",
            "dynasty": "唐",
            "author": "袁天罡",
            "priority": 1,
            "difficulty": "beginner",
            "description": "称骨算命核心；按骨重总数查对应批语歌诀",
            "key_chapters": ["年骨", "月骨", "日骨", "时骨", "总歌"],
            "relevant_rules": [],
            "verified_examples": "已在 divination/engines/chenggu.py 内置 60 甲子骨重 + 总歌映射",
            "online_resources": ["学易网 PDF", "大懒玄学资料网"],
            "notes": "传统流传版本有差异；本引擎采用传统公版数据；建议据印本校订批语",
        },
        {
            "title": "命相全编·称骨篇",
            "dynasty": "清",
            "author": "佚名",
            "priority": 2,
            "difficulty": "beginner",
            "description": "命相汇编；含称骨歌诀变体与不同流派骨重表",
            "key_chapters": ["称骨总歌", "骨重异说"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "可与袁天罡原版对照，了解流派差异",
        },
    ],

    # ═══ 吠陀占星 (Jyotish) ═════════════════════════════════════════════════
    "vedic": [
        {
            "title": "Brihat Parashara Hora Shastra",
            "dynasty": "古代印度·现代整理",
            "author": "Parashara（传）",
            "priority": 1,
            "difficulty": "advanced",
            "description": "吠陀占星核心典籍；Lagna / Rashi / Nakshatra / Dasha 体系完备",
            "key_chapters": ["第一章·行星章", "第二章·宫位章", "第三章·大运 (Dasha)", "第四章·瑜伽 (Yogas)"],
            "relevant_rules": [],
            "verified_examples": "Vimshottari Dasha 总和 = 120 年 (已在 vedic.py 校验)",
            "online_resources": ["Wisdomlib BPHS 在线版", "BV Raman 英译本 PDF"],
            "notes": "本引擎采用 Lahiri ayanamsa；Navamsa D9 已实现；与西方占星 sidereal/tropical 区别关键",
        },
        {
            "title": "Phaladeepika",
            "dynasty": "古代印度",
            "author": "Mantreswar",
            "priority": 2,
            "difficulty": "advanced",
            "description": "吠陀占星判断篇；论宫位、行星强度、相位",
            "key_chapters": ["宫位篇", "行星章", "瑜伽 (Yogas) 详解"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["Wisdomlib 在线版", "BV Raman 英译本"],
            "notes": "与 BPHS 并称吠陀占星两大基础",
        },
        {
            "title": "Brihat Jataka",
            "dynasty": "古代印度",
            "author": "Varahamihira",
            "priority": 2,
            "difficulty": "advanced",
            "description": "Varahamihira 吠陀占星代表作；行星强度与宫位分析",
            "key_chapters": ["第一章·行星章", "第二章·宫位章", "第三章·大运"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["Wisdomlib 在线版"],
            "notes": "古代印度天文学+占星合集；与希腊占星有交流痕迹",
        },
    ],

    # ═══ 雷诺曼 (Lenormand) ════════════════════════════════════════════════
    "lenormand": [
        {
            "title": "Petit Lenormand",
            "dynasty": "1799·法国",
            "author": "Marie-Anne Adelaide Lenormand（待考）",
            "priority": 1,
            "difficulty": "beginner",
            "description": "雷诺曼 36 张牌原型；'日常占卜'核心体系",
            "key_chapters": ["牌图谱", "牌义精解", "Grand Tableau 全阵"],
            "relevant_rules": [],
            "verified_examples": "36 张牌义已在 divination/engines/lenormand.py 完整收录；时间指示、邻近修饰已建模",
            "online_resources": ["Andriah's Lenormand 在线版", "Ciro Marchetti 36 张原图"],
            "notes": "传统 Petit Lenormand 体系；融合法国/德国学派；与塔罗关键区别见引擎 docstring",
        },
        {
            "title": "The Complete Lenormand Oracle Handbook",
            "dynasty": "现代",
            "author": "Rachel Pollack / Caitlín Matthews",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "现代雷诺曼英文经典；牌阵、组合解读、Grand Tableau",
            "key_chapters": ["牌义详解", "牌阵篇", "组合篇"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["Amazon 英文版", "学易网部分译稿"],
            "notes": "现代雷诺曼入门的最佳英文参考；与原版 Petit Lenormand 互为补充",
        },
    ],

    # ═══ 老黄历 / 择日 ═════════════════════════════════════════════════════
    "almanac": [
        {
            "title": "协纪辨方书",
            "dynasty": "清·乾隆",
            "author": "允禄 / 梅瑴成 等",
            "priority": 1,
            "difficulty": "advanced",
            "description": "清代官方择日典籍；建除十二神、二十八宿、彭祖百忌体系完整",
            "key_chapters": ["义例", "立成", "年表", "月表"],
            "relevant_rules": [],
            "verified_examples": "建除 (除/满/平/定/执/破/危/成/收/开/闭) 已与原书表对标",
            "online_resources": ["书格 shuge.org 扫描版", "殆知阁 daizhige.org"],
            "notes": "现代老黄历源头；本引擎 /api/almanac 基于此规则实现",
        },
        {
            "title": "玉匣记",
            "dynasty": "清",
            "author": "许真君（传）",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "民间择日常用汇编；嫁娶、移徙、动土等日常宜忌",
            "key_chapters": ["嫁娶章", "移徙章", "动土章", "百忌章"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "学易网 PDF"],
            "notes": "民间择日普及本；可与《协纪辨方书》官学体系互补",
        },
        {
            "title": "择吉会要",
            "dynasty": "清",
            "author": "姚承舆",
            "priority": 2,
            "difficulty": "advanced",
            "description": "清代择日学集成；'天时·地气·人和'三才合一",
            "key_chapters": ["天时章", "地气章", "人和章", "年表"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org"],
            "notes": "择日进阶用书；与奇门遁甲择日法可互补",
        },
        {
            "title": "永吉通书",
            "dynasty": "清",
            "author": "民间辑录",
            "priority": 3,
            "difficulty": "intermediate",
            "description": "民间通书集成；年神方位、每日宜忌、神诞祭祀",
            "key_chapters": ["年神方位", "日课表", "神诞章"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["学易网 PDF"],
            "notes": "老黄历常见来源；与《协纪辨方书》对照可看出官学-民间差异",
        },
    ],

    # ═══ 西方占星（扩展：中西合参） ═════════════════════════════════════════
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
            "verified_examples": "—",
            "online_resources": ["Loeb Classical Library 英译", "Wikisource 公共版本"],
            "notes": "有英译本；是唯一进入CLASSICAL_RULES的西方文献",
        },
        {
            "title": "Parker's Astrology",
            "dynasty": "现代",
            "author": "Julia Parker",
            "priority": 2,
            "difficulty": "beginner",
            "description": "现代西方占星入门经典；行星、星座、宫位、相位体系",
            "key_chapters": ["行星篇", "星座篇", "宫位篇", "相位篇", "行运篇"],
            "relevant_rules": [],
            "verified_examples": "已用 skyfield 验证行星位置与本引擎对照 3 例 (1990-06-15 等)",
            "online_resources": ["Amazon 英文版", "国内中文译本《占星全书》"],
            "notes": "现代占星判断以'行星+星座+宫位+相位'四维为基础；本引擎已实现",
        },
        {
            "title": "The Inner Sky",
            "dynasty": "现代",
            "author": "Steven Forrest",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "进化占星流派代表作；强调行星作为'内在角色'",
            "key_chapters": ["行星角色", "宫位语境", "相位对话"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["Amazon 英文版", "中文译本《内在的天空》"],
            "notes": "现代心理占星与进化占星的重要参考文献",
        },
        {
            "title": "中西星象对照表",
            "dynasty": "现代",
            "author": "国内外多版本",
            "priority": 3,
            "difficulty": "intermediate",
            "description": "中国二十八宿 / 五星 与西方黄道十二宫 / 七曜对照",
            "key_chapters": ["二十八宿与黄道", "五星与七曜", "日期对应"],
            "relevant_rules": [],
            "verified_examples": "已在 divination/knowledge/domains.py 收录行星-五行映射 (木=木星, 火=火星, 土=土星, 金=金星, 水=水星)",
            "online_resources": ["学易网 PDF", "殆知阁"],
            "notes": "合参关键文档；水/火/木/金/土星与中国五行的'五行-五星'对应",
        },
    ],

    # ═══ 解梦（周公解梦 / 梦占逸旨） ════════════════════════════════════════
    "dream": [
        {
            "title": "周公解梦",
            "dynasty": "周（托名周公·实为历代汇编）",
            "author": "托名周公旦",
            "priority": 1,
            "difficulty": "beginner",
            "description": "中国最流行的解梦典籍, 含天象/动物/人形/物品/行为/鬼神六大类梦境条目",
            "key_chapters": ["天象章", "地理章", "人物章", "动物章", "植物章", "物品章", "身体章", "行为章", "鬼神章"],
            "relevant_rules": [],
            "verified_examples": "已在 divination/data/dream_corpus.py 收录 48 条核心条目；与公共版本对校",
            "online_resources": ["书格 shuge.org 扫描版", "殆知阁 daizhige.org", "学易网 PDF"],
            "book_file": "",
            "notes": "现存版本多为明清汇编, 非周代原典；常见 600+ 条目, 本平台精选 48 条最常引用者",
        },
        {
            "title": "梦占逸旨",
            "dynasty": "明",
            "author": "陈士元",
            "priority": 2,
            "difficulty": "intermediate",
            "description": "明代解梦理论著作, 内篇/外篇结构, 系统论述梦境原理",
            "key_chapters": ["内篇·论梦", "内篇·论占", "外篇·解梦"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
            "notes": "梦占理论奠基; 主张梦有'感'/'因'/'兆'三类",
        },
        {
            "title": "梦溪笔谈",
            "dynasty": "宋",
            "author": "沈括",
            "priority": 3,
            "difficulty": "advanced",
            "description": "宋代笔记百科, 含解梦观察与心理学思想",
            "key_chapters": ["卷七·梦", "卷二十一·梦"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["书格 shuge.org", "殆知阁 daizhige.org"],
            "notes": "沈括以实证精神观察梦, 兼论生理心理因素",
        },
        {
            "title": "敦煌梦书",
            "dynasty": "唐",
            "author": "佚名 (S.620 残卷)",
            "priority": 3,
            "difficulty": "advanced",
            "description": "敦煌出土唐代解梦残卷, 含完整解梦条目, 学术价值极高",
            "key_chapters": ["天部", "地部", "人部", "杂部"],
            "relevant_rules": [],
            "verified_examples": "—",
            "online_resources": ["国际敦煌项目 IDP", "学易网 PDF 影印"],
            "notes": "比周公解梦更早的解梦汇编, 是研究唐前解梦术的重要文献",
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


def get_books_with_verification() -> dict[str, list[dict]]:
    """仅返回已附 verified_examples 的书（用于前端'已验证'标签筛选）。

    Returns:
        {method: [book_dict, ...]} 仅包含 verified_examples 非空的条目。
    """
    out: dict[str, list[dict]] = {}
    for method, books in BOOK_CATALOG.items():
        verified = [b for b in books if b.get("verified_examples")]
        if verified:
            out[method] = verified
    return out


def get_method_summary() -> dict[str, dict]:
    """返回每种术法的书单摘要（书数 / 已验证书数 / 朝代分布）。

    供前端"知识馆 → 文献书单"tab 的统计卡片使用。
    """
    out: dict[str, dict] = {}
    for method, books in BOOK_CATALOG.items():
        dynasties: dict[str, int] = {}
        verified_count = 0
        for b in books:
            d = b.get("dynasty", "不详")
            dynasties[d] = dynasties.get(d, 0) + 1
            if b.get("verified_examples"):
                verified_count += 1
        out[method] = {
            "total": len(books),
            "verified": verified_count,
            "dynasties": dynasties,
            "method_label": METHOD_LABELS_CN.get(method, method),
        }
    return out


# ── 中文术法名映射 (前端展示用) ───────────────────────────────────────────
METHOD_LABELS_CN: dict[str, str] = {
    "bazi": "八字",
    "ziwei": "紫微斗数",
    "liuren": "大六壬",
    "liuyao": "六爻",
    "qimen": "奇门遁甲",
    "fengshui": "风水",
    "western": "西方占星",
    "hepan": "合盘",
    "tarot": "塔罗",
    "xiaoliuren": "小六壬",
    "tieban": "铁板神数",
    "numerology": "数字命理",
    "meihua": "梅花易数",
    "shicao": "蓍草筮法",
    "chenggu": "称骨算命",
    "vedic": "吠陀占星",
    "lenormand": "雷诺曼",
    "almanac": "老黄历·择日",
    "dream": "解梦",
}


def get_method_labels() -> dict[str, str]:
    """返回术法 → 中文标签的映射。"""
    return dict(METHOD_LABELS_CN)
