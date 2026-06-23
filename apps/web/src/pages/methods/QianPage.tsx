/** QianPage v2 — 灵签(观音/关帝)独立页
 *  闭环:问题 → 选签型 → 签枝下落动画 → 签文/解签/行动建议
 */
import { type FormEvent, useState, useCallback, type CSSProperties } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { QianChart } from "../../components/charts/QianChart";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";

type QianType = "guanyin" | "guandi";
type Phase = "form" | "shaking" | "revealed";
const STICK_ANIM_MS = 1200;
const CHECK_LABEL: CSSProperties = { fontFamily: "'Noto Serif SC', serif", fontSize: "0.78rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" };

export function QianPage() {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("qian"));

  const [question, setQuestion] = useState("");
  const [qianType, setQianType] = useState<QianType>("guanyin");
  const [manual, setManual] = useState(false);
  const [qianNumber, setQianNumber] = useState("1");
  const [fixSeed, setFixSeed] = useState(false);
  const [seed, setSeed] = useState("");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [phase, setPhase] = useState<Phase>("form");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { getStyle: getRevealStyle } = useStaggeredReveal(2, { interval: 220 });

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null); setLoading(true); setPhase("shaking");
    try {
      const result = await computeChart({
        method: "qian", birth: emptyBirth(),
        options: {
          mode: manual ? "manual_number" : "random_draw",
          qian_type: qianType,
          qian_number: manual ? Number(qianNumber) : undefined,
          seed: fixSeed && seed ? seed : undefined,
          question: question || "今日一签",
        },
      });
      setChart(result);
      // 等签枝下落动画结束再揭晓签文
      window.setTimeout(() => { setPhase("revealed"); setLoading(false); }, STICK_ANIM_MS);
    } catch (err: any) {
      setError(String(err?.message || err));
      setPhase("form"); setLoading(false);
    }
  }, [fixSeed, manual, qianNumber, qianType, question, seed]);

  const addToBasket = () => {
    if (chart) basketAdd({ method: "qian", chart, birth: emptyBirth(), addedAt: Date.now() });
  };
  const reset = () => { setChart(null); setPhase("form"); setError(null); };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{isZh ? "灵签" : "Qian Oracle"}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {isZh ? "支持观音灵签、关帝灵签;可随机抽签,也可录入实体签号。默请一签,静候签落。" : "Guanyin and Guandi qian oracle, random draw or manual number."}
        </p>
      </header>

      {(phase === "form" || phase === "shaking") && (
        <form onSubmit={submit} className="space-y-5">
          <section className="paper-frame space-y-4">
            <h2 className="paper-eyebrow">{isZh ? "起签" : "Draw"}</h2>
            <div className="flex gap-2 flex-wrap">
              {[
                { v: "guanyin" as QianType, l: isZh ? "观音灵签" : "Guanyin" },
                { v: "guandi"  as QianType, l: isZh ? "关帝灵签" : "Guandi"  },
              ].map((opt) => (
                <button key={opt.v} type="button" onClick={() => setQianType(opt.v)}
                  className="paper-tag" style={{ cursor: "pointer", color: qianType === opt.v ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: qianType === opt.v ? "var(--cinnabar)" : "var(--rule)" }}>
                  {opt.l}
                </button>
              ))}
            </div>
            <label style={CHECK_LABEL}>
              <input type="checkbox" checked={manual} onChange={(e) => setManual(e.target.checked)} />
              {isZh ? "我已有实体签号,直接录入" : "I already have a qian number"}
            </label>
            {manual ? (
              <input className="paper-input" style={{ maxWidth: 160 }} type="number" min={1} max={100} value={qianNumber} onChange={(e) => setQianNumber(e.target.value)} />
            ) : (
              <div>
                <label style={CHECK_LABEL}>
                  <input type="checkbox" checked={fixSeed} onChange={(e) => setFixSeed(e.target.checked)} />
                  {isZh ? "固定 seed(复盘可重现)" : "Lock seed"}
                </label>
                {fixSeed && <input className="paper-input" style={{ maxWidth: 160, marginTop: "0.3rem" }} value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="42" />}
              </div>
            )}
            <QuestionInput value={question} onChange={setQuestion} required={false} />
          </section>

          {error && <div className="paper-error">{error}</div>}

          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
              {loading ? (isZh ? "求签中…" : "Casting…") : ""}
            </div>
            <div className="flex items-center gap-2">
              <button type="button" onClick={addToBasket} className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} disabled={inBasket}>
                {inBasket ? (isZh ? "已收入合参" : "In Docket") : (isZh ? "加入合参" : "Add to Basket")}
              </button>
              <button type="submit" disabled={loading} className="paper-btn" style={{ fontSize: "0.85rem", minWidth: 140 }}>
                {loading ? (isZh ? "求签中…" : "Casting…") : (isZh ? "抽签" : "Draw")}
              </button>
            </div>
          </div>
        </form>
      )}

      {phase === "shaking" && (
        <section className="paper-frame" style={{ textAlign: "center", padding: "3rem 1rem" }} aria-live="polite">
          <div style={{ position: "relative", width: "5rem", height: "9rem", margin: "0 auto 1rem" }}>
            <div style={{
              position: "absolute", left: "0.6rem", right: "0.6rem", bottom: 0, height: "3.2rem",
              border: "1.5px solid var(--rule)", borderTop: "1.5px solid var(--cinnabar)",
              background: "linear-gradient(180deg, var(--paper-2), var(--paper))",
              borderRadius: "2px 2px 4px 4px", boxShadow: "inset 0 -4px 0 rgba(176,58,46,0.06)",
            }} />
            <div className="qian-stick-fall" style={{
              position: "absolute", left: "50%", top: 0, width: "0.5rem", height: "7rem", marginLeft: "-0.25rem",
              transformOrigin: "top center",
              background: "linear-gradient(180deg, var(--cinnabar) 0%, var(--cinnabar) 12%, var(--paper) 12%, var(--paper) 100%)",
              border: "1px solid var(--rule)", borderRadius: "1px",
            }} />
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif", letterSpacing: "0.18em" }}>
            {isZh ? "签枝落定中 …" : "The stick is falling …"}
          </p>
        </section>
      )}

      {phase === "revealed" && chart && (
        <div className="space-y-5">
          <section className="animate-fade-in" style={getRevealStyle(0)}>
            <QianChart chart={chart} />
          </section>
          <section className="animate-fade-in" style={getRevealStyle(1)}>
            <div className="paper-frame space-y-2" style={{ borderColor: "var(--cinnabar)", borderWidth: "1.5px", background: "rgba(176,58,46,0.03)" }}>
              <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>{isZh ? "求签缘起" : "Origin"}</div>
              <p style={{ fontSize: "0.82rem", color: "var(--ink)", lineHeight: 1.7, margin: 0 }}>
                {question || (isZh ? "今日一签" : "Today's draw")}
              </p>
            </div>
          </section>
          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              engine: {chart.engine} · {chart.elapsed_ms}ms
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={addToBasket} className="paper-btn-ghost" style={{ fontSize: "0.78rem" }} disabled={inBasket}>
                {inBasket ? (isZh ? "已收入合参" : "In Docket") : (isZh ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" onClick={reset} className="paper-btn" style={{ fontSize: "0.78rem" }}>
                {isZh ? "再求一签" : "Draw Again"}
              </button>
            </div>
          </div>
        </div>
      )}

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {isZh ? "灵签仅供传统文化参考,基础条目会在结果中标明。" : "For cultural reference only. Base catalog entries are labelled."}
      </p>
      <MethodSourcesPanel method="qian" />
    </div>
  );
}
