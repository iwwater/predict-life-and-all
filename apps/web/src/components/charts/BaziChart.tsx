// 八字四柱表(年/月/日/时,各列上干下支,大运时间轴 + 五行雷达)
// 术语全用 <Jargon> 包起来,显示"术语·大白话"
// v2: 增加藏干、十神、12长生、身强评分进度条、流年互动
// v3: 支持交叉验证、桃花指数、改命建议展示
import type { ChartResult } from "../../lib/types";
import type { CrossValidationResult, PeachBlossomResult, FateModificationPlan } from "../../lib/api";
import { COLOR, Stat } from "../ui";
import { ElementsRadar } from "../ElementsRadar";
import { Jargon } from "../Jargon";

interface BaziChartProps {
  chart: ChartResult;
  crossValidation?: CrossValidationResult | null;
  peachBlossom?: PeachBlossomResult | null;
  fateModification?: FateModificationPlan | null;
}

export function BaziChart({ chart, crossValidation, peachBlossom, fateModification }: BaziChartProps) {
  const r = chart.raw;
  const pillars = r.pillars || {};
  const pd: any[] = r.pillar_details || [];
  const cols: Array<{ key: string; term: string; override: { plain: string; hint: string } }> = [
    { key: "year",  term: "年柱", override: { plain: "出生那年",   hint: "代表祖辈、0-15 岁的大运背景" } },
    { key: "month", term: "月柱", override: { plain: "出生那月",   hint: "代表父母、青年时期的成长环境" } },
    { key: "day",   term: "日柱", override: { plain: "你自己",     hint: "代表命主自己与配偶" } },
    { key: "hour",  term: "时柱", override: { plain: "出生那时",   hint: "代表子女、晚年的归宿" } },
  ];
  const timeline = chart.normalized.timeline || [];
  const score = r.strength_score as number | undefined;
  const sb = r.strength_basis as any;
  const cl = r.current_luck as any;
  const ai = r.annual_interactions as any;
  const ls = r.life_stage as any;

  return (
    <div className="space-y-4">
      {/* 四柱表 */}
      <div className="card">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            <Jargon term="四柱" />·八字
          </h3>
          <span className="tag tag-east">
            <Jargon term="日主" mode="plain" /> {r.day_master || "—"}
          </span>
        </div>
        <div className="grid grid-cols-4 gap-2 sm:gap-3">
          {cols.map((c) => {
            const gz = pillars[c.key] || "??";
            const detail = pd.find((d: any) => d.label === c.key);
            const hs = detail?.hidden_stems || [];
            const shigan = detail?.ten_god_stem || "";
            const gs = detail?.growth_stage || "";
            return (
              <div key={c.key}
                className="rounded-md p-3 text-center"
                style={{ background: "rgba(8,10,15,0.5)", border: `1px solid ${COLOR.line}` }}>
                <div className="mb-2 text-[10px] uppercase tracking-widest"
                  style={{ color: COLOR.muted, position: "relative" }}>
                  <Jargon term={c.term} override={c.override} />
                </div>
                <div className="text-2xl sm:text-3xl font-display" style={{ color: COLOR.gold }}>{gz[0] || "?"}</div>
                <div className="text-2xl sm:text-3xl font-display mt-1" style={{ color: COLOR.ink }}>{gz[1] || "?"}</div>
                {hs.length > 0 && (
                  <div className="text-[9px] mt-1" style={{ color: COLOR.muted }}>
                    藏:{hs.join("/")}
                  </div>
                )}
                {shigan && (
                  <div className="text-[9px] mt-0.5" style={{ color: COLOR.jade }}>
                    {shigan}
                  </div>
                )}
                {gs && (
                  <div className="text-[9px] mt-0.5" style={{ color: COLOR.azure }}>
                    {gs}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div className="card flex justify-center">
          <ElementsRadar elements={chart.normalized.elements || {}} variant="five"
            title={`${r.day_master || "—"} 的五行`} />
        </div>
        <div className="card">
          <h3 className="text-sm mb-3" style={{ color: COLOR.goldBright }}>
            <Jargon term="大运" />·十年换一次
          </h3>
          {timeline.length === 0
            ? <p className="text-xs" style={{ color: COLOR.muted }}>未生成大运。</p>
            : (
              <ul className="space-y-1.5">
                {timeline.map((t, i) => (
                  <li key={i} className="flex justify-between text-sm">
                    <span style={{ color: COLOR.ink }}>{t.label}</span>
                    <span style={{ color: COLOR.muted }}>{t.from}-{t.to}</span>
                  </li>
                ))}
              </ul>
            )}
        </div>
      </div>

      {/* 身强评分 */}
      {typeof score === "number" && (
        <div className="card space-y-2">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>日主身强评分</h3>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
              <div className="h-full rounded-full transition-all" style={{
                width: `${Math.min(score, 100)}%`,
                background: score < 30 ? COLOR.danger : score < 55 ? COLOR.gold : score < 75 ? COLOR.jade : COLOR.ok,
              }} />
            </div>
            <span className="text-sm font-mono" style={{ color: COLOR.ink }}>{score}/100</span>
          </div>
          {sb && (
            <div className="text-[10px] space-x-3" style={{ color: COLOR.muted }}>
              <span>比劫{sb.peer_count}</span><span>印星{sb.resource_count}</span>
              <span>食伤{sb.output_count}</span><span>官杀{sb.official_count}</span>
              <span>财{sb.wealth_count}</span><span>月令分{sb.month_strength}</span>
            </div>
          )}
        </div>
      )}

      {/* 流年互动 */}
      {ai?.interactions?.length > 0 && (
        <div className="card space-y-1.5">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>
            流年 {ai.ganzhi} 与原局互动
          </h3>
          {ai.interactions.map((it: any, i: number) => (
            <div key={i} className="text-xs" style={{ color: COLOR.inkSoft }}>{it.note}</div>
          ))}
        </div>
      )}

      {/* 12长生四柱标记 */}
      {ls?.stages?.length > 0 && (
        <div className="card space-y-1.5">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>
            <Jargon term="十二长生" />·{ls.day_master}{ls.is_yang ? "阳顺" : "阴逆"}
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            {ls.stages.map((s: any) => (
              <div key={s.pillar} className="px-2 py-1 rounded text-xs" style={{ background: COLOR.bgDeep, border: `1px solid ${COLOR.lineSoft}` }}>
                <span style={{ color: COLOR.muted }}>{s.pillar} </span>
                <span style={{ color: COLOR.ink }}>{s.zhi}→{s.stage}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 当前运势摘要 */}
      {cl?.decade_ganzhi && (
        <div className="card space-y-1">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>当前运势</h3>
          <div className="text-sm" style={{ color: COLOR.ink }}>
            大运 {cl.decade_ganzhi}({cl.decade_from}-{cl.decade_to}) · {cl.annual_label}
          </div>
          {typeof cl.decade_score === "number" && (
            <div className="text-xs" style={{ color: COLOR.muted }}>阶段评分: {cl.decade_score}</div>
          )}
        </div>
      )}

      {/* ── 桃花指数 ── */}
      {peachBlossom && typeof peachBlossom.index === "number" && (
        <div className="card space-y-2">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>
            🌸 桃花指数 · 感情运
          </h3>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
              <div className="h-full rounded-full transition-all" style={{
                width: `${Math.min(peachBlossom.index, 100)}%`,
                background: `linear-gradient(90deg, ${COLOR.gold}, #ff6b9d)`,
              }} />
            </div>
            <span className="text-sm font-mono" style={{ color: COLOR.ink }}>{Math.round(peachBlossom.index)}/100</span>
          </div>
          {peachBlossom.level && (
            <div className="text-xs" style={{ color: COLOR.inkSoft }}>
              评级: <span style={{ color: COLOR.goldBright }}>{peachBlossom.level}</span>
              {peachBlossom.timing && ` · 时机: ${peachBlossom.timing}`}
            </div>
          )}
          {peachBlossom.details?.taohua_stars?.length > 0 && (
            <div className="text-[10px]" style={{ color: COLOR.muted }}>
              桃花星: {peachBlossom.details!.taohua_stars.join("、")}
            </div>
          )}
        </div>
      )}

      {/* ── 交叉验证支持度 ── */}
      {crossValidation && typeof crossValidation.ensemble_score === "number" && (
        <div className="card space-y-2">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>
            🔗 多系统交叉验证
          </h3>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full" style={{ background: COLOR.lineSoft, overflow: "hidden" }}>
              <div className="h-full rounded-full transition-all" style={{
                width: `${Math.min(crossValidation.ensemble_score, 100)}%`,
                background: crossValidation.ensemble_score >= 70 ? COLOR.jade
                  : crossValidation.ensemble_score >= 45 ? COLOR.gold : COLOR.danger,
              }} />
            </div>
            <span className="text-sm font-mono" style={{ color: COLOR.ink }}>{Math.round(crossValidation.ensemble_score)}%</span>
          </div>
          {crossValidation.overall_assessment && (
            <div className="text-xs" style={{ color: COLOR.inkSoft }}>
              {crossValidation.overall_assessment}
            </div>
          )}
          {crossValidation.domain_checks && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {Object.entries(crossValidation.domain_checks).map(([domain, check]: [string, any]) => {
                const dl: Record<string, string> = {
                  self_life: "本命", career: "事业", wealth: "财富",
                  relationship: "感情", health: "健康", timing: "时机",
                };
                const conf = typeof check.confidence === "number" ? check.confidence
                  : typeof check.agreement === "number" ? check.agreement * 100 : null;
                return (
                  <div key={domain} className="px-2 py-1 rounded text-[10px]"
                    style={{ background: COLOR.bgDeep, border: `1px solid ${COLOR.lineSoft}` }}>
                    <span style={{ color: COLOR.muted }}>{dl[domain] || domain} </span>
                    {conf !== null && (
                      <span style={{ color: conf >= 70 ? COLOR.jade : conf >= 45 ? COLOR.gold : COLOR.danger }}>
                        {Math.round(conf)}%
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── 改命建议 ── */}
      {fateModification && (fateModification.daily_practices?.length || fateModification.mutable_patterns?.length) && (
        <div className="card space-y-2">
          <h3 className="text-sm" style={{ color: COLOR.goldBright }}>
            🌿 五行调理 · 改命建议
          </h3>
          {fateModification.element_balance?.advice && (
            <div className="text-xs" style={{ color: COLOR.inkSoft }}>
              {fateModification.element_balance.advice}
            </div>
          )}
          {fateModification.mutable_patterns && fateModification.mutable_patterns.length > 0 && (
            <ul className="text-[10px] space-y-1" style={{ color: COLOR.jade }}>
              {fateModification.mutable_patterns.map((p: any, i: number) => (
                <li key={i}>
                  <span className="font-semibold">{p.aspect || p}</span>
                  {p.description && <span className="ml-1" style={{ color: COLOR.inkSoft }}>— {p.description}</span>}
                </li>
              ))}
            </ul>
          )}
          {fateModification.fixed_patterns && fateModification.fixed_patterns.length > 0 && (
            <ul className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
              {fateModification.fixed_patterns.map((p: any, i: number) => (
                <li key={i}>
                  <span className="font-semibold">{p.aspect || p}</span>
                  {p.description && <span className="ml-1">— {p.description}</span>}
                </li>
              ))}
            </ul>
          )}
          {fateModification.daily_practices && fateModification.daily_practices.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] font-semibold" style={{ color: COLOR.gold }}>日常实践:</div>
              <ul className="text-[10px] space-y-1" style={{ color: COLOR.inkSoft }}>
                {fateModification.daily_practices.map((p: any, i: number) => (
                  <li key={i} className="pl-2 border-l" style={{ borderColor: COLOR.lineSoft }}>
                    <div className="flex items-center gap-2">
                      {p.time && <span className="tag text-[9px]" style={{ color: COLOR.goldBright, borderColor: COLOR.line }}>{p.time}</span>}
                      <span>{p.practice || p}</span>
                    </div>
                    {p.benefit && <div className="mt-0.5" style={{ color: COLOR.muted }}>{p.benefit}</div>}
                    {p.duration && <div className="text-[9px]" style={{ color: COLOR.muted }}>⏱ {p.duration}</div>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="card-raised flex gap-6 flex-wrap">
        <Stat label="排盘算法" value={chart.engine} tone="ink" />
        <Stat label="学派" value="东方·命" tone="jade" />
      </div>
    </div>
  );
}
