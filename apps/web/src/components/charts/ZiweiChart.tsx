// 紫微斗数: 十二宫盘 + 星曜着色 + 四化标注 + 长生/博士/将前 + 运程
// 专业级斗数盘面渲染
import type React from "react";
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";

type Star = string | { name?: string; mutagen?: string };

interface Palace {
  name?: string;
  major_stars?: Star[];
  minor_stars?: Star[];
  adjective_stars?: Star[];
  is_body_palace?: boolean;
  is_original_palace?: boolean;
  is_empty?: boolean;
  earthly_branch?: string;
  heavenly_stem?: string;
  changsheng12?: string;
  boshi12?: string;
  jiangqian12?: string;
  decadal?: any;
  ages?: number[];
}

const BRANCH_ORDER = ["巳", "午", "未", "申", "辰", "酉", "卯", "戌", "寅", "丑", "子", "亥"];

const MUTAGEN_COLOR: Record<string, string> = {
  "禄": "#5AA469", "权": "#C9A24B", "科": "#5B8DEF", "忌": "#C8553D",
};

function displayText(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if ("year" in obj && "month" in obj && "day" in obj) {
      const leap = obj.is_leap_month ? " 闰月" : "";
      return `${obj.year}-${obj.month}-${obj.day}${leap}`;
    }
    if ("name" in obj) return displayText(obj.name);
    try { return JSON.stringify(value); } catch { return "—"; }
  }
  return String(value);
}

function starLabel(star: Star): { text: string; mutagen?: string } {
  if (typeof star === "string") return { text: star };
  const name = displayText(star.name);
  return { text: name, mutagen: star.mutagen };
}

function starDisplayText(star: Star): string {
  const { text, mutagen } = starLabel(star);
  return mutagen ? `${text}·${mutagen}` : text;
}

function palaceTitle(palace?: Palace): string {
  if (!palace?.name) return "—";
  return displayText(palace.name);
}

// Major 14 stars for special coloring
const MAJOR_STAR_SET = new Set([
  "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
  "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]);

export function ZiweiChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const palaces: Palace[] = Array.isArray(r.palaces) ? r.palaces : [];
  const byBranch: Record<string, Palace> = {};
  for (const palace of palaces) {
    if (palace.earthly_branch) byBranch[palace.earthly_branch] = palace;
  }
  const ming = palaces.find((p) => p.is_original_palace || p.name === "命宫");
  const bodyPalace = palaces.find((p) => p.is_body_palace);
  const mingBranch = ming?.earthly_branch;
  const horoscope = r.horoscope || {};

  // Collect all 四化 stars across palaces
  const mutagenStars = new Map<string, string>(); // starName -> mutagen
  palaces.forEach((p) => {
    [...(p.major_stars || []), ...(p.minor_stars || [])].forEach((s) => {
      const { text, mutagen } = starLabel(s);
      if (mutagen && text) mutagenStars.set(text, mutagen);
    });
  });

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="paper-frame">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            紫微斗数 · 十二宫
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className="paper-tag paper-tag-east">
              命主 {displayText(r.soul)}
            </span>
            <span className="paper-tag paper-tag-east">
              身主 {displayText(r.body)}
            </span>
            {r.five_elements_class && (
              <span className="paper-tag" style={{ background: "rgba(201,162,75,0.10)", color: COLOR.gold }}>
                五行局 {displayText(r.five_elements_class)}
              </span>
            )}
            {r.gender && (
              <span className="paper-tag" style={{ color: COLOR.inkSoft }}>
                {displayText(r.gender)}
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-4 text-xs flex-wrap">
          <Stat label="命宫" value={`${palaceTitle(ming)} · ${mingBranch || "?"}`} tone="gold" />
          <Stat label="身宫" value={`${palaceTitle(bodyPalace)} · ${bodyPalace?.earthly_branch || "?"}`} tone="azure" />
          <Stat label="五行局" value={displayText(r.five_elements_class)} tone="ink" />
          <Stat label="生肖" value={displayText(r.zodiac)} tone="ink" />
        </div>

        {/* 四化 legend */}
        {mutagenStars.size > 0 && (
          <div className="mt-3 flex gap-3 text-xs flex-wrap">
            {["禄", "权", "科", "忌"].map((m) => {
              const stars = [...mutagenStars.entries()].filter(([, v]) => v === m).map(([k]) => k);
              if (stars.length === 0) return null;
              return (
                <div key={m} className="flex items-center gap-1.5">
                  <span className="px-1 py-0.5 rounded text-[10px] font-semibold"
                    style={{ background: `${MUTAGEN_COLOR[m]}20`, color: MUTAGEN_COLOR[m] }}>
                    {m}
                  </span>
                  <span style={{ color: COLOR.inkSoft }}>{stars.join(" ")}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── 12-Palace Grid ── */}
      <div className="paper-frame">
        <div className="grid grid-cols-4 grid-rows-4 gap-1.5 max-w-xl mx-auto" style={{ aspectRatio: "1 / 1" }}>
          {/* Top row: 巳 午 未 申 */}
          {BRANCH_ORDER.slice(0, 4).map((branch) => (
            <PalaceCell key={branch} branch={branch} palace={byBranch[branch]} isMing={branch === mingBranch} />
          ))}
          {/* Second row: 辰 | Center | 酉 */}
          <PalaceCell branch="辰" palace={byBranch["辰"]} isMing={"辰" === mingBranch} />
          <CenterCell title="中宫">
            {mingBranch && <div style={{ color: COLOR.goldBright }}>命宫 → {mingBranch}</div>}
            <div style={{ color: COLOR.inkSoft }}>{displayText(r.zodiac)}</div>
          </CenterCell>
          <CenterCell title="身宫">
            <div style={{ color: COLOR.inkSoft }}>{displayText(bodyPalace?.earthly_branch)}</div>
            <div className="mt-0.5" style={{ color: COLOR.gold }}>{palaceTitle(bodyPalace)}</div>
          </CenterCell>
          <PalaceCell branch="酉" palace={byBranch["酉"]} isMing={"酉" === mingBranch} />
          {/* Third row: 卯 | Center | 戌 */}
          <PalaceCell branch="卯" palace={byBranch["卯"]} isMing={"卯" === mingBranch} />
          <CenterCell title="大限">
            {horoscope.decadal ? (
              <>
                <div style={{ color: COLOR.inkSoft }}>{horoscope.decadal.heavenly_stem}{horoscope.decadal.earthly_branch}</div>
                <div className="mt-0.5" style={{ color: COLOR.gold }}>
                  {horoscope.decadal.range?.from || ""}{horoscope.decadal.range ? "–" : ""}{horoscope.decadal.range?.to || ""}
                </div>
              </>
            ) : (
              <div style={{ color: COLOR.muted }}>—</div>
            )}
          </CenterCell>
          <CenterCell title="流年">
            {horoscope.yearly ? (
              <>
                <div style={{ color: COLOR.inkSoft }}>{horoscope.yearly.heavenly_stem}{horoscope.yearly.earthly_branch}</div>
                <div className="mt-0.5 text-[10px]" style={{ color: COLOR.muted }}>
                  {horoscope.yearly.scope || ""}
                </div>
              </>
            ) : (
              <div style={{ color: COLOR.muted }}>—</div>
            )}
          </CenterCell>
          <PalaceCell branch="戌" palace={byBranch["戌"]} isMing={"戌" === mingBranch} />
          {/* Bottom row: 寅 丑 子 亥 */}
          {BRANCH_ORDER.slice(8).map((branch) => (
            <PalaceCell key={branch} branch={branch} palace={byBranch[branch]} isMing={branch === mingBranch} />
          ))}
        </div>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px]" style={{ color: COLOR.muted }}>
          <span><span style={{ color: COLOR.gold }}>■</span> 十四主星</span>
          <span><span style={{ color: COLOR.jade }}>■</span> 辅星/杂曜</span>
          <span><span className="px-0.5 rounded" style={{ background: "rgba(90,164,105,0.15)", color: "#5AA469" }}>禄</span>化禄</span>
          <span><span className="px-0.5 rounded" style={{ background: "rgba(201,162,75,0.15)", color: "#C9A24B" }}>权</span>化权</span>
          <span><span className="px-0.5 rounded" style={{ background: "rgba(91,141,239,0.15)", color: "#5B8DEF" }}>科</span>化科</span>
          <span><span className="px-0.5 rounded" style={{ background: "rgba(200,85,61,0.15)", color: "#C8553D" }}>忌</span>化忌</span>
        </div>
      </div>

      {/* ── 十二长生 / 博士 / 将前 ── */}
      {(palaces.some((p) => p.changsheng12 || p.boshi12 || p.jiangqian12)) && (
        <div className="paper-frame">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
            神煞附宫
            <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
              — 十二长生 · 博士十二神 · 将前十二神
            </span>
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 text-[10px]">
            {palaces.map((p) => {
              const key = p.earthly_branch || p.name || "";
              const cs = p.changsheng12;
              const bs = p.boshi12;
              const js = p.jiangqian12;
              if (!cs && !bs && !js) return null;
              return (
                <div key={key} className="rounded p-1.5"
                  style={{ background: "var(--paper-2)", border: `1px solid ${COLOR.lineSoft}` }}>
                  <div style={{ color: COLOR.gold }}>{palaceTitle(p)}</div>
                  {cs && <div style={{ color: COLOR.azure }}>{cs}</div>}
                  {bs && <div style={{ color: COLOR.inkSoft }}>{bs}</div>}
                  {js && <div style={{ color: COLOR.muted }}>{js}</div>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Footer ── */}
      <div className="card-raised flex gap-6 flex-wrap text-xs">
        <div><span style={{ color: COLOR.muted }}>排盘算法</span> <span style={{ color: COLOR.ink }}>{chart.engine}</span></div>
        <div><span style={{ color: COLOR.muted }}>公历</span> <span style={{ color: COLOR.ink }}>{displayText(r.chinese_date)}</span></div>
        <div><span style={{ color: COLOR.muted }}>农历</span> <span style={{ color: COLOR.ink }}>{displayText(r.lunar_date)}</span></div>
        {r.fallback && <div style={{ color: COLOR.danger }}>fallback: {displayText(r.fallback_reason)}</div>}
      </div>
    </div>
  );
}

// ── Center Cell ──
function CenterCell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md flex flex-col items-center justify-center p-2 text-center"
      style={{ background: "var(--paper-2)", border: `1px solid ${COLOR.goldDim}` }}>
      <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>{title}</div>
      <div className="text-xs mt-1 space-y-0.5">{children}</div>
    </div>
  );
}

// ── Palace Cell ──
function PalaceCell({ branch, palace, isMing }: { branch: string; palace?: Palace; isMing: boolean }) {
  const major = (palace?.major_stars || []).map(starDisplayText).filter(Boolean);
  const minor = [...(palace?.minor_stars || []), ...(palace?.adjective_stars || [])].map(starDisplayText).filter(Boolean);
  const empty = Boolean(palace?.is_empty);
  const isBody = Boolean(palace?.is_body_palace);

  // Determine border style
  let borderColor: string = empty ? COLOR.muted : COLOR.line;
  let borderStyle: string = empty ? "dashed" : "solid";
  if (isMing) { borderColor = COLOR.gold; borderStyle = "solid"; }
  if (isBody) { borderColor = COLOR.azure; borderStyle = "solid"; }

  // Background
  let bg = "var(--paper-2)";
  if (isMing) bg = "rgba(201,162,75,0.10)";
  else if (isBody) bg = "rgba(91,141,239,0.06)";

  return (
    <div className="rounded-md p-1.5 text-[10px] sm:text-xs flex flex-col overflow-hidden"
      style={{ background: bg, border: `1px ${borderStyle} ${borderColor}`, minHeight: 72 }}>
      {/* Header: Palace name + Branch */}
      <div className="flex justify-between items-center gap-1">
        <span className="truncate font-semibold"
          style={{ color: isMing ? COLOR.goldBright : isBody ? COLOR.azure : COLOR.inkSoft }}>
          {palaceTitle(palace)}
        </span>
        <span style={{ color: COLOR.muted, fontSize: 9 }}>{branch}</span>
      </div>

      {/* Heavenly stem */}
      {palace?.heavenly_stem && (
        <div className="text-[9px]" style={{ color: COLOR.muted }}>
          天干 {palace.heavenly_stem}
        </div>
      )}

      {/* Major stars */}
      <div className="mt-0.5 leading-tight space-y-0.5">
        {major.length > 0 ? major.map((s, i) => (
          <MajorStar key={i} star={palace?.major_stars?.[i]} text={s} />
        )) : (
          <span style={{ color: COLOR.muted }}>—</span>
        )}
      </div>

      {/* Minor/adjective stars */}
      {minor.length > 0 && (
        <div className="mt-auto leading-tight text-[10px] space-y-0">
          {minor.slice(0, 3).map((s, i) => {
            // Find the original star object to check for mutagen
            const allMinor = [...(palace?.minor_stars || []), ...(palace?.adjective_stars || [])];
            const orig = allMinor[i];
            return <MinorStar key={i} star={orig} text={s} />;
          })}
          {minor.length > 3 && (
            <span style={{ color: COLOR.muted }}>+{minor.length - 3} 杂曜</span>
          )}
        </div>
      )}
    </div>
  );
}

// ── Major Star with mutagen coloring ──
function MajorStar({ star, text }: { star?: Star; text: string }) {
  const { text: name, mutagen } = star ? starLabel(star) : { text, mutagen: undefined };
  const mColor = mutagen ? MUTAGEN_COLOR[mutagen] : undefined;

  // If there's a mutagen, split display
  if (mutagen && mColor) {
    const baseName = text.replace(`·${mutagen}`, "");
    return (
      <div className="flex items-center gap-1">
        <span style={{ color: COLOR.gold, fontWeight: 600 }}>{baseName}</span>
        <span className="text-[10px] px-0.5 rounded font-semibold"
          style={{ background: `${mColor}20`, color: mColor }}>{mutagen}</span>
      </div>
    );
  }

  return <span style={{ color: COLOR.gold, fontWeight: 600 }}>{text}</span>;
}

// ── Minor Star with optional mutagen ──
function MinorStar({ star, text }: { star?: Star; text: string }) {
  const { mutagen } = star ? starLabel(star) : { mutagen: undefined };
  const mColor = mutagen ? MUTAGEN_COLOR[mutagen] : undefined;
  const baseName = mutagen ? text.replace(`·${mutagen}`, "") : text;

  return (
    <span style={{ color: mColor || COLOR.jade }}>
      {baseName}
      {mutagen && mColor && (
        <span className="ml-0.5 text-[9px] px-0.5 rounded font-semibold"
          style={{ background: `${mColor}15`, color: mColor }}>{mutagen}</span>
      )}
    </span>
  );
}
