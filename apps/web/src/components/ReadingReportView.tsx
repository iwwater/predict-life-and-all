/** ReadingReport — 综合解读报告（「古籍×仪器」命书风格）
 *
 * LLM 报告即正文；结构化信号退到可折叠附录。
 * 解决上一版"正文+结构化重复渲染"导致的用户不可读问题。
 */
import { useState, useMemo, useCallback } from "react";
import type { ReadingResult, DivinationSignal } from "../lib/types";
import { METHOD_LABELS_ZH } from "../lib/types";
import { saveReadingToHistory } from "../store/readingHistory";

// ── 静态常量 ──────────────────────────────────────────────────────────────────

const CONFIDENCE_COLORS: Record<string, string> = {
  low: "var(--cinnabar)", medium: "var(--cinnabar-dim)", medium_high: "var(--indigo)", high: "var(--verdigris)",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  low: "可信度较低", medium: "参考可信", medium_high: "较可信", high: "高度可信",
};

const POLARITY_MARK: Record<string, string> = {
  positive: "吉", negative: "凶", neutral: "平", mixed: "杂",
};

// ── 子组件 ────────────────────────────────────────────────────────────────────

function ScoreSeal({ score }: { score: number }) {
  const color = score >= 70 ? "var(--verdigris)" : score >= 50 ? "var(--indigo)" : score >= 35 ? "var(--cinnabar-dim)" : "var(--cinnabar)";
  return (
    <span className="paper-seal" style={{
      width: "2.6rem", height: "2.6rem", lineHeight: "2.6rem", fontSize: "1rem",
      color, borderColor: color,
    }}>
      {score}
    </span>
  );
}

// Phase 1: 5 维小印章 (紧凑版, 用于 dim 矩阵)
function DimSeal({ label, score }: { label: string; score: number }) {
  const color = score >= 70 ? "var(--verdigris)" : score >= 50 ? "var(--indigo)" : score >= 35 ? "var(--cinnabar-dim)" : "var(--cinnabar)";
  return (
    <div className="text-center" style={{ flex: "1 1 0", minWidth: 0 }}>
      <span className="paper-seal" style={{
        display: "inline-block",
        width: "1.8rem", height: "1.8rem", lineHeight: "1.8rem", fontSize: "0.7rem",
        color, borderColor: color,
      }}>
        {Math.round(score)}
      </span>
      <div style={{ fontSize: "0.5rem", color: "var(--ink-soft)", marginTop: "0.15rem", letterSpacing: "0.04em" }}>
        {label}
      </div>
    </div>
  );
}

const DIM_LABELS: Record<string, string> = {
  long_term:     "长期命格",
  current_cycle: "当前周期",
  relationship:  "关系合参",
  one_question:  "一事一断",
  space:         "空间环境",
};

// ── Markdown → HTML（去掉 LLM 输出中的 emoji 字符）──────────────────────────

const EMOJI_STRIP = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{200D}]/gu;

function renderMarkdown(text: string): string {
  let html = text
    .replace(EMOJI_STRIP, "")
    .replace(/^### (.+)$/gm, '<h3 style="font-size:0.82rem;font-weight:600;margin:0.9rem 0 0.35rem;color:var(--cinnabar);font-family:\'Noto Serif SC\',serif">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:0.9rem;font-weight:600;margin:1rem 0 0.45rem;color:var(--ink);font-family:\'Noto Serif SC\',serif">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:1rem;font-weight:700;margin:1.2rem 0 0.5rem;color:var(--ink)">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--ink)">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li style="margin-left:1em;color:var(--ink-soft);line-height:1.7">· $1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li style="margin-left:1em;color:var(--ink-soft);line-height:1.7">$1. $2</li>')
    .replace(/^---$/gm, '<hr style="margin:0.6rem 0;border:none;border-top:1px solid var(--rule)">')
    .replace(/^> (.+)$/gm, '<blockquote style="border-left:2px solid var(--cinnabar);padding-left:0.75rem;margin:0.4rem 0;color:var(--ink-soft);font-family:\'Noto Serif SC\',serif">$1</blockquote>')
    .replace(/\n\n/g, '</p><p style="margin:0.4rem 0;line-height:1.85;color:var(--ink-soft)">')
    .replace(/\n/g, '<br/>');

  html = '<p style="margin:0.4rem 0;line-height:1.85;color:var(--ink-soft)">' + html + '</p>';
  return html;
}

// ── Main Component ────────────────────────────────────────────────────────────

export interface ReadingReportViewProps {
  result: ReadingResult;
}

export function ReadingReportView({ result }: ReadingReportViewProps) {
  const [showAppendix, setShowAppendix] = useState(false);
  const [saved, setSaved] = useState(false);
  const [viewTier, setViewTier] = useState<"standard" | "premium">("standard");

  const { validation, report, signals } = result;

  const handleSave = useCallback(() => {
    try {
      saveReadingToHistory(result);
      setSaved(true);
    } catch { /* localStorage full */ }
  }, [result]);

  // 默认显示标准报告，premium 可切换
  const hasPremium = result.is_unlocked_premium;
  const displayReport = viewTier === "premium" && hasPremium
    ? (report.premium || report.standard || "")
    : (report.standard || report.free || "");

  // 从 displayReport 首行 blockquote 提取 headline
  const headline = useMemo(() => {
    const m = displayReport.match(/^>\s*(.+)$/m);
    return m ? m[1] : "综合分析完成";
  }, [displayReport]);

  // 各法最强信号（附录用）
  const methodSummary = useMemo(() => {
    const map = new Map<string, DivinationSignal>();
    for (const s of signals) {
      const existing = map.get(s.method);
      if (!existing || s.strength > existing.strength) map.set(s.method, s);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [signals]);

  // 是否有值得展示的结构化共识/分歧
  const hasConsensus = validation.consensus.length > 0;
  const hasConflicts = validation.conflicts.length > 0;
  const hasRisks = validation.risks.length > 0;
  const hasAdvice = validation.action_advice.length > 0;
  const hasTiming = validation.timing && (validation.timing.short_term_signals || validation.timing.medium_term_signals || validation.timing.long_term_signals);

  return (
    <div className="space-y-5">
      {/* ── 安全降级 ── */}
      {result.safety_downgrades && result.safety_downgrades.length > 0 && (
        <div className="space-y-1">
          {result.safety_downgrades.map((msg, i) => (
            <div key={i} className="paper-caution" style={{ fontSize: "0.72rem" }}>
              {msg}
            </div>
          ))}
        </div>
      )}

      {/* ═══ 命书正文 ═══ */}
      <div className="paper-frame">
        <div className="paper-compass-bg" aria-hidden />

        {/* ── 标题栏 ── */}
        <div className="flex items-start justify-between flex-wrap gap-3" style={{ marginBottom: "0.75rem" }}>
          <div>
            <h1 className="paper-title" style={{ marginBottom: "0.2rem" }}>
              <span className="stamp" />
              <span>合参命书</span>
              <span className="sub" style={{ fontSize: "0.7rem" }}>
                {result.methods_used.length} 术 · {result.signals.length} 信号
              </span>
            </h1>
            <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              {result.session_id.slice(0, 12)} · {result.elapsed_ms}ms
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-center">
              <ScoreSeal score={validation.overall_score} />
              <div style={{ fontSize: "0.52rem", color: "var(--ink-soft)", marginTop: "0.1rem" }}>综合</div>
            </div>
            <div style={{
              textAlign: "center", padding: "0.25rem 0.5rem",
              border: `1px solid ${CONFIDENCE_COLORS[validation.confidence_level] || "var(--rule)"}`,
              borderRadius: "2px",
            }}>
              <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)", letterSpacing: "0.08em" }}>可信</div>
              <div style={{
                fontSize: "0.7rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif",
                color: CONFIDENCE_COLORS[validation.confidence_level] || "var(--ink-soft)",
              }}>
                {CONFIDENCE_LABELS[validation.confidence_level] || validation.confidence_level}
              </div>
            </div>
          </div>
        </div>

        {/* ── 一句话结论 ── */}
        <blockquote style={{
          borderLeft: "3px solid var(--cinnabar)",
          padding: "0.4rem 0 0.4rem 0.9rem",
          margin: "0 0 0.75rem",
          fontSize: "0.92rem", fontWeight: 600, lineHeight: 1.8,
          color: "var(--ink)", fontFamily: "'Noto Serif SC', serif",
          letterSpacing: "0.02em",
        }}>
          {headline}
        </blockquote>

        {/* ── Phase 1: 5 维 score 矩阵 ── */}
        {validation.dim_scores && Object.keys(validation.dim_scores).length > 0 && (
          <div style={{
            display: "flex", gap: "0.4rem", alignItems: "stretch",
            padding: "0.5rem 0.25rem 0.6rem",
            borderTop: "1px dashed var(--rule)",
            borderBottom: "1px dashed var(--rule)",
            margin: "0 0 0.75rem",
          }}>
            {Object.entries(validation.dim_scores).map(([dim, sc]) => (
              <DimSeal key={dim} label={DIM_LABELS[dim] || dim} score={sc as number} />
            ))}
          </div>
        )}

        {/* ── 报告层级切换 ── */}
        <div className="flex items-center justify-between" style={{ marginBottom: "0.5rem" }}>
          <div className="flex items-center gap-1.5">
            <button type="button" onClick={() => setViewTier("standard")}
              className="paper-tag" style={{
                cursor: "pointer", fontSize: "0.62rem",
                color: viewTier === "standard" ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: viewTier === "standard" ? "var(--cinnabar)" : "var(--rule)",
              }}>标准报告</button>
            {hasPremium && (
              <button type="button" onClick={() => setViewTier("premium")}
                className="paper-tag" style={{
                  cursor: "pointer", fontSize: "0.62rem",
                  color: viewTier === "premium" ? "var(--cinnabar)" : "var(--ink-soft)",
                  borderColor: viewTier === "premium" ? "var(--cinnabar)" : "var(--rule)",
                }}>深度报告</button>
            )}
          </div>
          {!hasPremium && result.is_unlocked_standard && (
            <span style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>
              AI 标准报告
            </span>
          )}
        </div>

        {/* ── 批文正文（LLM 生成的完整报告，唯一正文）── */}
        <div className="paper-body"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(displayReport) }} />

        {/* ── 分隔 ── */}
        <div className="paper-hr" style={{ margin: "0.75rem 0" }} />

        {/* ── 参与术法标签 ── */}
        <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginBottom: "0.4rem" }}>
          参与术法：
        </div>
        <div className="flex flex-wrap gap-1">
          {result.methods_used.map((m) => (
            <span key={m} className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar-dim)" }}>
              {METHOD_LABELS_ZH[m] || m}
            </span>
          ))}
        </div>

        {/* ── 附录：信号详情（可折叠）── */}
        <div style={{ marginTop: "0.6rem" }}>
          <button onClick={() => setShowAppendix(!showAppendix)}
            className="paper-link" style={{ fontSize: "0.68rem", cursor: "pointer", background: "none", border: "none" }}>
            {showAppendix ? "收起附录" : "附录：信号详情"}（{signals.length} 条，{result.methods_used.length} 法）
          </button>

          {showAppendix && (
            <div className="space-y-3" style={{ marginTop: "0.6rem", paddingTop: "0.6rem", borderTop: "1px solid var(--rule)" }}>

              {/* 各法最强信号 */}
              <div>
                <div className="paper-eyebrow" style={{ marginBottom: "0.3rem" }}>各法摘要</div>
                <div className="space-y-0">
                  {methodSummary.map(([method, s]) => (
                    <div key={method} className="flex items-center gap-2" style={{ fontSize: "0.65rem", padding: "0.15rem 0" }}>
                      <span style={{
                        fontSize: "0.55rem", width: "0.9rem", textAlign: "center", fontWeight: 700,
                        color: s.polarity === "positive" ? "var(--verdigris)" : s.polarity === "negative" ? "var(--cinnabar)" : "var(--ink-soft)",
                      }}>{POLARITY_MARK[s.polarity] || "平"}</span>
                      <span className="font-semibold" style={{ color: "var(--ink)", minWidth: 65, fontFamily: "'Noto Serif SC', serif" }}>
                        {METHOD_LABELS_ZH[s.method] || s.method}
                      </span>
                      <span style={{ color: "var(--ink-soft)" }}>{s.signal_key}</span>
                      <span className="paper-mono" style={{ fontSize: "0.52rem", color: "var(--rule)", marginLeft: "auto" }}>
                        s{s.strength.toFixed(2)} c{s.confidence.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 共识（仅当 LLM 未覆盖时展示） */}
              {hasConsensus && (
                <div>
                  <div className="paper-eyebrow" style={{ marginBottom: "0.3rem" }}>术法共识</div>
                  <div className="space-y-1.5">
                    {validation.consensus.map((c, i) => (
                      <div key={i} style={{ borderLeft: "2px solid var(--verdigris)", padding: "0.2rem 0 0.2rem 0.6rem" }}>
                        <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--verdigris)", fontFamily: "'Noto Serif SC', serif" }}>
                          {c.theme}
                        </span>
                        <span className="paper-mono" style={{ fontSize: "0.52rem", color: "var(--verdigris)", marginLeft: "0.5rem" }}>
                          {c.weight_strength}/100
                        </span>
                        <p style={{ fontSize: "0.68rem", color: "var(--ink-soft)", lineHeight: 1.7, margin: "0.15rem 0" }}>
                          {c.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 分歧 */}
              {hasConflicts && (
                <div>
                  <div className="paper-eyebrow" style={{ marginBottom: "0.3rem" }}>术法分歧</div>
                  <div className="space-y-1.5">
                    {validation.conflicts.map((c, i) => (
                      <div key={i} style={{ borderLeft: `2px solid ${c.severity === "high" ? "var(--cinnabar)" : "var(--rule)"}`, padding: "0.2rem 0 0.2rem 0.6rem" }}>
                        <span style={{ fontSize: "0.68rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                          {c.domain}
                        </span>
                        <p style={{ fontSize: "0.65rem", color: "var(--ink-soft)", lineHeight: 1.7, margin: "0.1rem 0" }}>
                          {c.conflict_explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 全量信号日志 */}
              <div>
                <div className="paper-eyebrow" style={{ marginBottom: "0.3rem" }}>全量信号日志</div>
                <div className="paper-frame space-y-0.5 max-h-64 overflow-y-auto" style={{ background: "var(--paper-2)", padding: "0.4rem" }}>
                  {signals.map((s, i) => (
                    <div key={i} className="paper-mono" style={{ fontSize: "0.55rem", color: "var(--ink-soft)", lineHeight: 1.6 }}>
                      [{s.method}] {s.domain}/{s.signal_key} | {s.polarity} | s={s.strength.toFixed(2)} c={s.confidence.toFixed(2)}
                      {s.evidence && ` | "${s.evidence.slice(0, 60)}"`}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ═══ 操作按钮 ─── */}
      <div className="flex flex-wrap gap-2 items-center" style={{ borderTop: "1px solid var(--rule)", paddingTop: "0.6rem" }}>
        <button onClick={handleSave}
          className={`paper-btn-ghost ${saved ? "opacity-50" : ""}`} style={{ fontSize: "0.7rem" }}>
          {saved ? "已保存" : "保存报告"}
        </button>
        <button className="paper-btn-ghost" style={{ fontSize: "0.7rem" }}>
          继续追问
        </button>
        <button onClick={() => window.print()}
          className="paper-btn-ghost" style={{ fontSize: "0.7rem" }}>
          导出 PDF
        </button>
        <span className="paper-source" style={{ marginLeft: "auto", fontSize: "0.58rem" }}>
          出生信息仅用于本次分析 · 报告仅存本地
        </span>
      </div>

      {/* ── 错误 ── */}
      {result.errors.length > 0 && (
        <div className="paper-error">
          <div style={{ fontWeight: 600, marginBottom: "0.2rem" }}>部分术法返回错误：</div>
          {result.errors.map((e, i) => (
            <div key={i} style={{ fontSize: "0.6rem" }}>· {METHOD_LABELS_ZH[e.method] || e.method}: {e.error}</div>
          ))}
        </div>
      )}
    </div>
  );
}
