// 统一 ChartRenderer:按 method 路由到对应盘面
import type { ChartResult, Method } from "../../lib/types";
import type { CrossValidationResult, PeachBlossomResult, FateModificationPlan } from "../../lib/api";
import { BaziChart } from "./BaziChart";
import { ZiweiChart } from "./ZiweiChart";
import { QimenChart } from "./QimenChart";
import { WesternChart } from "./WesternChart";
import { VedicChart } from "./VedicChart";
import { LiuyaoChart } from "./LiyaoChart";
import { MeihuaChart } from "./MeihuaChart";
import { ChengguChart } from "./ChengguChart";
import { BazhaiChart } from "./BazhaiChart";
import { XuankongChart } from "./XuankongChart";
import { TarotChart } from "./TarotChart";
import { NumerologyChart } from "./NumerologyChart";
import { LenormandChart } from "./LenormandChart";
import { LiurenChart } from "./LiurenChart";
import { TiebanChart } from "./TiebanChart";

interface ChartRendererProps {
  chart: ChartResult;
  crossValidation?: CrossValidationResult | null;
  peachBlossom?: PeachBlossomResult | null;
  fateModification?: FateModificationPlan | null;
}

export function ChartRenderer({ chart, crossValidation, peachBlossom, fateModification }: ChartRendererProps) {
  const m = chart.method as Method;
  switch (m) {
    case "bazi":
    case "bazi_v2":
      return <BaziChart chart={chart} crossValidation={crossValidation} peachBlossom={peachBlossom} fateModification={fateModification} />;
    case "ziwei":      return <ZiweiChart chart={chart} />;
    case "qimen":      return <QimenChart chart={chart} />;
    case "western":    return <WesternChart chart={chart} />;
    case "vedic":      return <VedicChart chart={chart} />;
    case "liuyao":     return <LiuyaoChart chart={chart} />;
    case "meihua":     return <MeihuaChart chart={chart} />;
    case "chenggu":    return <ChengguChart chart={chart} />;
    case "bazhai":     return <BazhaiChart chart={chart} />;
    case "xuankong":   return <XuankongChart chart={chart} />;
    case "tarot":      return <TarotChart chart={chart} />;
    case "numerology": return <NumerologyChart chart={chart} />;
    case "lenormand":  return <LenormandChart chart={chart} />;
    case "liuren":     return <LiurenChart chart={chart} />;
    case "tieban":     return <TiebanChart chart={chart} />;
    default: return <div className="card">未知占卜法: {m}</div>;
  }
}
