/** NumerologyPage v2 — 生命灵数专页（最简） */
import { ChartFooter } from "../../components/ChartFooter";
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

const MODES = [
  { value: "life_path", labelZh: "生命灵数", labelEn: "Life Path" },
  { value: "destiny", labelZh: "表达数", labelEn: "Destiny" },
  { value: "soul_urge", labelZh: "灵魂驱策", labelEn: "Soul Urge" },
];

export function NumerologyPage() {
  const { t, lang } = useI18n();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("numerology"));

  const [year, setYear] = useState(1990);
  const [month, setMonth] = useState(6);
  const [day, setDay] = useState(15);
  const [name, setName] = useState("");
  const [mode, setMode] = useState("life_path");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const birth: Birth = { year, month, day, hour: 12, minute: 0, gender: "unspecified", calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" };
      const result = await computeChart({
        method: "numerology", birth,
        options: { mode, ...(name ? { name } : {}) },
      });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [year, month, day, name, mode]);

  const r = chart?.raw;
  const baseBirth: Birth = { year, month, day, hour: 12, minute: 0, gender: "unspecified", calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "生命灵数" : "Numerology"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "生命灵数、表达数、灵魂驱策。年月日 + 名字即可。" : "Life path, destiny, soul urge numbers."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "基本信息" : "Info"}</h2>
        <div className="grid grid-cols-3 gap-3" style={{ maxWidth: 360 }}>
          <F label={lang === "zh" ? "年" : "Year"}><input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "月" : "Mon"}><input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 0)} min={1} max={12} /></F>
          <F label={lang === "zh" ? "日" : "Day"}><input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value) || 0)} min={1} max={31} /></F>
        </div>
        <F label={`${lang === "zh" ? "名字" : "Name"} (${lang === "zh" ? "可选" : "optional"})`}>
          <input className="paper-input" style={{ maxWidth: 260 }} value={name} onChange={(e) => setName(e.target.value)} placeholder={lang === "zh" ? "用于表达数/灵魂驱策" : "For destiny/soul urge"} />
        </F>
        <div className="flex gap-1.5 flex-wrap">
          {MODES.map((m) => (
            <button key={m.value} type="button" onClick={() => setMode(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>
              {lang === "zh" ? m.labelZh : m.labelEn}
            </button>
          ))}
        </div>
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "推算中…" : "Calculating…") : (lang === "zh" ? "推算灵数" : "Calculate")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--ink-soft)", marginBottom: "0.5rem" }}>
              {lang === "zh" ? MODES.find((m) => m.value === mode)?.labelZh : MODES.find((m) => m.value === mode)?.labelEn}
            </div>
            <div style={{ fontSize: "4rem", fontWeight: 700, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif", lineHeight: 1 }}>
              {r?.number ?? r?.life_path ?? r?.destiny ?? r?.soul_urge ?? "—"}
            </div>
            {r?.master_number && (
              <div style={{ fontSize: "0.8rem", color: "var(--verdigris)", marginTop: "0.5rem" }}>
                {lang === "zh" ? "大师数" : "Master Number"}: {r.master_number}
              </div>
            )}
          </section>

          {/* 衍生数字 */}
          {r?.numbers && (
            <section className="paper-frame">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {Object.entries(r.numbers as Record<string, number>).map(([k, v]) => (
                  <div key={k} className="text-center p-2 rounded-sm" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)" }}>
                    <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>{k}</div>
                    <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--ink)" }}>{v}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <ChartFooter method="numerology" recastLabel="重新推算" chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({ method: "numerology", chart, birth: baseBirth, addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }

