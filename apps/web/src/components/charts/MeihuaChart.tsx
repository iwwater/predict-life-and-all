// 梅花易数:主 / 互 / 变 三卦 + 体用
// 术语:主卦/互卦/变卦/体卦/用卦
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

function GuaSymbol({ name, size = 80 }: { name: string; size?: number }) {
  const upper = name[0] || "—";
  const lower = name[1] || "—";
  const BAGUA_YANG: Record<string, [number, number, number]> = {
    乾: [1, 1, 1], 兑: [1, 1, 0], 离: [1, 0, 1], 震: [1, 0, 0],
    巽: [0, 1, 1], 坎: [0, 1, 0], 艮: [0, 0, 1], 坤: [0, 0, 0],
  };
  const upperLines = BAGUA_YANG[upper] || [0, 0, 0];
  const lowerLines = BAGUA_YANG[lower] || [0, 0, 0];
  const lines = [...lowerLines, ...upperLines];
  return (
    <svg width={size} height={size} viewBox="0 0 80 80">
      {lines.map((y, i) => (
        <g key={i} transform={`translate(0, ${10 + i * 10})`}>
          {y === 1
            ? <rect x={10} y={0} width={60} height={4} fill={COLOR.gold} rx={1} />
            : <g>
                <rect x={10} y={0} width={26} height={4} fill={COLOR.ink} rx={1} />
                <rect x={44} y={0} width={26} height={4} fill={COLOR.ink} rx={1} />
              </g>}
        </g>
      ))}
    </svg>
  );
}

export function MeihuaChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>梅花易数</h3>
          <span className="paper-tag paper-tag-east">
            <Jargon term="动爻" mode="plain" /> {r.dong_yao}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3 max-w-2xl mx-auto">
          {[
            { label: "主卦", term: "主卦" as const, name: r.zhu_gua, color: COLOR.gold },
            { label: "互卦", term: "互卦" as const, name: r.hu_gua, color: COLOR.ink },
            { label: "变卦", term: "变卦" as const, name: r.bian_gua, color: COLOR.jade },
          ].map((g) => (
            <div key={g.label} className="text-center">
              <div className="text-xs mb-2" style={{ color: COLOR.muted }}>
                <Jargon term={g.term} mode="plain" />
              </div>
              <GuaSymbol name={g.name || "—"} />
              <div className="text-sm mt-1" style={{ color: g.color }}>{g.name || "—"}</div>
            </div>
          ))}
        </div>
      </div>

      <JargonBox
        title="三卦怎么看"
        items={[
          { term: "主卦", plain: "原本的卦(现状)" },
          { term: "互卦", plain: "中间的卦(内在过程)" },
          { term: "变卦", plain: "变化后的卦(发展)" },
        ]}
      />

      <div className="paper-frame">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span style={{ color: COLOR.muted }}><Jargon term="体卦" mode="plain" /> </span>
            <span style={{ color: COLOR.goldBright }}>{r.ti_gua}({r.ti_wuxing})</span>
            <span className="text-[10px] ml-1" style={{ color: COLOR.muted }}>· 不动那一卦 = 你</span>
          </div>
          <div>
            <span style={{ color: COLOR.muted }}><Jargon term="用卦" mode="plain" /> </span>
            <span style={{ color: COLOR.jade }}>{r.yong_gua}({r.yong_wuxing})</span>
            <span className="text-[10px] ml-1" style={{ color: COLOR.muted }}>· 有动爻那一卦 = 问的事</span>
          </div>
        </div>
        <div className="mt-3 p-3 rounded-md" style={{ background: "var(--paper-2)" }}>
          <div className="text-xs" style={{ color: COLOR.muted }}>总断</div>
          <div className="text-sm mt-1" style={{ color: COLOR.ink }}>{r.duan || "—"}</div>
        </div>
      </div>
    </div>
  );
}
