/** ReadingReport — 12 术法聚合解读报告展示
 *
 * RPT-UI-001: 接收 ReadingResult 渲染
 * RPT-UI-002: 一句话结论（headline）顶部突出
 * RPT-UI-003: 综合评分 0-100
 * RPT-UI-004: 可信等级 low/medium/medium_high/high
 * RPT-UI-005: 多法共识列表
 * RPT-UI-006: 多法冲突列表
 * RPT-UI-007: 风险提醒列表
 * RPT-UI-008: 时间窗口
 * RPT-UI-009: 行动建议列表
 * RPT-UI-010: 12 法摘要完整渲染
 * RPT-UI-011: 原始盘面折叠展示
 * RPT-UI-012: 三档报告切换
 * RPT-UI-013: 解锁完整报告按钮（UI 占位）
 * RPT-UI-014: 继续追问按钮（UI 占位）
 * RPT-UI-015: 导出 PDF 按钮（UI 占位）
 * RPT-UI-016: 生成分享图按钮（UI 占位）
 */
import { useState, useMemo, useCallback } from "react";
import { COLOR, ErrorBox } from "./ui";
import type { ReadingResult, ReadingDepth, DivinationSignal } from "../lib/types";
import { METHOD_LABELS_ZH } from "../lib/types";
import { saveReadingToHistory, deleteReadingFromHistory } from "../store/readingHistory";

// ── Helpers ────────────────────────────────────────────────────────────────

const CONFIDENCE_COLORS: Record<string, string> = {
  low: COLOR.danger, medium: COLOR.gold, medium_high: COLOR.azure, high: COLOR.ok,
};

const CONFIDENCE_LABELS: Record<string, string> = {
  low: "可信度较低", medium: "参考可信", medium_high: "较可信", high: "高度可信",
};

const SEVERITY_ICON: Record<string, string> = { low: "🟡", medium: "🟠", high: "🔴" };

const POLARITY_EMOJI: Record<string, string> = {
  positive: "✅", negative: "⚠", neutral: "➖", mixed: "🔄",
};

function ScoreBar({ score }: { score: number }) {
  const barLen = 30;
  const filled = Math.round((score / 100) * barLen);
  const color = score >= 70 ? COLOR.ok : score >= 50 ? COLOR.gold : score >= 35 ? COLOR.goldDim : COLOR.danger;
  return (
    <div className="flex items-center gap-3">
      <span className="text-3xl font-bold font-display" style={{ color }}>{score}</span>
      <span className="text-xs" style={{ color: COLOR.muted }}>/100</span>
      <div className="flex-1 ml-2">
        <div className="flex rounded-full overflow-hidden h-2.5" style={{ background: "rgba(255,255,255,0.06)" }}>
          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, background: color }} />
        </div>
      </div>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-display flex items-center gap-2" style={{ color: COLOR.goldBright }}>
        {icon} {title}
      </h3>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function MethodSignalRow({ signal: s }: { signal: DivinationSignal }) {
  return (
    <div className="flex items-center gap-2 text-xs py-1.5 px-2.5 rounded" style={{ background: "rgba(22,27,34,0.3)" }}>
      <span>{POLARITY_EMOJI[s.polarity] || "➖"}</span>
      <span className="font-semibold" style={{ color: COLOR.ink, minWidth: 70 }}>
        {METHOD_LABELS_ZH[s.method] || s.method}
      </span>
      <span style={{ color: COLOR.inkSoft }}>{s.signal_key}</span>
      <div className="flex-1" />
      <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
        background: s.polarity === "positive" ? "rgba(90,164,105,0.15)" :
                    s.polarity === "negative" ? "rgba(200,85,61,0.15)" : "rgba(138,143,152,0.1)",
        color: s.polarity === "positive" ? COLOR.ok :
               s.polarity === "negative" ? COLOR.danger : COLOR.muted,
      }}>{s.polarity}</span>
      <span className="text-[10px]" style={{ color: COLOR.muted }}>
        强度 {s.strength.toFixed(2)} · 置信 {s.confidence.toFixed(2)}
      </span>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

export interface ReadingReportViewProps {
  result: ReadingResult;
}

export function ReadingReportView({ result }: ReadingReportViewProps) {
  const [activeTier, setActiveTier] = useState<ReadingDepth>("standard");
  const [showRawSignals, setShowRawSignals] = useState(false);
  const [saved, setSaved] = useState(false);

  const { validation, report, signals } = result;

  // EXP-001: Save to history
  const handleSave = useCallback(() => {
    try {
      saveReadingToHistory(result);
      setSaved(true);
    } catch { /* localStorage full */ }
  }, [result]);

  // Method summary: strongest signal per method
  const methodSummary = useMemo(() => {
    const map = new Map<string, DivinationSignal>();
    for (const s of signals) {
      const existing = map.get(s.method);
      if (!existing || s.strength > existing.strength) map.set(s.method, s);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [signals]);

  // Signal heatmap data
  const domainHeat = useMemo(() => {
    const h: Record<string, { pos: number; neg: number; count: number }> = {};
    for (const s of signals) {
      h[s.domain] = h[s.domain] || { pos: 0, neg: 0, count: 0 };
      h[s.domain].count++;
      if (s.polarity === "positive") h[s.domain].pos += s.strength;
      else if (s.polarity === "negative") h[s.domain].neg += s.strength;
    }
    return Object.entries(h).sort(([, a], [, b]) => b.count - a.count);
  }, [signals]);

  const reportText = report[activeTier];
  const isPremium = activeTier === "premium";

  return (
    <div className="space-y-6">
      {/* ── Header card ── */}
      <div className="rounded-2xl border p-6 sm:p-8 relative overflow-hidden" style={{
        background: `linear-gradient(150deg, rgba(22,27,34,0.95) 0%, rgba(12,16,24,0.98) 100%)`,
        borderColor: COLOR.line,
      }}>
        {/* Background glow */}
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[400px] h-[120px] pointer-events-none"
          style={{ background: `radial-gradient(ellipse at center, rgba(201,162,75,0.06) 0%, transparent 70%)` }} />

        <div className="relative">
          {/* Session info */}
          <div className="flex items-center gap-2 mb-3 text-[10px]" style={{ color: COLOR.muted }}>
            <span className="px-2 py-0.5 rounded" style={{ background: "rgba(201,162,75,0.08)", border: `1px solid ${COLOR.goldDim}40`, color: COLOR.goldDim }}>
              ID: {result.session_id}
            </span>
            <span>{result.methods_used.length} 术法 · {result.signals.length} 信号</span>
            <span>{result.elapsed_ms}ms</span>
          </div>

          {/* RPT-UI-002: Headline */}
          <h2 className="text-lg sm:text-xl font-display leading-relaxed mb-4" style={{ color: COLOR.ink }}>
            {report.free.split("\n").find(l => l.startsWith(">"))?.replace(/^>\s*/, "") || "综合分析完成"}
          </h2>

          {/* RPT-UI-003: Score + RPT-UI-004: Confidence */}
          <div className="flex flex-wrap items-center gap-6">
            <ScoreBar score={validation.overall_score} />
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>可信等级</span>
              <span className="px-3 py-1 rounded-full text-xs font-semibold" style={{
                background: `${CONFIDENCE_COLORS[validation.confidence_level]}20`,
                color: CONFIDENCE_COLORS[validation.confidence_level],
                border: `1px solid ${CONFIDENCE_COLORS[validation.confidence_level]}40`,
              }}>
                {CONFIDENCE_LABELS[validation.confidence_level] || validation.confidence_level}
              </span>
            </div>
          </div>

          {/* Method badges */}
          <div className="flex flex-wrap gap-1.5 mt-4">
            {result.methods_used.map((m) => (
              <span key={m} className="text-[9px] px-2 py-0.5 rounded" style={{
                background: "rgba(201,162,75,0.06)", color: COLOR.goldDim, border: `1px solid ${COLOR.lineSoft}`,
              }}>
                {METHOD_LABELS_ZH[m] || m}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── SAFE-002~004: Safety downgrade banners ── */}
      {result.safety_downgrades && result.safety_downgrades.length > 0 && (
        <div className="space-y-2">
          {result.safety_downgrades.map((msg, i) => (
            <div key={i} className="p-3 rounded-lg border text-xs flex items-start gap-2" style={{
              borderColor: `${COLOR.goldDim}60`, background: "rgba(201,162,75,0.06)", color: COLOR.inkSoft,
            }}>
              <span>⚠️</span>
              <span>{msg}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── SAFE-007: Privacy notice ── */}
      <div className="text-[10px] flex items-center gap-1" style={{ color: COLOR.muted }}>
        🔒 您的出生信息仅用于本次分析，历史报告仅保存在本地浏览器中
      </div>

      {/* ── Tier switch (RPT-UI-012) ── */}
      <div className="flex rounded-xl border overflow-hidden" style={{ borderColor: COLOR.line }}>
        {(["free", "standard", "premium"] as ReadingDepth[]).map((tier) => (
          <button key={tier} onClick={() => setActiveTier(tier)}
            className="flex-1 py-2.5 text-xs font-semibold transition"
            style={{
              background: activeTier === tier ? "rgba(201,162,75,0.1)" : "transparent",
              color: activeTier === tier ? COLOR.goldBright : COLOR.muted,
              borderRight: tier !== "premium" ? `1px solid ${COLOR.lineSoft}` : "none",
            }}>
            {{ free: "🆓 免费版", standard: "📋 标准版", premium: "👑 深度版" }[tier]}
          </button>
        ))}
      </div>

      {/* ── RPT-UI-013: Unlock prompt ── */}
      {activeTier === "free" && (
        <div className="p-4 rounded-xl border text-center space-y-2" style={{
          borderColor: COLOR.goldDim, background: "rgba(201,162,75,0.05)",
        }}>
          <p className="text-xs" style={{ color: COLOR.inkSoft }}>
            以上为免费版速览。切换至「标准版」查看 12 术法详细依据、多法共识与冲突分析。
          </p>
          <button onClick={() => setActiveTier("standard")}
            className="text-xs px-4 py-1.5 rounded-lg transition" style={{
              background: `linear-gradient(135deg, ${COLOR.gold} 0%, ${COLOR.goldBright} 100%)`,
              color: "#0a0a0a",
            }}>
            解锁标准报告 →
          </button>
        </div>
      )}

      {/* ── Consensus (RPT-UI-005) ── */}
      {validation.consensus.length > 0 && (
        <Section title="多术法共识" icon="🤝">
          {validation.consensus.map((c, i) => (
            <div key={i} className="p-4 rounded-xl border" style={{ borderColor: `${COLOR.ok}30`, background: "rgba(90,164,105,0.05)" }}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm font-semibold" style={{ color: COLOR.ok }}>{c.theme}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "rgba(90,164,105,0.15)", color: COLOR.ok }}>
                  共识强度 {c.weight_strength}/100
                </span>
              </div>
              <p className="text-xs mb-1.5" style={{ color: COLOR.inkSoft }}>{c.explanation}</p>
              <div className="flex flex-wrap gap-1">
                {c.supporting_methods.map((m) => (
                  <span key={m} className="text-[9px] px-1.5 py-0.5 rounded" style={{
                    background: "rgba(90,164,105,0.1)", color: COLOR.ok,
                  }}>{METHOD_LABELS_ZH[m] || m}</span>
                ))}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* ── Conflicts (RPT-UI-006) ── */}
      {validation.conflicts.length > 0 && (
        <Section title="术法分歧 · 需关注" icon="⚡">
          {validation.conflicts.map((c, i) => (
            <div key={i} className="p-4 rounded-xl border" style={{
              borderColor: c.severity === "high" ? `${COLOR.danger}50` : c.severity === "medium" ? `${COLOR.gold}40` : `${COLOR.lineSoft}`,
              background: c.severity === "high" ? "rgba(200,85,61,0.06)" : "rgba(22,27,34,0.2)",
            }}>
              <div className="flex items-center gap-2 mb-1.5">
                <span>{SEVERITY_ICON[c.severity]}</span>
                <span className="text-sm font-semibold" style={{ color: COLOR.ink }}>{c.domain}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                  background: c.severity === "high" ? "rgba(200,85,61,0.15)" :
                              c.severity === "medium" ? "rgba(201,162,75,0.15)" :
                              "rgba(138,143,152,0.1)",
                  color: c.severity === "high" ? COLOR.danger : c.severity === "medium" ? COLOR.gold : COLOR.muted,
                }}>
                  {{ low: "轻度分歧", medium: "中度分歧", high: "严重分歧" }[c.severity]}
                </span>
              </div>
              <p className="text-xs mb-2" style={{ color: COLOR.inkSoft }}>{c.conflict_explanation}</p>
              <div className="flex flex-wrap gap-1.5 mb-1.5">
                <span className="text-[9px]" style={{ color: COLOR.ok }}>
                  正向：{c.positive_methods.map(m => METHOD_LABELS_ZH[m] || m).join(" · ")}
                </span>
                <span className="text-[9px]" style={{ color: COLOR.muted }}>|</span>
                <span className="text-[9px]" style={{ color: COLOR.danger }}>
                  负向：{c.negative_methods.map(m => METHOD_LABELS_ZH[m] || m).join(" · ")}
                </span>
              </div>
              {c.resolution && (
                <p className="text-xs" style={{ color: COLOR.gold }}>
                  💡 调和思路：{c.resolution}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* ── PAY-005: Premium unlock overlay ── */}
      {isPremium && !result.is_unlocked_premium && (
        <div className="relative">
          {/* Premium content — blurred */}
          <div className="filter blur-sm opacity-40 pointer-events-none">
            {domainHeat.length > 0 && (
              <Section title="信号强度热力图" icon="🔥">
                <div className="space-y-1.5">
                  {domainHeat.slice(0, 3).map(([domain, h]) => (
                    <div key={domain} className="flex items-center gap-2 text-xs">
                      <span style={{ color: COLOR.inkSoft, minWidth: 80 }}>{domain}</span>
                      <div className="flex-1 h-3 rounded-full" style={{ background: "rgba(255,255,255,0.05)" }} />
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>
          {/* Unlock CTA overlay (PAY-006, PAY-007) */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-6 rounded-2xl border space-y-3" style={{
              background: "rgba(8,10,15,0.92)", borderColor: COLOR.gold, backdropFilter: "blur(8px)",
            }}>
              <div className="text-3xl">👑</div>
              <h3 className="text-lg font-display" style={{ color: COLOR.goldBright }}>解锁深度报告</h3>
              <p className="text-xs max-w-xs" style={{ color: COLOR.inkSoft }}>
                深度报告包含信号热力图、术法贡献度排名、风险深度拆解、时间窗口分析、追问上下文等。
              </p>
              <button className="px-6 py-2 rounded-xl text-sm font-semibold transition" style={{
                background: `linear-gradient(135deg, ${COLOR.gold} 0%, ${COLOR.goldBright} 100%)`,
                color: "#0a0a0a",
              }}>
                解锁深度报告 →
              </button>
              <p className="text-[9px]" style={{ color: COLOR.muted }}>即将支持 Stripe / 微信 / 支付宝</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Premium: Heatmap (unlocked) ── */}
      {isPremium && result.is_unlocked_premium && domainHeat.length > 0 && (
        <Section title="信号强度热力图" icon="🔥">
          <div className="space-y-1.5">
            {domainHeat.map(([domain, h]) => {
              const total = Math.max(1, h.pos + h.neg);
              const posW = Math.round((h.pos / total) * 100);
              const negW = Math.round((h.neg / total) * 100);
              return (
                <div key={domain} className="flex items-center gap-2 text-xs">
                  <span style={{ color: COLOR.inkSoft, minWidth: 80 }}>{domain}</span>
                  <span className="text-[10px]" style={{ color: COLOR.muted }}>({h.count}条)</span>
                  <div className="flex-1 h-3 rounded-full overflow-hidden flex" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <div style={{ width: `${posW}%`, background: COLOR.ok, transition: "width 0.5s" }} />
                    <div style={{ width: `${negW}%`, background: COLOR.danger, transition: "width 0.5s" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* ── 12 Method Summary (RPT-UI-010) ── */}
      {(activeTier !== "free") && (
        <Section title={`${result.methods_used.length} 术法依据摘要`} icon="📜">
          <div className="space-y-1">
            {methodSummary.map(([method, s]) => (
              <MethodSignalRow key={method} signal={s} />
            ))}
            {/* Missing methods */}
            {result.methods_used.filter(m => !methodSummary.find(([name]) => name === m)).map(m => (
              <div key={m} className="text-xs py-1.5 px-2.5" style={{ color: COLOR.muted }}>
                ⬜ {METHOD_LABELS_ZH[m] || m}：未产生有效信号
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Risks (RPT-UI-007) ── */}
      {validation.risks.length > 0 && (
        <Section title="风险提醒" icon="⚠️">
          <div className="p-4 rounded-xl border space-y-1.5" style={{ borderColor: `${COLOR.danger}30`, background: "rgba(200,85,61,0.04)" }}>
            {validation.risks.map((r, i) => (
              <div key={i} className="text-xs flex items-start gap-2" style={{ color: COLOR.inkSoft }}>
                <span style={{ color: COLOR.danger }}>•</span>
                <span>{r}</span>
              </div>
            ))}
          </div>
          <p className="text-[10px]" style={{ color: COLOR.muted }}>
            *以上风险提示基于术法信号的统计分析，仅供参考，不构成确定性判断。
          </p>
        </Section>
      )}

      {/* ── Action Advice (RPT-UI-009) ── */}
      {validation.action_advice.length > 0 && (
        <Section title="行动建议" icon="💡">
          <div className="space-y-1.5">
            {validation.action_advice.map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-xs p-2.5 rounded-lg"
                style={{ background: "rgba(22,27,34,0.4)", color: COLOR.inkSoft }}>
                <span className="font-semibold" style={{ color: COLOR.goldBright }}>{i + 1}.</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Timing (RPT-UI-008) ── */}
      {validation.timing && (
        <Section title="时间窗口" icon="⏰">
          <div className="p-4 rounded-xl border space-y-2" style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.3)" }}>
            <div className="flex gap-4 text-xs">
              <span style={{ color: COLOR.ok }}>短期信号：{validation.timing.short_term_signals || 0}条</span>
              <span style={{ color: COLOR.gold }}>中期信号：{validation.timing.medium_term_signals || 0}条</span>
              <span style={{ color: COLOR.azure }}>长期信号：{validation.timing.long_term_signals || 0}条</span>
            </div>
            <p className="text-xs" style={{ color: COLOR.inkSoft }}>{validation.timing.summary || ""}</p>
          </div>
        </Section>
      )}

      {/* ── Raw signals collapsible (RPT-UI-011) ── */}
      <div>
        <button onClick={() => setShowRawSignals(!showRawSignals)}
          className="text-xs flex items-center gap-2 transition" style={{ color: COLOR.muted }}>
          <span>{showRawSignals ? "▼" : "▶"}</span>
          原始信号详情（{signals.length} 条）
        </button>
        {showRawSignals && (
          <div className="mt-2 p-4 rounded-xl border space-y-1 max-h-96 overflow-y-auto"
            style={{ borderColor: COLOR.lineSoft, background: "rgba(8,10,15,0.6)" }}>
            {signals.map((s, i) => (
              <div key={i} className="text-[10px] py-1" style={{ color: COLOR.muted, fontFamily: "monospace" }}>
                [{s.method}] {s.domain}/{s.signal_key} | {s.polarity} | str={s.strength.toFixed(2)} conf={s.confidence.toFixed(2)}
                {s.evidence && ` | "${s.evidence.slice(0, 80)}"`}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── RPT-UI-014/015/016 + EXP actions ── */}
      <div className="flex flex-wrap gap-3 pt-2">
        {/* EXP-001: Save to history */}
        <button onClick={handleSave}
          className={`text-xs px-4 py-2 rounded-lg border transition ${saved ? "opacity-50" : ""}`}
          style={{
            borderColor: saved ? COLOR.ok : COLOR.goldDim,
            color: saved ? COLOR.ok : COLOR.goldBright,
            background: saved ? "rgba(90,164,105,0.08)" : "rgba(201,162,75,0.05)",
          }}>
          {saved ? "✅ 已保存" : "💾 保存报告"}
        </button>
        <button className="text-xs px-4 py-2 rounded-lg border transition"
          style={{ borderColor: COLOR.goldDim, color: COLOR.goldBright, background: "rgba(201,162,75,0.05)" }}>
          💬 继续追问
        </button>
        {/* EXP-003: PDF export */}
        <button onClick={() => window.print()}
          className="text-xs px-4 py-2 rounded-lg border transition"
          style={{ borderColor: COLOR.azureDim, color: COLOR.azure, background: "rgba(91,141,239,0.05)" }}>
          📄 导出 PDF
        </button>
        {/* EXP-004: Share image */}
        <button className="text-xs px-4 py-2 rounded-lg border transition"
          style={{ borderColor: COLOR.jadeDim, color: COLOR.jade, background: "rgba(79,179,160,0.05)" }}>
          📤 生成分享图
        </button>
      </div>

      {/* ── Full report markdown ── */}
      <div className="rounded-xl border p-6" style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.4)" }}>
        <div className="prose prose-invert prose-sm max-w-none" style={{ color: COLOR.inkSoft }}
          dangerouslySetInnerHTML={{ __html: simpleMarkdownToHtml(reportText) }} />
      </div>

      {/* ── Disclaimer ── */}
      <div className="p-4 rounded-xl border text-xs space-y-1" style={{
        borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.3)", color: COLOR.muted,
      }}>
        <div className="font-semibold" style={{ color: COLOR.inkSoft }}>📜 免责声明</div>
        <p>{result.disclaimer}</p>
      </div>

      {/* ── Errors (if any) ── */}
      {result.errors.length > 0 && (
        <ErrorBox>
          <div className="text-xs font-semibold mb-1">部分术法返回错误（已使用备用信号）：</div>
          {result.errors.map((e, i) => (
            <div key={i} className="text-[10px]">• {METHOD_LABELS_ZH[e.method] || e.method}: {e.error}</div>
          ))}
        </ErrorBox>
      )}
    </div>
  );
}

// ── Simple markdown-to-HTML for report rendering ───────────────────────────

function simpleMarkdownToHtml(text: string): string {
  let html = text
    // headers
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-semibold mt-4 mb-2" style="color: var(--gold-bright)">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-base font-semibold mt-5 mb-2" style="color: var(--gold)">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-lg font-bold mt-6 mb-3" style="color: var(--gold-bright)">$1</h1>')
    // bold / italic
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color: var(--ink)">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // lists
    .replace(/^- (.+)$/gm, '<li style="margin-left:1em;color:var(--ink-soft)">• $1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li style="margin-left:1em;color:var(--ink-soft)">$1. $2</li>')
    // horizontal rule
    .replace(/^---$/gm, '<hr class="my-3" style="border-color:var(--line-soft)">')
    // blockquote
    .replace(/^> (.+)$/gm, '<blockquote class="border-l-2 pl-3 my-2" style="border-color:var(--gold-dim);color:var(--ink-soft)">$1</blockquote>')
    // paragraphs (double newline)
    .replace(/\n\n/g, '</p><p class="my-1">')
    // line breaks
    .replace(/\n/g, '<br/>');

  html = '<p class="my-1">' + html + '</p>';
  return html;
}
