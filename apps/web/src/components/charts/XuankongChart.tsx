// 玄空飞星:九宫格
// 术语:运/坐/向/山星/向星/格局 全部用 <Jargon> 翻白话
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

const GONG_BY_LUO_SHU: Record<string, [number, number]> = {
  巽: [0, 0], 离: [0, 1], 坤: [0, 2],
  震: [1, 0], 中: [1, 1], 兑: [1, 2],
  艮: [2, 0], 坎: [2, 1], 乾: [2, 2],
};

// 格局对应"人话评级"
const PATTERN_PLAIN: Record<string, { plain: string; tone: "ok" | "danger" | "warn" }> = {
  旺山旺向: { plain: "最佳格局", tone: "ok" },
  上山下水: { plain: "较差格局", tone: "danger" },
  双星到向: { plain: "偏财格局", tone: "warn" },
};

export function XuankongChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const grid: Record<string, { 运: number; 山: number; 向: number; 运_旺衰?: string; 山_旺衰?: string; 向_旺衰?: string }> = r.grid || {};

  // Timeliness color map
  const TML_COLOR: Record<string, string> = {
    "旺": "#5AA469", "生": "#5B8DEF", "退": "#C9A24B", "死": "#C8A951", "煞": COLOR.danger, "平": COLOR.muted,
  };
  const TML_BG: Record<string, string> = {
    "旺": "rgba(90,164,105,0.15)", "生": "rgba(91,141,239,0.12)", "退": "rgba(201,162,75,0.10)", "死": "rgba(200,169,81,0.08)", "煞": "rgba(200,85,61,0.10)", "平": "rgba(255,255,255,0.03)",
  };
  const pattern = r.pattern || "";
  const patInfo = PATTERN_PLAIN[pattern] || { plain: pattern, tone: "warn" as const };
  const patColor = patInfo.tone === "ok" ? COLOR.ok : patInfo.tone === "danger" ? COLOR.danger : COLOR.gold;

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>玄空飞星</h3>
          <div className="flex gap-2 text-xs flex-wrap">
            <span className="tag tag-east">
              <Jargon term="运" mode="plain" /> {r.period || "—"}
            </span>
            <span className="tag">
              <Jargon term="坐" mode="plain" /> {r.sitting} · <Jargon term="向" mode="plain" /> {r.facing}
            </span>
            <span className="tag" style={{ color: patColor, borderColor: `${patColor}66` }}>
              <Jargon term="格局" mode="plain" /> {patInfo.plain}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1.5 max-w-sm mx-auto" style={{ aspectRatio: "1 / 1" }}>
          {Object.entries(GONG_BY_LUO_SHU).map(([gua, [row, col]]) => {
            const idx = row * 3 + col;
            const data = grid[gua] || { 运: 0, 山: 0, 向: 0 };
            const isCenter = gua === "中";
            return (
              <div key={gua}
                className="rounded-md p-2 text-xs flex flex-col"
                style={{
                  background: isCenter ? "rgba(201,162,75,0.08)" : "rgba(8,10,15,0.5)",
                  border: `1px solid ${isCenter ? COLOR.gold : COLOR.line}`,
                  minHeight: 70,
                }}
              >
                <div className="flex justify-between items-center">
                  <span style={{ color: isCenter ? COLOR.goldBright : COLOR.inkSoft }}>{gua}</span>
                  <span className="text-[10px]" style={{ color: COLOR.muted }}>#{idx + 1}</span>
                </div>
                {!isCenter && (
                  <div className="mt-auto grid grid-cols-3 gap-1 text-center">
                    {(["运", "山", "向"] as const).map((k) => {
                      const tmlKey = `${k}_旺衰` as string;
                      const tml = (data as any)[tmlKey] || "";
                      const tmlColor = TML_COLOR[tml] || COLOR.muted;
                      return (
                        <div key={k}>
                          <div className="text-[9px]" style={{ color: COLOR.muted }}>
                            <Jargon term={k === "运" ? "运星" : k === "山" ? "山星" : "向星"} mode="plain" />
                          </div>
                          <div className="text-sm font-mono" style={{ color: COLOR.gold }}>{data[k]}</div>
                          {tml && (
                            <span
                              className="text-[8px] px-0.5 rounded"
                              style={{ background: TML_BG[tml] || "transparent", color: tmlColor }}
                            >
                              {tml}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
                {isCenter && (
                  <div className="mt-auto text-center text-[10px]" style={{ color: COLOR.muted }}>
                    中宫无星<br />运入中
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <JargonBox
        title="玄空怎么读"
        items={[
          { term: "运星", plain: "时运星(主导旺衰)" },
          { term: "山星", plain: "坐方星(靠山方向)" },
          { term: "向星", plain: "向方星(面对方向)" },
        ]}
      />

      <div className="card-raised text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div>说明: 数字为星曜,排盘按洛书飞布。</div>
        <div className="mt-1">
          格局判定: <Jargon term="格局" mode="plain" /> ·{" "}
          <span style={{ color: patColor }}>{patInfo.plain}</span>
          (简化算法,真实使用需结合峦头/形局)。
        </div>
      </div>
    </div>
  );
}
