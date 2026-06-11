/** MeihuaPage v2 — 梅花易数专页（最轻量）
 *  默认此刻起卦，可改任意时刻，进页即排
 */
import { type FormEvent, useState, useCallback, useEffect } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";

export function MeihuaPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("meihua"));

  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("time_qigua"); // 默认时间起卦
  const [seed, setSeed] = useState("");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 进页即排
  useEffect(() => { if (!chart) setMode("time_qigua"); }, []);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = birthStore.toApiBirth();
      const result = await computeChart({
        method: "meihua", birth: b,
        options: { mode, question: question || "问事", seed: seed || undefined },
      });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [question, mode, seed, birthStore]);

  const r = chart?.raw;

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
          placeholder={lang === "zh" ? "一事一问。默认以此刻时间起卦。" : "Defaults to current time."} />
        <div className="flex gap-1.5 flex-wrap">
          {[{ value: "time_qigua", label: lang === "zh" ? "时间起卦" : "Time" }, { value: "number_qigua", label: lang === "zh" ? "数字起卦" : "Number" }].map((m) => (
            <button key={m.value} type="button" onClick={() => setMode(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>{m.label}</button>
          ))}
        </div>
        {mode === "number_qigua" && (
          <input className="paper-input" style={{ maxWidth: 200 }} value={seed}
            onChange={(e) => setSeed(e.target.value)} placeholder={lang === "zh" ? "输入 3 个数字" : "3 numbers"} />
        )}
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "起卦中…" : "Casting…") : (lang === "zh" ? "起梅花卦" : "Cast Mei Hua")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <div className="flex items-center justify-between mb-3">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {r?.hexagram_name || (lang === "zh" ? "本卦" : "Hexagram")}
              </h2>
              {r?.tiyong && <span className="paper-tag">{r.tiyong}</span>}
            </div>
            {(r?.trigrams || []).length > 0 ? (
              <div className="grid grid-cols-3 gap-3">
                {(r?.trigrams || []).map((t: any, i: number) => (
                  <div key={i} className="text-center p-3 rounded-sm" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)" }}>
                    <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{t.role || ["主卦", "互卦", "变卦"][i]}</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{t.name || t.hexagram || ""}</div>
                    <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{t.upper_trigram || ""} / {t.lower_trigram || ""}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "0.8rem", color: "var(--ink)", textAlign: "center" }}>{r?.bagua_sequence || ""}</div>
            )}
          </section>
          <ChartFooter chart={chart} method="meihua" inBasket={inBasket}
            onBasket={() => basketAdd({ method: "meihua", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function ChartFooter({ chart, inBasket, onBasket, onReset }: any) {
  const { lang } = useI18n();
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
      <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>engine: {chart.engine} · {chart.elapsed_ms}ms</div>
      <div className="flex gap-2">
        <button type="button" className="paper-btn-ghost" onClick={onBasket} disabled={inBasket} style={{ fontSize: "0.78rem" }}>
          {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
        </button>
        <button type="button" className="paper-btn" onClick={onReset} style={{ fontSize: "0.78rem" }}>{lang === "zh" ? "重新起卦" : "Recast"}</button>
      </div>
    </div>
  );
}
