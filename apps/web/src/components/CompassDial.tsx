// 罗盘选向: 8 方位圆形 dial, hover 浮起, 选中金色高亮 + 八卦符号
// Sprint 3 P2: show24 模式支持 24 山独立交互 (hover/click each mountain)
import { useState } from "react";
import { COLOR } from "./ui";
import {
  DIRECTIONS_8,
  SANS_24,
  SANS_TRIGRAM,
  type DirectionChoice,
} from "../lib/compass";

// 24 山 → 对应的 8 方位 parent code
const TRIGRAM_TO_DIR8: Record<string, string> = {
  坎: "正北", 艮: "东北", 震: "正东", 巽: "东南",
  离: "正南", 坤: "西南", 兑: "正西", 乾: "西北",
};

interface Props {
  value: string;
  onChange: (code: string) => void;
  size?: number;
  // 玄空/八宅: 还能转 24 山
  show24?: boolean;
  /** Sprint 3 P2: 24 山选中回调 — 传入 sans 字符 (e.g. "壬") */
  onSelectMountain?: (sans: string) => void;
  /** Sprint 3 P2: 当前选中的 24 山 (持久高亮) */
  selectedMountain?: string;
}

// 八卦符号 (简易)
const TRIGRAM: Record<string, string> = {
  坎: "☵", 艮: "☶", 震: "☳", 巽: "☴",
  离: "☲", 坤: "☷", 兑: "☱", 乾: "☰",
};

export function CompassDial({
  value,
  onChange,
  size = 280,
  show24 = false,
  onSelectMountain,
  selectedMountain,
}: Props) {
  const [hoverCode, setHoverCode] = useState<string | null>(null);
  // 24 山 hover 独立状态
  const [hoverSans, setHoverSans] = useState<string | null>(null);
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 8;
  const innerR = r * 0.55;
  const labelR = r * 0.78;
  const midR = r * 0.70; // 24 山弧内半径
  const sansLabelR = r * 0.91; // 24 山标签半径

  const active = hoverCode || value;
  const activeDir = DIRECTIONS_8.find((d) => d.code === active) || DIRECTIONS_8[2];

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="overflow-visible"
          onMouseLeave={() => { setHoverCode(null); setHoverSans(null); }}
        >
          {/* 外圈虚线 */}
          <circle cx={cx} cy={cy} r={r + 4} fill="none" stroke="var(--cinnabar-dim)" strokeWidth="0.5" strokeDasharray="2 4" className="" />
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--rule)" strokeWidth="1" />
          <circle cx={cx} cy={cy} r={r * 0.85} fill="none" stroke="var(--rule-soft)" strokeWidth="0.5" />
          <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="var(--rule-soft)" strokeWidth="0.5" />
          <circle cx={cx} cy={cy} r={innerR * 0.55} fill="var(--paper)" stroke="var(--rule)" strokeWidth="0.5" />

          {/* 8 方位扇形 + 标签 (底层) */}
          {DIRECTIONS_8.map((d, i) => {
            // 顺时针: 0=正北(上) → 7=西北
            const startAngle = i * 45 - 90 - 22.5;
            const endAngle = startAngle + 45;
            const isActive = active === d.code;
            const isSelected = value === d.code;
            const path = arcPath(cx, cy, innerR, r, startAngle, endAngle);
            const labelAngle = ((startAngle + endAngle) / 2 * Math.PI) / 180;
            const lx = cx + Math.cos(labelAngle) * labelR;
            const ly = cy + Math.sin(labelAngle) * labelR;
            return (
              <g
                key={d.code}
                onMouseEnter={() => setHoverCode(d.code)}
                onClick={() => onChange(d.code)}
                className="cursor-pointer"
              >
                <path
                  d={path}
                  fill={isSelected ? "rgba(201,162,75,0.18)" : isActive ? "rgba(201,162,75,0.10)" : "rgba(255,255,255,0.02)"}
                  stroke={isSelected ? COLOR.gold : isActive ? "var(--rule)" : "var(--rule-soft)"}
                  strokeWidth={isSelected ? 1.2 : 0.6}
                />
                <text
                  x={lx} y={ly}
                  textAnchor="middle" dominantBaseline="middle"
                  fontSize={isSelected ? 14 : 12}
                  fill={isSelected ? COLOR.goldBright : isActive ? COLOR.ink : COLOR.inkSoft}
                  style={{ pointerEvents: "none", userSelect: "none", fontWeight: isSelected ? 600 : 400 }}
                >
                  {d.code}
                </text>
                {show24 && (
                  <text
                    x={lx} y={ly + 13}
                    textAnchor="middle" dominantBaseline="middle"
                    fontSize={9}
                    fill={isActive ? COLOR.goldDim : "var(--ink-soft)"}
                    style={{ pointerEvents: "none", userSelect: "none" }}
                  >
                    {d.sans}
                  </text>
                )}
              </g>
            );
          })}

          {/* 24 山交互弧 (Sprint 3 P2 — 上层, 捕获外圈点击) */}
          {show24 && SANS_24.map((sans, i) => {
            const compassCenter = (i * 15 + 352.5) % 360; // 各山罗盘中心角
            const screenCenter = compassCenter - 90;        // → SVG 坐标系
            const startA = screenCenter - 7.5;
            const endA = screenCenter + 7.5;
            const trigram = SANS_TRIGRAM[sans] || "";
            const parentDir8 = TRIGRAM_TO_DIR8[trigram] || "";
            const isSelected24 = selectedMountain === sans;
            const isHovered24 = hoverSans === sans;
            const path = arcPath(cx, cy, midR, r, startA, endA);
            const labelRad = (screenCenter * Math.PI) / 180;
            const lx = cx + Math.cos(labelRad) * sansLabelR;
            const ly = cy + Math.sin(labelRad) * sansLabelR;

            // 子午卯酉四正山加粗
            const isCardinal = sans === "子" || sans === "午" || sans === "卯" || sans === "酉";
            const strokeW = isSelected24 ? 1.4 : isCardinal ? 0.8 : 0.4;

            return (
              <g key={`m24-${sans}`}>
                <path
                  d={path}
                  fill={isSelected24 ? "rgba(201,162,75,0.22)" : isHovered24 ? "rgba(201,162,75,0.10)" : "rgba(255,255,255,0.015)"}
                  stroke={isSelected24 ? COLOR.gold : isHovered24 ? COLOR.goldDim : "var(--rule)"}
                  strokeWidth={strokeW}
                  className="cursor-pointer"
                  onMouseEnter={() => setHoverSans(sans)}
                  onClick={() => {
                    onChange(parentDir8);
                    onSelectMountain?.(sans);
                  }}
                />
                <text
                  x={lx} y={ly}
                  textAnchor="middle" dominantBaseline="middle"
                  fontSize={isSelected24 ? 11 : 9}
                  fontWeight={isCardinal || isSelected24 ? 600 : 400}
                  fill={isSelected24 ? COLOR.goldBright : isHovered24 ? COLOR.gold : isCardinal ? COLOR.ink : COLOR.inkSoft}
                  style={{ pointerEvents: "none", userSelect: "none" }}
                >
                  {sans}
                </text>
              </g>
            );
          })}

          {/* 中央指示: 八卦符号 + 选中方位 */}
          <text
            x={cx} y={cy - 6}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={32} fill={COLOR.goldBright}
            style={{ userSelect: "none" }}
          >
            {TRIGRAM[activeDir.trigram] || "○"}
          </text>
          <text
            x={cx} y={cy + 18}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={11} fill={COLOR.ink}
            style={{ userSelect: "none" }}
          >
            {activeDir.code} · {activeDir.trigram}
          </text>
          <text
            x={cx} y={cy + 32}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={9} fill={COLOR.muted}
            style={{ userSelect: "none" }}
          >
            五行: {activeDir.element}
          </text>

          {/* 罗针 (指向当前方位) */}
          {(() => {
            const idx = DIRECTIONS_8.findIndex((d) => d.code === value);
            if (idx < 0) return null;
            const angle = idx * 45 - 90; // 上 = 正北
            const rad = (angle * Math.PI) / 180;
            const tx = cx + Math.cos(rad) * (innerR * 0.35);
            const ty = cy + Math.sin(rad) * (innerR * 0.35);
            return (
              <>
                <line x1={cx} y1={cy} x2={tx} y2={ty} stroke={COLOR.gold} strokeWidth="1.5" strokeLinecap="round" />
                <circle cx={tx} cy={ty} r="3" fill={COLOR.gold} />
              </>
            );
          })()}
        </svg>
      </div>

      {/* 选中方位的白话提示 */}
      <div className="text-xs text-center max-w-xs " key={activeDir.code} style={{ color: COLOR.inkSoft }}>
        <span className="font-display" style={{ color: COLOR.goldBright }}>{activeDir.trigram}卦 · {activeDir.code}</span>
        <span className="ml-2" style={{ color: COLOR.muted }}>{activeDir.hint}</span>
      </div>
    </div>
  );
}

function arcPath(cx: number, cy: number, rInner: number, rOuter: number, startAngle: number, endAngle: number) {
  const startRad = (startAngle * Math.PI) / 180;
  const endRad = (endAngle * Math.PI) / 180;
  const x1 = cx + Math.cos(startRad) * rOuter;
  const y1 = cy + Math.sin(startRad) * rOuter;
  const x2 = cx + Math.cos(endRad) * rOuter;
  const y2 = cy + Math.sin(endRad) * rOuter;
  const x3 = cx + Math.cos(endRad) * rInner;
  const y3 = cy + Math.sin(endRad) * rInner;
  const x4 = cx + Math.cos(startRad) * rInner;
  const y4 = cy + Math.sin(startRad) * rInner;
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
  return [
    `M ${x1} ${y1}`,
    `A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x2} ${y2}`,
    `L ${x3} ${y3}`,
    `A ${rInner} ${rInner} 0 ${largeArc} 0 ${x4} ${y4}`,
    "Z",
  ].join(" ");
}
