// 首页:东西方术数展示 + 合盘 CTA + 任务入口 + 华美装饰
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMethods, fetchCases, fetchDaily, type DailyPayload } from "../lib/api";
import type { MethodMeta, Case } from "../lib/types";
import { COLOR, SchoolChip } from "../components/ui";
import { METHOD_PLAIN } from "../lib/method-info";
import { useHistory } from "../store/history";
import { SUBJECTS } from "../lib/method-info";
import type { HistoryEntry } from "../store/history";
import { Reveal, SubjectGlyph, GoldDust, OrnamentalDivider } from "../components/Interactions";
import { BaGuaRing, WuXingRing, ZodiacRing, FlowerOfLife, PlanetSymbols, AuspiciousClouds } from "../components/MysticElements";
import { useI18n } from "../lib/i18n";

const SUBJECT_LABEL: Record<string, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<string, string>,
);

export function Home() {
  const { t, lang } = useI18n();
  const [methods, setMethods] = useState<MethodMeta[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [daily, setDaily] = useState<DailyPayload | null>(null);
  const items = useHistory((s) => s.items);
  const recent3 = items.slice(0, 3);

  useEffect(() => {
    fetchMethods().then(setMethods).catch(() => setMethods([]));
    fetchCases().then(setCases).catch(() => setCases([]));
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
    <div className="space-y-12">
      {/* 今日摘要 */}
      <DailyTeaser payload={daily} hasBirth={items.some((it) => it.birth?.year)} />

      {/* 任务型入口 */}
      <TaskEntries recent={recent3} />

      {/* Hero — 华美版 */}
      <Reveal>
        <section
          className="relative overflow-hidden rounded-2xl border p-8 sm:p-12 card-glow card-highlight"
          style={{
            background: `linear-gradient(150deg,
              rgba(22,27,34,0.95) 0%,
              rgba(12,16,24,0.98) 30%,
              rgba(8,10,15,1) 70%,
              rgba(22,27,34,0.95) 100%)`,
            borderColor: COLOR.line,
          }}>
          {/* 金尘粒子 */}
          <GoldDust count={18} />

          {/* 右上的大型装饰: 多层仪象圈 + 慢旋 */}
          <ConstellationDecor />
          {/* 左下的八卦环 */}
          <div className="absolute -left-16 -bottom-16 opacity-[0.08] pointer-events-none">
            <BaGuaRing size={280} spinning />
          </div>

          {/* 顶部光晕 */}
          <div
            className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] h-[200px] pointer-events-none"
            style={{
              background: `radial-gradient(ellipse at center, rgba(201,162,75,0.07) 0%, transparent 70%)`,
            }}
          />

          <div className="relative max-w-2xl">
            {/* 小徽章 */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] uppercase tracking-[0.3em] mb-4"
              style={{
                background: "rgba(201,162,75,0.08)",
                border: `1px solid ${COLOR.goldDim}40`,
                color: COLOR.gold,
              }}>
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{ background: COLOR.goldBright, boxShadow: `0 0 6px ${COLOR.gold}` }}
              />
              Mystic Hub · {t("app.name")}
            </div>

            <h1 className="text-3xl sm:text-4xl mt-3 leading-tight text-shimmer" style={{ color: COLOR.ink }}>
              {t("home.hero.title")}<br />
              <span className="text-2xl sm:text-3xl" style={{ color: COLOR.inkSoft }}>
                {t("home.hero.subtitle")}
              </span>
            </h1>

            <p className="mt-5 text-sm leading-relaxed max-w-lg" style={{ color: COLOR.inkSoft }}>
              {t("home.hero.desc")}
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/reading" className="btn-primary gold-sweep-host text-sm px-6 py-3">
                🔮 开始提问（12 法合参）
              </Link>
              <Link to="/compatibility" className="btn-ghost tap text-sm px-5 py-3"
                style={{ borderColor: COLOR.goldDim, color: COLOR.goldBright }}>
                {t("home.cta.compat")}
              </Link>
              <Link to="/about" className="btn-ghost text-sm">{t("home.cta.about")}</Link>
            </div>
          </div>
        </section>
      </Reveal>

      {/* === 合盘 CTA — 华丽版 === */}
      <Reveal delayMs={100}>
        <Link to="/compatibility"
          className="block rounded-2xl border p-6 sm:p-8 lift-on-hover tap relative overflow-hidden group card-highlight"
          style={{
            background: `linear-gradient(135deg,
              rgba(201,162,75,0.10) 0%,
              rgba(201,162,75,0.03) 40%,
              rgba(91,141,239,0.06) 100%)`,
            borderColor: COLOR.goldDim,
          }}>
          {/* 背景装饰 */}
          <div className="absolute -right-8 -top-8 w-48 h-48 pointer-events-none opacity-15 group-hover:opacity-25 transition-opacity"
            style={{
              background: `radial-gradient(circle, ${COLOR.goldBright} 0%, transparent 70%)`,
            }}
          />
          {/* 神圣几何 - 生命之花 */}
          <div className="absolute -left-12 bottom-0 opacity-[0.06] group-hover:opacity-[0.12] transition-opacity pointer-events-none">
            <FlowerOfLife size={220} />
          </div>
          <div className="absolute right-8 top-1/2 -translate-y-1/2 text-6xl opacity-15 group-hover:opacity-35 transition-all duration-500 group-hover:scale-110">
            💞
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              <span
                className="inline-flex items-center justify-center w-10 h-10 rounded-xl text-xl"
                style={{ background: `${COLOR.gold}15`, border: `1px solid ${COLOR.goldDim}50` }}
              >
                💞
              </span>
              <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{t("home.compat.title")}</h2>
              <span className="tag tag-east text-[10px]" style={{ borderColor: `${COLOR.jade}60` }}>{t("compat.bazi")}</span>
              <span className="tag tag-west text-[10px]" style={{ borderColor: `${COLOR.azure}60` }}>{t("compat.western")}</span>
            </div>

            <p className="text-sm max-w-xl leading-relaxed" style={{ color: COLOR.inkSoft }}>
              {t("home.compat.desc")}
            </p>

            <div className="mt-4 inline-flex items-center gap-2 text-sm font-semibold group-hover:gap-3 transition-all"
              style={{ color: COLOR.goldBright }}>
              {t("home.compat.action")}
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </div>
          </div>
        </Link>
      </Reveal>

      {/* 装饰分段线 */}
      <OrnamentalDivider />

      {/* === 东方命理 === */}
      <section className="relative">
        {/* 五行环背景装饰 */}
        <div className="absolute right-4 top-0 opacity-[0.06] pointer-events-none">
          <WuXingRing size={160} />
        </div>
        <SectionHeader
          title={t("section.east")}
          subtitle="Bazi · Ziwei · Qimen · Liuren · Liuyao · Meihua · ChengGu · TieBan"
          color={COLOR.jade}
          icon="☯️"
        />
        <MethodGrid methods={eastMethods} stagger accentColor={COLOR.jade} />
      </section>

      {/* === 西方占卜 === */}
      <section className="relative">
        {/* 十二星座环背景装饰 */}
        <div className="absolute right-4 top-0 opacity-[0.06] pointer-events-none">
          <ZodiacRing size={160} />
        </div>
        <SectionHeader
          title={t("section.west")}
          subtitle="Astrology · Tarot · Lenormand · Numerology · Vedic"
          color={COLOR.azure}
          icon="✨"
        />
        <MethodGrid methods={westMethods} stagger accentColor={COLOR.azure} />
      </section>

      <OrnamentalDivider />

      {/* 案例 */}
      {cases.length > 0 && (
        <section>
          <h2 className="text-lg mb-4 font-display" style={{ color: COLOR.goldBright }}>📖 {lang === "zh" ? "公开案例" : "Public Cases"}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 reveal-stagger">
            {cases.map((c) => (
              <Link key={c.id} to={`/cast?fromCase=${c.id}`}
                className="card card-highlight lift-on-hover text-xs tap">
                <div className="font-semibold" style={{ color: COLOR.ink }}>{c.name_zh}</div>
                <div className="mt-1" style={{ color: COLOR.muted }}>{c.year}-{c.month}-{c.day}</div>
                <div className="mt-1 truncate" style={{ color: COLOR.inkSoft }}>{c.note}</div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 合规 */}
      <section
        className="rounded-xl border p-5 text-xs space-y-1.5"
        style={{
          background: "rgba(22,27,34,0.3)",
          borderColor: COLOR.lineSoft,
          color: COLOR.muted,
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span style={{ color: COLOR.jade }}>◆</span>
          <span style={{ color: COLOR.inkSoft, fontWeight: 600 }}>{t("home.privacy")}</span>
        </div>
        <div>{t("app.compliance")}</div>
        <div>{lang === "zh" ? "你的 LLM API Key 仅存在浏览器本地；解读时浏览器直连 provider，Key 不出前端。" : "Your LLM API key stays in your browser — sent directly to the provider, never to our backend."}</div>
      </section>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────

function SectionHeader({ title, subtitle, color, icon }: {
  title: string;
  subtitle: string;
  color: string;
  icon: string;
}) {
  return (
    <div className="flex items-center gap-4 mb-5">
      <span
        className="inline-flex items-center justify-center w-10 h-10 rounded-xl text-xl"
        style={{
          background: `linear-gradient(135deg, ${color}18 0%, ${color}08 100%)`,
          border: `1px solid ${color}30`,
          boxShadow: `0 0 16px ${color}10`,
        }}
      >
        {icon}
      </span>
      <div>
        <h2 className="text-xl font-display" style={{ color }}>{title}</h2>
        <p className="text-[10px] mt-1 tracking-wide" style={{ color: COLOR.muted }}>{subtitle}</p>
      </div>
    </div>
  );
}

function MethodGrid({ methods, stagger, accentColor }: {
  methods: MethodMeta[];
  stagger?: boolean;
  accentColor?: string;
}) {
  const { t, lang } = useI18n();
  if (methods.length === 0) {
    return (
      <div className="card text-center text-xs py-8" style={{ color: COLOR.muted }}>
        <span className="inline-block w-4 h-4 rounded-full border-2 border-dashed spin-slow"
          style={{ borderColor: COLOR.line }} />
        <div className="mt-2">{t("action.loading")}</div>
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 ${stagger ? "reveal-stagger" : ""}`}>
      {methods.map((m) => {
        const info = METHOD_PLAIN[m.id as keyof typeof METHOD_PLAIN];
        return (
          <Link key={m.id} to={`/cast?methods=${m.id}`}
            className="card card-highlight lift-on-hover tap relative overflow-hidden group">
            {/* 卡片顶部微光 (对应东方/西方色) */}
            <div
              className="absolute top-0 left-3 right-3 h-px opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
              style={{
                background: `linear-gradient(90deg, transparent, ${accentColor || COLOR.gold}60, transparent)`,
              }}
            />
            <div className="flex items-center justify-between mb-1.5">
              <h3 className="text-base font-display group-hover:text-shimmer-fast transition-colors" style={{ color: COLOR.ink }}>
                {m.name_zh}
              </h3>
              <SchoolChip school={m.school} />
            </div>
            <div className="text-[10px]" style={{ color: COLOR.muted }}>{m.name_en}</div>
            {info?.tagline && (
              <div className="text-xs mt-2 leading-snug" style={{ color: COLOR.inkSoft }}>
                {info.tagline}
              </div>
            )}
            {info?.bestFor && (
              <div className="text-[10px] mt-1.5 leading-snug" style={{ color: COLOR.goldDim }}>
                {lang === "zh" ? "擅长" : "Best for"}: {info.bestFor}
              </div>
            )}
            <div className="text-[10px] mt-2 truncate opacity-0 group-hover:opacity-100 transition-all duration-300"
              style={{ color: accentColor || COLOR.goldDim }}>
              {m.engine}
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function DailyTeaser({ payload, hasBirth }: { payload: DailyPayload | null; hasBirth: boolean }) {
  const { t } = useI18n();
  if (!payload) return null;
  const td = payload.today;
  const it = payload.interaction;
  return (
    <Reveal>
      <section
        className="card-raised card-highlight flex items-center justify-between gap-4 flex-wrap p-4 sm:p-5 relative overflow-hidden"
        style={{
          background: `linear-gradient(120deg, rgba(201,162,75,0.10) 0%, rgba(22,27,34,0.6) 60%)`,
          borderColor: COLOR.line,
        }}>
        {/* 装饰波浪线 */}
        <svg aria-hidden className="absolute right-0 top-0 h-full w-32 opacity-25 pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path d="M0,30 Q50,10 100,40" stroke="var(--gold-dim)" strokeWidth="0.5" fill="none" />
          <path d="M0,55 Q50,30 100,65" stroke="var(--gold-dim)" strokeWidth="0.4" fill="none" />
          <path d="M0,80 Q50,55 100,90" stroke="var(--gold-dim)" strokeWidth="0.3" fill="none" />
        </svg>
        <div className="min-w-0 flex-1 relative z-10">
          <div className="text-[10px] uppercase tracking-[0.4em] flex items-center gap-2" style={{ color: COLOR.gold }}>
            <span className="inline-block w-1 h-1 rounded-full" style={{ background: COLOR.goldBright }} />
            {t("home.daily.label")} · {payload.date}
          </div>
          <div className="text-base sm:text-lg mt-1 font-display" style={{ color: COLOR.ink }}>
            {td.ganzhi_day} {t("cast.birth.day")} · {td.day_wuxing} · {td.tarot_card.name}{" "}
            <span className="text-xs" style={{
              color: td.tarot_card.orient === "正位" ? COLOR.jade : COLOR.muted,
            }}>({td.tarot_card.orient})</span>
          </div>
          {it && (
            <div className="text-xs mt-1.5" style={{ color: COLOR.inkSoft }}>
              {it.label} · {it.action}
            </div>
          )}
          {!hasBirth && (
            <div className="text-[10px] mt-1" style={{ color: COLOR.muted }}>
              {t("daily.noBirth")}
            </div>
          )}
        </div>
        <Link to="/daily" className="btn-primary text-xs shrink-0 relative z-10 gold-sweep-host">
          {t("daily.title")} →
        </Link>
      </section>
    </Reveal>
  );
}

function TaskEntries({ recent }: { recent: HistoryEntry[] }) {
  const { t, lang } = useI18n();
  const tasks: Array<{
    key: string; label: string; desc: string; to: string; tone: string;
    glyph: "self" | "annual" | "decision" | "relationship" | "career" | "wealth" | "lost" | "home" | "tarot" | "lenormand";
  }> = [
    { key: "daily", label: t("home.daily.label"), desc: t("home.ask.title"), to: "/daily", tone: COLOR.goldBright, glyph: "annual" },
    { key: "self_life", label: lang === "zh" ? "本命" : "Self", desc: "Life Chart Core", to: "/cast?subject=self_life", tone: COLOR.gold, glyph: "self" },
    { key: "relationship", label: lang === "zh" ? "关系" : "Love", desc: "Relationship dynamics", to: "/cast?subject=relationship", tone: COLOR.jade, glyph: "relationship" },
    { key: "career", label: lang === "zh" ? "事业" : "Career", desc: "Career path & opportunities", to: "/cast?subject=career", tone: COLOR.azure, glyph: "career" },
    { key: "decision", label: lang === "zh" ? "决策" : "Decide", desc: "Should I or shouldn't I?", to: "/cast?subject=decision", tone: COLOR.goldBright, glyph: "decision" },
    { key: "home_fengshui", label: lang === "zh" ? "住宅" : "Home", desc: "Feng Shui house reading", to: "/cast?subject=home_fengshui", tone: COLOR.jade, glyph: "home" },
  ];

  return (
    <section>
      <div className="flex items-center gap-3 mb-3">
        <h2 className="text-lg font-display" style={{ color: COLOR.goldBright }}>{t("home.ask.title")}</h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 reveal-stagger">
        {tasks.map((t) => (
          <Link key={t.key} to={t.to}
            className="card card-highlight lift-on-hover tap relative overflow-hidden group">
            <div className="flex items-start justify-between mb-1.5">
              <SubjectGlyph glyph={t.glyph} color={t.tone} size={24} />
              <span className="text-[9px] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:translate-x-0.5"
                style={{ color: t.tone }}>→</span>
            </div>
            <div className="text-sm font-display" style={{ color: t.tone }}>{t.label}</div>
            <div className="text-[10px] mt-1 leading-snug" style={{ color: COLOR.muted }}>{t.desc}</div>
          </Link>
        ))}
      </div>

      {recent.length > 0 && (
        <div className="mt-5">
          <div className="flex items-center gap-2 text-xs mb-3" style={{ color: COLOR.muted }}>
            <span style={{ color: COLOR.goldDim }}>◆</span>
            {t("home.recent")}
          </div>
          <ul className="space-y-1.5 reveal-stagger">
            {recent.map((it) => (
              <li key={it.id}
                className="card-raised card-highlight flex items-center justify-between gap-2 text-xs lift-on-hover">
                <div className="min-w-0 flex-1 truncate" style={{ color: COLOR.inkSoft }}>
                  <span className="tag mr-2" style={{
                    color: COLOR.goldBright,
                    borderColor: `${COLOR.goldDim}60`,
                  }}>
                  {SUBJECT_LABEL[it.subject || ""] || it.subject || (lang === "zh" ? "未分类" : "Uncategorized")}
                  </span>
                  {it.question || it.methods.join(" / ")}
                  <span className="ml-2" style={{ color: COLOR.muted }}>
                    {new Date(it.ts).toLocaleString()}
                  </span>
                </div>
                <Link to={`/cast?fromHistory=${encodeURIComponent(it.id)}`}
                  className="btn-ghost text-[10px] shrink-0 tap"
                  style={{ borderColor: `${COLOR.goldDim}40` }}>
                  {t("history.continue")}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function ConstellationDecor() {
  return (
    <>
      {/* 大型多层仪象圈 */}
      <svg
        aria-hidden
        className="absolute -right-20 -top-20 w-[420px] h-[420px] opacity-35 spin-slow pointer-events-none"
        viewBox="0 0 200 200"
      >
        <circle cx="100" cy="100" r="94" fill="none" stroke="var(--gold-dim)" strokeWidth="0.4" strokeDasharray="3 5" />
        <circle cx="100" cy="100" r="78" fill="none" stroke="var(--gold-dim)" strokeWidth="0.5" />
        <circle cx="100" cy="100" r="62" fill="none" stroke="var(--gold-dim)" strokeWidth="0.3" strokeDasharray="1 3" />
        <circle cx="100" cy="100" r="46" fill="none" stroke="var(--gold-dim)" strokeWidth="0.4" />
        <circle cx="100" cy="100" r="30" fill="none" stroke="var(--gold-dim)" strokeWidth="0.3" />
        {/* 象限点 + 十字线 */}
        {[[100, 6], [194, 100], [100, 194], [6, 100]].map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="2.5" fill="var(--gold-bright)" opacity="0.8" />
            <line x1={x} y1="100" x2={x} y2={y} stroke="var(--gold-dim)" strokeWidth="0.3" />
            <line x1="100" y1={y} x2={x} y2={y} stroke="var(--gold-dim)" strokeWidth="0.3" />
          </g>
        ))}
        {/* 内圈小星 */}
        {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
          const rad = (deg * Math.PI) / 180;
          const cx = 100 + 38 * Math.cos(rad);
          const cy = 100 + 38 * Math.sin(rad);
          return (
            <circle key={deg} cx={cx} cy={cy} r="1" fill="var(--gold)" opacity="0.5" />
          );
        })}
      </svg>
      {/* 左下小型仪象 */}
      <svg
        aria-hidden
        className="absolute -left-8 bottom-2 w-[180px] h-[100px] opacity-25 spin-slow-rev pointer-events-none"
        viewBox="0 0 200 120"
      >
        <path d="M 10 60 Q 100 0 190 60 Q 100 120 10 60 Z" fill="none" stroke="var(--gold-dim)" strokeWidth="0.5" />
        <path d="M 30 60 Q 100 20 170 60 Q 100 100 30 60 Z" fill="none" stroke="var(--gold-dim)" strokeWidth="0.35" />
        <circle cx="100" cy="60" r="3" fill="var(--gold-bright)" opacity="0.7" />
        <circle cx="100" cy="60" r="8" fill="none" stroke="var(--gold)" strokeWidth="0.3" opacity="0.5" />
      </svg>
    </>
  );
}
