// 八宅:八方罗盘图
// 术语:命卦/东四命/西四命 + 八星(生气/延年/天医/伏位/五鬼/六煞/祸害/绝命)
// 引擎 raw 为中文键: 命卦/命('东四命'字串)/八方{宫:{游年,吉凶}}/吉方/凶方; 宫键繁体(兌/離)
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

const GUA_DIR: Record<string, string> = {
  坎: "北", 艮: "东北", 震: "东", 巽: "东南",
  离: "南", 坤: "西南", 兑: "西", 乾: "西北",
};

const TRAD: Record<string, string> = { 兑: "兌", 离: "離" };
const pick = (d: Record<string, any> | undefined, name: string) =>
  (d && (d[name] ?? d[TRAD[name] ?? name])) || undefined;

export function BazhaiChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw as Record<string, any>;
  const lifeGua = r["命卦"] || "—";
  const ming = String(r["命"] || "");
  const isEast = ming.includes("东");
  const own: string[] = Array.isArray(r["吉方"]) ? r["吉方"] : [];
  const notOwn: string[] = Array.isArray(r["凶方"]) ? r["凶方"] : [];
  const bafang: Record<string, { 游年: string; 吉凶: string }> = r["八方"] || {};

  const cellGua: Record<string, string> = {};
  for (const g of Object.keys(GUA_DIR)) {
    cellGua[GUA_DIR[g]] = g;
  }

  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>八宅 · 八方罗盘</h3>
          <div className="flex gap-2 text-xs">
            <span className="paper-tag paper-tag-east">
              <Jargon term="命卦" mode="plain" /> {lifeGua}
            </span>
            <span className="paper-tag">
              {isEast
                ? <Jargon term="东四命" mode="plain" />
                : <Jargon term="西四命" mode="plain" />}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-4 grid-rows-3 gap-1.5 max-w-md mx-auto" style={{ aspectRatio: "4 / 3" }}>
          {Array.from({ length: 12 }, (_, i) => {
            const row = Math.floor(i / 4);
            const col = i % 4;
            if (row === 1 && col === 1) {
              return (
                <div key={i}
                  className="rounded-md flex flex-col items-center justify-center"
                  style={{ background: "rgba(201,162,75,0.10)", border: `1px solid ${COLOR.gold}` }}>
                  <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>命卦</div>
                  <div className="text-2xl font-display" style={{ color: COLOR.gold }}>{lifeGua}</div>
                  <div className="text-[10px] mt-1" style={{ color: COLOR.goldBright }}>{isEast ? "东四" : "西四"}</div>
                </div>
              );
            }
            if (row === 1 && col === 2) {
              return (
                <div key={i} className="rounded-md p-2 text-[11px] flex flex-col"
                  style={{ background: "var(--paper-2)", border: `1px solid ${COLOR.line}` }}>
                  <div style={{ color: COLOR.muted }}>本命吉方</div>
                  <div className="mt-1" style={{ color: COLOR.ok }}>
                    {own.join(" ")}
                  </div>
                </div>
              );
            }
            const dir = (Object.entries(GUA_DIR).map(([g, d]) => [g, d] as const)
              .find(([_, d]) => {
                if (d === "北") return row === 2 && col === 1;
                if (d === "东北") return row === 2 && col === 0;
                if (d === "东") return row === 1 && col === 0;
                if (d === "东南") return row === 0 && col === 1;
                if (d === "南") return row === 0 && col === 2;
                if (d === "西南") return row === 0 && col === 3;
                if (d === "西") return row === 1 && col === 3;
                if (d === "西北") return row === 2 && col === 3;
                return false;
              })?.[1]) || null;
            if (!dir) return <div key={i} />;
            const gua = cellGua[dir] || "—";
            const starData = pick(bafang, gua) as { 游年: string; 吉凶: string } | undefined;
            const isGoodDir = starData ? starData["吉凶"] === "吉" : own.includes(gua);
            return (
              <div key={i} className="rounded-md p-2 text-[11px] flex flex-col"
                style={{
                  background: isGoodDir ? "rgba(90,164,105,0.08)" : "rgba(200,85,61,0.06)",
                  border: `1px solid ${isGoodDir ? "rgba(90,164,105,0.4)" : "rgba(200,85,61,0.3)"}`,
                }}>
                <div className="flex justify-between">
                  <span style={{ color: COLOR.muted }}>{dir}</span>
                  <span style={{ color: COLOR.gold }}>{gua}</span>
                </div>
                <div className="mt-auto">
                  <span style={{ color: isGoodDir ? COLOR.ok : COLOR.danger }}>{starData?.["游年"] || "—"}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <JargonBox
        title="八宅四吉四凶"
        items={[
          { term: "生气", plain: "大吉" },
          { term: "延年", plain: "次吉" },
          { term: "天医", plain: "健康位" },
          { term: "伏位", plain: "平稳位" },
          { term: "五鬼", plain: "凶" },
          { term: "六煞", plain: "凶" },
          { term: "祸害", plain: "凶" },
          { term: "绝命", plain: "凶" },
        ]}
      />

      <div className="card-raised text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div>本命吉方: <span style={{ color: COLOR.ok }}>{own.join(" ") || "—"}</span></div>
        <div>本命凶方: <span style={{ color: COLOR.danger }}>{notOwn.join(" ") || "—"}</span></div>
      </div>
    </div>
  );
}
