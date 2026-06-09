/** Reading — 12 术法聚合解读主页面（FE-001~011）
 *
 * 从"选术法"转向"选问题"：用户只需输入问题，系统自动调用 12 法
 */
import { useState, useCallback } from "react";
import { COLOR } from "../components/ui";
import { ReadingForm } from "../components/ReadingForm";
import { ReadingReportView } from "../components/ReadingReportView";
import type { ReadingAPIRequest, ReadingResult } from "../lib/types";
import { fetchReading } from "../lib/api";

export function Reading() {
  const [result, setResult] = useState<ReadingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (req: ReadingAPIRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchReading(req);
      setResult(res);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* ── Page Header ── */}
      <section className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] uppercase tracking-[0.3em]" style={{
          background: "rgba(201,162,75,0.08)", border: `1px solid ${COLOR.goldDim}40`, color: COLOR.gold,
        }}>
          <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: COLOR.goldBright }} />
          12 术法合参
        </div>
        <h1 className="text-2xl sm:text-3xl font-display" style={{ color: COLOR.ink }}>
          一次输入，12 法合参
        </h1>
        <p className="text-sm max-w-lg mx-auto" style={{ color: COLOR.inkSoft }}>
          系统自动调度八字、紫微、奇门、六爻、梅花、风水、八宅、玄空、西方占星、吠陀占星、塔罗、数字命理共 12 种术法，交叉验证给出综合解读。
        </p>
      </section>

      {/* ── Form or Results ── */}
      {result ? (
        <>
          <div className="flex items-center justify-between">
            <button onClick={() => { setResult(null); setError(null); }}
              className="text-xs px-3 py-1.5 rounded-lg border transition" style={{
                borderColor: COLOR.goldDim, color: COLOR.goldBright,
              }}>
              ← 重新提问
            </button>
            <span className="text-[10px]" style={{ color: COLOR.muted }}>
              {result.elapsed_ms}ms · {result.methods_used.length} 法 · {result.signals.length} 信号
            </span>
          </div>
          <ReadingReportView result={result} />
        </>
      ) : (
        <div className="rounded-2xl border p-6 sm:p-8" style={{ borderColor: COLOR.line, background: "rgba(22,27,34,0.4)" }}>
          <ReadingForm onSubmit={handleSubmit} loading={loading} error={error} />
        </div>
      )}

      {/* ── Info: 12 Methods ── */}
      {!result && (
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-center">
          {[
            "八字", "紫微", "奇门", "六爻", "梅花",
            "风水", "八宅", "玄空", "西方占星", "吠陀占星",
            "塔罗", "数字命理",
          ].map((name) => (
            <div key={name} className="p-2 rounded-lg text-[10px]" style={{
              background: "rgba(22,27,34,0.3)", border: `1px solid ${COLOR.lineSoft}`, color: COLOR.muted,
            }}>
              {name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
