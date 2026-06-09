// 结果页:左侧盘面(Tab 切换 / 单盘) + 右侧解读面板
// Cut 2 增量:收藏 / 反馈 / 分享卡(本地 store;分享卡模板化)
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Birth, ChartResult, Method } from "../lib/types";
import type { CrossValidationResult, PeachBlossomResult, FateModificationPlan } from "../lib/api";
import { ChartRenderer } from "../components/charts";
import { Interpretation } from "../components/Interpretation";
import { BaziKline } from "../components/BaziKline";
import { Jargon } from "../components/Jargon";
import { COLOR, SchoolChip, EmptyBox } from "../components/ui";
import { METHOD_PLAIN } from "../lib/method-info";
import { useHistory, type Reflection, type ReflectionVerdict } from "../store/history";
import { buildShareCard, shareCardToText, type ShareCard } from "../lib/share";
import { OrnamentalDivider } from "../components/Interactions";
import { YinYang, AuspiciousClouds } from "../components/MysticElements";
import { useI18n } from "../lib/i18n";

interface ResultState {
  birth?: Birth;
  question?: string;
  charts: Record<string, ChartResult>;
  methods: Method[];
  enhancedData?: {
    cross_validation?: CrossValidationResult;
    peach_blossom?: PeachBlossomResult;
    relationship_timing?: any;
    fate_modification?: FateModificationPlan;
  };
}

export function Result() {
  const { t, lang } = useI18n();
  const REFLECT_CHOICES: { v: ReflectionVerdict; label: string; color: string }[] = [
    { v: "accurate",   label: lang === "zh" ? "准" : "Yes",     color: "var(--ok)" },
    { v: "inaccurate", label: lang === "zh" ? "不准" : "No",   color: "var(--danger)" },
    { v: "pending",    label: lang === "zh" ? "待观察" : "Maybe", color: "var(--muted)" },
  ];
  const [data, setData] = useState<ResultState | null>(null);
  const [hid, setHid] = useState<string | null>(null);
  const [active, setActive] = useState<Method | "all">("all");
  const [share, setShare] = useState<ShareCard | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("mystic:result");
    if (!raw) return;
    try {
      const d = JSON.parse(raw);
      setData(d);
      setActive(d.methods?.[0] || "all");
    } catch { /* noop */ }
    setHid(sessionStorage.getItem("mystic:result_id"));
  }, []);

  // 从 store 同步当前条目(收藏/反馈)
  const entry = useHistory((s) => (hid ? s.items.find((i) => i.id === hid) : undefined));
  const toggleFavorite = useHistory((s) => s.toggleFavorite);
  const setReflection = useHistory((s) => s.setReflection);

  const reflectionVerdict = entry?.reflection?.verdict;

  const showChart = useMemo(() => {
    if (!data) return null;
    if (active === "all") {
      const first = data.methods.map((m) => data.charts[m]).filter(Boolean)[0];
      return first || null;
    }
    return data.charts[active as string] || null;
  }, [data, active]);

  if (!data || data.methods.length === 0) {
    return (
      <EmptyBox>
        {t("result.empty")}<Link to="/cast" className="underline ml-1" style={{ color: COLOR.gold }}>{lang === "zh" ? "去排盘 →" : "Cast →"}</Link>
      </EmptyBox>
    );
  }

  const chartList = data.methods.map((m) => data.charts[m]).filter(Boolean);

  function openShare() {
    if (!entry) return;
    setShare(buildShareCard(entry));
    setCopied(false);
  }

  function pickReflection(v: ReflectionVerdict) {
    if (!entry) return;
    const next: Reflection | null = entry.reflection?.verdict === v
      ? null  // 再次点同项 = 取消
      : { verdict: v, at: Date.now() };
    setReflection(entry.id, next);
  }

  async function copyShare() {
    if (!share) return;
    const text = shareCardToText(share);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // 退化:弹 textarea
      window.prompt("复制以下文本:", text);
    }
  }

  return (
    <div className="space-y-4">
      {/* 阴阳装饰 + 祥云 */}
      <div className="fixed right-6 top-20 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <YinYang size={80} />
      </div>
      <div className="fixed right-0 bottom-0 pointer-events-none opacity-[0.06] z-0" aria-hidden>
        <AuspiciousClouds />
      </div>
      <div className="card-raised card-highlight flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-3 flex-wrap">
          <span style={{ color: COLOR.muted }}>
            <Jargon term="命主" mode="plain" />
          </span>
          <span style={{ color: COLOR.ink }}>{data.birth?.year}-{data.birth?.month}-{data.birth?.day} {data.birth?.hour}:{String(data.birth?.minute).padStart(2, "0")}</span>
          <span style={{ color: COLOR.muted }}>· {data.birth?.gender}</span>
          {data.question && <span className="ml-2" style={{ color: COLOR.gold }}>「{data.question}」</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn-ghost text-xs"
            onClick={() => entry && toggleFavorite(entry.id)}
            disabled={!entry}
            title={entry?.favorite ? (lang === "zh" ? "取消收藏" : "Unsave") : (lang === "zh" ? "收藏这条排盘" : "Save this chart")}
            style={entry?.favorite ? { color: COLOR.goldBright, borderColor: COLOR.gold } : undefined}
          >
            {entry?.favorite ? t("result.favorited") : t("result.favorite")}
          </button>
          <div className="flex items-center gap-1" role="group" aria-label="反馈">
            {REFLECT_CHOICES.map((c) => {
              const on = reflectionVerdict === c.v;
              return (
                <button
                  key={c.v}
                  className="btn-ghost text-xs"
                  onClick={() => pickReflection(c.v)}
                  disabled={!entry}
                  style={on ? { color: c.color, borderColor: c.color } : undefined}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
          <button className="btn-ghost text-xs" onClick={openShare} disabled={!entry}>
            {t("result.share")}
          </button>
          <Link to="/cast" className="btn-ghost text-xs">{t("result.cast.again")}</Link>
        </div>
      </div>

      {/* 12 法 Tab — 主标 + tagline 白话副标 */}
      <div className="flex flex-wrap gap-1.5">
        {data.methods.map((m) => {
          const c = data.charts[m];
          const plain = METHOD_PLAIN[m];
          return (
            <button key={m} onClick={() => setActive(m)}
              title={plain?.tagline}
              className={`tag cursor-pointer text-left transition-all duration-200 ${active === m ? "nav-link-active" : ""}`}
              style={active === m ? { boxShadow: `0 0 8px ${COLOR.gold}40` } : undefined}>
              <span className="font-semibold">{methodLabel(m)}</span>
              {c?.school && <span className="ml-1 opacity-70">· {c.school === "east" ? "东" : "西"}</span>}
              {plain?.tagline && (
                <span className="ml-1.5 font-normal opacity-75 hidden sm:inline">· {plain.tagline}</span>
              )}
            </button>
          );
        })}
      </div>

      <OrnamentalDivider />

      <div className="grid lg:grid-cols-2 gap-5">
        {/* 左:盘面 */}
        <div className="space-y-4">
          {showChart ? (
            <>
              <ChartRenderer
                chart={showChart}
                crossValidation={data.enhancedData?.cross_validation ?? null}
                peachBlossom={data.enhancedData?.peach_blossom ?? null}
                fateModification={data.enhancedData?.fate_modification ?? null}
              />
              <CalculationBasis chart={showChart} />
            </>
          ) : <EmptyBox>{lang === "zh" ? "盘面数据丢失" : "Chart data lost"}</EmptyBox>}
          {data.charts.bazi && data.charts.bazi.method === "bazi" && (
            <BaziKline chart={data.charts.bazi} />
          )}
        </div>

        {/* 右:解读 */}
        <div className="space-y-4">
          <Interpretation
            charts={chartList}
            question={data.question || ""}
            enhancedData={data.enhancedData ?? undefined}
          />
        </div>
      </div>

      {share && <ShareCardModal card={share} copied={copied} onClose={() => setShare(null)} onCopy={copyShare} />}
    </div>
  );
}

function methodLabel(m: Method) {
  return ({
    bazi: "八字", bazi_v2: "八字·精算", ziwei: "紫微", qimen: "奇门",
    liuyao: "六爻", meihua: "梅花", chenggu: "称骨",
    bazhai: "八宅", xuankong: "玄空",
    western: "西方占星", vedic: "吠陀",
    tarot: "塔罗", numerology: "数字命理",
    lenormand: "雷诺曼", liuren: "大六壬", tieban: "铁板神数",
    cross_validator: "交叉验证 / Cross-Validation", hour_calibrator: "时辰校准 / Hour Calibration", compatibility: "合婚 / Match",
  } as Record<Method, string>)[m] || m;
}

function CalculationBasis({ chart }: { chart: ChartResult }) {
  const { t } = useI18n();
  const basis = chart.raw?.calculation_basis;
  if (!basis) return null;
  const limits: string[] = Array.isArray(basis.limits) ? basis.limits : [];
  return (
    <div className="card-raised card-highlight text-xs leading-relaxed space-y-1" style={{ color: COLOR.muted }}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-semibold" style={{ color: COLOR.goldBright }}>{t("result.basis.title")}</span>
        {basis.rule_version && (
          <span className="tag" style={{ borderColor: COLOR.gold, color: COLOR.goldBright }}>v{basis.rule_version}</span>
        )}
        {chart.method === "ziwei" && chart.raw?.fallback && (
          <span className="tag" style={{ borderColor: COLOR.danger, color: COLOR.danger }} title={chart.raw?.fallback_reason || ""}>
            fallback
          </span>
        )}
      </div>
      <div>方法: {basis.method || chart.method} · 模式: {basis.mode || chart.raw?.mode || "默认"} · 对象: {basis.subject || chart.raw?.subject || "未标注"}</div>
      {basis.input_source && <div>输入: {basis.input_source}</div>}
      {basis.rule && <div>规则: {basis.rule}</div>}
      {basis.scope && <div>范围: {basis.scope}</div>}
      {basis.calendar_source && <div>历法来源: {basis.calendar_source}</div>}
      {basis.draw_rule && <div>抽牌规则: {basis.draw_rule}</div>}
      {basis.period_rule && <div>元运: {basis.period_rule}</div>}
      {basis.sitting_rule && <div>坐向: {basis.sitting_rule}</div>}
      {limits.length > 0 && (
        <details className="pt-1">
          <summary className="cursor-pointer" style={{ color: COLOR.goldBright }}>不可判断范围 / 限制 ({limits.length})</summary>
          <ul className="mt-1 space-y-0.5 list-disc pl-5">
            {limits.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </details>
      )}
      <MethodExtras chart={chart} />
    </div>
  );
}

// 各法专项展开(Cut 6/7/8/9/10/11 补全字段)
function MethodExtras({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  if (chart.method === "bazi" || chart.method === "bazi_v2") {
    const score = r.strength_score;
    const cl = r.current_luck || {};
    const ai = r.annual_interactions || {};
    const ls = r.life_stage || {};
    const isV2 = chart.method === "bazi_v2";
    return (
      <div className="pt-2 mt-1 border-t space-y-2" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>
          {isV2 ? "八字精算专项 · 格局/用神/神煞/身强/大运/流年" : "八字专项 · 身强 / 当前大运 / 流年 / 12 长生"}
        </div>
        {isV2 && r.pattern && (
          <div>
            格局: <span style={{ color: COLOR.goldBright }}>{r.pattern.pattern}</span>
            {r.pattern.description && <span className="opacity-70"> — {r.pattern.description}</span>}
          </div>
        )}
        {isV2 && r.yong_shen && (
          <div>用神: <span style={{ color: COLOR.jade }}>{r.yong_shen.rationale}</span></div>
        )}
        {isV2 && typeof r.yong_shen_quality?.score === "number" && (
          <div>用神质量: <span style={{ color: COLOR.ink }}>{r.yong_shen_quality.score}/100 ({r.yong_shen_quality.level})</span></div>
        )}
        {isV2 && r.shensha?.summary?.notable?.length > 0 && (
          <div>关键神煞: <span style={{ color: COLOR.gold }}>{r.shensha.summary.notable.join("、")}</span></div>
        )}
        {isV2 && r.element_flow?.interpretation && (
          <div>五行流转: <span className="opacity-80">{r.element_flow.interpretation}</span></div>
        )}
        {typeof score === "number" && (
          <div>日主身强评分: <span style={{ color: COLOR.ink }}>{score}</span> / 100</div>
        )}
        {r.strength_basis && (
          <div className="text-[10px]">同党 = 比劫 {r.strength_basis.peer_count ?? 0} + 印星 {r.strength_basis.resource_count ?? 0}; 异党 = 食伤 {r.strength_basis.output_count ?? 0} / 官杀 {r.strength_basis.official_count ?? 0} / 财 {r.strength_basis.wealth_count ?? 0}; 月令分 {r.strength_basis.month_strength}</div>
        )}
        {cl.decade_ganzhi && (
          <div>当前大运: <span style={{ color: COLOR.ink }}>{cl.decade_ganzhi}</span> ({cl.decade_from}-{cl.decade_to}, 虚岁 {cl.age}) · 阶段分 {cl.decade_score}</div>
        )}
        {cl.annual_label && (
          <div>流年: <span style={{ color: COLOR.ink }}>{cl.annual_label}</span></div>
        )}
        {Array.isArray(ai.interactions) && ai.interactions.length > 0 && (
          <div>
            <div>流年 {ai.ganzhi} 与原局互动:</div>
            <ul className="list-disc pl-5 space-y-0.5">
              {ai.interactions.map((it: any, i: number) => (
                <li key={i}>{it.note} <span className="opacity-70">({it.kind_zh})</span></li>
              ))}
            </ul>
          </div>
        )}
        {Array.isArray(ls.stages) && ls.stages.length > 0 && (
          <div>
            <div>12 长生 ({ls.day_master} {ls.is_yang ? "阳顺" : "阴逆"}):</div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 mt-1">
              {ls.stages.map((s: any) => (
                <div key={s.pillar} className="px-2 py-1 rounded" style={{ background: COLOR.bgDeep, border: `1px solid ${COLOR.lineSoft}` }}>
                  <div className="text-[10px] opacity-70">{s.pillar} · {s.pillar_ganzhi}</div>
                  <div style={{ color: COLOR.ink }}>{s.zhi} → {s.stage}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }
  if (chart.method === "ziwei") {
    const h = r.horoscope || {};
    const periods = ["decadal", "yearly", "monthly", "daily", "hourly"] as const;
    return (
      <div className="pt-2 mt-1 border-t space-y-2" style={{ borderColor: COLOR.lineSoft }}>
        <div className="flex items-center gap-2 flex-wrap font-semibold" style={{ color: COLOR.goldBright }}>
          紫微专项 · 12 宫 + 限运四化
          {r.fallback && <span className="tag" style={{ borderColor: COLOR.danger, color: COLOR.danger }}>fallback</span>}
        </div>
        {r.fallback_reason && <div className="text-[10px] opacity-80">fallback 原因: {r.fallback_reason}</div>}
        <div className="text-[10px] opacity-80">本命 12 宫 × {r.palaces?.length || 0}; 五行局 {r.five_elements_class || "-"}</div>
        {periods.map((p) => {
          const item = h[p];
          if (!item) return null;
          const scope = p === "decadal" ? "大限" : p === "yearly" ? "流年" : p === "monthly" ? "流月" : p === "daily" ? "流日" : "流时";
          return (
            <div key={p} className="text-[11px]">
              <span className="opacity-80">{scope}:</span>{" "}
              <span style={{ color: COLOR.ink }}>{item.ganzhi}</span>{" "}
              {Array.isArray(item.mutagen) && item.mutagen.length === 4 && (
                <span style={{ color: COLOR.gold }}>四化: {item.mutagen.join(" / ")}</span>
              )}
            </div>
          );
        })}
      </div>
    );
  }
  if (chart.method === "tarot") {
    const rec = r.spread_recommendation;
    return (
      <div className="pt-2 mt-1 border-t space-y-2" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>塔罗专项 · 牌位模板 + 牌阵推荐</div>
        {rec && (
          <div className="text-[10px] opacity-80">牌阵推荐: subject={rec.subject}, time_budget={rec.time_budget} → {rec.spread_name} ({rec.position_count} 张)</div>
        )}
        {Array.isArray(r.cards) && r.cards.length > 0 && (
          <div className="space-y-1">
            {r.cards.map((c: any, i: number) => (
              <div key={i} className="text-[11px]">
                <span style={{ color: COLOR.gold }}>{c.position}</span>{" "}
                <span style={{ color: COLOR.ink }}>{c.name}</span>{" "}
                <span className="opacity-70">{c.orient}</span>
                {c.position_template_filled && (
                  <div className="opacity-80 leading-snug pl-2 border-l-2" style={{ borderColor: COLOR.lineSoft }}>{c.position_template_filled}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  if (chart.method === "liuyao") {
    return (
      <div className="pt-2 mt-1 border-t space-y-1" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>六爻专项 · 用神依据</div>
        {r.using_god && <div>用神: <span style={{ color: COLOR.ink }}>{r.using_god}</span></div>}
        {r.using_god_basis && <div className="text-[10px] opacity-80">依据: {r.using_god_basis}</div>}
        {Array.isArray(r.hex_lines) && (
          <div className="text-[10px] opacity-80">
            纳甲: {r.hex_lines.map((h: any) => `${h.pos}${h.yang ? "—" : "--"}(${h.gan_zhi})`).join(" ")}
          </div>
        )}
      </div>
    );
  }
  if (chart.method === "qimen") {
    return (
      <div className="pt-2 mt-1 border-t space-y-1" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>奇门专项 · 旬首 + 拆补/置闰</div>
        {r.xun_shou && <div>旬首: {r.xun_shou}</div>}
        {r.config && (
          <div className="text-[10px] opacity-80">
            排盘: {r.config.layout} · 起法: {r.config.method} · {r.config.fallback_to} · 真太阳时: {r.config.true_solar_time}
          </div>
        )}
        {r.zhifu && (
          <div className="text-[10px] opacity-80">
            值符: {r.zhifu.star}(落 {r.zhifu.star_gong}) · 值使: {r.zhifu.door}(落 {r.zhifu.door_gong}) · 时干: {r.zhifu.gan}
          </div>
        )}
      </div>
    );
  }
  if (chart.method === "xuankong") {
    return (
      <div className="pt-2 mt-1 border-t space-y-1" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>玄空专项 · 24 山合法性 + 替卦预留</div>
        <div className="text-[10px] opacity-80">
          坐山 {r.sitting} 合法: {String(r.sitting_valid)} · 向山 {r.facing} 合法: {String(r.facing_valid)}
        </div>
        {r.ti_gua_reserved && (
          <div className="text-[10px] opacity-80">替卦: {r.ti_gua_reserved.enabled ? "已启用" : r.ti_gua_reserved.note}</div>
        )}
      </div>
    );
  }
  if (chart.method === "meihua") {
    return (
      <div className="pt-2 mt-1 border-t space-y-1" style={{ borderColor: COLOR.lineSoft }}>
        <div className="font-semibold" style={{ color: COLOR.goldBright }}>梅花专项 · 八卦五行表</div>
        {r.trigram_table && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[10px]">
            {Object.entries(r.trigram_table).map(([name, t]: [string, any]) => (
              <div key={name} className="px-2 py-1 rounded" style={{ background: COLOR.bgDeep, border: `1px solid ${COLOR.lineSoft}` }}>
                <div style={{ color: COLOR.ink }}>{name} · {t.wuxing}</div>
                <div className="opacity-70">{t.nature}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
  return null;
}

function ShareCardModal({ card, copied, onClose, onCopy }: {
  card: ShareCard; copied: boolean; onClose: () => void; onCopy: () => void;
}) {
  const { t, lang } = useI18n();
  return (
    <div
      role="dialog" aria-modal="true" aria-label={t("result.share")}
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" }}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="card-raised card-glow"
        style={{ maxWidth: 480, width: "100%", maxHeight: "85vh", overflow: "auto" }}>
        <div className="flex items-center justify-between mb-3">
          <div className="text-base font-display" style={{ color: COLOR.goldBright }}>{t("result.share")}</div>
          <button className="btn-ghost text-xs" onClick={onClose}>{t("action.close")}</button>
        </div>
        <div className="text-sm font-semibold mb-2" style={{ color: COLOR.ink }}>{card.title}</div>
        <div className="text-xs mb-3" style={{ color: COLOR.muted }}>{t("result.basis.method")}: {card.methods.join(" / ")}</div>
        <div className="text-sm leading-relaxed mb-3" style={{ color: COLOR.inkSoft }}>{card.summary}</div>
        {card.basis.length > 0 && (
          <div className="mb-3">
            <div className="text-xs font-semibold mb-1" style={{ color: COLOR.gold }}>{lang === "zh" ? "盘面依据" : "Chart Basis"}</div>
            <ul className="text-xs space-y-0.5" style={{ color: COLOR.muted }}>
              {card.basis.map((b, i) => <li key={i}>· {b}</li>)}
            </ul>
          </div>
        )}
        {card.cards.length > 0 && (
          <div className="mb-3">
            <div className="text-xs font-semibold mb-1" style={{ color: COLOR.gold }}>{lang === "zh" ? "牌面" : "Cards"}</div>
            <ul className="text-xs space-y-0.5" style={{ color: COLOR.inkSoft }}>
              {card.cards.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        )}
        <div className="mb-3">
          <div className="text-xs font-semibold mb-1" style={{ color: COLOR.gold }}>建议</div>
          <ol className="text-xs space-y-0.5 list-decimal pl-4" style={{ color: COLOR.inkSoft }}>
            {card.suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ol>
        </div>
        <div className="text-[10px] mb-3" style={{ color: COLOR.muted }}>{card.footer}</div>
        <div className="flex justify-end gap-2">
          <button className="btn-primary text-xs" onClick={onCopy}>{copied ? "已复制 ✓" : "复制全文"}</button>
        </div>
      </div>
    </div>
  );
}
