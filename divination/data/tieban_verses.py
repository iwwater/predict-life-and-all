"""铁板神数条文数据库 — 扩展版 (~150 条核心条文).

传统铁板神数有 12,000+ 条条文,本实现为 MVP 扩展子集.

字段:
    verse_set      条文集数（4 位数）
    categories     分类 → 条文列表（按条文编号）
    checksum       校验和（条文编号 +3 位随机数）

考刻分（父母生肖校验）:
    当用户输入父母生肖时,可筛选对应 verse_set;
    校验算法见 tbs_002 (classical.py)。
"""
from __future__ import annotations

# ── 主要条文集 ─────────────────────────────────────────────
TIEBAN_VERSES: dict[str, dict] = {

    # ═══ 集数 1000-1099: 父母 ═══
    "1000-1099": {
        "verse_set": 1050,
        "categories": {
            "父母": [
                {"number": 1, "text": "椿萱并茂,兰桂齐芳,父母双全之命也。", "checksum": 312},
                {"number": 2, "text": "椿庭先逝,萱草犹荣,父早亡而母长寿。", "checksum": 418},
                {"number": 3, "text": "萱堂早萎,椿树长青,母先逝而父在堂。", "checksum": 523},
                {"number": 4, "text": "父母俱存,寿考康宁,享天伦之乐。", "checksum": 647},
                {"number": 5, "text": "幼年失怙,赖母抚养,克勤克俭以成家。", "checksum": 731},
                {"number": 6, "text": "慈母早逝,严父兼教养之恩,刚毅自立。", "checksum": 856},
                {"number": 7, "text": "双亲年高德劭,福寿双全,晚景安康。", "checksum": 924},
                {"number": 8, "text": "父母缘薄,少小离家,自立门户有成。", "checksum": 103},
                {"number": 9, "text": "过继之命,养父母恩深,视如己出。", "checksum": 712},
                {"number": 10, "text": "父母远行,聚少离多,然孝心不减。", "checksum": 825},
                {"number": 11, "text": "父有外室,嫡庶分明,主早年多扰。", "checksum": 938},
                {"number": 12, "text": "父母皆出于书香,家教甚严,有以成名。", "checksum": 146},
                {"number": 13, "text": "幼失双亲,赖祖父母或外祖父母抚养成人。", "checksum": 259},
                {"number": 14, "text": "父母晚年多病,主事必躬亲以尽孝道。", "checksum": 363},
                {"number": 15, "text": "父教甚严,母慈爱有加,文武兼备之家教。", "checksum": 475},
            ],
        },
    },

    # ═══ 集数 1100-1199: 兄弟 ═══
    "1100-1199": {
        "verse_set": 1150,
        "categories": {
            "兄弟": [
                {"number": 1, "text": "手足众多,兄弟三四,和睦相处,各有所成。", "checksum": 215},
                {"number": 2, "text": "兄弟二人,兄友弟恭,互相扶持。", "checksum": 327},
                {"number": 3, "text": "独子无兄弟,然朋友如手足,多得贵人相助。", "checksum": 439},
                {"number": 4, "text": "昆仲虽多,缘分浅薄,各奔前程。", "checksum": 541},
                {"number": 5, "text": "兄弟三四人,中有贵显者,可资依托。", "checksum": 658},
                {"number": 6, "text": "姊妹众多,兄弟稀少,阴盛阳衰之象。", "checksum": 762},
                {"number": 7, "text": "长兄如父,幼弟赖之,手足情深。", "checksum": 875},
                {"number": 8, "text": "兄弟争产,各怀异志,宜早分家。", "checksum": 981},
                {"number": 9, "text": "异母兄弟,虽非同胞,情同手足。", "checksum": 193},
                {"number": 10, "text": "兄姊提携,弟妹依附,家族和睦。", "checksum": 308},
                {"number": 11, "text": "兄弟各立门户,中年后方才来往密切。", "checksum": 421},
                {"number": 12, "text": "有同胞而中途夭折,主悲痛一生。", "checksum": 537},
            ],
        },
    },

    # ═══ 集数 1200-1299: 夫妻 ═══
    "1200-1299": {
        "verse_set": 1250,
        "categories": {
            "夫妻": [
                {"number": 1, "text": "鸾凤和鸣,夫妻偕老,白头齐眉之庆。", "checksum": 113},
                {"number": 2, "text": "琴瑟调和,夫唱妇随,家道兴隆。", "checksum": 224},
                {"number": 3, "text": "早婚不利,迟配方宜,三十后婚为吉。", "checksum": 336},
                {"number": 4, "text": "克妻之命,宜配年长或年幼者化解。", "checksum": 448},
                {"number": 5, "text": "夫星不显,妻宫得力,家有贤内助。", "checksum": 552},
                {"number": 6, "text": "夫妻聚少离多,然感情深厚,不因远而疏。", "checksum": 669},
                {"number": 7, "text": "梅开二度,前婚不终,后配方得长久。", "checksum": 773},
                {"number": 8, "text": "孤鸾之命,宜修身养性,不急于婚配。", "checksum": 887},
                {"number": 9, "text": "妻财丰厚,因婚得福,家业日隆。", "checksum": 992},
                {"number": 10, "text": "夫妻恩爱,白首同心,家道昌盛。", "checksum": 108},
                {"number": 11, "text": "老夫少妻,琴瑟和谐,晚年得伴。", "checksum": 259},
                {"number": 12, "text": "异路姻缘,远嫁他乡或娶外邦之女。", "checksum": 363},
                {"number": 13, "text": "妻贤而早逝,中年再娶方得长久。", "checksum": 471},
                {"number": 14, "text": "晚婚得佳偶,中年夫妻情深意长。", "checksum": 585},
                {"number": 15, "text": "夫妻共白首,儿孙绕膝,福禄双全。", "checksum": 693},
            ],
        },
    },

    # ═══ 集数 1300-1399: 子女 ═══
    "1300-1399": {
        "verse_set": 1350,
        "categories": {
            "子女": [
                {"number": 1, "text": "子女成行,三男二女,皆有出息。", "checksum": 211},
                {"number": 2, "text": "一子独秀,光大门楣,不辱门风。", "checksum": 322},
                {"number": 3, "text": "先花后果,先生女而后得子。", "checksum": 434},
                {"number": 4, "text": "子息艰难,宜积德行善,可得螟蛉。", "checksum": 546},
                {"number": 5, "text": "儿女双全,各有所长,晚年有靠。", "checksum": 651},
                {"number": 6, "text": "子女早立,少年成名,光宗耀祖。", "checksum": 767},
                {"number": 7, "text": "子息缘深,晚年得子,老来得福。", "checksum": 873},
                {"number": 8, "text": "女儿贵显,胜于男儿,巾帼不让须眉。", "checksum": 985},
                {"number": 9, "text": "子女远行,各奔前程,晚年归省。", "checksum": 197},
                {"number": 10, "text": "养子有恩,视如己出,子亦尽孝。", "checksum": 312},
                {"number": 11, "text": "子女承父业,家业代代相传。", "checksum": 425},
                {"number": 12, "text": "子女多才艺,然各有志向,不必从父。", "checksum": 538},
                {"number": 13, "text": "子嗣单薄,中年得女晚得子,小有所成。", "checksum": 642},
            ],
        },
    },

    # ═══ 集数 1400-1499: 财运 ═══
    "1400-1499": {
        "verse_set": 1450,
        "categories": {
            "财运": [
                {"number": 1, "text": "财帛丰盈,一生衣食无忧,中年后更旺。", "checksum": 114},
                {"number": 2, "text": "正财稳固,偏财不旺,宜守不宜攻。", "checksum": 226},
                {"number": 3, "text": "早年财来财去,四十后聚财有方。", "checksum": 338},
                {"number": 4, "text": "财星高照,经营有道,富甲一方之命。", "checksum": 441},
                {"number": 5, "text": "财源广进,然花销亦大,宜节俭持家。", "checksum": 553},
                {"number": 6, "text": "命中财薄,然勤俭可补,晚景小康。", "checksum": 665},
                {"number": 7, "text": "横财就手,然来得快去得也快,宜置产。", "checksum": 778},
                {"number": 8, "text": "财旺身弱,富屋贫人,有钱难享。", "checksum": 882},
                {"number": 9, "text": "中年发财,白手起家,创业有成。", "checksum": 994},
                {"number": 10, "text": "因妻得财,妻家助力,家业兴隆。", "checksum": 105},
                {"number": 11, "text": "偏财运佳,投资投机皆有收获,然须谨慎。", "checksum": 219},
                {"number": 12, "text": "财来财去如流水,宜托人理财或置不动产。", "checksum": 326},
                {"number": 13, "text": "祖业丰厚,守成有余,发展不足。", "checksum": 431},
                {"number": 14, "text": "白手成家,不靠祖业,自力更生。", "checksum": 542},
                {"number": 15, "text": "先贫后富,中年转运,晚景丰隆。", "checksum": 653},
                {"number": 16, "text": "先富后贫,守财不易,宜早作安排。", "checksum": 764},
                {"number": 17, "text": "财聚于南方,宜远行南方以求财。", "checksum": 871},
                {"number": 18, "text": "财禄丰厚,然为人慷慨,施多于聚。", "checksum": 982},
            ],
        },
    },

    # ═══ 集数 1500-1599: 官禄 ═══
    "1500-1599": {
        "verse_set": 1550,
        "categories": {
            "官禄": [
                {"number": 1, "text": "官星明亮,仕途顺利,有贵人提携。", "checksum": 317},
                {"number": 2, "text": "文星拱命,利科举考试,学而优则仕。", "checksum": 422},
                {"number": 3, "text": "官运亨通,中年后位至中等,有实权。", "checksum": 536},
                {"number": 4, "text": "命无官星,不宜从政,宜从商或技艺。", "checksum": 648},
                {"number": 5, "text": "印绶相生,宜文职教育,桃李满天下。", "checksum": 753},
                {"number": 6, "text": "武职大利,军警或纪律部队有发展。", "checksum": 869},
                {"number": 7, "text": "官杀混杂,仕途多波折,宜以退为进。", "checksum": 974},
                {"number": 8, "text": "食神制杀,以技艺成名,不靠官场。", "checksum": 182},
                {"number": 9, "text": "权柄在握,然高处不胜寒,宜谦逊自持。", "checksum": 291},
                {"number": 10, "text": "仕途平平,然安分守己,亦有清福。", "checksum": 408},
                {"number": 11, "text": "弃官从商,商途胜于仕途,财利双收。", "checksum": 514},
                {"number": 12, "text": "技艺成名,不以官职论高低,一技傍身。", "checksum": 621},
                {"number": 13, "text": "宦海浮沉,几起几落,终成正果。", "checksum": 736},
                {"number": 14, "text": "文职显达,主掌文书档案类事务。", "checksum": 842},
                {"number": 15, "text": "为官清廉,然不善理财,官至中等。", "checksum": 958},
            ],
        },
    },

    # ═══ 集数 1600-1699: 寿命 ═══
    "1600-1699": {
        "verse_set": 1650,
        "categories": {
            "寿命": [
                {"number": 1, "text": "寿元绵长,享年古稀以上,晚景安康。", "checksum": 512},
                {"number": 2, "text": "命有疾厄,中年宜注意养生,可保平安。", "checksum": 628},
                {"number": 3, "text": "体魄强健,少病少灾,精力充沛。", "checksum": 734},
                {"number": 4, "text": "先天不足,后天可调,注意饮食起居。", "checksum": 847},
                {"number": 5, "text": "寿考康宁,子孙满堂,福寿双全。", "checksum": 953},
                {"number": 6, "text": "命运多舛,然心志坚定,可克难关。", "checksum": 161},
                {"number": 7, "text": "六十后宜退休静养,不宜再奔波劳碌。", "checksum": 278},
                {"number": 8, "text": "一生平安,无大灾厄,此乃上等福命。", "checksum": 384},
                {"number": 9, "text": "晚年需防心血之疾,定期体检为宜。", "checksum": 497},
                {"number": 10, "text": "命有劫数,五十前后宜谨慎,过此则安。", "checksum": 601},
                {"number": 11, "text": "寿逾八旬,福寿康宁,子孙贤孝。", "checksum": 712},
                {"number": 12, "text": "命中有灾,若能行善积德,可化险为夷。", "checksum": 825},
            ],
        },
    },

    # ═══ 集数 1800-1899: 疾病（新增） ═══
    "1800-1899": {
        "verse_set": 1850,
        "categories": {
            "疾病": [
                {"number": 1, "text": "体健少病,一生鲜有灾疾,唯中年须防肝疾。", "checksum": 132},
                {"number": 2, "text": "先天肾弱,后天宜调养,中年可复。", "checksum": 245},
                {"number": 3, "text": "心气不足,易惊悸失眠,中年尤甚。", "checksum": 358},
                {"number": 4, "text": "脾胃虚弱,饮食不节易泄泻,宜节饮食。", "checksum": 461},
                {"number": 5, "text": "肺金弱而多咳,秋冬须重养生。", "checksum": 573},
                {"number": 6, "text": "肝木旺而目疾,中年须防眼患。", "checksum": 685},
                {"number": 7, "text": "中年须防心血之疾,忌暴怒激动。", "checksum": 797},
                {"number": 8, "text": "筋骨之疾,劳伤所致,晚年行动不便。", "checksum": 809},
                {"number": 9, "text": "痰湿壅盛,中年体丰,须防中风。", "checksum": 911},
                {"number": 10, "text": "一生体健,虽老不衰,享高寿。", "checksum": 124},
                {"number": 11, "text": "幼年多惊风,中年渐愈,晚景康宁。", "checksum": 236},
                {"number": 12, "text": "妇女须防血疾,产后尤须谨慎。", "checksum": 348},
                {"number": 13, "text": "外科小疾频见,无大碍,主小手术。", "checksum": 452},
                {"number": 14, "text": "晚年须防跌仆,行动宜缓。", "checksum": 564},
            ],
        },
    },

    # ═══ 集数 1900-1999: 出行（新增） ═══
    "1900-1999": {
        "verse_set": 1950,
        "categories": {
            "出行": [
                {"number": 1, "text": "命带驿马,一生多迁动,远行可成大业。", "checksum": 156},
                {"number": 2, "text": "幼年多迁居,少小离家,自立门户。", "checksum": 268},
                {"number": 3, "text": "中年远行,于他乡立业,故土难归。", "checksum": 372},
                {"number": 4, "text": "远行东方或南方大吉,西方小有波折。", "checksum": 485},
                {"number": 5, "text": "出国之命,异域发展胜于本土。", "checksum": 597},
                {"number": 6, "text": "商旅频繁,因商远行,财运随行。", "checksum": 703},
                {"number": 7, "text": "读书远游,异乡求学有成。", "checksum": 815},
                {"number": 8, "text": "宜水路出行,陆路多阻。", "checksum": 927},
                {"number": 9, "text": "不远行而居家乐,安土重迁之命。", "checksum": 139},
                {"number": 10, "text": "中年出奔他方,晚景归乡。", "checksum": 241},
                {"number": 11, "text": "旅途中多逢贵人,遇难呈祥。", "checksum": 352},
                {"number": 12, "text": "出行忌北方,北方多凶险。", "checksum": 463},
            ],
        },
    },

    # ═══ 集数 2000-2099: 流年（新增） ═══
    "2000-2099": {
        "verse_set": 2050,
        "categories": {
            "流年": [
                {"number": 1, "text": "本命流年大吉,百事可为,进取有功。", "checksum": 178},
                {"number": 2, "text": "流年犯太岁,主一年不顺,慎之。", "checksum": 289},
                {"number": 3, "text": "流年遇天德,遇难呈祥,可解百厄。", "checksum": 393},
                {"number": 4, "text": "流年遇文昌,利考试文书,功名有望。", "checksum": 405},
                {"number": 5, "text": "流年逢驿马,主迁官调动,出行大吉。", "checksum": 517},
                {"number": 6, "text": "流年逢桃花,异性缘佳,然须防纠纷。", "checksum": 629},
                {"number": 7, "text": "流年遇财星,财运亨通,大进财利。", "checksum": 731},
                {"number": 8, "text": "流年见七杀,主凶险,慎防官非。", "checksum": 843},
                {"number": 9, "text": "流年逢天乙,贵人相助,事半功倍。", "checksum": 955},
                {"number": 10, "text": "流年遇劫煞,主破财损失,谨防盗贼。", "checksum": 167},
                {"number": 11, "text": "流年平稳,无大起伏,适守旧业。", "checksum": 279},
                {"number": 12, "text": "流年逢丧门,主亲属有丧,慎之。", "checksum": 381},
                {"number": 13, "text": "流年遇将星,主升迁得位,掌权有实。", "checksum": 493},
                {"number": 14, "text": "流年遇华盖,主艺术才华,利学术研究。", "checksum": 605},
                {"number": 15, "text": "流年逢病符,主身体欠安,宜调养。", "checksum": 717},
            ],
        },
    },

    # ═══ 集数 2100-2199: 田宅（新增） ═══
    "2100-2199": {
        "verse_set": 2150,
        "categories": {
            "田宅": [
                {"number": 1, "text": "祖宅宽广,世代相传,有以庇荫。", "checksum": 192},
                {"number": 2, "text": "自立宅基,中年置产,家业渐丰。", "checksum": 304},
                {"number": 3, "text": "多迁居,宅基不稳,然每迁皆吉。", "checksum": 416},
                {"number": 4, "text": "晚年置业,得以安居,享天伦乐。", "checksum": 528},
                {"number": 5, "text": "祖宅有破败,须修缮方保家业。", "checksum": 631},
                {"number": 6, "text": "置产于南方或东方大吉,西方小凶。", "checksum": 743},
                {"number": 7, "text": "家有池塘或园林,主财禄丰盈。", "checksum": 855},
                {"number": 8, "text": "宅近水而财聚,主一生不贫。", "checksum": 967},
                {"number": 9, "text": "宅基宽广而门庭显赫,主贵。", "checksum": 179},
                {"number": 10, "text": "晚年迁居他处,以享清福。", "checksum": 281},
                {"number": 11, "text": "祖业薄而自创,主晚年丰裕。", "checksum": 393},
                {"number": 12, "text": "家中风水有亏,宜修整以保安康。", "checksum": 505},
            ],
        },
    },

    # ═══ 集数 2200-2299: 人际/六亲（新增） ═══
    "2200-2299": {
        "verse_set": 2250,
        "categories": {
            "人际": [
                {"number": 1, "text": "人缘极佳,朋友遍天下,助力众多。", "checksum": 213},
                {"number": 2, "text": "贵人缘深,遇难必有人相助。", "checksum": 325},
                {"number": 3, "text": "小人相扰,主早年多受暗算。", "checksum": 437},
                {"number": 4, "text": "得师友之力,学艺有成,事业大进。", "checksum": 549},
                {"number": 5, "text": "朋友虽多,知己者少,主晚年得一知己足矣。", "checksum": 651},
                {"number": 6, "text": "六亲之中,与母亲一族最为亲近。", "checksum": 763},
                {"number": 7, "text": "姻亲助力大,因婚而得贵人。", "checksum": 875},
                {"number": 8, "text": "与同事合作多波折,主自立门户为佳。", "checksum": 987},
                {"number": 9, "text": "得长辈垂青,提携之恩,终身铭记。", "checksum": 199},
                {"number": 10, "text": "善结人缘,虽有小人而终无害。", "checksum": 301},
                {"number": 11, "text": "以信义立身,人皆敬重,事业因之而成。", "checksum": 413},
                {"number": 12, "text": "晚年门生故旧遍天下,享尊荣。", "checksum": 525},
            ],
        },
    },

    # ═══ 集数 2300-2399: 大运（新增） ═══
    "2300-2399": {
        "verse_set": 2350,
        "categories": {
            "大运": [
                {"number": 1, "text": "少年运佳,十五至三十大吉。", "checksum": 236},
                {"number": 2, "text": "中年运旺,四十至六十最盛。", "checksum": 348},
                {"number": 3, "text": "晚景运佳,六十后享福。", "checksum": 451},
                {"number": 4, "text": "行运起伏大,十年一变,须随运调整。", "checksum": 563},
                {"number": 5, "text": "早运平平,中年后渐入佳境。", "checksum": 675},
                {"number": 6, "text": "三十前后须防破败,四十后转运。", "checksum": 787},
                {"number": 7, "text": "运交脱运之年,主变革更新。", "checksum": 899},
                {"number": 8, "text": "大运逢禄,十年之内大富贵。", "checksum": 102},
                {"number": 9, "text": "大运逢羊刃,主凶险,慎之。", "checksum": 214},
                {"number": 10, "text": "大运转折之年,事业大进或大退,主动应对。", "checksum": 326},
                {"number": 11, "text": "大运遇文昌,十年之内,名利双收。", "checksum": 438},
                {"number": 12, "text": "大运逆行,主早年辛苦,中晚渐顺。", "checksum": 541},
            ],
        },
    },
}

# 所有条文集的总数 (用于取模)
VERSE_SET_COUNT = len(TIEBAN_VERSES)

# ── 字段字典（与 engines/tieban.py 一致）────────────────────
# 生肖编码表 (用于父母生肖校验)
ZODIAC_NUM = {
    "鼠": 1, "牛": 2, "虎": 3, "兔": 4, "龙": 5, "蛇": 6,
    "马": 7, "羊": 8, "猴": 9, "鸡": 10, "狗": 11, "猪": 12,
}

# 天干数: 甲1..癸10
TIANGAN_NUM = {"甲": 1, "乙": 2, "丙": 3, "丁": 4, "戊": 5,
               "己": 6, "庚": 7, "辛": 8, "壬": 9, "癸": 10}

# 地支太玄数: 阴支/阳支各取不同值
TAIXUAN_NUM = {
    "子": (1, 6), "丑": (5, 10), "寅": (3, 8), "卯": (3, 8),
    "辰": (5, 10), "巳": (2, 7), "午": (2, 7), "未": (5, 10),
    "申": (4, 9), "酉": (4, 9), "戌": (5, 10), "亥": (1, 6),
}

# 阳支: 子寅辰午申戌; 阴支: 丑卯巳未酉亥
YANG_ZHI = {"子", "寅", "辰", "午", "申", "戌"}

# 六十甲子纳音五行数
NAYIN_NUM = {"金": (4, 9), "木": (3, 8), "水": (1, 6),
             "火": (2, 7), "土": (5, 10)}


# ══════════════════════════════════════════════════════════════
# 考刻分（父母生肖校验）
# ══════════════════════════════════════════════════════════════

# 12 条文集 → 父母生肖组合（按 cha_ke 索引）
# 简化映射: 父母生肖差 = cha_ke_idx → 对应 verse_set 范围
CHA_KE_FEN_MAP: dict[int, dict[str, int | str]] = {
    # cha_ke_idx → (verse_set_range, description)
    0: {"range": "1000-1099", "verse_set": 1050, "desc": "父母子位,主椿萱并茂"},
    1: {"range": "1100-1199", "verse_set": 1150, "desc": "父母丑位,主幼年失怙"},
    2: {"range": "1200-1299", "verse_set": 1250, "desc": "父母寅位,主父母双全"},
    3: {"range": "1300-1399", "verse_set": 1350, "desc": "父母卯位,主手足众多"},
    4: {"range": "1400-1499", "verse_set": 1450, "desc": "父母辰位,主家业兴隆"},
    5: {"range": "1500-1599", "verse_set": 1550, "desc": "父母巳位,主文昌显达"},
    6: {"range": "1600-1699", "verse_set": 1650, "desc": "父母午位,主寿元绵长"},
    7: {"range": "1800-1899", "verse_set": 1850, "desc": "父母未位,主疾病可治"},
    8: {"range": "1900-1999", "verse_set": 1950, "desc": "父母申位,主出行有吉"},
    9: {"range": "2000-2099", "verse_set": 2050, "desc": "父母酉位,主流年大吉"},
    10: {"range": "2100-2199", "verse_set": 2150, "desc": "父母戌位,主田宅丰盈"},
    11: {"range": "2200-2299", "verse_set": 2250, "desc": "父母亥位,主六亲兴旺"},
}


def compute_cha_ke_fen(father_zodiac: str, mother_zodiac: str) -> int:
    """计算考刻分 (0-11)。

    算法 (tbs_002):
        cha_ke_idx = (ZODIAC_NUM[father] + ZODIAC_NUM[mother]) % 12

    Returns:
        考刻分 0-11, 用于索引 CHA_KE_FEN_MAP
    """
    f = ZODIAC_NUM.get(father_zodiac, 0)
    m = ZODIAC_NUM.get(mother_zodiac, 0)
    return (f + m) % 12


def lookup_verse_set_by_cha_ke(father_zodiac: str, mother_zodiac: str) -> dict:
    """根据父母生肖查找对应条文集。

    Args:
        father_zodiac: 父生肖 (鼠牛虎兔龙蛇马羊猴鸡狗猪)
        mother_zodiac: 母生肖 (同上)

    Returns:
        {cha_ke, range, verse_set, desc, categories}
        若生肖不合法 → 返回 {error: "..."}
    """
    if father_zodiac not in ZODIAC_NUM:
        return {"error": f"未知父生肖: {father_zodiac}"}
    if mother_zodiac not in ZODIAC_NUM:
        return {"error": f"未知母生肖: {mother_zodiac}"}

    cha_ke = compute_cha_ke_fen(father_zodiac, mother_zodiac)
    mapping = CHA_KE_FEN_MAP[cha_ke]
    verse_set = TIEBAN_VERSES.get(mapping["range"], {})

    return {
        "cha_ke": cha_ke,
        "range": mapping["range"],
        "verse_set": mapping["verse_set"],
        "desc": mapping["desc"],
        "categories": verse_set.get("categories", {}),
    }


def get_verse_count() -> dict[str, int]:
    """返回各类别条文数（用于自检/统计）。"""
    counts: dict[str, int] = {}
    for range_key, data in TIEBAN_VERSES.items():
        for cat, verses in data.get("categories", {}).items():
            counts[cat] = counts.get(cat, 0) + len(verses)
    return counts


def get_total_verse_count() -> int:
    """返回总条文数。"""
    return sum(get_verse_count().values())


def get_category_names() -> list[str]:
    """返回所有分类名（去重排序）。"""
    return sorted(get_verse_count().keys())


# ══════════════════════════════════════════════════════════════
# 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 铁板神数条文数据库 (扩展版) 自检 ===\n")

    # 1. 条文集统计
    print(f"1. 条文集总数: {len(TIEBAN_VERSES)} 个范围")
    for range_key, data in TIEBAN_VERSES.items():
        n_verses = sum(len(v) for v in data["categories"].values())
        cats = list(data["categories"].keys())
        print(f"   {range_key} (verse_set={data['verse_set']}): "
              f"{n_verses} 条, 分类={cats}")

    # 2. 分类统计
    counts = get_verse_count()
    print(f"\n2. 分类统计 ({len(counts)} 类, {get_total_verse_count()} 条):")
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {n} 条")

    # 3. 考刻分验证
    print("\n3. 考刻分 (父母生肖校验) 测试:")
    for fz, mz in [("鼠", "牛"), ("虎", "兔"), ("龙", "蛇"),
                   ("马", "羊"), ("猴", "鸡"), ("狗", "猪")]:
        cha_ke = compute_cha_ke_fen(fz, mz)
        result = lookup_verse_set_by_cha_ke(fz, mz)
        n_cats = len(result.get("categories", {}))
        print(f"   父{fz}+母{mz} → 考刻分={cha_ke:2d} → "
              f"集{result['verse_set']} ({result['range']}), "
              f"{n_cats} 类 → {result['desc']}")

    # 4. 错误处理
    print("\n4. 错误处理:")
    r = lookup_verse_set_by_cha_ke("猪", "牛")
    print(f"   父猪母牛: cha_ke={r['cha_ke']}, desc={r['desc']}")
    r = lookup_verse_set_by_cha_ke("xxx", "牛")
    print(f"   父xxx母牛: {r.get('error')}")
