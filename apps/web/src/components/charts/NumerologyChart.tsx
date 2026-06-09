// 数字命理 · 完整版:生命灵数 + 核心数字 + 周期数字
// v2: 支持多个核心数字(Destiny/Soul Urge/Personality/Maturity)和流年流月
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon } from "../Jargon";

interface NumberCard {
  name: string;
  name_en: string;
  number: number;
  is_master: boolean;
  meaning: {
    title: string;
    keywords: string[];
    strength: string;
    challenge: string;
    element: string;
    planet: string;
    color: string;
    career: string[];
    is_master?: boolean;
  };
  importance: string;
  description: string;
}

interface CycleCard {
  name: string;
  name_en: string;
  number: number;
  year?: number;
  month?: string;
  meaning: {
    title: string;
    keywords: string[];
    strength: string;
    element: string;
    planet: string;
  };
  description: string;
}

function NumberGlow({ number, size = "lg" }: { number: number; size?: "lg" | "md" | "sm" }) {
  const isMaster = number === 11 || number === 22 || number === 33;
  const sizes = { lg: "text-7xl sm:text-8xl", md: "text-4xl", sm: "text-3xl" };
  const glows = { lg: 28, md: 16, sm: 12 };
  return (
    <div
      className={`${sizes[size]} font-display my-1`}
      style={{
        color: isMaster ? COLOR.goldBright : COLOR.gold,
        textShadow: isMaster
          ? `0 0 ${glows[size]}px ${COLOR.goldBright}, 0 0 ${glows[size] * 2}px ${COLOR.gold}`
          : `0 0 ${glows[size]}px ${COLOR.gold}`,
      }}
    >
      {number}
    </div>
  );
}

function CoreNumberCard({ card }: { card: NumberCard }) {
  const m = card.meaning;
  return (
    <div
      className="card lift-on-hover relative overflow-hidden"
      style={{
        borderColor: card.importance === "primary" ? COLOR.gold : COLOR.line,
        background: card.importance === "primary"
          ? "rgba(201,162,75,0.06)"
          : "rgba(255,255,255,0.02)",
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-xs font-semibold" style={{ color: COLOR.goldBright }}>
            {card.name}
          </div>
          <div className="text-[9px] uppercase tracking-wider" style={{ color: COLOR.muted }}>
            {card.name_en}
          </div>
        </div>
        {card.importance === "primary" && (
          <span className="tag text-[9px]" style={{ borderColor: COLOR.gold, color: COLOR.goldBright }}>
            核心
          </span>
        )}
      </div>
      <NumberGlow number={card.number} size="md" />
      <div className="text-sm font-semibold mt-1" style={{ color: COLOR.ink }}>
        {m.title}
      </div>
      <div className="flex flex-wrap gap-1 mt-1.5">
        {m.keywords.map((kw) => (
          <span key={kw} className="text-[9px] px-1.5 py-0.5 rounded"
            style={{ background: "rgba(255,255,255,0.04)", color: COLOR.inkSoft, border: "1px solid var(--line-soft)" }}>
            {kw}
          </span>
        ))}
      </div>
      <div className="text-[10px] mt-2 leading-relaxed" style={{ color: COLOR.muted }}>
        {card.description}
      </div>
    </div>
  );
}

export function NumerologyChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;

  // v2 format: core_numbers array
  const coreNumbers: NumberCard[] = r.core_numbers || [];
  const cycleNumbers: CycleCard[] = r.cycle_numbers || [];

  // v1 backward compat
  const lifeLegacy = r.life_path;
  const meaningLegacy = r.meaning;
  const isMasterLegacy = r.is_master;

  // Life path profile for hero
  const lifeProfile = r.life_path_profile || {};

  return (
    <div className="space-y-4">
      {/* Hero: 生命路径 */}
      <div className="card text-center relative overflow-hidden">
        {/* bg glow */}
        <div className="absolute inset-0 pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at center, rgba(201,162,75,0.08) 0%, transparent 70%)`,
          }}
        />
        <div className="relative z-10">
          <div className="text-xs uppercase tracking-widest mb-2" style={{ color: COLOR.muted }}>
            <Jargon term="生命灵数" mode="plain" /> · Life Path
          </div>
          <NumberGlow number={lifeLegacy ?? coreNumbers[0]?.number ?? 0} size="lg" />
          {isMasterLegacy && (
            <div className="tag tag-west">
              <Jargon term="Master" mode="plain" />
            </div>
          )}
          <div className="mt-2 text-base font-semibold" style={{ color: COLOR.ink }}>
            {lifeProfile.title || ""}
          </div>
          <div className="mt-2 text-sm max-w-md mx-auto leading-relaxed" style={{ color: COLOR.inkSoft }}>
            {lifeProfile.strength || meaningLegacy || ""}
          </div>
          {lifeProfile.challenge && (
            <div className="mt-1.5 text-xs max-w-md mx-auto" style={{ color: COLOR.muted }}>
              ⚠ {lifeProfile.challenge}
            </div>
          )}
        </div>
      </div>

      {/* 核心数字卡片网格 */}
      {coreNumbers.length > 0 && (
        <div>
          <h3 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>
            📐 核心数字 ({coreNumbers.length})
          </h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {coreNumbers.map((cn) => (
              <CoreNumberCard key={cn.name_en} card={cn} />
            ))}
          </div>
        </div>
      )}

      {/* 周期数字: 流年 + 流月 */}
      {cycleNumbers.length > 0 && (
        <div>
          <h3 className="text-sm mb-2" style={{ color: COLOR.goldBright }}>
            🔄 周期运势
          </h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {cycleNumbers.map((cy) => {
              const m = cy.meaning;
              return (
                <div key={cy.name_en} className="card"
                  style={{ borderColor: COLOR.line, background: "rgba(91,141,239,0.04)" }}>
                  <div className="text-xs font-semibold mb-1" style={{ color: COLOR.azure }}>
                    {cy.name}
                  </div>
                  <div className="flex items-end gap-3">
                    <NumberGlow number={cy.number} size="sm" />
                    <div>
                      <div className="text-sm font-semibold" style={{ color: COLOR.ink }}>
                        {m.title}
                      </div>
                      <div className="text-[10px]" style={{ color: COLOR.muted }}>
                        {cy.year || cy.month || ""}
                      </div>
                    </div>
                  </div>
                  <div className="text-[10px] mt-2 leading-relaxed" style={{ color: COLOR.inkSoft }}>
                    {cy.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 详细信息卡 */}
      <div className="card-raised text-xs space-y-1.5" style={{ color: COLOR.muted }}>
        <div>
          <span style={{ color: COLOR.muted }}>出生数总和</span>{" "}
          <span style={{ color: COLOR.ink }}>{r.birth_sum}</span>
        </div>
        <div>
          <span style={{ color: COLOR.muted }}>计算方法</span>{" "}
          逐位求和 → <Jargon term="化简" mode="plain" /> 至 1-9 或 11/22/33
        </div>
        {r.has_name_data && (
          <div>
            <span style={{ color: COLOR.muted }}>名字输入</span>{" "}
            <span style={{ color: COLOR.ink }}>{r.name_provided}</span>
          </div>
        )}
        {isMasterLegacy && (
          <div className="mt-1" style={{ color: COLOR.goldBright }}>
            你是 <Jargon term="Master" mode="plain" /> — 11/22/33 三种特别灵数,业内称"大师数",代表更强烈的人生主题
          </div>
        )}
        <div className="mt-1 pt-1.5 border-t" style={{ borderColor: COLOR.lineSoft }}>
          <span style={{ color: COLOR.muted }}>版本</span>{" "}
          <span style={{ color: COLOR.ink }}>{r.rule_version || "v1"}</span>
          <span className="ml-3" style={{ color: COLOR.muted }}>已计算核心数</span>{" "}
          <span style={{ color: COLOR.ink }}>{coreNumbers.length || 1}</span>
        </div>
      </div>
    </div>
  );
}
