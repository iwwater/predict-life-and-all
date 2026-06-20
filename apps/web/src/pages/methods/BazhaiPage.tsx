/** BazhaiPage v2 — 八宅明镜专页（生辰 + 坐向）
 *  闭环：生辰/坐向表单 → 八宅盘面 → 吉凶方位
 */
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

const DIRECTIONS = ["正北", "东北", "正东", "东南", "正南", "西南", "正西", "西北"];

export function BazhaiPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("bazhai"));
  const b = birthStore.birth;

  const [year, setYear] = useState(b.year);
  const [month, setMonth] = useState(b.month);
  const [day, setDay] = useState(b.day);
  const [hour, setHour] = useState(b.hour);
  const [minute, setMinute] = useState(b.minute);
  const [gender, setGender] = useState<"male" | "female" | "unspecified">(b.gender);
  const [sittingDir, setSittingDir] = useState("正东");
  const [constructionYear, setConstructionYear] = useState(new Date().getFullYear());
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    birthStore.setBirth({ year, month, day, hour, minute, gender });
    try {
      const birth: Birth = { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz };
      const result = await computeChart({ method: "bazhai", birth, options: { mode: "home_fengshui", sitting: sittingDir, construction_year: constructionYear } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [year, month, day, hour, minute, gender, sittingDir, constructionYear, b, birthStore]);

  const r = chart?.raw;
  const directions = r?.directions || [];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "八宅明镜" : "Ba Zhai Ming Jing"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "以命卦配宅卦，分东四宅与西四宅。吉凶八方位各有定论。" : "Match life gua to house gua. East/West four house groups."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "命主 & 宅向" : "Birth & Orientation"}</h2>
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
        <div className="flex gap-3 flex-wrap items-end">
          <F label={lang === "zh" ? "坐向" : "Sitting Dir"}>
            <select className="paper-input" value={sittingDir} onChange={(e) => setSittingDir(e.target.value)}>
              {DIRECTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </F>
          <F label={lang === "zh" ? "建造年" : "Build Year"}>
            <input className="paper-input" type="number" style={{ maxWidth: 100 }} value={constructionYear} onChange={(e) => setConstructionYear(parseInt(e.target.value) || 0)} />
          </F>
        </div>
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "排盘中…" : "Casting…") : (lang === "zh" ? "排八宅盘" : "Cast Ba Zhai")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <div className="flex items-center justify-between mb-3">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {lang === "zh" ? "命卦" : "Life Gua"}: {r?.life_gua || "—"}
              </h2>
              <span className="paper-tag">{r?.east_west || ""}</span>
            </div>
            {directions.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {directions.map((d: any, i: number) => (
                  <div key={i} className="p-2 rounded-sm"
                    style={{ border: `1px solid ${d.auspicious ? "var(--verdigris)" : "var(--cinnabar)"}`, background: d.auspicious ? "rgba(46,125,50,0.06)" : "rgba(176,58,46,0.06)", fontSize: "0.75rem" }}>
                    <div style={{ fontWeight: 600, color: "var(--ink)" }}>{d.direction || d.name}</div>
                    <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{d.star || d.wu_xing || d.label}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="paper-empty">{lang === "zh" ? "方位数据载入中…" : "Loading directions…"}</div>
            )}
          </section>
          <ChartFooter chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({ method: "bazhai", chart, birth: { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz }, addedAt: Date.now() })}
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
      <MethodSourcesPanel method="fengshui" />
    </div>
  );
}
