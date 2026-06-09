// 大六壬: 天地盘 + 四课三传 + 十二天将 + 课式分析
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";

const DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
const DZ_MEANING: Record<string, string> = {
  "子": "北方·隐私·子女·夜半", "丑": "东北·田土·库房·鸡鸣",
  "寅": "东北·功曹·生机·平旦", "卯": "东方·门户·车船·日出",
  "辰": "东南·水库·争讼·食时", "巳": "东南·炉灶·文书·隅中",
  "午": "南方·光明·官禄·日中", "未": "西南·木库·酒食·日昳",
  "申": "西南·传送·道路·晡时", "酉": "西方·寺观·奴婢·日入",
  "戌": "西北·火库·欺诈·黄昏", "亥": "西北·天门·江河·人定",
};
const WX_COLOR: Record<string, string> = {
  "金": COLOR.gold, "木": COLOR.jade, "水": COLOR.azure, "火": COLOR.danger, "土": "#C8A951",
};
const GENERAL_AUSPICE: Record<string, "ji" | "xiong" | "ping"> = {
  "贵人": "ji", "青龙": "ji", "六合": "ji", "太常": "ji", "天后": "ji",
  "腾蛇": "xiong", "白虎": "xiong", "玄武": "xiong", "天空": "xiong",
  "朱雀": "ping", "勾陈": "ping", "太阴": "ping",
};

function BranchCell({ zhi, label, wuxing }: { zhi: string; label?: string; wuxing?: string }) {
  const wx = wuxing || "";
  const wxColor = WX_COLOR[wx] || COLOR.muted;
  return (
    <div className="text-center p-1.5 rounded" style={{ background: "rgba(8,10,15,0.35)" }}>
      {label && (
        <div className="text-[8px] uppercase tracking-wide" style={{ color: COLOR.muted }}>
          {label}
        </div>
      )}
      <div className="text-sm font-semibold" style={{ color: COLOR.goldBright }}>
        {zhi}
      </div>
      {wx && (
        <div className="text-[9px]" style={{ color: wxColor }}>
          {wx}
        </div>
      )}
    </div>
  );
}

export function LiurenChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const cosmic = r.cosmic_board || {};
  const skyPan: Record<string, string> = cosmic.sky_pan || {};
  const earthPan: Record<string, string> = cosmic.earth_pan || {};
  const divTime = r.divination_time || {};
  const lessons: any[] = r.four_lessons || [];
  const threeTrans = r.three_transmissions || {};
  const generals: any[] = r.twelve_generals || [];
  const hints = r.reading_hints || {};
  const basis = r.calculation_basis || {};

  // Parse pan entries
  const panEntries = DZ.map((zhi) => {
    const key = `宫${DZ.indexOf(zhi)}(${zhi})`;
    const skyZhi = skyPan[key] || "";
    const earthZhi = earthPan[key] || zhi;
    return { zhi, skyZhi, earthZhi };
  });

  // General stats
  const jiCount = generals.filter((g) => GENERAL_AUSPICE[g.general] === "ji").length;
  const xiongCount = generals.filter((g) => GENERAL_AUSPICE[g.general] === "xiong").length;

  const methodLabel: Record<string, string> = {
    chu_chuan: "初传·起因", zhong_chuan: "中传·过程", mo_chuan: "末传·结果",
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            大六壬 · 天地盘
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className="tag tag-east">三式之首</span>
            <span className="tag" style={{ background: "rgba(91,141,239,0.10)", color: COLOR.azure }}>
              日{divTime.is_day ? "昼" : "夜"}占
            </span>
          </div>
        </div>

        {/* Header stats */}
        <div className="flex gap-4 mt-3 text-xs flex-wrap">
          <Stat label="占时" value={`${divTime.hour_branch}时`} tone="gold" />
          <Stat label="月将" value={`${divTime.month_general_name}(${divTime.month_general})`} tone="azure" />
          <Stat label="日柱" value={r.day_ganzhi || "—"} tone="gold" />
          <Stat label="旬空" value={r.xun_kong || "—"} tone="ink" />
          <Stat label="贵人" value={r.gui_ren_zhi || "—"} tone="gold" />
        </div>

        {/* Overall assessment */}
        {hints.overall && (
          <div
            className="mt-3 p-3 rounded-md text-sm leading-relaxed"
            style={{ background: "rgba(201,162,75,0.06)", border: `1px solid ${COLOR.lineSoft}` }}
          >
            <span style={{ color: COLOR.gold }}>课式总断: </span>
            <span style={{ color: COLOR.inkSoft }}>{hints.overall}</span>
          </div>
        )}
      </div>

      {/* Cosmic Board (天地盘) */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          天地盘
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 上行天盘(月将加时) · 下行地盘(固定十二宫)
          </span>
        </h4>
        <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
          {panEntries.map(({ zhi, skyZhi, earthZhi }) => (
            <div
              key={zhi}
              className="rounded-md p-2 text-center"
              style={{ background: "rgba(8,10,15,0.4)", border: `1px solid ${COLOR.lineSoft}` }}
            >
              <div className="text-[9px] uppercase tracking-wide mb-1" style={{ color: COLOR.muted }}>
                {zhi}宫
              </div>
              <div className="text-sm font-semibold" style={{ color: COLOR.goldBright }}>
                {skyZhi || "—"}
              </div>
              <div className="text-xs mt-0.5" style={{ color: COLOR.inkSoft }}>
                {earthZhi || zhi}
              </div>
              <div className="text-[8px] mt-0.5" style={{ color: COLOR.muted }}>
                {DZ_MEANING[zhi]?.split("·")[0] || ""}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Four Lessons (四课) */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          四课
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 日干支与天地盘交互生成的上下神关系
          </span>
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {lessons.map((l, i) => (
            <div
              key={i}
              className="rounded-md p-3 text-center"
              style={{ background: "rgba(8,10,15,0.4)", border: `1px solid ${COLOR.lineSoft}` }}
            >
              <div className="text-[9px] uppercase tracking-widest mb-2" style={{ color: COLOR.muted }}>
                第{l.idx}课
              </div>
              <div className="flex items-center justify-center gap-0.5">
                <span className="text-sm font-semibold" style={{ color: COLOR.gold }}>
                  {l.upper}
                </span>
                <span className="text-[9px]" style={{ color: COLOR.muted }}>
                  上
                </span>
              </div>
              <div className="flex items-center justify-center gap-0.5 mt-1">
                <span className="text-sm" style={{ color: COLOR.inkSoft }}>
                  {l.lower}
                </span>
                <span className="text-[9px]" style={{ color: COLOR.muted }}>
                  下
                </span>
              </div>
              <div className="text-[8px] mt-1.5" style={{ color: COLOR.muted }}>
                {l.upper_label?.split("·")[0]}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Three Transmissions (三传) */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          三传
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 事情的起因·过程·结果
          </span>
          <span
            className="ml-2 text-[10px] px-1.5 py-0.5 rounded"
            style={{ background: "rgba(91,141,239,0.10)", color: COLOR.azure }}
          >
            {threeTrans.method || "—"}
          </span>
        </h4>

        {/* Transmission flow */}
        <div className="flex items-stretch gap-0 mb-4">
          {["chu_chuan", "zhong_chuan", "mo_chuan"].map((key, idx) => (
            <div key={key} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-md p-3 text-center"
                style={{ background: idx === 0 ? "rgba(201,162,75,0.08)" : "rgba(8,10,15,0.3)", border: `1px solid ${idx === 0 ? COLOR.goldDim : COLOR.lineSoft}` }}
              >
                <div className="text-[9px] uppercase tracking-widest mb-1" style={{ color: COLOR.muted }}>
                  {methodLabel[key] || key}
                </div>
                <div className="text-xl font-display" style={{ color: idx === 0 ? COLOR.goldBright : COLOR.ink }}>
                  {threeTrans[key] || "—"}
                </div>
                <div
                  className="text-[10px] mt-1"
                  style={{ color: WX_COLOR[threeTrans[`${key.replace("_chuan", "")}_wx`]] || COLOR.muted }}
                >
                  {threeTrans[`${key.replace("_chuan", "")}_wx`] || "—"}
                </div>
              </div>
              {idx < 2 && (
                <div className="text-lg my-0" style={{ color: COLOR.goldDim }}>
                  →
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Flow summary */}
        <div className="text-xs text-center" style={{ color: COLOR.inkSoft }}>
          {threeTrans.chu_chuan} → {threeTrans.zhong_chuan} → {threeTrans.mo_chuan}
          {threeTrans.has_fuyin && (
            <span className="ml-2 px-1.5 py-0.5 rounded" style={{ background: "rgba(200,85,61,0.10)", color: COLOR.danger }}>
              伏吟
            </span>
          )}
        </div>
      </div>

      {/* Twelve Generals (十二天将) */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          十二天将 · 贵人起{divTime.is_day ? "昼" : "夜"}顺逆排布
        </h4>

        {/* Summary bar */}
        <div className="flex gap-3 mb-4 text-xs flex-wrap">
          <Stat label="吉将" value={`${jiCount} 位`} tone="jade" />
          <Stat label="凶将" value={`${xiongCount} 位`} tone="azure" />
          <Stat label="平将" value={`${12 - jiCount - xiongCount} 位`} tone="ink" />
        </div>

        <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
          {generals.map((g, i) => {
            const auspice = GENERAL_AUSPICE[g.general] || "ping";
            const auspiceColor =
              auspice === "ji" ? COLOR.jade
              : auspice === "xiong" ? COLOR.danger
              : COLOR.muted;
            const auspiceBg =
              auspice === "ji" ? "rgba(79,179,160,0.08)"
              : auspice === "xiong" ? "rgba(200,85,61,0.06)"
              : "rgba(255,255,255,0.02)";
            return (
              <div
                key={i}
                className="rounded-md p-2 text-center"
                style={{ background: auspiceBg, border: `1px solid ${COLOR.lineSoft}` }}
              >
                <div className="text-[8px] uppercase tracking-widest" style={{ color: COLOR.muted }}>
                  {g.position}宫
                </div>
                <div className="text-xs font-semibold mt-1" style={{ color: auspiceColor }}>
                  {g.general}
                </div>
                <div className="text-[10px] mt-0.5" style={{ color: COLOR.inkSoft }}>
                  {g.tian_pan_zhi}
                </div>
                <div className="text-[9px]" style={{ color: WX_COLOR[g.zhi_wx] || COLOR.muted }}>
                  {g.zhi_wx}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
        <p>大六壬为"三式"之首 · 天地盘 + 四课三传 + 十二天将体系</p>
        <p>
          本实现使用简化九宗门法 (
          {basis.limits ? basis.limits[0] : "基础课式"}
          ) · 遁干/神煞/长生十二宫等高级体系待后续版本展开
        </p>
      </div>
    </div>
  );
}
