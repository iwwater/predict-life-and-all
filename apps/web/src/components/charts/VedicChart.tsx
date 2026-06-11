// 吠陀占星: 北印度方盘 + 行星细节 + Nakshatra + Dasha + Yoga
// 专业级 Jyotish 盘面渲染
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";
import { ElementsRadar } from "../ElementsRadar";
import { Jargon } from "../Jargon";

const SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
  "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"];
const SIGN_SYM = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"];

const DIGNITY_COLOR: Record<string, string> = {
  "own": "#5AA469", "exalted": "#4FB3A0", "moolatrikona": "#C9A24B",
  "friendly": "#5B8DEF", "neutral": "#8A8F98", "enemy": "#C8553D",
  "debilitated": "#C8553D",
};
const DIGNITY_LABEL: Record<string, string> = {
  "own": "本垣", "exalted": "擢升", "moolatrikona": "根曜",
  "friendly": "友好", "neutral": "中性", "enemy": "敌对",
  "debilitated": "落陷",
};

const NAKSHATRA_NAMES = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
  "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
  "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
  "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
];
const NAKSHATRA_LORDS = [
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
  "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
  "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
  "Jupiter", "Saturn", "Mercury",
];

const DASHA_COLORS: Record<string, string> = {
  "Ketu": "#C8A951", "Venus": "#C8553D", "Sun": "#C9A24B",
  "Moon": "#5B8DEF", "Mars": "#C8553D", "Rahu": "#8A6E32",
  "Jupiter": "#4FB3A0", "Saturn": "#5B8DEF", "Mercury": "#5AA469",
};

function degreeText(value: unknown): string {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return "0.00°";
  return `${n.toFixed(2)}°`;
}

export function VedicChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const planets: Record<string, any> = r.planets || {};
  const houses: any[] = Array.isArray(r.houses) ? r.houses : [];
  const asc = r.ascendant;
  const ayanamsa = r.ayanamsa;
  const nodes = r.nodes || {};
  const dasha = r.vimsottari_dasha || {};
  const yogas: any[] = Array.isArray(r.yogas) ? r.yogas : [];
  const moonNakshatra = r.moon_nakshatra || planets["月亮"]?.nakshatra || {};

  // Planet table rows
  const planetRows = Object.entries(planets).map(([name, data]: [string, any]) => ({
    name,
    sign: data.sign || "—",
    signIdx: data.sign_idx ?? SIGNS.indexOf(data.sign),
    degree: data.degree ?? data.lon % 30,
    lon: data.lon ?? 0,
    element: data.element || "—",
    house: data.house || 0,
    dignity: data.dignity || "neutral",
    nakshatra: data.nakshatra || {},
  }));

  // Dasha timeline
  const dashaTimeline: any[] = dasha.full_timeline || [];
  const currentDasha = dasha.current;

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="paper-frame">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            吠陀占星 · Jyotish 出生盘
          </h3>
          <div className="flex gap-2 text-xs flex-wrap">
            <span className="paper-tag" style={{ background: "rgba(201,162,75,0.10)", color: COLOR.gold }}>
              Lahiri Ayanamsa {typeof ayanamsa === "number" ? ayanamsa.toFixed(2) + "°" : ""}
            </span>
            <span className="paper-tag paper-tag-west">恒星黄道</span>
            {asc && (
              <span className="paper-tag" style={{ background: "rgba(91,141,239,0.10)", color: COLOR.azure }}>
                Lagna {asc.sign}
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-4 text-xs flex-wrap">
          <Stat label="上升" value={asc ? `${asc.sign} ${degreeText(asc.degree)}` : "—"} tone="azure" />
          <Stat label="月亮星宿" value={moonNakshatra.name_ia ? `${moonNakshatra.name_ia} · Pada ${moonNakshatra.pada || "?"}` : "—"} tone="gold" />
          <Stat label="Ayanamsa" value={typeof ayanamsa === "number" ? `${ayanamsa.toFixed(4)}°` : "—"} tone="ink" />
          <Stat label="体系" value="Vimshottari 120yr" tone="ink" />
        </div>
      </div>

      {/* ── North Indian Chart (Diamond Layout) ── */}
      <div className="paper-frame flex flex-col items-center">
        <h4 className="text-sm mb-4 self-start" style={{ color: COLOR.gold }}>
          北印度方盘 · 宫位落星
        </h4>
        <div className="grid grid-cols-4 grid-rows-4 gap-1.5 w-full max-w-md mx-auto"
          style={{ aspectRatio: "1 / 1" }}>
          {Array.from({ length: 12 }, (_, i) => {
            // North Indian: houses counter-clockwise from top-center
            // Row 0: H12 H1 H2 H3 | Row 1: H11 — — H4 | Row 2: H10 — — H5 | Row 3: H9 H8 H7 H6
            const houseIdx = [12, 1, 2, 3, 11, -1, -1, 4, 10, -1, -1, 5, 9, 8, 7, 6][i];
            if (houseIdx < 0) {
              // Center cells
              return <div key={i} />;
            }
            const planetsInHouse = planetRows.filter((p) => p.house === houseIdx);
            const hSign = houses.find((h: any) => h.house === houseIdx);
            const signForHouse = hSign
              ? SIGNS[Math.floor(hSign.cusp_lon / 30) % 12]
              : SIGNS[(houseIdx + (asc ? Math.floor(asc.lon / 30) : 0) - 1) % 12];
            const signSym = SIGN_SYM[SIGNS.indexOf(signForHouse)];
            const isLagna = houseIdx === 1;
            return (
              <div key={i} className="rounded p-1.5 text-[10px] sm:text-xs flex flex-col"
                style={{
                  background: isLagna ? "rgba(91,141,239,0.06)" : "var(--paper-2)",
                  border: `1px solid ${isLagna ? COLOR.azure + "40" : COLOR.line}`,
                  minHeight: 52,
                }}>
                <div className="flex justify-between items-center">
                  <span style={{ color: isLagna ? COLOR.azure : COLOR.gold, fontWeight: 600 }}>
                    {houseIdx}
                  </span>
                  <span style={{ color: COLOR.muted, fontSize: 9 }}>
                    {signSym} {signForHouse}
                  </span>
                </div>
                <div className="mt-1 leading-tight space-y-0.5">
                  {planetsInHouse.length === 0
                    ? <span style={{ color: COLOR.muted }}>—</span>
                    : planetsInHouse.map((p) => (
                        <div key={p.name} className="flex items-center gap-1">
                          <span style={{ color: COLOR.gold, fontSize: 10, fontWeight: 600 }}>
                            {p.name[0]}
                          </span>
                          <span style={{ color: COLOR.inkSoft }}>
                            {degreeText(p.degree)}
                          </span>
                        </div>
                      ))
                  }
                </div>
              </div>
            );
          })}
        </div>
        <p className="text-[10px] mt-2" style={{ color: COLOR.muted }}>
          宫位编号 · 逆时针排列 (北印度传统) · 宫头星座标注
        </p>
      </div>

      {/* ── Planet Detail Table ── */}
      <div className="paper-frame">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          行星明细
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 含星宿·Pada·尊贵
          </span>
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}>
                <th className="text-left py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>行星</th>
                <th className="text-left py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>星座</th>
                <th className="text-right py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>度数</th>
                <th className="text-left py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>星宿</th>
                <th className="text-right py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>Pada</th>
                <th className="text-right py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>宫</th>
                <th className="text-left py-1.5 font-normal" style={{ color: COLOR.muted }}>尊贵</th>
              </tr>
            </thead>
            <tbody>
              {planetRows.map((p) => {
                const n = p.nakshatra || {};
                const dColor = DIGNITY_COLOR[p.dignity] || COLOR.muted;
                return (
                  <tr key={p.name} style={{ borderBottom: `1px solid ${COLOR.lineSoft}12` }}>
                    <td className="py-1.5 pr-2" style={{ color: COLOR.ink, fontWeight: 600 }}>{p.name}</td>
                    <td className="py-1.5 pr-2" style={{ color: COLOR.inkSoft }}>
                      {SIGN_SYM[p.signIdx] || ""} {p.sign}
                    </td>
                    <td className="py-1.5 pr-2 text-right font-mono" style={{ color: COLOR.ink }}>
                      {degreeText(p.degree)}
                    </td>
                    <td className="py-1.5 pr-2" style={{ color: COLOR.gold }}>
                      {n.name_ia || "—"}
                    </td>
                    <td className="py-1.5 pr-2 text-right" style={{ color: COLOR.inkSoft }}>
                      {n.pada || "—"}
                    </td>
                    <td className="py-1.5 pr-2 text-right" style={{ color: COLOR.gold }}>
                      {p.house || "—"}
                    </td>
                    <td className="py-1.5" style={{ color: dColor }}>
                      {DIGNITY_LABEL[p.dignity] || p.dignity}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Nakshatra + Elements ── */}
      <div className="grid sm:grid-cols-2 gap-4">
        {/* Moon Nakshatra details */}
        <div className="card space-y-3">
          <h4 className="text-sm" style={{ color: COLOR.gold }}>月亮星宿 · Janma Nakshatra</h4>
          {moonNakshatra.name_ia ? (
            <>
              <div className="flex items-baseline gap-3">
                <span className="text-xl font-display" style={{ color: COLOR.goldBright }}>
                  {moonNakshatra.name_ia}
                </span>
                <span className="text-xs" style={{ color: COLOR.muted }}>
                  Pada {moonNakshatra.pada || "—"}
                </span>
              </div>
              <div className="flex gap-3 text-xs flex-wrap">
                <Stat label="主星" value={moonNakshatra.lord || "—"} tone="gold" />
                <Stat label=" Pada 度数" value={moonNakshatra.pada_lon ? `${moonNakshatra.pada_lon.toFixed(2)}°` : "—"} tone="ink" />
                <Stat label="索引" value={moonNakshatra.index ? `第${moonNakshatra.index}宿` : "—"} tone="ink" />
              </div>
              {/* 27 Nakshatra ruler reference */}
              <div className="text-[10px] pt-2 border-t" style={{ color: COLOR.muted, borderColor: COLOR.lineSoft }}>
                27 宿 · 每宿 13°20′ · 每宿 4 Pada (各 3°20′)
              </div>
            </>
          ) : (
            <p className="text-xs" style={{ color: COLOR.muted }}>需要月亮位置</p>
          )}
        </div>

        {/* Element distribution */}
        <div className="paper-frame flex justify-center items-center">
          <ElementsRadar elements={chart.normalized.elements || {}} variant="four" title="四元素分布" />
        </div>
      </div>

      {/* ── Vimshottari Dasha ── */}
      {dashaTimeline.length > 0 && (
        <div className="paper-frame">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
            Vimshottari Dasha · 120 年大运
            <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
              — 出生星宿主星: {dasha.birth_nakshatra_lord || "—"}
            </span>
          </h4>

          {/* Current Dasha highlight */}
          {currentDasha && (
            <div className="rounded-md p-3 mb-4" style={{
              background: "rgba(201,162,75,0.06)",
              border: `1px solid ${COLOR.goldDim}40`,
            }}>
              <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: COLOR.muted }}>
                当前大运
              </div>
              <div className="flex items-baseline gap-3 flex-wrap">
                <span className="text-lg font-display" style={{ color: COLOR.goldBright }}>
                  {currentDasha.maha_lord} Mahadasha
                </span>
                <span className="text-sm" style={{ color: COLOR.inkSoft }}>
                  {currentDasha.maha_start} — {currentDasha.maha_end}
                </span>
                <span className="text-xs px-1.5 py-0.5 rounded" style={{
                  background: "rgba(91,141,239,0.10)", color: COLOR.azure,
                }}>
                  已完成 {currentDasha.elapsed_in_maha_pct}%
                </span>
              </div>
              {currentDasha.antara_lord && (
                <div className="mt-2 text-sm" style={{ color: COLOR.inkSoft }}>
                  <span style={{ color: COLOR.muted }}>子运 Antardasha: </span>
                  <span style={{ color: COLOR.jade }}>{currentDasha.antara_lord}</span>
                  <span className="text-xs ml-2" style={{ color: COLOR.muted }}>
                    {currentDasha.antara_start} — {currentDasha.antara_end}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Full timeline */}
          <div className="space-y-1">
            {dashaTimeline.map((t: any, i: number) => {
              const isCurrent = currentDasha && t.lord === currentDasha.maha_lord;
              const dColor = DASHA_COLORS[t.lord] || COLOR.muted;
              return (
                <div key={i} className="flex items-center gap-2 text-xs py-1 px-2 rounded"
                  style={{
                    background: isCurrent ? "rgba(201,162,75,0.06)" : "transparent",
                    border: isCurrent ? `1px solid ${COLOR.goldDim}30` : `1px solid transparent`,
                  }}>
                  {/* Progress bar */}
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
                    <div className="h-full rounded-full"
                      style={{ width: `${(t.years / 20) * 100}%`, background: dColor }} />
                  </div>
                  <span style={{ color: dColor, fontWeight: 600, width: 72 }}>{t.lord}</span>
                  <span className="font-mono" style={{ color: COLOR.ink }}>{t.years}yr</span>
                  <span style={{ color: COLOR.muted, width: 120, textAlign: "right" }}>
                    {t.start} → {t.end}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-3 text-[10px] space-y-0.5" style={{ color: COLOR.muted }}>
            <p>Vimshottari Dasha · 120 年周期 · 9 星轮值 · 大运/子运体系</p>
            <p>出生前已消耗大运: {dasha.dasha_elapsed_years_at_birth} 年 · 剩余: {dasha.dasha_remaining_years_at_birth} 年</p>
          </div>
        </div>
      )}

      {/* ── Yogas ── */}
      {yogas.length > 0 && (
        <div className="paper-frame">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
            Yoga 检测
            <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
              — 行星组合形成的特殊格局
            </span>
          </h4>
          <div className="space-y-2">
            {yogas.map((y: any, i: number) => {
              const strengthColor =
                y.strength === "strong" ? COLOR.jade
                : y.strength === "moderate" ? COLOR.gold
                : COLOR.muted;
              return (
                <div key={i} className="rounded-md p-3 text-sm"
                  style={{ background: "var(--paper-2)", border: `1px solid ${COLOR.lineSoft}` }}>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span style={{ color: COLOR.goldBright, fontWeight: 600 }}>{y.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded"
                      style={{ background: `${strengthColor}15`, color: strengthColor }}>
                      {y.strength === "strong" ? "强力" : y.strength === "moderate" ? "中等" : "弱"}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
                    {y.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Rahu/Ketu ── */}
      {nodes.rahu && (
        <div className="paper-frame">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>月交点 · Rahu & Ketu</h4>
          <div className="grid grid-cols-2 gap-4 text-xs">
            {(["rahu", "ketu"] as const).map((node) => {
              const n = nodes[node];
              if (!n) return null;
              return (
                <div key={node} className="rounded p-3" style={{
                  background: node === "rahu" ? "rgba(200,85,61,0.04)" : "rgba(91,141,239,0.04)",
                  border: `1px solid ${COLOR.lineSoft}`,
                }}>
                  <div className="text-sm font-semibold mb-1"
                    style={{ color: node === "rahu" ? COLOR.danger : COLOR.azure }}>
                    {node === "rahu" ? "☊ Rahu 罗睺" : "☋ Ketu 计都"}
                  </div>
                  <div className="space-y-0.5" style={{ color: COLOR.inkSoft }}>
                    <div>恒星黄经: {n.lon_sidereal?.toFixed(2)}°</div>
                    <div>星座: {n.sign?.sign || n.sign} {n.sign?.degree ? degreeText(n.sign.degree) : ""}</div>
                    <div>星宿: {n.name_ia} · Pada {n.pada}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
        <p>吠陀占星 · Sidereal Lahiri · 整宫制 · 27 Nakshatras · Vimshottari Dasha</p>
        <p>Rahu/Ketu 使用均值月交点 (Meeus 公式) · 木星/土星使用质心 · Skyfield + JPL DE421</p>
      </div>
    </div>
  );
}
