// 统一 ChartRenderer:按 method 路由到对应盘面 (P2-7: React.lazy + Suspense 懒加载)
import { lazy, Suspense } from "react";
import type { ChartResult, Method } from "../../lib/types";
import type { CrossValidationResult, PeachBlossomResult, FateModificationPlan } from "../../lib/api";

export { XiaoliurenChart } from "./XiaoliurenChart";

// ── 各盘面组件懒加载 ──
const LazyBaziChart = lazy(() => import("./BaziChart").then((m) => ({ default: m.BaziChart })));
const LazyZiweiChart = lazy(() => import("./ZiweiChart").then((m) => ({ default: m.ZiweiChart })));
const LazyQimenChart = lazy(() => import("./QimenChart").then((m) => ({ default: m.QimenChart })));
const LazyWesternChart = lazy(() => import("./WesternChart").then((m) => ({ default: m.WesternChart })));
const LazyVedicChart = lazy(() => import("./VedicChart").then((m) => ({ default: m.VedicChart })));
const LazyLiuyaoChart = lazy(() => import("./LiyaoChart").then((m) => ({ default: m.LiuyaoChart })));
const LazyMeihuaChart = lazy(() => import("./MeihuaChart").then((m) => ({ default: m.MeihuaChart })));
const LazyChengguChart = lazy(() => import("./ChengguChart").then((m) => ({ default: m.ChengguChart })));
const LazyBazhaiChart = lazy(() => import("./BazhaiChart").then((m) => ({ default: m.BazhaiChart })));
const LazyXuankongChart = lazy(() => import("./XuankongChart").then((m) => ({ default: m.XuankongChart })));
const LazyTarotChart = lazy(() => import("./TarotChart").then((m) => ({ default: m.TarotChart })));
const LazyNumerologyChart = lazy(() => import("./NumerologyChart").then((m) => ({ default: m.NumerologyChart })));
const LazyLenormandChart = lazy(() => import("./LenormandChart").then((m) => ({ default: m.LenormandChart })));
const LazyQianChart = lazy(() => import("./QianChart").then((m) => ({ default: m.QianChart })));
const LazyLiurenChart = lazy(() => import("./LiurenChart").then((m) => ({ default: m.LiurenChart })));
const LazyTiebanChart = lazy(() => import("./TiebanChart").then((m) => ({ default: m.TiebanChart })));

interface ChartRendererProps {
  chart: ChartResult;
  crossValidation?: CrossValidationResult | null;
  peachBlossom?: PeachBlossomResult | null;
  fateModification?: FateModificationPlan | null;
}

/** 统一盘面加载占位 */
function ChartLoadingFallback() {
  return (
    <div className="paper-empty flex items-center justify-center" style={{ minHeight: "12rem" }}>
      <div className="space-y-2 text-center">
        <span className="paper-pulse" style={{ width: "1rem", height: "1rem", display: "inline-block" }} />
        <div style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>排盘中…</div>
      </div>
    </div>
  );
}

export function ChartRenderer({ chart, crossValidation, peachBlossom, fateModification }: ChartRendererProps) {
  const m = chart.method as Method;
  switch (m) {
    case "bazi":
    case "bazi_v2":
      return <Suspense fallback={<ChartLoadingFallback />}><LazyBaziChart chart={chart} crossValidation={crossValidation} peachBlossom={peachBlossom} fateModification={fateModification} /></Suspense>;
    case "ziwei":      return <Suspense fallback={<ChartLoadingFallback />}><LazyZiweiChart chart={chart} /></Suspense>;
    case "qimen":      return <Suspense fallback={<ChartLoadingFallback />}><LazyQimenChart chart={chart} /></Suspense>;
    case "western":    return <Suspense fallback={<ChartLoadingFallback />}><LazyWesternChart chart={chart} /></Suspense>;
    case "vedic":      return <Suspense fallback={<ChartLoadingFallback />}><LazyVedicChart chart={chart} /></Suspense>;
    case "liuyao":     return <Suspense fallback={<ChartLoadingFallback />}><LazyLiuyaoChart chart={chart} /></Suspense>;
    case "meihua":     return <Suspense fallback={<ChartLoadingFallback />}><LazyMeihuaChart chart={chart} /></Suspense>;
    case "chenggu":    return <Suspense fallback={<ChartLoadingFallback />}><LazyChengguChart chart={chart} /></Suspense>;
    case "bazhai":     return <Suspense fallback={<ChartLoadingFallback />}><LazyBazhaiChart chart={chart} /></Suspense>;
    case "xuankong":   return <Suspense fallback={<ChartLoadingFallback />}><LazyXuankongChart chart={chart} /></Suspense>;
    case "tarot":      return <Suspense fallback={<ChartLoadingFallback />}><LazyTarotChart chart={chart} /></Suspense>;
    case "numerology": return <Suspense fallback={<ChartLoadingFallback />}><LazyNumerologyChart chart={chart} /></Suspense>;
    case "lenormand":  return <Suspense fallback={<ChartLoadingFallback />}><LazyLenormandChart chart={chart} /></Suspense>;
    case "qian":       return <Suspense fallback={<ChartLoadingFallback />}><LazyQianChart chart={chart} /></Suspense>;
    case "liuren":     return <Suspense fallback={<ChartLoadingFallback />}><LazyLiurenChart chart={chart} /></Suspense>;
    case "tieban":     return <Suspense fallback={<ChartLoadingFallback />}><LazyTiebanChart chart={chart} /></Suspense>;
    default: return <div className="paper-empty">未知占卜法: {m}</div>;
  }
}
