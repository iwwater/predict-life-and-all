// 24 山精确选向 dial — 每山 15°, 可点击切换
// 选中后高亮 + 显示 八卦/五行/阴阳, 距山界 < 5° 自动标双候选
import { useState } from "react";
import { COLOR } from "./ui";
import {
  SANS_24,
  SANS_CENTER_DEG,
  SANS_TRIGRAM,
  SANS_ELEMENT,
  SANS_YINYANG,
  checkBoundary,
  type BoundaryCheck,
} from "../lib/compass";

interface Props {
  // 当前选中的 24 山字符 (例如 "卯")
  value: string;
  // 选中后回调 (传入 mountain code)
  onChange: (sans: string) => void;
  // 可视直径
  size?: number;
}

// 八卦符号 (与 CompassDial 保持一致)
const TRIGRAM: Record<string, string> = {
  坎: "☵", 艮: "☶", 震: "☳", 巽: "☴",
  离: "☲", 坤: "☷", 兑: "☱", 乾: "☰",
};

export function TwentyFourMountainDial({ value, onChange, size = 320 }: Props) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const cx = size / 2;
  const cy = size / 2;
  const rOuter = size / 2 - 8;
  const rInner = rOuter * 0.42;
  const labelR = rOuter * 0.78;
  const smallLabelR = rOuter * 0.62;

  const activeIdx = hoverIdx !== null
    ? hoverIdx
    : Math.max(0, SANS_24.indexOf(value as any));
  const activeSans = SANS_24[activeIdx] || value;
  const activeTrigram = SANS_TRIGRAM[activeSans] || "";
  const activeElement = SANS_ELEMENT[activeSans] || "";
  const activeYy = SANS_YINYANG[activeSans] || "";
  const activeCenter = SANS_CENTER_DEG[activeIdx] || 0;

  // 临界角检测 (基于 active 山中心 ± 7.5° 边界)
  const boundaryDistance = Math.abs(
    (activeCenter + 7.5) - (((activeCenter + 7.5) % 360 + 360) % 360),
  ); // 简化: 仅显示 active 山位置, 实时 boundary 由父组件传入/计算
  // 实际 boundary 用父组件传入的 heading 检测
  // 此处保留 hover 反馈, 边界提示由调用方控制

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="overflow-visible"
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* 外圈装饰 */}
          <circle cx={cx} cy={cy} r={rOuter + 4} fill="none" stroke="var(--cinnabar-dim)" strokeWidth="0.5" strokeDasharray="2 4" />
          <circle cx={cx} cy={cy} r={rOuter} fill="none" stroke="var(--rule)" strokeWidth="1" />
          <circle cx={cx} cy={cy} r={rOuter * 0.85} fill="none" stroke="var(--rule-soft)" strokeWidth="0.5" />
          <circle cx={cx} cy={cy} r={rInner * 1.15} fill="none" stroke="var(--rule-soft)" strokeWidth="0.5" />
          <circle cx={cx} cy={cy} r={rInner} fill="var(--paper)" stroke="var(--rule)" strokeWidth="0.5" />

          {/* 8 方位参考线 (浅色, 仅辅助识别) */}
          {Array.from({ length: 8 }).map((_, i) => {
            const a = (i * 45 - 90) * Math.PI / 180;
            return (
              <line
                key={`dir-${i}`}
                x1={cx + Math.cos(a) * rInner * 1.15}
                y1={cy + Math.sin(a) * rInner * 1.15}
                x2={cx + Math.cos(a) * rOuter * 0.85}
                y2={cy + Math.sin(a) * rOuter * 0.85}
                stroke="var(--rule-soft)"
                strokeWidth="0.4"
                strokeDasharray="2 3"
              />
            );
          })}

          {/* 24 山扇区 + 标签 */}
          {SANS_24.map((sans, i) => {
            const startAngle = i * 15 - 90 - 7.5;
            const endAngle = startAngle + 15;
            const isActive = activeIdx === i;
            const isSelected = value === sans;
            // 中央角度位置 (标签)
            const labelAngle = ((i * 15 - 90) * Math.PI) / 180;
            const lx = cx + Math.cos(labelAngle) * labelR;
            const ly = cy + Math.sin(labelAngle) * labelR;
            // 次级标签 (卦位)
            const sx = cx + Math.cos(labelAngle) * smallLabelR;
            const sy = cy + Math.sin(labelAngle) * smallLabelR;
            const path = arcPath(cx, cy, rInner * 1.15, rOuter * 0.85, startAngle, endAngle);
            // 8 主方位 (i % 3 === 0) 显示大字, 其余显示小字
            const isTrigram = i % 3 === 0;
            return (
              <g
                key={sans}
                onMouseEnter={() => setHoverIdx(i)}
                onClick={() => onChange(sans)}
                className="cursor-pointer"
              >
                <path
                  d={path}
                  fill={isSelected ? "rgba(201,162,75,0.22)" : isActive ? "rgba(201,162,75,0.10)" : "rgba(255,255,255,0.015)"}
                  stroke={isSelected ? COLOR.gold : isActive ? "var(--rule)" : "var(--rule-soft)"}
                  strokeWidth={isSelected ? 1.2 : 0.4}
                />
                {/* 山名 (大字, 主方位) */}
                <text
                  x={lx} y={ly}
                  textAnchor="middle" dominantBaseline="middle"
                  fontSize={isSelected ? 15 : isActive ? 13 : 11}
                  fontWeight={isTrigram ? 600 : 400}
                  fill={isSelected ? COLOR.goldBright : isActive ? COLOR.ink : COLOR.inkSoft}
                  style={{ pointerEvents: "none", userSelect: "none" }}
                >
                  {sans}
                </text>
                {/* 副标 (八卦/五行, 仅 hover 或选中时显示) */}
                {(isActive || isSelected) && (
                  <text
                    x={sx} y={sy}
                    textAnchor="middle" dominantBaseline="middle"
                    fontSize={8}
                    fill="var(--ink-soft)"
                    style={{ pointerEvents: "none", userSelect: "none" }}
                  >
                    {SANS_TRIGRAM[sans] || ""}
                  </text>
                )}
              </g>
            );
          })}

          {/* 罗针指向 active 山 */}
          {(() => {
            const a = (activeCenter - 90) * Math.PI / 180;
            const tx = cx + Math.cos(a) * (rInner * 0.6);
            const ty = cy + Math.sin(a) * (rInner * 0.6);
            return (
              <>
                <line x1={cx} y1={cy} x2={tx} y2={ty} stroke={COLOR.gold} strokeWidth="1.5" strokeLinecap="round" />
                <circle cx={tx} cy={ty} r="3" fill={COLOR.gold} />
              </>
            );
          })()}

          {/* 中央显示: 八卦 + 山名 + 五行/阴阳 */}
          <text
            x={cx} y={cy - 14}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={28} fill={COLOR.goldBright}
            style={{ userSelect: "none" }}
          >
            {TRIGRAM[activeTrigram] || "○"}
          </text>
          <text
            x={cx} y={cy + 6}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={16} fontWeight={600}
            fill={COLOR.goldBright}
            style={{ userSelect: "none" }}
          >
            {activeSans}
          </text>
          <text
            x={cx} y={cy + 22}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={9} fill={COLOR.ink}
            style={{ userSelect: "none" }}
          >
            {activeTrigram}卦 · {activeElement} · {activeYy}
          </text>
          <text
            x={cx} y={cy + 34}
            textAnchor="middle" dominantBaseline="middle"
            fontSize={8} fill={COLOR.muted}
            style={{ userSelect: "none" }}
          >
            {activeCenter}°
          </text>
        </svg>
      </div>

      <div className="text-xs text-center" style={{ color: COLOR.inkSoft }}>
        24 山精确模式 · 每山 15° · 中心 = <span style={{ color: COLOR.goldBright }}>{activeCenter}°</span>
      </div>
    </div>
  );
}

// 弧形路径 (复用 CompassDial 公式)
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

// 导出 BoundaryCheck 类型供父组件使用
export type { BoundaryCheck };
