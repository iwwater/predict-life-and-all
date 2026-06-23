// 合盘报告: showing compatibility scoring with visual breakdown
import type { CompatibilityResult, MultiMethodCompatibilityResult } from "../lib/api";
import { COLOR } from "./ui";

interface Props {
  result: CompatibilityResult | MultiMethodCompatibilityResult;
  personAName?: string;
  personBName?: string;
}

function ScoreBar({ score, max = 100, color = COLOR.gold }: { score: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-mono w-10 text-right" style={{ color: COLOR.ink }}>
        {typeof score === "number" ? score.toFixed(0) : "—"}
      </span>
    </div>
  );
}

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const stroke = 7;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct / 100);
  const color =
    pct >= 75 ? COLOR.jade :
    pct >= 60 ? COLOR.gold :
    pct >= 45 ? COLOR.azure :
    pct >= 30 ? COLOR.goldDim :
    COLOR.danger;

  return (
    <div className="relative inline-flex items-center justify-center "
      style={{ ["--glow-color" as string]: color }}>
      {/* 外圈慢旋装饰 */}
      <svg width={size + 16} height={size + 16} className="absolute " style={{ opacity: 0.15 }}>
        <circle cx={(size + 16) / 2} cy={(size + 16) / 2} r={r + 6}
          fill="none" stroke={color} strokeWidth="0.4" strokeDasharray="3 8" />
      </svg>
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={COLOR.lineSoft} strokeWidth={stroke} />
        {/* Score arc */}
        <circle cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 1.5s cubic-bezier(0.2, 0.7, 0.2, 1)",
          }}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold font-display" style={{ color }}>{score.toFixed(0)}</span>
        <span className="text-[10px] tracking-wider" style={{ color: COLOR.muted }}>分</span>
      </div>
    </div>
  );
}

function VerdictBadge({ level, score }: { level?: string; score: number }) {
  const lvl = level || (
    score >= 75 ? "天作之合" :
    score >= 60 ? "佳偶天成" :
    score >= 50 ? "中上之配" :
    score >= 40 ? "中等姻缘" :
    score >= 30 ? "多有磨合" : "需要慎重"
  );
  const color =
    score >= 75 ? COLOR.jade :
    score >= 60 ? COLOR.gold :
    score >= 50 ? COLOR.azure :
    score >= 40 ? COLOR.goldDim :
    COLOR.danger;

  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold"
      style={{
        color,
        background: `${color}15`,
        border: `1px solid ${color}40`,
      }}
    >
      <span
        className="inline-block w-1.5 h-1.5 rounded-full"
        style={{ background: color }}
      />
      {lvl}
    </span>
  );
}

export function CompatibilityReport({ result, personAName, personBName }: Props) {
  // Determine if multi-method
  const isMulti = "ensemble_score" in result && "method_scores" in result;
  const score = isMulti
    ? (result as MultiMethodCompatibilityResult).ensemble_score
    : (result as CompatibilityResult).compatibility_score
      || (result as CompatibilityResult).total_score
      || (result as CompatibilityResult).scoring?.compatibility_score
      || 50;

  const level = (result as CompatibilityResult).level
    || (result as CompatibilityResult).scoring?.interpretation?.level;

  const interpretation = (result as CompatibilityResult).interpretation
    || (result as CompatibilityResult).scoring?.interpretation?.description;

  const breakdown = (result as CompatibilityResult).breakdown
    || (result as CompatibilityResult).scoring?.breakdown
    || {};

  const methodScores = isMulti
    ? (result as MultiMethodCompatibilityResult).method_scores || []
    : [];

  const synastryResult = (result as any).results?.western_synastry
    || ((result as CompatibilityResult).cross_aspects ? result : null);

  const nameA = personAName || "A";
  const nameB = personBName || "B";

  return (
    <div className="space-y-5">
      {/* Score Hero */}
      <div className="paper-frame text-center relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at center, ${score >= 60 ? COLOR.jade : COLOR.gold}12 0%, transparent 70%)`,
          }}
        />
        {/* Gold dust subtle overlay for high scores */}
        {score >= 60 && (
          <div className="absolute inset-0 pointer-events-none opacity-30">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="absolute rounded-full "
                style={{
                  width: "3px", height: "3px",
                  left: `${15 + i * 14}%`, top: `${20 + (i * 17) % 60}%`,
                  background: COLOR.goldBright,
                  animationDelay: `${i * 0.4}s`,
                }} />
            ))}
          </div>
        )}
        <div className="relative z-10">
          <div className="text-xs uppercase tracking-widest mb-3" style={{ color: COLOR.muted }}>
            {nameA} × {nameB} · 合盘
          </div>
          <div className="flex items-center justify-center gap-6 flex-wrap">
            <ScoreRing score={score} size={130} />
            <div className="text-left">
              <VerdictBadge level={level} score={score} />
              {interpretation && (
                <div className="text-xs mt-2 max-w-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
                  {typeof interpretation === "string" ? interpretation : ""}
                </div>
              )}
            </div>
          </div>

          {/* Multi-method scores */}
          {methodScores.length > 0 && (
            <div className="mt-4 pt-3 border-t flex justify-center gap-4 flex-wrap"
              style={{ borderColor: COLOR.lineSoft }}>
              {methodScores.map((ms) => (
                <div key={ms.method} className="text-center">
                  <div className="text-[10px]" style={{ color: COLOR.muted }}>
                    {ms.method === "bazi" ? "八字合婚" : ms.method === "western_synastry" ? "西方合盘" : ms.method}
                  </div>
                  <div className="text-sm font-semibold" style={{ color: COLOR.ink }}>
                    {ms.score.toFixed(0)}
                    <span className="text-[9px] ml-0.5" style={{ color: COLOR.muted }}>
                      ({Math.round(ms.weight * 100)}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Dimension Breakdown */}
      {Object.keys(breakdown).length > 0 && (
        <div className="paper-frame">
          <h3 className="text-sm mb-3" style={{ color: COLOR.goldBright }}>■ 评分维度</h3>
          <div className="space-y-3">
            {Object.entries(breakdown).map(([key, data]: [string, any]) => {
              const max = data.max || 30;
              const s = data.score || 0;
              const pct = (s / max) * 100;
              const barColor =
                pct >= 70 ? COLOR.jade :
                pct >= 50 ? COLOR.gold :
                pct >= 35 ? COLOR.azure : COLOR.danger;

              const dimLabels: Record<string, string> = {
                day_master: "日主匹配",
                elements: "五行互补",
                branches: "地支关系",
                shensha: "神煞互补",
                pattern: "格局配合",
                cross_aspects: "跨盘相位",
                house_overlays: "宫位叠加",
                ascendant_connections: "上升连接",
                sun_moon: "日月连接",
              };

              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs" style={{ color: COLOR.inkSoft }}>
                      {dimLabels[key] || key}
                    </span>
                    <span className="text-[10px]" style={{ color: COLOR.muted }}>
                      {typeof s === "number" ? s.toFixed(1) : s} / {max}
                    </span>
                  </div>
                  <ScoreBar score={s} max={max} color={barColor} />
                  {data.detail && (
                    <div className="text-[9px] mt-0.5" style={{ color: COLOR.muted }}>{data.detail}</div>
                  )}
                  {data.aspects && data.aspects.length > 0 && (
                    <div className="text-[9px] mt-0.5" style={{ color: COLOR.inkSoft }}>
                      {data.aspects.join(" · ")}
                    </div>
                  )}
                  {data.connections && data.connections.length > 0 && (
                    <div className="text-[9px] mt-0.5" style={{ color: COLOR.azure }}>
                      {data.connections.map((c: string, i: number) => (
                        <div key={i}>{c}</div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Synastry Cross-Aspects */}
      {synastryResult?.cross_aspects?.length > 0 && (
        <div className="paper-frame">
          <h3 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>
            ◆ 跨盘相位 ({synastryResult.cross_aspects.length})
          </h3>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {synastryResult.cross_aspects.slice(0, 15).map((a: any, i: number) => {
              const aspectColors: Record<string, string> = {
                "合": COLOR.jade, "拱": COLOR.gold, "六合": COLOR.azure,
                "刑": COLOR.goldDim, "冲": COLOR.danger,
              };
              const clr = aspectColors[a.aspect] || COLOR.muted;
              return (
                <div key={i} className="flex items-center gap-2 text-xs py-0.5"
                  style={{ borderBottom: `1px solid ${COLOR.lineSoft}10` }}>
                  <span className="font-semibold" style={{ color: COLOR.ink }}>
                    {a.planet_a}
                  </span>
                  <span style={{ color: clr, fontWeight: 600 }}>
                    {a.aspect_label || a.aspect}
                  </span>
                  <span className="font-semibold" style={{ color: COLOR.ink }}>
                    {a.planet_b}
                  </span>
                  <span className="text-[9px] ml-auto" style={{ color: COLOR.muted }}>
                    orb {a.orb?.toFixed?.(1) ?? a.orb}°
                    {a.weight > 3 && (
                      <span className="ml-1" style={{ color: COLOR.goldBright }}>★重要</span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Synastry Overlays */}
      {synastryResult?.overlays && (
        <div className="paper-frame">
          <h3 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>■ 宫位叠加</h3>
          <div className="grid sm:grid-cols-2 gap-3 text-xs">
            {(["a_in_b", "b_in_a"] as const).map((key) => {
              const overlays = synastryResult.overlays[key] || {};
              const label = key === "a_in_b"
                ? `${nameA}的行星在${nameB}的宫位`
                : `${nameB}的行星在${nameA}的宫位`;
              const romanticHouses = [5, 7, 8];
              return (
                <div key={key}>
                  <div className="text-[10px] mb-1.5 font-semibold" style={{ color: COLOR.muted }}>{label}</div>
                  <div className="space-y-1">
                    {Object.entries(overlays as Record<string, any>).map(([planet, overlay]) => {
                      const isRomantic = romanticHouses.includes(overlay.house);
                      return (
                        <div key={planet} className="flex items-center gap-1.5">
                          <span style={{ color: COLOR.ink }}>{planet}</span>
                          <span style={{ color: COLOR.muted }}>→</span>
                          <span style={{
                            color: isRomantic ? COLOR.goldBright : COLOR.inkSoft,
                            fontWeight: isRomantic ? 600 : 400,
                          }}>
                            第{overlay.house}宫
                          </span>
                          {isRomantic && (
                            <span className="text-[9px]" style={{ color: COLOR.gold }}>
                              {overlay.house === 5 ? "吉" : overlay.house === 7 ? "合" : "烈"}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Advice */}
      {((result as CompatibilityResult).advice?.length ?? 0) > 0 && (
        <div className="paper-frame">
          <h3 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>· 建议</h3>
          <ul className="space-y-1">
            {(result as CompatibilityResult).advice!.map((a, i) => (
              <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: COLOR.inkSoft }}>
                <span style={{ color: COLOR.gold }}>•</span>
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
