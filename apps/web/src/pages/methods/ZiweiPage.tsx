/** ZiweiPage v2 — 紫微斗数专页
 *  闭环：生辰表单 → 紫微盘面 (后端 SVG 直出) → 解读
 */
import { ChartFooter } from "../../components/ChartFooter";
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

/** 4 种盘型布局 (后端 viz/ziwei_svg.py) */
const SVG_STYLES = [
  { id: "traditional", zh: "经典方盘", en: "Traditional" },
  { id: "wheel", zh: "现代轮盘", en: "Wheel" },
  { id: "grid", zh: "宫位网格", en: "Grid" },
  { id: "star_map", zh: "星曜地图", en: "Star Map" },
] as const;

/** 5 个运程盘 (仅经典方盘布局支持) */
const SVG_SCOPES = [
  { id: "natal", zh: "本命", en: "Natal" },
  { id: "decadal", zh: "大限", en: "Decadal" },
  { id: "yearly", zh: "流年", en: "Yearly" },
  { id: "monthly", zh: "流月", en: "Monthly" },
  { id: "xiaoxian", zh: "小限", en: "Minor" },
] as const;

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
  const [svgStyle, setSvgStyle] = useState<(typeof SVG_STYLES)[number]["id"]>("traditional");
  const [svgScope, setSvgScope] = useState<(typeof SVG_SCOPES)[number]["id"]>("natal");
  const [svgLoaded, setSvgLoaded] = useState(false);

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
  /** 盘面 SVG 直出地址 (与后端 /api/ziwei/svg 对齐; 经 vite proxy) */
  const svgUrl = chart
    ? `/api/ziwei/svg?year=${year}&month=${month}&day=${day}&hour=${hour}&minute=${minute}&gender=${gender}` +
      `&style=${svgStyle}&scope=${svgStyle === "traditional" ? svgScope : "natal"}`
    : null;
  const svgKey = `${svgStyle}-${svgScope}`;
  const chip = (active: boolean) => ({
    fontSize: "0.72rem",
    padding: "0.28rem 0.85rem",
    borderRadius: "999px",
    border: `1px solid ${active ? "var(--cinnabar)" : "var(--rule)"}`,
    color: active ? "#fff" : "var(--ink-soft)",
    background: active ? "var(--cinnabar)" : "transparent",
    cursor: "pointer",
  } as React.CSSProperties);

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

      {chart && svgUrl && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame space-y-3">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {lang === "zh" ? "命宫" : "Life Palace"}: {r?.ming_gong || "—"}
              </h2>
              <span className="paper-tag">{r?.ming_zhu || ""} · {r?.shen_zhu || ""}</span>
            </div>

            {/* 盘型切换 */}
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex gap-1.5 flex-wrap">
                {SVG_STYLES.map((s) => (
                  <button key={s.id} type="button" style={chip(svgStyle === s.id)}
                    onClick={() => { setSvgStyle(s.id); setSvgLoaded(false); }}>
                    {lang === "zh" ? s.zh : s.en}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <a className="paper-btn-ghost" style={{ fontSize: "0.75rem", textDecoration: "none" }}
                  href={svgUrl} download={`ziwei-${svgStyle}.svg`}>
                  {lang === "zh" ? "下载 SVG" : "Download"}
                </a>
                <a className="paper-btn-ghost" style={{ fontSize: "0.75rem", textDecoration: "none" }}
                  href={svgUrl} target="_blank" rel="noreferrer">
                  {lang === "zh" ? "原图" : "Raw"}
                </a>
              </div>
            </div>

            {/* 运程切换 (仅经典方盘) */}
            {svgStyle === "traditional" && (
              <div className="flex gap-1.5 flex-wrap">
                {SVG_SCOPES.map((s) => (
                  <button key={s.id} type="button" style={chip(svgScope === s.id)}
                    onClick={() => { setSvgScope(s.id); setSvgLoaded(false); }}>
                    {lang === "zh" ? s.zh : s.en}
                  </button>
                ))}
              </div>
            )}

            {r?.fallback && (
              <div className="paper-note" style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
                {lang === "zh"
                  ? "引擎运行于降级模式（iztro 原生引擎在本环境不可用），盘面为简化排盘。"
                  : "Engine is in fallback mode (iztro native unavailable here); chart is simplified."}
              </div>
            )}

            {/* 盘面 SVG */}
            <div style={{ position: "relative" }}>
              {!svgLoaded && (
                <div className="paper-empty" style={{ minHeight: "240px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {lang === "zh" ? "盘面渲染中…" : "Rendering chart…"}
                </div>
              )}
              <img key={svgKey} src={svgUrl} alt={lang === "zh" ? "紫微盘面" : "Zi Wei chart"}
                onLoad={() => setSvgLoaded(true)} onError={() => setSvgLoaded(false)}
                style={{
                  width: "100%", height: "auto", display: svgLoaded ? "block" : "none",
                  border: "1px solid var(--rule)", borderRadius: "3px", background: "var(--paper-2)",
                }} />
            </div>

            {/* 宫位速览 (SVG 之外的文本对照, 供复制/检索) */}
            {palaces.length > 0 && (
              <details style={{ borderTop: "1px dashed var(--rule)", paddingTop: "0.75rem" }}>
                <summary style={{ fontSize: "0.78rem", color: "var(--ink-soft)", cursor: "pointer" }}>
                  {lang === "zh" ? `十二宫速览（${palaces.length} 宫）` : `Palace list (${palaces.length})`}
                </summary>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5" style={{ marginTop: "0.75rem" }}>
                  {palaces.map((p: any, i: number) => (
                    <div key={i} className="text-center p-2 rounded-sm"
                      style={{ border: `1px solid ${p.name === r?.ming_gong ? "var(--cinnabar)" : "var(--rule)"}`, background: p.name === r?.ming_gong ? "rgba(176,58,46,0.06)" : "var(--paper-2)" }}>
                      <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>{p.name}</div>
                      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{p.stars?.slice(0, 2).join(" ") || p.zhi || ""}</div>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </section>
          <ChartFooter chart={chart} method="ziwei" inBasket={inBasket} onBasket={() => basketAdd({ method: "ziwei", chart, birth: { year, month, day, hour, minute, gender, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz, is_leap_month: false }, addedAt: Date.now() })} onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }

