/** ReadingHistory — 已保存的报告历史（「古籍×仪器」纸墨风格） */
import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { loadHistory, deleteReadingFromHistory, clearHistory, type HistoryEntry } from "../store/readingHistory";
import { METHOD_LABELS_ZH } from "../lib/types";

const GOAL_LABELS: Record<string, string> = {
  general_life: "本命格局", career: "事业工作", wealth: "财运",
  relationship: "感情姻缘", compatibility: "合盘分析", yearly: "年度运势",
  monthly: "月运", daily: "日运", decision: "重大决策", timing: "时机分析",
  fengshui: "风水调理", health_reflection: "健康自省", crisis: "安全响应",
};

// 整体基调(对齐后端 _tone_level 与 readingHistory.computeTone)
const TONE_META: Record<string, { zh: string; color: string }> = {
  very_positive: { zh: "大吉", color: "var(--verdigris)" },
  positive:      { zh: "小吉", color: "var(--verdigris)" },
  mixed:         { zh: "参半", color: "var(--indigo)" },
  cautious:      { zh: "当慎", color: "var(--cinnabar-dim)" },
  negative:      { zh: "有险", color: "var(--cinnabar)" },
  neutral:       { zh: "平和", color: "var(--ink-soft)" },
};

function ToneChip({ tone }: { tone: string }) {
  const meta = TONE_META[tone] || TONE_META.neutral;
  return (
    <span style={{
      display: "inline-block",
      padding: "0.1rem 0.45rem",
      border: `1px solid ${meta.color}`,
      borderRadius: "2px",
      fontSize: "0.7rem", fontWeight: 700, color: meta.color,
      fontFamily: "'Noto Serif SC', serif",
    }}>{meta.zh}</span>
  );
}

export function ReadingHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleDelete = useCallback((id: string) => {
    deleteReadingFromHistory(id);
    setHistory((prev) => prev.filter((h) => h.id !== id));
    if (selectedId === id) setSelectedId(null);
  }, [selectedId]);

  const handleClear = useCallback(() => {
    if (confirm("确定清空所有历史报告？此操作不可撤销。")) {
      clearHistory(); setHistory([]); setSelectedId(null);
    }
  }, []);

  const selectedEntry = selectedId ? history.find((h) => h.id === selectedId) : null;

  return (
    <div className="space-y-5 max-w-5xl mx-auto">
      <section className="flex items-center justify-between">
        <h1 className="paper-title"><span className="stamp" />历史报告</h1>
        {history.length > 0 && (
          <button onClick={handleClear} className="paper-btn-ghost" style={{ fontSize: "0.72rem", color: "var(--cinnabar)" }}>
            清空全部
          </button>
        )}
      </section>
      <p style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "-0.75rem" }}>
        已保存 {history.length} 份报告（最多 50 份，保存在本地浏览器中）
      </p>

      {history.length === 0 ? (
        <div className="paper-empty" style={{ padding: "2.5rem 0" }}>
          <p style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>暂无保存的历史报告</p>
          <p style={{ fontSize: "0.78rem", marginBottom: "1rem" }}>在 12 法合参页面完成解读后，点击「保存报告」即可在此查看</p>
          <Link to="/reading" className="paper-btn">开始提问</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="space-y-1.5 lg:col-span-1 max-h-[70vh] overflow-y-auto">
            {history.map((entry) => (
              <button key={entry.id} onClick={() => setSelectedId(entry.id)}
                className="paper-grid-cell w-full text-left" style={{
                  padding: "0.5rem 0.75rem", cursor: "pointer",
                  borderColor: selectedId === entry.id ? "var(--cinnabar)" : "var(--rule)",
                }}>
                <div className="flex items-center justify-between" style={{ marginBottom: "0.15rem" }}>
                  <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                    {GOAL_LABELS[entry.goal] || entry.goalLabel || entry.goal}
                  </span>
                  <ToneChip tone={entry.tone} />
                </div>
                <p style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }} className="truncate">{entry.question.slice(0, 60) || "无问题"}</p>
                <div className="flex items-center justify-between" style={{ marginTop: "0.25rem" }}>
                  <span style={{ fontSize: "0.55rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
                    {new Date(entry.savedAt).toLocaleString()}
                  </span>
                  <span style={{ fontSize: "0.55rem", color: "var(--ink-soft)", opacity: 0.5, fontFamily: "'JetBrains Mono', monospace" }}>{entry.id}</span>
                </div>
              </button>
            ))}
          </div>

          <div className="lg:col-span-2">
            {selectedEntry ? (
              <div className="paper-frame space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: "var(--ink)" }}>
                      {GOAL_LABELS[selectedEntry.goal] || selectedEntry.goalLabel}
                    </h3>
                    <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>{selectedEntry.question}</p>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/reading?historyId=${selectedEntry.id}`} className="paper-btn-ghost" style={{ fontSize: "0.62rem", padding: "0.25rem 0.6rem" }}>
                      重新打开
                    </Link>
                    <button onClick={() => handleDelete(selectedEntry.id)} className="paper-btn-ghost" style={{ fontSize: "0.62rem", padding: "0.25rem 0.6rem", color: "var(--cinnabar)" }}>
                      删除
                    </button>
                  </div>
                </div>

                <div className="paper-grid-cell space-y-1.5" style={{ padding: "0.6rem 0.85rem", fontSize: "0.72rem", maxHeight: "24rem", overflowY: "auto" }}>
                  <div className="flex gap-3 flex-wrap" style={{ color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
                    <span>基调: <ToneChip tone={selectedEntry.tone} /></span>
                    <span>方法: <strong>{selectedEntry.result.methods_used?.length || 0}/12</strong></span>
                  </div>

                  {selectedEntry.result.consensus && selectedEntry.result.consensus.length > 0 && (
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--verdigris)", fontFamily: "'Noto Serif SC', serif" }}>多法共识:</div>
                      {selectedEntry.result.consensus.slice(0, 3).map((c, i) => (
                        <div key={i} style={{ paddingLeft: "0.5rem" }}>· {c.theme}</div>
                      ))}
                    </div>
                  )}

                  {selectedEntry.result.validation?.risks && selectedEntry.result.validation.risks.length > 0 && (
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>风险:</div>
                      {selectedEntry.result.validation.risks.slice(0, 3).map((r, i) => (
                        <div key={i} style={{ paddingLeft: "0.5rem" }}>· {r}</div>
                      ))}
                    </div>
                  )}

                  <div className="paper-hr" />
                  <div style={{ fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>报告摘要:</div>
                  <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                    {selectedEntry.result.report?.free?.slice(0, 500) || "无摘要"}
                  </div>

                  <div style={{ color: "var(--ink-soft)", opacity: 0.6 }}>
                    {selectedEntry.result.disclaimer?.slice(0, 200) || ""}
                  </div>
                </div>

                <button onClick={() => window.print()} className="paper-btn-ghost" style={{ fontSize: "0.72rem" }}>
                  导出 PDF
                </button>
              </div>
            ) : (
              <div className="paper-empty" style={{ padding: "3rem 0", minHeight: "300px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <p style={{ fontSize: "0.88rem", color: "var(--ink-soft)" }}>选择左侧的报告查看详情</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
