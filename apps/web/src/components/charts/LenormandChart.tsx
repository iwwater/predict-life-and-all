// 雷诺曼: 卡牌阵型 + 组合解读 + 牌阵氛围分析
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";

const SUIT_SYMBOL: Record<string, string> = {
  "♠": "♠", "♣": "♣", "♥": "♥", "♦": "♦",
};
const SUIT_COLOR: Record<string, string> = {
  "♠": COLOR.ink, "♣": COLOR.jade, "♥": COLOR.danger, "♦": COLOR.azure,
};

function LenormandCard({ card, index, total }: { card: any; index: number; total: number }) {
  const posLabel = card.position || `第${index + 1}位`;
  const suit = (card.suit || "")[0] || "";
  const suitColor = SUIT_COLOR[suit] || COLOR.muted;
  const isCenter = total >= 5 && index === Math.floor(total / 2);

  return (
    <div
      className="rounded-md p-3 flex flex-col gap-1.5 relative"
      style={{
        background: isCenter ? `linear-gradient(135deg, rgba(201,162,75,0.08), rgba(8,10,15,0.6))` : "rgba(8,10,15,0.4)",
        border: `1px solid ${isCenter ? COLOR.goldDim : COLOR.line}`,
      }}
    >
      {/* Position badge */}
      <div className="flex items-center justify-between gap-2">
        <span
          className="text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded"
          style={{ background: isCenter ? "rgba(201,162,75,0.15)" : "rgba(255,255,255,0.04)", color: isCenter ? COLOR.gold : COLOR.muted }}
        >
          {posLabel}
          {isCenter && " · 核心"}
        </span>
        {card.timing && (
          <span className="text-[9px]" style={{ color: COLOR.muted }}>
            ⏱ {card.timing}
          </span>
        )}
      </div>

      {/* Card name */}
      <div className="flex items-baseline gap-2">
        <span className="text-base font-semibold" style={{ color: COLOR.goldBright }}>
          {card.name_zh}
        </span>
        <span className="text-[10px] uppercase tracking-wide" style={{ color: suitColor }}>
          {card.name_en}
        </span>
        {suit && (
          <span className="text-[11px] ml-auto" style={{ color: suitColor }}>
            {suit}
          </span>
        )}
      </div>

      {/* Core meaning */}
      <p className="text-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
        {card.core_meaning}
      </p>

      {/* Position meaning hint */}
      {card.position_meaning && (
        <div className="text-[9px] italic mt-0.5" style={{ color: COLOR.muted }}>
          「{card.position_meaning}」
        </div>
      )}
    </div>
  );
}

export function LenormandChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const cards: any[] = r.cards || [];
  const analysis = r.analysis || {};
  const pairs: any[] = analysis.pairs || [];
  const tone = analysis.tone || "neutral";
  const maleCards = analysis.male_cards ?? 0;
  const femaleCards = analysis.female_cards ?? 0;
  const spreadName = r.spread_name || r.spread || "牌阵";
  const basis = r.calculation_basis || {};

  const toneCfg: Record<string, { label: string; bg: string; fg: string }> = {
    positive: { label: "吉 · 阳性能量主导", bg: "rgba(79,179,160,0.12)", fg: COLOR.jade },
    neutral: { label: "平 · 阴阳均衡", bg: "rgba(161,161,170,0.10)", fg: COLOR.muted },
    negative: { label: "提醒 · 阴性能量偏重", bg: "rgba(200,85,61,0.10)", fg: COLOR.danger },
  };
  const tc = toneCfg[tone] || toneCfg.neutral;

  return (
    <div className="space-y-4">
      {/* Header card */}
      <div className="card">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            雷诺曼 · {spreadName}
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span
              className="tag text-xs"
              style={{ background: tc.bg, color: tc.fg, border: `1px solid ${tc.fg}40` }}
            >
              {tc.label}
            </span>
            <span className="tag tag-west">{cards.length} 张 · 无逆位</span>
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex gap-4 mt-3 text-xs flex-wrap">
          <Stat label="阳牌" value={`${maleCards} 张`} tone="gold" />
          <Stat label="阴牌" value={`${femaleCards} 张`} tone="azure" />
          <Stat label="牌阵" value={spreadName} tone="ink" />
          {basis.mode && <Stat label="模式" value={basis.mode} tone="ink" />}
        </div>
      </div>

      {/* Card layout */}
      <div className="card">
        <h4 className="text-sm mb-4" style={{ color: COLOR.gold }}>
          牌面布局
        </h4>
        <div className={`grid gap-3 ${cards.length <= 3 ? "grid-cols-1 sm:grid-cols-3" : cards.length <= 5 ? "grid-cols-1 sm:grid-cols-3" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"}`}>
          {cards.map((c, i) => (
            <LenormandCard key={i} card={c} index={i} total={cards.length} />
          ))}
        </div>
      </div>

      {/* Pairs combination analysis — the soul of Lenormand */}
      {pairs.length > 0 && (
        <div className="card">
          <h4 className="text-sm mb-4" style={{ color: COLOR.gold }}>
            相邻牌组合解读
            <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
              — 雷诺曼的灵魂: 两张相邻牌共同产生新含义
            </span>
          </h4>
          <div className="space-y-3">
            {pairs.map((pair: any, i: number) => (
              <div
                key={i}
                className="rounded-md p-3 text-sm leading-relaxed flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3"
                style={{ background: "rgba(8,10,15,0.3)", border: `1px solid ${COLOR.lineSoft}` }}
              >
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="font-semibold" style={{ color: COLOR.goldDim }}>
                    {pair.card1_zh || pair.card1}
                  </span>
                  <span className="text-xs" style={{ color: COLOR.muted }}>
                    +
                  </span>
                  <span className="font-semibold" style={{ color: COLOR.goldDim }}>
                    {pair.card2_zh || pair.card2}
                  </span>
                </div>
                <span className="hidden sm:inline text-xs" style={{ color: COLOR.muted }}>
                  →
                </span>
                <span style={{ color: COLOR.inkSoft }}>{pair.combined}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
        <p>雷诺曼 36 张 · 传统 Petit Lenormand 体系 · 无逆位 · 牌义高度依赖邻近组合</p>
        <p>组合含义来源于传统法国/德国学派 + 174 组已知固定组合 (共 630 组可能相邻)</p>
      </div>
    </div>
  );
}
