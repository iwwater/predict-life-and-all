// 小六壬: 六宫掌诀 + 月日时定位
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import type { StaggerStyle } from "../../lib/useStaggeredReveal";

const PALACE_TONE: Record<string, { color: string; bg: string }> = {
  auspicious: { color: COLOR.jade, bg: "rgba(79,179,160,0.10)" },
  delayed:    { color: COLOR.gold, bg: "rgba(201,162,75,0.10)" },
  conflict:   { color: COLOR.danger, bg: "rgba(200,85,61,0.10)" },
  "minor luck": { color: COLOR.goldBright, bg: "rgba(201,162,75,0.12)" },
  void:       { color: COLOR.muted, bg: "rgba(255,255,255,0.03)" },
};

export function XiaoliurenChart({ chart, cellReveal }: { chart: ChartResult; cellReveal?: (i: number) => StaggerStyle }) {
  const r = chart.raw || {};
  const palaces: any[] = r.six_palaces || [];
  const selectedName = r.palace || "";
  const mode = r.mode || "time_xiaoliuren";
  const basis = r.calculation_basis || {};
  const input = basis.input || {};
  const idx = typeof r.result_index === "number" ? r.result_index : 0;

  // 12 cells = 6 palaces × 2 phases (主课 + 变课), selected palace highlighted
  const cells: Array<{ name: string; phase: string; tone: string; meaning: string; selected: boolean }> = [];
  for (let i = 0; i < 6; i++) {
    const p = palaces[i] || { name: "—", tone: "void", meaning: "" };
    cells.push({ name: p.name, phase: "主课", tone: p.tone, meaning: p.meaning || "", selected: i === idx - 1 });
    cells.push({ name: p.name, phase: "变课", tone: p.tone, meaning: p.meaning || "", selected: i === idx - 1 });
  }

  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            小六壬 · {selectedName || "—"}
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className="paper-tag paper-tag-east">掌诀</span>
            <span className="paper-tag" style={{ background: "rgba(91,141,239,0.10)", color: COLOR.azure }}>
              {mode === "number_xiaoliuren" ? "数字起卦" : "月日时起卦"}
            </span>
          </div>
        </div>
        <div className="flex gap-4 mt-3 text-xs flex-wrap">
          {mode === "number_xiaoliuren" && input.numbers && (
            <div style={{ color: COLOR.inkSoft }}>三数: {input.numbers.join(" · ")}</div>
          )}
          {mode === "time_xiaoliuren" && (
            <div style={{ color: COLOR.inkSoft }}>
              农历 {input.month}月{input.day}日 · {input.hour_branch}时
            </div>
          )}
          <div style={{ color: COLOR.muted }}>索引: 第{idx}宫</div>
        </div>
      </div>

      <div className="paper-frame">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          六宫掌诀
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 主课示当前事态 · 变课示后续走向
          </span>
        </h4>
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {cells.map((c, i) => {
            const tone = PALACE_TONE[c.tone] || PALACE_TONE.void;
            return (
              <div
                key={i}
                className="paper-grid-cell rounded-md p-2 text-center animate-fade-in"
                style={{
                  background: c.selected ? tone.bg : "var(--paper-2)",
                  border: `1px solid ${c.selected ? tone.color : COLOR.lineSoft}`,
                  ...(cellReveal ? cellReveal(i) : {}),
                }}
              >
                <div className="text-[8px] uppercase tracking-widest" style={{ color: COLOR.muted }}>
                  第{Math.floor(i / 2) + 1}宫 · {c.phase}
                </div>
                <div className="text-sm font-semibold mt-1" style={{ color: tone.color }}>
                  {c.name}
                </div>
                <div className="text-[10px] mt-1 leading-snug" style={{ color: COLOR.inkSoft }}>
                  {c.meaning}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="text-[10px]" style={{ color: COLOR.muted }}>
        小六壬适合即时决疑 · 不同传承对起数细节略有差异 · 本版本采用月日时顺推六宫
      </div>
    </div>
  );
}
