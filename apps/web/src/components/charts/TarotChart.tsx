import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";

interface Card {
  position: string;
  position_meaning?: string;
  name: string;
  orient: "正位" | "逆位";
  keywords: string;
  system_reading?: string;
}

const ORIENT = {
  正位: { label: "正向能量", color: COLOR.jade },
  逆位: { label: "受阻/反向", color: COLOR.danger },
};

function TarotCard({ card, index }: { card: Card; index: number }) {
  const reversed = card.orient === "逆位";
  const orient = ORIENT[card.orient] || ORIENT.正位;
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="rounded-md flex flex-col items-center justify-center text-center p-2 tarot-flip"
        style={{
          width: 82,
          height: 116,
          transform: reversed ? "rotate(180deg)" : "none",
          background: `linear-gradient(135deg, ${COLOR.surface} 0%, ${COLOR.bgDeep} 100%)`,
          border: `1px solid ${COLOR.gold}`,
          boxShadow: `0 0 0 1px rgba(201,162,75,0.10), 0 0 14px rgba(201,162,75,0.10)`,
          animationDelay: `${index * 120}ms`,
        }}
      >
        <div className="text-[10px] leading-tight" style={{ color: COLOR.goldBright }}>{card.position}</div>
        <div className="text-xs font-display mt-2 leading-tight" style={{ color: COLOR.ink }}>{card.name}</div>
        <div className="text-[9px] mt-auto" style={{ color: orient.color }}>{card.orient}</div>
      </div>
      <div className="text-[10px] text-center max-w-[120px]" style={{ color: COLOR.muted }}>
        {card.position_meaning || orient.label}
      </div>
    </div>
  );
}

export function TarotChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const cards: Card[] = (r.cards || r.牌面 || []).map((c: any) => ({
    position: c.position || c.位置,
    position_meaning: c.position_meaning || c.位置含义,
    name: c.name || c.牌,
    orient: c.orient || c.方位,
    keywords: c.keywords || c.牌义,
    system_reading: c.system_reading || c.主体系解读,
  }));
  const basis = r.calculation_basis || {};
  const systemName = r.塔罗体系名称 || r.tarot_system_name;

  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            塔罗 · {r.spread_name || r.牌阵名称 || r.spread || r.牌阵}
          </h3>
          <div className="flex gap-2 flex-wrap text-xs">
            <span className="paper-tag paper-tag-west">{cards.length} 张</span>
            {systemName && <span className="paper-tag">{systemName}</span>}
            <span className="paper-tag">{r.subject || "tarot"}</span>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 justify-items-center">
          {cards.map((card, index) => <TarotCard key={`${card.position}-${index}`} card={card} index={index} />)}
        </div>
      </div>

      <div className="card-raised">
        <div className="text-xs mb-2" style={{ color: COLOR.muted }}>牌位与牌面</div>
        <ul className="space-y-1 text-sm">
          {cards.map((card, index) => {
            const orient = ORIENT[card.orient] || ORIENT.正位;
            return (
              <li key={index} className="flex flex-wrap gap-x-2 gap-y-1">
                <span style={{ color: COLOR.gold }}>{card.position}</span>
                <span style={{ color: COLOR.ink }}>{card.name}</span>
                <span className="text-[10px]" style={{ color: orient.color }}>{card.orient} · {orient.label}</span>
                {card.keywords && <span className="text-[10px]" style={{ color: COLOR.muted }}>{card.keywords}</span>}
                {card.system_reading && <span className="basis-full text-[10px]" style={{ color: COLOR.muted }}>{card.system_reading}</span>}
              </li>
            );
          })}
        </ul>
        <div className="mt-3 text-[10px] leading-relaxed" style={{ color: COLOR.muted }}>
          起法: {basis.draw_rule || "78 张牌不放回抽样"}；seed: {String(r.seed_used ?? r.抽牌参数?.seed ?? "随机")}
        </div>
      </div>
    </div>
  );
}
