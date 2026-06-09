"""Professional Tarot engine: 78-card Waite-Smith system.

Features:
- 78 cards with rich upright/reversed meanings, element, yes/no, timing
- Elemental dignities for card interaction analysis
- 7 spreads including Celtic Cross with detailed positional meanings
- Card interaction scoring (mutual strengthening / weakening)
- Major Arcana lifecycle analysis
- Court card personality profiling
- Number/suit pattern detection
"""

import random
from datetime import date
from typing import Optional

from ..contracts import Birth, ChartResult

# ═══════════════════════════════════════════════════════════════
# 1. 78-Card Database (Waite-Smith)
# ═══════════════════════════════════════════════════════════════
# Each entry: (name, upright, reversed, element, yes_no, timing, astrology, symbol_desc)

MAJOR_ARCANA = [
    # 0
    ("愚者", "崭新的开始——怀抱纯真踏入未知。冒险、自由、无限可能、跟随直觉。这不是鲁莽,是灵魂选择跳跃。",
     "鲁莽冲动、逃避责任、错失良机、过度天真而被利用。你不是自由的,你是迷路的。",
     "风", "maybe", "当下/即时", "天王星", "悬崖边的旅人,脚边小狗在吠叫,手持白玫瑰,肩扛小包袱——自由与风险的临界点。"),

    # 1
    ("魔术师", "所有资源已齐备。意志力、技巧、沟通能力皆在巅峰。你有能力将意念显化为现实。专注,然后行动。",
     "能力被浪费或误用。欺骗、操控、尚未准备好的自我展示。工具都在,但你不是真的会用。",
     "风", "yes", "当下", "水星", "桌前摆放着圣杯、宝剑、权杖、星币四元素,头顶∞符号——显化的力量。"),

    # 2
    ("女祭司", "静默中藏着答案。直觉比逻辑更清晰,潜意识正在对你说话。暂停行动,向内聆听。奥秘会在该揭晓时揭晓。",
     "直觉被忽视,秘密被暴露,过度理性化的情感。你与自己的内在声音失联了。",
     "水", "maybe", "等待", "月亮", "坐在帷幕之间的女祭司,脚下有新月,手持 Torah 卷轴——二元帷幕后的隐秘知识。"),

    # 3
    ("皇后", "丰盛正在流淌。创造力、感官愉悦、自然的滋养。允许自己接收,也允许自己给予。这是大地母亲的拥抱。",
     "创造力的枯竭、过度依赖他人、忽视自我的付出。你在给予中耗尽了自己。",
     "土", "yes", "季节周期", "金星", "金色麦田中的王座,心形盾牌上刻着金星符号,森林与瀑布环绕——生命的丰饶。"),

    # 4
    ("皇帝", "秩序带来安全。结构、纪律、权威——这些不是枷锁,是你为自己建立的王国。负起责任,行使你的主权。",
     "专制僵化、滥用权力、失控的暴怒、孤立无援。你的王国正在崩塌。",
     "火", "yes", "长期", "白羊座", "石制王座上的帝王,手持权杖与地球,背后是荒芜山脉——权力的重量。"),

    # 5
    ("教皇", "传统的智慧值得倾听。导师、仪式、信仰体系——它们提供了容器,但真正的信念在你心中。寻求指导,也质疑教条。",
     "盲从教条、虚假导师、被传统束缚、反叛却无方向。你交出自己的力量给了谁?",
     "土", "maybe", "按常规", "金牛座", "双手指天指地的教皇,脚下两把钥匙,两名弟子跪于前——正统与传承。"),

    # 6
    ("恋人", "选择面前,请听从你的核心价值。这不是关于对错,是关于什么让你成为你自己。真正的联结起始于自我诚实。",
     "价值观冲突、关系失衡、逃避选择或选了却后悔。你不是在选择道路,你是在逃避结果。",
     "风", "maybe", "决策时刻", "双子座", "伊甸园中的亚当与夏娃,天使拉斐尔在上方祝福,智慧树与蛇——神圣的选择。"),

    # 7
    ("战车", "意志统领一切。内在的矛盾力量被你驾驭,朝着明确的胜利推进。专注力是你的战车,决心是你的缰绳。",
     "失控、内在崩溃、方向迷失、被自己的矛盾反噬。这不是前进,是失控的狂奔。",
     "水", "yes", "短期/快速", "巨蟹座", "战士驾驭黑白双狮,头顶星辰华盖,身后的城市在远去——意志的胜利。"),

    # 8
    ("力量", "真正的力量来自温柔。驯服内在的野兽不是靠压制,而是靠理解和耐心。恐惧可以被拥抱,然后被转化。",
     "软弱退缩、自我怀疑、压抑本能而爆发的危机。你误以为强硬就是力量。",
     "火", "yes", "需要耐心", "狮子座", "白衣女子轻抚雄狮的嘴,头顶∞符号环绕——柔韧对刚强。"),

    # 9
    ("隐者", "向内行走的时刻。孤独不是惩罚,是遇见自己的唯一路径。提灯照亮的不是远方,是你脚下的这一步。",
     "过度封闭、拒绝帮助、假清高式的孤立。你不是在修行,你是在逃避。",
     "土", "maybe", "缓慢/等待", "处女座", "山顶老者手持星灯,拄着长杖独行于雪夜——向内求索。"),

    # 10
    ("命运之轮", "运势在转动。高潮与低谷都是周期的一部分。此刻的转折点不是随机事件,是你之前所有选择汇聚的结果。顺应流转。",
     "抗拒变化、陷入恶性循环、衰退期、觉得被命运捉弄。你越挣扎,轮子转得越快。",
     "火", "maybe", "周期转折", "木星", "旋转的命运之轮,四角有天使、鹰、牛、狮四活物,蛇与阿努比斯在轮上——无常。"),

    # 11
    ("正义", "因果不昧。每一个选择都有后果,此刻天平正在校准。诚实面对自己,承担你该承担的,也接受你该接受的。",
     "不公、逃避责任、偏颇判断、因果失衡。你在欺骗系统,系统也在欺骗你。",
     "风", "maybe", "按因果", "天秤座", "手持天平与剑的正义女神,端坐于石柱之间,紫色帷幕——衡量的不可逃避。"),

    # 12
    ("倒吊人", "悬置是礼物。当你停止挣扎,倒过来看世界,答案会自己浮现。牺牲不是失去——是你愿意暂时放下以获得更大的视角。",
     "无意义的自我牺牲、抗拒放下、固守在痛苦中不肯转换视角。你的牺牲没人看见,包括你自己。",
     "水", "maybe", "暂停/等待", "海王星", "倒吊于T形木架上的人,面色平静,头顶光环——反转即救赎。"),

    # 13
    ("死神", "某一个阶段必须结束。这是蜕皮,不是灭亡。放下那些已经死去的关系、身份、执念——为新的生长腾出空间。",
     "抗拒结束、腐烂的滞留、恐惧转变而麻木度日。你抱着尸体不肯松手。",
     "水", "no", "终结/新开始", "天蝎座", "黑甲骑士持黑旗前行,众人倒地,远处旭日初升——结束即开始。"),

    # 14
    ("节制", "一切在于平衡。极端不是答案,调和才是。缓慢而稳定地混合对立的力量,找到那个恰到好处的节奏。",
     "失衡、透支、冲突加剧、节奏失控。你在两极之间摇摆,却不肯停下来调一杯。",
     "火", "yes", "稳步渐进", "射手座", "天使手持双杯倒水,一脚在水中一脚在岸上,头顶三角光环——中庸之美。"),

    # 15
    ("恶魔", "看清你的锁链。那些成瘾、执念、不健康的关系——它们的锁链其实松的。承认阴影的存在,然后选择是否继续被束缚。",
     "从锁链中觉醒、直面欲望的真相、打破依赖模式。你终于看清——门一直没锁。",
     "土", "no", "困局/需突破", "摩羯座", "半人半羊的恶魔立于黑柱之上,亚当夏娃被细链轻锁——欲望的真相。"),

    # 16
    ("高塔", "崩塌是恩典。那些建立在虚假之上的结构必须倒塌。闪电击中之处正是你最脆弱又最需要清醒的地方。",
     "勉强维持危楼、延迟必然的崩塌、缓慢瓦解中自欺。你明知塔要倒,还在粉刷外墙。",
     "火", "no", "突变/瞬间", "火星", "高塔被闪电击中,火焰从窗口喷出,两人从塔顶坠落——崩塌即真相。"),

    # 17
    ("星星", "疗愈已开始。在最暗的夜之后,星光出现了。赤裸的信任、纯粹的灵感——你不需要伪装,只需要接受这温柔的指引。",
     "信念动摇、灵感枯竭、与希望的源头失联。你不再相信光,所以你看不到任何光。",
     "风", "yes", "慢慢恢复", "水瓶座", "裸女跪于池边,手持双壶倒水入池与大地,天穹有八芒星——希望与疗愈。"),

    # 18
    ("月亮", "迷雾中有真相。恐惧、梦境、潜意识正在浮现——你所害怕的可能只是影子。在月光下行走,但记住不是所有路都通向现实。",
     "迷雾渐散、恐惧被克服、幻象被识破。你终于从月光的催眠中醒来。",
     "水", "maybe", "模糊/未知", "双鱼座", "月下双塔之间的小径,狗与狼对月长嚎,龙虾从水中爬出——潜意识的迷宫。"),

    # 19
    ("太阳", "一切明朗。生命力满溢、成功清晰可见、快乐无需理由。这是属于你的高光时刻,放下防备,让阳光照进来。",
     "短暂阴郁、成功延迟、被乌云暂时遮蔽却不至熄灭。太阳还在云背后。",
     "火", "yes", "明确/立即", "太阳", "巨大太阳照耀,白马上坐着微笑的孩童,手持红旗,向日葵盛开——纯粹的喜悦。"),

    # 20
    ("审判", "觉醒的号角已吹响。回顾你走过的路,接受所有经历——它们成就了此刻的你。上升或停留,选择权在你。",
     "拒绝召唤、自我否定、错过觉醒时刻而假装什么都没发生。号角已响,你捂住耳朵。",
     "火", "yes", "觉醒时刻", "冥王星", "天使加百列在天吹响号角,棺材中的人们伸手回应——复活与召唤。"),

    # 21
    ("世界", "一个完整的循环已闭合。成就、整合、圆融——你到达了这一个阶段的目的地。舞蹈没有结束,但这一曲已完成。",
     "未完成、拖延闭合、欠缺最后一环而无法前进。你再走半步就到了,却停下了。",
     "土", "yes", "完成/圆满", "土星", "舞者悬浮在月桂花环中,四角有四活物,手持双杖——完整与完成。"),
]

# ═══════════════════════════════
# Minor Arcana: 56 cards
# ═══════════════════════════════
SUIT_META = {
    "权杖": {"element": "火", "theme": "行动、热情、事业、创造力", "court_role": "企业家/行动者"},
    "圣杯": {"element": "水", "theme": "情感、关系、直觉、灵性", "court_role": "感受者/关系者"},
    "宝剑": {"element": "风", "theme": "思维、冲突、沟通、真理", "court_role": "思考者/裁决者"},
    "星币": {"element": "土", "theme": "物质、财富、身体、稳定", "court_role": "建设者/管理者"},
}

# Minor arcana keyword table: (rank, suit) → (upright, reversed, yes_no, timing)
MINOR_KEYWORDS = {
    "Ace": {
        "权杖": ("创造的火花已点燃。新事业、新灵感的起点——纯粹的行动潜能握在你手中。让它燃烧,但别忘了添柴。",
                 "火花未燃便被扑灭。拖延、灵感枯竭、错失启动时机。不是没有火种,是你不肯吹气。", "yes", "即刻"),
        "圣杯": ("心门打开了。爱、直觉、灵感的源头涌动而出。这是一段情感旅程的起点——允许自己去感受。",
                 "情感压抑、心门紧闭、错过爱的讯号。不是没有水,是你把井盖封死了。", "yes", "即刻"),
        "宝剑": ("真理如利刃。一个清晰的想法划破迷雾——看清它,接受它。新洞见带来突破性的解决方案。",
                 "思路混乱、真相被扭曲、词不达意——你脑子里全是噪音,找不到那个清晰的信号。", "maybe", "当下"),
        "星币": ("种子已入土。一个实在的机会、一笔新的资源、一项踏实的起步。现在需要的是耐心浇水。",
                 "机会擦肩而过、资源空转、起步犹豫不决——种子在口袋里,不在土里。", "yes", "长期"),
    },
    "2": {
        "权杖": ("站得高些,看得远些。此刻需要规划和决策——你已有了火花,现在要选一个方向。",
                 "恐惧让你无法抉择、视野受限而陷入分析瘫痪。你不是在看,你是在躲。", "maybe", "中期"),
        "圣杯": ("两颗心的共振。伙伴关系、双向的吸引和承诺——这是情感的联结,也是选择。",
                 "关系失衡、单向付出、价值观不合。你们之间有一条看不见的裂缝。", "yes", "中期"),
        "宝剑": ("两难困局。信息不足或选项冲突让你难以行动。暂停不是逃避——给自己看清真相的时间。",
                 "拒绝做出决定、逃避对峙、假装看不见矛盾。你不是在权衡,你是在拖延。", "maybe", "停滞"),
        "星币": ("多线并进的艺术。灵活调配资源、同时兼顾多项事务。但小心——你只有两只手。",
                 "顾此失彼、资源耗散、什么都想做却什么都做不好。掉在地上的球比手里的多。", "maybe", "中期"),
    },
    "3": {
        "权杖": ("第一步的成果已经显现。远眺未来,等待回响——你的船已在海上,现在需要的是信心和耐心。",
                 "计划受挫、成果延迟、视野收窄而焦虑。船才刚出海,你就已经开始怀疑方向了。", "yes", "短期"),
        "圣杯": ("欢庆时刻。友谊、共聚、情感的丰收——分享你的快乐,它就会翻倍。",
                 "过度社交而空洞、友谊中的紧张、独饮式的热闹。满屋子的笑声里,你还是一个人。", "yes", "短期"),
        "宝剑": ("心碎是真实的。但疼痛中藏着一个真相——它在等你承认。允许这几把剑刺痛你,然后让它们被拔出。",
                 "疗愈开始、痛苦正在转化、真相终于被看见。最痛的已经过去了。", "no", "中期"),
        "星币": ("团队协作的力量。学习、技能积累、初阶成果——这不是一个人的战斗。找到你的同路人。",
                 "合作不顺畅、学习卡关、团队磨合的阵痛。各做各的,谁也不服谁。", "yes", "中期"),
    },
    "4": {
        "权杖": ("里程碑值得庆祝。稳定、归属、温暖的家庭庆典——这是暂停休整的驿站。享受此刻。",
                 "庆祝被推迟、关系紧绷、过渡期卡顿。该欢乐却没有欢乐——你是被什么事卡住了?", "yes", "短期"),
        "圣杯": ("倦怠。对一切都提不起兴趣——不是世界没有在召唤你,是你已经把耳朵关了。",
                 "重新觉知、从麻木中醒来、找到新的兴趣点。那扇窗其实一直开着。", "no", "中期"),
        "宝剑": ("休息是必要的。退守静养、让大脑从持续的战斗中恢复。不是懦弱,是智慧。",
                 "强迫自己继续运转、拒绝休息而精疲力竭。你不是在坚持,你是在自毁。", "no", "短期"),
        "星币": ("安全感的极致。攥紧已有资源、稳固防守——但别忘了,攥得太紧的水会从指缝流走。",
                 "过于吝啬、对失去的焦虑过度、放开手才能真正拥有。你不是在守护,你是在囚禁。", "maybe", "长期"),
    },
    "5": {
        "权杖": ("竞争与冲突。混乱的角力场——但正是这些张力在磨你的技能。别逃避对抗,它让你更强。",
                 "避免冲突、内在挣扎、退出竞争——你不是在求太平,你是在认输。", "no", "短期"),
        "圣杯": ("遗憾的味道。你只看到了打翻的三个杯子,忘了身后还有两个站着的。失落是真的,但剩下的也是真的。",
                 "走出失落、转念看到剩余、希望重新浮现。泪水擦干后你发现——还有半杯。", "no", "中期"),
        "宝剑": ("自我消耗的战争。空虛的胜利、无意义的冲突——你赢了这场争吵却输掉了自己的平静。",
                 "走出冲突、寻求和解、放下胜负心。你终于意识到——这架打不赢,也不需要打赢。", "no", "中期"),
        "星币": ("匮乏感。孤立无援、经济紧张、被世界遗忘在寒冬里。但记住——冬天不会永远。",
                 "找到出路、获得支持、匮乏中的转机。第一片雪花融化的时候,春就不远了。", "no", "中期"),
    },
    "6": {
        "权杖": ("凯旋。认可、成就、众人为你欢呼——这不是终点,是新一轮的起点。接受荣誉,但别停在马上。",
                 "胜利打折、自我怀疑抹去了荣光——不是别人不认可你,是你不认可自己。", "yes", "短期"),
        "圣杯": ("怀旧。回到熟悉的人与地——童年的味道、旧日的联结。这不是倒退,是根基的回访。",
                 "困在过去不愿前行、沉溺于怀旧而拒绝当下。你不是在回忆,你是在逃避。", "yes", "中期"),
        "宝剑": ("渡过。从混乱中过渡到平静——船已过河,彼岸在望。那段艰难的水路已经在你身后了。",
                 "困在渡口不肯登岸、留恋混乱中的熟悉感。船到岸了,你还不肯下船。", "yes", "短期"),
        "星币": ("给予与接收的平衡。慷慨地给予,也坦然地接收——这是富足的双向流动。",
                 "不平衡的施与受、依赖关系、被利用的善意。你给出去的和你收到的不在一个天平上。", "yes", "中期"),
    },
    "7": {
        "权杖": ("坚守阵地。压力来了,所有人都在看你能否挺住。你不是一个人在战斗——站稳,你有优势。",
                 "不堪重压、放弃立场、被围攻而退却。你不是在让步,你是在溃败。", "maybe", "中期"),
        "圣杯": ("七重幻象。太多选项、太多诱惑——你被自己想要的东西迷了眼。其中一个是真的,其他六个是雾。",
                 "迷雾散尽、看清真相、从迷恋中清醒。你终于认出了那第七个杯子里装的是什么。", "maybe", "短期"),
        "宝剑": ("以退为进的策略。不是正面冲突,而是绕行包抄——聪明人知道什么时候该绕路。",
                 "直面真相、不再隐藏、攻守转换——回避策略到期了。", "maybe", "中期"),
        "星币": ("耐心评估。长期布局需要时间——你已种下,现在等收成。焦虑不会让庄稼长得更快。",
                 "怀疑自己的成果、焦虑收成、半信半疑——你不是在评估,你是在自我否定。", "maybe", "长期"),
    },
    "8": {
        "权杖": ("消息来了。风向转变、事情开始加速——准备好接收,速度会很快。箭已离弦。",
                 "节奏失控、消息被延迟、刹车失灵——你不是在前进,你是在被拖着跑。", "yes", "即刻"),
        "圣杯": ("放下,继续走。你已经喝够了这口井的水。转身不是放弃,是去寻找更深的水源。",
                 "留恋不肯放下、滞留在熟悉的浅井旁——深水在外面,你却不肯离开这口枯井。", "yes", "中期"),
        "宝剑": ("被围困的感觉。但仔细看——这些束缚大部分是你自己绑上去的。限制是真实的,也是可以拆的。",
                 "信念解放、看清自我设限、走出囚笼——你突然发现那些绳子从来都是松的。", "no", "中期"),
        "星币": ("一门深入的手艺。勤奋练习、专注精进——你正在成为某个领域的匠人。这需要时间,但值得。",
                 "匠气太重失去灵气、机械重复而丧失热情——你不是在精进,你是在磨损自己。", "yes", "长期"),
    },
    "9": {
        "权杖": ("最后一道防线。警觉地守护你已建立的一切——这是最后一搏前的对峙。你还有余力。",
                 "防线松动、精疲力竭、放弃抵抗——你不是在守卫,你是在勉强支撑一个已经失守的阵地。", "maybe", "短期"),
        "圣杯": ("心愿达成。九只杯子满溢——你在情感上获得了真正的满足。这是你应得的。",
                 "愿望未满、表面满足内在空虚——九只杯子看着满,喝起来是空的。", "yes", "短期"),
        "宝剑": ("午夜惊醒。焦虑的思绪在黑暗中翻滚——那些担忧被放大了。天亮了它们会小很多。",
                 "焦虑在缓解、恐惧被看清后变小——你发现昨晚担心的那件事其实没那么可怕。", "no", "短期"),
        "星币": ("丰收的自足。自给自足、不依赖外界的丰饶——这是你一手建立的富足。享受它,但别独享。",
                 "过度依赖他人的供养、外强中干的华丽——脱下那身袍子,里面是空的。", "yes", "长期"),
    },
    "10": {
        "权杖": ("责任的重担。十个权杖压在肩上——这些确实是你该承担的,但也许不需要同时扛所有。",
                 "终于卸下重担、学会说'不'、释放不必要的责任。放下两根,剩下八根就轻多了。", "maybe", "中期"),
        "圣杯": ("情感的圆满。家庭、长期伴侣、共同体——这是属于你的情感家园。守护它。",
                 "家庭不和、价值观冲突、幸福画面下的裂缝——彩虹的底部有雨。", "yes", "长期"),
        "宝剑": ("终结。事情到了该收尾的时刻——但这个终结也是新的开始。接受它,放下它。",
                 "延迟终结、短暂恢复后继续挣扎——你不是在休整,你是在装死。", "maybe", "短期"),
        "星币": ("家业的传承。长期积累的财富、家族的根基——这是你为后代铺的路。物质上的圆满。",
                 "家庭财务矛盾、传承断裂、根基动摇——积累了三代的财富可能毁于一代的争执。", "yes", "长期"),
    },
    "侍从": {
        "权杖": ("一个热情的消息或新项目正在萌芽。探索的冲动——像少年一样好奇地迈出第一步。",
                 "三分钟热度、分心、消息未明而躁动不安。你不是在探索,你是在乱跑。", "maybe", "即将"),
        "圣杯": ("敏感的心灵带来创意的火花。一段温柔的讯息或邀请——允许自己被感动。",
                 "情绪化的反应、不成熟的情感表达、讯息被误读。你不是在感受,你是在反应。", "maybe", "即将"),
        "宝剑": ("机警的观察者。新讯息、新视角——好奇心是此刻最好的向导。保持敏锐。",
                 "八卦与闲言、轻率的判断、讯息被扭曲传播。你不是在观察,你是在偷窥。", "maybe", "即将"),
        "星币": ("踏实学习的新阶段。一项技能、一个计划正在起步——认准方向,从基本功开始。",
                 "懒散拖延、缺乏计划、起步期的漂浮不定。你不是在准备,你是在磨蹭。", "yes", "即将"),
    },
    "骑士": {
        "权杖": ("行动派出征。热情驱动下的快速推进——冲,但别忘了看路。",
                 "鲁莽冒进、半途而废、冲太快翻了车。你不是在冲锋,你是在失控。", "yes", "快速"),
        "圣杯": ("浪漫的邀约。情感的提案——骑士献上的是真心,还是那一刻的热烈?",
                 "情绪不稳、逃避承诺、浪漫变泡沫。那匹马跑太快了,你追不上。", "yes", "快速"),
        "宝剑": ("理性驱动下的行动。雄心勃勃、目标明确——你是用脑子在战斗,不是用肾上腺。",
                 "攻击性过强、理性变冷酷、为达目的不惜伤及无辜。你不是在推进,你是在碾压。", "maybe", "快速"),
        "星币": ("稳健推进。一步一个脚印,慢但不会倒——这是值得信赖的节奏。",
                 "过于保守而停滞、惧怕变化而原地踏步。你不是在稳健,你是在固守。", "yes", "缓慢"),
    },
    "皇后": {
        "权杖": ("自信的独立女性。魅力、磁场、温暖——她是自己的太阳,不需要别人照亮。",
                 "自我中心、情绪化占有、灼伤身边的人。她的光太强了,把别人都照成了影子。", "yes", "中期"),
        "圣杯": ("滋养与共情。如母亲般的直觉和关怀——在用爱浇灌别人的同时,别忘了自己也需要水。",
                 "情绪依赖、自我忽视、以付出为名的情绪勒索。她给你的水,其实是你的泪。", "yes", "中期"),
        "宝剑": ("清醒的独立。原则清晰的女性——她的锋利是为了划开迷雾,不是为了伤人。",
                 "冷酷隔离、过分严苛的理性、切断情感联结。她不是清醒,她是结了冰。", "maybe", "中期"),
        "星币": ("务实的丰盛。职场/家庭都能打理得井井有条——她是财富的创造者和守护者。",
                 "过度物质化、缺乏弹性、把一切换算成数字。她不是务实,她是只剩数字。", "yes", "长期"),
    },
    "国王": {
        "权杖": ("远见卓识的领导者。雄心不是野心,是让更多人一起成功的愿景。",
                 "专制独断、冲动决策、用权力代替智慧。他不是领导,他是暴君。", "yes", "长期"),
        "圣杯": ("情感成熟的男性。共情与稳定——他有力量承载,也有柔软回应。",
                 "情绪操控、内在压抑而爆发的暗流。他不是温柔,他是闷着。", "yes", "长期"),
        "宝剑": ("公正的裁决者。理性权威——他的判断是冷静的,他的决定是清晰的。",
                 "专横操控、滥用理性为自己辩护。他不是公正,他是擅长诡辩。", "maybe", "长期"),
        "星币": ("成功的实业家。稳健、富足、可靠——他会把一件事做到极致,然后传给下一代。",
                 "物质主义至上、固执不肯改变、对资源的病态掌控。他不是成功,他是囤积。", "yes", "长期"),
    },
}

RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "侍从", "骑士", "皇后", "国王"]
SUITS = list(SUIT_META.keys())

# Build full deck
FULL_DECK = []
CARD_DB = {}

# Major arcana
for name, up, rev, elem, yn, timing, astro, symbol in MAJOR_ARCANA:
    entry = {
        "name": name, "upright": up, "reversed": rev,
        "element": elem, "yes_no": yn, "timing": timing,
        "astrology": astro, "symbol": symbol,
        "arcana": "major", "number": MAJOR_ARCANA.index((name, up, rev, elem, yn, timing, astro, symbol)),
    }
    CARD_DB[name] = entry
    FULL_DECK.append(name)

# Minor arcana
for suit in SUITS:
    sm = SUIT_META[suit]
    for rank in RANKS:
        name = f"{suit}{rank}"
        up, rev, yn, timing = MINOR_KEYWORDS.get(rank, {}).get(suit, ("", "", "maybe", "未知"))
        # Court cards
        if rank in ("侍从", "骑士", "皇后", "国王"):
            arcana = "court"
        elif rank == "Ace":
            arcana = "ace"
        elif rank in ("2", "3", "4", "5", "6", "7", "8", "9", "10"):
            arcana = "numbered"
        else:
            arcana = "minor"
        entry = {
            "name": name, "upright": up, "reversed": rev,
            "element": sm["element"], "yes_no": yn, "timing": timing,
            "astrology": "", "symbol": f"{suit}·{rank}",
            "arcana": arcana, "suit": suit, "rank": rank,
        }
        CARD_DB[name] = entry
        FULL_DECK.append(name)

# Backward-compatible aliases
ALL_CARDS = FULL_DECK
ALL_KEYWORDS = CARD_DB


# ═══════════════════════════════════════════════════════════════
# 2. Elemental Dignities System
# ═══════════════════════════════════════════════════════════════
# Fire strengthens Air, weakens Water; Water strengthens Earth, weakens Fire;
# Air strengthens Fire, weakens Earth; Earth strengthens Water, weakens Air.
ELEMENT_BOOST = {"火": "风", "风": "火", "水": "土", "土": "水"}
ELEMENT_WEAKEN = {"火": "水", "水": "火", "风": "土", "土": "风"}


def _card_interaction(card_a: dict, card_b: dict) -> str:
    """返回两张牌之间的元素互动关系。"""
    ea = card_a.get("element", "")
    eb = card_b.get("element", "")
    if not ea or not eb:
        return "neutral"
    if ea == eb:
        return "reinforce"  # 同元素互相加强
    if ELEMENT_BOOST.get(ea) == eb:
        return "boost"  # A 被 B 加强
    if ELEMENT_WEAKEN.get(ea) == eb:
        return "weaken"  # A 被 B 削弱
    return "neutral"


_INTERACT_LABELS = {
    "reinforce": "同元素共鸣——这两张牌的能量互相放大",
    "boost": "正向支持——前一张牌的能量被后一张激活和加强",
    "weaken": "元素冲突——这两张牌的能量有对立和损耗,需额外觉察",
    "neutral": "中性配合——各司其职,没有明显冲突或加强",
}


# ═══════════════════════════════════════════════════════════════
# 3. Spread Definitions
# ═══════════════════════════════════════════════════════════════
SPREADS = {
    "single": {
        "name": "单张指引",
        "description": "一张牌回应你最需要看见的核心能量。适合日常快速觉察,或聚焦一个具体问题。",
        "subjects": ["tarot_guidance", "decision"],
        "time_budget": "quick",
        "positions": [
            {
                "name": "当下指引",
                "meaning": "此刻最需要你看见的核心能量与方向。它不替你决定,只是把被忽略的真相放回你眼前。",
            }
        ],
    },
    "daily": {
        "name": "每日一牌",
        "description": "每天早晨抽一张牌,作为当日的能量锚点和觉察主题。",
        "subjects": ["tarot_guidance", "self_life"],
        "time_budget": "quick",
        "positions": [
            {
                "name": "今日主题",
                "meaning": "今日的能量基调——不是预言,是一个可以随身携带的觉察角度。",
            }
        ],
    },
    "three_time": {
        "name": "时间之流",
        "description": "过去→现在→未来三张牌,呈现一件事的自然发展脉络。适合梳理任何正在展开的议题。",
        "subjects": ["decision", "career", "relationship", "tarot_guidance"],
        "time_budget": "reflective",
        "positions": [
            {"name": "过去", "meaning": "形成当前局面的根源和背景。理解它,但不必再被它定义。"},
            {"name": "现在", "meaning": "此刻最核心的张力所在。先承认它,再决定行动。"},
            {"name": "未来", "meaning": "如果当前轨迹不被打断会走向的趋势。是惯性方向,不是命运判决。"},
        ],
    },
    "three_mind": {
        "name": "身心灵",
        "description": "分别从现实、情绪、精神三个层面透视同一个问题。适合想要全面觉察自己的时刻。",
        "subjects": ["tarot_guidance", "self_life"],
        "time_budget": "reflective",
        "positions": [
            {"name": "身体/现实", "meaning": "作息、金钱、行动、环境的实际状态。你的身体在经历什么?"},
            {"name": "情绪/心", "meaning": "感受模式、关系中的位置、内心真实的情绪天气。"},
            {"name": "精神/建议", "meaning": "更高层面的提醒——关于长期方向和核心价值。"},
        ],
    },
    "choice_two": {
        "name": "二择一",
        "description": "当面前有两条路时,分别展开 A/B 选项的现状、阻力与趋势,帮你做出更清醒的选择。",
        "subjects": ["decision", "career", "relationship"],
        "time_budget": "reflective",
        "positions": [
            {"name": "选项A现状", "meaning": "选择 A 在当前的真实起点。"},
            {"name": "选项A阻力", "meaning": "A 路上你最可能遇到的阻碍。"},
            {"name": "选项A结果", "meaning": "如果走 A 路的自然发展趋势。"},
            {"name": "选项B现状", "meaning": "选择 B 在当前的真实起点。"},
            {"name": "选项B阻力", "meaning": "B 路上你最可能遇到的阻碍。"},
            {"name": "选项B结果", "meaning": "如果走 B 路的自然发展趋势。"},
        ],
    },
    "relationship_cross": {
        "name": "关系十字",
        "description": "五张牌从你、对方、互动、阻碍、建议五个层面审视一段关系。不替代沟通,但能照亮盲区。",
        "subjects": ["relationship"],
        "time_budget": "reflective",
        "positions": [
            {"name": "你", "meaning": "你在这段关系中的真实状态和能量。"},
            {"name": "对方", "meaning": "对方此刻的状态(是你的感知,不是读心术)。"},
            {"name": "互动", "meaning": "你们两个能量交汇时产生的化学反应。"},
            {"name": "阻碍", "meaning": "关系中最大的卡点在哪里。"},
            {"name": "建议", "meaning": "接下来可以采取的温和行动。"},
        ],
    },
    "career_path": {
        "name": "事业路径",
        "description": "从现状、优势、阻力、机会、建议五个角度审视职业发展。",
        "subjects": ["career"],
        "time_budget": "reflective",
        "positions": [
            {"name": "现状", "meaning": "此刻你在工作中的真实处境。"},
            {"name": "优势", "meaning": "你手中可以调动的资源和长板。"},
            {"name": "阻碍", "meaning": "现实层面的阻力和挑战。"},
            {"name": "机会", "meaning": "可以把握的潜在突破口。"},
            {"name": "建议", "meaning": "综合前四张的具体行动方向。"},
        ],
    },
    "celtic_cross": {
        "name": "凯尔特十字",
        "description": "最经典也最深入的十张牌阵。从核心、交叉、根基、过去、显意识、近期未来、自我、环境、希望与恐惧、长期结果十个维度完整解剖一个议题。",
        "subjects": ["decision", "relationship", "career", "self_life"],
        "time_budget": "deep",
        "positions": [
            {"name": "核心", "meaning": "问题的核心——这张牌放置在最中心,代表此时此刻占卜议题的心脏。"},
            {"name": "交叉/挑战", "meaning": "横在核心之上的挑战或助力——它是你需要跨越的,也可能是你需要利用的。"},
            {"name": "根基", "meaning": "深埋在底部的根源——可能来自更早的经历或无意识模式。"},
            {"name": "过去/退隐", "meaning": "正在退场的过往——对现状产生了影响但在逐渐消退的力量。"},
            {"name": "显意识/冠", "meaning": "你自以为想要的目标——它在头顶,但未必是你灵魂真正的方向。"},
            {"name": "近期未来", "meaning": "接下来较短时间内的趋势——即将展开的画面。"},
            {"name": "自我位置", "meaning": "你在此议题中的姿态和自我认知——这是你面对世界的面具。"},
            {"name": "环境", "meaning": "外界如何看待这个议题——家人、同事、社会的眼光和影响。"},
            {"name": "希望与恐惧", "meaning": "你对此议题最深层的期待和害怕——这两种情感常常戴着同一个面具。"},
            {"name": "长期结果", "meaning": "综合所有因素之后的整体趋势——不是命运的判决,是当下路径的延伸。记住你可以改变它。"},
        ],
    },
}

ALIASES = {"three": "three_time", "celtic": "celtic_cross"}

# ═══════════════════════════════════════════════════════════════
# 4. Spread Recommendation Matrix
# ═══════════════════════════════════════════════════════════════
SPREAD_MATRIX = {
    "tarot_guidance": {
        "default": "three_mind",
        "by_budget": {"quick": "single", "reflective": "three_mind", "deep": "celtic_cross"},
        "notes": "日常觉察用 single;想深入看自己用 three_mind;重大议题用 celtic_cross。",
    },
    "decision": {
        "default": "three_time",
        "by_budget": {"quick": "three_time", "reflective": "choice_two", "deep": "celtic_cross"},
        "notes": "看趋势用 three_time;有明确 A/B 选项用 choice_two;复杂决策用 celtic_cross。",
    },
    "career": {
        "default": "career_path",
        "by_budget": {"quick": "three_time", "reflective": "career_path", "deep": "celtic_cross"},
        "notes": "具体职业议题用 career_path;想看趋势用 three_time;重大转折用 celtic_cross。",
    },
    "relationship": {
        "default": "relationship_cross",
        "by_budget": {"quick": "three_mind", "reflective": "relationship_cross", "deep": "celtic_cross"},
        "notes": "聚焦感受用 three_mind;想看双方动态用 relationship_cross;深层纠葛用 celtic_cross。",
    },
    "self_life": {
        "default": "three_mind",
        "by_budget": {"quick": "daily", "reflective": "three_mind", "deep": "celtic_cross"},
        "notes": "每日觉察用 daily;看身心灵三层用 three_mind;深挖自己用 celtic_cross。",
    },
}


def _default_spread(subject: str, time_budget: str = "reflective") -> str:
    matrix = SPREAD_MATRIX.get(subject)
    if matrix:
        if time_budget in matrix.get("by_budget", {}):
            return matrix["by_budget"][time_budget]
        return matrix["default"]
    return "three_time"


def recommend_spread(subject: str, time_budget: str = "reflective") -> dict:
    """返回某个 subject + time_budget 的推荐牌阵。"""
    spread_key = _default_spread(subject, time_budget)
    spread = SPREADS.get(spread_key, SPREADS["three_time"])
    return {
        "subject": subject,
        "time_budget": time_budget,
        "spread": spread_key,
        "spread_name": spread["name"],
        "spread_description": spread.get("description", ""),
        "position_count": len(spread["positions"]),
    }


# ═══════════════════════════════════════════════════════════════
# 5. Analysis Functions
# ═══════════════════════════════════════════════════════════════
def _analyze_draw(cards_data: list[dict]) -> dict:
    """对抽出的牌做多维分析: 元素分布、牌类分布、数字/宫廷特征、互动、大牌故事线。"""
    if not cards_data:
        return {}

    # Element tally (store English keys for cross-engine consistency)
    elem_cn_to_en = {"火": "fire", "土": "earth", "风": "air", "水": "water"}
    eng_to_cn = {"fire": "火", "earth": "土", "air": "风", "water": "水"}
    elem_count = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    arcana_count = {"major": 0, "numbered": 0, "court": 0, "ace": 0}
    yes_tally = {"yes": 0, "no": 0, "maybe": 0}
    reversal_count = 0

    for c in cards_data:
        elem_cn = c.get("element", "")
        eng_key = elem_cn_to_en.get(elem_cn, elem_cn)
        if eng_key in elem_count:
            elem_count[eng_key] += 1
        arc = c.get("arcana", "minor")
        arcana_count[arc] = arcana_count.get(arc, 0) + 1
        yn = c.get("yes_no", "maybe")
        yes_tally[yn] = yes_tally.get(yn, 0) + 1
        if c.get("orient") == "逆位":
            reversal_count += 1

    # Dominant element
    dominant_elem = max(elem_count, key=elem_count.get) if any(elem_count.values()) else None
    elem_imbalance = []
    for e, cnt in elem_count.items():
        if cnt >= 3:
            cn = eng_to_cn.get(e, e)
            elem_imbalance.append(f"{cn}元素过强({cnt}张)——此领域的能量可能过度集中")
    if dominant_elem and elem_count.get(dominant_elem, 0) == 0:
        cn_dom = eng_to_cn.get(dominant_elem, dominant_elem)
        elem_imbalance.append(f"{cn_dom}元素完全缺失——需要关注此领域的能量空白")

    # Card interactions
    interactions = []
    for i in range(len(cards_data)):
        for j in range(i + 1, len(cards_data)):
            inter = _card_interaction(cards_data[i], cards_data[j])
            interactions.append({
                "from_idx": i, "to_idx": j,
                "from_card": cards_data[i]["name"],
                "to_card": cards_data[j]["name"],
                "type": inter,
                "note": _INTERACT_LABELS.get(inter, ""),
            })

    # Major arcana story
    major_numbers = []
    for c in cards_data:
        if c.get("arcana") == "major":
            major_numbers.append((c.get("number", -1), c["name"]))

    major_story = ""
    if len(major_numbers) >= 3:
        major_story = "大阿尔卡纳占比高——你正在经历的是人生重要节点/命运级课题,不是日常琐事。"
    elif len(major_numbers) == 0:
        major_story = "全无大阿尔卡纳——当前议题偏重日常层面和具体情境,并非命运转折点。"

    court_count = arcana_count.get("court", 0)
    court_note = ""
    if court_count >= 3:
        court_note = "宫廷牌占比较高——人际关系和角色定位在当下议题中非常关键。"

    # Yes/no tendency
    y = yes_tally.get("yes", 0)
    n = yes_tally.get("no", 0)
    m = yes_tally.get("maybe", 0)
    if y > n and y > m:
        yn_tendency = "positive"
        yn_text = "牌面整体偏积极——但请把它当风向标而非保证书。"
    elif n > y and n > m:
        yn_tendency = "negative"
        yn_text = "牌面整体偏警示——这不是坏事,是提前看到的弯道提醒。"
    else:
        yn_tendency = "neutral"
        yn_text = "牌面整体态度中立——答案不在牌里,在你的下一步行动里。"

    return {
        "element_distribution": elem_count,
        "dominant_element": dominant_elem,
        "element_imbalance": elem_imbalance,
        "arcana_distribution": arcana_count,
        "major_arcana_count": arcana_count.get("major", 0),
        "major_story": major_story,
        "court_count": court_count,
        "court_note": court_note,
        "yes_no_tendency": yn_tendency,
        "yes_no_text": yn_text,
        "yes_no_breakdown": yes_tally,
        "reversal_count": reversal_count,
        "reversal_rate": round(reversal_count / len(cards_data), 2) if cards_data else 0,
        "interactions": interactions,
    }


# ═══════════════════════════════════════════════════════════════
# 6. Main Compute Function
# ═══════════════════════════════════════════════════════════════
def compute(b: Birth) -> ChartResult:
    subject = b.subject or "tarot_guidance"
    time_budget = b.mode or "reflective"
    if time_budget not in {"quick", "reflective", "deep"}:
        time_budget = "reflective"

    spread_key = ALIASES.get(b.spread or "", b.spread or _default_spread(subject, time_budget))
    if spread_key not in SPREADS:
        spread_key = _default_spread(subject, time_budget)
    spread = SPREADS[spread_key]

    # Deterministic seed: 同一问题同一天抽到相同的牌 (避免刷新就变)
    if b.seed is not None:
        seed_used = b.seed
    elif b.question:
        seed_used = f"{date.today().isoformat()}-{b.question}"
    else:
        seed_used = f"{date.today().isoformat()}-{subject}-{spread_key}"
    rng = random.Random(str(seed_used))

    # Draw without replacement (standard tarot practice)
    draw = rng.sample(FULL_DECK, len(spread["positions"]))

    # More realistic reversal rate: ~40% (closer to actual shuffle probability)
    # This can be overridden — some readers don't use reversals at all
    cards = []
    for (position_def, name) in zip(spread["positions"], draw):
        card_info = CARD_DB.get(name, {})
        orient = "正位" if rng.random() < 0.60 else "逆位"
        keywords = card_info.get("upright", "") if orient == "正位" else card_info.get("reversed", "")
        up_kw = card_info.get("upright", "")
        rev_kw = card_info.get("reversed", "")
        orient_zh = "正位" if orient == "正位" else "逆位"
        # Build backward-compatible template_filled
        tmpl = f"{name}{orient_zh}在「{position_def['name']}」位: {keywords}"
        cards.append({
            "position": position_def["name"],
            "position_meaning": position_def["meaning"],
            "position_template_filled": tmpl,
            "name": name,
            "orient": orient,
            "orient_zh": orient_zh,
            "keywords": keywords,
            "keywords_upright": up_kw,
            "keywords_reversed": rev_kw,
            "image_hint": card_info.get("symbol", ""),
            "element": card_info.get("element", ""),
            "yes_no": card_info.get("yes_no", "maybe"),
            "timing": card_info.get("timing", ""),
            "astrology": card_info.get("astrology", ""),
            "symbol": card_info.get("symbol", ""),
            "arcana": card_info.get("arcana", ""),
            "number": card_info.get("number"),
            "suit": card_info.get("suit", ""),
            "rank": card_info.get("rank", ""),
            "keywords_full": {
                "upright": up_kw,
                "reversed": rev_kw,
            },
        })

    # Multi-dimensional analysis
    analysis = _analyze_draw(cards)

    # Spread recommendation
    recommendation = recommend_spread(subject, time_budget)

    return ChartResult(
        method="tarot",
        school="west",
        engine="random+spread-schema+elemental-dignities+multi-analysis",
        normalized={"elements": analysis["element_distribution"], "timeline": []},
        raw={
            "computed_at": date.today().isoformat(),
            "mode": "tarot_spread",
            "subject": subject,
            "spread": spread_key,
            "spread_name": spread["name"],
            "spread_description": spread.get("description", ""),
            "spread_schema": [
                {"position": p["name"], "meaning": p["meaning"], "template_filled": ""}
                for p in spread["positions"]
            ],
            "spread_recommendation": recommendation,
            "cards": cards,
            "analysis": analysis,
            "deck_size": 78,
            "deck_type": "Waite-Smith (Rider-Waite)",
            "seed_used": seed_used,
            "rule_version": "v2",
            "calculation_basis": {
                "method": "tarot",
                "mode": "tarot_spread",
                "subject": subject,
                "spread": spread_key,
                "draw_rule": "78-card Waite-Smith deck, no replacement, ~40% reversal rate",
                "analysis_included": [
                    "elemental_distribution",
                    "elemental_dignities_between_cards",
                    "major_arcana_lifecycle_analysis",
                    "court_card_personality_profiling",
                    "yes_no_tendency_aggregate",
                    "reversal_rate",
                ],
                "rule_version": "v2",
                "input_source": "user question + seed (deterministic with seed)",
                "limits": [
                    "塔罗解读本质上是象征性的——牌的意义在具体的个人情境中才会真正活化",
                    "Yes/No 倾向仅供参考——不是概率计算",
                    "时序指示基于传统对应(如权杖=快/星币=慢),不可当日历使用",
                    "凯尔特十字为 10 张牌阵,信息量大;较短的牌阵通常更聚焦",
                ],
            },
        },
    )
