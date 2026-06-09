// 解读面板:流式 + Markdown + 危机 block + 免责常驻
//  - 用户有 LLM Key → 走 llm-client 流式直连
//  - 用户无 Key → 走 server /api/interpret(mock) 兜底
import { useEffect, useRef, useState } from "react";
import { fetchPrompt, streamInterpret } from "../lib/api";
import { streamChat } from "../lib/llm-client";
import { md } from "../lib/markdown";
import { useKeys } from "../store/keys";
import { COLOR } from "./ui";
import type { ChartResult } from "../lib/types";

interface Props {
  charts: ChartResult[];
  question: string;
  enhancedData?: Record<string, any>;
}

interface InterpretState {
  text: string;
  loading: boolean;
  done: boolean;
  blocked: boolean;
  meta?: { softened_terms?: string[]; methods?: string[]; flags?: string[] };
  error?: string;
}

const DISCLAIMER = "以上为传统文化象征视角的参考,非科学预测,重大决定请结合现实并咨询专业人士。";

const CRISIS_FALLBACK = {
  blocked: true,
  text:
    "听起来你正承受很大的痛苦。这不是算命能回答的问题,也请不要独自承受。\n\n" +
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
      // v2 fields
      if (r.pattern) {
        parts.push(`格局:${r.pattern.pattern} — ${r.pattern.description}`);
      }
      if (r.yong_shen) {
        parts.push(`用神分析:${r.yong_shen.rationale}`);
      }
      if (r.yong_shen_quality) {
        parts.push(`用神质量:${r.yong_shen_quality.score}/100 (${r.yong_shen_quality.level}) — ${r.yong_shen_quality.analysis}`);
      }
      if (r.shensha?.summary?.notable?.length) {
        parts.push(`关键神煞:${r.shensha.summary.notable.join("、")}`);
      }
      if (r.element_flow?.interpretation) {
        parts.push(`五行流转:${r.element_flow.interpretation}`);
      }
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
    // 全量序列化其余方法
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
- 时态:可以据盘面中的大运、流年等具体年份进行推演解读,这正是用户关心的内容。但措辞必须用"倾向、可能、容易、可留意"等推测语气,禁止用"注定、必然、一定会"等绝对化表达断言某年某事。过去年份的盘面信息可作为性格形成和格局变化的背景解释。
- 结构:整体印象→性格特质→事业与方向→感情与人际→当前提示与建议(2-3条)。
- 中西合参:印证之处可加强,分歧之处如实并陈"从X法看…从Y法看…"。
- 古籍引用注明出处,只依盘面推演不杜撰。
- 输出格式:直接从"## 整体印象"开始输出解读内容。严禁任何开场白、确认语、过渡句，如"好的""请允许我""我会遵守""根据您的要求""以下是解读"等。第一个字符就是"## 整体印象"。不要复述系统规则。`;

  const facts = charts.map(serialize).join("\n\n");
  const multi = charts.length > 1 ? "\n【中西合参】已提供多种术数,请中西合参。" : "";

  // ── Enhanced data serialization ──────────────────────────────
  let enhancedFacts = "";
  if (enhancedData) {
    const enh: string[] = [];
    if (enhancedData.cross_validation) {
      const cv = enhancedData.cross_validation;
      enh.push("【交叉验证·多系统合参】");
      if (typeof cv.ensemble_score === "number") {
        enh.push(`综合置信度:${Math.round(cv.ensemble_score)}%`);
      }
      if (cv.overall_assessment) {
        enh.push(`综合评估:${cv.overall_assessment}`);
      }
      if (cv.domain_checks) {
        for (const [domain, check] of Object.entries(cv.domain_checks)) {
          const c = check as any;
          const dl: Record<string, string> = {
            self_life: "本命格局", career: "事业", wealth: "财富",
            relationship: "感情", health: "健康", timing: "时机",
          };
          const label = dl[domain] || domain;
          enh.push(`${label}:${c.assessment || c.confidence + "%一致" || JSON.stringify(c)}`);
        }
      }
    }
    if (enhancedData.peach_blossom) {
      const pb = enhancedData.peach_blossom;
      enh.push("\n【桃花指数·感情时机】");
      if (typeof pb.index === "number") enh.push(`桃花指数:${Math.round(pb.index)}/100 (${pb.level || "—"})`);
      if (pb.details?.taohua_stars?.length) enh.push(`桃花星:${pb.details.taohua_stars.join("、")}`);
      if (pb.timing) enh.push(`最佳时机:${pb.timing}`);
    }
    if (enhancedData.relationship_timing) {
      const rt = enhancedData.relationship_timing;
      if (rt.windows?.length) {
        enh.push("\n【关系时间窗口】");
        enh.push(rt.windows.map((w: any) =>
          `${w.label || w.from + "-" + w.to}:${w.significance || w.score || ""}`
        ).join("; "));
      }
    }
    if (enhancedData.fate_modification) {
      const fm = enhancedData.fate_modification;
      enh.push("\n【改命建议·五行调理】");
      if (fm.element_balance?.advice) enh.push(`五行平衡:${fm.element_balance.advice}`);
      if (fm.daily_practices?.length) enh.push(`日常实践:${fm.daily_practices.join("；")}`);
      if (fm.mutable_patterns?.length) enh.push(`可改格局:${fm.mutable_patterns.join("、")}`);
      if (fm.fixed_patterns?.length) enh.push(`定数格局:${fm.fixed_patterns.join("、")}`);
    }
    if (enh.length > 0) enhancedFacts = "\n\n" + enh.join("\n");
  }

  const user = `求测者所问:${question || "(无)"}${multi}\n\n盘面事实(${methods.join("、")}):\n\n${facts}${enhancedFacts}\n\n直接输出解读,不要开场白。第一个字必须是"## 整体印象"。可以据盘面中的大运、流年等具体年份推演,但措辞保持推测语气。总字数不少于500字。\n\n当前日期:${dateStr}。`;
  return { system: SYSTEM, user };
}

const CRISIS_KEYWORDS = ["自杀", "自残", "轻生", "不想活", "活不下去", "想死"];

function isCrisis(q?: string) {
  if (!q) return false;
  return CRISIS_KEYWORDS.some((k) => q.includes(k));
}

/** 去除 LLM 输出的开场白,从第一个 markdown 标题开始展示 */
function stripPreamble(text: string): string {
  for (const marker of ["### 整体印象", "## 整体印象", "# 整体印象"]) {
    const idx = text.indexOf(marker);
    if (idx >= 0) return text.slice(idx);
  }
  // 如果没找到标题,去掉常见的确认句
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
    // 组件挂载时自动起一次(可被按钮重起)
    start();
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function start() {
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
   setState({ text: "", loading: true, done: false, blocked: false });
    // 清掉上一轮的 error,避免 StrictMode 双调或重起时残留
    setState((s) => ({ ...s, error: undefined }));
    if (isCrisis(question)) {
      setState({ text: CRISIS_FALLBACK.text, loading: false, done: true, blocked: true });
      return;
    }
    try {
      if (hasKey()) {
        await runLLMDirect(ctl.signal);
      } else {
        await runServerMock(ctl.signal);
      }
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
        { role: "system", content: system },
        { role: "user", content: user },
      ], signal)) {
        if (signal.aborted) return;
        buf += delta;
        setState((s) => ({ ...s, text: buf, loading: true }));
      }
      setState((s) => ({ ...s, text: buf + "\n\n(" + DISCLAIMER + ")", loading: false, done: true }));
   } catch (e: any) {
      // fallback 到 server mock
      if (signal.aborted) return;
      setState((s) => ({ ...s, error: `直连失败(${e?.message || e}),已切换到 mock` }));
      await runServerMock(signal);
    }
  }

  async function runServerMock(signal: AbortSignal) {
    try {
      for await (const ev of streamInterpret({ charts, question, client: "mock", enhancedData }, signal)) {
        if (signal.aborted) return;
        if (ev.type === "delta") {
          setState((s) => ({ ...s, text: ev.text, loading: true }));
        } else if (ev.type === "done") {
          setState((s) => ({ ...s, loading: false, done: true, meta: ev.meta }));
        } else if (ev.type === "error") {
          setState((s) => ({ ...s, loading: false, error: ev.text }));
        }
      }
    } catch (e: any) {
      if (signal.aborted) return;
      setState((s) => ({ ...s, loading: false, error: String(e?.message || e) }));
    }
  }

  // 危机 block: 只显示转介,不渲染盘面/原解读
  if (state.blocked) {
    return (
      <div className="card space-y-3" style={{ borderColor: "rgba(200,85,61,0.4)" }}>
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: COLOR.danger }} />
          <h3 className="text-sm font-semibold" style={{ color: COLOR.danger }}>危机话题转介</h3>
        </div>
        <pre className="text-sm whitespace-pre-wrap font-sans" style={{ color: COLOR.ink, lineHeight: 1.75 }}>{state.text}</pre>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold" style={{ color: COLOR.goldBright }}>AI 解读</h3>
          {state.loading && <span className="text-[10px] flex items-center gap-1" style={{ color: COLOR.muted }}>
            <span className="pulse-dot" /> 解读生成中
          </span>}
          {state.done && <span className="text-[10px]" style={{ color: COLOR.ok }}>· 已完成</span>}
        </div>
        <button className="btn-ghost text-xs" onClick={start} disabled={state.loading}>
          {state.loading ? "生成中" : "重新解读"}
        </button>
      </div>

      {state.error && (
        <div className="text-xs p-2 rounded" style={{ background: "rgba(200,85,61,0.1)", color: COLOR.danger }}>
          {state.error}
        </div>
      )}

      <div className="markdown" dangerouslySetInnerHTML={{ __html: md(stripPreamble(state.text)) }} />

      {state.meta?.softened_terms && state.meta.softened_terms.length > 0 && (
        <div className="text-[10px]" style={{ color: COLOR.muted }}>
          系统把以下绝对化用词改成了更克制的说法: {state.meta.softened_terms.map((t) => `"${t}"`).join("、")}
        </div>
      )}

      <div className="divider-soft" />
      <div className="text-[10px] leading-relaxed" style={{ color: COLOR.muted }}>
        {DISCLAIMER}
      </div>
    </div>
  );
}
