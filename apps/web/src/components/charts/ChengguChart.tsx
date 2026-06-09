// 称骨:秤视觉
// 术语:骨重/批语
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon } from "../Jargon";

function WeightBar({ label, liang, max }: { label: string; liang: number; max: number }) {
  const pct = Math.min(100, (liang / max) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span style={{ color: COLOR.inkSoft }}>{label}</span>
        <span style={{ color: COLOR.gold }}>{liang.toFixed(1)} <span className="text-[10px]" style={{ color: COLOR.muted }}>两</span></span>
      </div>
      <div className="h-2 rounded-sm overflow-hidden" style={{ background: "rgba(8,10,15,0.5)" }}>
        <div className="h-full rounded-sm transition-all"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${COLOR.goldDim}, ${COLOR.gold})` }} />
      </div>
    </div>
  );
}

export function ChengguChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const weights = [r.year_liang, r.month_liang, r.day_liang, r.hour_liang].map((v) => Number(v) || 0);
  const max = Math.max(1.5, ...weights);
  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>称骨算命</h3>
          <div className="flex gap-2 text-xs">
            <span className="tag tag-east">
              <Jargon term="骨重" mode="plain" /> 总 {r.total_liang} 两 ({r.total_qian} 钱)
            </span>
          </div>
        </div>

        <div className="space-y-3 max-w-md mx-auto">
          <WeightBar label="年柱" liang={weights[0]} max={max} />
          <WeightBar label="月柱" liang={weights[1]} max={max} />
          <WeightBar label="日柱" liang={weights[2]} max={max} />
          <WeightBar label="时柱" liang={weights[3]} max={max} />
        </div>

        <div className="mt-5 text-center">
          <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>
            <Jargon term="骨重" mode="plain" /> 总分
          </div>
          <div className="text-5xl font-display mt-1" style={{ color: COLOR.gold }}>
            {r.total_liang} <span className="text-lg" style={{ color: COLOR.muted }}>两</span>
            <span className="text-base ml-2" style={{ color: COLOR.muted }}>({r.total_qian} 钱)</span>
          </div>
          <div className="text-[10px] mt-2" style={{ color: COLOR.muted }}>
            越大越重 = 命格档次越高
          </div>
        </div>
      </div>

      <div className="card">
        <div className="text-xs mb-2" style={{ color: COLOR.muted }}>
          <Jargon term="批语" mode="plain" />
        </div>
        <div className="text-sm" style={{ color: COLOR.ink }}>{r.piyu}</div>
        <div className="text-[10px] mt-3" style={{ color: COLOR.muted }}>
          干支: {r.ganzhi?.年} {r.ganzhi?.月} {r.ganzhi?.日} {r.ganzhi?.时}
        </div>
      </div>
    </div>
  );
}
