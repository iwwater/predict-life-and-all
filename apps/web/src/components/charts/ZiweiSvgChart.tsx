// 紫微斗数 4 盘 SVG 可视化 (React JSX 版本)
// 本命/大限/流年/流月/小限 — 古籍×仪器 风格
// 后端 divination.viz.ziwei_svg 的 React 等价实现 (避免 server fetch)
import type React from "react";
import { useMemo, useState } from "react";

export type ScopeKey = "natal" | "decadal" | "yearly" | "monthly" | "xiaoxian";

interface Star {
  name?: string;
  mutagen?: string;
}

interface Palace {
  name?: string;
  index?: number | string;
  major_stars?: (string | Star)[];
  minor_stars?: (string | Star)[];
  adjective_stars?: (string | Star)[];
  is_body_palace?: boolean;
  is_body?: boolean;
  is_original_palace?: boolean;
  heavenly_stem?: string;
  earthly_branch?: string;
  changsheng12?: string;
}

interface HoroscopeItem {
  name?: string;
  index?: number | string;
  ganzhi?: string;
  heavenly_stem?: string;
  earthly_branch?: string;
  palace_names?: string[];
  mutagen?: string[];
  /** 小限所在宫位索引 (0..11) — 仅小限盘需要 */
  xiaoxian_palace_idx?: number;
  /** 出生年支 "子".."亥" — 用于小限查表 */
  birth_year_zhi?: string;
  /** 虚岁 (1-120) — 用于小限查表 */
  age?: number;
}

interface Horoscope {
  decadal?: HoroscopeItem;
  yearly?: HoroscopeItem;
  monthly?: HoroscopeItem;
  /** 小限数据 (顶层) */
  xiaoxian?: HoroscopeItem;
}

interface ZiweiSvgChartProps {
  scope: ScopeKey;
  palaces: Palace[];
  horoscope?: Horoscope;
  soul?: string;
  body?: string;
  fiveElements?: string;
  size?: number;
  /** 外部传入的小限宫位索引 (覆盖 horoscope.xiaoxian.xiaoxian_palace_idx) */
  xiaoxianPalaceIdx?: number;
}

// ── Design tokens (与后端 ziwei_svg.COLORS 对齐) ──
const C = {
  bg: "#F4EFE6",
  ink: "#2B2620",
  inkSoft: "#6B6256",
  cinnabar: "#B03A2E",
  gold: "#C9A24B",
  azure: "#2F4858",
  jade: "#5A7058",
  rule: "#C9BFA9",
  ruleSoft: "rgba(201, 191, 169, 0.55)",
  cellBg: "#FDFAF2",
  cellBgBody: "#FDE8E8",
  majorStar: "#7A1F1F",
  minorStar: "#5A5A5A",
  adjStar: "#9A7B3A",
  paper2: "#EDE6D8",
} as const;

const SCOPE_BADGE_COLOR: Record<string, string> = {
  禄: "#5A7058",
  权: "#2F4858",
  科: "#5A7058",
  忌: "#B03A2E",
};

const SCOPE_LABEL: Record<ScopeKey, string> = {
  natal: "本命盘",
  decadal: "大限盘",
  yearly: "流年盘",
  monthly: "流月盘",
  xiaoxian: "小限盘",
};

const SCOPE_SUBTITLE: Record<ScopeKey, string> = {
  natal: "生年四化 · 命主先天",
  decadal: "十年大限 · 行运主题",
  yearly: "本年流年 · 太岁所临",
  monthly: "本月流月 · 月建所主",
  xiaoxian: "小限所临 · 虚岁行运",
};

// 12 生肖起例宫位索引 (与后端 ziwei_xiaoxian.START_PALACE_IDX 对齐)
const XIAOXIAN_START_PALACE: Record<string, number> = {
  子: 0, 丑: 1, 寅: 2, 卯: 3,
  辰: 4, 巳: 5, 午: 6, 未: 7,
  申: 8, 酉: 9, 戌: 10, 亥: 11,
};

function lookupXiaoxianIdx(birthYearZhi: string, age: number): number {
  const start = XIAOXIAN_START_PALACE[birthYearZhi];
  if (start === undefined) return -1;
  if (!Number.isFinite(age) || age < 1) return -1;
  // 12 宫循环: 虚岁 1 → start, 2 → start+1, ... 12 → start+11, 13 → start
  const effAge = ((age - 1) % 12) + 1;
  return (start + (effAge - 1)) % 12;
}

// 12 宫在方盘的位置 (4×4 网格, 中宫 2×2 合并)
const PALACE_POSITIONS: Record<string, number> = {
  "0,0": 10, "0,1": 11, "0,2": 9, "0,3": 8,
  "1,0": 0,                    "1,3": 6,
  "2,0": 5,                    "2,3": 7,
  "3,0": 1,  "3,1": 2,  "3,2": 3,  "3,3": 4,
};

const NATAL_SIHUA: Record<string, Record<string, string>> = {
  甲: { 禄: "廉贞", 权: "破军", 科: "武曲", 忌: "太阳" },
  乙: { 禄: "天机", 权: "天梁", 科: "紫微", 忌: "太阴" },
  丙: { 禄: "天同", 权: "天机", 科: "文昌", 忌: "廉贞" },
  丁: { 禄: "太阴", 权: "天同", 科: "天机", 忌: "巨门" },
  戊: { 禄: "贪狼", 权: "太阴", 科: "右弼", 忌: "天机" },
  己: { 禄: "武曲", 权: "贪狼", 科: "天梁", 忌: "文曲" },
  庚: { 禄: "太阳", 权: "武曲", 科: "太阴", 忌: "天同" },
  辛: { 禄: "巨门", 权: "太阳", 科: "文曲", 忌: "文昌" },
  壬: { 禄: "天梁", 权: "紫微", 科: "左辅", 忌: "武曲" },
  癸: { 禄: "破军", 权: "巨门", 科: "太阴", 忌: "贪狼" },
};

function starName(s: string | Star | undefined): string {
  if (!s) return "";
  if (typeof s === "string") return s;
  return s.name || "";
}

function starMutagen(s: string | Star | undefined): string | undefined {
  if (!s) return undefined;
  if (typeof s === "string") return undefined;
  return s.mutagen;
}

function detectMutagen(starName: string, mutagens?: string[]): string | null {
  if (!mutagens || !starName) return null;
  for (const m of mutagens) {
    if (!m) continue;
    for (const hua of ["禄", "权", "科", "忌"] as const) {
      const patterns = [
        `${starName}化${hua}`,
        `化${hua}${starName}`,
        `${starName} 化${hua}`,
        `化${hua} ${starName}`,
      ];
      if (patterns.some((p) => m.includes(p))) return hua;
      if (starName && m.includes(starName) && m.includes(hua) && m.length <= 8) return hua;
    }
  }
  return null;
}

function buildMutagenMap(palaces: Palace[], mutagens?: string[]): Map<string, string> {
  const map = new Map<string, string>();
  palaces.forEach((p, idx) => {
    const all = [
      ...(p.major_stars || []),
      ...(p.minor_stars || []),
      ...(p.adjective_stars || []),
    ];
    for (const s of all) {
      const name = starName(s);
      const hua = detectMutagen(name, mutagens);
      if (hua) map.set(`${idx}:${name}`, hua);
    }
  });
  return map;
}

function sortedPalaces(palaces: Palace[]): Palace[] {
  const byIdx: Record<number, Palace> = {};
  palaces.forEach((p) => {
    const i = typeof p.index === "number" ? p.index : parseInt(String(p.index ?? "-1"), 10);
    if (i >= 0 && i < 12) byIdx[i] = p;
  });
  const out: Palace[] = [];
  for (let i = 0; i < 12; i++) {
    out.push(byIdx[i] || {
      name: "",
      index: i,
      is_body: false,
      is_body_palace: false,
      is_original_palace: false,
      heavenly_stem: "",
      earthly_branch: "",
      major_stars: [],
      minor_stars: [],
      adjective_stars: [],
      changsheng12: "",
    });
  }
  return out;
}

function getNatalMutagens(palaces: Palace[]): string[] {
  const sorted = sortedPalaces(palaces);
  const yearGan = sorted[0]?.heavenly_stem || "";
  const nat = NATAL_SIHUA[yearGan];
  if (!nat) return [];
  return Object.entries(nat).map(([hua, star]) => `${star}化${hua}`);
}

function getScopeInfo(scope: ScopeKey, palaces: Palace[], horoscope?: Horoscope): {
  ganzhi: string;
  mutagens: string[];
} {
  if (scope === "natal") {
    return {
      ganzhi: sortedPalaces(palaces)[0]?.heavenly_stem || "—",
      mutagens: getNatalMutagens(palaces),
    };
  }
  const item = horoscope?.[scope];
  if (!item) return { ganzhi: "—", mutagens: [] };
  return {
    ganzhi: item.ganzhi || (item.heavenly_stem && item.earthly_branch
      ? `${item.heavenly_stem}${item.earthly_branch}`
      : "—"),
    mutagens: item.mutagen || [],
  };
}

/** 小限盘: 计算小限所在宫位索引 + 用于右上角展示的 ganzhi. */
function getXiaoxianInfo(
  palaces: Palace[],
  horoscope?: Horoscope,
  overrideIdx?: number,
): { ganzhi: string; palaceIdx: number; age: number | undefined; zhi: string | undefined } {
  const item = horoscope?.xiaoxian;
  const zhi = item?.birth_year_zhi;
  const age = item?.age;

  // 优先级: override > item.xiaoxian_palace_idx > 查表
  let palaceIdx = -1;
  if (typeof overrideIdx === "number" && overrideIdx >= 0 && overrideIdx < 12) {
    palaceIdx = overrideIdx;
  } else if (item && typeof item.xiaoxian_palace_idx === "number"
             && item.xiaoxian_palace_idx >= 0 && item.xiaoxian_palace_idx < 12) {
    palaceIdx = item.xiaoxian_palace_idx;
  } else if (zhi && typeof age === "number") {
    palaceIdx = lookupXiaoxianIdx(zhi, age);
  }

  const baseGz = item?.ganzhi || (item?.heavenly_stem && item?.earthly_branch
    ? `${item.heavenly_stem}${item.earthly_branch}`
    : "");
  const ganzhi = baseGz
    ? (typeof age === "number" ? `${baseGz} 虚岁${age}` : baseGz)
    : (typeof age === "number" ? `虚岁${age}` : "—");

  return { ganzhi, palaceIdx, age, zhi };
}

// ── Main component ──
export function ZiweiSvgChart({
  scope,
  palaces,
  horoscope,
  soul = "",
  body = "",
  fiveElements = "",
  size = 600,
  xiaoxianPalaceIdx,
}: ZiweiSvgChartProps) {
  const sorted = sortedPalaces(palaces);
  const info = useMemo(
    () => (scope === "xiaoxian"
      ? getXiaoxianInfo(sorted, horoscope, xiaoxianPalaceIdx)
      : { ...getScopeInfo(scope, sorted, horoscope) }),
    [scope, sorted, horoscope, xiaoxianPalaceIdx],
  );
  const mMap = buildMutagenMap(sorted, "mutagens" in info ? info.mutagens : []);

  // 小限盘: 小限所在宫位索引 (用于高亮)
  const xiaoxianHi = useMemo<number | null>(() => {
    if (scope !== "xiaoxian") return null;
    if (!("palaceIdx" in info)) return null;
    const p = info.palaceIdx;
    if (typeof p === "number" && p >= 0 && p < 12) return p;
    return null;
  }, [scope, info]);

  // 交互态: hover/click 宫位
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [pinnedIdx, setPinnedIdx] = useState<number | null>(null);

  const cell = size / 4;
  const gridTop = 60;
  const gridHeight = cell * 4;
  const totalHeight = gridTop + gridHeight + 22;
  const midX = cell * 2;
  const midY = gridTop + cell * 2;
  const label = SCOPE_LABEL[scope];
  const subtitle = SCOPE_SUBTITLE[scope];
  const titleText = `紫微斗数 · ${label}`;

  // 当前展示 (pinned 优先, 否则 hover)
  const activeIdx = pinnedIdx ?? hoverIdx;
  const activePalace = activeIdx != null ? sorted[activeIdx] : null;

  return (
    <div
      className="ziwei-svg-wrapper"
      style={{ overflowX: "auto", overflowY: "hidden" }}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox={`0 0 ${size} ${totalHeight}`}
        width={size}
        height={totalHeight}
        className={`ziwei-scope-square ziwei-scope-${scope}`}
        style={{ display: "block", margin: "0 auto", maxWidth: "100%", height: "auto" }}
      >
        {/* 宣纸底 */}
        <rect width={size} height={totalHeight} fill={C.bg} />

        {/* ── 顶部古籍版心 ── */}
        <line x1={20} y1={14} x2={size - 20} y2={14} stroke={C.rule} strokeWidth={0.75} />
        <rect x={24} y={22} width={10} height={14} fill={C.cinnabar} />
        <text
          x={42}
          y={36}
          fontSize={20}
          fontWeight="bold"
          fill={C.ink}
          fontFamily="serif"
          letterSpacing="0.15em"
        >
          {titleText}
        </text>
        <text
          x={size - 24}
          y={32}
          textAnchor="end"
          fontSize={14}
          fontWeight="bold"
          fill={C.majorStar}
          fontFamily="'JetBrains Mono', monospace"
        >
          {info.ganzhi}
        </text>
        <text
          x={size - 24}
          y={50}
          textAnchor="end"
          fontSize={10}
          fill={C.adjStar}
          letterSpacing="0.1em"
          fontFamily="serif"
        >
          {subtitle}
        </text>
        <line x1={20} y1={58} x2={size - 20} y2={58} stroke={C.rule} strokeWidth={0.75} />

        {/* ── 12 宫方格 ── */}
        <rect
          x={0}
          y={gridTop}
          width={size}
          height={gridHeight}
          fill={C.cellBg}
          stroke={C.ink}
          strokeWidth={1.5}
        />
        {[1, 2, 3].map((i) => (
          <line
            key={`h${i}`}
            x1={0}
            y1={gridTop + cell * i}
            x2={size}
            y2={gridTop + cell * i}
            stroke={C.ink}
            strokeWidth={1}
          />
        ))}
        {[1, 2, 3].map((i) => (
          <line
            key={`v${i}`}
            x1={cell * i}
            y1={gridTop}
            x2={cell * i}
            y2={gridTop + gridHeight}
            stroke={C.ink}
            strokeWidth={1}
          />
        ))}

        {/* ── 中宫 ── */}
        <rect
          x={cell}
          y={gridTop + cell}
          width={cell * 2}
          height={cell * 2}
          fill={C.bg}
          stroke={C.ink}
          strokeWidth={0.75}
        />
        <circle
          cx={midX}
          cy={midY}
          r={cell * 0.72}
          fill="none"
          stroke={C.rule}
          strokeWidth={0.5}
          strokeDasharray="2 2"
        />
        <text
          x={midX}
          y={midY - cell * 0.35}
          textAnchor="middle"
          fontSize={20}
          fontWeight="bold"
          fill={C.ink}
          fontFamily="serif"
          letterSpacing="0.4em"
        >
          {label}
        </text>
        <text
          x={midX}
          y={midY - cell * 0.05}
          textAnchor="middle"
          fontSize={10}
          fill={C.adjStar}
          letterSpacing="0.15em"
          fontFamily="serif"
        >
          {subtitle}
        </text>
        {/* 命主/身主/五行局 */}
        {(() => {
          const lines: Array<[string, string, string]> = [];
          if (fiveElements) lines.push(["五行局", fiveElements, C.adjStar]);
          if (soul) lines.push(["命主", soul, C.cinnabar]);
          if (body) lines.push(["身主", body, C.majorStar]);
          return lines.map(([k, v, color], i) => (
            <text
              key={k}
              x={midX}
              y={midY + cell * 0.2 + i * 14}
              textAnchor="middle"
              fontSize={11}
              fill={color}
              fontFamily="serif"
            >
              {k} {v}
            </text>
          ));
        })()}

        {/* ── 12 宫位 ── */}
        {Object.entries(PALACE_POSITIONS).map(([key, pIdx]) => {
          const p = sorted[pIdx];
          if (!p) return null;
          const [row, col] = key.split(",").map(Number);
          const x = col * cell;
          const y = gridTop + row * cell;
          const cxCell = x + cell / 2;
          const isBody = p.is_body_palace || p.is_body;
          const isOrig = p.is_original_palace;
          const fill = isBody ? C.cellBgBody : C.cellBg;

          const major = p.major_stars || [];
          const minor = p.minor_stars || [];
          const adj = p.adjective_stars || [];

          // 高亮态: 小限/大限/流年(小限: xiaoxianHi) 与 active hover/pin
          const isXiaoHi = xiaoxianHi !== null && pIdx === xiaoxianHi;
          const isActive = activeIdx === pIdx;

          return (
            <g
              key={key}
              data-gong={pIdx}
              data-gong-name={p.name || ""}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHoverIdx(pIdx)}
              onMouseLeave={() => setHoverIdx((h) => (h === pIdx ? null : h))}
              onClick={() => setPinnedIdx((p) => (p === pIdx ? null : pIdx))}
            >
              <rect
                x={x + 1}
                y={y + 1}
                width={cell - 2}
                height={cell - 2}
                fill={isActive ? C.cellBgBody : fill}
                stroke="none"
              />
              {/* 小限高亮环 (朱砂虚线 + "小限" 角标) */}
              {isXiaoHi && (
                <>
                  <rect
                    x={x + 2}
                    y={y + 2}
                    width={cell - 4}
                    height={cell - 4}
                    fill="none"
                    stroke={C.cinnabar}
                    strokeWidth={2.5}
                    strokeDasharray="3 2"
                  />
                  <rect
                    x={x + cell - 38}
                    y={y + 22}
                    width={34}
                    height={13}
                    fill={C.cinnabar}
                  />
                  <text
                    x={x + cell - 21}
                    y={y + 32}
                    textAnchor="middle"
                    fontSize={9}
                    fontWeight="bold"
                    fill={C.bg}
                    fontFamily="serif"
                  >
                    小限
                  </text>
                </>
              )}
              {/* hover 边框提示 (轻量, 不抢戏) */}
              {isActive && !isXiaoHi && (
                <rect
                  x={x + 2}
                  y={y + 2}
                  width={cell - 4}
                  height={cell - 4}
                  fill="none"
                  stroke={C.azure}
                  strokeWidth={1.2}
                  strokeDasharray="2 2"
                  opacity={0.7}
                />
              )}
              <text
                x={x + 8}
                y={y + 16}
                fontSize={12}
                fontWeight="bold"
                fill={isBody ? C.cinnabar : C.ink}
                fontFamily="serif"
              >
                {p.name || ""}{isBody ? " ●" : isOrig ? " ☆" : ""}
              </text>
              {(p.heavenly_stem || p.earthly_branch) && (
                <text
                  x={x + cell - 8}
                  y={y + 16}
                  textAnchor="end"
                  fontSize={10}
                  fill={C.adjStar}
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {p.heavenly_stem}{p.earthly_branch}
                </text>
              )}
              <line
                x1={x + 4}
                y1={y + 22}
                x2={x + cell - 4}
                y2={y + 22}
                stroke={C.rule}
                strokeWidth={0.4}
              />
              {/* 主星 + 四化 badge */}
              {major.map((star, j) => {
                const name = starName(star);
                const hua = mMap.get(`${pIdx}:${name}`);
                const badgeColor = hua ? SCOPE_BADGE_COLOR[hua] : undefined;
                const ty = y + 38 + j * 16;
                return (
                  <g key={`m${j}`}>
                    <text
                      x={cxCell}
                      y={ty}
                      textAnchor="middle"
                      fontSize={13}
                      fontWeight="bold"
                      fill={C.majorStar}
                      fontFamily="serif"
                    >
                      {name}
                    </text>
                    {badgeColor && (
                      <>
                        <rect
                          x={cxCell + 24}
                          y={ty - 11}
                          width={14}
                          height={13}
                          fill={badgeColor}
                        />
                        <text
                          x={cxCell + 31}
                          y={ty}
                          textAnchor="middle"
                          fontSize={9}
                          fontWeight="bold"
                          fill={C.bg}
                          fontFamily="serif"
                        >
                          {hua}
                        </text>
                      </>
                    )}
                  </g>
                );
              })}
              {/* 副星 */}
              {minor.slice(0, 3).map((star, j) => {
                const name = starName(star);
                const hua = mMap.get(`${pIdx}:${name}`);
                const color = hua ? SCOPE_BADGE_COLOR[hua] : C.minorStar;
                const ty = y + 38 + major.length * 16 + j * 12;
                return (
                  <text
                    key={`n${j}`}
                    x={cxCell}
                    y={ty}
                    textAnchor="middle"
                    fontSize={10}
                    fill={color}
                    fontFamily="serif"
                  >
                    {name}{hua ? `·${hua}` : ""}
                  </text>
                );
              })}
              {/* 杂曜 */}
              {adj.slice(0, 2).map((star, j) => {
                const name = starName(star);
                const ty = y + 38 + major.length * 16 + Math.min(minor.length, 3) * 12 + j * 11;
                return (
                  <text
                    key={`a${j}`}
                    x={cxCell}
                    y={ty}
                    textAnchor="middle"
                    fontSize={9}
                    fill={C.adjStar}
                    fontFamily="serif"
                  >
                    {name}
                  </text>
                );
              })}
              {/* 长生 */}
              {p.changsheng12 && (
                <>
                  <line
                    x1={x + 4}
                    y1={y + cell - 16}
                    x2={x + cell - 4}
                    y2={y + cell - 16}
                    stroke={C.rule}
                    strokeWidth={0.4}
                  />
                  <text
                    x={x + cell - 8}
                    y={y + cell - 5}
                    textAnchor="end"
                    fontSize={9}
                    fill={C.adjStar}
                    fontFamily="'JetBrains Mono', monospace"
                  >
                    {p.changsheng12}
                  </text>
                </>
              )}
            </g>
          );
        })}

        {/* ── 底部图例 ── */}
        <line
          x1={20}
          y1={gridTop + gridHeight + 8}
          x2={size - 20}
          y2={gridTop + gridHeight + 8}
          stroke={C.rule}
          strokeWidth={0.5}
        />
        {(["禄", "权", "科", "忌"] as const).map((hua, i) => {
          const lx = 24 + i * 70;
          return (
            <g key={hua}>
              <rect
                x={lx}
                y={gridTop + gridHeight + 12}
                width={14}
                height={13}
                fill={SCOPE_BADGE_COLOR[hua]}
              />
              <text
                x={lx + 7}
                y={gridTop + gridHeight + 22}
                textAnchor="middle"
                fontSize={9}
                fontWeight="bold"
                fill={C.bg}
                fontFamily="serif"
              >
                {hua}
              </text>
              <text
                x={lx + 18}
                y={gridTop + gridHeight + 22}
                fontSize={10}
                fill={C.ink}
                fontFamily="serif"
              >
                化{hua}
              </text>
            </g>
          );
        })}
        <text
          x={size - 24}
          y={gridTop + gridHeight + 22}
          textAnchor="end"
          fontSize={10}
          fill={C.adjStar}
          fontFamily="serif"
          letterSpacing="0.15em"
        >
          {label} · {totalHeight}×{size}
        </text>
      </svg>

      {/* 交互式 hover/pin 信息卡 (移动端 tap 触发) */}
      {activePalace && (
        <PalaceInfoCard
          palace={activePalace}
          palaceIdx={activeIdx as number}
          scope={scope}
          xiaoxianHi={xiaoxianHi}
          mutagens={info}
          pinned={pinnedIdx === activeIdx}
          onClose={() => {
            setPinnedIdx(null);
            setHoverIdx(null);
          }}
        />
      )}
    </div>
  );
}

/** 宫位详情卡 (hover/click 弹出, 沿用 COLOR 常量). */
function PalaceInfoCard({
  palace,
  palaceIdx,
  scope,
  xiaoxianHi,
  mutagens,
  pinned,
  onClose,
}: {
  palace: Palace;
  palaceIdx: number;
  scope: ScopeKey;
  xiaoxianHi: number | null;
  mutagens: { ganzhi: string; mutagens?: string[] } | { palaceIdx: number; age: number | undefined; zhi: string | undefined; ganzhi: string };
  pinned: boolean;
  onClose: () => void;
}) {
  const major = (palace.major_stars || []).map(starName).filter(Boolean);
  const minor = (palace.minor_stars || []).map(starName).filter(Boolean);
  const adj = (palace.adjective_stars || []).map(starName).filter(Boolean);
  const stemBranch = (palace.heavenly_stem || "") + (palace.earthly_branch || "");
  const isXiao = xiaoxianHi === palaceIdx;
  const isBody = palace.is_body_palace || palace.is_body;

  return (
    <div
      role="tooltip"
      data-pinned={pinned ? "true" : "false"}
      onClick={pinned ? onClose : undefined}
      style={{
        position: "relative",
        margin: "12px auto 0",
        padding: "14px 18px",
        maxWidth: 560,
        background: "#FDFAF2",
        border: `1px solid ${isXiao ? C.cinnabar : C.rule}`,
        borderLeft: `4px solid ${isXiao ? C.cinnabar : isBody ? C.cinnabar : C.azure}`,
        borderRadius: 4,
        boxShadow: "0 4px 16px rgba(43, 38, 32, 0.08)",
        fontFamily: "serif",
        color: C.ink,
        fontSize: 13,
        lineHeight: 1.7,
        cursor: pinned ? "pointer" : "default",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{
          fontSize: 16,
          fontWeight: "bold",
          color: isBody ? C.cinnabar : C.ink,
        }}>
          {palace.name || `第${palaceIdx + 1}宫`}
          {isBody ? " ●" : palace.is_original_palace ? " ☆" : ""}
        </span>
        {stemBranch && (
          <span style={{
            fontSize: 12,
            color: C.adjStar,
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {stemBranch}
          </span>
        )}
        {isXiao && (
          <span style={{
            fontSize: 10,
            fontWeight: "bold",
            color: C.bg,
            background: C.cinnabar,
            padding: "2px 8px",
            borderRadius: 2,
            letterSpacing: "0.1em",
          }}>
            小限
          </span>
        )}
        {pinned && (
          <span style={{
            fontSize: 10,
            color: C.adjStar,
            marginLeft: "auto",
            fontStyle: "italic",
          }}>
            (已固定, 点击关闭)
          </span>
        )}
      </div>

      {major.length > 0 && (
        <div>
          <span style={{ color: C.adjStar }}>主星: </span>
          <span style={{ color: C.majorStar, fontWeight: "bold" }}>{major.join(" · ")}</span>
        </div>
      )}
      {minor.length > 0 && (
        <div>
          <span style={{ color: C.adjStar }}>辅星: </span>
          <span style={{ color: C.minorStar }}>{minor.join(" · ")}</span>
        </div>
      )}
      {adj.length > 0 && (
        <div>
          <span style={{ color: C.adjStar }}>杂曜: </span>
          <span style={{ color: C.adjStar }}>{adj.join(" · ")}</span>
        </div>
      )}

      {/* 四化信息 (本命/大限/流年) */}
      {"mutagens" in mutagens && mutagens.mutagens && mutagens.mutagens.length > 0 && (
        <div style={{ marginTop: 4, fontSize: 12 }}>
          <span style={{ color: C.adjStar }}>{SCOPE_LABEL[scope]}四化: </span>
          {mutagens.mutagens.join(" · ")}
        </div>
      )}

      {/* 小限专属: 显示所在宫位 + 流年干支 */}
      {scope === "xiaoxian" && "zhi" in mutagens && mutagens.zhi && (
        <div style={{ marginTop: 4, fontSize: 12 }}>
          <span style={{ color: C.adjStar }}>小限起例: </span>
          {mutagens.zhi}年生 · 虚岁
          {mutagens.age ?? "—"}
        </div>
      )}

      {palace.changsheng12 && (
        <div style={{ marginTop: 4, fontSize: 12 }}>
          <span style={{ color: C.adjStar }}>长生十二神: </span>
          {palace.changsheng12}
        </div>
      )}

      <div style={{
        marginTop: 8,
        fontSize: 11,
        color: C.adjStar,
        borderTop: `1px dashed ${C.ruleSoft}`,
        paddingTop: 6,
      }}>
        {pinned
          ? "Tap 该卡可关闭 · hover 切换其他宫位"
          : "Hover 切换 · Click 固定 (移动端 Tap 触发)"}
      </div>
    </div>
  );
}

export default ZiweiSvgChart;
