/** ChengguPage v2 — 称骨专页（全页最简，30 秒体验）
 *  一杆秤：年/月/日/时四个秤砣 → 总骨重 → 歌诀竖排
 */
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

export function ChengguPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("chenggu"));
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

  const { getStyle } = useStaggeredReveal(4, { interval: 100, initialDelay: 0 });

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    birthStore.setBirth({ year, month, day, hour, minute, gender });
    try {
      const birth = { year, month, day, hour, minute, gender, calendar: "gregorian" as const, lat: null, lng: null, tz: "Asia/Shanghai", is_leap_month: false };
      const result = await computeChart({ method: "chenggu", birth, options: { mode: "traditional_weight" } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [year, month, day, hour, minute, gender, birthStore]);

  const r = chart?.raw;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "称骨算命" : "Bone Weighing"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "一杆秤，四个秤砣，30 秒知命重。年/月/日/时各秤一次，合为总骨重。" : "Four weights, 30 seconds to know your destiny weight."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "命主信息" : "Birth Info"}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <F label={lang === "zh" ? "年" : "Year"}><input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "月" : "Mon"}><input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 0)} min={1} max={12} /></F>
          <F label={lang === "zh" ? "日" : "Day"}><input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value) || 0)} min={1} max={31} /></F>
          <F label={lang === "zh" ? "时" : "Hr"}><input className="paper-input" type="number" value={hour} onChange={(e) => setHour(parseInt(e.target.value) || 0)} min={0} max={23} /></F>
          <F label={lang === "zh" ? "分" : "Min"}><input className="paper-input" type="number" value={minute} onChange={(e) => setMinute(parseInt(e.target.value) || 0)} /></F>
          <F label={lang === "zh" ? "性别" : "Sex"}>
            <select className="paper-input" value={gender} onChange={(e) => setGender(e.target.value as any)}>
              <option value="male">{lang === "zh" ? "男" : "M"}</option>
              <option value="female">{lang === "zh" ? "女" : "F"}</option>
            </select>
          </F>
        </div>
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "称骨中…" : "Weighing…") : (lang === "zh" ? "称骨算" : "Weigh Bones")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 秤砣挂上动画 — 四个重量 */}
          <section className="paper-frame">
            <div className="grid grid-cols-4 gap-3 text-center">
              {[
                { label: lang === "zh" ? "年" : "Year", w: r?.weight_year },
                { label: lang === "zh" ? "月" : "Month", w: r?.weight_month },
                { label: lang === "zh" ? "日" : "Day", w: r?.weight_day },
                { label: lang === "zh" ? "时" : "Hour", w: r?.weight_hour },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-sm animate-fade-in" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)", ...getStyle(i) }}>
                  <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{item.label}</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>
                    {item.w || "—"}
                  </div>
                  <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>{lang === "zh" ? "钱" : "qian"}</div>
                </div>
              ))}
            </div>
          </section>

          {/* 总骨重 + 歌诀 */}
          <section className="paper-frame" style={{ textAlign: "center", borderColor: "var(--cinnabar)", borderWidth: "1.5px" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--ink-soft)", marginBottom: "0.3rem" }}>
              {lang === "zh" ? "总骨重" : "Total Weight"}
            </div>
            <div style={{ fontSize: "3rem", fontWeight: 700, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>
              {r?.total_weight || "—"}
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{lang === "zh" ? "两" : "liang"}</div>
            {r?.ballad && (
              <div style={{
                marginTop: "1.5rem",
                fontSize: "0.9rem",
                color: "var(--ink)",
                fontFamily: "'Noto Serif SC', serif",
                lineHeight: 2,
                writingMode: lang === "zh" ? "vertical-rl" : "horizontal-tb",
                maxHeight: lang === "zh" ? 400 : "auto",
                margin: "1.5rem auto 0",
              }}>
                {r.ballad}
              </div>
            )}
          </section>

          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>engine: {chart.engine}</div>
            <div className="flex gap-2">
              <button type="button" className="paper-btn-ghost" onClick={() => basketAdd({ method: "chenggu", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() })} disabled={inBasket} style={{ fontSize: "0.78rem" }}>
                {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" className="paper-btn" onClick={() => setChart(null)} style={{ fontSize: "0.78rem" }}>{lang === "zh" ? "重新称骨" : "Re-weigh"}</button>
            </div>
          </div>
        </div>
      )}
      <MethodSourcesPanel method="chenggu" />
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }
