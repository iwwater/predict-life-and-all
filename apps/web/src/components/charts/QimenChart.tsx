// 奇门遁甲 3×3 宫格(后天八卦方位)+ 顶部条
// 术语密集:阴遁/阳遁/局/值符/值使/天盘/地盘/九星/八门/八神/节气/真太阳时
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

const PALACE_ORDER: Array<[string, string, [number, number]]> = [
  ["巽", "巽", [0, 0]],
  ["离", "离", [0, 1]],
  ["坤", "坤", [0, 2]],
  ["震", "震", [1, 0]],
  ["中", "中", [1, 1]],
  ["兑", "兑", [1, 2]],
  ["艮", "艮", [2, 0]],
  ["坎", "坎", [2, 1]],
  ["乾", "乾", [2, 2]],
];

export function QimenChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const earth = r.earth_pan || {};
  const sky = r.sky_pan || {};
  const stars = r.stars || {};
  const doors = r.doors || {};
  const gods = r.gods || {};
  const zhifu = r.zhifu || {};

  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>奇门遁甲</h3>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="paper-tag paper-tag-east">
              <Jargon term={r.dun === "阴遁" ? "阴遁" : "阳遁"} mode="plain" /> {r.yuan || ""} {r.ju}<Jargon term="局" mode="plain" />
            </span>
            <span className="paper-tag">
              <Jargon term="节气" mode="plain" /> {r.solar_term || ""}
            </span>
            <span className="paper-tag">
              <Jargon term="值符" mode="plain" /> {zhifu.star} · {zhifu.star_gong}
            </span>
            <span className="paper-tag">
              <Jargon term="值使" mode="plain" /> {zhifu.door} · {zhifu.door_gong}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1.5 max-w-md mx-auto" style={{ aspectRatio: "1 / 1" }}>
          {PALACE_ORDER.map(([name]) => {
            const earthGan = earth[name] || "";
            const skyGan = sky[name] || "";
            const star = stars[name] || "";
            const door = doors[name] || "";
            const god = gods[name] || "";
            const isZhi = (name === zhifu.star_gong);
            return (
              <div key={name}
                className="rounded-md p-2 text-[11px] sm:text-xs flex flex-col"
                style={{
                  background: isZhi ? "rgba(201,162,75,0.10)" : "var(--paper-2)",
                  border: `1px solid ${isZhi ? COLOR.gold : COLOR.line}`,
                  minHeight: 88,
                }}
              >
                <div className="flex justify-between items-center">
                  <span style={{ color: isZhi ? COLOR.goldBright : COLOR.muted }}>{name}</span>
                  {god && <span style={{ color: COLOR.danger }}>{god}</span>}
                </div>
                <div className="mt-1 space-y-0.5 leading-tight">
                  <div>
                    <span style={{ color: COLOR.muted }}><Jargon term="天盘" mode="plain" /></span>{" "}
                    <span style={{ color: COLOR.gold }}>{skyGan}</span>
                  </div>
                  <div>
                    <span style={{ color: COLOR.muted }}><Jargon term="地盘" mode="plain" /></span>{" "}
                    <span style={{ color: COLOR.ink }}>{earthGan}</span>
                  </div>
                  <div style={{ color: COLOR.jade }}>{star}</div>
                  <div style={{ color: COLOR.azure }}>{door}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <JargonBox
        title="奇门盘怎么看"
        items={[
          { term: "九星",  plain: "9 颗行动力(怎么动)" },
          { term: "八门",  plain: "8 种进退(能不能办)" },
          { term: "八神",  plain: "8 种气场(暗力量)" },
          { term: "三奇六仪", plain: "10 个天干布盘" },
        ]}
      />

      <div className="card-raised text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div><Jargon term="真太阳时" mode="plain" /> <span style={{ color: COLOR.ink }}>{r.true_solar_time || "—"}</span></div>
        <div>干支: <span style={{ color: COLOR.ink }}>年 {r.ganzhi?.年} 月 {r.ganzhi?.月} 日 {r.ganzhi?.日} 时 {r.ganzhi?.时}</span></div>
      </div>
    </div>
  );
}
