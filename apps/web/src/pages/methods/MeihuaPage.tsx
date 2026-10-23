/** MeihuaPage v2 — 梅花易数专页（最轻量）
 *  默认此刻起卦，可改任意时刻，进页即排
 */
import { ChartFooter } from "../../components/ChartFooter";
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";

export function MeihuaPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("meihua"));

  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("time_qigua"); // 默认时间起卦
  const [nums, setNums] = useState(["", "", ""]); // 数字起卦: 上卦数/下卦数/动爻数(可选)
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = birthStore.toApiBirth();
      const options: Record<string, unknown> = { mode };
      if (question.trim()) options.question = question.trim();
      if (mode === "external_omen" && question.trim().length < 2) {
        throw new Error(lang === "zh" ? "外应起卦（字占）需要至少两个字的问题。" : "External omen needs ≥2 characters.");
      }
      if (mode === "number_qigua") {
        const [a, c, d] = nums.map((s) => s.trim());
        const n1 = Number(a), n2 = Number(c), n3 = d === "" ? undefined : Number(d);
        if (!Number.isInteger(n1) || !Number.isInteger(n2) || n1 < 1 || n2 < 1) {
          throw new Error(lang === "zh" ? "数字起卦需要两个正整数（上卦数、下卦数）。" : "Two positive integers required.");
        }
        options.n1 = n1; options.n2 = n2;
        if (n3 !== undefined) {
          if (!Number.isInteger(n3) || n3 < 1) throw new Error(lang === "zh" ? "动爻数须为正整数。" : "Moving line must be positive.");
          options.n3 = n3;
        }
      }
      const result = await computeChart({ method: "meihua", birth: b, options });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [question, mode, nums, birthStore, lang]);

  const r = chart?.raw;

  // 主/互/变 三卦 stagger fade-in
  const { getStyle: getTrigramStyle } = useStaggeredReveal(3, { interval: 200 });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "梅花易数" : "Plum Blossom"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "最轻量的一法。主/互/变三卦横列，体用关系一句话总断。" : "Lightest method. Main/Mutual/Changed trigrams, Ti-Yong diagnosis."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "问事" : "Question"}</h2>
        <textarea className="paper-input" style={{ minHeight: 80 }} value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={mode === "external_omen"
            ? (lang === "zh" ? "以所问之字起卦（至少两个字）。例如：钥匙在哪里" : "Cast from the question text (≥2 chars).")
            : (lang === "zh" ? "一事一问。默认以此刻时间起卦。" : "Defaults to current time.")} />
        <div className="flex gap-1.5 flex-wrap">
          {[{ value: "time_qigua", label: lang === "zh" ? "时间起卦" : "Time" }, { value: "number_qigua", label: lang === "zh" ? "数字起卦" : "Number" }, { value: "external_omen", label: lang === "zh" ? "外应起卦" : "External Omen" }].map((m) => (
            <button key={m.value} type="button" onClick={() => setMode(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>{m.label}</button>
          ))}
        </div>
        {mode === "number_qigua" && (
          <div className="flex gap-2 flex-wrap items-center">
            {["上卦数", "下卦数", "动爻数(可选)"].map((label, i) => (
              <label key={i} className="flex items-center gap-1" style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
                <span>{label}</span>
                <input className="paper-input" style={{ maxWidth: 90, minHeight: 32 }} inputMode="numeric" value={nums[i]}
                  onChange={(e) => setNums((a) => a.map((v, j) => (j === i ? e.target.value : v)))} />
              </label>
            ))}
          </div>
        )}
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "起卦中…" : "Casting…") : (lang === "zh" ? "起梅花卦" : "Cast Mei Hua")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            {(() => {
              const d = (r || {}) as Record<string, any>;
              const df = d["断法"] || {};
              const guas = [["主卦", "本卦"], ["互卦", "互卦"], ["变卦", "变卦"]]
                .map(([k, role]) => { const g = d[k] || {}; return { role, name: g.name, upper: g.upper, lower: g.lower }; })
                .filter((g) => g.name);
              const wang = (d["卦气旺衰"] || {})["本卦"] || {};
              return (
                <>
                  <div className="flex items-center justify-between mb-3 gap-2 flex-wrap">
                    <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                      {guas[0]?.name || (lang === "zh" ? "本卦" : "Hexagram")}
                    </h2>
                    <div className="flex gap-1.5 flex-wrap">
                      {(df.体卦 || df.用卦) && (
                        <span className="paper-tag" style={{ fontSize: "0.72rem" }}>
                          {lang === "zh" ? `体${df.体卦} · 用${df.用卦} · ${df.体用关系}` : `${df.体用关系}`}</span>
                      )}
                      {df.总断 && (
                        <span className="paper-tag" style={{ fontSize: "0.72rem", color: df.总断 === "吉" ? "var(--verdigris)" : df.总断 === "凶" ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: "currentColor" }}>
                          {lang === "zh" ? `总断 · ${df.总断}` : df.总断}</span>
                      )}
                    </div>
                  </div>
                  {guas.length > 0 ? (
                    <div className="grid grid-cols-3 gap-3">
                      {guas.map((g, i: number) => (
                        <div key={i} className="text-center p-3 rounded-sm animate-fade-in" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)", ...getTrigramStyle(i) }}>
                          <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>{g.role}</div>
                          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{g.name}</div>
                          <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>
                            {lang === "zh" ? `上${g.upper || "—"} · 下${g.lower || "—"}` : `${g.upper || "—"} / ${g.lower || "—"}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {d["起卦方式"] && (
                    <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.75rem", textAlign: "center" }}>{String(d["起卦方式"])}</div>
                  )}
                  {df.断语 && (
                    <div style={{ marginTop: "0.9rem", padding: "0.55rem 0.8rem", borderLeft: "3px solid var(--cinnabar)", background: "var(--paper-2)", fontSize: "0.85rem", color: "var(--ink)" }}>
                      {df.断语}
                    </div>
                  )}
                  {(df.互卦提示 || df.变卦提示 || d["综合解读"] || wang.旺衰) && (
                    <details style={{ marginTop: "0.9rem" }}>
                      <summary style={{ cursor: "pointer", fontSize: "0.75rem", color: "var(--ink-soft)" }}>{lang === "zh" ? "断卦细节" : "Details"}</summary>
                      <div className="space-y-2" style={{ marginTop: "0.6rem", fontSize: "0.78rem", color: "var(--ink)" }}>
                        {wang.旺衰 && (
                          <div>{lang === "zh"
                            ? `卦气：本卦${wang.卦}(${wang.五行})，月令${wang.月令地支}(${wang.月令五行})，${wang.状态}（系数 ${wang.系数}，${wang.旺衰}）`
                            : `Vigor: ${wang.状态} (${wang.系数})`}</div>
                        )}
                        {df.互卦提示 && <div>{df.互卦提示}</div>}
                        {df.变卦提示 && <div>{df.变卦提示}</div>}
                        {d["综合解读"] && <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{d["综合解读"]}</div>}
                      </div>
                    </details>
                  )}
                </>
              );
            })()}
          </section>
          <ChartFooter chart={chart} method="meihua" inBasket={inBasket}
            onBasket={() => basketAdd({ method: "meihua", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

