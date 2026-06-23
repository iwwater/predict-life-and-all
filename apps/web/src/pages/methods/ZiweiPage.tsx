/** ZiweiPage v2 — 紫微斗数专页
 *  闭环：生辰表单 → 紫微盘面 → 解读
 */
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

export function ZiweiPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("ziwei"));
  const b = birthStore.birth;

  const [year, setYear] = useState(b.year);
  const [month, setMonth] = useState(b.month);
  const [day, setDay] = useState(b.day);
  const [hour, setHour] = useState(b.hour);
  const [minute, setMinute] = useState(b.minute);
  const [gender, setGender] = useState<"male" | "female" | "unspecified">(b.gender);
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    birthStore.setBirth({ year, month, day, hour, minute, gender });
    try {
      const birth = { year, month, day, hour, minute, gender, calendar: "gregorian" as const, lat: b.lat, lng: b.lng, tz: b.tz };
      const result = await computeChart({ method: "ziwei", birth: birth as Birth, options: { mode: "natal" } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [year, month, day, hour, minute, gender, b, birthStore]);

  const r = chart?.raw;
  const palaces = r?.palaces || [];
  const { getStyle: getPalaceStyle } = useStaggeredReveal(12, { interval: 80 });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "紫微斗数" : "Zi Wei Dou Shu"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "十二宫方盘，命宫为纲。星辰分布各有深意，宫位联动见人生全貌。" : "12 Palaces chart. Life Palace is the key."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "命主信息" : "Birth Info"}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <F label={lang === "zh" ? "年" : "Year"}><input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "月" : "Month"}><input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "日" : "Day"}><input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "时" : "Hour"}><input className="paper-input" type="number" value={hour} onChange={(e) => setHour(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "分" : "Min"}><input className="paper-input" type="number" value={minute} onChange={(e) => setMinute(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "性别" : "Sex"}>
            <select className="paper-input" value={gender} onChange={(e) => setGender(e.target.value as any)}>
              <option value="male">{lang === "zh" ? "男" : "M"}</option>
              <option value="female">{lang === "zh" ? "女" : "F"}</option>
            </select>
          </F>
        </div>
        <button type="submit" className="paper-btn" disabled={loading}>{loading ? (lang === "zh" ? "排盘中…" : "Casting…") : (lang === "zh" ? "排紫微盘" : "Cast Zi Wei")}</button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <div className="flex items-center justify-between mb-3">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {lang === "zh" ? "命宫" : "Life Palace"}: {r?.ming_gong || "—"}
              </h2>
              <span className="paper-tag">{r?.ming_zhu || ""} · {r?.shen_zhu || ""}</span>
            </div>
            {palaces.length > 0 ? (
              <div className="grid grid-cols-4 gap-1.5">
                {palaces.map((p: any, i: number) => (
                  <div key={i} className="text-center p-2 rounded-sm animate-fade-in"
                    style={{ border: `1px solid ${p.name === r?.ming_gong ? "var(--cinnabar)" : "var(--rule)"}`, background: p.name === r?.ming_gong ? "rgba(176,58,46,0.06)" : "var(--paper-2)", ...getPalaceStyle(i) }}>
                    <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{p.name}</div>
                    <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{p.stars?.slice(0, 2).join(" ") || p.zhi || ""}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="paper-empty">{lang === "zh" ? "盘面数据载入中…" : "Loading chart data…"}</div>
            )}
          </section>
          <ChartFooter chart={chart} method="ziwei" inBasket={inBasket} onBasket={() => basketAdd({ method: "ziwei", chart, birth: { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz, is_leap_month: false }, addedAt: Date.now() })} onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }

function ChartFooter({ chart, method, inBasket, onBasket, onReset }: any) {
  const { lang } = useI18n();
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
      <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>engine: {chart.engine} · {chart.elapsed_ms}ms</div>
      <div className="flex gap-2">
        <button type="button" className="paper-btn-ghost" onClick={onBasket} disabled={inBasket} style={{ fontSize: "0.78rem" }}>
          {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
        </button>
        <button type="button" className="paper-btn" onClick={onReset} style={{ fontSize: "0.78rem" }}>{lang === "zh" ? "重新排盘" : "Recast"}</button>
      </div>
      <MethodSourcesPanel method="ziwei" />
    </div>
  );
}
