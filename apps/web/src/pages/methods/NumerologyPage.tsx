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
        <F label={`${lang === "zh" ? "英文/拼音姓名" : "Name (latin)"} (${lang === "zh" ? "命运数与灵魂驱策必需" : "for destiny & soul urge"})`}>
          <input className="paper-input" style={{ maxWidth: 260 }} value={name} onChange={(e) => setName(e.target.value)} placeholder={lang === "zh" ? "如 Zhang San" : "e.g. Zhang San"} />
        </F>
        {mode !== "life_path" && !name.trim() && (
          <p style={{ fontSize: "0.72rem", color: "var(--cinnabar)" }}>
            {lang === "zh" ? "该模式需要填写英文/拼音姓名。" : "This mode needs a latin name."}
          </p>
        )}
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
          {/* 主数字 */}
          <section className="paper-frame" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--ink-soft)", marginBottom: "0.4rem" }}>
              {r?.primary?.label ?? (lang === "zh" ? MODES.find((m) => m.value === mode)?.labelZh : MODES.find((m) => m.value === mode)?.labelEn)}
            </div>
            <div style={{ fontSize: "4rem", fontWeight: 700, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif", lineHeight: 1 }}>
              {r?.primary?.number ?? "—"}
            </div>
            {r?.primary?.meaning && (
              <div style={{ fontSize: "0.9rem", color: "var(--ink)", marginTop: "0.5rem", fontFamily: "'Noto Serif SC', serif" }}>
                {r.primary.meaning}
              </div>
            )}
            {r?.primary?.is_master && (
              <div style={{ fontSize: "0.75rem", color: "var(--verdigris)", marginTop: "0.35rem" }}>
                {lang === "zh" ? "大师数 · 不归约" : "Master Number"}
              </div>
            )}
            {r?.primary?.calculation_basis && (
              <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)", marginTop: "0.5rem" }}>
                {r.primary.calculation_basis}
              </div>
            )}
          </section>

          {/* 三个数字对照 */}
          <section className="paper-frame">
            <h2 className="paper-eyebrow">{lang === "zh" ? "三数对照" : "Three Numbers"}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {[
                { key: "life_path", labelZh: "生命灵数", labelEn: "Life Path" },
                { key: "destiny", labelZh: "命运数", labelEn: "Destiny" },
                { key: "soul_urge", labelZh: "灵魂驱策", labelEn: "Soul Urge" },
              ].map((m) => {
                const v = (r as any)?.[m.key];
                return (
                  <div key={m.key} className="text-center p-2 rounded-sm"
                    style={{ border: `1px solid ${r?.primary?.label === (lang === "zh" ? m.labelZh : m.labelEn) ? "var(--cinnabar)" : "var(--rule)"}`, background: "var(--paper-2)" }}>
                    <div style={{ fontSize: "0.66rem", color: "var(--ink-soft)" }}>{lang === "zh" ? m.labelZh : m.labelEn}</div>
                    <div style={{ fontSize: "1.4rem", fontWeight: 600, color: v ? "var(--ink)" : "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
                      {v?.number ?? "—"}
                    </div>
                    <div style={{ fontSize: "0.66rem", color: "var(--ink-soft)", minHeight: "1.1em" }}>{v?.meaning ?? (m.key === "life_path" ? "" : lang === "zh" ? "需英文姓名" : "needs latin name")}</div>
                  </div>
                );
              })}
            </div>
            {r?.备注 && (
              <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.5rem" }}>{r.备注}</p>
            )}
          </section>

          {/* 综合解读 + 文献 */}
          {(r?.综合解读 || r?.evidence_sources) && (
            <section className="paper-frame space-y-2">
              <h2 className="paper-eyebrow">{lang === "zh" ? "综合" : "Summary"}</h2>
              {r?.综合解读 && (
                <p style={{ fontSize: "0.85rem", color: "var(--ink)", lineHeight: 1.75 }}>{r.综合解读}</p>
              )}
              {Array.isArray(r?.evidence_sources) && (
                <p style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>
                  {lang === "zh" ? "文献" : "Sources"}: {(r.evidence_sources as string[]).join(" · ")}
                </p>
              )}
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

