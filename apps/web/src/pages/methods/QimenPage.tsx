/** QimenPage v2 — 奇门遁甲专页（九宫式盘）
 *  问事 + 时间（默认此刻）→ 九宫盘 → 解读
 */
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

export function QimenPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("qimen"));

  const [question, setQuestion] = useState("");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = birthStore.toApiBirth();
      const result = await computeChart({ method: "qimen", birth: b, options: { mode: "hour_qimen", question: question || "问事" } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [question, birthStore]);

  const r = chart?.raw;
  const palaces = r?.grid_palaces || r?.palaces || [];

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
              {r?.zhifu && <span className="paper-tag">{lang === "zh" ? "值符" : "Zhi Fu"}: {r.zhifu}</span>}
              {r?.zhishi && <span className="paper-tag">{lang === "zh" ? "值使" : "Zhi Shi"}: {r.zhishi}</span>}
            </div>
            <div className="grid grid-cols-3 gap-1.5" style={{ maxWidth: 480, margin: "0 auto" }}>
              {PALACE_ORDER.map((p, i) => {
                const data = palaces.find((g: any) => g.palace === p.name || g.palace === p.idx);
                return (
                  <div key={p.name} className="text-center p-2 rounded-sm animate-fade-in"
                    style={{ border: `1px solid var(--rule)`, background: p.name === "中" ? "var(--paper-2)" : "var(--paper)", minHeight: 70, ...getPalaceStyle(i) }}>
                    <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>{p.name}{p.name !== "中" ? ` ${p.en}` : ""}</div>
                    {data ? (
                      <div style={{ fontSize: "0.65rem", color: "var(--ink)", lineHeight: 1.4 }}>
                        <div>{data.stem || ""}{data.door || ""}</div>
                        <div style={{ color: "var(--ink-soft)" }}>{data.star || ""}{data.spirit || ""}</div>
                      </div>
                    ) : <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>—</div>}
                  </div>
                );
              })}
            </div>
          </section>
          <ChartFooter chart={chart} method="qimen" inBasket={inBasket}
            onBasket={() => basketAdd({ method: "qimen", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() })}
            onReset={() => setChart(null)} />
        </div>
      )}
    </div>
  );
}

function ChartFooter({ chart, inBasket, onBasket, onReset }: any) {
  const { lang } = useI18n();
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
      <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>engine: {chart.engine} · {chart.elapsed_ms}ms</div>
      <div className="flex gap-2">
        <button type="button" className="paper-btn-ghost" onClick={onBasket} disabled={inBasket} style={{ fontSize: "0.78rem" }}>
          {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
        </button>
        <button type="button" className="paper-btn" onClick={onReset} style={{ fontSize: "0.78rem" }}>{lang === "zh" ? "重新起盘" : "Recast"}</button>
      </div>
      <MethodSourcesPanel method="qimen" />
    </div>
  );
}
