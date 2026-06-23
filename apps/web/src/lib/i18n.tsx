// 国际化: 中英双语 Context
// 中文为主, 英文提供完整翻译, 专有名词保留原文+括号解释
import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

export type Lang = "zh" | "en";

interface I18nContextValue {
  lang: Lang;
  toggle: () => void;
  t: (key: string, fallback?: string) => string;
}

const I18nContext = createContext<I18nContextValue>({
  lang: "zh",
  toggle: () => {},
  t: (k, fb) => fb || k,
});

// ── 翻译表 ──────────────────────────────────────────────────────────
// 键名用英文, 值分别提供中/英
const DICT: Record<string, { zh: string; en: string }> = {
  // 通用
  "app.name": { zh: "玄枢", en: "Mystic Hub" },
  "app.tagline": { zh: "中西融通 · 十四术数", en: "East-West Synthesis · 14 Arts" },
  "app.disclaimer": { zh: "本站所有解读为传统文化象征视角的参考，非科学预测，亦不构成医疗、法律、财务等专业意见。重大决定请结合现实并咨询专业人士。", en: "All readings on this site are presented as traditional cultural and symbolic references, not scientific predictions. They do not constitute medical, legal, financial, or other professional advice. Important decisions should be made with professional consultation." },
  "app.compliance": { zh: "全栈 MIT/BSD 许可，零 AGPL，可闭源商用。你的 LLM API Key 仅存在浏览器本地，不会上传到本服务后端。", en: "Full-stack MIT/BSD licensed. Zero AGPL. Closed-source commercial use permitted. Your LLM API key stays in your browser — never uploaded to our backend." },

  // 导航
  "nav.home": { zh: "首页", en: "Home" },
  "nav.cast": { zh: "排盘", en: "Chart Cast" },
  "nav.daily": { zh: "今日", en: "Daily" },
  "nav.almanac": { zh: "老黄历", en: "Almanac" },
  "nav.dateselect": { zh: "择日择吉", en: "Date Select" },
  "nav.fengshui": { zh: "风水", en: "Feng Shui" },
  "nav.astrology": { zh: "占星", en: "Astrology" },
  "nav.compatibility": { zh: "合盘", en: "Synastry" },
  "nav.knowledge": { zh: "知识馆", en: "Library" },
  "nav.history": { zh: "历史", en: "History" },
  "nav.about": { zh: "关于", en: "About" },

  // 分类
  "section.east": { zh: "东方命理", en: "Eastern Arts" },
  "section.west": { zh: "西方占卜", en: "Western Divination" },
  "section.compat": { zh: "合盘姻缘", en: "Synastry & Love" },
  "section.more": { zh: "更多", en: "More" },

  // 首页
  "home.badge": { zh: "Mystic Hub · 玄枢", en: "Mystic Hub · Xuan Shu" },
  "home.hero.title": { zh: "中西融通，十四术数", en: "East Meets West · 14 Divination Arts" },
  "home.hero.subtitle": { zh: "排盘解读 · 合盘姻缘", en: "Chart Reading · Synastry Matching" },
  "home.hero.desc": { zh: "命 · 卜 · 风水术数 + 西方占星 · 塔罗 · 雷诺曼 · 数字命理。AI 解读融合中西视角，重大决定请结合现实并咨询专业人士。", en: "Destiny · Divination · Feng Shui + Western Astrology · Tarot · Lenormand · Numerology. AI-powered readings blending Eastern and Western perspectives. Important decisions require real-world consultation." },
  "home.cta.cast": { zh: "开始排盘", en: "Cast Chart" },
  "home.cta.compat": { zh: "合盘配对", en: "Synastry Match" },
  "home.cta.about": { zh: "关于", en: "About" },
  "home.compat.title": { zh: "合盘 · 缘分配对", en: "Synastry · Compatibility" },
  "home.compat.desc": { zh: "输入两人的出生信息，系统将综合八字五行互补、地支关系、神煞相合，以及西方占星的跨盘相位、宫位叠加、组合中点盘，给出加权综合评分与详细解读。", en: "Enter two birth charts. The system combines Bazi Five-Element complementarity, Earthly Branch relations, Shensha harmony, plus Western cross-aspects, house overlays, and composite midpoint charts — delivering a weighted ensemble score with detailed interpretation." },
  "home.compat.action": { zh: "开始合盘", en: "Start Synastry" },
  "home.daily.label": { zh: "今日", en: "Today" },
  "home.ask.title": { zh: "今天你适合问什么", en: "What to Ask Today" },
  "home.recent": { zh: "最近的问题 · 继续追问", en: "Recent Queries · Follow Up" },
  "home.privacy": { zh: "合规与隐私", en: "Compliance & Privacy" },

  // Cast 页
  "cast.title": { zh: "排盘", en: "Chart Cast" },
  "cast.step.subject": { zh: "意图", en: "Intent" },
  "cast.step.subject.hint": { zh: "想测什么", en: "What to ask" },
  "cast.step.birth": { zh: "命主", en: "Subject" },
  "cast.step.birth.hint": { zh: "出生信息", en: "Birth Info" },
  "cast.step.methods": { zh: "术数", en: "Methods" },
  "cast.step.methods.hint": { zh: "起哪些法", en: "Select methods" },
  "cast.step.params": { zh: "起法", en: "Setup" },
  "cast.step.params.hint": { zh: "参数 + 提问", en: "Params + Question" },
  "cast.ask.subject": { zh: "你想测什么?", en: "What would you like to explore?" },
  "cast.ask.subject.desc": { zh: "先定一个意图,系统会按它推荐最合适的术数组合。", en: "Choose an intent — the system will recommend the best methods." },
  "cast.birth.title": { zh: "命主 · 出生与时间", en: "Subject · Birth & Time" },
  "cast.birth.desc": { zh: "填得越准,排盘越贴近你。城市用于经纬度 + 真太阳时换算。", en: "More accurate input = more precise charts. City is used for coordinates + true solar time." },
  "cast.birth.year": { zh: "年", en: "Year" },
  "cast.birth.month": { zh: "月", en: "Month" },
  "cast.birth.day": { zh: "日", en: "Day" },
  "cast.birth.hour": { zh: "时", en: "Hour" },
  "cast.birth.minute": { zh: "分", en: "Min" },
  "cast.birth.gender": { zh: "性别", en: "Gender" },
  "cast.birth.city": { zh: "出生城市", en: "Birth City" },
  "cast.gender.male": { zh: "男", en: "Male" },
  "cast.gender.female": { zh: "女", en: "Female" },
  "cast.gender.unspec": { zh: "未指定", en: "Unspecified" },
  "cast.methods.title": { zh: "推荐术数与起法", en: "Recommended Methods" },
  "cast.methods.more": { zh: "更多术数", en: "More Methods" },
  "cast.methods.less": { zh: "收起更多术数", en: "Show Less" },
  "cast.params.title": { zh: "本次起法参数", en: "Casting Parameters" },
  "cast.params.desc": { zh: "仅按所选术数显示需要的参数,其他隐藏。", en: "Only parameters needed by selected methods are shown." },
  "cast.question.label": { zh: "问题", en: "Question" },
  "cast.question.help": { zh: "系统会把\"测算对象、起法、参数\"写入盘面依据,解读只基于盘面事实。", en: "The system records your subject, method, and parameters as calculation basis. Interpretation is based on chart facts only." },
  "cast.reset": { zh: "重置", en: "Reset" },
  "cast.prev": { zh: "← 上一步", en: "← Back" },
  "cast.next": { zh: "下一步 →", en: "Next →" },
  "cast.submit": { zh: "排盘", en: "Cast" },
  "cast.submitting": { zh: "排盘中...", en: "Casting..." },

  // Result 页
  "result.empty": { zh: "还没有排盘数据。", en: "No chart data yet." },
  "result.cast.again": { zh: "再排一次", en: "Cast Again" },
  "result.favorite": { zh: "☆ 收藏", en: "☆ Save" },
  "result.favorited": { zh: "★ 已收藏", en: "★ Saved" },
  "result.share": { zh: "生成分享卡", en: "Share Card" },
  "result.accurate": { zh: "准", en: "Accurate" },
  "result.inaccurate": { zh: "不准", en: "Inaccurate" },
  "result.pending": { zh: "待观察", en: "Pending" },
  "result.basis.title": { zh: "本次采用的起法", en: "Calculation Basis" },
  "result.basis.method": { zh: "方法", en: "Method" },
  "result.basis.mode": { zh: "模式", en: "Mode" },
  "result.basis.subject": { zh: "对象", en: "Subject" },
  "result.basis.input": { zh: "输入", en: "Input" },
  "result.basis.rule": { zh: "规则", en: "Rule" },
  "result.basis.scope": { zh: "范围", en: "Scope" },
  "result.basis.limits": { zh: "不可判断范围 / 限制", en: "Limitations" },

  // Compatibility
  "compat.title": { zh: "合盘 · 缘分配对", en: "Synastry · Compatibility" },
  "compat.personA": { zh: "第一位 · Ta", en: "Person A" },
  "compat.personB": { zh: "第二位 · Ta", en: "Person B" },
  "compat.method": { zh: "选择合盘方法", en: "Select Method" },
  "compat.method.desc": { zh: "八字合婚侧重五行互补与地支关系；西方合盘侧重行星相位与宫位互动；中西合参综合加权评分。", en: "Bazi method focuses on Five-Element harmony and Earthly Branch relations. Western method focuses on planetary aspects and house overlays. Combined uses weighted ensemble scoring." },
  "compat.bazi": { zh: "八字合婚", en: "Bazi Match" },
  "compat.bazi.desc": { zh: "基于日主五行、地支关系、神煞互补的传统合婚法", en: "Traditional marriage matching via Day Master elements, Branch relations, and Shensha harmony" },
  "compat.western": { zh: "西方合盘", en: "Western Synastry" },
  "compat.western.desc": { zh: "跨盘相位、宫位叠加、组合中点盘的综合分析", en: "Cross-chart aspects, house overlays, and composite midpoint analysis" },
  "compat.both": { zh: "中西合参", en: "Combined" },
  "compat.both.desc": { zh: "八字 + 西方占星双重验证，加权综合评分", en: "Dual validation with Bazi + Western astrology, weighted ensemble score" },
  "compat.compute": { zh: "开始合盘", en: "Compute Synastry" },
  "compat.computing": { zh: "合盘计算中...", en: "Computing synastry..." },
  "compat.retry": { zh: "重新合盘", en: "New Synastry" },
  "compat.noResult": { zh: "尚未计算合盘", en: "No synastry computed yet" },
  "compat.noResult.hint": { zh: "请返回上一步填写信息并提交", en: "Go back to fill in info and submit" },

  // 老黄历
  "almanac.title": { zh: "老黄历", en: "Chinese Almanac" },
  "almanac.prev": { zh: "← 上月", en: "← Prev" },
  "almanac.next": { zh: "下月 →", en: "Next →" },
  "almanac.today": { zh: "回到本月", en: "Today" },

  // 择日
  "dateselect.title": { zh: "择日择吉", en: "Auspicious Date Select" },
  "dateselect.desc": { zh: "基于建除十二神 · 二十八星宿 · 吉神凶煞 · 宜忌冲煞 · 综合评分", en: "Based on Jianchu stars · 28 Mansions · Auspicious/Inauspicious gods · Yi/Ji · Composite scoring" },
  "dateselect.purpose": { zh: "请选择用途", en: "Select Purpose" },
  "dateselect.marriage": { zh: "婚嫁", en: "Marriage" },
  "dateselect.opening": { zh: "开业", en: "Business" },
  "dateselect.travel": { zh: "出行", en: "Travel" },
  "dateselect.moving": { zh: "搬家", en: "Moving" },
  "dateselect.construction": { zh: "动土", en: "Construction" },
  "dateselect.general": { zh: "通用吉日", en: "General" },
  "dateselect.top": { zh: "本月推荐", en: "Top Picks" },
  "dateselect.score": { zh: "分", en: "pts" },
  "dateselect.great": { zh: "大吉日", en: "Excellent" },
  "dateselect.good": { zh: "宜用日", en: "Favorable" },
  "dateselect.neutral": { zh: "平日", en: "Neutral" },
  "dateselect.bad": { zh: "慎用日", en: "Caution" },
  "dateselect.stats": { zh: "本月共", en: "This month:" },
  "dateselect.goodDays": { zh: "个宜用日", en: "favorable days" },
  "dateselect.greatDays": { zh: "其中大吉日", en: "excellent days" },
  "dateselect.totalDays": { zh: "总天数", en: "total days" },

  // 风水
  "fengshui.title": { zh: "风水专区", en: "Feng Shui" },
  "fengshui.desc": { zh: "八宅明镜 + 玄空飞星 — 宅命相配、三元九运、飞星旺衰", en: "Eight Mansions + Flying Stars — House-Life matching, Nine Periods, Star strength" },
  "fengshui.bazhai": { zh: "八宅明镜", en: "Eight Mansions" },
  "fengshui.xuankong": { zh: "玄空飞星", en: "Flying Stars" },
  "fengshui.submit": { zh: "风水排盘", en: "Cast Feng Shui" },

  // 知识馆
  "knowledge.title": { zh: "玄学知识馆", en: "Occult Library" },
  "knowledge.desc": { zh: "五行生克 · 神煞大全 · 经典文摘 · 职业适配 · 节气体质 — 传统文化知识集", en: "Five Elements · Shensha · Classical Texts · Career Guidance · Seasonal Wellness" },
  "knowledge.wuxing": { zh: "五行详解", en: "Five Elements" },
  "knowledge.shensha": { zh: "神煞大全", en: "Shensha Gods" },
  "knowledge.classical": { zh: "经典文摘", en: "Classical Texts" },
  "knowledge.profession": { zh: "职业适配", en: "Career Match" },
  "knowledge.wellness": { zh: "节气养生", en: "Wellness" },

  // 404
  "404.badge1": { zh: "无明 · Avidyā", en: "Avidyā · Unseeing" },
  "404.badge2": { zh: "Void · 虚空", en: "Void · Emptiness" },
  "404.title": { zh: "此页不在命盘之中", en: "This Page Is Not in the Chart" },
  "404.desc": { zh: "你所寻之境不在八卦之内，亦不落黄道十二宫。或许是星象偏移，或许是卦爻未成——请折返，另寻他途。", en: "What you seek lies beyond the Eight Trigrams and outside the Zodiac. Perhaps the stars have shifted, or the hexagram remains unformed — please turn back and seek another path." },
  "404.home": { zh: "返回首页", en: "Return Home" },
  "404.cast": { zh: "排盘问事 →", en: "Cast a Chart →" },
  "404.iching": { zh: "「眇能视，跛能履，履虎尾，咥人，凶」——《易·履卦》", en: "\"He who treads on the tail of the tiger will be bitten. Misfortune.\" — I Ching, Hexagram 10 (Lü)" },

  // 关于
  "about.title": { zh: "关于 Mystic Hub", en: "About Mystic Hub" },
  "about.desc": { zh: "Mystic Hub 是一个面向研究 / 兴趣 / 自我反思的玄学工具。集成十四种术数(命 / 卜 / 风水 / 西方)，统一排盘接口 + 多 LLM 流式解读。全栈 MIT/BSD 许可，零 AGPL，可闭源商用。", en: "Mystic Hub is an esoteric arts tool for research, interest, and self-reflection. It integrates 14 methods (Destiny / Divination / Feng Shui / Western), with a unified casting interface and multi-LLM streaming interpretation. Full-stack MIT/BSD licensed." },
  "about.disclaimer": { zh: "免责声明（全文）", en: "Disclaimer (Full)" },
  "about.llm": { zh: "LLM 解读设置", en: "LLM Settings" },
  "about.tech": { zh: "技术栈与合规", en: "Tech Stack & Compliance" },

  // 方法
  "methods.refs": { zh: "文献依据", en: "References" },
  "methods.cast": { zh: "用此法排盘 →", en: "Cast with this method →" },
  "methods.notice": { zh: "以上为文化与符号象征视角的参考,非科学预测。重大决定请结合现实并咨询专业人士。", en: "The above is a cultural and symbolic reference, not a scientific prediction. For important decisions, please consult professionals." },

  // History
  "history.title": { zh: "我的问题日志", en: "My Query Log" },
  "history.empty": { zh: "还没有问题日志。", en: "No queries yet." },
  "history.clear": { zh: "清空", en: "Clear" },
  "history.filter.all": { zh: "全部", en: "All" },
  "history.view": { zh: "查看", en: "View" },
  "history.continue": { zh: "继续追问", en: "Follow Up" },
  "history.delete": { zh: "删", en: "Del" },

  // 日常
  "daily.title": { zh: "今日个人化", en: "Daily · Personalized" },
  "daily.noBirth": { zh: "录入一次生日,这里会按你的日主 + 今日五行生成温和的互动建议。", en: "Enter your birth info once, and your Day Master + today's element will generate personalized suggestions." },
  "daily.enterBirth": { zh: "录入生日 + 排一次盘", en: "Enter Birth + Cast Chart" },
  "daily.tarot": { zh: "今日塔罗 · 单张", en: "Today's Tarot · Single" },
  "daily.question": { zh: "今日一问", en: "Daily Reflection" },
  "daily.question.disclaimer": { zh: "只作自我观察的入口,不对应确定性预测。", en: "For self-reflection only. Not a deterministic prediction." },
  "daily.basis": { zh: "本次采用的起法与限制", en: "Calculation Basis & Limitations" },

  // LLM Settings
  "settings.apiKey": { zh: "LLM API Key", en: "LLM API Key" },
  "settings.provider": { zh: "提供商", en: "Provider" },
  "settings.model": { zh: "模型", en: "Model" },
  "settings.save": { zh: "保存 (仅本地)", en: "Save (Local Only)" },

  // 通用动作
  "action.loading": { zh: "加载中...", en: "Loading..." },
  "action.error": { zh: "出错了", en: "Error" },
  "action.retry": { zh: "重试", en: "Retry" },
  "action.close": { zh: "关闭", en: "Close" },
  "action.confirm": { zh: "确认", en: "Confirm" },
  "action.cancel": { zh: "取消", en: "Cancel" },

  // 语言
  "lang.switch": { zh: "EN", en: "中文" },
  "lang.label": { zh: "语言", en: "Language" },

  // SEO
  "seo.home": { zh: "玄枢 Mystic Hub — 中西命理合参平台", en: "Mystic Hub — East-West Divination Platform" },
  "seo.cast": { zh: "排盘 — 玄枢", en: "Chart Cast — Mystic Hub" },
  "seo.result": { zh: "排盘结果 — 玄枢", en: "Chart Result — Mystic Hub" },
  "seo.daily": { zh: "今日运势 — 玄枢", en: "Daily — Mystic Hub" },
  "seo.almanac": { zh: "老黄历 — 玄枢", en: "Almanac — Mystic Hub" },
  "seo.dateselect": { zh: "择日择吉 — 玄枢", en: "Date Selection — Mystic Hub" },
  "seo.fengshui": { zh: "风水专区 — 玄枢", en: "Feng Shui — Mystic Hub" },
  "seo.compat": { zh: "合盘配对 — 玄枢", en: "Synastry — Mystic Hub" },
  "seo.knowledge": { zh: "玄学知识馆 — 玄枢", en: "Occult Library — Mystic Hub" },
  "seo.about": { zh: "关于 — 玄枢", en: "About — Mystic Hub" },
  "seo.history": { zh: "历史记录 — 玄枢", en: "History — Mystic Hub" },
  "seo.notfound": { zh: "404 — 玄枢", en: "404 — Mystic Hub" },

  // Intro for Western users
  "intro.baZi": { zh: "八字 (Bā Zì)", en: "Ba Zi (Eight Characters / Four Pillars of Destiny)" },
  "intro.baZi.desc": { zh: "以出生年月日时的天干地支构成四柱八字，分析日主五行强弱、格局用神、大运流年。", en: "Constructed from the Heavenly Stems and Earthly Branches of birth year, month, day, and hour. Analyzes Day Master element strength, pattern, Yong Shen (useful god), and luck cycles." },
  "intro.ziWei": { zh: "紫微斗数 (Zǐ Wēi Dòu Shù)", en: "Zi Wei Dou Shu (Purple Star Astrology)" },
  "intro.ziWei.desc": { zh: "以出生时辰定命宫，十四主星分入十二宫，推演人生格局与大限流年。", en: "Places 14 major stars into 12 palaces based on birth time. Reads life patterns and period-based luck cycles." },
  "intro.wuXing": { zh: "五行 (Wǔ Xíng)", en: "Wu Xing (Five Elements / Five Phases)" },
  "intro.wuXing.desc": { zh: "木火土金水，相生相克，是一切中式命理的基础框架。", en: "Wood, Fire, Earth, Metal, Water — generating and controlling cycles. The foundational framework of all Chinese metaphysics." },

  // ── 共享表单组件 ────────────────────────────────────────────────────
  "form.birth.title": { zh: "出生信息", en: "Birth Info" },
  "form.birth.desc": { zh: "填得越准，排盘越贴近你。", en: "More accurate input = more precise charts." },
  "form.birth.year": { zh: "出生年", en: "Year" },
  "form.birth.month": { zh: "月", en: "Month" },
  "form.birth.day": { zh: "日", en: "Day" },
  "form.birth.hour": { zh: "时", en: "Hour" },
  "form.birth.minute": { zh: "分", en: "Min" },
  "form.birth.gender": { zh: "性别", en: "Gender" },
  "form.birth.city": { zh: "出生城市", en: "Birth City" },
  "form.birth.genderMale": { zh: "男", en: "Male" },
  "form.birth.genderFemale": { zh: "女", en: "Female" },
  "form.birth.genderUnspec": { zh: "未指定", en: "Unspecified" },
  "form.question.label": { zh: "问题", en: "Question" },
  "form.question.optional": { zh: "可选", en: "Optional" },
  "form.question.required": { zh: "必填", en: "Required" },
  "form.question.placeholder": { zh: "请描述你要问的事...", en: "Describe what you'd like to ask..." },
  "form.question.hint": { zh: "写清楚要测的事，解读会更聚焦。", en: "Clear questions yield more focused readings." },
  "form.question.chars": { zh: "字", en: "chars" },
  "form.spread.label": { zh: "牌阵", en: "Spread" },
  "form.spread.desc": { zh: "选择塔罗/雷诺曼牌阵", en: "Choose card spread" },
  "form.direction.label": { zh: "坐向", en: "Sitting Direction" },
  "form.direction.desc": { zh: "选择房屋坐山/门向方位", en: "Select house sitting/facing direction" },
  "form.direction.year": { zh: "建造/入伙年份", en: "Construction Year" },
  "form.mode.label": { zh: "起法", en: "Casting Mode" },
  "form.mode.desc": { zh: "选择起卦/排盘方式", en: "Select casting method" },
  "form.coin.label": { zh: "摇卦 · 六次铜钱结果", en: "Coin Toss · 6 Results" },
  "form.coin.desc": { zh: "每次抛三枚铜钱，记录阴阳。或使用自动摇卦。", en: "Toss 3 coins per line, record yin/yang. Or use auto-toss." },
  "form.coin.tossN": { zh: "第 {n} 次", en: "Toss {n}" },
  "form.coin.oldYang": { zh: "老阳 ○ (3正)", en: "Old Yang ○" },
  "form.coin.youngYang": { zh: "少阳 — (2正1反)", en: "Young Yang —" },
  "form.coin.youngYin": { zh: "少阴 - - (1正2反)", en: "Young Yin - -" },
  "form.coin.oldYin": { zh: "老阴 × (3反)", en: "Old Yin ×" },
  "form.coin.auto": { zh: "自动摇卦", en: "Auto Toss" },
  "form.seed.label": { zh: "固定种子", en: "Fixed Seed" },
  "form.seed.hint": { zh: "固定种子使结果可复现", en: "Lock seed for reproducible results" },
  "form.name.label": { zh: "姓名（可选）", en: "Name (optional)" },
  "form.zodiac.father": { zh: "父生肖（可选·条文校验）", en: "Father Zodiac (optional)" },
  "form.zodiac.mother": { zh: "母生肖（可选·条文校验）", en: "Mother Zodiac (optional)" },

  // ── 提交相关 ────────────────────────────────────────────────────────
  "form.submit": { zh: "开始排盘", en: "Cast Chart" },
  "form.submitting": { zh: "排盘中...", en: "Casting..." },
  "form.reset": { zh: "重置", en: "Reset" },

  // ── 合参篮 ──────────────────────────────────────────────────────────
  "basket.add": { zh: "+ 加入合参篮", en: "+ Add to Basket" },
  "basket.added": { zh: "✓ 已加入合参篮", en: "✓ In Basket" },
  "basket.remove": { zh: "移出", en: "Remove" },
  "basket.title": { zh: "合参篮", en: "Aggregation Basket" },
  "basket.empty": { zh: "合参篮为空。在各术法页排盘后点击「加入合参篮」。", en: "Basket is empty. Cast charts on method pages and click \"Add to Basket\"." },
  "basket.view": { zh: "查看合参篮", en: "View Basket" },
  "basket.clear": { zh: "清空", en: "Clear" },

  // ── 聚合页 ──────────────────────────────────────────────────────────
  "aggregate.title": { zh: "多法合参", en: "Multi-Method Aggregation" },
  "aggregate.desc": { zh: "选择多个术法联合排盘，系统将交叉验证各法结果，识别共识与冲突，给出加权综合评分。", en: "Select multiple methods for joint casting. The system cross-validates results, identifies consensus and conflicts, and provides a weighted ensemble score." },
  "aggregate.selectMethods": { zh: "选择术法", en: "Select Methods" },
  "aggregate.selectMethods.hint": { zh: "至少选择 2 个术法，建议不超过 6 个。", en: "Select at least 2 methods, recommended ≤ 6." },
  "aggregate.sharedBirth": { zh: "共享出生信息", en: "Shared Birth Info" },
  "aggregate.sharedBirth.hint": { zh: "将用于以下术法: ", en: "Will be used for: " },
  "aggregate.noBirthNeeded": { zh: "所选术法均不需要出生信息", en: "Selected methods do not require birth info" },
  "aggregate.submit": { zh: "合参排盘", en: "Aggregate Cast" },
  "aggregate.submitting": { zh: "多法计算中...", en: "Computing multiple methods..." },
  "aggregate.fromBasket": { zh: "从合参篮导入", en: "Import from Basket" },

  // ── 术法独立页 — 通用 ───────────────────────────────────────────────
  "method.backToMethods": { zh: "← 术法列表", en: "← All Methods" },
  "method.formTitle": { zh: "排盘参数", en: "Chart Parameters" },
  "method.formDesc.single": { zh: "仅需以下参数即可起盘。", en: "Only the following parameters are needed." },
  "method.formDesc.birth": { zh: "出生信息 + 以下参数。", en: "Birth info + the following parameters." },
  "method.notice": { zh: "以上为传统文化象征视角的参考，非科学预测。重大决定请结合现实并咨询专业人士。", en: "The above is a cultural and symbolic reference, not a scientific prediction. For important decisions, please consult professionals." },

  // ── 各术法页专属 ─────────────────────────────────────────────────────
  "method.bazi.title": { zh: "八字命盘", en: "Ba Zi · Four Pillars" },
  "method.bazi.desc": { zh: "以出生年月日时的天干地支构成四柱八字，分析日主五行强弱、格局用神、大运流年。经典子平八字体系。", en: "Constructed from the Heavenly Stems and Earthly Branches of birth year, month, day, and hour. Analyzes Day Master element strength, pattern, Yong Shen, and luck cycles. Classical Zi Ping system." },
  "method.bazi_v2.title": { zh: "八字精算", en: "Ba Zi · Enhanced" },
  "method.bazi_v2.desc": { zh: "精算版八字——用神格局神煞全解。在传统四柱基础上加强神煞精断、职业适配、用神喜忌分析。", en: "Enhanced Ba Zi — complete analysis of Yong Shen, patterns, and Shensha gods. Professional-grade career guidance and element balance." },
  "method.ziwei.title": { zh: "紫微斗数", en: "Zi Wei Dou Shu" },
  "method.ziwei.desc": { zh: "以出生时辰定命宫，十四主星分入十二宫，推演人生格局与大限流年。三方四正、四化飞星。", en: "Places 14 major stars into 12 palaces based on birth time. Reads life patterns and period-based luck cycles through palace interactions and Four Transformations." },
  "method.qimen.title": { zh: "奇门遁甲", en: "Qi Men Dun Jia" },
  "method.qimen.desc": { zh: "时家奇门，一事一局看行动时机。结合时辰、方位、八门九星，判断吉凶方位和最佳行动时机。", en: "Hour-based Qi Men — analyzes action timing per situation. Combines time, direction, 8 Doors and 9 Stars to determine favorable positions and optimal timing." },
  "method.liuyao.title": { zh: "六爻纳甲", en: "Liu Yao · Coin Divination" },
  "method.liuyao.desc": { zh: "一事一卦，以铜钱六次成卦，重世应、动爻、用神。可手动摇卦或用时间/数字起卦。", en: "One question, one hexagram. Cast 6 coin tosses to form a hexagram. Analyzes Shi/Ying lines, moving lines, and Yong Shen. Manual coin, time-based, or number-based casting." },
  "method.meihua.title": { zh: "梅花易数", en: "Mei Hua Yi Shu" },
  "method.meihua.desc": { zh: "时间/数字/外应起卦，看体用生克。象数起卦、心易灵动、吉凶速断。", en: "Plum Blossom numerology — cast by time, numbers, or external omens. Analyzes Ti-Yong (subject-object) interactions for quick fate judgments." },
  "method.chenggu.title": { zh: "称骨歌", en: "Bone Weight · Chenggu" },
  "method.chenggu.desc": { zh: "袁天罡称骨歌——以出生年月日时对应骨重，累计总两数，查对应歌诀断命。传统速断法。", en: "Yuan Tiangang's Bone Weight method — each birth pillar has a bone weight. The total weight maps to a classical verse judgment. Traditional quick assessment." },
  "method.liuren.title": { zh: "大六壬", en: "Da Liu Ren" },
  "method.liuren.desc": { zh: "三式之首，以天盘地盘四课三传推演人事。用于复杂决疑、天时地利、因果走向。", en: "The foremost of the Three Styles. Uses Heaven/Earth plates, Four Lessons, and Three Transmissions to analyze human affairs, timing, and causality." },
  "method.tieban.title": { zh: "铁板神数", en: "Tie Ban Shen Shu" },
  "method.tieban.desc": { zh: "铁板条文——以四柱八字转换为太玄数，编码考刻分，落条文断终身。六亲校验加持。", en: "Iron Plate divination — converts Four Pillars to Tai Xuan numbers, encodes Ke-Fen, and maps to ironclad verse judgments. Ancestral verification included." },
  "method.western.title": { zh: "西方占星", en: "Western Astrology" },
  "method.western.desc": { zh: "现代西方占星——计算本命盘、行星相位、宫位系统。需要精确的出生经纬度和时区以确定上升星座。", en: "Modern Western astrology — calculates natal chart, planetary aspects, and house system. Requires accurate birth coordinates and timezone for ascendant calculation." },
  "method.vedic.title": { zh: "吠陀占星", en: "Vedic Astrology · Jyotish" },
  "method.vedic.desc": { zh: "吠陀恒星黄道命盘——二十七宿、大运体系、星曜力度。采用恒星黄道 Lahiri 岁差校正。", en: "Vedic sidereal zodiac chart — 27 Nakshatras, Dasha period system, and planetary strengths. Uses Lahiri ayanamsha precession correction." },
  "method.tarot.title": { zh: "塔罗", en: "Tarot" },
  "method.tarot.desc": { zh: "韦特体系塔罗——无需生辰，按问题选择牌阵。从单张指引到凯尔特十字，意象解读。", en: "Waite-style Tarot — no birth info needed. Choose a spread based on your question, from single-card guidance to Celtic Cross. Imagery-based reading." },
  "method.lenormand.title": { zh: "雷诺曼", en: "Lenormand" },
  "method.lenormand.desc": { zh: "Petit Lenormand 体系——36张具体象征牌，组合解读日常。Grand Tableau、日常决策。无需生辰。", en: "Petit Lenormand system — 36 concrete symbol cards for combinatorial daily readings. Grand Tableau spreads and daily decisions. No birth info needed." },
  "method.numerology.title": { zh: "生命灵数", en: "Life Path Numerology" },
  "method.numerology.desc": { zh: "毕达哥拉斯数字命理——只需出生年月日，计算生命灵数、命运数字、周期年运。可加姓名数字。", en: "Pythagorean numerology — only birth date needed. Calculates Life Path number, Destiny number, and personal year cycles. Optional name numerology." },
  "method.xuankong.title": { zh: "玄空飞星", en: "Xuan Kong Flying Stars" },
  "method.xuankong.desc": { zh: "三元九运玄空飞星——不需生辰，只要房屋坐向+建造年份。宅盘理气、旺山旺向、飞星旺衰。", en: "Flying Star Feng Shui — no birth info needed. Requires sitting direction and construction year. Analyzes house chart, prosperous stars, and period influences." },
  "method.bazhai.title": { zh: "八宅明镜", en: "Eight Mansions · Bazhai" },
  "method.xiaoliuren.title": { zh: "小六壬", en: "Xiao Liu Ren · Palm Divination" },
  "method.xiaoliuren.desc": { zh: "小六壬掌诀——以月日时三轮推六宫，速断吉凶。可按时辰或任意三数起课，简明直观。", en: "Xiao Liu Ren palm method — derives one of 6 positions from lunar month, day, and hour for quick fortune judgment. Time-based or arbitrary 3-number casting." },
  "method.bazhai.desc": { zh: "八宅明镜——以宅主生辰定命卦，结合坐向方位，推四吉四凶方。门床灶布局指引。", en: "Eight Mansions method — determines Life Gua from birth date, matches with house direction to identify 4 auspicious and 4 inauspicious sectors. Door, bed, and stove placement guidance." },

  // ── 导航独立页 ───────────────────────────────────────────────────────
  "nav.aggregate": { zh: "多法合参", en: "Aggregate" },
  "nav.bazi": { zh: "八字", en: "Ba Zi" },
  "nav.baziV2": { zh: "八字精算", en: "Ba Zi Pro" },
  "nav.ziwei": { zh: "紫微斗数", en: "Zi Wei" },
  "nav.qimen": { zh: "奇门遁甲", en: "Qi Men" },
  "nav.liuyao": { zh: "六爻", en: "Liu Yao" },
  "nav.meihua": { zh: "梅花易数", en: "Mei Hua" },
  "nav.chenggu": { zh: "称骨", en: "Bone Weight" },
  "nav.liuren": { zh: "大六壬", en: "Liu Ren" },
  "nav.tieban": { zh: "铁板神数", en: "Tie Ban" },
  "nav.xiaoliuren": { zh: "小六壬", en: "Xiao Liu Ren" },
  "nav.western": { zh: "西方占星", en: "Astrology" },
  "nav.vedic": { zh: "吠陀占星", en: "Vedic" },
  "nav.tarot": { zh: "塔罗", en: "Tarot" },
  "nav.lenormand": { zh: "雷诺曼", en: "Lenormand" },
  "nav.numerology": { zh: "灵数", en: "Numerology" },
  "nav.xuankong": { zh: "玄空", en: "Flying Star" },
  "nav.bazhai": { zh: "八宅", en: "8 Mansions" },
  "nav.reading": { zh: "12法解读", en: "12-Method Reading" },
  "nav.readingHistory": { zh: "解读历史", en: "Reading History" },
  "section.eastMantra": { zh: "东方命理", en: "Eastern Arts" },
  "section.westOracle": { zh: "西方占卜", en: "Western Divination" },
  "section.fengshuiNav": { zh: "风水堪舆", en: "Feng Shui" },
  "section.aggregateNav": { zh: "合参与工具", en: "Aggregate & Tools" },
};

// ── Provider ────────────────────────────────────────────────────────
export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    // 从 localStorage 恢复
    try { return (localStorage.getItem("mystic:lang") as Lang) || "zh"; }
    catch { return "zh"; }
  });

  const toggle = useCallback(() => {
    setLang((prev) => {
      const next = prev === "zh" ? "en" : "zh";
      try { localStorage.setItem("mystic:lang", next); } catch { /* noop */ }
      return next;
    });
  }, []);

  const t = useCallback((key: string, fallback?: string) => {
    const entry = DICT[key];
    if (!entry) return fallback || key;
    return entry[lang] || fallback || key;
  }, [lang]);

  return (
    <I18nContext.Provider value={{ lang, toggle, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

// 可直接导入的翻译函数(不在 React 组件内时使用)
export function getDict() { return DICT; }
