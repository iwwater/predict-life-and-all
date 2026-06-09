// 玄学元素库: 东西方神秘学符号 SVG
// 包含: 八卦 / 阴阳 / 五行 / 星座 / 行星符号 / 神圣几何 / 天干地支装饰
import { useMemo } from "react";

// ── 八卦符号 ──────────────────────────────────────────────────────
const BAGUA = {
  qian:  "☰", dui: "☱", li: "☲", zhen: "☳",
  xun:  "☴", kan: "☵", gen: "☶", kun: "☷",
} as const;

const BAGUA_NAMES: Record<string, string> = {
  qian: "乾·天", dui: "兑·泽", li: "離·火", zhen: "震·雷",
  xun: "巽·風", kan: "坎·水", gen: "艮·山", kun: "坤·地",
};

export const BAGUA_KEYS = Object.keys(BAGUA);

// ── 五行配色 ──────────────────────────────────────────────────────
export const WUXING_COLORS: Record<string, string> = {
  金: "#F5E6B8",
  木: "#5AA469",
  水: "#5B8DEF",
  火: "#C8553D",
  土: "#C9A24B",
};

export const WUXING_GLYPHS: Record<string, string> = {
  金: "⚙", 木: "🌿", 水: "💧", 火: "🔥", 土: "⛰",
};

const WUXING_GENERATING = ["金→水→木→火→土→金"];
const WUXING_CONTROLLING = ["金→木→土→水→火→金"];

// ── 行星符号 ──────────────────────────────────────────────────────
const PLANET_SYMBOLS: Record<string, { glyph: string; name: string; nameZh: string; color: string }> = {
  sun:     { glyph: "☉", name: "Sun",     nameZh: "日", color: "#E5BC5E" },
  moon:    { glyph: "☽", name: "Moon",    nameZh: "月", color: "#C8C2B0" },
  mercury: { glyph: "☿", name: "Mercury", nameZh: "水星", color: "#8A8F98" },
  venus:   { glyph: "♀", name: "Venus",   nameZh: "金星", color: "#5AA469" },
  mars:    { glyph: "♂", name: "Mars",    nameZh: "火星", color: "#C8553D" },
  jupiter: { glyph: "♃", name: "Jupiter", nameZh: "木星", color: "#5B8DEF" },
  saturn:  { glyph: "♄", name: "Saturn",  nameZh: "土星", color: "#8A6E32" },
  uranus:  { glyph: "♅", name: "Uranus",  nameZh: "天王星", color: "#4FB3A0" },
  neptune: { glyph: "♆", name: "Neptune", nameZh: "海王星", color: "#3A6BC2" },
  pluto:   { glyph: "♇", name: "Pluto",   nameZh: "冥王星", color: "#36766A" },
};

// ── 星座符号 ──────────────────────────────────────────────────────
const ZODIAC_SYMBOLS: Record<string, { glyph: string; nameZh: string; element: string }> = {
  aries:       { glyph: "♈", nameZh: "白羊", element: "火" },
  taurus:      { glyph: "♉", nameZh: "金牛", element: "土" },
  gemini:      { glyph: "♊", nameZh: "双子", element: "風" },
  cancer:      { glyph: "♋", nameZh: "巨蟹", element: "水" },
  leo:         { glyph: "♌", nameZh: "狮子", element: "火" },
  virgo:       { glyph: "♍", nameZh: "处女", element: "土" },
  libra:       { glyph: "♎", nameZh: "天秤", element: "風" },
  scorpio:     { glyph: "♏", nameZh: "天蝎", element: "水" },
  sagittarius: { glyph: "♐", nameZh: "射手", element: "火" },
  capricorn:   { glyph: "♑", nameZh: "摩羯", element: "土" },
  aquarius:    { glyph: "♒", nameZh: "水瓶", element: "風" },
  pisces:      { glyph: "♓", nameZh: "双鱼", element: "水" },
};

// ── 天干符号 ──────────────────────────────────────────────────────
const TIANGAN: Record<string, { gan: string; element: string }> = {
  jia: { gan: "甲", element: "木" }, yi: { gan: "乙", element: "木" },
  bing: { gan: "丙", element: "火" }, ding: { gan: "丁", element: "火" },
  wu: { gan: "戊", element: "土" }, ji: { gan: "己", element: "土" },
  geng: { gan: "庚", element: "金" }, xin: { gan: "辛", element: "金" },
  ren: { gan: "壬", element: "水" }, gui: { gan: "癸", element: "水" },
};

// ── 地支符号 ──────────────────────────────────────────────────────
const DIZHI: Record<string, { zhi: string; animal: string; element: string }> = {
  zi:   { zhi: "子", animal: "鼠", element: "水" },
  chou: { zhi: "丑", animal: "牛", element: "土" },
  yin:  { zhi: "寅", animal: "虎", element: "木" },
  mao:  { zhi: "卯", animal: "兔", element: "木" },
  chen: { zhi: "辰", animal: "龍", element: "土" },
  si:   { zhi: "巳", animal: "蛇", element: "火" },
  wu:   { zhi: "午", animal: "馬", element: "火" },
  wei:  { zhi: "未", animal: "羊", element: "土" },
  shen: { zhi: "申", animal: "猴", element: "金" },
  you:  { zhi: "酉", animal: "雞", element: "金" },
  xu:   { zhi: "戌", animal: "狗", element: "土" },
  hai:  { zhi: "亥", animal: "豬", element: "水" },
};

// ══════════════════════════════════════════════════════════════
// 可复用组件
// ══════════════════════════════════════════════════════════════

/** 八卦环: 八边形排列的八卦符号, 可旋转 */
export function BaGuaRing({ size = 200, className = "", spinning = true }: {
  size?: number; className?: string; spinning?: boolean;
}) {
  const keys = ["qian", "dui", "li", "zhen", "xun", "kan", "gen", "kun"];
  const r = size * 0.38;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg
      width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`${spinning ? "spin-slow" : ""} ${className}`}
      aria-hidden
    >
      {/* 三圈层 */}
      <circle cx={cx} cy={cy} r={r + 18} fill="none" stroke="var(--gold-dim)" strokeWidth="0.5" strokeDasharray="3 5" />
      <circle cx={cx} cy={cy} r={r + 8} fill="none" stroke="var(--gold-dim)" strokeWidth="0.3" opacity="0.7" />
      <circle cx={cx} cy={cy} r={r - 8} fill="none" stroke="var(--gold-dim)" strokeWidth="0.3" opacity="0.7" />
      {/* 八条射线 */}
      {keys.map((_, i) => {
        const angle = (i * Math.PI * 2) / 8 - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        const ix = cx + 10 * Math.cos(angle);
        const iy = cy + 10 * Math.sin(angle);
        return (
          <line key={`line-${i}`} x1={ix} y1={iy} x2={x} y2={y}
            stroke="var(--gold-dim)" strokeWidth="0.4" opacity="0.5" />
        );
      })}
      {/* 八卦符号 */}
      {keys.map((key, i) => {
        const angle = (i * Math.PI * 2) / 8 - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return (
          <text key={key} x={x} y={y}
            textAnchor="middle" dominantBaseline="central"
            fontSize={size * 0.1} fill="var(--gold-bright)" opacity="0.85"
            style={{ fontFamily: "serif" }}>
            {BAGUA[key as keyof typeof BAGUA]}
          </text>
        );
      })}
      {/* 中心阴阳 */}
      <circle cx={cx} cy={cy} r={12} fill="none" stroke="var(--gold)" strokeWidth="0.8" opacity="0.7" />
    </svg>
  );
}

/** 太极阴阳 */
export function YinYang({ size = 40, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--gold)" strokeWidth="0.8" />
      {/* 简化的太极: 两半圆 + 两小点 */}
      <path
        d={`M${cx},${cy - r} A${r / 2},${r / 2} 0 0,1 ${cx},${cy} A${r / 2},${r / 2} 0 0,0 ${cx},${cy + r} A${r},${r} 0 0,1 ${cx},${cy - r}`}
        fill="var(--ink)" opacity="0.25"
      />
      <path
        d={`M${cx},${cy - r} A${r / 2},${r / 2} 0 0,0 ${cx},${cy} A${r / 2},${r / 2} 0 0,1 ${cx},${cy + r} A${r},${r} 0 0,0 ${cx},${cy - r}`}
        fill="var(--gold)" opacity="0.15"
      />
      <circle cx={cx} cy={cy - r / 2} r={r * 0.12} fill="var(--gold)" opacity="0.8" />
      <circle cx={cx} cy={cy + r / 2} r={r * 0.12} fill="var(--ink)" opacity="0.5" />
    </svg>
  );
}

/** 五行相生环 */
export function WuXingRing({ size = 140, className = "" }: { size?: number; className?: string }) {
  const elements = ["金", "水", "木", "火", "土"];
  const r = size * 0.35;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`spin-slow-rev ${className}`} aria-hidden>
      {/* 五边形连线 */}
      <polygon
        points={elements.map((_, i) => {
          const angle = (i * Math.PI * 2) / 5 - Math.PI / 2;
          return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
        }).join(" ")}
        fill="none" stroke="var(--gold-dim)" strokeWidth="0.6" opacity="0.6"
      />
      {/* 五芒星 (相克) */}
      <polygon
        points={elements.map((_, i) => {
          const idx = (i * 2) % 5;
          const angle = (idx * Math.PI * 2) / 5 - Math.PI / 2;
          return `${cx + r * 0.6 * Math.cos(angle)},${cy + r * 0.6 * Math.sin(angle)}`;
        }).join(" ")}
        fill="none" stroke="var(--gold-dim)" strokeWidth="0.4" opacity="0.35"
      />
      {/* 五行节点 */}
      {elements.map((el, i) => {
        const angle = (i * Math.PI * 2) / 5 - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return (
          <g key={el}>
            <circle cx={x} cy={y} r={8} fill="none" stroke={WUXING_COLORS[el]} strokeWidth="0.8" opacity="0.5" />
            <text x={x} y={y} textAnchor="middle" dominantBaseline="central"
              fontSize={11} fill={WUXING_COLORS[el]} opacity="0.85"
              style={{ fontFamily: "serif" }}>
              {el}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/** 黄道十二宫环 */
export function ZodiacRing({ size = 220, className = "", showLabels = false }: {
  size?: number; className?: string; showLabels?: boolean;
}) {
  const signs = Object.entries(ZODIAC_SYMBOLS);
  const r = size * 0.4;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`spin-slow ${className}`} aria-hidden>
      {/* 外圈 */}
      <circle cx={cx} cy={cy} r={r + 12} fill="none" stroke="var(--azure-dim)" strokeWidth="0.5" strokeDasharray="2 4" opacity="0.5" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--azure)" strokeWidth="0.6" opacity="0.4" />
      {/* 十字分割 */}
      <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} stroke="var(--azure-dim)" strokeWidth="0.3" opacity="0.3" />
      <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} stroke="var(--azure-dim)" strokeWidth="0.3" opacity="0.3" />
      {/* 12 星座符号 */}
      {signs.map(([key, s], i) => {
        const angle = (i * Math.PI * 2) / 12 - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        const elemColor = WUXING_COLORS[s.element] || "var(--muted)";
        return (
          <g key={key}>
            <text x={x} y={showLabels ? y - 2 : y}
              textAnchor="middle" dominantBaseline="central"
              fontSize={size * 0.07} fill={elemColor} opacity="0.7"
              style={{ fontFamily: "serif" }}>
              {s.glyph}
            </text>
            {showLabels && (
              <text x={x} y={y + 8} textAnchor="middle"
                fontSize={7} fill="var(--muted)" opacity="0.5">
                {s.nameZh}
              </text>
            )}
          </g>
        );
      })}
      {/* 中心 */}
      <circle cx={cx} cy={cy} r={6} fill="none" stroke="var(--azure)" strokeWidth="0.6" opacity="0.5" />
      <circle cx={cx} cy={cy} r={2} fill="var(--azure)" opacity="0.6" />
    </svg>
  );
}

/** 神圣几何: 生命之花 (简化版) */
export function FlowerOfLife({ size = 160, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2;
  const cy = size / 2;
  const rings = 3;
  const petalR = size * 0.13;

  // 生成六边形网格中心
  const centers: [number, number][] = [];
  for (let ring = 0; ring <= rings; ring++) {
    if (ring === 0) {
      centers.push([cx, cy]);
      continue;
    }
    for (let i = 0; i < ring * 6; i++) {
      const angle = (i * Math.PI * 2) / (ring * 6) + (ring * Math.PI / 6);
      const dist = ring * petalR * 1.73;
      centers.push([cx + dist * Math.cos(angle), cy + dist * Math.sin(angle)]);
    }
  }

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`spin-slow-rev ${className}`} aria-hidden>
      {centers.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={petalR}
          fill="none" stroke="var(--gold-dim)" strokeWidth="0.35" opacity="0.3" />
      ))}
    </svg>
  );
}

/** 梅塔特隆立方体 (简化) */
export function MetatronCube({ size = 160, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.4;

  // 13 个节点
  const nodes: [number, number][] = [[cx, cy]];
  for (let i = 0; i < 6; i++) {
    const angle = (i * Math.PI * 2) / 6;
    nodes.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
    nodes.push([cx + r * 0.5 * Math.cos(angle), cy + r * 0.5 * Math.sin(angle)]);
  }

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`spin-slow ${className}`} aria-hidden>
      {/* 外六边形 */}
      <polygon
        points={Array.from({ length: 6 }, (_, i) => {
          const angle = (i * Math.PI * 2) / 6;
          return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
        }).join(" ")}
        fill="none" stroke="var(--azure-dim)" strokeWidth="0.4" opacity="0.35"
      />
      {/* 连线 */}
      {nodes.slice(0, 7).map(([x1, y1], i) =>
        nodes.slice(i + 1, 7).map(([x2, y2], j) => (
          <line key={`${i}-${j}`} x1={x1} y1={y1} x2={x2} y2={y2}
            stroke="var(--azure-dim)" strokeWidth="0.2" opacity="0.2" />
        ))
      )}
      {/* 节点 */}
      {nodes.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i === 0 ? 2.5 : 1.5}
          fill="var(--azure)" opacity="0.5" />
      ))}
    </svg>
  );
}

/** 行星符号行 */
export function PlanetSymbols({ size = 16, className = "" }: { size?: number; className?: string }) {
  const planets = Object.values(PLANET_SYMBOLS);
  return (
    <div className={`flex items-center gap-1 ${className}`} aria-hidden>
      {planets.map((p) => (
        <span key={p.name} title={p.nameZh}
          className="inline-block transition-opacity hover:opacity-100"
          style={{ fontSize: size, color: p.color, opacity: 0.55, fontFamily: "serif" }}>
          {p.glyph}
        </span>
      ))}
    </div>
  );
}

/** 天干地支装饰线 */
export function GanZhiStripe({ className = "" }: { className?: string }) {
  const gans = Object.values(TIANGAN);
  const zhis = Object.values(DIZHI);
  const all = [...gans, ...zhis];

  return (
    <div className={`flex items-center gap-0.5 opacity-20 ${className}`} aria-hidden>
      {all.map((item, i) => {
        const color = WUXING_COLORS[item.element] || "var(--muted)";
        return (
          <span key={i} className="text-[8px] font-serif" style={{ color }}>
            {"gan" in item ? (item as typeof gans[0]).gan : (item as typeof zhis[0]).zhi}
          </span>
        );
      })}
    </div>
  );
}

/** 罗盘刻度装饰 (同心圆 + 刻度线) */
export function CompassRing({ size = 180, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}
      className={`spin-slow ${className}`} aria-hidden>
      {/* 多层同心环 */}
      {[0.85, 0.78, 0.70, 0.62, 0.42, 0.35].map((scale, i) => (
        <circle key={i} cx={cx} cy={cy} r={cx * scale}
          fill="none" stroke="var(--gold-dim)"
          strokeWidth={i < 2 ? 0.6 : 0.3}
          strokeDasharray={i % 2 === 0 ? "none" : "1 3"}
          opacity={0.15 + i * 0.05} />
      ))}
      {/* 24 山刻度 */}
      {Array.from({ length: 24 }).map((_, i) => {
        const angle = (i * Math.PI * 2) / 24;
        const inner = cx * 0.68;
        const outer = cx * 0.82;
        const isCardinal = i % 6 === 0;
        return (
          <line key={i}
            x1={cx + inner * Math.cos(angle)}
            y1={cy + inner * Math.sin(angle)}
            x2={cx + outer * Math.cos(angle)}
            y2={cy + outer * Math.sin(angle)}
            stroke="var(--gold-dim)"
            strokeWidth={isCardinal ? 0.8 : 0.3}
            opacity={isCardinal ? 0.4 : 0.2}
          />
        );
      })}
      {/* 中心十字 */}
      {[0, Math.PI / 2].map((a) => (
        <line key={a}
          x1={cx - cx * 0.3 * Math.cos(a)}
          y1={cy - cy * 0.3 * Math.sin(a)}
          x2={cx + cx * 0.3 * Math.cos(a)}
          y2={cy + cy * 0.3 * Math.sin(a)}
          stroke="var(--gold)" strokeWidth="0.5" opacity="0.4"
        />
      ))}
      <circle cx={cx} cy={cy} r={3} fill="var(--gold-bright)" opacity="0.6" />
    </svg>
  );
}

/** 祥云图案 (简化中式云纹) */
export function AuspiciousClouds({ className = "" }: { className?: string }) {
  return (
    <svg width="120" height="40" viewBox="0 0 120 40"
      className={`${className}`} aria-hidden fill="none"
      stroke="var(--gold-dim)" strokeWidth="0.6" opacity="0.25">
      <path d="M 10 30 Q 15 20 25 20 Q 30 10 40 15 Q 45 5 55 10 Q 60 15 65 10 Q 75 5 80 15 Q 90 10 95 20 Q 105 18 110 28" />
      <path d="M 5 35 Q 15 28 25 30 Q 35 22 50 26 Q 60 20 75 25 Q 85 18 95 26 Q 105 22 115 28" strokeWidth="0.4" opacity="0.5" />
    </svg>
  );
}

/** 炼金术符号 */
export function AlchemySymbols({ size = 14, className = "" }: { size?: number; className?: string }) {
  const symbols = [
    { glyph: "🜁", name: "Air" },
    { glyph: "🜂", name: "Fire" },
    { glyph: "🜄", name: "Water" },
    { glyph: "🜃", name: "Earth" },
    { glyph: "🜔", name: "Salt" },
    { glyph: "🜍", name: "Sulphur" },
    { glyph: "☿", name: "Mercury" },
  ];
  return (
    <div className={`flex items-center gap-0.5 ${className}`} aria-hidden>
      {symbols.map((s) => (
        <span key={s.name} title={s.name}
          className="opacity-40 hover:opacity-80 transition-opacity"
          style={{ fontSize: size }}>
          {s.glyph}
        </span>
      ))}
    </div>
  );
}

/** 装饰性星辰阵列 */
export function StarArray({ count = 7, size = 16, className = "" }: {
  count?: number; size?: number; className?: string;
}) {
  const stars = useMemo(() =>
    Array.from({ length: count }).map((_, i) => ({
      x: 15 + (i * 70) / (count - 1),
      y: 20 + Math.sin(i * 1.8) * 25,
      r: (i % 3 === 0) ? 1.2 : 0.7,
      delay: i * 0.3,
    }))
  , [count]);

  return (
    <svg width="100%" height={size * 3} viewBox="0 0 100 60"
      className={className} aria-hidden>
      {stars.map((s, i) => (
        <circle key={i} cx={`${s.x}%`} cy={`${s.y}%`} r={s.r}
          fill="var(--gold-bright)" opacity="0.35"
          className="crystal-sparkle"
          style={{ animationDelay: `${s.delay}s` }} />
      ))}
    </svg>
  );
}

/** 综合神秘学背景装饰 (随机选择符不符合) */
export function MysticBackground({ className = "" }: { className?: string }) {
  return (
    <div className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`} aria-hidden>
      {/* 八卦环 - 右上 */}
      <div className="absolute -right-12 -top-12 opacity-[0.06]">
        <BaGuaRing size={220} spinning={true} />
      </div>
      {/* 星座环 - 左下 */}
      <div className="absolute -left-16 -bottom-16 opacity-[0.05]">
        <ZodiacRing size={260} />
      </div>
      {/* 神圣几何 - 中右 */}
      <div className="absolute right-[10%] top-[30%] opacity-[0.04]">
        <FlowerOfLife size={140} />
      </div>
      {/* 罗盘 - 左中 */}
      <div className="absolute left-[5%] top-[20%] opacity-[0.04]">
        <CompassRing size={150} />
      </div>
    </div>
  );
}
