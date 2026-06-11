/** Reading — 多术法聚合解读（「古籍×仪器」命书风格） */
import { useState, useCallback } from "react";
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
    <div className="space-y-5 max-w-4xl mx-auto">
      {/* Page Header */}
      <section>
        <h1 className="paper-title">
          <span className="stamp" />
          <span>多法合参</span>
          <span className="sub">诸术交叉验证 · 综合命书</span>
        </h1>
        <p style={{
          fontSize: "0.82rem", color: "var(--ink-soft)", lineHeight: 1.8,
          marginTop: "0.5rem", maxWidth: "40rem",
        }}>
          输入一事一问，系统自动调度八字、紫微、奇门、六爻、梅花、风水、八宅、玄空、
          西方占星、吠陀占星、塔罗、数字命理等术法，交叉验证给出综合解读。
        </p>
      </section>

      {/* Form or Results */}
      {result ? (
        <>
          <div className="flex items-center justify-between">
            <button onClick={() => { setResult(null); setError(null); }}
              className="paper-btn-ghost" style={{ fontSize: "0.78rem" }}>
              ← 重新提问
            </button>
            <span style={{ fontSize: "0.65rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              {result.elapsed_ms}ms · {result.methods_used.length} 法 · {result.signals.length} 信号
            </span>
          </div>
          <ReadingReportView result={result} />
        </>
      ) : (
        <div className="paper-frame">
          <ReadingForm onSubmit={handleSubmit} loading={loading} error={error} />
        </div>
      )}
    </div>
  );
}
