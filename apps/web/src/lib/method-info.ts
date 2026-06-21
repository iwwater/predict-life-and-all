import type { Method, Subject, TarotSpread, TarotSystem } from "./types";

export interface MethodPlain {
  tagline: string;
  bestFor: string;
  sample: string;
  source: string;
}

export const METHOD_PLAIN: Record<Method, MethodPlain> = {
  bazi: { tagline: "四柱命盘，看命局、大运、流年", bestFor: "命局五行喜忌、大运流年走向", sample: "我的命局和近几年运势怎么看?", source: "子平八字体系" },
  bazi_v2: { tagline: "精算版·用神格局神煞全解", bestFor: "深度命局、用神喜忌、神煞精断、职业适配", sample: "我的命格格局和职业方向是什么?", source: "子平八字+神煞+格局体系" },
  ziwei: { tagline: "十二宫星曜，看命身宫与限运", bestFor: "十二宫精析、四化星曜、三方四正", sample: "我的命宫主星和关系模式是什么?", source: "紫微斗数" },
  qimen: { tagline: "时家奇门，一事一局看行动时机", bestFor: "时辰方位择吉、百事占断", sample: "今天这个时辰签合同合适吗?", source: "奇门遁甲" },
  liuyao: { tagline: "一事一卦，重世应、动爻、用神", bestFor: "一事一占、六亲应期、卦象吉凶", sample: "我该不该换工作?", source: "六爻纳甲体系" },
  meihua: { tagline: "时间/数字/外应起卦，看体用生克", bestFor: "象数起卦、心易灵动、吉凶速断", sample: "我报个数字看这事走向?", source: "梅花易数" },
  chenggu: { tagline: "传统称骨表，命重量歌诀参考", bestFor: "袁天罡称骨歌、命重量速断", sample: "我的称骨重量是多少?", source: "袁天罡称骨歌" },
  bazhai: { tagline: "宅主命卦与四吉四凶方", bestFor: "宅命相配、八星方位、门床灶布局", sample: "我适合住哪个方位?", source: "八宅明镜" },
  xuankong: { tagline: "三元九运、坐山向星、宅盘理气", bestFor: "三元九运飞星、旺山旺向、宅盘理气", sample: "我家坐向在九运怎么排盘?", source: "玄空飞星" },
  western: { tagline: "西方本命盘，太阳月亮上升与行星", bestFor: "行星相位、宫位大运、本命格局", sample: "我的上升和本命主题是什么?", source: "现代西方占星" },
  vedic: { tagline: "吠陀恒星黄道命盘", bestFor: "二十七宿、大运体系、星曜力度", sample: "吠陀盘里我的人生主题是什么?", source: "Jyotish" },
  tarot: { tagline: "按问题选择牌阵，而不是只抽几张", bestFor: "身心灵牌阵、当下指引、意象解读", sample: "这段关系现在应该怎么看?", source: "Waite-style Tarot" },
  numerology: { tagline: "生命灵数与数字主题", bestFor: "生命数字、周期年运、姓名数字", sample: "我的生命灵数是几?", source: "Pythagorean Numerology" },
  lenormand: { tagline: "36张具体象征牌，组合解读日常", bestFor: "Grand Tableau、日常决策、组合解读", sample: "今天的状况怎么看?", source: "Petit Lenormand 体系" },
  liuren: { tagline: "三式之首，天地盘四课三传断人事", bestFor: "人事决疑、天时地利、三式之首", sample: "这件事的因果走向如何?", source: "大六壬传统体系" },
  tieban: { tagline: "铁板条文，太玄数编码考刻分", bestFor: "铁板条文、六亲校验、神数定数", sample: "我的铁板神数条文是什么?", source: "铁板神数传统体系" },
  xiaoliuren: { tagline: "掌诀速断，月日时三轮推六宫", bestFor: "小六壬掌诀、即时决疑、出行择时", sample: "今天出行顺利吗?", source: "小六壬掌诀体系" },
  cross_validator: { tagline: "多系统交叉验证·合参置信", bestFor: "多术数合参、置信度评估、交叉验证", sample: "八字和紫微结果一致吗?", source: "多系统ensemble方法" },
  hour_calibrator: { tagline: "时辰校准·解决排盘幻觉", bestFor: "出生时辰不确定、定盘校验", sample: "我不确定出生时辰，帮我校准?", source: "AI时辰校准算法" },
  compatibility: { tagline: "八字合婚·五行互补分析", bestFor: "婚配合盘、关系匹配度、五行互补", sample: "我们俩八字合不合?", source: "子平合婚体系" },
  hepan: { tagline: "双人合盘·多维比对", bestFor: "四维评级、印证分歧、八字/紫微/西方", sample: "我们各方面匹配吗?", source: "多系统合盘" },
  dream: { tagline: "周公解梦·古典语义匹配", bestFor: "梦境符号解读、古典文献对照、组合梦境分析", sample: "我梦见一条龙在天上飞是什么意思?", source: "《周公解梦》《梦占逸旨》《梦溪笔谈》" },
};

export const SUBJECTS: Array<{
  key: Subject;
  label: string;
  desc: string;
  methods: Method[];
  modeByMethod: Partial<Record<Method, string>>;
  defaultSpread?: TarotSpread;
}> = [
  { key: "self_life", label: "本命格局", desc: "长期命局、性格、人生阶段", methods: ["bazi", "bazi_v2", "ziwei", "western", "vedic", "chenggu", "numerology", "tieban"], modeByMethod: { bazi: "natal", bazi_v2: "natal", ziwei: "natal", tieban: "tieban_base" } },
  { key: "annual_luck", label: "流年/阶段运", desc: "今年、近几年、大运限运", methods: ["bazi", "bazi_v2", "ziwei", "western", "vedic"], modeByMethod: { bazi: "annual_luck", bazi_v2: "annual_luck", ziwei: "annual" } },
  { key: "decision", label: "具体一事", desc: "成败、去留、该不该做", methods: ["liuyao", "meihua", "qimen", "tarot", "liuren"], modeByMethod: { liuyao: "time_qigua", meihua: "time_qigua", qimen: "hour_qimen", tarot: "tarot_spread", liuren: "liuren_divination" }, defaultSpread: "choice_two" },
  { key: "relationship", label: "关系感情", desc: "双方状态、互动、阻碍", methods: ["liuyao", "tarot", "lenormand", "ziwei", "western"], modeByMethod: { liuyao: "time_qigua", tarot: "tarot_spread", lenormand: "lenormand_spread", ziwei: "natal" }, defaultSpread: "relationship_cross" },
  { key: "career", label: "事业工作", desc: "工作路径、机会、阻力", methods: ["bazi", "bazi_v2", "liuyao", "qimen", "tarot", "lenormand"], modeByMethod: { bazi: "annual_luck", bazi_v2: "annual_luck", liuyao: "time_qigua", qimen: "hour_qimen", tarot: "tarot_spread", lenormand: "lenormand_spread" }, defaultSpread: "career_path" },
  { key: "wealth", label: "求财", desc: "财运、项目、交易", methods: ["liuyao", "qimen", "bazi", "bazi_v2"], modeByMethod: { liuyao: "time_qigua", qimen: "hour_qimen", bazi: "annual_luck", bazi_v2: "annual_luck" } },
  { key: "lost_item", label: "寻人寻物", desc: "短期寻找、方向线索", methods: ["qimen", "liuyao", "meihua"], modeByMethod: { qimen: "hour_qimen", liuyao: "time_qigua", meihua: "external_omen" } },
  { key: "home_fengshui", label: "住宅风水", desc: "命卦、坐向、三元九运", methods: ["bazhai", "xuankong"], modeByMethod: { bazhai: "residential_bazhai", xuankong: "residential_xuankong" } },
  { key: "tarot_guidance", label: "塔罗指引", desc: "今日建议、身心灵、复杂牌阵", methods: ["tarot"], modeByMethod: { tarot: "tarot_spread" }, defaultSpread: "single" },
  { key: "lenormand_guidance", label: "雷诺曼指引", desc: "日常具体占卜、组合解读", methods: ["lenormand"], modeByMethod: { lenormand: "lenormand_spread" } },
];

export const INTENTS = SUBJECTS.map((s) => ({
  key: s.key,
  label: s.label,
  desc: s.desc,
  emoji: "•",
  methods: s.methods,
}));

export const TAROT_SPREADS: Array<{ code: TarotSpread; label: string; desc: string; subjects: Subject[] }> = [
  { code: "single", label: "单张指引", desc: "今日建议/快速判断", subjects: ["tarot_guidance", "decision"] },
  { code: "three_time", label: "时间三张", desc: "过去-现在-未来", subjects: ["decision", "career", "relationship"] },
  { code: "three_mind", label: "身心灵三张", desc: "现实-情绪-建议", subjects: ["tarot_guidance"] },
  { code: "choice_two", label: "二择一", desc: "两个选项各看现状/阻力/趋势", subjects: ["decision", "career", "relationship"] },
  { code: "relationship_cross", label: "关系十字", desc: "你、对方、互动、阻碍、建议", subjects: ["relationship"] },
  { code: "career_path", label: "事业路径", desc: "现状、优势、阻碍、机会、建议", subjects: ["career"] },
  { code: "celtic_cross", label: "凯尔特十字", desc: "复杂综合问题十张", subjects: ["decision", "career", "relationship"] },
];

export const TAROT_SYSTEMS: Array<{ code: TarotSystem; label: string; desc: string }> = [
  { code: "waite", label: "韦特 RWS", desc: "图像叙事清晰，适合通用问题与新手读牌" },
  { code: "thoth", label: "托特 Thoth", desc: "占星、炼金术与卡巴拉视角更重，适合深层结构" },
  { code: "modern", label: "现代心理", desc: "聚焦情绪模式、关系边界与可执行行动" },
];
