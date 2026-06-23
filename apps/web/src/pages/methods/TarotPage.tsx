/** TarotPage v2 — 塔罗专页（牌阵型）
 *  闭环：问题 → 系统建议牌阵 → 洗牌动画 → 逐张翻牌 → 牌组分析 + 解读
 *  依据: 前端重构指示v2 §三·西方类
 */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { emptyBirth } from "../../lib/method-inputs";
import { TAROT_SPREADS, TAROT_SYSTEMS } from "../../lib/method-info";
import type { TarotSpread, TarotSystem } from "../../lib/types";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useStaggeredReveal } from "../../lib/useStaggeredReveal";
import { COLOR } from "../../components/ui";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

// 问题关键词 → 推荐牌阵映射
function suggestSpread(question: string): TarotSpread {
  const q = question.toLowerCase();
  if (/感情|恋爱|关系|姻缘|love|relation|partner|couple/i.test(q)) return "relationship_cross";
  if (/事业|工作|转行|跳槽|career|job|work|promot/i.test(q)) return "career_path";
  if (/选择|二选一|两个|还是|犹豫|option|choice|either/i.test(q)) return "choice_two";
  if (/全年|一年|运势|年运|202|annual|year|overview/i.test(q)) return "celtic_cross";
  if (/内心|情绪|身心灵|自己|成长|mind|soul|spirit/i.test(q)) return "three_mind";
  if (/今天|今日|现在|当下|today|now|immediate/i.test(q)) return "single";
  return "three_time"; // 默认时间之流
}

export function TarotPage() {
  const { t, lang } = useI18n();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("tarot"));

  // 流程阶段
  type Stage = "question" | "spread" | "shuffle" | "reveal" | "result";
  const [stage, setStage] = useState<Stage>("question");

  const [question, setQuestion] = useState("");
  const [spread, setSpread] = useState<TarotSpread>("three_time");
  const [tarotSystem, setTarotSystem] = useState<TarotSystem>("waite");
  const suggestedSpread = useMemo(() => suggestSpread(question), [question]);

  // 翻牌状态
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [revealedIndices, setRevealedIndices] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shuffling, setShuffling] = useState(false);

  const spreadInfo = TAROT_SPREADS.find((s) => s.code === spread) || TAROT_SPREADS[0];
  const suggestedInfo = TAROT_SPREADS.find((s) => s.code === suggestedSpread) || TAROT_SPREADS[0];

  const cards = (chart?.raw?.牌面 || []) as any[];
  const analysis = chart?.raw?.牌组分析 as any;
  const allRevealed = revealedIndices.size >= cards.length;

  // 翻牌 3D 翻动动画的逐张延迟 (card 0 = 0ms, card 1 = 120ms, ...)
  const { getDelay } = useStaggeredReveal(cards.length, {
    interval: 120,
    easing: "cubic-bezier(0.2, 0.7, 0.2, 1)",
  });

  // 步骤1: 确认牌阵 → 抽牌
  const startDraw = useCallback(async () => {
    setLoading(true);
    setError(null);
    setShuffling(true);
    // 洗牌动画: 短暂延迟
    await new Promise((r) => setTimeout(r, 1200));
    setShuffling(false);
    try {
      const birth = emptyBirth();
      const result = await computeChart({
        method: "tarot", birth,
        options: {
          mode: "tarot_spread",
          spread: spread as any,
          tarot_system: tarotSystem,
          question: question || "指引",
        },
      });
      setChart(result);
      setRevealedIndices(new Set());
      setStage("reveal");
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [question, spread, tarotSystem]);

  const revealCard = (idx: number) => {
    setRevealedIndices((prev) => {
      const next = new Set(prev);
      next.add(idx);
      if (next.size >= (chart?.raw?.牌面?.length || 0)) {
        setStage("result");
      }
      return next;
    });
  };

  const revealAll = () => {
    const cards = chart?.raw?.牌面 || [];
    setRevealedIndices(new Set(cards.map((_: any, i: number) => i)));
    setStage("result");
  };

  const addToBasket = () => {
    basketAdd({ method: "tarot", chart, birth: emptyBirth(), addedAt: Date.now() });
  };

  const reset = () => {
    setStage("question");
    setChart(null);
    setRevealedIndices(new Set());
    setError(null);
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title">
          <span className="stamp" />
          {lang === "zh" ? "塔罗抽牌" : "Tarot"}
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {lang === "zh"
            ? "静心凝神，写下你的问题。系统会为你的问题推荐最适合的牌阵，你也可以自己选择。翻开每一张牌，读它的故事。"
            : "Center yourself, write your question, then draw your cards."}
        </p>
      </header>

      {/* Stage 1-2: 问题 + 牌阵选择 */}
      {(stage === "question" || stage === "spread") && (
        <div className="space-y-5">
          {/* 问题 */}
          <section className="paper-frame space-y-3">
            <h2 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>
              {lang === "zh" ? "你的问题" : "Your Question"}
            </h2>
            <textarea
              className="paper-input"
              style={{ minHeight: 80, fontSize: "0.9rem" }}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={lang === "zh" ? "写下你想问的事…" : "What do you want to ask…"}
            />
          </section>

          {/* 牌阵选择 */}
          <section className="paper-frame space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="paper-eyebrow">
                {lang === "zh" ? "选择牌阵" : "Choose Spread"}
              </h2>
              {question.trim() && suggestedSpread !== spread && (
                <button type="button" className="paper-link" onClick={() => setSpread(suggestedSpread)}
                  style={{ fontSize: "0.72rem" }}>
                  {lang === "zh" ? `系统推荐: ${suggestedInfo.label} →` : `Suggested: ${suggestedInfo.label} →`}
                </button>
              )}
              {question.trim() && suggestedSpread === spread && (
                <span className="paper-tag" style={{ borderColor: "var(--verdigris)", color: "var(--verdigris)", fontSize: "0.65rem" }}>
                  {lang === "zh" ? "系统推荐" : "Recommended"}
                </span>
              )}
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {TAROT_SPREADS.map((sp) => {
                const on = spread === sp.code;
                const suggested = sp.code === suggestedSpread && question.trim();
                return (
                  <button key={sp.code} type="button" onClick={() => setSpread(sp.code)}
                    className="paper-grid-cell text-left" style={{
                      borderColor: on ? "var(--cinnabar)" : suggested ? "var(--verdigris)" : "var(--rule)",
                      borderWidth: on ? 2 : 1,
                      background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                      cursor: "pointer", padding: "0.7rem",
                    }}>
                    <div className="flex items-center justify-between">
                      <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.88rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
                        {sp.label}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", marginTop: "0.25rem", lineHeight: 1.4 }}>
                      {sp.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="paper-frame space-y-3">
            <h2 className="paper-eyebrow">
              {lang === "zh" ? "选择解读体系" : "Choose System"}
            </h2>
            <div className="grid sm:grid-cols-3 gap-2">
              {TAROT_SYSTEMS.map((sys) => {
                const on = tarotSystem === sys.code;
                return (
                  <button key={sys.code} type="button" onClick={() => setTarotSystem(sys.code)}
                    className="paper-grid-cell text-left" style={{
                      borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                      borderWidth: on ? 2 : 1,
                      background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                      cursor: "pointer", padding: "0.7rem",
                    }}>
                    <div style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.88rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
                      {sys.label}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", marginTop: "0.25rem", lineHeight: 1.4 }}>
                      {sys.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* 抽牌按钮 */}
          <div className="paper-frame text-center">
            <button type="button" className="paper-btn" onClick={startDraw} disabled={loading || !question.trim()}
              style={{ minWidth: 160, fontSize: "1rem", padding: "0.7rem 2rem" }}>
              {loading ? (lang === "zh" ? "洗牌中…" : "Shuffling…") : (lang === "zh" ? "洗牌抽牌" : "Shuffle & Draw")}
            </button>
            {!question.trim() && (
              <p style={{ fontSize: "0.7rem", color: "var(--ink-soft)", marginTop: "0.5rem" }}>
                {lang === "zh" ? "请先写下你的问题" : "Please write your question first"}
              </p>
            )}
            {error && <div className="paper-error" style={{ marginTop: "0.5rem" }}>{error}</div>}
          </div>
        </div>
      )}

      {/* 洗牌动画 */}
      {shuffling && (
        <section className="paper-frame" style={{ textAlign: "center", padding: "3rem 1rem" }}>
          <div style={{
            width: "2.4rem",
            height: "2.4rem",
            margin: "0 auto",
            border: "1px solid var(--rule)",
            background: "var(--paper-2)",
            animation: "spin 0.5s linear infinite",
            borderRadius: "2px",
          }} />
          <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "1rem", fontFamily: "'Noto Serif SC', serif" }}>
            {lang === "zh" ? "洗牌中… 请凝神专注于你的问题" : "Shuffling… Focus on your question"}
          </p>
        </section>
      )}

      {/* Stage 3: 逐张翻牌 */}
      {stage === "reveal" && chart && (
        <div className="space-y-5 animate-fade-in">
          <section className="paper-frame">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.1rem", fontWeight: 600, color: "var(--cinnabar)" }}>
                {chart.raw?.牌阵名称 || spreadInfo.label}
              </h2>
              <div className="flex gap-2 flex-wrap">
                {chart.raw?.塔罗体系名称 && (
                  <span className="paper-tag" style={{ fontSize: "0.68rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>
                    {chart.raw.塔罗体系名称}
                  </span>
                )}
                <span className="paper-tag" style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>
                  {cards.length} {lang === "zh" ? "张牌 · 点按翻牌" : "cards · tap to reveal"}
                </span>
              </div>
            </div>

            {/* 牌位布局 */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {cards.map((card: any, i: number) => {
                const revealed = revealedIndices.has(i);
                return (
                  <button key={i} type="button" onClick={() => !revealed && revealCard(i)}
                    className={`text-center rounded-sm transition-all ${revealed ? "tarot-flip" : ""}`}
                    style={{
                      border: `1px solid ${revealed ? "var(--rule)" : "var(--cinnabar)"}`,
                      background: revealed ? "var(--paper-2)" : "rgba(176,58,46,0.06)",
                      cursor: revealed ? "default" : "pointer",
                      padding: revealed ? "0.8rem" : "1.5rem 0.5rem",
                      minHeight: revealed ? "auto" : 120,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      animationDelay: revealed ? getDelay(i) : undefined,
                    }}>
                    {!revealed ? (
                      <>
                        <div style={{
                          width: "2rem",
                          height: "2.8rem",
                          border: "1px solid var(--rule)",
                          background: "var(--paper-2)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          opacity: 0.7,
                          borderRadius: "2px",
                        }}>?</div>
                        <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.3rem", fontFamily: "'JetBrains Mono', monospace" }}>
                          {card.位置 || `Card ${i + 1}`}
                        </div>
                        <div style={{ fontSize: "0.55rem", color: "var(--cinnabar)", marginTop: "0.2rem" }}>
                          {lang === "zh" ? "点按翻牌" : "Tap to flip"}
                        </div>
                      </>
                    ) : (
                      <>
                        <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginBottom: "0.2rem", letterSpacing: "0.05em" }}>
                          {card.位置}
                        </div>
                        <div style={{
                          fontFamily: "'Noto Serif SC', serif",
                          fontSize: "1.1rem",
                          fontWeight: 700,
                          color: card.方位 === "逆位" ? "var(--ink)" : "var(--cinnabar)",
                          transform: card.方位 === "逆位" ? "rotate(180deg)" : "none",
                        }}>
                          {card.牌 || card.名称}
                        </div>
                        <div style={{
                          fontSize: "0.6rem",
                          color: card.方位 === "逆位" ? "var(--ink-soft)" : "var(--cinnabar)",
                          marginTop: "0.2rem",
                        }}>
                          {card.方位 === "逆位" ? "逆位 ↑" : "正位"}
                        </div>
                        <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.3rem", lineHeight: 1.4, maxWidth: 200 }}>
                          {card.牌义}
                        </div>
                        {card.主体系解读 && (
                          <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.25rem", lineHeight: 1.4, maxWidth: 220 }}>
                            {card.主体系解读}
                          </div>
                        )}
                      </>
                    )}
                  </button>
                );
              })}
            </div>

            {/* 一键全翻 */}
            {!allRevealed && (
              <div className="text-center mt-4">
                <button type="button" className="paper-btn-ghost" onClick={revealAll}
                  style={{ fontSize: "0.72rem" }}>
                  {lang === "zh" ? "一键全翻（急性子用）" : "Reveal All (for the impatient)"}
                </button>
              </div>
            )}
          </section>
        </div>
      )}

      {/* Stage 4: 全部翻完 → 牌组分析 */}
      {stage === "result" && chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 牌组总览 */}
          <section className="paper-frame space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.1rem", fontWeight: 600, color: "var(--cinnabar)" }}>
                {chart.raw?.牌阵名称} — {lang === "zh" ? "全牌解读" : "Full Reading"}
              </h2>
              {chart.raw?.塔罗体系名称 && (
                <span className="paper-tag" style={{ fontSize: "0.68rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>
                  {chart.raw.塔罗体系名称}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {cards.map((card: any, i: number) => (
                <div key={i} className="text-center rounded-sm p-3"
                  style={{
                    border: "1px solid var(--rule)",
                    background: "var(--paper-2)",
                  }}>
                  <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginBottom: "0.2rem" }}>
                    {card.位置}
                  </div>
                  <div style={{
                    fontFamily: "'Noto Serif SC', serif",
                    fontSize: "1.1rem",
                    fontWeight: 700,
                    color: card.方位 === "逆位" ? "var(--ink)" : "var(--cinnabar)",
                    transform: card.方位 === "逆位" ? "rotate(180deg)" : "none",
                  }}>
                    {card.牌 || card.名称}
                  </div>
                  <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>
                    {card.方位}
                  </div>
                  <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.3rem", lineHeight: 1.4 }}>
                    {card.牌义}
                  </div>
                  {card.主体系解读 && (
                    <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.3rem", lineHeight: 1.4 }}>
                      {card.主体系解读}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* 牌组分析 */}
          {analysis && (
            <section className="paper-frame space-y-2" style={{ borderColor: "var(--cinnabar)", borderWidth: "1.5px", background: "rgba(176,58,46,0.03)" }}>
              <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>
                {lang === "zh" ? "牌组分析" : "Spread Analysis"}
              </div>
              <div className="grid sm:grid-cols-4 gap-2 text-center">
                <StatBox label={lang === "zh" ? "大牌" : "Major"} value={analysis.大牌数} total={cards.length} />
                <StatBox label={lang === "zh" ? "逆位" : "Reversed"} value={analysis.逆位数} total={cards.length} accent />
                <StatBox label={lang === "zh" ? "宫廷" : "Court"} value={analysis.宫廷牌数 || 0} total={cards.length} />
                <StatBox label={lang === "zh" ? "花色" : "Suits"} value={Object.values(analysis.花色分布 || {}).reduce((a: number, b: any) => a + (typeof b === "number" ? b : 0), 0) as number} total={cards.length} />
              </div>
              {analysis.整体提示?.length > 0 && (
                <ul style={{ fontSize: "0.75rem", color: "var(--ink)", lineHeight: 1.6, paddingLeft: "1.2rem" }}>
                  {analysis.整体提示.map((tip: string, i: number) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              )}
            </section>
          )}

          {/* 底部操作栏 */}
          <div className="flex items-center justify-between gap-3 flex-wrap"
            style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              engine: {chart.engine} · {chart.elapsed_ms}ms
            </div>
            <div className="flex gap-2">
              <button type="button" className="paper-btn-ghost" onClick={addToBasket}
                style={{ fontSize: "0.78rem" }} disabled={inBasket}>
                {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" className="paper-btn" onClick={reset}
                style={{ fontSize: "0.78rem" }}>
                {lang === "zh" ? "重新抽牌" : "Redraw"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, total, accent }: { label: string; value: number; total: number; accent?: boolean }) {
  return (
    <div className="p-2 rounded-sm" style={{ background: "var(--paper-2)", border: "1px solid var(--rule)" }}>
      <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{label}</div>
      <div style={{
        fontSize: "1.2rem",
        fontWeight: 700,
        color: accent ? "var(--cinnabar)" : "var(--ink)",
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {value}
        <span style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>/{total}</span>
      </div>
      <MethodSourcesPanel method="tarot" />
    </div>
  );
}
