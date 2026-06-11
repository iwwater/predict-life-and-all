// 首页:「排盘台」— 一屏即用的排盘入口,非落地页
// 依据:《前端视觉重设计规范》§3
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMethods, fetchDaily, type DailyPayload } from "../lib/api";
import type { MethodMeta } from "../lib/types";
import { SchoolChip } from "../components/ui";
import { METHOD_PLAIN, SUBJECTS } from "../lib/method-info";
import { useHistory } from "../store/history";
import type { HistoryEntry } from "../store/history";
import { useI18n } from "../lib/i18n";

const SUBJECT_LABEL: Record<string, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<string, string>,
);

export function Home() {
  const { t, lang } = useI18n();
  const [methods, setMethods] = useState<MethodMeta[]>([]);
  const [daily, setDaily] = useState<DailyPayload | null>(null);
  const items = useHistory((s) => s.items);
  const recent3 = items.slice(0, 3);

  useEffect(() => {
    fetchMethods().then(setMethods).catch(() => setMethods([]));
    const last = items.find((it) => it.birth?.year);
    const birth = last
      ? {
          year: last.birth.year, month: last.birth.month, day: last.birth.day,
          hour: last.birth.hour, minute: last.birth.minute,
          gender: last.birth.gender, calendar: "gregorian" as const,
          lat: last.birth.lat ?? null, lng: last.birth.lng ?? null,
          tz: last.birth.tz, is_leap_month: false,
        }
      : undefined;
    fetchDaily(undefined, birth).then(setDaily).catch(() => setDaily(null));
  }, [items]);

  const eastMethods = methods.filter((m) => m.school === "east");
  const westMethods = methods.filter((m) => m.school === "west");

  return (
    <div className="space-y-8">
      {/* 今日摘要 — 纸墨风格 */}
      <DailyTeaser payload={daily} hasBirth={items.some((it) => it.birth?.year)} />

      {/* 排盘台主体 */}
      <section className="paper-frame relative">
        <div className="paper-compass-bg" aria-hidden />
        <div className="relative z-10">
          {/* 标题 */}
          <h1 className="paper-title mb-5">
            <span className="stamp" />
            <span>排盘台</span>
            <span className="sub">{t("app.tagline")}</span>
          </h1>

          <div className="paper-main-grid">
            {/* 左:五术导航 + 快捷入口 */}
            <div className="flex gap-4 min-w-0">
              {/* 五术竖题签 */}
              <div className="paper-vertical shrink-0" style={{ fontSize: "0.95rem" }}>
                命 · 卜 · 相 · 山 · 医
              </div>
              {/* 快捷任务 */}
              <div className="flex-1 min-w-0 space-y-2">
                <div className="paper-eyebrow">问事</div>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { key: "self_life", label: lang === "zh" ? "本命格局" : "Life Chart", to: "/cast?subject=self_life" },
                    { key: "career", label: lang === "zh" ? "事业工作" : "Career", to: "/cast?subject=career" },
                    { key: "relationship", label: lang === "zh" ? "感情姻缘" : "Love", to: "/cast?subject=relationship" },
                    { key: "wealth", label: lang === "zh" ? "财运" : "Wealth", to: "/cast?subject=wealth" },
                    { key: "decision", label: lang === "zh" ? "重大决策" : "Decision", to: "/cast?subject=decision" },
                    { key: "annual_luck", label: lang === "zh" ? "年度运势" : "Annual", to: "/cast?subject=annual_luck" },
                    { key: "home_fengshui", label: lang === "zh" ? "风水调理" : "Feng Shui", to: "/cast?subject=home_fengshui" },
                    { key: "tarot_guidance", label: lang === "zh" ? "塔罗指引" : "Tarot", to: "/cast?subject=tarot_guidance" },
                  ].map((t) => (
                    <Link
                      key={t.key}
                      to={t.to}
                      className="paper-grid-cell"
                      style={{ padding: "0.4rem 0.6rem", textDecoration: "none", display: "block" }}
                    >
                      <span style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.82rem", color: "var(--ink)", fontWeight: 500 }}>
                        {t.label}
                      </span>
                    </Link>
                  ))}
                </div>

                {/* 关键入口 */}
                <div className="paper-eyebrow" style={{ marginTop: "0.75rem" }}>合参</div>
                <div className="flex flex-wrap gap-1.5">
                  <Link to="/reading" className="paper-btn" style={{ fontSize: "0.8rem" }}>
                    12法合参
                  </Link>
                  <Link to="/compatibility" className="paper-btn-ghost" style={{ fontSize: "0.8rem" }}>
                    {t("nav.compatibility")}
                  </Link>
                  <Link to="/daily" className="paper-btn-ghost" style={{ fontSize: "0.8rem" }}>
                    {t("nav.daily")}
                  </Link>
                </div>
              </div>
            </div>

            {/* 右:罗盘装饰 + 快捷信息 */}
            <div className="min-w-0 space-y-3" style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
              {/* 罗盘环(纯装饰,极淡) */}
              <svg aria-hidden width="180" height="180" viewBox="0 0 200 200" style={{ opacity: 0.12 }}>
                <circle cx="100" cy="100" r="94" fill="none" stroke="var(--cinnabar)" strokeWidth="0.8" />
                <circle cx="100" cy="100" r="78" fill="none" stroke="var(--cinnabar)" strokeWidth="0.6" strokeDasharray="3 5" />
                <circle cx="100" cy="100" r="62" fill="none" stroke="var(--cinnabar)" strokeWidth="0.5" />
                <circle cx="100" cy="100" r="46" fill="none" stroke="var(--cinnabar)" strokeWidth="0.4" />
                <circle cx="100" cy="100" r="30" fill="none" stroke="var(--cinnabar)" strokeWidth="0.4" />
                <circle cx="100" cy="100" r="14" fill="none" stroke="var(--cinnabar)" strokeWidth="0.5" />
                {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => {
                  const rad = (deg * Math.PI) / 180;
                  const x1 = 100 + 85 * Math.cos(rad);
                  const y1 = 100 + 85 * Math.sin(rad);
                  const x2 = 100 + 95 * Math.cos(rad);
                  const y2 = 100 + 95 * Math.sin(rad);
                  return <line key={deg} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--cinnabar)" strokeWidth="0.6" />;
                })}
                {["子", "午", "卯", "酉"].map((z, i) => {
                  const deg = i * 90 - 90;
                  const rad = (deg * Math.PI) / 180;
                  const x = 100 + 70 * Math.cos(rad);
                  const y = 100 + 70 * Math.sin(rad);
                  return (
                    <text key={z} x={x} y={y} textAnchor="middle" dominantBaseline="central"
                      fontFamily="'Noto Serif SC', serif" fontSize="14" fill="var(--cinnabar)" fontWeight="700">
                      {z}
                    </text>
                  );
                })}
              </svg>
              <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.72rem", color: "var(--ink-soft)", letterSpacing: "0.2em", textAlign: "center" }}>
                子午卯酉<br/>天地定位
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 近期排盘 */}
      {recent3.length > 0 && (
        <section>
          <div className="paper-eyebrow" style={{ marginBottom: "0.5rem" }}>
            {lang === "zh" ? "近期排盘" : "Recent Casts"}
          </div>
          <div className="space-y-1">
            {recent3.map((it) => (
              <div key={it.id} className="paper-grid-cell flex items-center justify-between gap-2 flex-wrap" style={{ padding: "0.5rem 0.8rem" }}>
                <div className="flex items-center gap-2 min-w-0 flex-wrap">
                  <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>
                    {SUBJECT_LABEL[it.subject || ""] || it.subject || (lang === "zh" ? "未分类" : "—")}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
                    {it.question || it.methods.join(" / ")}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "var(--rule)" }}>
                    {new Date(it.ts).toLocaleString()}
                  </span>
                </div>
                <Link
                  to={`/cast?fromHistory=${encodeURIComponent(it.id)}`}
                  className="paper-btn-ghost"
                  style={{ fontSize: "0.7rem", padding: "0.2rem 0.6rem" }}
                >
                  {t("history.continue")}
                </Link>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="paper-hr" />

      {/* 术数总览 */}
      <MethodOverview eastMethods={eastMethods} westMethods={westMethods} />

      {/* 公开案例已下架 — 法律合规:真实名人生辰/命运论断涉及个人信息保护法与民法典人格权 */}

      {/* 合规说明由全局 Footer 统一承载，此处不再重复 */}
    </div>
  );
}

/* ── 子组件 ── */

function DailyTeaser({ payload, hasBirth }: { payload: DailyPayload | null; hasBirth: boolean }) {
  const { t, lang } = useI18n();
  if (!payload) return null;
  const td = payload.today;
  const it = payload.interaction;
  return (
    <section className="paper-grid-cell" style={{ padding: "0.7rem 1rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
      <div className="min-w-0 flex-1">
        <div className="paper-eyebrow">
          {t("home.daily.label")} · {payload.date}
        </div>
        <div style={{ fontSize: "0.92rem", color: "var(--ink)", fontFamily: "'Noto Serif SC', serif", marginTop: "0.2rem" }}>
          {td.ganzhi_day} {t("cast.birth.day")} · {td.day_wuxing} · {td.tarot_card.name}{" "}
          <span style={{
            fontSize: "0.75rem",
            color: td.tarot_card.orient === "正位" ? "var(--verdigris)" : "var(--ink-soft)",
          }}>
            ({td.tarot_card.orient})
          </span>
        </div>
        {it && (
          <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "0.2rem" }}>
            {it.label} · {it.action}
          </div>
        )}
        {!hasBirth && (
          <div style={{ fontSize: "0.68rem", color: "var(--rule)", marginTop: "0.15rem" }}>
            {t("daily.noBirth")}
          </div>
        )}
      </div>
      <Link to="/daily" className="paper-btn" style={{ fontSize: "0.78rem", flexShrink: 0 }}>
        {t("daily.title")} →
      </Link>
    </section>
  );
}

function MethodOverview({ eastMethods, westMethods }: { eastMethods: MethodMeta[]; westMethods: MethodMeta[] }) {
  const { t, lang } = useI18n();
  const all = [...eastMethods, ...westMethods];
  if (all.length === 0) {
    return (
      <div className="paper-empty">
        <span className="paper-pulse" style={{ marginRight: "0.5rem" }} />
        {t("action.loading")}
      </div>
    );
  }
  return (
    <section>
      <div className="paper-eyebrow" style={{ marginBottom: "0.5rem" }}>
        {lang === "zh" ? "十四术数" : "Fourteen Arts"}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {all.map((m) => {
          const plain = METHOD_PLAIN[m.id as keyof typeof METHOD_PLAIN];
          return (
            <Link
              key={m.id}
              to={`/m/${m.id}`}
              className="paper-grid-cell"
              style={{ textDecoration: "none", display: "block" }}
            >
              <div className="flex items-center justify-between mb-0.5">
                <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, fontSize: "0.88rem", color: "var(--ink)" }}>
                  {m.name_zh}
                </span>
                <SchoolChip school={m.school} />
              </div>
              <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
                {m.name_en}
              </div>
              {plain?.tagline && (
                <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.3rem", letterSpacing: "0.03em" }}>
                  {plain.tagline}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </section>
  );
}
