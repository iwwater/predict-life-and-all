// 五行 / 元素强弱雷达图(各法 normalized.elements 通用)
// 增强: 5 个轴点可 hover, 命中轴放大约 1.15x + 显示数值 tooltip
import { useState } from "react";
import { COLOR } from "./ui";

interface Props {
  elements: Record<string, number>;
  // "five" 东方五行 / "four" 西方四元素
  variant?: "five" | "four";
  size?: number;
  title?: string;
}

const ELEMENT_LABELS: Record<string, { zh: string; en: string; color: string }> = {
  metal: { zh: "金", en: "Metal", color: COLOR.gold },
  wood:  { zh: "木", en: "Wood",  color: COLOR.jade },
  water: { zh: "水", en: "Water", color: COLOR.azure },
  fire:  { zh: "火", en: "Fire",  color: COLOR.danger },
  earth: { zh: "土", en: "Earth", color: COLOR.goldDim },
};

export function ElementsRadar({ elements, variant = "five", size = 220, title }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const order = variant === "five"
    ? ["wood", "fire", "earth", "metal", "water"]
    : ["fire", "earth", "air", "water"];
  const labels = variant === "five"
    ? order
    : ["fire", "earth", "air", "water"];
  // 支持英文 key（API 默认）+ 中文 key（向后兼容）
  const KEY_ALIAS: Record<string, string[]> = {
    metal: ["metal", "金"], wood: ["wood", "木"], water: ["water", "水"],
    fire: ["fire", "火"], earth: ["earth", "土"], air: ["air", "风"],
  };
  const get = (k: string) => {
    for (const alias of KEY_ALIAS[k] || [k]) {
      const v = (elements as any)[alias];
      if (typeof v === "number") return v;
    }
    return 0;
  };
  const values = labels.map(get);
  const max = Math.max(1, ...values);
  const total = values.reduce((a, b) => a + b, 0);
  const cx = size / 2, cy = size / 2;
  const r = size / 2 - 24;
  const n = labels.length;
  // hover 时让命中轴的半径放大
  const points = values.map((v, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const boost = hover === i ? 1.18 : 1;
    const rr = (v / max) * r * boost;
    return [cx + Math.cos(angle) * rr, cy + Math.sin(angle) * rr] as const;
  });
  const polyStr = points.map((p) => p.join(",")).join(" ");

  return (
    <div className="flex flex-col items-center">
      {title && <div className="text-xs uppercase tracking-widest mb-2" style={{ color: COLOR.muted }}>{title}</div>}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* 同心环 */}
        {[0.25, 0.5, 0.75, 1].map((p, i) => (
          <circle key={i} cx={cx} cy={cy} r={r * p} fill="none" stroke={COLOR.line} strokeWidth={1} />
        ))}
        {/* 轴线 */}
        {labels.map((_, i) => {
          const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
          return (
            <line key={i}
              x1={cx} y1={cy}
              x2={cx + Math.cos(angle) * r} y2={cy + Math.sin(angle) * r}
              stroke={hover === i ? COLOR.gold : COLOR.line}
              strokeWidth={hover === i ? 1.2 : 1}
              style={{ transition: "stroke 0.2s ease, stroke-width 0.2s ease" }}
            />
          );
        })}
        {/* 多边形 */}
        <polygon
          points={polyStr}
          fill={hover !== null ? COLOR.gold : COLOR.gold}
          fillOpacity={hover !== null ? 0.28 : 0.18}
          stroke={COLOR.gold} strokeWidth={1.5}
          style={{ transition: "fill-opacity 0.2s ease" }}
        />
        {/* 5 个轴点 (hover 区域 + 节点) */}
        {labels.map((k, i) => {
          const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
          const px = cx + Math.cos(angle) * r;
          const py = cy + Math.sin(angle) * r;
          const lx = cx + Math.cos(angle) * (r + 14);
          const ly = cy + Math.sin(angle) * (r + 14);
          const meta = ELEMENT_LABELS[k] || { zh: k, color: COLOR.gold };
          const v = values[i];
          const pct = total > 0 ? Math.round((v / total) * 100) : 0;
          return (
            <g
              key={k}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: "pointer" }}
            >
              {/* 透明 hover 区(扩大到整轴,容易命中) */}
              <circle
                cx={cx} cy={cy} r={r + 12}
                fill="transparent"
                pointerEvents="all"
                style={{ pointerEvents: "all" }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
              />
              {/* 实际可命中区域: 轴端三角 */}
              <path
                d={`M ${px - 12} ${py - 12} L ${px + 12} ${py + 12} L ${px - 12} ${py + 12} Z`}
                fill="transparent"
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
              />
              {/* 节点 */}
              <circle
                cx={points[i][0]} cy={points[i][1]}
                r={hover === i ? 5 : 3}
                fill={meta.color}
                style={{ transition: "r 0.18s ease" }}
              />
              <text x={lx} y={ly}
                textAnchor="middle" dominantBaseline="middle"
                fill={hover === i ? COLOR.goldBright : COLOR.ink} fontSize={hover === i ? 12 : 11}
                style={{ transition: "fill 0.2s ease, font-size 0.2s ease" }}>
                {meta.zh}
              </text>
              <text x={lx} y={ly + 13}
                textAnchor="middle" dominantBaseline="middle"
                fill={hover === i ? COLOR.goldBright : COLOR.muted} fontSize={hover === i ? 10 : 9}>
                {v}
              </text>
              {/* hover 浮动 tooltip */}
              {hover === i && (
                <g style={{ pointerEvents: "none" }}>
                  <rect
                    x={lx - 32} y={ly - 30} width={64} height={22} rx={4}
                    fill="var(--paper-2)" stroke="var(--cinnabar)" strokeWidth={0.6}
                  />
                  <text
                    x={lx} y={ly - 16}
                    textAnchor="middle" dominantBaseline="middle"
                    fill={COLOR.goldBright} fontSize={10}
                  >
                    {meta.zh} · {v} ({pct}%)
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
