// 西方占星: 圆形星盘 + 宫位线 + 相位网格 + 元素/模式统计
// 专业级星盘渲染: ASC 在左 (东方地平线)、MC 在上、星座环逆时针
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";
import { ElementsRadar } from "../ElementsRadar";
import { Jargon } from "../Jargon";

const ZODIAC = [
  { name: "白羊", sym: "♈", en: "Aries" },
  { name: "金牛", sym: "♉", en: "Taurus" },
  { name: "双子", sym: "♊", en: "Gemini" },
  { name: "巨蟹", sym: "♋", en: "Cancer" },
  { name: "狮子", sym: "♌", en: "Leo" },
  { name: "处女", sym: "♍", en: "Virgo" },
  { name: "天秤", sym: "♎", en: "Libra" },
  { name: "天蝎", sym: "♏", en: "Scorpio" },
  { name: "射手", sym: "♐", en: "Sagittarius" },
  { name: "摩羯", sym: "♑", en: "Capricorn" },
  { name: "水瓶", sym: "♒", en: "Aquarius" },
  { name: "双鱼", sym: "♓", en: "Pisces" },
];

const PLANET_GLYPH: Record<string, string> = {
  "太阳": "☉", "月亮": "☽", "水星": "☿", "金星": "♀",
  "火星": "♂", "木星": "♃", "土星": "♄",
  "天王星": "♅", "海王星": "♆", "冥王星": "♇",
};

const ASPECT_META: Record<string, { color: string; label: string; sym: string }> = {
  "合相": { color: "#5AA469", label: "合", sym: "☌" },
  "拱相": { color: "#4FB3A0", label: "拱", sym: "△" },
  "六分相": { color: "#5B8DEF", label: "六分", sym: "⚹" },
  "刑相": { color: "#D4A843", label: "刑", sym: "□" },
  "冲相": { color: "#C8553D", label: "冲", sym: "☍" },
};

const ASPECT_GLOSS: Record<string, string> = {
  "合相": "合·能量融合", "拱相": "拱·顺畅和谐",
  "六分相": "六分·机遇助力", "刑相": "刑·张力挑战",
  "冲相": "冲·对立平衡",
};

const MODALITY: Record<number, string> = {
  0: "基本", 1: "固定", 2: "变动",
  3: "基本", 4: "固定", 5: "变动",
  6: "基本", 7: "固定", 8: "变动",
  9: "基本", 10: "固定", 11: "变动",
};

const ELEMENT_COLOR: Record<string, string> = {
  "火": "#C8553D", "土": "#C8A951", "风": "#C8C2B0", "水": "#5B8DEF",
};

function signIndex(name: unknown): number {
  return ZODIAC.findIndex((z) => z.name === name);
}

function degreeText(value: unknown): string {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return "0.00°";
  return `${n.toFixed(2)}°`;
}

function fmtDeg(deg: number): string {
  const d = Math.floor(deg);
  const m = Math.floor((deg - d) * 60);
  return `${d}°${m.toString().padStart(2, "0")}′`;
}

export function WesternChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const planets: Record<string, any> = r.planets || {};
  const aspects: any[] = Array.isArray(r.aspects) ? r.aspects : [];
  const houses: any[] = Array.isArray(r.houses) ? r.houses : [];
  const asc = r.ascendant;

  const size = 420;
  const cx = size / 2;
  const cy = size / 2;
  const R = size / 2 - 14;
  const R_SIGN = R - 28;
  const R_HOUSE = R_SIGN - 20;
  const R_PLANET = R_HOUSE - 26;
  const R_CENTER = R_PLANET - 20;

  // ── ASC longitude (full 0-360) ──
  const ascIdx = signIndex(asc?.sign);
  const ascLon = ascIdx >= 0 ? ascIdx * 30 + (Number(asc.degree) || 0) : 0;

  // ── Professional orientation: ASC at LEFT, zodiac counter-clockwise ──
  // polarAngle = (270 - ascLon + zodiacLon) % 360
  // polar(0)=top, polar(90)=right, polar(180)=bottom, polar(270)=left
  const toAngle = (zodiacLon: number) => ((270 - ascLon + zodiacLon) % 360 + 360) % 360;

  const polar = (zodiacLon: number, radius: number) => {
    const angle = toAngle(zodiacLon);
    const rad = ((angle - 90) * Math.PI) / 180;
    return [cx + Math.cos(rad) * radius, cy + Math.sin(rad) * radius];
  };

  // ── Build planet rows ──
  const planetRows = Object.entries(planets)
    .map(([name, planet]) => {
      const idx = signIndex(planet?.sign);
      if (idx < 0) return null;
      const lon = typeof planet.lon === "number" ? planet.lon : idx * 30 + (Number(planet.degree) || 0);
      let houseNum = idx + 1;
      if (houses.length === 12) {
        for (let hi = 0; hi < 12; hi++) {
          const cuspS = houses[hi].cusp_lon;
          const cuspE = houses[(hi + 1) % 12].cusp_lon;
          if (cuspS < cuspE) { if (lon >= cuspS && lon < cuspE) { houseNum = houses[hi].house; break; } }
          else { if (lon >= cuspS || lon < cuspE) { houseNum = houses[hi].house; break; } }
        }
      }
      return { name, planet, angle: lon, glyph: PLANET_GLYPH[name] || name[0], house: houseNum };
    })
    .filter(Boolean) as Array<{ name: string; planet: any; angle: number; glyph: string; house: number }>;

  const planetAngles = Object.fromEntries(planetRows.map((row) => [row.name, row.angle]));

  // ── MC: approximate from ASC + 90° (whole-sign approximation) ──
  const mcLon = (ascLon + 270) % 360;

  // Element & modality counts
  const elemCount: Record<string, number> = { "火": 0, "土": 0, "风": 0, "水": 0 };
  const modalityCount: Record<string, number> = { "基本": 0, "固定": 0, "变动": 0 };
  planetRows.forEach(({ planet }) => {
    const el = planet.element;
    if (el && elemCount[el] !== undefined) elemCount[el]++;
    const idx = signIndex(planet.sign);
    if (idx >= 0) {
      const mod = MODALITY[idx];
      if (mod) modalityCount[mod] = (modalityCount[mod] || 0) + 1;
    }
  });

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="card">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            西方占星 · 本命星盘
          </h3>
          <div className="flex gap-2 text-xs flex-wrap">
            {asc && (
              <span className="tag" style={{ background: "rgba(91,141,239,0.10)", color: COLOR.azure }}>
                ASC {asc.sign} {degreeText(asc.degree)}
              </span>
            )}
            <span className="tag tag-west">{r.rule_version === "v2" ? "十大行星" : "古典七星"}</span>
          </div>
        </div>

        <div className="flex gap-4 text-xs flex-wrap">
          <Stat label="上升 ASC" value={asc ? `${asc.sign} ${fmtDeg(ascLon % 30)}` : "—"} tone="azure" />
          <Stat label="中天 MC" value={mcLon != null ? `${ZODIAC[Math.floor(mcLon / 30) % 12]?.name} ${fmtDeg(mcLon % 30)}` : "—"} tone="ink" />
          <Stat label="宫位制" value="整宫 Whole Sign" tone="ink" />
          <Stat label="行星" value={`${planetRows.length} 颗`} tone="gold" />
        </div>
      </div>

      {/* ── Circular Chart ── */}
      <div className="card flex flex-col items-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label="西方占星星盘">
          {/* Outer rim */}
          <circle cx={cx} cy={cy} r={R} fill="none" stroke={COLOR.line} strokeWidth={1.5} />
          <circle cx={cx} cy={cy} r={R_SIGN} fill="none" stroke={COLOR.line} strokeWidth={0.6} />
          <circle cx={cx} cy={cy} r={R_HOUSE} fill="none" stroke={COLOR.lineSoft} strokeWidth={0.5} />
          <circle cx={cx} cy={cy} r={R_PLANET} fill="none" stroke={COLOR.line} strokeWidth={0.6} />
          <circle cx={cx} cy={cy} r={R_CENTER} fill="none" stroke={COLOR.lineSoft} strokeWidth={0.3} />

          {/* Sign symbols in outer ring (12 equal segments, rotated with chart) */}
          {Array.from({ length: 12 }, (_, i) => {
            const signLon = i * 30; // sign starts at i*30
            const midLon = signLon + 15; // middle of sign
            const labelP = polar(midLon, (R + R_SIGN) / 2);
            // Sign boundary lines
            const p1 = polar(signLon, R);
            const p2 = polar(signLon, R_SIGN);
            return (
              <g key={i}>
                <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke={COLOR.line} strokeWidth={0.8} />
                <text x={labelP[0]} y={labelP[1]} textAnchor="middle" dominantBaseline="central"
                  fill={COLOR.ink} fontSize={15} fontWeight={600}>
                  {ZODIAC[i].sym}
                </text>
              </g>
            );
          })}

          {/* House cusps + numbers */}
          {houses.map((h: any) => {
            const cusp = h.cusp_lon;
            const p1 = polar(cusp, R_SIGN);
            const p2 = polar(cusp, R_HOUSE);
            const labelP = polar(cusp + 10, (R_SIGN + R_HOUSE) / 2);
            return (
              <g key={`h${h.house}`}>
                <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke={COLOR.goldDim} strokeWidth={0.6} />
                <text x={labelP[0]} y={labelP[1]} textAnchor="middle" dominantBaseline="central"
                  fill={COLOR.gold} fontSize={9} fontWeight={600}>
                  {h.house}
                </text>
              </g>
            );
          })}

          {/* House extension lines inward */}
          {houses.map((h: any) => {
            const p1 = polar(h.cusp_lon, R_HOUSE);
            const p2 = polar(h.cusp_lon, R_CENTER);
            return <line key={`he${h.house}`} x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke={COLOR.lineSoft} strokeWidth={0.3} />;
          })}

          {/* ASC line — bold with marker at outer ring */}
          {ascIdx >= 0 && (() => {
            const p1 = polar(ascLon, R + 4);
            const p2 = polar(ascLon, R_CENTER);
            return (
              <g>
                <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]}
                  stroke={COLOR.azure} strokeWidth={2} strokeDasharray="6 4" strokeLinecap="round" />
                <circle cx={p1[0]} cy={p1[1]} r={4} fill={COLOR.azure} stroke={COLOR.bgDeep} strokeWidth={1} />
              </g>
            );
          })()}

          {/* MC line */}
          <g>
            {(() => {
              const p1 = polar(mcLon, R);
              const p2 = polar(mcLon, R_CENTER);
              return (
                <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]}
                  stroke={COLOR.danger} strokeWidth={1} strokeDasharray="4 4" strokeLinecap="round" />
              );
            })()}
          </g>

          {/* Aspect lines between planets */}
          {aspects.map((aspect: any, i: number) => {
            const a1 = planetAngles[aspect.a];
            const a2 = planetAngles[aspect.b];
            if (a1 == null || a2 == null) return null;
            const p1 = polar(a1, R_PLANET);
            const p2 = polar(a2, R_PLANET);
            const meta = ASPECT_META[aspect.aspect] || { color: COLOR.muted };
            return (
              <line key={i} x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]}
                stroke={meta.color} strokeWidth={1.2} strokeOpacity={0.4} strokeLinecap="round" />
            );
          })}

          {/* Planet markers with degree labels */}
          {planetRows.map(({ name, angle, glyph }) => {
            const p = polar(angle, R_PLANET);
            const labelP = polar(angle, R_HOUSE - 5);
            const deg = degreeText(angle % 30);
            return (
              <g key={name}>
                <circle cx={p[0]} cy={p[1]} r={10.5}
                  fill="rgba(8,10,15,0.92)" stroke={COLOR.gold} strokeWidth={1.3} />
                <text x={p[0]} y={p[1] + 1} textAnchor="middle" dominantBaseline="central"
                  fill={COLOR.ink} fontSize={15} fontWeight={600}>
                  {glyph}
                </text>
                {/* Outer degree label */}
                <text x={labelP[0]} y={labelP[1]} textAnchor="middle" dominantBaseline="central"
                  fill={COLOR.muted} fontSize={7} fontFamily="monospace">
                  {deg}
                </text>
              </g>
            );
          })}

          {/* Center: ASC sign symbol + detail */}
          <text x={cx} y={cy - 8} textAnchor="middle"
            fill={COLOR.gold} fontSize={26} fontWeight={700}>
            {asc ? ZODIAC[signIndex(asc.sign)]?.sym || "" : "?"}
          </text>
          <text x={cx} y={cy + 14} textAnchor="middle"
            fill={COLOR.inkSoft} fontSize={10}>
            ASC {asc?.sign || ""} {fmtDeg(ascLon % 30)}
          </text>
        </svg>

        {/* Orientation hint */}
        <p className="text-[10px] mt-2" style={{ color: COLOR.muted }}>
          ASC 东方地平线 (左) · MC 中天 (上) · 星座逆时针排列
        </p>
      </div>

      {/* ── Elements & Modality ── */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="card flex justify-center items-center">
          <ElementsRadar elements={chart.normalized.elements || {}} variant="four" title="四元素分布" />
        </div>
        <div className="card space-y-3">
          <h4 className="text-sm" style={{ color: COLOR.gold }}>元素 · 模式平衡</h4>
          {["火", "土", "风", "水"].map((el) => {
            const count = elemCount[el] || 0;
            const barW = Math.max(4, (count / Math.max(1, planetRows.length)) * 100);
            return (
              <div key={el} className="flex items-center gap-2 text-xs">
                <span className="w-6 text-right" style={{ color: COLOR.muted }}>{el}</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
                  <div className="h-full rounded-full" style={{ width: `${barW}%`, background: ELEMENT_COLOR[el] || COLOR.muted }} />
                </div>
                <span className="w-4 text-right font-mono" style={{ color: COLOR.ink }}>{count}</span>
              </div>
            );
          })}
          <div className="pt-2 border-t" style={{ borderColor: COLOR.lineSoft }}>
            <div className="flex gap-4 text-xs">
              {Object.entries(modalityCount).map(([mod, count]) => (
                <span key={mod} style={{ color: COLOR.inkSoft }}>
                  <span style={{ color: COLOR.muted }}>{mod}</span>{" "}
                  <span style={{ color: COLOR.gold }}>{count}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Planet Detail Table ── */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          行星明细
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}>
                <th className="text-left py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>符</th>
                <th className="text-left py-1.5 pr-3 font-normal" style={{ color: COLOR.muted }}>行星</th>
                <th className="text-left py-1.5 pr-3 font-normal" style={{ color: COLOR.muted }}>星座</th>
                <th className="text-right py-1.5 pr-3 font-normal" style={{ color: COLOR.muted }}>黄经</th>
                <th className="text-right py-1.5 pr-3 font-normal" style={{ color: COLOR.muted }}>宫位</th>
                <th className="text-left py-1.5 pr-2 font-normal" style={{ color: COLOR.muted }}>元素</th>
                <th className="text-left py-1.5 font-normal" style={{ color: COLOR.muted }}>模式</th>
              </tr>
            </thead>
            <tbody>
              {planetRows.map(({ name, planet, glyph, angle, house }) => {
                const sIdx = signIndex(planet.sign);
                return (
                  <tr key={name} style={{ borderBottom: `1px solid ${COLOR.lineSoft}12` }}>
                    <td className="py-1.5 pr-2" style={{ color: COLOR.gold, fontSize: 15 }}>{glyph}</td>
                    <td className="py-1.5 pr-3 font-semibold" style={{ color: COLOR.ink }}>{name}</td>
                    <td className="py-1.5 pr-3" style={{ color: COLOR.inkSoft }}>
                      {ZODIAC[sIdx]?.sym} {planet.sign}
                    </td>
                    <td className="py-1.5 pr-3 text-right font-mono" style={{ color: COLOR.ink }}>{fmtDeg(angle % 30)}</td>
                    <td className="py-1.5 pr-3 text-right" style={{ color: COLOR.gold }}>第{house}宫</td>
                    <td className="py-1.5 pr-2" style={{ color: ELEMENT_COLOR[planet.element] || COLOR.muted }}>{planet.element}</td>
                    <td className="py-1.5" style={{ color: COLOR.muted }}>{MODALITY[sIdx] || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Aspect Grid ── */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          相位表
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>— 行星间的角度关系与容许度</span>
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-5 gap-y-1.5">
          {aspects.map((aspect: any, i: number) => {
            const meta = ASPECT_META[aspect.aspect] || { color: COLOR.muted, sym: "·", label: aspect.aspect };
            return (
              <div key={i} className="flex items-center gap-1.5 text-xs py-1"
                style={{ borderBottom: `1px solid ${COLOR.lineSoft}12` }}>
                <span style={{ color: meta.color, fontSize: 13 }}>{meta.sym}</span>
                <span style={{ color: COLOR.ink }}>{aspect.a}</span>
                <span style={{ color: meta.color, fontWeight: 600 }}>{meta.label}</span>
                <span style={{ color: COLOR.ink }}>{aspect.b}</span>
                <span className="ml-auto text-[10px] font-mono" style={{ color: COLOR.muted }}>
                  orb {aspect.orb?.toFixed(1)}°
                </span>
              </div>
            );
          })}
        </div>
        {!aspects.length && <p className="text-xs" style={{ color: COLOR.muted }}>暂无主要相位</p>}
        <div className="mt-3 pt-2 flex gap-4 flex-wrap text-[10px]"
          style={{ borderTop: `1px solid ${COLOR.lineSoft}` }}>
          {Object.entries(ASPECT_GLOSS).map(([aspect, gloss]) => {
            const meta = ASPECT_META[aspect];
            return (
              <span key={aspect} className="flex items-center gap-1" style={{ color: COLOR.muted }}>
                <span style={{ color: meta?.color }}>{meta?.sym}</span>
                {gloss}
              </span>
            );
          })}
        </div>
      </div>

      {/* ── House Table ── */}
      {houses.length > 0 && (
        <div className="card">
          <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>十二宫位 · 整宫制</h4>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2 text-xs">
            {houses.map((h: any) => {
              const signAtCusp = ZODIAC[Math.floor(h.cusp_lon / 30) % 12];
              const isAscHouse = ascIdx >= 0 && Math.floor(ascLon / 30) === Math.floor(h.cusp_lon / 30);
              return (
                <div key={h.house} className="rounded p-2 text-center"
                  style={{
                    background: isAscHouse ? "rgba(91,141,239,0.06)" : "rgba(8,10,15,0.3)",
                    border: `1px solid ${isAscHouse ? COLOR.azure + "30" : COLOR.lineSoft}`,
                  }}>
                  <div style={{ color: isAscHouse ? COLOR.azure : COLOR.gold }} className="text-[10px]">
                    第{h.house}宫
                  </div>
                  <div className="mt-0.5" style={{ color: COLOR.inkSoft }}>
                    {signAtCusp?.sym} {signAtCusp?.name}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── v2: 分布分析 ── */}
      {r.distribution && (
        <div className="card space-y-2">
          <h4 className="text-sm" style={{ color: COLOR.goldBright }}>📊 星盘分布分析</h4>
          {r.distribution.interpretation && (
            <div className="text-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
              {r.distribution.interpretation}
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            <div className="rounded p-2" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--line-soft)" }}>
              <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>主导元素</div>
              <span style={{ color: COLOR.goldBright }}>
                {r.distribution.dominant_element || "均衡"}
              </span>
            </div>
            <div className="rounded p-2" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--line-soft)" }}>
              <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>主导模式</div>
              <span style={{ color: COLOR.jade }}>
                {r.distribution.dominant_modality || "均衡"}
              </span>
            </div>
            {r.distribution.missing_elements?.length > 0 && (
              <div className="rounded p-2" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--line-soft)" }}>
                <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>缺失元素</div>
                <span style={{ color: COLOR.danger }}>
                  {r.distribution.missing_elements.join(", ")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── v2: 上升守护星 ── */}
      {r.ascendant_ruler?.ruler_position && (
        <div className="card space-y-1.5">
          <h4 className="text-sm" style={{ color: COLOR.goldBright }}>🌟 上升守护星</h4>
          <div className="text-xs" style={{ color: COLOR.inkSoft }}>
            上升星座的守护星是 <span style={{ color: COLOR.gold }}>{r.ascendant_ruler.ruler_position.planet}</span>
            {r.ascendant_ruler.ruler_classical && r.ascendant_ruler.ruler !== r.ascendant_ruler.ruler_classical && (
              <span>（古典: {r.ascendant_ruler.ruler_classical}）</span>
            )}
            ，落入 <span style={{ color: COLOR.ink }}>{r.ascendant_ruler.ruler_position.sign}</span>
            · 第{r.ascendant_ruler.ruler_position.house}宫
            <span className="ml-1 tag text-[9px]" style={{ borderColor: COLOR.line, color: COLOR.goldBright }}>
              {r.ascendant_ruler.ruler_position.dignity}
            </span>
          </div>
        </div>
      )}

      {/* ── v2: 相位汇总 ── */}
      {r.aspect_summary && (
        <div className="card space-y-2">
          <h4 className="text-sm" style={{ color: COLOR.goldBright }}>🔗 相位分布</h4>
          <div className="flex items-center gap-3 text-xs flex-wrap">
            <span style={{ color: COLOR.inkSoft }}>
              总计 <span style={{ color: COLOR.ink }}>{r.aspect_summary.total}</span> 个相位
            </span>
            <span style={{ color: COLOR.muted }}>
              合: <span style={{ color: COLOR.ink }}>{r.aspect_summary.conjunctions}</span>
            </span>
            <span style={{ color: COLOR.muted }}>
              软: <span style={{ color: COLOR.jade }}>{r.aspect_summary.soft_aspects}</span>
              （拱+六合）
            </span>
            <span style={{ color: COLOR.muted }}>
              硬: <span style={{ color: COLOR.danger }}>{r.aspect_summary.hard_aspects}</span>
              （刑+冲）
            </span>
          </div>
          {r.aspect_summary.note && (
            <div className="text-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
              {r.aspect_summary.note}
            </div>
          )}
        </div>
      )}

      {/* ── v2: 宫主星 ── */}
      {r.house_rulers && Object.keys(r.house_rulers).length > 0 && (
        <div className="card">
          <h4 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>🏛 宫主星飞星</h4>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5 text-xs">
            {Object.entries(r.house_rulers as Record<string, any>).map(([houseName, hr]) => (
              <div key={houseName} className="rounded p-1.5 text-center"
                style={{ background: "rgba(8,10,15,0.4)", border: "1px solid var(--line-soft)" }}>
                <div className="text-[10px]" style={{ color: COLOR.muted }}>{houseName}</div>
                <div style={{ color: COLOR.gold }}>{hr.ruler}</div>
                {hr.ruler_in_house ? (
                  <div className="text-[9px]" style={{ color: COLOR.inkSoft }}>
                    → 第{hr.ruler_in_house}宫
                  </div>
                ) : (
                  <div className="text-[9px]" style={{ color: COLOR.muted }}>—</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
        <p>西方占星 · {r.planet_count || 7} 颗行星 · 整宫 Whole Sign · Skyfield + JPL DE421</p>
        <p>容许度: 合/冲 ±8° · 拱/刑 ±6° · 六分 ±4°</p>
      </div>
    </div>
  );
}
