// 八宅:八方罗盘图
// 术语:命卦/东四命/西四命 + 八星(生气/延年/天医/伏位/五鬼/六煞/祸害/绝命)
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

const GUA_DIR: Record<string, string> = {
  坎: "北", 艮: "东北", 震: "东", 巽: "东南",
  离: "南", 坤: "西南", 兑: "西", 乾: "西北",
};

const GUA_STAR: Record<string, { star: string; good: boolean; plain: string }> = {
  坎: { star: "生气", good: true,  plain: "大吉" },
  艮: { star: "延年", good: true,  plain: "次吉" },
  震: { star: "天医", good: true,  plain: "健康位" },
  巽: { star: "伏位", good: true,  plain: "平稳位" },
  离: { star: "五鬼", good: false, plain: "凶" },
  坤: { star: "祸害", good: false, plain: "凶" },
  兑: { star: "六煞", good: false, plain: "凶" },
  乾: { star: "绝命", good: false, plain: "凶" },
};

export function BazhaiChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const lifeGua = r.life_gua || "—";
  const eastFour: string[] = r.east_four || [];
  const westFour: string[] = r.west_four || [];
  const isEast = r.is_east;
  const own = isEast ? eastFour : westFour;

  const cellGua: Record<string, string> = {};
  for (const g of Object.keys(GUA_DIR)) {
    cellGua[GUA_DIR[g]] = g;
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>八宅 · 八方罗盘</h3>
          <div className="flex gap-2 text-xs">
            <span className="tag tag-east">
              <Jargon term="命卦" mode="plain" /> {lifeGua}
            </span>
            <span className="tag">
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
                  style={{ background: "rgba(8,10,15,0.5)", border: `1px solid ${COLOR.line}` }}>
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
            const starInfo = GUA_STAR[gua] || { star: "—", good: false, plain: "—" };
            const isGoodDir = own.includes(gua);
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
                  <span style={{ color: isGoodDir ? COLOR.ok : COLOR.danger }}>{starInfo.star}</span>
                  <span className="text-[9px] ml-1" style={{ color: COLOR.muted }}>·{starInfo.plain}</span>
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
        <div>年柱: <span style={{ color: COLOR.ink }}>{r.year_gz}</span></div>
        <div>本命凶方: <span style={{ color: COLOR.danger }}>{((r.inauspicious_dirs || []) as string[]).join(" ")}</span></div>
        {r.sitting && <div>坐山: <span style={{ color: COLOR.ink }}>{r.sitting}</span></div>}
      </div>

      {/* House-Resident Match */}
      {r.house_resident_match && (
        <div className="card">
          <h4 className="text-sm mb-2" style={{ color: COLOR.gold }}>宅命相配</h4>
          <div className="flex items-center gap-3 flex-wrap text-sm">
            <span style={{ color: COLOR.gold }}>
              宅卦: {r.house_gua}({r.house_is_east ? "东四宅" : "西四宅"})
            </span>
            <span style={{ color: r.house_resident_match.matched ? COLOR.jade : COLOR.danger }}>
              {r.house_resident_match.matched ? "✓ 相配" : "✗ 不配"}
            </span>
          </div>
          <div className="text-xs mt-2 leading-relaxed" style={{ color: COLOR.inkSoft }}>
            {r.house_resident_match.description}
          </div>
        </div>
      )}

      {/* 八星方位 from 大游年歌 */}
      {r.bazhai_stars && (
        <div className="card">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
            大游年 · 八星方位
            <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
              — 以宅卦{r.house_gua}定八方星曜
            </span>
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(r.bazhai_stars as Record<string, any>)
              .sort(([, a], [, b]) => (a.rank || 9) - (b.rank || 9))
              .map(([dir, star]) => {
                const isAuspicious = star.auspicious;
                return (
                  <div
                    key={dir}
                    className="p-2 rounded text-center"
                    style={{
                      background: isAuspicious ? "rgba(90,164,105,0.08)" : "rgba(200,85,61,0.06)",
                      border: `1px solid ${isAuspicious ? "rgba(90,164,105,0.3)" : "rgba(200,85,61,0.2)"}`,
                    }}
                  >
                    <div className="text-[10px]" style={{ color: COLOR.muted }}>{dir}</div>
                    <div
                      className="text-sm font-semibold mt-0.5"
                      style={{ color: isAuspicious ? COLOR.jade : COLOR.danger }}
                    >
                      {star.star}
                    </div>
                    <div className="text-[9px] mt-0.5" style={{ color: COLOR.muted }}>
                      {star.nature?.split("·")[0] || ""} #{star.rank}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
