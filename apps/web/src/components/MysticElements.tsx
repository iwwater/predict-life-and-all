// 玄学元素库: 东西方神秘学符号（「古籍×仪器」纸墨风格）
// 保留数据导出和 Unicode 符号，简化装饰性组件
import { useMemo } from "react";

// ── 五行配色 ──────────────────────────────────────────────────────
export const WUXING_COLORS: Record<string, string> = {
  金: "#8E8A7A",
  木: "#5A7058",
  水: "#2F4858",
  火: "#B03A2E",
  土: "#9E8B5A",
};

export const WUXING_GLYPHS: Record<string, string> = {
  金: "⚙", 木: "☰", 水: "☵", 火: "☲", 土: "☷",
};

// ── 八卦符号 ──────────────────────────────────────────────────────
const BAGUA = {
  qian: "☰", dui: "☱", li: "☲", zhen: "☳",
  xun: "☴", kan: "☵", gen: "☶", kun: "☷",
} as const;

// ── 行星符号 ──────────────────────────────────────────────────────
const PLANET_SYMBOLS: Record<string, { glyph: string; name: string; nameZh: string; color: string }> = {
  sun:     { glyph: "☉", name: "Sun",     nameZh: "日", color: "#B03A2E" },
  moon:    { glyph: "☽", name: "Moon",    nameZh: "月", color: "#6B6256" },
  mercury: { glyph: "☿", name: "Mercury", nameZh: "水星", color: "#8E8A7A" },
  venus:   { glyph: "♀", name: "Venus",   nameZh: "金星", color: "#5A7058" },
  mars:    { glyph: "♂", name: "Mars",    nameZh: "火星", color: "#B03A2E" },
  jupiter: { glyph: "♃", name: "Jupiter", nameZh: "木星", color: "#2F4858" },
  saturn:  { glyph: "♄", name: "Saturn",  nameZh: "土星", color: "#9E8B5A" },
  uranus:  { glyph: "♅", name: "Uranus",  nameZh: "天王星", color: "#5A7058" },
  neptune: { glyph: "♆", name: "Neptune", nameZh: "海王星", color: "#2F4858" },
  pluto:   { glyph: "♇", name: "Pluto",   nameZh: "冥王星", color: "#5A7058" },
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

// ── 天干地支 ──────────────────────────────────────────────────────
const TIANGAN: Record<string, { gan: string; element: string }> = {
  jia: { gan: "甲", element: "木" }, yi: { gan: "乙", element: "木" },
  bing: { gan: "丙", element: "火" }, ding: { gan: "丁", element: "火" },
  wu: { gan: "戊", element: "土" }, ji: { gan: "己", element: "土" },
  geng: { gan: "庚", element: "金" }, xin: { gan: "辛", element: "金" },
  ren: { gan: "壬", element: "水" }, gui: { gan: "癸", element: "水" },
};

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
// 可复用组件（纸墨风格：取消旋转动画，使用 paper token 颜色）
// ══════════════════════════════════════════════════════════════

/** 八卦环 */
export function BaGuaRing({ size = 200, className = "" }: { size?: number; className?: string }) {
  const keys = ["qian", "dui", "li", "zhen", "xun", "kan", "gen", "kun"];
  const r = size * 0.38;
  const cx = size / 2, cy = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <circle cx={cx} cy={cy} r={r + 18} fill="none" stroke="var(--rule)" strokeWidth="0.5" strokeDasharray="3 5" />
      <circle cx={cx} cy={cy} r={r + 8} fill="none" stroke="var(--rule)" strokeWidth="0.3" opacity="0.6" />
      <circle cx={cx} cy={cy} r={r - 8} fill="none" stroke="var(--rule)" strokeWidth="0.3" opacity="0.6" />
      {keys.map((_, i) => {
        const angle = (i * Math.PI * 2) / 8 - Math.PI / 2;
        const x = cx + r * Math.cos(angle), y = cy + r * Math.sin(angle);
        const ix = cx + 10 * Math.cos(angle), iy = cy + 10 * Math.sin(angle);
        return <line key={`line-${i}`} x1={ix} y1={iy} x2={x} y2={y} stroke="var(--rule)" strokeWidth="0.4" opacity="0.4" />;
      })}
      {keys.map((key, i) => {
        const angle = (i * Math.PI * 2) / 8 - Math.PI / 2;
        return (
          <text key={key} x={cx + r * Math.cos(angle)} y={cy + r * Math.sin(angle)}
            textAnchor="middle" dominantBaseline="central"
            fontSize={size * 0.1} fill="var(--ink-soft)" opacity="0.6"
            style={{ fontFamily: "serif" }}>{BAGUA[key as keyof typeof BAGUA]}</text>
        );
      })}
      <circle cx={cx} cy={cy} r={12} fill="none" stroke="var(--rule)" strokeWidth="0.6" opacity="0.5" />
    </svg>
  );
}

/** 太极阴阳 */
export function YinYang({ size = 40, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2, cy = size / 2, r = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--rule)" strokeWidth="0.6" />
      <path d={`M${cx},${cy - r} A${r / 2},${r / 2} 0 0,1 ${cx},${cy} A${r / 2},${r / 2} 0 0,0 ${cx},${cy + r} A${r},${r} 0 0,1 ${cx},${cy - r}`}
        fill="var(--ink)" opacity="0.08" />
      <path d={`M${cx},${cy - r} A${r / 2},${r / 2} 0 0,0 ${cx},${cy} A${r / 2},${r / 2} 0 0,1 ${cx},${cy + r} A${r},${r} 0 0,0 ${cx},${cy - r}`}
        fill="var(--cinnabar)" opacity="0.1" />
      <circle cx={cx} cy={cy - r / 2} r={r * 0.12} fill="var(--cinnabar)" opacity="0.5" />
      <circle cx={cx} cy={cy + r / 2} r={r * 0.12} fill="var(--ink)" opacity="0.3" />
    </svg>
  );
}

/** 五行相生环 */
export function WuXingRing({ size = 140, className = "" }: { size?: number; className?: string }) {
  const elements = ["金", "水", "木", "火", "土"];
  const r = size * 0.35;
  const cx = size / 2, cy = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <polygon points={elements.map((_, i) => {
        const angle = (i * Math.PI * 2) / 5 - Math.PI / 2;
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
      }).join(" ")} fill="none" stroke="var(--rule)" strokeWidth="0.5" opacity="0.5" />
      <polygon points={elements.map((_, i) => {
        const idx = (i * 2) % 5;
        const angle = (idx * Math.PI * 2) / 5 - Math.PI / 2;
        return `${cx + r * 0.6 * Math.cos(angle)},${cy + r * 0.6 * Math.sin(angle)}`;
      }).join(" ")} fill="none" stroke="var(--rule)" strokeWidth="0.3" opacity="0.3" />
      {elements.map((el, i) => {
        const angle = (i * Math.PI * 2) / 5 - Math.PI / 2;
        const x = cx + r * Math.cos(angle), y = cy + r * Math.sin(angle);
        return (
          <g key={el}>
            <circle cx={x} cy={y} r={8} fill="none" stroke={WUXING_COLORS[el]} strokeWidth="0.7" opacity="0.4" />
            <text x={x} y={y} textAnchor="middle" dominantBaseline="central"
              fontSize={11} fill={WUXING_COLORS[el]} opacity="0.7" style={{ fontFamily: "serif" }}>{el}</text>
          </g>
        );
      })}
    </svg>
  );
}

/** 黄道十二宫环 */
export function ZodiacRing({ size = 220, className = "" }: { size?: number; className?: string }) {
  const signs = Object.entries(ZODIAC_SYMBOLS);
  const r = size * 0.4;
  const cx = size / 2, cy = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <circle cx={cx} cy={cy} r={r + 12} fill="none" stroke="var(--rule)" strokeWidth="0.5" strokeDasharray="2 4" opacity="0.4" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--indigo)" strokeWidth="0.5" opacity="0.3" />
      <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} stroke="var(--rule)" strokeWidth="0.3" opacity="0.25" />
      <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} stroke="var(--rule)" strokeWidth="0.3" opacity="0.25" />
      {signs.map(([key, s], i) => {
        const angle = (i * Math.PI * 2) / 12 - Math.PI / 2;
        const elemColor = WUXING_COLORS[s.element] || "var(--ink-soft)";
        return (
          <text key={key} x={cx + r * Math.cos(angle)} y={cy + r * Math.sin(angle)}
            textAnchor="middle" dominantBaseline="central"
            fontSize={size * 0.07} fill={elemColor} opacity="0.5" style={{ fontFamily: "serif" }}>{s.glyph}</text>
        );
      })}
      <circle cx={cx} cy={cy} r={6} fill="none" stroke="var(--indigo)" strokeWidth="0.5" opacity="0.3" />
      <circle cx={cx} cy={cy} r={2} fill="var(--indigo)" opacity="0.4" />
    </svg>
  );
}

/** 生命之花 (简化) */
export function FlowerOfLife({ size = 160, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2, cy = size / 2;
  const rings = 3, petalR = size * 0.13;
  const centers: [number, number][] = [];
  for (let ring = 0; ring <= rings; ring++) {
    if (ring === 0) { centers.push([cx, cy]); continue; }
    for (let i = 0; i < ring * 6; i++) {
      const angle = (i * Math.PI * 2) / (ring * 6) + (ring * Math.PI / 6);
      const dist = ring * petalR * 1.73;
      centers.push([cx + dist * Math.cos(angle), cy + dist * Math.sin(angle)]);
    }
  }
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      {centers.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={petalR} fill="none" stroke="var(--rule)" strokeWidth="0.3" opacity="0.25" />
      ))}
    </svg>
  );
}

/** 梅塔特隆立方体 (简化) */
export function MetatronCube({ size = 160, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2, cy = size / 2, r = size * 0.4;
  const nodes: [number, number][] = [[cx, cy]];
  for (let i = 0; i < 6; i++) {
    const angle = (i * Math.PI * 2) / 6;
    nodes.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
    nodes.push([cx + r * 0.5 * Math.cos(angle), cy + r * 0.5 * Math.sin(angle)]);
  }
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      <polygon points={Array.from({ length: 6 }, (_, i) => {
        const angle = (i * Math.PI * 2) / 6;
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
      }).join(" ")} fill="none" stroke="var(--rule)" strokeWidth="0.4" opacity="0.3" />
      {nodes.slice(0, 7).map(([x1, y1], i) =>
        nodes.slice(i + 1, 7).map(([x2, y2], j) => (
          <line key={`${i}-${j}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--rule)" strokeWidth="0.2" opacity="0.15" />
        ))
      )}
      {nodes.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i === 0 ? 2.5 : 1.5} fill="var(--indigo)" opacity="0.35" />
      ))}
    </svg>
  );
}

/** 行星符号行 (Unicode, 纸墨色调) */
export function PlanetSymbols({ size = 16, className = "" }: { size?: number; className?: string }) {
  const planets = Object.values(PLANET_SYMBOLS);
  return (
    <div className={`flex items-center gap-1 ${className}`} aria-hidden>
      {planets.map((p) => (
        <span key={p.name} title={p.nameZh} style={{ fontSize: size, color: p.color, opacity: 0.5, fontFamily: "serif" }}>
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
    <div className={`flex items-center gap-0.5 opacity-15 ${className}`} aria-hidden>
      {all.map((item, i) => {
        const color = WUXING_COLORS[item.element] || "var(--ink-soft)";
        return <span key={i} style={{ fontSize: "0.52rem", color, fontFamily: "serif" }}>{"gan" in item ? (item as typeof gans[0]).gan : (item as typeof zhis[0]).zhi}</span>;
      })}
    </div>
  );
}

/** 罗盘刻度装饰 */
export function CompassRing({ size = 180, className = "" }: { size?: number; className?: string }) {
  const cx = size / 2, cy = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className} aria-hidden>
      {[0.85, 0.78, 0.70, 0.62, 0.42, 0.35].map((scale, i) => (
        <circle key={i} cx={cx} cy={cy} r={cx * scale} fill="none" stroke="var(--rule)"
          strokeWidth={i < 2 ? 0.5 : 0.25} strokeDasharray={i % 2 === 0 ? "none" : "1 3"}
          opacity={0.12 + i * 0.04} />
      ))}
      {Array.from({ length: 24 }).map((_, i) => {
        const angle = (i * Math.PI * 2) / 24;
        const isCardinal = i % 6 === 0;
        return (
          <line key={i} x1={cx + cx * 0.68 * Math.cos(angle)} y1={cy + cy * 0.68 * Math.sin(angle)}
            x2={cx + cx * 0.82 * Math.cos(angle)} y2={cy + cy * 0.82 * Math.sin(angle)}
            stroke="var(--rule)" strokeWidth={isCardinal ? 0.7 : 0.25} opacity={isCardinal ? 0.3 : 0.15} />
        );
      })}
      <circle cx={cx} cy={cy} r={3} fill="var(--cinnabar)" opacity="0.4" />
    </svg>
  );
}

/** 祥云图案 */
export function AuspiciousClouds({ className = "" }: { className?: string }) {
  return (
    <svg width="120" height="40" viewBox="0 0 120 40" className={className} aria-hidden fill="none"
      stroke="var(--rule)" strokeWidth="0.5" opacity="0.15">
      <path d="M 10 30 Q 15 20 25 20 Q 30 10 40 15 Q 45 5 55 10 Q 60 15 65 10 Q 75 5 80 15 Q 90 10 95 20 Q 105 18 110 28" />
      <path d="M 5 35 Q 15 28 25 30 Q 35 22 50 26 Q 60 20 75 25 Q 85 18 95 26 Q 105 22 115 28" strokeWidth="0.35" opacity="0.4" />
    </svg>
  );
}

/** 星辰阵列 (纸墨风格，无动画) */
export function StarArray({ count = 7, size = 16, className = "" }: { count?: number; size?: number; className?: string }) {
  const stars = useMemo(() =>
    Array.from({ length: count }).map((_, i) => ({
      x: 15 + (i * 70) / (count - 1),
      y: 20 + Math.sin(i * 1.8) * 25,
      r: (i % 3 === 0) ? 1.2 : 0.7,
    })), [count]);
  return (
    <svg width="100%" height={size * 3} viewBox="0 0 100 60" className={className} aria-hidden>
      {stars.map((s, i) => (
        <circle key={i} cx={`${s.x}%`} cy={`${s.y}%`} r={s.r} fill="var(--ink-soft)" opacity="0.15" />
      ))}
    </svg>
  );
}
