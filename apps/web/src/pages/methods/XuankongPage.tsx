/** XuankongPage v2 — 玄空飞星专页
 *  不需生辰, 只需坐向 + 建造年份 + 运期 → 九宫飞星
 */
import { ChartFooter } from "../../components/ChartFooter";
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

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
        options: { mode: "residential_xuankong", sitting: sittingDir, construction_year: constructionYear, period },
      });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [sittingDir, constructionYear, period]);

  const r = chart?.raw as Record<string, any> | undefined;
  // 引擎 raw 中文键: 九宫{宫:{运,山,向}}/坐/向/运/格局(list)/向首/坐山; 宫键繁体(兌/離)
  const TRAD: Record<string, string> = { 兑: "兌", 离: "離" };
  const pick = (d: Record<string, any> | undefined, name: string) => (d && (d[name] ?? d[TRAD[name] ?? name])) || undefined;
  const LUO_SHU: Array<[string, string]> = [
    ["巽", "SE"], ["离", "S"], ["坤", "SW"],
    ["震", "E"], ["中", "C"], ["兑", "W"],
    ["艮", "NE"], ["坎", "N"], ["乾", "NW"],
  ];
  const jiuGong = r?.["九宫"] || {};
  const geju = Array.isArray(r?.["格局"]) ? r!["格局"] : [];

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
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {lang === "zh" ? "飞星盘" : "Flying Stars"}
              </h2>
              <div className="flex gap-1.5 flex-wrap">
                {r?.["坐"] && <span className="paper-tag">{lang === "zh" ? `坐${r["坐"]}山 · 向${r["向"]}向` : `${r["坐"]}→${r["向"]}`}</span>}
                {r?.["运"] != null && <span className="paper-tag">{lang === "zh" ? `入运 ${r["运"]}` : `P ${r["运"]}`}</span>}
                {geju.length > 0 && <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "currentColor" }}>{geju[0]}</span>}
              </div>
            </div>
            {Object.keys(jiuGong).length > 0 ? (
              <div className="grid grid-cols-3 gap-1.5" style={{ maxWidth: 400, margin: "0 auto" }}>
                {LUO_SHU.map(([g, en]) => {
                  const cell = pick(jiuGong, g) as { 运: number; 山: number; 向: number } | undefined;
                  const isC = g === "中";
                  return (
                    <div key={g} className="text-center p-2 rounded-sm"
                      style={{ border: `1px solid ${isC ? "var(--gold, #c9a227)" : "var(--rule)"}`, background: "var(--paper-2)", minHeight: 64 }}>
                      <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>{g}{isC ? "" : ` ${en}`}</div>
                      {cell ? (
                        <div className="grid grid-cols-3 gap-0.5" style={{ marginTop: "0.35rem" }}>
                          {(["运", "山", "向"] as const).map((k) => (
                            <div key={k}>
                              <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>{k}</div>
                              <div style={{ fontSize: "0.95rem", fontWeight: 700, color: k === "向" ? "var(--cinnabar)" : k === "山" ? "var(--verdigris, #2f6f6a)" : "var(--ink)", fontFamily: "'JetBrains Mono', monospace" }}>{cell[k] ?? "—"}</div>
                            </div>
                          ))}
                        </div>
                      ) : <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.5rem" }}>—</div>}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="paper-empty">{lang === "zh" ? "盘面数据为空。" : "No grid data."}</div>
            )}
            {(geju.length > 1 || r?.["向首"] || r?.["坐山"]) && (
              <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", textAlign: "center", marginTop: "0.7rem" }}>
                {geju.length > 1 ? geju.slice(1).join("；") : ""}
                {r?.["向首"] ? ` · 向首${r["向首"]}` : ""}
                {r?.["坐山"] ? ` · 坐山${r["坐山"]}` : ""}
              </div>
            )}
          </section>
          <ChartFooter method="fengshui" recastLabel="重新排盘" chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({ method: "xuankong", chart, birth: { year: constructionYear, month: 1, day: 1, hour: 12, minute: 0, gender: "unspecified", calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" }, addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="paper-label">{label}</label>{children}</div>; }

