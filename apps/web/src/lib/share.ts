// 分享卡生成:模板化、不调用 LLM,保证:
//   - 不写完整生日(只写主题+方法+结论+建议)
//   - 不出现恐吓/绝对判断
//   - 强调"自我观察/传统文化参考"
import type { HistoryEntry } from "../store/history";
import type { Method, Subject } from "./types";
import { SUBJECTS } from "./method-info";

const METHOD_LABEL: Record<Method, string> = {
  bazi: "八字", bazi_v2: "八字·精算", ziwei: "紫微", qimen: "奇门",
  liuyao: "六爻", meihua: "梅花", chenggu: "称骨",
  bazhai: "八宅", xuankong: "玄空",
  western: "西方占星", vedic: "吠陀",
  tarot: "塔罗", numerology: "数字命理",
  lenormand: "雷诺曼", liuren: "大六壬", tieban: "铁板神数",
  cross_validator: "交叉验证", hour_calibrator: "时辰校准", compatibility: "合婚",
};

const SUBJECT_LABEL: Record<Subject, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<Subject, string>,
);

const SUBJECT_SUMMARY: Record<Subject, string> = {
  self_life: "聚焦长期命局与核心人格主题,可作长期自我观察的参考。",
  annual_luck: "聚焦近阶段运势与大运流年,适合做节奏参考。",
  decision: "针对具体一事看时机、阻力、趋势,适合短期决策参考。",
  relationship: "聚焦关系状态与互动模式,适合沟通前自我观察。",
  career: "聚焦工作路径与机会阻力,适合阶段规划参考。",
  wealth: "聚焦财运与项目取舍,适合节奏与方向参考。",
  lost_item: "聚焦短期寻找的方向线索,适合作为辅助参考。",
  home_fengshui: "聚焦住宅命卦与坐向理气,适合环境参考。",
  tarot_guidance: "聚焦当下建议与身心灵整合,适合作为当下提问。",
  lenormand_guidance: "雷诺曼 36 张牌阵指引,聚焦日常决策与细节解读。",
};

const SUGGESTIONS = [
  "把结果当作自我观察工具,不替代现实判断。",
  "重大决定请结合现实并咨询专业人士。",
  "建议记下今天的实际体验,几周后回看验证。",
];

// 黑名单:出现这些词就替换成温和表达
const SOFTEN: Record<string, string> = {
  "一定": "倾向", "必定": "倾向", "绝对": "通常", "必然": "可能",
  "大凶": "阻力", "必败": "承压", "死": "阻", "杀": "克",
};

function soften(line: string): string {
  let out = line;
  for (const [k, v] of Object.entries(SOFTEN)) {
    out = out.split(k).join(v);
  }
  return out;
}

export interface ShareCard {
  title: string;
  subject: string;
  methods: string[];
  summary: string;
  basis: string[];
  cards: string[];   // 塔罗牌面摘要(其他术数空)
  suggestions: string[];
  footer: string;
}

function subjectLabel(s?: Subject): string {
  return s ? (SUBJECT_LABEL[s] || s) : "综合";
}

function methodLabel(m: Method): string {
  return METHOD_LABEL[m] || m;
}

export function buildShareCard(entry: HistoryEntry): ShareCard {
  const subjectName = subjectLabel(entry.subject);
  const methodNames = entry.methods.map(methodLabel);
  const summary = soften(entry.subject
    ? (SUBJECT_SUMMARY[entry.subject] || "综合参考。")
    : "综合参考。");

  // 盘面依据:从每张盘里抽 rule / mode / subject 1-2 行
  const basis: string[] = [];
  for (const m of entry.methods) {
    const c = entry.charts?.[m];
    const raw = c?.raw || {};
    const cb = raw.calculation_basis || {};
    const mode = cb.mode || raw.mode || "默认";
    const rule = cb.rule || `${methodLabel(m)} · 标准起法`;
    const sub = cb.subject || raw.subject || entry.subject || "—";
    basis.push(`${methodLabel(m)} · 模式 ${mode} · 主题 ${sub} · ${rule}`);
  }

  // 塔罗牌面:只抽中的牌不重不漏,只列名+位+朝向
  const cards: string[] = [];
  for (const m of entry.methods) {
    if (m !== "tarot") continue;
    const c = entry.charts?.[m];
    const raw = c?.raw || {};
    const spreadName = raw.spread_name || raw.spread || "—";
    const list = Array.isArray(raw.cards) ? raw.cards : [];
    if (list.length) {
      cards.push(`牌阵: ${spreadName}(${list.length} 张)`);
      for (const card of list) {
        const pos = card.position || "位";
        const nm = card.name || "?";
        const orient = card.orient || "";
        cards.push(`· ${pos} · ${nm} ${orient ? "(" + orient + ")" : ""}`);
      }
    }
  }

  const date = new Date(entry.ts).toLocaleDateString("zh-CN", { month: "long", day: "numeric" });

  return {
    title: `${subjectName} · ${date}`,
    subject: subjectName,
    methods: methodNames,
    summary,
    basis,
    cards,
    suggestions: SUGGESTIONS,
    footer: "本卡来自玄枢 Mystic Hub · 传统文化象征视角 · 非科学预测,仅作自我观察与文化参考。",
  };
}

export function shareCardToText(card: ShareCard): string {
  const lines: string[] = [];
  lines.push(`【${card.title}】`);
  lines.push(`方法: ${card.methods.join(" / ")}`);
  lines.push("");
  lines.push(card.summary);
  if (card.basis.length) {
    lines.push("");
    lines.push("盘面依据");
    for (const b of card.basis) lines.push(`· ${b}`);
  }
  if (card.cards.length) {
    lines.push("");
    lines.push("牌面");
    for (const c of card.cards) lines.push(c);
  }
  lines.push("");
  lines.push("建议");
  for (let i = 0; i < card.suggestions.length; i++) lines.push(`${i + 1}. ${card.suggestions[i]}`);
  lines.push("");
  lines.push(card.footer);
  return lines.join("\n");
}
