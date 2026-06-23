/** XiaoliurenPage v2 — 小六壬独立排盘页(月日时掌诀 / 数字掌诀)
 *  闭环:问题 → 选模式 → 输入月日时或三数 → 掐诀 → 六宫 12 格循环揭晓
 */
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG, emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { XiaoliurenChart } from "../../components/charts/XiaoliurenChart";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";

type Phase = "form" | "calculating" | "revealed";

export function XiaoliurenPage() {
  const { t, lang } = useI18n();
  const cfg = METHOD_INPUT_CONFIG.xiaoliuren;
  const [mode, setMode] = useState(cfg.defaultMode);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [day, setDay] = useState(new Date().getDate());
  const [hour, setHour] = useState(new Date().getHours());
  const [numbers, setNumbers] = useState("");
  const [question, setQuestion] = useState("");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [phase, setPhase] = useState<Phase>("form");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("xiaoliuren"));

  const isTimeMode = mode === "time_xiaoliuren";
  const { getStyle: getCellStyle } = useStaggeredReveal(12, { interval: 80 });

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null); setLoading(true); setPhase("calculating");
    try {
      const birth = isTimeMode
        ? { year: 2000, month, day, hour, minute: 0, gender: "unspecified" as const, calendar: "lunar" as const, lat: null as number | null, lng: null as number | null, tz: "Asia/Shanghai" }
        : emptyBirth();
      const result = await computeChart({
        method: "xiaoliuren", birth,
        options: { mode, question: question || "问事", seed: !isTimeMode && numbers ? numbers : undefined },
      });
      setChart(result);
      setPhase("revealed"); setLoading(false);
    } catch (err: any) {
      setError(String(err?.message || err));
      setPhase("form"); setLoading(false);
    }
  }, [isTimeMode, month, day, hour, numbers, question, mode]);

  const addToBasket = () => {
    const birth = isTimeMode
      ? { year: 2000, month, day, hour, minute: 0, gender: "unspecified" as const, calendar: "lunar" as const, lat: null as number | null, lng: null as number | null, tz: "Asia/Shanghai" }
      : emptyBirth();
    if (chart) basketAdd({ method: "xiaoliuren", chart, birth, addedAt: Date.now() });
    else basketAdd({ method: "xiaoliuren", chart: null, birth, addedAt: Date.now() });
  };
  const reset = () => { setChart(null); setPhase("form"); setError(null); };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("method.xiaoliuren.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {t("method.xiaoliuren.desc")}
        </p>
      </header>

      {(phase === "form" || phase === "calculating") && (
        <form onSubmit={submit} className="space-y-5">
          <section className="paper-frame space-y-4">
            <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
            <div>
              <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
              <div className="flex gap-1.5">{cfg.availableModes.map((m) => (
                <button key={m.value} type="button" onClick={() => setMode(m.value)} className="paper-tag"
                  style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>
                  {m.label}
                </button>
              ))}</div>
            </div>
            {isTimeMode ? (
              <div className="grid grid-cols-3 gap-3">
                <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "月(农历)" : "Month (Lunar)"}</label>
                  <input className="paper-input" type="number" min={1} max={12} value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 1)} /></div>
                <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "日(农历)" : "Day (Lunar)"}</label>
                  <input className="paper-input" type="number" min={1} max={30} value={day} onChange={(e) => setDay(parseInt(e.target.value) || 1)} /></div>
                <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "时辰" : "Hour"}</label>
                  <select className="paper-input" value={hour} onChange={(e) => setHour(parseInt(e.target.value))}>
                    {Array.from({ length: 12 }, (_, i) => {
                      const h = i * 2;
                      const names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
                      return <option key={i} value={h}>{names[i]}时 ({h}:00-{(h + 2) % 24}:00)</option>;
                    })}
                  </select>
                </div>
              </div>
            ) : (
              <div><label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{lang === "zh" ? "三数起课" : "Three Numbers"}</label>
                <input className="paper-input" style={{ maxWidth: 240 }} value={numbers} onChange={(e) => setNumbers(e.target.value)}
                  placeholder={lang === "zh" ? "输入 3 个数字,如 3 7 5 / 留空随机" : "3 numbers, e.g. 3 7 5 / leave blank for random"} /></div>
            )}
            <QuestionInput value={question} onChange={setQuestion} required placeholder={lang === "zh" ? "你要问什么事?(出行/寻物/决策...)" : "What do you want to ask? (travel/lost items/decisions...)"} />
          </section>

          {error && <div className="paper-error">{error}</div>}

          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
              {loading ? (lang === "zh" ? "掐诀中…" : "Casting…") : ""}
            </div>
            <div className="flex items-center gap-2">
              <button type="button" onClick={addToBasket} className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} disabled={inBasket}>
                {inBasket ? (lang === "zh" ? "已收入合参" : "In Docket") : (lang === "zh" ? "加入合参" : "Add to Basket")}
              </button>
              <button type="submit" disabled={loading} className="paper-btn" style={{ fontSize: "0.85rem", minWidth: 140 }}>
                {loading ? (lang === "zh" ? "掐诀中…" : "Casting…") : (lang === "zh" ? "掐小六壬" : "Cast Xiao Liu Ren")}
              </button>
            </div>
          </div>
        </form>
      )}

      {phase === "revealed" && chart && (
        <div className="space-y-5">
          <section className="animate-fade-in">
            <XiaoliurenChart chart={chart} cellReveal={getCellStyle} />
          </section>
          <section className="animate-fade-in" style={{ animationDelay: "960ms", animationDuration: "520ms", opacity: 0, animationTimingFunction: "ease-out", animationFillMode: "forwards" }}>
            <div className="paper-frame space-y-2" style={{ borderColor: "var(--cinnabar)", borderWidth: "1.5px", background: "rgba(176,58,46,0.03)" }}>
              <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>{lang === "zh" ? "求卦缘起" : "Origin"}</div>
              <p style={{ fontSize: "0.82rem", color: "var(--ink)", lineHeight: 1.7, margin: 0 }}>
                {question || (lang === "zh" ? "即时决疑" : "Quick decision")}
              </p>
            </div>
          </section>
          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              engine: {chart.engine} · {chart.elapsed_ms}ms
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={addToBasket} className="paper-btn-ghost" style={{ fontSize: "0.78rem" }} disabled={inBasket}>
                {inBasket ? (lang === "zh" ? "已收入合参" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" onClick={reset} className="paper-btn" style={{ fontSize: "0.78rem" }}>
                {lang === "zh" ? "再起一局" : "Cast Again"}
              </button>
            </div>
          </div>
        </div>
      )}

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
      <MethodSourcesPanel method="xiaoliuren" />
    </div>
  );
}
