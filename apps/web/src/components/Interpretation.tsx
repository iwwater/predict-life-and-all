// 解读面板: 流式 + Markdown + 危机 block + 免责常驻（「古籍×仪器」纸墨风格）
import { useEffect, useRef, useState } from "react";
import { fetchPrompt, streamInterpret } from "../lib/api";
import { streamChat } from "../lib/llm-client";
import { md } from "../lib/markdown";
import { useKeys } from "../store/keys";
import type { ChartResult } from "../lib/types";

interface Props {
  charts: ChartResult[];
  question: string;
  enhancedData?: Record<string, any>;
}

interface InterpretState {
  text: string; loading: boolean; done: boolean; blocked: boolean;
  meta?: { softened_terms?: string[]; methods?: string[]; flags?: string[] };
  error?: string;
}

const DISCLAIMER = "以上为传统文化象征视角的参考，非科学预测，重大决定请结合现实并咨询专业人士。";

const CRISIS_FALLBACK = {
  blocked: true,
  text:
    "听起来你正承受很大的痛苦。这不是算命能回答的问题，也请不要独自承受。\n\n" +
    "中国心理援助热线:400-161-9995\n" +
    "北京心理危机研究与干预中心:010-82951332\n" +
    "或与信任的人、专业人士谈谈。",
};

function buildPromptFromCharts(charts: ChartResult[], question: string, enhancedData?: Record<string, any>) {
  const methods = Array.from(new Set(charts.map((c) => c.method)));
  const serialize = (c: ChartResult) => {
    const r = c.raw || {};
    const m = c.method;
    if (m === "bazi" || m === "bazi_v2") {
      const p = r.pillars || {};
      const pd = r.pillar_details || [];
      const label = m === "bazi_v2" ? "【八字四柱·精算版】" : "【八字四柱】";
      const parts = [
        `${label}年${p.year} 月${p.month} 日${p.day} 时${p.hour}`,
        `日主:${r.day_master}，身强评分:${r.strength_score ?? "?"}/100`,
      ];
      for (const d of pd) {
        const hs = d.hidden_stems || [];
        parts.push(`${d.label}:${d.ganzhi}/${d.wuxing}` +
          (hs.length ? ` 藏干:${hs.join("/")}` : "") +
          (d.ten_god_stem ? ` 十神:${d.ten_god_stem}` : "") +
          (d.growth_stage ? ` 长生:${d.growth_stage}` : ""));
      }
      if (r.pattern) parts.push(`格局:${r.pattern.pattern} — ${r.pattern.description}`);
      if (r.yong_shen) parts.push(`用神分析:${r.yong_shen.rationale}`);
      if (r.yong_shen_quality) parts.push(`用神质量:${r.yong_shen_quality.score}/100 (${r.yong_shen_quality.level}) — ${r.yong_shen_quality.analysis}`);
      if (r.shensha?.summary?.notable?.length) parts.push(`关键神煞:${r.shensha.summary.notable.join("、")}`);
      if (r.element_flow?.interpretation) parts.push(`五行流转:${r.element_flow.interpretation}`);
      return parts.join("\n");
    }
    if (m === "western") {
      const pl = Object.entries(r.planets || {}).map(([n, p]) => `${n}=${(p as any).sign}${(p as any).degree?.toFixed(1)}°`).join(" ");
      const asc = r.ascendant?.sign || "?";
      const parts = [
        `【西方占星】上升:${asc}`,
        `行星:${pl}`,
        `相位:${(r.aspects || []).map((a: any) => `${a.a}${a.aspect}${a.b}(${a.orb?.toFixed(1)}°)`).join("; ")}`,
      ];
      const refs = r.calculation_basis?.references || [];
      if (refs.length) parts.push(`古籍:${refs.map((rf: any) => rf.source).join("; ")}`);
      return parts.join("\n");
    }
    if (m === "qimen") return `【奇门遁甲】${r.dun}${r.yuan}${r.ju}局 节气:${r.solar_term} 旬首:${r.xun_shou} 值符:${r.zhifu?.star}落${r.zhifu?.star_gong}`;
    if (m === "liuyao") return `【六爻】本卦:${r.ben_gua} 变卦:${r.bian_gua} 用神:${r.using_god} 依据:${r.using_god_basis}`;
    if (m === "meihua") return `【梅花】主:${r.zhu_gua}/互:${r.hu_gua}/变:${r.bian_gua} 体:${r.ti_gua}用:${r.yong_gua}`;
    if (m === "tarot") return `【塔罗·${r.spread_name||r.spread}】${(r.cards||[]).map((c:any)=>`${c.position}:${c.name}(${c.orient}) ${c.keywords||""}`).join("; ")}`;
    return `【${m}】${JSON.stringify(r).slice(0, 400)}`;
  };
  const today = new Date();
  const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;

  const SYSTEM = `你是一位融通中西的玄学解读助手。当前日期是 ${dateStr}。请严格遵守以下规则:

- 立场:传统文化象征视角,非科学预测,不替代医疗/法律/财务专业意见。
- 措辞:用"倾向、常见、容易、可留意、建议"等,禁止"注定、必然、一定、肯定会"。
- 时态:可以据盘面中的大运、流年等具体年份进行推演解读,这正是用户关心的内容。但措辞必须用"倾向、可能、容易、可留意"等推测语气。
- 结构:整体印象→性格特质→事业与方向→感情与人际→当前提示与建议(2-3条)。
- 中西合参:印证之处可加强,分歧之处如实并陈。
- 古籍引用注明出处。
- 输出格式:直接从"## 整体印象"开始,严禁任何开场白。`;

  const facts = charts.map(serialize).join("\n\n");
  const multi = charts.length > 1 ? "\n【中西合参】已提供多种术数,请中西合参。" : "";

  let enhancedFacts = "";
  if (enhancedData) {
    const enh: string[] = [];
    if (enhancedData.cross_validation) {
      const cv = enhancedData.cross_validation;
      enh.push("【交叉验证·多系统合参】");
      if (typeof cv.ensemble_score === "number") enh.push(`综合置信度:${Math.round(cv.ensemble_score)}%`);
      if (cv.overall_assessment) enh.push(`综合评估:${cv.overall_assessment}`);
    }
    if (enhancedData.peach_blossom) {
      const pb = enhancedData.peach_blossom;
      enh.push("\n【桃花指数·感情时机】");
      if (typeof pb.index === "number") enh.push(`桃花指数:${Math.round(pb.index)}/100`);
    }
    if (enhancedData.fate_modification) {
      const fm = enhancedData.fate_modification;
      enh.push("\n【改命建议·五行调理】");
      if (fm.element_balance?.advice) enh.push(`五行平衡:${fm.element_balance.advice}`);
      if (fm.daily_practices?.length) enh.push(`日常实践:${fm.daily_practices.join("；")}`);
    }
    if (enh.length > 0) enhancedFacts = "\n\n" + enh.join("\n");
  }

  const user = `求测者所问:${question || "(无)"}${multi}\n\n盘面事实(${methods.join("、")}):\n\n${facts}${enhancedFacts}\n\n直接输出解读,不要开场白。第一个字必须是"## 整体印象"。总字数不少于500字。\n\n当前日期:${dateStr}。`;
  return { system: SYSTEM, user };
}

const CRISIS_KEYWORDS = ["自杀", "自残", "轻生", "不想活", "活不下去", "想死"];

function isCrisis(q?: string) { return q ? CRISIS_KEYWORDS.some((k) => q.includes(k)) : false; }

function stripPreamble(text: string): string {
  for (const marker of ["### 整体印象", "## 整体印象", "# 整体印象"]) {
    const idx = text.indexOf(marker);
    if (idx >= 0) return text.slice(idx);
  }
  const preambles = ["好的，", "好的。", "没问题，", "请允许我", "我会遵守", "根据您的要求"];
  let t = text.trimStart();
  for (const p of preambles) {
    if (t.startsWith(p)) {
      const sep = t.indexOf("\n\n");
      if (sep > 0) return t.slice(sep + 2).trimStart();
      const dot = t.indexOf("。");
      if (dot > 0) return t.slice(dot + 1).trimStart();
      break;
    }
  }
  return text;
}

export function Interpretation({ charts, question, enhancedData }: Props) {
  const { config, hasKey } = useKeys();
  const [state, setState] = useState<InterpretState>({ text: "", loading: false, done: false, blocked: false });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    start();
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function start() {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    setState({ text: "", loading: true, done: false, blocked: false });
    setState((s) => ({ ...s, error: undefined }));
    if (isCrisis(question)) {
      setState({ text: CRISIS_FALLBACK.text, loading: false, done: true, blocked: true });
      return;
    }
    try {
      if (hasKey()) { await runLLMDirect(ctl.signal); } else { await runServerMock(ctl.signal); }
    } catch (e: any) {
      if (ctl.signal.aborted) return;
      setState((s) => ({ ...s, loading: false, error: String(e?.message || e) }));
    }
  }

  async function runLLMDirect(signal: AbortSignal) {
    const { system, user } = buildPromptFromCharts(charts, question, enhancedData);
    let buf = "";
    try {
      for await (const delta of streamChat(config, [
        { role: "system", content: system }, { role: "user", content: user },
      ], signal)) {
        if (signal.aborted) return;
        buf += delta;
        setState((s) => ({ ...s, text: buf, loading: true }));
      }
      setState((s) => ({ ...s, text: buf + "\n\n(" + DISCLAIMER + ")", loading: false, done: true }));
    } catch (e: any) {
      if (signal.aborted) return;
      setState((s) => ({ ...s, error: `直连失败(${e?.message || e}),已切换到 mock` }));
      await runServerMock(signal);
    }
  }

  async function runServerMock(signal: AbortSignal) {
    try {
      for await (const ev of streamInterpret({ charts, question, client: "mock", enhancedData }, signal)) {
        if (signal.aborted) return;
        if (ev.type === "delta") setState((s) => ({ ...s, text: ev.text, loading: true }));
        else if (ev.type === "done") setState((s) => ({ ...s, loading: false, done: true, meta: ev.meta }));
        else if (ev.type === "error") setState((s) => ({ ...s, loading: false, error: ev.text }));
      }
    } catch (e: any) {
      if (signal.aborted) return;
      setState((s) => ({ ...s, loading: false, error: String(e?.message || e) }));
    }
  }

  // 危机 block
  if (state.blocked) {
    return (
      <div className="paper-frame" style={{ borderColor: "rgba(176,58,46,0.4)" }}>
        <div className="flex items-center gap-2" style={{ marginBottom: "0.5rem" }}>
          <span style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", background: "var(--cinnabar)" }} />
          <h3 style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>危机话题转介</h3>
        </div>
        <pre className="paper-body" style={{ whiteSpace: "pre-wrap", lineHeight: 1.8 }}>{state.text}</pre>
      </div>
    );
  }

  return (
    <div className="paper-frame space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="paper-eyebrow">AI 解读</h3>
          {state.loading && <span className="paper-pulse" style={{ fontSize: "0.62rem" }}>解读生成中</span>}
          {state.done && <span style={{ fontSize: "0.62rem", color: "var(--verdigris)" }}>· 已完成</span>}
        </div>
        <button className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} onClick={start} disabled={state.loading}>
          {state.loading ? "生成中" : "重新解读"}
        </button>
      </div>

      {state.error && <div className="paper-error">{state.error}</div>}

      <div className="paper-body markdown" dangerouslySetInnerHTML={{ __html: md(stripPreamble(state.text)) }} />

      {state.meta?.softened_terms && state.meta.softened_terms.length > 0 && (
        <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>
          系统把以下绝对化用词改成了更克制的说法: {state.meta.softened_terms.map((t) => `"${t}"`).join("、")}
        </div>
      )}

      <div className="paper-hr" />
      <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", lineHeight: 1.7 }}>
        {DISCLAIMER}
      </div>
    </div>
  );
}
