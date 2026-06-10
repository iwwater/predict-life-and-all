// 结果页:「古籍×仪器」纸墨风格 — 左侧盘面 + 右侧解读
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Birth, ChartResult, Method } from "../lib/types";
import type { CrossValidationResult, PeachBlossomResult, FateModificationPlan } from "../lib/api";
import { ChartRenderer } from "../components/charts";
import { Interpretation } from "../components/Interpretation";
import { BaziKline } from "../components/BaziKline";
import { Jargon } from "../components/Jargon";
import { SchoolChip, EmptyBox } from "../components/ui";
import { METHOD_PLAIN } from "../lib/method-info";
import { useHistory, type Reflection, type ReflectionVerdict } from "../store/history";
import { buildShareCard, shareCardToText, type ShareCard } from "../lib/share";
import { useI18n } from "../lib/i18n";
import { useBasket } from "../store/basket";
import { ResultSample } from "./ResultSample";

interface ResultState {
  birth?: Birth;
  question?: string;
  charts: Record<string, ChartResult>;
  methods: Method[];
  enhancedData?: {
    cross_validation?: CrossValidationResult;
    peach_blossom?: PeachBlossomResult;
    relationship_timing?: any;
    fate_modification?: FateModificationPlan;
  };
}

export function Result() {
  const { t, lang } = useI18n();
  const REFLECT_CHOICES: { v: ReflectionVerdict; label: string; color: string }[] = [
    { v: "accurate",   label: lang === "zh" ? "准" : "Yes",     color: "var(--verdigris)" },
    { v: "inaccurate", label: lang === "zh" ? "不准" : "No",   color: "var(--cinnabar)" },
    { v: "pending",    label: lang === "zh" ? "待观察" : "Maybe", color: "var(--ink-soft)" },
  ];
  const [data, setData] = useState<ResultState | null>(null);
  const [hid, setHid] = useState<string | null>(null);
  const [active, setActive] = useState<Method | "all">("all");
  const [share, setShare] = useState<ShareCard | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("mystic:result");
    if (!raw) return;
    try {
      const d = JSON.parse(raw);
      setData(d);
      setActive(d.methods?.[0] || "all");
    } catch { /* noop */ }
    setHid(sessionStorage.getItem("mystic:result_id"));
  }, []);

  const entry = useHistory((s) => (hid ? s.items.find((i) => i.id === hid) : undefined));
  const toggleFavorite = useHistory((s) => s.toggleFavorite);
  const setReflection = useHistory((s) => s.setReflection);

  const reflectionVerdict = entry?.reflection?.verdict;
  const basketAdd = useBasket((s) => s.add);
  const basketHas = useBasket((s) => s.has);
  const inBasket = data ? data.methods.some((m) => basketHas(m)) : false;

  const showChart = useMemo(() => {
    if (!data) return null;
    if (active === "all") {
      const first = data.methods.map((m) => data.charts[m]).filter(Boolean)[0];
      return first || null;
    }
    return data.charts[active as string] || null;
  }, [data, active]);

  if (!data || data.methods.length === 0) {
    return <ResultSample />;
  }

  const chartList = data.methods.map((m) => data.charts[m]).filter(Boolean);

  function openShare() {
    if (!entry) return;
    setShare(buildShareCard(entry));
    setCopied(false);
  }

  function pickReflection(v: ReflectionVerdict) {
    if (!entry) return;
    const next: Reflection | null = entry.reflection?.verdict === v
      ? null
      : { verdict: v, at: Date.now() };
    setReflection(entry.id, next);
  }

  function addAllToBasket() {
    if (!data) return;
    for (const m of data.methods) {
      basketAdd({ method: m, chart: data.charts[m] || null, birth: data.birth || null, addedAt: Date.now() });
    }
  }

  async function copyShare() {
    if (!share) return;
    const text = shareCardToText(share);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      window.prompt("复制以下文本:", text);
    }
  }

  return (
    <div className="space-y-4">
      {/* 命主信息栏 */}
      <div className="paper-grid-cell flex flex-wrap items-center justify-between gap-3" style={{ padding: "0.6rem 1rem" }}>
        <div className="flex items-center gap-3 flex-wrap" style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.83rem" }}>
          <span style={{ color: "var(--ink-soft)" }}>命主</span>
          <span style={{ color: "var(--ink)", fontFamily: "'JetBrains Mono', monospace" }}>
            {data.birth?.year}-{data.birth?.month}-{data.birth?.day} {String(data.birth?.hour).padStart(2, "0")}:{String(data.birth?.minute).padStart(2, "0")}
          </span>
          <span style={{ color: "var(--ink-soft)" }}>· {data.birth?.gender}</span>
          {data.question && <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>「{data.question}」</span>}
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            className="paper-btn-ghost"
            style={{ fontSize: "0.72rem", padding: "0.25rem 0.55rem" }}
            onClick={() => entry && toggleFavorite(entry.id)}
            disabled={!entry}
          >
            {entry?.favorite ? t("result.favorited") : t("result.favorite")}
          </button>
          {REFLECT_CHOICES.map((c) => {
            const on = reflectionVerdict === c.v;
            return (
              <button
                key={c.v}
                className="paper-btn-ghost"
                style={{
                  fontSize: "0.72rem", padding: "0.25rem 0.5rem",
                  color: on ? c.color : undefined,
                  borderColor: on ? c.color : undefined,
                }}
                onClick={() => pickReflection(c.v)}
                disabled={!entry}
              >
                {c.label}
              </button>
            );
          })}
          <button className="paper-btn-ghost" style={{ fontSize: "0.72rem", padding: "0.25rem 0.55rem" }} onClick={openShare} disabled={!entry}>
            {t("result.share")}
          </button>
          <Link to="/cast" className="paper-btn-ghost" style={{ fontSize: "0.72rem", padding: "0.25rem 0.55rem" }}>
            {t("result.cast.again")}
          </Link>
          <button className="paper-btn-ghost" style={{ fontSize: "0.72rem", padding: "0.25rem 0.55rem", color: inBasket ? "var(--verdigris)" : undefined }} onClick={addAllToBasket}>
            {inBasket ? t("basket.added") : t("basket.add")}
          </button>
        </div>
      </div>

      {/* 术数 Tab */}
      <div className="flex flex-wrap gap-1">
        {data.methods.map((m) => {
          const c = data.charts[m];
          const plain = METHOD_PLAIN[m];
          const isActive = active === m;
          return (
            <button key={m} onClick={() => setActive(m)}
              className="paper-tag"
              style={{
                cursor: "pointer",
                color: isActive ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: isActive ? "var(--cinnabar)" : "var(--rule)",
                background: isActive ? "rgba(176,58,46,0.04)" : "var(--paper)",
              }}>
              {methodLabel(m)}
              {c?.school && <span style={{ opacity: 0.6 }}>· {c.school === "east" ? "东" : "西"}</span>}
              {plain?.tagline && (
                <span className="hidden sm:inline" style={{ opacity: 0.6 }}>· {plain.tagline}</span>
              )}
            </button>
          );
        })}
      </div>

      <div className="paper-hr" />

      <div className="paper-main-grid">
        {/* 左:盘面 */}
        <div className="space-y-4 min-w-0">
          {showChart ? (
            <>
              <ChartRenderer
                chart={showChart}
                crossValidation={data.enhancedData?.cross_validation ?? null}
                peachBlossom={data.enhancedData?.peach_blossom ?? null}
                fateModification={data.enhancedData?.fate_modification ?? null}
              />
              <CalculationBasis chart={showChart} />
            </>
          ) : <EmptyBox>{lang === "zh" ? "盘面数据丢失" : "Chart data lost"}</EmptyBox>}
          {data.charts.bazi && data.charts.bazi.method === "bazi" && (
            <BaziKline chart={data.charts.bazi} />
          )}
        </div>

        {/* 右:解读 */}
        <div className="space-y-4 min-w-0">
          <Interpretation
            charts={chartList}
            question={data.question || ""}
            enhancedData={data.enhancedData ?? undefined}
          />
        </div>
      </div>

      {share && <ShareCardModal card={share} copied={copied} onClose={() => setShare(null)} onCopy={copyShare} />}
    </div>
  );
}

function methodLabel(m: Method) {
  return ({
    bazi: "八字", bazi_v2: "八字·精算", ziwei: "紫微", qimen: "奇门",
    liuyao: "六爻", meihua: "梅花", chenggu: "称骨",
    bazhai: "八宅", xuankong: "玄空",
    western: "西方占星", vedic: "吠陀",
    tarot: "塔罗", numerology: "数字命理",
    lenormand: "雷诺曼", liuren: "大六壬", tieban: "铁板神数", xiaoliuren: "小六壬",
    cross_validator: "交叉验证", hour_calibrator: "时辰校准", compatibility: "合婚",
  } as Record<Method, string>)[m] || m;
}

function CalculationBasis({ chart }: { chart: ChartResult }) {
  const { t } = useI18n();
  const basis = chart.raw?.calculation_basis;
  if (!basis) return null;
  const limits: string[] = Array.isArray(basis.limits) ? basis.limits : [];
  return (
    <div className="paper-grid-cell" style={{ padding: "0.7rem 0.9rem", fontSize: "0.75rem", lineHeight: 1.6, color: "var(--ink-soft)" }}>
      <div className="flex items-center gap-2 flex-wrap" style={{ marginBottom: "0.3rem" }}>
        <span style={{ fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{t("result.basis.title")}</span>
        {basis.rule_version && (
          <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>
            v{basis.rule_version}
          </span>
        )}
        {chart.method === "ziwei" && chart.raw?.fallback && (
          <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>
            fallback
          </span>
        )}
      </div>
      <div>方法: {basis.method || chart.method} · 模式: {basis.mode || chart.raw?.mode || "默认"}</div>
      {basis.input_source && <div>输入: {basis.input_source}</div>}
      {basis.rule && <div>规则: {basis.rule}</div>}
      {basis.scope && <div>范围: {basis.scope}</div>}
      {basis.calendar_source && <div>历法来源: {basis.calendar_source}</div>}
      {basis.draw_rule && <div>抽牌规则: {basis.draw_rule}</div>}
      {basis.period_rule && <div>元运: {basis.period_rule}</div>}
      {basis.sitting_rule && <div>坐向: {basis.sitting_rule}</div>}
      {limits.length > 0 && (
        <details style={{ marginTop: "0.3rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>
            不可判断范围 ({limits.length})
          </summary>
          <ul style={{ marginTop: "0.3rem", paddingLeft: "1.2rem", listStyle: "disc" }}>
            {limits.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </details>
      )}
      <MethodExtras chart={chart} />
    </div>
  );
}

// 各法专项 — 保持逻辑,更新样式
function MethodExtras({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const cs = "var(--ink-soft)";
  const ca = "var(--cinnabar)";
  const cv = "var(--verdigris)";
  const ci = "var(--ink)";
  const lb = "rgba(201,191,169,0.3)";

  if (chart.method === "bazi" || chart.method === "bazi_v2") {
    const score = r.strength_score;
    const cl = r.current_luck || {};
    const ai = r.annual_interactions || {};
    const ls = r.life_stage || {};
    const isV2 = chart.method === "bazi_v2";
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-2">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>
          {isV2 ? "八字精算 · 格局/用神/神煞/身强/大运/流年" : "八字专项 · 身强 / 当前大运 / 流年"}
        </div>
        {isV2 && r.pattern && (
          <div>格局: <span style={{ color: ca }}>{r.pattern.pattern}</span></div>
        )}
        {isV2 && r.yong_shen && (
          <div>用神: <span style={{ color: cv }}>{r.yong_shen.rationale}</span></div>
        )}
        {isV2 && typeof r.yong_shen_quality?.score === "number" && (
          <div>用神质量: <span style={{ color: ci }}>{r.yong_shen_quality.score}/100 ({r.yong_shen_quality.level})</span></div>
        )}
        {isV2 && r.shensha?.summary?.notable?.length > 0 && (
          <div>关键神煞: <span style={{ color: ca }}>{r.shensha.summary.notable.join("、")}</span></div>
        )}
        {typeof score === "number" && (
          <div>日主身强评分: <span style={{ color: ci }}>{score}</span> / 100</div>
        )}
        {cl.decade_ganzhi && (
          <div>当前大运: <span style={{ color: ci }}>{cl.decade_ganzhi}</span> ({cl.decade_from}-{cl.decade_to}, 虚岁 {cl.age})</div>
        )}
        {cl.annual_label && <div>流年: <span style={{ color: ci }}>{cl.annual_label}</span></div>}
        {Array.isArray(ai.interactions) && ai.interactions.length > 0 && (
          <div>
            <div>流年 {ai.ganzhi} 与原局互动:</div>
            <ul className="list-disc pl-5 space-y-0.5">
              {ai.interactions.map((it: any, i: number) => (
                <li key={i}>{it.note} <span style={{ opacity: 0.7 }}>({it.kind_zh})</span></li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (chart.method === "ziwei") {
    const periods = ["decadal", "yearly", "monthly", "daily", "hourly"] as const;
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-2">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>紫微专项 · 12 宫 + 限运四化</div>
        {periods.map((p) => {
          const item = r.horoscope?.[p];
          if (!item) return null;
          const scope = p === "decadal" ? "大限" : p === "yearly" ? "流年" : p === "monthly" ? "流月" : p === "daily" ? "流日" : "流时";
          return (
            <div key={p} style={{ fontSize: "0.73rem" }}>
              <span style={{ opacity: 0.7 }}>{scope}:</span>{" "}
              <span style={{ color: ci }}>{item.ganzhi}</span>
              {Array.isArray(item.mutagen) && item.mutagen.length === 4 && (
                <span style={{ color: ca }}> 四化: {item.mutagen.join(" / ")}</span>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  if (chart.method === "tarot") {
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-1">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>塔罗专项</div>
        {Array.isArray(r.cards) && r.cards.map((c: any, i: number) => (
          <div key={i} style={{ fontSize: "0.73rem" }}>
            <span style={{ color: ca }}>{c.position}</span>{" "}
            <span style={{ color: ci }}>{c.name}</span>{" "}
            <span style={{ opacity: 0.7 }}>{c.orient}</span>
          </div>
        ))}
      </div>
    );
  }

  if (chart.method === "liuyao") {
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-1">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>六爻专项</div>
        {r.using_god && <div>用神: <span style={{ color: ci }}>{r.using_god}</span></div>}
      </div>
    );
  }

  if (chart.method === "qimen") {
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-1">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>奇门专项 · 旬首/拆补</div>
        {r.xun_shou && <div>旬首: {r.xun_shou}</div>}
      </div>
    );
  }

  if (chart.method === "xuankong") {
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-1">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>玄空专项</div>
        <div style={{ fontSize: "0.7rem" }}>坐山 {r.sitting} 合法: {String(r.sitting_valid)} · 向山 {r.facing} 合法: {String(r.facing_valid)}</div>
      </div>
    );
  }

  if (chart.method === "meihua") {
    return (
      <div style={{ marginTop: "0.6rem", paddingTop: "0.5rem", borderTop: `1px solid ${lb}` }} className="space-y-1">
        <div style={{ fontWeight: 600, color: ca, fontFamily: "'Noto Serif SC', serif" }}>梅花专项 · 八卦五行</div>
        {r.trigram_table && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5" style={{ fontSize: "0.68rem" }}>
            {Object.entries(r.trigram_table).map(([name, t]: [string, any]) => (
              <div key={name} className="paper-grid-cell" style={{ padding: "0.3rem 0.4rem" }}>
                <div style={{ color: ci }}>{name} · {t.wuxing}</div>
                <div style={{ opacity: 0.7 }}>{t.nature}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return null;
}

function ShareCardModal({ card, copied, onClose, onCopy }: {
  card: ShareCard; copied: boolean; onClose: () => void; onCopy: () => void;
}) {
  const { t, lang } = useI18n();
  return (
    <div
      role="dialog" aria-modal="true" aria-label={t("result.share")}
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" }}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="paper-frame"
        style={{ maxWidth: 480, width: "100%", maxHeight: "85vh", overflow: "auto" }}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="paper-title" style={{ borderBottom: "none", paddingBottom: 0 }}>
            <span className="stamp" />{t("result.share")}
          </h3>
          <button className="paper-btn-ghost" onClick={onClose} style={{ fontSize: "0.72rem" }}>{t("action.close")}</button>
        </div>
        <div style={{ fontWeight: 600, color: "var(--ink)", marginBottom: "0.3rem", fontFamily: "'Noto Serif SC', serif" }}>{card.title}</div>
        <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginBottom: "0.5rem" }}>{t("result.basis.method")}: {card.methods.join(" / ")}</div>
        <div className="paper-body" style={{ marginBottom: "0.6rem" }}>{card.summary}</div>
        {card.suggestions.length > 0 && (
          <div style={{ marginBottom: "0.6rem" }}>
            <div style={{ fontWeight: 600, color: "var(--cinnabar)", fontSize: "0.78rem" }}>建议</div>
            <ol style={{ fontSize: "0.78rem", color: "var(--ink-soft)", paddingLeft: "1.2rem" }}>
              {card.suggestions.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          </div>
        )}
        <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginBottom: "0.6rem" }}>{card.footer}</div>
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button className="paper-btn" onClick={onCopy} style={{ fontSize: "0.78rem" }}>
            {copied ? "已复制" : "复制全文"}
          </button>
        </div>
      </div>
    </div>
  );
}
