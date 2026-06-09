/** ReadingHistory — 已保存的报告历史 (EXP-002~008)
 *
 * EXP-002: 用户可以查看历史报告
 * EXP-007: 历史报告可重新打开
 * EXP-008: 历史报告可删除
 */
import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { COLOR } from "../components/ui";
import { loadHistory, deleteReadingFromHistory, clearHistory, type HistoryEntry } from "../store/readingHistory";
import { METHOD_LABELS_ZH } from "../lib/types";

const GOAL_LABELS: Record<string, string> = {
  general_life: "本命格局", career: "事业工作", wealth: "财运",
  relationship: "感情姻缘", compatibility: "合盘分析", yearly: "年度运势",
  monthly: "月运", daily: "日运", decision: "重大决策", timing: "时机分析",
  fengshui: "风水调理", health_reflection: "健康自省", crisis: "安全响应",
};

function ScoreBarSmall({ score }: { score: number }) {
  const color = score >= 70 ? COLOR.ok : score >= 50 ? COLOR.gold : score >= 35 ? COLOR.goldDim : COLOR.danger;
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-sm font-bold" style={{ color }}>{score}</span>
      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
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
      clearHistory();
      setHistory([]);
      setSelectedId(null);
    }
  }, []);

  const selectedEntry = selectedId ? history.find((h) => h.id === selectedId) : null;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <section className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display" style={{ color: COLOR.ink }}>📋 历史报告</h1>
          <p className="text-xs mt-1" style={{ color: COLOR.muted }}>
            已保存 {history.length} 份报告（最多 50 份，保存在本地浏览器中）
          </p>
        </div>
        {history.length > 0 && (
          <button onClick={handleClear}
            className="text-xs px-3 py-1.5 rounded-lg border transition"
            style={{ borderColor: `${COLOR.danger}40`, color: COLOR.danger, background: "rgba(200,85,61,0.05)" }}>
            清空全部
          </button>
        )}
      </section>

      {history.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border" style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.3)" }}>
          <div className="text-4xl mb-3">📭</div>
          <p className="text-sm" style={{ color: COLOR.inkSoft }}>暂无保存的历史报告</p>
          <p className="text-xs mt-1" style={{ color: COLOR.muted }}>
            在 12 法合参页面完成解读后，点击「保存报告」即可在此查看
          </p>
          <Link to="/reading" className="inline-block mt-4 text-sm px-4 py-2 rounded-lg transition"
            style={{ background: `linear-gradient(135deg, ${COLOR.gold} 0%, ${COLOR.goldBright} 100%)`, color: "#0a0a0a" }}>
            🔮 开始提问
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* List */}
          <div className="space-y-2 lg:col-span-1 max-h-[70vh] overflow-y-auto">
            {history.map((entry) => (
              <button key={entry.id}
                onClick={() => setSelectedId(entry.id)}
                className={`w-full text-left p-3 rounded-xl border transition ${selectedId === entry.id ? "ring-1" : ""}`}
                style={{
                  borderColor: selectedId === entry.id ? COLOR.gold : COLOR.lineSoft,
                  background: selectedId === entry.id ? "rgba(201,162,75,0.06)" : "rgba(22,27,34,0.3)",
                }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold" style={{ color: COLOR.ink }}>
                    {GOAL_LABELS[entry.goal] || entry.goalLabel || entry.goal}
                  </span>
                  <ScoreBarSmall score={entry.score} />
                </div>
                <p className="text-[10px] truncate" style={{ color: COLOR.muted }}>
                  {entry.question.slice(0, 60) || "无问题"}
                </p>
                <div className="flex items-center justify-between mt-1.5">
                  <span className="text-[9px]" style={{ color: COLOR.muted }}>
                    {new Date(entry.savedAt).toLocaleString()}
                  </span>
                  <span className="text-[9px]" style={{ color: COLOR.goldDim }}>{entry.id}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Detail */}
          <div className="lg:col-span-2">
            {selectedEntry ? (
              <div className="rounded-2xl border p-5 space-y-4" style={{ borderColor: COLOR.line, background: "rgba(22,27,34,0.4)" }}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-display" style={{ color: COLOR.goldBright }}>
                      {GOAL_LABELS[selectedEntry.goal] || selectedEntry.goalLabel}
                    </h3>
                    <p className="text-xs mt-0.5" style={{ color: COLOR.inkSoft }}>{selectedEntry.question}</p>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/reading?historyId=${selectedEntry.id}`}
                      className="text-[10px] px-3 py-1.5 rounded-lg transition"
                      style={{ border: `1px solid ${COLOR.goldDim}`, color: COLOR.goldBright }}>
                      重新打开
                    </Link>
                    <button onClick={() => handleDelete(selectedEntry.id)}
                      className="text-[10px] px-3 py-1.5 rounded-lg transition"
                      style={{ border: `1px solid ${COLOR.danger}40`, color: COLOR.danger }}>
                      删除
                    </button>
                  </div>
                </div>

                {/* Mini report preview */}
                <div className="p-4 rounded-xl border text-xs space-y-2 max-h-96 overflow-y-auto"
                  style={{ borderColor: COLOR.lineSoft, background: "rgba(8,10,15,0.4)", color: COLOR.inkSoft }}>
                  <div className="flex gap-4 mb-2">
                    <span>评分: <strong style={{ color: COLOR.gold }}>{selectedEntry.score}/100</strong></span>
                    <span>置信度: <strong style={{ color: COLOR.azure }}>{selectedEntry.result.validation?.confidence_level || "medium"}</strong></span>
                    <span>方法: <strong>{selectedEntry.result.methods_used?.length || 0}/12</strong></span>
                  </div>

                  {/* Consensus */}
                  {selectedEntry.result.consensus && selectedEntry.result.consensus.length > 0 && (
                    <div>
                      <div className="font-semibold" style={{ color: COLOR.ok }}>多法共识:</div>
                      {selectedEntry.result.consensus.slice(0, 3).map((c, i) => (
                        <div key={i} className="ml-2">• {c.theme}</div>
                      ))}
                    </div>
                  )}

                  {/* Risks */}
                  {selectedEntry.result.validation?.risks && selectedEntry.result.validation.risks.length > 0 && (
                    <div>
                      <div className="font-semibold" style={{ color: COLOR.danger }}>风险:</div>
                      {selectedEntry.result.validation.risks.slice(0, 3).map((r, i) => (
                        <div key={i} className="ml-2">• {r}</div>
                      ))}
                    </div>
                  )}

                  {/* Free report snippet */}
                  <div className="font-semibold" style={{ color: COLOR.goldDim }}>报告摘要:</div>
                  <div style={{ whiteSpace: "pre-wrap" }}>
                    {selectedEntry.result.report?.free?.slice(0, 500) || "无摘要"}
                  </div>

                  {/* Disclaimer */}
                  <div style={{ color: COLOR.muted }}>
                    {selectedEntry.result.disclaimer?.slice(0, 200) || ""}
                  </div>
                </div>

                {/* Download button */}
                <button onClick={() => window.print()}
                  className="text-xs px-3 py-1.5 rounded-lg border transition"
                  style={{ borderColor: COLOR.azureDim, color: COLOR.azure }}>
                  📄 导出 PDF
                </button>
              </div>
            ) : (
              <div className="p-12 text-center rounded-2xl border flex flex-col items-center justify-center"
                style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.2)", minHeight: 300 }}>
                <div className="text-3xl mb-2">📋</div>
                <p className="text-sm" style={{ color: COLOR.muted }}>选择左侧的报告查看详情</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
