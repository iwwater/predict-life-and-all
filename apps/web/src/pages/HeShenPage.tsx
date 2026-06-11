/** HeShenPage v2 — 合参专页
 *  卷宗收集 → 提问 → /api/reading 合参 → 共识/分歧/报告
 */
import { type FormEvent, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { useBasket } from "../store/basket";
import { useBirthStore } from "../store/birth";
import { useI18n } from "../lib/i18n";
import { fetchReading } from "../lib/api";
import type { ReadingResult } from "../lib/types";

const METHOD_NAMES_ZH: Record<string, string> = {
  bazi: "八字", bazi_v2: "八字", ziwei: "紫微", qimen: "奇门",
  liuyao: "六爻", meihua: "梅花", chenggu: "称骨",
  bazhai: "八宅", xuankong: "玄空",
  western: "西方占星", vedic: "吠陀", tarot: "塔罗", numerology: "数字命理",
  hepan: "合盘",
};

export function HeShenPage() {
  const { t, lang } = useI18n();
  const items = useBasket((s) => s.items);
  const removeItem = useBasket((s) => s.remove);
  const clearBasket = useBasket((s) => s.clear);
  const birthStore = useBirthStore();

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ReadingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    if (items.length === 0) return;
    setError(null); setLoading(true); setResult(null);
    try {
      const methods = items.map((it) => it.method);
      const birth = birthStore.birth;
      const res = await fetchReading({
        question: question || (lang === "zh" ? "请综合解读" : "Please interpret comprehensively"),
        birth: {
          year: birth.year, month: birth.month, day: birth.day,
          hour: birth.hour, minute: birth.minute, gender: birth.gender,
          calendar: "gregorian", lat: birth.lat, lng: birth.lng, tz: birth.tz || "Asia/Shanghai",
        },
        methods,
        depth: "standard",
        language: lang as "zh" | "en",
      });
      setResult(res);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [items, question, birthStore, lang]);

  const isZh = lang === "zh";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{isZh ? "合参" : "Cross-Reference"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {isZh
            ? "将各专页排好的盘收入卷宗，在此拼合出跨术数共识报告。用户主动合参，非自动触发。"
            : "Collect charts from method pages, then cross-reference them here. User-initiated, not automatic."}
        </p>
      </header>

      {/* 卷宗 */}
      <section className="paper-frame">
        <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
          <h2 className="paper-eyebrow" style={{ margin: 0 }}>
            {isZh ? `卷宗 · ${items.length} 张盘` : `Docket · ${items.length} charts`}
          </h2>
          {items.length > 0 && (
            <button type="button" className="paper-btn-ghost" onClick={clearBasket} style={{ fontSize: "0.72rem" }}>
              {isZh ? "清空" : "Clear"}
            </button>
          )}
        </div>

        {items.length === 0 ? (
          <div className="paper-empty" style={{ textAlign: "center", padding: "2rem 1rem" }}>
            {isZh ? "卷宗为空。请前往各术数专页排盘，然后点击「收入合参」。" : "Docket empty. Go to method pages, cast charts, then tap 'Add to Cross-Reference'."}
            <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
              {["bazi", "ziwei", "liuyao", "tarot", "qimen", "western"].map((m) => (
                <Link key={m} to={`/m/${m}`} className="paper-tag" style={{ textDecoration: "none", fontSize: "0.72rem" }}>
                  {METHOD_NAMES_ZH[m] || m}
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-1.5">
            {items.map((entry, i) => (
              <div key={i} className="flex items-center justify-between gap-2 p-2 rounded-sm"
                style={{ border: "1px solid var(--rule)", background: "var(--paper-2)" }}>
                <div>
                  <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, fontSize: "0.85rem", color: "var(--ink)" }}>
                    {METHOD_NAMES_ZH[entry.method] || entry.method}
                  </span>
                  <span style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginLeft: "0.6rem" }}>
                    {entry.chart ? `${entry.chart.engine}` : (isZh ? "未计算" : "not computed")}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>
                    {new Date(entry.addedAt).toLocaleTimeString()}
                  </span>
                  <button type="button" onClick={() => removeItem(entry.method)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-soft)", fontSize: "0.8rem", padding: "0 0.2rem" }}>
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 合参提问 */}
      {items.length > 0 && (
        <form onSubmit={submit} className="paper-frame space-y-4">
          <h2 className="paper-eyebrow">{isZh ? "发起合参" : "Start Cross-Reference"}</h2>
          <textarea className="paper-input" style={{ minHeight: 80 }} value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={isZh ? "输入你想问的问题…（可选，留空则综合解读）" : "Your question… (optional)"} />
          <div className="flex items-center gap-2 flex-wrap">
            <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
              {loading ? (isZh ? "合参中…" : "Analyzing…") : (isZh ? "发起合参解读" : "Cross-Reference")}
            </button>
            <Link to="/reading" className="paper-btn-ghost" style={{ fontSize: "0.78rem", textDecoration: "none" }}>
              {isZh ? "或使用12法全量合参 →" : "Or full 12-method →"}
            </Link>
          </div>
          {error && <div className="paper-error">{error}</div>}
        </form>
      )}

      {/* 合参结果 */}
      {result && (
        <div className="space-y-5 animate-fade-in">
          {/* 概览 */}
          <section className="paper-frame">
            <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)" }}>
                {isZh ? "合参报告" : "Report"}
              </h2>
              <div className="flex gap-2 flex-wrap" style={{ fontSize: "0.65rem" }}>
                <span className="paper-tag">{isZh ? "术法" : "Methods"}: {result.methods_used?.join(", ") || "—"}</span>
                <span className="paper-tag">{isZh ? "信号" : "Signals"}: {result.signals?.length || 0}</span>
                <span className="paper-tag" style={{
                  color: (result.validation?.confidence ?? 0) >= 0.7 ? "var(--verdigris)" : (result.validation?.confidence ?? 0) >= 0.4 ? "var(--ink)" : "var(--cinnabar)",
                  borderColor: (result.validation?.confidence ?? 0) >= 0.7 ? "var(--verdigris)" : (result.validation?.confidence ?? 0) >= 0.4 ? "var(--ink)" : "var(--cinnabar)",
                }}>
                  {isZh ? "置信" : "Conf"}: {((result.validation?.confidence ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* 共识域 */}
            {result.consensus?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--verdigris)", marginBottom: "0.5rem" }}>
                  {isZh ? "共识" : "Consensus"} ({result.consensus.length})
                </div>
                <div className="space-y-2">
                  {result.consensus.map((c, i) => (
                    <div key={i} className="p-2 rounded-sm" style={{ border: "1px solid var(--rule)", background: "rgba(46,125,50,0.04)" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--ink)" }}>{c.domain}: {c.theme}</div>
                      <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{c.explanation}</div>
                      <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>
                        {isZh ? "支持方法" : "Supporting"}: {c.supporting_methods?.join(", ")}
                        {c.weight_strength ? ` · ${isZh ? "权重" : "weight"}: ${(c.weight_strength * 100).toFixed(0)}%` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 分歧 */}
            {result.conflicts?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.5rem" }}>
                  {isZh ? "分歧" : "Conflicts"} ({result.conflicts.length})
                </div>
                <div className="space-y-2">
                  {result.conflicts.map((c, i) => (
                    <div key={i} className="p-2 rounded-sm" style={{ border: "1px solid var(--rule)", background: "rgba(176,58,46,0.04)" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--cinnabar)" }}>
                        {c.domain}: {c.severity === "high" ? "⚠" : c.severity === "medium" ? "·" : ""} {isZh ? "分歧" : "conflict"}
                      </div>
                      <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{c.conflict_explanation}</div>
                      {c.resolution && (
                        <div style={{ fontSize: "0.63rem", color: "var(--verdigris)", marginTop: "0.3rem" }}>
                          {isZh ? "调和" : "Resolution"}: {c.resolution}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 行动建议 */}
            {result.validation?.action_advice?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--ink)", marginBottom: "0.5rem" }}>
                  {isZh ? "行动建议" : "Action Advice"}
                </div>
                <ul style={{ fontSize: "0.68rem", color: "var(--ink)", paddingLeft: "1.2rem", lineHeight: 1.8 }}>
                  {result.validation.action_advice.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </div>
            )}

            {/* 风险提示 */}
            {result.validation?.risks?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.5rem" }}>
                  {isZh ? "注意事项" : "Risks"}
                </div>
                <ul style={{ fontSize: "0.65rem", color: "var(--ink-soft)", paddingLeft: "1.2rem", lineHeight: 1.8 }}>
                  {result.validation.risks.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </section>

          {/* 解读报告 */}
          {result.report && (
            <section className="paper-frame">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.8rem" }}>
                {isZh ? "综合解读" : "Full Report"}
              </h2>
              {result.report.standard ? (
                <div style={{ fontSize: "0.82rem", color: "var(--ink)", lineHeight: 1.9, whiteSpace: "pre-wrap" }}>
                  {result.report.standard}
                </div>
              ) : result.report.free ? (
                <div style={{ fontSize: "0.82rem", color: "var(--ink)", lineHeight: 1.9, whiteSpace: "pre-wrap" }}>
                  {result.report.free}
                </div>
              ) : null}
              {result.report.premium && result.is_unlocked_premium && (
                <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--rule)" }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.5rem" }}>
                    {isZh ? "深度解读" : "Premium"}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--ink)", lineHeight: 1.9, whiteSpace: "pre-wrap" }}>
                    {result.report.premium}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 安全标记 */}
          {result.safety_flags?.length > 0 && (
            <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", textAlign: "center" }}>
              {result.safety_flags.join(" · ")}
            </div>
          )}

          {/* 免责声明 */}
          <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", textAlign: "center", lineHeight: 1.6 }}>
            {result.disclaimer || (isZh ? "以上为传统文化参考，不构成人生决策建议。" : "Traditional cultural reference only. Not life advice.")}
          </div>
        </div>
      )}
    </div>
  );
}
