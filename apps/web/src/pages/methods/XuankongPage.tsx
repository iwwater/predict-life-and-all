/** XuankongPage v2 — 玄空飞星专页
 *  不需生辰, 只需坐向 + 建造年份 + 运期 → 九宫飞星
 */
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";

const DIRECTIONS = ["子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬"];

export function XuankongPage() {
  const { t, lang } = useI18n();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("xuankong"));

  const [sittingDir, setSittingDir] = useState("子");
  const [constructionYear, setConstructionYear] = useState(new Date().getFullYear());
  const [period, setPeriod] = useState(8);
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const result = await computeChart({
        method: "xuankong",
        birth: { year: constructionYear, month: 1, day: 1, hour: 12, minute: 0, gender: "unspecified", calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" },
        options: { mode: "home_fengshui", sitting: sittingDir, construction_year: constructionYear, period },
      });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [sittingDir, constructionYear, period]);

  const r = chart?.raw;
  const grid = r?.flying_stars || r?.grid || [];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "玄空飞星" : "Xuan Kong Fei Xing"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "三元九运飞星盘。宅命相配，山向合局。" : "Flying Stars chart with mountain/facing stars."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "宅向" : "Orientation"}</h2>
        <div className="flex gap-3 flex-wrap items-end">
          <F label={lang === "zh" ? "坐向" : "Sitting"}>
            <select className="paper-input" value={sittingDir} onChange={(e) => setSittingDir(e.target.value)}>
              {DIRECTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </F>
          <F label={lang === "zh" ? "建造年" : "Year"}>
            <input className="paper-input" type="number" style={{ maxWidth: 100 }} value={constructionYear} onChange={(e) => setConstructionYear(parseInt(e.target.value) || 0)} />
          </F>
          <F label={lang === "zh" ? "运期" : "Period"}>
            <select className="paper-input" value={period} onChange={(e) => setPeriod(parseInt(e.target.value, 10))}>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((p) => <option key={p} value={p}>{`${lang === "zh" ? "第" : "P"}${p}${lang === "zh" ? "运" : ""}`}</option>)}
            </select>
          </F>
        </div>
        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "飞星中…" : "Casting…") : (lang === "zh" ? "排玄空盘" : "Cast Stars")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "1rem" }}>
              {lang === "zh" ? "飞星盘" : "Flying Stars"} {lang === "zh" ? `第${period}运` : `Period ${period}`}
            </h2>
            {grid.length > 0 ? (
              <div className="grid grid-cols-3 gap-1.5" style={{ maxWidth: 400, margin: "0 auto" }}>
                {grid.map((g: any, i: number) => (
                  <div key={i} className="text-center p-2 rounded-sm"
                    style={{ border: "1px solid var(--rule)", background: "var(--paper-2)", minHeight: 60 }}>
                    <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>{g.palace || g.name || i + 1}</div>
                    <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                      {Array.isArray(g.stars) ? g.stars.join(" ") : (g.star || "—")}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="paper-empty">{lang === "zh" ? "飞星盘面载入中…" : "Loading grid…"}</div>
            )}
          </section>
          <ChartFooter chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({ method: "xuankong", chart, birth: { year: constructionYear, month: 1, day: 1, hour: 12, minute: 0, gender: "unspecified", calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" }, addedAt: Date.now() })}
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
