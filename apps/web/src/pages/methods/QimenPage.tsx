/** QimenPage v2 — 奇门遁甲专页（九宫式盘）
 *  问事 + 时间（默认此刻）→ 九宫盘 → 解读
 */
import { ChartFooter } from "../../components/ChartFooter";
import { type FormEvent, useState, useCallback } from "react";
import type { ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";

// 九宫方位: 按 巽离坤/震中兑/艮坎乾 排列（方位是红线不能错）
const PALACE_ORDER = [
  { name: "巽", en: "SE", idx: 3 },
  { name: "离", en: "S", idx: 8 },
  { name: "坤", en: "SW", idx: 1 },
  { name: "震", en: "E", idx: 2 },
  { name: "中", en: "C", idx: 4 },
  { name: "兑", en: "W", idx: 6 },
  { name: "艮", en: "NE", idx: 7 },
  { name: "坎", en: "N", idx: 0 },
  { name: "乾", en: "NW", idx: 5 },
];

// kinqimen 原生输出的宫键是繁体（兌/離），与简体方位名做归一
const TRAD: Record<string, string> = { 兑: "兌", 离: "離" };
const pick = (d: Record<string, any> | undefined, name: string) =>
  (d && (d[name] ?? d[TRAD[name] ?? name])) || undefined;

export function QimenPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("qimen"));

  const [question, setQuestion] = useState("");
  const [panMode, setPanMode] = useState("hour_qimen");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = birthStore.toApiBirth();
      const result = await computeChart({ method: "qimen", birth: b, options: { mode: panMode, question: question || "问事" } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [question, panMode, birthStore]);

  const r = chart?.raw;
  const d = (r || {}) as Record<string, any>;
  const tianPan = d["天盘三奇六仪"] || {};
  const diPan = d["地盘三奇六仪"] || {};
  const doors = d["八门"] || {};
  const stars = d["九星"] || {};
  const spirits = d["八神"] || {};
  const hasGrid = Object.keys(tianPan).length > 0 || Object.keys(doors).length > 0;
  const zfzs = d["值符值使"] || {};
  const zfGong = Array.isArray(zfzs["值符星宮"]) ? zfzs["值符星宮"][1] : undefined;
  const zsGong = Array.isArray(zfzs["值使門宮"]) ? zfzs["值使門宮"][1] : undefined;
  const zfStar = Array.isArray(zfzs["值符星宮"]) ? zfzs["值符星宮"][0] : undefined;
  const zsDoor = Array.isArray(zfzs["值使門宮"]) ? zfzs["值使門宮"][0] : undefined;
  const duan = d["断"] || {};
  const panInfo = d["pan_info"] || {};
  const paiJu = String(d["排局"] || "").replace(/陽/g, "阳").replace(/陰/g, "阴");

  const { getStyle: getPalaceStyle } = useStaggeredReveal(9, {
    interval: 110,
    initialDelay: 0,
    maxTotal: 1500,
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "奇门遁甲" : "Qi Men Dun Jia"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "九宫式盘，按天地盘干、九星、八门、八神叠布。值符值使为纲，格局为目。" : "9-Palace chart with heaven/earth stems, stars, doors, spirits."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "问事" : "Question"} ({lang === "zh" ? "必填" : "required"})</h2>
        <textarea className="paper-input" style={{ minHeight: 80 }} value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={lang === "zh" ? "一事一问，默认为此刻起盘。" : "Default to current moment."} />
        <div className="flex gap-1.5 flex-wrap">
          {[{ value: "hour_qimen", label: lang === "zh" ? "时家奇门" : "Hour" }, { value: "day_qimen", label: lang === "zh" ? "日家奇门" : "Day" }].map((m) => (
            <button key={m.value} type="button" onClick={() => setPanMode(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: panMode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: panMode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>{m.label}</button>
          ))}
        </div>
        {panMode === "day_qimen" && (
          <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
            {lang === "zh" ? "日家奇门走模拟排层（原生库仅支持时家转盘），盘面带「模拟」标记。" : "Day pan uses a simulated layer."}
          </div>
        )}
        <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
          {lang === "zh" ? "出生信息从全局记忆带入，用于命主定位。" : "Birth info from global memory."}
        </div>
        <button type="submit" className="paper-btn" disabled={loading || !question.trim()} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "布盘中…" : "Casting…") : (lang === "zh" ? "起奇门盘" : "Cast Qi Men")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {lang === "zh" ? "奇门九宫盘" : "Qi Men Chart"}
              </h2>
              <div className="flex gap-1.5 flex-wrap">
                {zfStar && <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "currentColor" }}>{lang === "zh" ? `值符 天${zfStar}星 · ${zfGong}宫` : `Zhi Fu: ${zfStar}`}</span>}
                {zsDoor && <span className="paper-tag" style={{ color: "var(--verdigris)", borderColor: "currentColor" }}>{lang === "zh" ? `值使 ${zsDoor}门 · ${zsGong}宫` : `Zhi Shi: ${zsDoor}`}</span>}
                {panInfo.fallback_simulated && <span className="paper-tag" style={{ color: "var(--ink-soft)" }}>{lang === "zh" ? "模拟盘" : "simulated"}</span>}
              </div>
            </div>
            {paiJu && (
              <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", textAlign: "center", marginBottom: "0.6rem" }}>
                {[paiJu, d["干支"], d["节气"] ? `节气${d["节气"]}` : null, d["旬首"] ? `旬首${d["旬首"]}` : null].filter(Boolean).join(" · ")}
              </div>
            )}
            {hasGrid ? (
              <div className="grid grid-cols-3 gap-1.5" style={{ maxWidth: 480, margin: "0 auto" }}>
                {PALACE_ORDER.map((p, i) => {
                  const tGan = pick(tianPan, p.name);
                  const dGan = pick(diPan, p.name);
                  const door = pick(doors, p.name);
                  const star = pick(stars, p.name);
                  const spirit = pick(spirits, p.name);
                  const isZF = p.name === zfGong || TRAD[p.name] === zfGong;
                  const isZS = p.name === zsGong || TRAD[p.name] === zsGong;
                  const border = isZF ? "var(--cinnabar)" : isZS ? "var(--verdigris)" : "var(--rule)";
                  return (
                    <div key={p.name} className="text-center p-2 rounded-sm animate-fade-in"
                      style={{ border: `1.5px solid ${border}`, background: p.name === "中" ? "var(--paper-2)" : "var(--paper)", minHeight: 92, ...getPalaceStyle(i) }}>
                      <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>
                        {p.name}{p.name !== "中" ? ` ${p.en}` : ""}{isZF ? " ·符" : ""}{isZS ? " ·使" : ""}
                      </div>
                      <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif", lineHeight: 1.3 }}>
                        {tGan || "—"}{dGan && dGan !== tGan ? <span style={{ fontSize: "0.62rem", color: "var(--ink-soft)", fontWeight: 400 }}> / 地{dGan}</span> : null}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--ink)", fontWeight: 600 }}>{door || ""}</div>
                      <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", lineHeight: 1.35 }}>{star || ""}{spirit ? ` ${spirit}` : ""}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "1rem 0" }}>
                <div style={{ fontSize: "0.85rem", color: "var(--ink)" }}>{lang === "zh" ? "原生排盘库不可用，未伪造九宫。" : "Native lib unavailable; no fake grid."}</div>
                {d["fallback_reason"] && <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>{d["fallback_reason"]}</div>}
              </div>
            )}
            {(duan["格局"] || []).length > 0 && (
              <details style={{ marginTop: "0.9rem" }}>
                <summary style={{ cursor: "pointer", fontSize: "0.75rem", color: "var(--ink-soft)" }}>{lang === "zh" ? `格局与断（${(duan["格局"] || []).length} 条）` : "Patterns"}</summary>
                <div className="space-y-1.5" style={{ marginTop: "0.6rem", fontSize: "0.75rem", color: "var(--ink)" }}>
                  {(duan["格局"] || []).map((g: string, i: number) => <div key={i} style={{ borderLeft: "2px solid var(--cinnabar)", paddingLeft: "0.5rem" }}>{g}</div>)}
                  {(duan["空亡宫"] || []).length > 0 && <div>{lang === "zh" ? `空亡宫：${(duan["空亡宫"] || []).map((g: string) => g.replace("離", "离")).join("、")}` : ""}</div>}
                  {Object.keys(duan["门状态"] || {}).length > 0 && (
                    <div>{Object.entries(duan["门状态"]).map(([k, v]) => `${k}:${v}`).join("；")}</div>
                  )}
                  {d["马星"] && (
                    <div>{lang === "zh" ? `马星：天马${d["马星"]["天馬"]} 丁马${d["马星"]["丁馬"]} 驿马${d["马星"]["驛馬"]}` : ""}</div>
                  )}
                  {duan["说明"] && <div style={{ color: "var(--ink-soft)" }}>{duan["说明"]}</div>}
                </div>
              </details>
            )}
          </section>
          <ChartFooter chart={chart} method="qimen" inBasket={inBasket}
            onBasket={() => basketAdd({ method: "qimen", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

