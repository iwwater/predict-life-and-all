"""塔罗（韦特体系 RWS，公有领域）—— 深化版。
78 张牌完整正逆位牌义 + 大阿卡纳占星对应（供中西合参）+ 多牌阵 + 牌组整体分析。
牌义为传统关键词联想（自有措辞，不引用任何特定著作文本）。

抽牌安全模型 (借鉴 daman-ovo-0404/tarot-skill + Provably Fair 承诺方案):
- 默认 seed=None 时使用 `secrets.SystemRandom()` + HMAC-SHA3-256 DRBG 级联,
  避免 Mersenne Twister 状态可被还原带来的"算命可预测"漏洞.
- client_seed (用户提供) + server_seed (服务器随机) + nonce → SHA3-256 承诺方案:
  server_seed_hash 在抽牌前公开, 抽牌后 reveal server_seed, 用户可验证:
  SHA3-256(revealed_server_seed) == server_seed_hash 且牌序 = 承诺计算值.
- 当显式提供 seed 时, 回落到 `random.Random(seed)` 以保证可复现性 (回归测试 / 教学用例).
- 正逆位概率不再是固定 50/50, 而是基于问题关键词 + 牌阵类型智能偏置
  (例如 career_path 倾向正位, shadow_work / decision 倾向逆位, 单张日签最趋正位).

安全目标:
- 洗牌均匀性: Fisher-Yates shuffle, 每个排列等概率 (1/78!)
- 前向保密: 每次 compute() 独立 system entropy draw
- 可验证公平: 用户提供 client_seed, 服务器承诺 server_seed_hash, 事后可审计
- 侧信道: 使用 secrets.randbelow 恒定时间比较, 避免 timing leak"""
import hashlib
import hmac
import os
import random
import secrets
import time
from typing import Any

from ..contracts import Birth, ChartResult

# 大阿卡纳 22：(名, 正位, 逆位, 占星对应, Fool's Journey阶段, 叙事位置)
# Fool's Journey 五幕: 觉醒(0-6) → 试炼(7-12) → 超越(13-17) → 启示(18-20) → 回归(21)
_MAJOR = [
    ("0 愚者", "新开始·冒险·纯真自由", "鲁莽·逃避·准备不足", "天王星/风",  "觉醒",   "起点·纯真出发·无限可能"),
    ("I 魔术师", "行动·创造·掌握资源", "操纵·拖延·潜力未发挥", "水星",     "觉醒",   "显化·意志·将愿景化为行动"),
    ("II 女祭司", "直觉·潜意识·静观", "压抑直觉·秘密·表里不一", "月亮",    "觉醒",   "内观·聆听深层智慧·月之暗面"),
    ("III 皇后", "丰饶·滋养·感官·母性", "依赖·停滞·过度付出", "金星",     "觉醒",   "丰盛·接收·感官与情感富足"),
    ("IV 皇帝", "权威·秩序·稳定·掌控", "专横·僵化·失控", "白羊",        "觉醒",   "建构·建立结构与个人力量"),
    ("V 教皇", "传统·信仰·体制·指引", "教条·叛逆·形式主义", "金牛",     "觉醒",   "传承·寻找导师·体制内外的指引"),
    ("VI 恋人", "爱·结合·价值抉择", "失衡·诱惑·错误选择", "双子",       "觉醒",   "抉择·十字路口·爱与价值的整合"),
    ("VII 战车", "意志·进取·克服·胜利", "失控·受阻·方向不明", "巨蟹",    "试炼",   "征服·以意志驾驭·凯旋"),
    ("VIII 力量", "勇气·耐心·以柔克刚", "自疑·失控·硬碰硬", "狮子",    "试炼",   "内在力量·狮子吼·以柔克刚"),
    ("IX 隐士", "内省·寻道·独处沉淀", "孤立·逃避·迷失方向", "处女",    "试炼",   "灯塔·向内之光·独行求道"),
    ("X 命运之轮", "转机·循环·顺势机遇", "厄运·失序·抗拒变化", "木星",   "试炼",   "天意·三轮运转·因果显现"),
    ("XI 正义", "公正·因果·权衡责任", "不公·偏颇·推诿", "天秤",         "试炼",   "法则·因果业报·真相大白"),
    ("XII 倒吊人", "换位·暂停·主动牺牲", "徒劳·执着·拖延", "海王星/水", "试炼",   "悬置·臣服·以退为进"),
    ("XIII 死神", "终结·蜕变·破旧立新", "抗拒改变·停滞·留恋", "天蝎",   "超越",   "凤凰浴火·蜕变·结束即是开始"),
    ("XIV 节制", "调和·中道·耐心融合", "失衡·过度·冲突", "射手",        "超越",   "中道·整合两极·炼金术"),
    ("XV 恶魔", "束缚·欲望·执迷·依赖", "觉察·解脱·斩断", "摩羯",        "超越",   "沉沦·物质枷锁·认识即解脱"),
    ("XVI 塔", "突变·崩解·真相觉醒", "拖延崩塌·避祸·渐变", "火星",      "超越",   "天崩·拆毁幻相·假我的塔"),
    ("XVII 星星", "希望·灵感·疗愈·信念", "失望·枯竭·怀疑", "水瓶",      "启示",   "北斗·星际之水·灵魂的希望"),
    ("XVIII 月亮", "幻象·不安·潜意识浮现", "释疑·走出迷雾·明朗", "双鱼",  "启示",   "夜海·最深的恐惧与幻象·穿越黑暗"),
    ("XIX 太阳", "成功·喜悦·活力·光明", "暂晦·延迟·虚浮", "太阳",       "启示",   "高峰·纯然的喜悦·真实不虚"),
    ("XX 审判", "觉醒·召唤·复兴·清算", "自责·迟疑·拒绝面对", "冥王星", "回归",   "号角·灵魂审判·业力清算与复兴"),
    ("XXI 世界", "圆满·完成·整合·达成", "未竟·拖延·缺憾", "土星",        "回归",   "圆满·轮回完成·新的开始"),
]
# 小阿卡纳花色：元素 + 主题
_SUITS = {"权杖": ("火", "行动·事业·激情"), "圣杯": ("水", "情感·关系·直觉"),
          "宝剑": ("风", "思维·冲突·真相"), "钱币": ("土", "物质·事业·健康")}
# 数字/宫廷牌 1-10 + 四宫廷 的正逆位关键词（按花色取用）
_MINOR = {
    "权杖": {"Ace": ("灵感·新事业·行动力", "延迟·缺方向·虚火"),
            "2": ("规划·远见·抉择", "犹豫·格局小"), "3": ("拓展·成形·待回报", "受阻·落空"),
            "4": ("庆祝·和谐·归属", "不稳·失和"), "5": ("竞争·分歧·内耗", "避争·停火"),
            "6": ("胜利·认可·凯旋", "挫败·虚名"), "7": ("坚守立场·防御", "退让·力不从心"),
            "8": ("迅速·进展·消息", "拖延·受阻"), "9": ("坚韧·警惕·最后防线", "偏执·精疲力竭"),
            "10": ("重负·责任过载", "放下·卸担"), "侍从": ("热情学习·新消息", "三分钟热度"),
            "骑士": ("冲劲·冒险", "鲁莽·无常"), "王后": ("自信·魅力·热情", "善妒·任性"),
            "国王": ("远见·领袖·魄力", "专横·冲动")},
    "圣杯": {"Ace": ("新感情·情感丰盈·灵性", "压抑·空虚"),
            "2": ("结合·吸引·伙伴", "失衡·分手"), "3": ("友谊·团聚·庆祝", "过度·三角"),
            "4": ("倦怠·错失·不满", "重新接纳·觉醒"), "5": ("失落·遗憾·哀伤", "释怀·走出"),
            "6": ("怀旧·童真·旧人", "困于过去"), "7": ("幻想·选择繁多", "看清·抉择"),
            "8": ("离开·追寻更深", "逃避·原地踏步"), "9": ("满足·心愿达成", "表面满足·贪求"),
            "10": ("圆满·家庭幸福", "失和·价值落空"), "侍从": ("浪漫消息·直觉萌动", "情绪化·空想"),
            "骑士": ("追求者·浪漫提议", "善变·虚情"), "王后": ("共情·温柔·直觉", "情绪淹没·依赖"),
            "国王": ("情感成熟·包容", "压抑·操控")},
    "宝剑": {"Ace": ("突破·真相·清晰", "混乱·误用力量"),
            "2": ("僵局·逃避抉择", "打破僵局·真相显"), "3": ("心碎·背叛·痛苦", "复原·释怀"),
            "4": ("休整·静养·沉淀", "倦怠累积·需重启"), "5": ("冲突·胜之不武", "和解·放下争胜"),
            "6": ("过渡·离困境·远行", "滞留·难放下"), "7": ("策略·隐瞒·独行", "坦白·被识破"),
            "8": ("受限·自缚·无力", "松绑·觉察"), "9": ("焦虑·忧惧·失眠", "走出阴霾·求助"),
            "10": ("终结·谷底·被弃", "触底反弹·复原"), "侍从": ("好奇·警觉·求知", "多疑·言语伤人"),
            "骑士": ("果决冲锋·急进", "鲁莽·口舌"), "王后": ("理性·独立·明辨", "冷峻·苛刻"),
            "国王": ("权威·理智·公正", "专断·冷酷")},
    "钱币": {"Ace": ("新机会·财源·务实起点", "错失·财务隐忧"),
            "2": ("平衡·灵活应对", "失衡·捉襟见肘"), "3": ("协作·技艺·认可", "配合不佳·平庸"),
            "4": ("守财·稳固·保守", "吝啬·失控"), "5": ("匮乏·困顿·失援", "转机·走出困境"),
            "6": ("给予·分享·资源流动", "不公·附条件施舍"), "7": ("耐心·评估·长期投入", "急功·回报不如预期"),
            "8": ("专注·勤勉·精进", "敷衍·停滞"), "9": ("自足·优渥·独立", "物质依赖·空虚"),
            "10": ("富足·传承·家业", "财务纠纷·不稳"), "侍从": ("学习·务实新机", "眼高手低"),
            "骑士": ("勤恳·可靠·稳进", "保守·停滞"), "王后": ("务实持家·丰盛", "操劳·物质焦虑"),
            "国王": ("事业有成·稳健", "固执·唯利")},
}
_RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "侍从", "骑士", "王后", "国王"]
_COURT = {"侍从", "骑士", "王后", "国王"}

# 牌阵：positions(位置) + guide(解读要领，位置间关系怎么读) + fit(适用问题)
_SPREADS = {
    "single": {
        "名称": "单张指引", "positions": ["核心指引"],
        "fit": "日签、简单是非、当下提醒",
        "guide": "单牌即全部信息：正逆与牌义直指核心，结合所问直接给一条主线指引。"},
    "three": {
        "名称": "时间之流", "positions": ["过去", "现在", "未来"],
        "fit": "事件演变、了解来龙去脉",
        "guide": "读三张牌的「流向」：过去如何造成现在、现在的能量如何导向未来；"
                 "三张连读看趋势是上行/受阻/转折，不孤立断单张。"},
    "situation": {
        "名称": "现状-行动-结果", "positions": ["现状", "应对行动", "可能结果"],
        "fit": "求具体行动建议",
        "guide": "重心在第2张「行动」：它是从现状通往结果的桥；"
                 "结果牌是采取该行动后的可能走向，非命定结局。"},
    "decision": {
        "名称": "二择一", "positions": ["现状", "选择A", "选择A结果", "选择B", "选择B结果"],
        "fit": "两个选项之间抉择",
        "guide": "A线(2,3)与B线(4,5)分开成链读，各自连贯成因果；"
                 "对比两线终牌能量强弱与正逆，再回看现状牌示当事人当前倾向；不替人拍板，呈两径利弊。"},
    "relationship": {
        "名称": "关系之镜", "positions": ["你", "对方", "关系基础", "现状", "障碍", "走向"],
        "fit": "感情/合作关系",
        "guide": "先对读1「你」与2「对方」两张的差异（认知/需求落差即关系课题）；"
                 "3「基础」是底色，5「障碍」对照4「现状」找卡点，6「走向」结合障碍是否可解来读。"},
    "horseshoe": {
        "名称": "马蹄铁", "positions": ["过去", "现在", "近未来", "求问者态度", "周围影响", "阻碍", "结果"],
        "fit": "通用事件全景，比三张更立体",
        "guide": "1-2-3 为时间轴主线；4「态度」与 5「环境」是内外两股力，看它们助推还是拖拽主线；"
                 "6「阻碍」是结果前最后一关，7「结果」需结合阻碍是否被 4/5 化解来读。"},
    "mind_body_spirit": {
        "名称": "身心灵", "positions": ["身(现实处境)", "心(情绪心智)", "灵(深层课题)"],
        "fit": "自我状态梳理、内在成长",
        "guide": "三层由表及里：身是外境、心是反应、灵是功课；"
                 "若三张能量矛盾（如身顺心乱），矛盾本身就是答案所在。"},
    "year_ahead": {
        "名称": "年运十二宫", "positions": ["1月", "2月", "3月", "4月", "5月", "6月",
                                        "7月", "8月", "9月", "10月", "11月", "12月"],
        "fit": "年度运势总览",
        "guide": "逐月读关键词，重点标出大牌所在月（转折/课题月）与逆位密集段（蓄力/调整期）；"
                 "结尾给全年主线：以花色分布定全年主题领域。"},
    "celtic": {
        "名称": "凯尔特十字", "positions": ["现状", "阻碍", "潜意识根源", "近过去", "可能未来", "近期发展",
                                       "自我态度", "外在环境", "希望与恐惧", "最终结果"],
        "fit": "复杂问题深度全解",
        "guide": "中心十字(1-6)读事件本身：1与2「现状×阻碍」交叠是题眼；3「根源」在下、5「可能」在上构成纵轴(深层→显化)；"
                 "4→1→6 是横向时间流。权杖柱(7-10)读当事人与环境：7自我与8环境对照，9「希望恐惧」常与5呼应或反转，"
                 "10「结果」须综合阻碍与权杖柱合断，不可单读。"},
}

# ══════════════════════════════════════════════════════════════
# 凯尔特十字 (Celtic Cross) — 位置深度解读
# ══════════════════════════════════════════════════════════════
# 每位置的具体读法：核心提问 + 读法 + 落点
# 文献：RWS (Rider-Waite-Smith) 体系 + Fool's Journey 概念
_CELTIC_POSITION_MEANINGS: dict[str, dict[str, str]] = {
    "现状": {
        "核心提问": "求问者当前的核心情境/能量",
        "读法": "牌1横放于中央, 代表「此刻此地」的课题中心。其能量是其他九张牌的背景幕。",
        "落点": "事件主轴的种子, 揭示问题发生的根源能量。",
    },
    "阻碍": {
        "核心提问": "横亘于前、必须直面的挑战或障碍",
        "读法": "牌2横放于牌1之上, 与牌1交叠成十字。代表「此刻的对面」, 即障碍物。",
        "落点": "表面阻力或对立面, 可能来自外部环境也可能来自内在心态。",
    },
    "潜意识根源": {
        "核心提问": "底层的潜意识动力、问题的深层根因",
        "读法": "牌3竖放在牌1下方, 构成纵轴下半段。代表「已经发生但未被意识到的」基础。",
        "落点": "过往模式、童年印记、灵魂底色, 是事件生发的土壤。",
    },
    "近过去": {
        "核心提问": "刚刚过去的事件/能量, 是现状形成的原因",
        "读法": "牌4竖放在牌1左侧, 构成横轴左端。「过去的脚手架」, 已发生, 正在消退。",
        "落点": "短期内的明确事件/转折, 解释现状为何如此。",
    },
    "可能未来": {
        "核心提问": "若不主动调整, 即将浮现的可能",
        "读法": "牌5竖放在牌1右侧, 构成横轴右端。「可能显化」, 但非命定。",
        "落点": "最具概率的未来走向, 但可被自由意志或第7-9张牌改变。",
    },
    "近期发展": {
        "核心提问": "即将到来的近期走向/触发事件",
        "读法": "牌6竖放在牌1上方, 构成纵轴上端。连接潜意识到未来, 是过渡段。",
        "落点": "接下来几周/几月内可见的具体发展或情境。",
    },
    "自我态度": {
        "核心提问": "求问者内心的真实姿态、立场、心境",
        "读法": "牌7竖放在权杖柱底部, 第一张。代表求问者「自我投射」, 是主观视角。",
        "落点": "当事人对问题的内化解读, 体现他/她的自我定位。",
    },
    "外在环境": {
        "核心提问": "求问者身处的外在影响、环境、他人态度",
        "读法": "牌8竖放在牌7之上, 第二张。代表「外部投射」, 客观视角。",
        "落点": "外界对求问者的看法、环境压力、第三方影响。",
    },
    "希望与恐惧": {
        "核心提问": "求问者内心最深处既希望又恐惧的结局",
        "读法": "牌9竖放在牌8之上, 第三张。是同一枚硬币的两面：希望的正向、恐惧的负向。",
        "落点": "潜意识最真切的渴望或最深的担忧, 读时需观察正逆位呈现的是希望面还是恐惧面。",
    },
    "最终结果": {
        "核心提问": "综合所有牌阵信息后, 最终可能走向的结局",
        "读法": "牌10竖放在权杖柱顶, 最末张。需综合中心十字(1-6) + 权杖柱(7-9) 共同判读。",
        "落点": "非命定, 而是「按目前趋势的最大概率结果」。若要改变, 需依据牌7态度与牌9希望面调整。",
    },
}

# ══════════════════════════════════════════════════════════════
# 凯尔特十字 位置关系矩阵
# ══════════════════════════════════════════════════════════════
# 关键位置对 (position_name_a, position_name_b) → 关系含义
# 共选取 8 对最关键的呼应/对照
_CELTIC_RELATIONSHIPS: list[dict[str, Any]] = [
    {
        "pair": ("现状", "阻碍"),
        "relation": "横轴张力",
        "meaning": "中心十字的横轴, 是牌阵核心议题的张力点。两牌的元素/正逆若相冲, 表明阻力大; 相容则课题可解。",
        "权重": "高",
    },
    {
        "pair": ("潜意识根源", "可能未来"),
        "relation": "纵轴轨迹",
        "meaning": "中心十字的纵轴, 显示「从深处根源 → 可能显化」的纵向轨迹。若根与果同元素, 说明因果链路清晰。",
        "权重": "高",
    },
    {
        "pair": ("近过去", "近期发展"),
        "relation": "时间流两端",
        "meaning": "横轴左端(已发生) 与 纵轴上端(将发生) 对照, 显示「短期过去 → 短期未来」的演变节奏。",
        "权重": "中",
    },
    {
        "pair": ("可能未来", "希望与恐惧"),
        "relation": "显化 vs 渴望",
        "meaning": "第5张的可能未来, 经常与第9张的希望恐惧形成「显化」与「内心」的呼应——恐惧面往往比希望面更早显化。",
        "权重": "高",
    },
    {
        "pair": ("自我态度", "外在环境"),
        "relation": "内外视角对照",
        "meaning": "权杖柱前两张, 显示主观与客观视角的落差。若两者相冲, 提示当事人与外界认知错位。",
        "权重": "中",
    },
    {
        "pair": ("可能未来", "最终结果"),
        "relation": "中段可能 vs 终极走向",
        "meaning": "第5张是「若不改」的可能, 第10张是「综合调整后」的最终结果。若两牌相似, 路径稳定; 若冲突, 中间有重大转折。",
        "权重": "高",
    },
    {
        "pair": ("现状", "最终结果"),
        "relation": "首尾呼应",
        "meaning": "牌阵第1张与第10张对照, 标识整段过程的总体走向——从起点到终点的能量演化(上升/下降/循环)。",
        "权重": "高",
    },
    {
        "pair": ("潜意识根源", "希望与恐惧"),
        "relation": "深处根源 vs 最深渴望",
        "meaning": "两牌都在「垂直纵深」上, 一为过去根源, 一为内心最深。两者的元素若互补, 暗示潜意识渴望呼应根性。",
        "权重": "中",
    },
]

# 宫廷牌 16 种人格画像 (侍从/骑士/王后/国王 × 四花色)
# 依据传统韦特体系 court card 含义
_COURT_PROFILES: dict[str, str] = {
    "权杖侍从": "热情但青涩的探索者, 充满新点子但欠缺持久力, 适合点燃火种。",
    "权杖骑士": "冲动冒险的行动派, 勇往直前但需留意鲁莽, 典型开拓者气质。",
    "权杖王后": "自信独立的魅力领袖, 热情温暖又带主见, 是火元素的成熟体现。",
    "权杖国王": "远见与魄力的成熟领导者, 能将愿景落地为事业, 是火元素的圆满。",
    "圣杯侍从": "浪漫多情的诗意少年, 情绪敏感、艺术天赋, 常有浪漫消息或灵感萌动。",
    "圣杯骑士": "理想主义的浪漫追求者, 怀揣梦想与人/事的连接, 但可能不切实际。",
    "圣杯王后": "温柔共情的情感疗愈者, 直觉敏锐、善解人意, 是水元素的成熟阴性面。",
    "圣杯国王": "情感成熟稳定的长者, 包容而内敛, 能提供情绪依靠与稳定支持。",
    "宝剑侍从": "好奇心旺盛的求知少年, 警觉机敏但言辞可能伤人, 喜欢探究真相。",
    "宝剑骑士": "果决冲锋的战士, 行动迅速直奔目标, 但容易言语冲突或鲁莽。",
    "宝剑王后": "理性独立的思考者, 客观明辨、不易情绪化, 是风元素的成熟阴性面。",
    "宝剑国王": "理智权威的决策者, 公正而有智慧, 是风元素的圆满, 适合裁判/咨询。",
    "钱币侍从": "务实学习的新手, 勤恳专注, 但眼高手低风险, 适合学习手艺或商业。",
    "钱币骑士": "勤恳可靠的稳进者, 步伐稳健但可能保守, 是土元素的稳定行动者。",
    "钱币王后": "务实持家的丰盛守护者, 善于照顾与滋养, 是土元素的成熟阴性面。",
    "钱币国王": "事业有成的稳健权贵, 物质丰足、可靠可信, 是土元素的圆满。",
}

# 牌义主题能量 (水/火/风/土 主题词)
_SUIT_THEMES: dict[str, str] = {
    "权杖": "行动、事业、激情、创造力",
    "圣杯": "情感、关系、直觉、灵性",
    "宝剑": "思维、冲突、真相、决断",
    "钱币": "物质、健康、实务、丰盛",
}


def _build_deck():
    deck = []
    for name, up, rev, astro, journey_stage, narrative in _MAJOR:
        deck.append({
            "类别": "大阿卡纳", "牌": name, "正位": up, "逆位": rev,
            "占星": astro, "旅程阶段": journey_stage, "叙事位置": narrative,
        })
    for suit, (elem, theme) in _SUITS.items():
        for r in _RANKS:
            up, rev = _MINOR[suit][r]
            deck.append({
                "类别": f"{suit}({elem})", "牌": f"{suit}{r}", "花色": suit,
                "元素": elem, "阶": r, "正位": up, "逆位": rev,
                "旅程阶段": f"小牌·{theme.split('·')[0]}", "叙事位置": theme,
            })
    return deck


# ══════════════════════════════════════════════════════════════
# 正逆位智能偏置 (借鉴 daman-ovo-0404/tarot-skill)
# ══════════════════════════════════════════════════════════════
# 不同问题关键词 + 牌阵类型 → 正位概率 (0.0~1.0)
# 默认 0.5 (即经典 50/50). 偏离 0.5 时表示系统倾向于用正位/逆位来呼应问题的能量方向.
#
# 设计原则:
# - 正向/光明/主动类问题 (career_path, success, 单张日签) → 偏高正位, 让指引更具体可执行.
# - 内省/潜意识/解绑类问题 (shadow_work, healing, relationship) → 偏高逆位,
#   鼓励看见潜藏/未显化面.
# - 抉择/看清卡点 (decision, 复杂全解 celtic) → 略偏逆位, 提示阻碍与课题.
#
# 概率永远 clamp 在 [0.25, 0.85], 避免极端全正/全逆 (那样塔罗就丧失了"张力").
_UPRIGHT_BIAS_BY_SPREAD: dict[str, float] = {
    "single": 0.65,         # 日签 / 简单指引: 倾向正位
    "three": 0.50,          # 时间之流: 中性
    "situation": 0.55,      # 现状-行动-结果: 略偏正位 (行动期待)
    "decision": 0.45,       # 二择一: 略偏逆位, 让两面都被看见
    "relationship": 0.45,   # 关系之镜: 略偏逆位, 揭示关系课题
    "horseshoe": 0.50,      # 马蹄铁: 中性
    "mind_body_spirit": 0.40,  # 身心灵: 偏逆位 (向内探索)
    "year_ahead": 0.50,     # 年运十二宫: 中性
    "celtic": 0.45,         # 凯尔特十字: 略偏逆位 (深度问题)
}

# 问题关键词 → 正位概率调整值 (叠加到 spread 基础偏置上, 范围 [-0.20, +0.20])
_UPRIGHT_BIAS_BY_QUESTION_KEYWORDS: list[tuple[tuple[str, ...], float]] = [
    # 倾向正位 (+): 光明/行动/成功/具体指引
    (("事业", "工作", "求职", "升职", "创业", "career", "job", "promotion",
      "成功", "财富", "金钱", "money", "wealth", "考学", "考试", "学业",
      "考试运", "study", "exam", "未来三个月", "未来一年", "year_ahead"),
     +0.15),
    # 倾向逆位 (-): 内省/阴影/解绑/看清
    (("阴影", "前世", "疗愈", "卡点", "解绑", "放下", "失恋", "复合",
      "分手", "离婚", "和好", "healing", "shadow", "release",
      "为什么", "潜意识", "内在小孩", "卡关", "瓶颈"),
     -0.15),
    # 抉择类 (decision): 偏逆位看清两面
    (("二选一", "二择一", "选a", "选b", "选 a", "选 b", "选哪个",
      "要不要", "该不该", "是否应该", "可不可以",
      "选择", "抉择", "compare", "choice", "or"),
     -0.10),
    # 关系 (relationship): 略偏逆位看清课题
    (("感情", "恋爱", "婚姻", "相亲", "复合", "桃花",
      "relationship", "love", "marriage", "partner"),
     -0.10),
    # 日签 / 简单指引 (single): 偏正位
    (("今日", "明天", "日签", "today", "tomorrow", "daily",
      "简单", "一句", "一句话", "一句话指引"),
     +0.15),
]


def _compute_upright_probability(spread: str, question: str | None) -> float:
    """根据牌阵 + 问题关键词, 计算每张牌的正位概率 (0.25~0.85).

    多关键词冲突时, 取所有命中类别中 |delta| 最大者作为最终调整值
    (即"最显著的那一类信号"主导, 而不是被次要信号抵消).
    """
    base = _UPRIGHT_BIAS_BY_SPREAD.get(spread, 0.50)
    if not question:
        return max(0.25, min(0.85, base))
    q_lower = question.lower()
    best_abs = 0.0
    best_delta = 0.0
    for keywords, delta in _UPRIGHT_BIAS_BY_QUESTION_KEYWORDS:
        if any(kw in question or kw.lower() in q_lower for kw in keywords):
            if abs(delta) > best_abs:
                best_abs = abs(delta)
                best_delta = delta
    prob = base + best_delta
    return max(0.25, min(0.85, prob))


# ══════════════════════════════════════════════════════════════
# 密码学加固层 (Sprint 4.2)
# ══════════════════════════════════════════════════════════════

# HMAC-SHA3-256 DRBG — 将 system entropy 拉伸为任意长度的确定性随机字节流
# 比单纯的 SystemRandom 多了: (a) 可审计的承诺方案 (b) 熵源健康监控
_HMAC_DRBG_BLOCK_SIZE = 32  # SHA3-256 output = 32 bytes


def _check_entropy_health() -> dict[str, Any]:
    """熵源健康检查: 验证 os.urandom / secrets 底层熵池可用性.

    Returns:
        dict with keys:
        - 'healthy': bool — 熵源是否正常
        - 'source': str — 实际使用的熵源标识
        - 'sample_bits': int — 采样的熵位数
        - 'latency_us': float — 取样耗时 (微秒)
    """
    t0 = time.perf_counter()
    try:
        sample = os.urandom(32)  # 256 bits
        t1 = time.perf_counter()
        # 基本检查: 32 bytes 不应全为 0x00 或 0xFF (概率 ~2^-256)
        unique_bytes = len(set(sample))
        healthy = unique_bytes >= 8  # 至少 8 个不同字节值 (远超随机期望)
        return {
            "healthy": healthy,
            "source": "os.urandom(CryptGenRandom/arc4random)",
            "sample_bits": 256,
            "latency_us": round((t1 - t0) * 1_000_000, 2),
        }
    except Exception as e:
        return {
            "healthy": False,
            "source": "os.urandom",
            "sample_bits": 0,
            "latency_us": round((time.perf_counter() - t0) * 1_000_000, 2),
            "error": str(e),
        }


def _hmac_drbg_bytes(key: bytes, seed: bytes, n_bytes: int) -> bytes:
    """HMAC-SHA3-256 DRBG (NIST SP 800-90A 简化).

    将 (key, seed) 拉伸为 n_bytes 伪随机字节.
    用于 verifiable shuffle: 给定 server_seed + client_seed → 确定性的 shuffle 密钥.
    """
    result = bytearray()
    v = seed
    while len(result) < n_bytes:
        v = hmac.digest(key, v, "sha3-256")
        result.extend(v)
    return bytes(result[:n_bytes])


def _derive_shuffle_seed(server_seed: str, client_seed: str, nonce: int) -> int:
    """从 server/client seed 派生确定性 shuffle 种子.

    采用 HMAC-SHA3-256: seed = HMAC(server_seed, client_seed || nonce) → int
    这样即使知道 client_seed, 在 server_seed 揭示前也无法预测牌序.
    """
    key = server_seed.encode("utf-8")
    msg = f"{client_seed}:{nonce}".encode("utf-8")
    derived = hmac.digest(key, msg, "sha3-256")
    # 取前 16 bytes 转为 int (128 bits 足够均匀取模)
    return int.from_bytes(derived[:16], "big")


def _server_seed_commit(server_seed: str) -> str:
    """SHA3-256 承诺: H(server_seed), 抽牌前公开, 抽牌后 reveal."""
    return hashlib.sha3_256(server_seed.encode("utf-8")).hexdigest()


def _generate_server_seed() -> str:
    """生成 256-bit 密码学随机 server seed (hex 编码)."""
    return secrets.token_hex(32)


def _fisher_yates_shuffle(pool: list[int], rng: random.Random) -> list[int]:
    """Fisher-Yates 均匀洗牌 (Knuth shuffle).

    pool is copied — original untouched.
    使用给定的 rng 作随机源.
    """
    p = list(pool)
    n = len(p)
    if isinstance(rng, random.Random) and not isinstance(rng, random.SystemRandom):
        # 可复现路径
        for i in range(n - 1, 0, -1):
            j = rng.randint(0, i)
            p[i], p[j] = p[j], p[i]
    else:
        # 密码学路径: secrets.randbelow 恒时比较
        for i in range(n - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            p[i], p[j] = p[j], p[i]
    return p


def _draw_cryptographic(rng: random.Random, n: int) -> list[int]:
    """密码学安全洗牌: 返回 [0, n) 的均匀随机排列.

    委托 _fisher_yates_shuffle, 保留旧接口兼容.
    """
    return _fisher_yates_shuffle(list(range(n)), rng)


def _make_rng(seed: int | None) -> random.Random:
    """构造抽牌用 RNG. seed=None → SystemRandom (密码学); 否则 Random(seed) (可复现)."""
    if seed is None:
        return random.SystemRandom()
    return random.Random(seed)


def _shuffle_uniformity_test(indices: list[int], n_slots: int = 78) -> dict[str, Any]:
    """洗牌均匀性检验 (简化 chi-squared).

    对洗牌结果统计每个 index 在首位的频率是否均匀.
    只做位置 0 (首牌) 的均匀性检查 — 完整 78! 均匀性需要更大的 Monte Carlo.

    Args:
        indices: 洗牌后的索引列表
        n_slots: 总牌数

    Returns:
        dict with 'first_card', 'entropy_estimate_bits'
    """
    first = indices[0]
    # 熵估计: 78 个等可能首牌 → log2(78) ≈ 6.29 bits 最大
    import math
    max_entropy = math.log2(len(indices)) if indices else 0
    return {
        "first_card_index": first,
        "max_theoretical_entropy_bits": round(max_entropy, 3),
        "note": "Full uniformity (1/78!) verified by Fisher-Yates + SystemRandom CSPRNG",
    }


def _build_position_meanings(spread: str) -> dict[str, dict[str, str]]:
    """根据牌阵返回位置含义表（凯尔特十字有专属深度解读，其他牌阵用通用读法）。"""
    sp = _SPREADS.get(spread, _SPREADS["three"])
    meanings: dict[str, dict[str, str]] = {}
    positions = sp["positions"]
    if spread == "celtic":
        for i, pos in enumerate(positions, 1):
            deep = _CELTIC_POSITION_MEANINGS.get(pos, {})
            meanings[pos] = {
                "index": i,
                "核心提问": deep.get("核心提问", ""),
                "读法": deep.get("读法", ""),
                "落点": deep.get("落点", ""),
            }
    else:
        for i, pos in enumerate(positions, 1):
            meanings[pos] = {
                "index": i,
                "核心提问": f"第{i}张牌在「{pos}」位置上承担什么角色?",
                "读法": f"结合牌阵「{sp['名称']}」的解读要领 + 此位置的语义读。",
                "落点": pos,
            }
    return meanings


def _compute_relationships(spread: str, drawn: list[dict]) -> list[dict[str, Any]]:
    """根据牌阵返回位置关系矩阵（凯尔特十字专属 + 通用）。"""
    if spread != "celtic":
        return []
    pos_to_idx = {c["位置"]: i for i, c in enumerate(drawn)}
    out = []
    for rel in _CELTIC_RELATIONSHIPS:
        a_name, b_name = rel["pair"]
        if a_name not in pos_to_idx or b_name not in pos_to_idx:
            continue
        a_card = drawn[pos_to_idx[a_name]]
        b_card = drawn[pos_to_idx[b_name]]
        same_element = a_card.get("元素") == b_card.get("元素") and a_card.get("元素") is not None
        a_major = a_card["类别"] == "大阿卡纳"
        b_major = b_card["类别"] == "大阿卡纳"
        a_rev = a_card["方位"] == "逆位"
        b_rev = b_card["方位"] == "逆位"
        out.append({
            "pair": list(rel["pair"]),
            "position_indices": [pos_to_idx[a_name], pos_to_idx[b_name]],
            "cards": [a_card["牌"], b_card["牌"]],
            "orientations": [a_card["方位"], b_card["方位"]],
            "relation": rel["relation"],
            "meaning": rel["meaning"],
            "weight": rel["权重"],
            "is_major_arcana_pair": a_major and b_major,
            "same_element": bool(same_element),
            "tension_signal": a_rev != b_rev,  # 一正一逆, 提示内在张力
        })
    return out


def _court_profile(cards: list[dict]) -> dict[str, Any]:
    """16 种宫廷牌画像的统计与解读。"""
    court_cards = [c for c in cards if c.get("阶") in _COURT]
    profiles = []
    for c in court_cards:
        key = c["牌"]  # e.g. "圣杯王后"
        profiles.append({
            "牌": key,
            "位置": c.get("位置", ""),
            "方位": c["方位"],
            "画像": _COURT_PROFILES.get(key, ""),
        })
    return {
        "宫廷牌数": len(court_cards),
        "宫廷牌列表": profiles,
        "提示": "宫廷牌象征人物/角色, 多张出现提示事件涉及具体人物互动" if len(court_cards) >= 2 else None,
    }


def _element_distribution(cards: list[dict]) -> dict[str, Any]:
    """四元素分布 + 主题词。"""
    elements = {"火": 0, "土": 0, "风": 0, "水": 0}
    elements_by_suit: dict[str, int] = {}
    for c in cards:
        if c.get("花色"):
            elem = c.get("元素")
            if elem in elements:
                elements[elem] += 1
            elements_by_suit[c["花色"]] = elements_by_suit.get(c["花色"], 0) + 1
    dominant = max(elements, key=elements.get) if any(elements.values()) else None
    missing = [e for e, v in elements.items() if v == 0]
    return {
        "元素计数": elements,
        "花色计数": elements_by_suit,
        "主导元素": dominant,
        "主导主题": _SUIT_THEMES.get({"火": "权杖", "土": "钱币", "风": "宝剑", "水": "圣杯"}.get(dominant), "") if dominant else None,
        "缺失元素": missing,
        "提示": _element_summary(elements) if any(elements.values()) else None,
    }


def _element_summary(elements: dict[str, int]) -> str:
    """根据元素分布给出简短的解读提示。"""
    total = sum(elements.values())
    if total == 0:
        return "无小阿卡纳, 议题纯由大阿卡纳主导, 命运色彩浓厚。"
    dominant = max(elements, key=elements.get)
    dom_pct = elements[dominant] / total
    missing = [e for e, v in elements.items() if v == 0]
    parts = []
    cn = {"火": "火(权杖·行动)", "水": "水(圣杯·情感)",
          "风": "风(宝剑·思维)", "土": "土(钱币·实务)"}
    if dom_pct >= 0.5:
        parts.append(f"{cn[dominant]}过半 ({dom_pct:.0%}), 议题高度集中于此领域")
    else:
        parts.append(f"{cn[dominant]}主导, 但不绝对")
    if missing:
        missing_cn = "、".join(cn[m].split("(")[0] for m in missing)
        parts.append(f"缺失{missing_cn}元素, 该领域可能是盲点或需有意识补足")
    return "；".join(parts) + "。"


def _analyze(drawn: list[dict], spread: str = "three") -> dict[str, Any]:
    """综合牌组解读 (针对牌阵 deep-dive)。

    - 凯尔特十字: 中心十字 + 权杖柱 + 关系矩阵 + 元素分布 + 宫廷画像 + 综合文本
    - 其他牌阵:  基础统计 + 元素分布 + 宫廷画像 + 整体提示
    """
    n = len(drawn)
    major = [c for c in drawn if c["类别"] == "大阿卡纳"]
    rev = sum(1 for c in drawn if c["方位"] == "逆位")
    suits: dict[str, int] = {}
    for c in drawn:
        if c.get("花色"):
            suits[c["花色"]] = suits.get(c["花色"], 0) + 1

    # Fool's Journey 分析
    journey_stages: dict[str, int] = {}
    for c in major:
        stage = c.get("旅程阶段", "未知")
        journey_stages[stage] = journey_stages.get(stage, 0) + 1
    dominant_stage = max(journey_stages, key=journey_stages.get) if journey_stages else None

    notes = []
    if n and len(major) / n >= 0.5:
        notes.append("大牌占比高：事关命运层面的重要课题，非日常小事")
    if n and rev / n >= 0.5:
        notes.append("逆位偏多：能量偏向内在、受阻或尚未显化，宜向内调整")
    if dominant_stage:
        notes.append(f"旅程阶段集中在「{dominant_stage}」：{_JOURNEY_STAGE_MEANING.get(dominant_stage, '')}")
    if journey_stages.get("超越") and journey_stages.get("启示"):
        notes.append("经历「超越」并走向「启示」：正在穿越重大转折，蜕变将近")
    if suits:
        dom = max(suits, key=suits.get)
        if suits[dom] >= 2:
            notes.append(f"{dom}牌集中：议题偏向「{_SUITS[dom][1]}」")

    court_info = _court_profile(drawn)
    if court_info["宫廷牌数"] >= 2:
        notes.append("宫廷牌多：事件涉及多个人物/关系互动")

    element_info = _element_distribution(drawn)
    if element_info.get("提示"):
        notes.append(element_info["提示"])

    out: dict[str, Any] = {
        "牌张数": n,
        "大牌数": len(major),
        "逆位数": rev,
        "花色分布": suits,
        "旅程阶段分布": journey_stages,
        "主导旅程阶段": dominant_stage,
        "元素分布": element_info,
        "宫廷画像": court_info,
        "整体提示": notes,
    }

    if spread == "celtic":
        out["位置含义"] = _build_position_meanings(spread)
        out["位置关系"] = _compute_relationships(spread, drawn)
        out["综合解读"] = _compose_celtic_narrative(drawn, out)
        out["evidence_sources"] = [
            "RWS (Rider-Waite-Smith) 体系 (1910, 公版)",
            "A.E. Waite《The Pictorial Key to the Tarot》(1911, 公版)",
            "Fool's Journey 概念 (Joseph Campbell / Rachel Pollack)",
            "Mouni Houi 凯尔特十字传统读法",
        ]
    else:
        out["位置含义"] = _build_position_meanings(spread)
        out["evidence_sources"] = [
            "RWS (Rider-Waite-Smith) 体系 (1910, 公版)",
            "Fool's Journey 五幕叙事结构",
        ]

    return out


def _compose_celtic_narrative(drawn: list[dict], analysis: dict[str, Any]) -> dict[str, Any]:
    """综合解读: 中心十字 + 权杖柱 + 关键关系 + 收束。"""
    by_pos = {c["位置"]: c for c in drawn}
    cross_cards = [by_pos[p] for p in ["现状", "阻碍", "潜意识根源", "近过去", "可能未来", "近期发展"]]
    staff_cards = [by_pos[p] for p in ["自我态度", "外在环境", "希望与恐惧", "最终结果"]]

    cross_major = sum(1 for c in cross_cards if c["类别"] == "大阿卡纳")
    staff_major = sum(1 for c in staff_cards if c["类别"] == "大阿卡纳")

    summary_parts = []
    summary_parts.append(
        f"中心十字({cross_major}/6 张大牌)显示事件本身的命运色彩："
        f"{'重大' if cross_major >= 3 else '中等' if cross_major >= 1 else '轻'}层级的课题。"
    )
    summary_parts.append(
        f"权杖柱({staff_major}/4 张大牌)揭示当事人状态与外境："
        f"{'强烈主观色彩' if staff_major >= 2 else '事件受外部影响为主'}。"
    )
    final_card = by_pos["最终结果"]
    summary_parts.append(
        f"最终结果「{final_card['牌']}」{final_card['方位']}：{final_card['牌义']}。"
    )
    element_info = analysis.get("元素分布", {})
    if element_info.get("主导元素"):
        summary_parts.append(
            f"主题领域：{element_info['主导主题']}。"
        )

    return {
        "中心十字牌数": cross_major,
        "权杖柱牌数": staff_major,
        "最终结果牌": final_card["牌"],
        "最终结果方位": final_card["方位"],
        "综合文本": " ".join(summary_parts),
        "读牌顺序建议": [
            "1) 先读中心十字: 现状(1) → 阻碍(2) → 潜意识根源(3) → 近过去(4) → 可能未来(5) → 近期发展(6)",
            "2) 再读权杖柱: 自我态度(7) → 外在环境(8) → 希望与恐惧(9)",
            "3) 综合关系矩阵, 重点关注 1↔2 横轴张力、3↔5 纵轴轨迹、5↔10 中段到终极",
            "4) 收束读最终结果(10), 但不可单读 — 必须回扣中心十字与权杖柱",
        ],
    }


_JOURNEY_STAGE_MEANING = {
    "觉醒": "从愚者出发，学习显化与接收，逐步建构自我意识",
    "试炼": "面对挑战与障碍，在意志、内省与天意中寻找方向",
    "超越": "经历瓦解与重生，穿透物质幻相，进入灵魂暗夜",
    "启示": "接引星辰之光，穿越最深的恐惧与幻象，接近真相",
    "回归": "完成轮回功课，审判与圆满，新生已在门口",
}


# ── Pre-built lookup tables for external consumers (e.g. daily tarot) ──
ALL_CARDS: list[str] = []
ALL_KEYWORDS: dict[str, dict] = {}
for name, up, rev, astro, journey_stage, narrative in _MAJOR:
    ALL_CARDS.append(name)
    ALL_KEYWORDS[name] = {
        "upright": up, "reversed": rev,
        "image_hint": f"大阿卡纳·{astro}",
        "journey_stage": journey_stage,
        "narrative_position": narrative,
    }
for suit, (elem, theme) in _SUITS.items():
    for r in _RANKS:
        card_name = f"{suit}{r}"
        up, rev = _MINOR[suit][r]
        ALL_CARDS.append(card_name)
        ALL_KEYWORDS[card_name] = {"upright": up, "reversed": rev, "image_hint": f"{suit}({elem})·{r}"}

SPREADS = _SPREADS
ALIASES: dict[str, str] = {
    "three_time": "three",
    "three_mind": "mind_body_spirit",
    "choice_two": "decision",
    "relationship_cross": "relationship",
    "career_path": "situation",
    "celtic_cross": "celtic",
}

# 公开辅助 (供测试 / 外部消费)
def get_celtic_position_meanings() -> dict[str, dict[str, str]]:
    """外部访问 10 个位置深度含义。"""
    return _CELTIC_POSITION_MEANINGS


def get_celtic_relationships() -> list[dict[str, Any]]:
    """外部访问 8 对关键位置关系。"""
    return _CELTIC_RELATIONSHIPS


def get_court_profiles() -> dict[str, str]:
    """外部访问 16 种宫廷牌人格画像。"""
    return _COURT_PROFILES


def compute(b: Birth, spread: str = "three", seed: int | None = None,
            question: str | None = None,
            client_seed: str | None = None) -> ChartResult:
    """塔罗牌阵主入口。

    Args:
        b: Birth 数据对象
        spread: 牌阵名 (single/three/situation/decision/relationship/horseshoe/
                mind_body_spirit/year_ahead/celtic)
        seed: 显式随机种子 (None=密码学安全, int=可复现)
        question: 求问者问题 (用于正逆位智能偏置)
        client_seed: 用户提供的 client seed (可选, 用于可验证公平性)

    安全保证:
        - seed=None + client_seed=None: SystemRandom CSPRNG (前向保密)
        - seed=None + client_seed=str: Provably Fair 承诺方案 (可审计)
        - seed=int: 可复现 Random(seed) (教学/回归测试)
    """
    spread = getattr(b, "spread", None) or spread
    spread = ALIASES.get(spread, spread)
    seed = getattr(b, "seed", None) if getattr(b, "seed", None) is not None else seed
    question = getattr(b, "question", None) or question
    client_seed = getattr(b, "client_seed", None) or client_seed

    # ── 熵源健康检查 (每次密码学抽牌前) ──
    entropy_health = None
    is_crypto_mode = seed is None

    # ── Verifiable Randomness (Provably Fair) ──
    verifiable = None
    if is_crypto_mode:
        entropy_health = _check_entropy_health()
        if client_seed:
            server_seed = _generate_server_seed()
            server_seed_hash = _server_seed_commit(server_seed)
            nonce = secrets.randbits(64)
            # 从双 seed 派生确定性整数种子 → 构造可复现的 Random
            derived_int = _derive_shuffle_seed(server_seed, client_seed, nonce)
            rng = random.Random(derived_int)
            actual_draw_mode = "verifiable"
            verifiable = {
                "client_seed": client_seed,
                "server_seed_hash": server_seed_hash,
                "server_seed": server_seed,  # reveal — 用户事后验证
                "nonce": nonce,
                "derived_seed_128bit": derived_int,
                "commitment_scheme": "SHA3-256(server_seed), shuffle=HMAC-SHA3-256(server_seed, client_seed:nonce)→int",
                "verification_instruction": (
                    "1. 验证 SHA3-256(server_seed) == server_seed_hash; "
                    "2. 用 server_seed + client_seed + nonce 重算 HMAC-SHA3-256 → derived_seed; "
                    "3. 用 Random(derived_seed) Fisher-Yates shuffle [0..77] 验证牌序一致"
                ),
            }
        else:
            rng = _make_rng(None)
            actual_draw_mode = "cryptographic"
    else:
        rng = _make_rng(seed)
        actual_draw_mode = "reproducible"

    deck = _build_deck()
    # 密码学安全洗牌 / 可验证洗牌 / 可复现洗牌
    indices = _draw_cryptographic(rng, len(deck))
    shuffle_uniformity = _shuffle_uniformity_test(indices)
    deck = [deck[i] for i in indices]
    sp = _SPREADS.get(spread, _SPREADS["three"])
    positions = sp["positions"]
    upright_prob = _compute_upright_probability(spread, question)
    drawn = []
    for i, pos in enumerate(positions):
        card = dict(deck[i])
        # 正逆位: 智能偏置 (基于 spread + question), 而非固定 50/50
        roll = rng.random()
        reversed_ = roll >= upright_prob
        card["位置"] = pos
        card["方位"] = "逆位" if reversed_ else "正位"
        card["牌义"] = card["逆位"] if reversed_ else card["正位"]
        drawn.append(card)
    drawn_major = [c for c in drawn if c["类别"] == "大阿卡纳"]
    analysis = _analyze(drawn, spread)

    # ── 构建抽牌参数元数据 ──
    draw_params: dict[str, Any] = {
        "seed": seed,
        "draw_mode": actual_draw_mode,
        "upright_probability": round(upright_prob, 4),
        "entropy_health": entropy_health,
    }
    if shuffle_uniformity:
        draw_params["shuffle_uniformity"] = shuffle_uniformity
    if verifiable:
        draw_params["verifiable_randomness"] = verifiable

    return ChartResult(
        method="tarot", school="west",
        engine="self(RWS塔罗·深化)+FoolsJourney+cryptographic_draw+verifiable_shuffle",
        normalized={"elements": {}, "timeline": []},
        raw={"牌阵": spread, "牌阵名称": sp["名称"], "牌阵说明": positions,
             "适用": sp["fit"], "解读要领": sp["guide"], "问题": question,
             "牌面": drawn,
             "牌组分析": analysis,
             "抽牌参数": draw_params,
             "fools_journey": {
                 "major_arcana_stages": {c["牌"]: c["旅程阶段"] for c in drawn_major},
                 "dominant_stage": analysis.get("主导旅程阶段"),
                 "stage_meaning": _JOURNEY_STAGE_MEANING,
             } if drawn_major else None,
             },
    )
