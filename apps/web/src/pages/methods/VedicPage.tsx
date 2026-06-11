/** VedicPage v2 — 吠陀占星专页
 *  闭环：生辰+地点 → 27 宿 → Nakshatra 盘面
 */
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";

const MODES = [
  { value: "natal", labelZh: "本命盘", labelEn: "Natal" },
  { value: "dasha", labelZh: "大运", labelEn: "Dasha" },
];

export function VedicPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("vedic"));
  const b = birthStore.birth;

  const [year, setYear] = useState(b.year);
  const [month, setMonth] = useState(b.month);
  const [day, setDay] = useState(b.day);
  const [hour, setHour] = useState(b.hour);
  const [minute, setMinute] = useState(b.minute);
  const [gender, setGender] = useState<"male" | "female" | "unspecified">(b.gender);
  const [mode, setMode] = useState("natal");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    birthStore.setBirth({ year, month, day, hour, minute, gender });
    try {
      const birth: Birth = { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz };
      const result = await computeChart({ method: "vedic", birth, options: { mode } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [year, month, day, hour, minute, gender, mode, b, birthStore]);

  const r = chart?.raw;
  const planets = r?.planets || [];
  const nakshatras = r?.nakshatras || [];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "吠陀占星" : "Vedic Astrology"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "27 宿体系。计算天顶/上升，月宿为纲。印度占星，重业力与时段。" : "27 Nakshatras. Sidereal zodiac. Moon mansion focus."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "命主信息" : "Birth Info"}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <F label={lang === "zh" ? "年" : "Year"}><input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "月" : "Mon"}><input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 0)} min={1} max={12} /></F>
          <F label={lang === "zh" ? "日" : "Day"}><input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value) || 0)} min={1} max={31} /></F>
          <F label={lang === "zh" ? "时" : "Hr"}><input className="paper-input" type="number" value={hour} onChange={(e) => setHour(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "分" : "Min"}><input className="paper-input" type="number" value={minute} onChange={(e) => setMinute(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "性别" : "Sex"}>
            <select className="paper-input" value={gender} onChange={(e) => setGender(e.target.value as any)}>
              <option value="male">{lang === "zh" ? "男" : "M"}</option>
              <option value="female">{lang === "zh" ? "女" : "F"}</option>
            </select>
          </F>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {MODES.map((m) => (
            <button key={m.value} type="button" onClick={() => setMode(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>
              {lang === "zh" ? m.labelZh : m.labelEn}
            </button>
          ))}
        </div>
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "排盘中…" : "Casting…") : (lang === "zh" ? "排吠陀盘" : "Cast Vedic")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 行星表 */}
          <section className="paper-frame">
            <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.8rem" }}>
              {lang === "zh" ? "行星落座" : "Planets"} · {r?.lagna ? `${lang === "zh" ? "上升" : "Lagna"}: ${r.lagna}` : ""}
            </h2>
            {planets.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {planets.map((p: any, i: number) => (
                  <div key={i} className="p-2 rounded-sm" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)", fontSize: "0.7rem" }}>
                    <span style={{ fontWeight: 600, color: "var(--ink)" }}>{p.name || p.planet}</span>
                    <span style={{ color: "var(--ink-soft)", marginLeft: "0.4rem" }}>{p.sign || p.rashi || ""}</span>
                    {p.nakshatra && <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{p.nakshatra} pada {p.pada}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="paper-empty">{lang === "zh" ? "行星数据载入中…" : "Loading planets…"}</div>
            )}
          </section>

          {/* 27 宿 */}
          {nakshatras.length > 0 && (
            <section className="paper-frame">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.8rem" }}>
                {lang === "zh" ? "月宿" : "Nakshatra"}: {r?.moon_nakshatra || ""}
              </h2>
              <div className="grid grid-cols-3 sm:grid-cols-9 gap-1">
                {nakshatras.slice(0, 27).map((n: any, i: number) => (
                  <div key={i} className="text-center p-1 rounded-sm" style={{ border: "1px solid var(--rule)", fontSize: "0.55rem", color: n.name === r?.moon_nakshatra ? "var(--cinnabar)" : "var(--ink-soft)" }}>
                    {n.name || n.nakshatra}
                  </div>
                ))}
              </div>
            </section>
          )}

          <ChartFooter chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({ method: "vedic", chart, birth: { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz }, addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }

function ChartFooter({ chart, inBasket, onBasket, onReset }: any) {
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
    </div>
  );
}
