// /daily - 每日个人化摘要（「古籍×仪器」纸墨风格）
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchDaily, type DailyPayload } from "../lib/api";
import { useHistory } from "../store/history";
import type { Birth } from "../lib/types";
import { EmptyBox, SkeletonBlock } from "../components/ui";
import { SUBJECTS } from "../lib/method-info";
import { useI18n } from "../lib/i18n";

const SUBJECT_LABEL: Record<string, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<string, string>,
);

const RELATION_TONE: Record<string, string> = {
  比和: "var(--verdigris)",
  印: "var(--indigo)",
  食伤: "var(--cinnabar)",
  官杀: "var(--cinnabar)",
  财: "var(--cinnabar)",
};

export function Daily() {
  const { t, lang } = useI18n();
  const [params] = useSearchParams();
  const dateParam = params.get("date") || undefined;
  const [payload, setPayload] = useState<DailyPayload | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const items = useHistory((s) => s.items);

  useEffect(() => {
    setPayload(null);
    setErr(null);
    const last = items.find((it) => it.birth?.year);
    const birth: Birth | undefined = last
      ? {
          year: last.birth.year, month: last.birth.month, day: last.birth.day,
          hour: last.birth.hour, minute: last.birth.minute,
          gender: last.birth.gender, calendar: "gregorian",
          lat: last.birth.lat ?? null, lng: last.birth.lng ?? null,
          tz: last.birth.tz, is_leap_month: false,
        }
      : undefined;
    fetchDaily(dateParam, birth).then(setPayload).catch((e) => setErr(String(e?.message || e)));
  }, [dateParam, items]);

  if (err) {
    return <EmptyBox>{lang === "zh" ? "加载今日摘要失败" : "Failed to load daily summary"}: {err}</EmptyBox>;
  }
  if (!payload) {
    return (
      <div className="space-y-4">
        <SkeletonBlock height={140} />
        <SkeletonBlock height={220} />
        <SkeletonBlock height={120} />
      </div>
    );
  }

  const td = payload.today;
  const u = payload.user;
  const it = payload.interaction;
  const tone = it ? RELATION_TONE[it.relation] || "var(--cinnabar)" : "var(--cinnabar)";
  const hasBirth = !!u;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="paper-title">
          <span className="stamp" />
          <span>{t("daily.title")}</span>
          <span className="sub">{payload.date}</span>
        </h1>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.82rem", color: "var(--ink)", marginTop: "0.35rem" }}>
          {td.ganzhi_day} {t("cast.birth.day")} · {td.day_wuxing}
        </div>
        <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>
          {td.lunar_date}
          {td.jie_qi && <span style={{ marginLeft: "0.5rem" }}>· {td.jie_qi}</span>}
          {td.shengxiao && <span style={{ marginLeft: "0.5rem" }}>· {td.shengxiao}{lang === "zh" ? "年" : ""}</span>}
        </div>
      </header>

      <section className="paper-grid-cell" style={{ padding: "0.7rem 1rem" }}>
        <div className="grid grid-cols-3 gap-3">
          <Stat label={lang === "zh" ? "日柱" : "Day Pillar"} value={td.ganzhi_day} />
          <Stat label={t("intro.wuXing")} value={td.day_wuxing} tone="verdigris" />
          <Stat label={lang === "zh" ? "年柱" : "Year Pillar"} value={td.ganzhi_year} tone="indigo" />
        </div>
      </section>

      {hasBirth ? (
        <section className="paper-frame space-y-3">
          <div className="flex items-center gap-3 flex-wrap" style={{ fontSize: "0.85rem", fontFamily: "'Noto Serif SC', serif" }}>
            <span style={{ color: "var(--ink-soft)" }}>{lang === "zh" ? "你的日主" : "Your Day Master"}</span>
            <span style={{ fontWeight: 700, color: "var(--ink)", fontSize: "1rem" }}>{u!.day_master}</span>
            <span className="paper-tag paper-tag-east">{u!.day_wuxing}</span>
            <span style={{ color: "var(--ink-soft)" }}>·</span>
            <span style={{ color: "var(--ink-soft)" }}>{lang === "zh" ? "今日五行" : "Today's Element"}</span>
            <span style={{ fontWeight: 700, color: "var(--ink)", fontSize: "1rem" }}>{td.day_wuxing}</span>
            <span className="paper-tag" style={{ color: tone, borderColor: tone, marginLeft: "auto" }}>
              {it!.label}
            </span>
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--ink)", lineHeight: 1.7 }}>{it!.action}</div>
          <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>{lang === "zh" ? "提醒" : "Note"}: {it!.watch}</div>
          {it!.subject_hint && (
            <div style={{ paddingTop: "0.5rem", borderTop: "1px solid var(--rule)" }}>
              <Link
                to={`/cast?subject=${it!.subject_hint}&fromDaily=1`}
                className="paper-link"
              >
                {lang === "zh" ? `顺着"${SUBJECT_LABEL[it!.subject_hint] || it!.subject_hint}"去看一次 →` : `Explore "${SUBJECT_LABEL[it!.subject_hint] || it!.subject_hint}" →`}
              </Link>
            </div>
          )}
        </section>
      ) : (
        <section className="paper-grid-cell flex items-center justify-between gap-3 flex-wrap" style={{ padding: "1rem" }}>
          <div style={{ color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif", fontSize: "0.85rem" }}>
            {t("daily.noBirth")}
          </div>
          <Link to="/cast" className="paper-btn" style={{ fontSize: "0.8rem" }}>{t("daily.enterBirth")}</Link>
        </section>
      )}

      <section className="grid sm:grid-cols-2 gap-4">
        <div className="paper-frame space-y-2">
          <div className="paper-eyebrow">{t("daily.tarot")}</div>
          <div className="flex items-baseline gap-2 flex-wrap">
            <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 700, fontSize: "1.1rem", color: "var(--ink)" }}>
              {td.tarot_card.name}
            </span>
            <span className="paper-tag" style={{
              color: td.tarot_card.orient === "正位" ? "var(--verdigris)" : "var(--ink-soft)",
              borderColor: td.tarot_card.orient === "正位" ? "rgba(90,112,88,0.4)" : "var(--rule)",
            }}>
              {td.tarot_card.orient}
            </span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>{td.tarot_card.keywords}</div>
          <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
            seed: {td.tarot_card.seed_used}
          </div>
          <Link
            to={`/cast?subject=tarot_guidance&spread=single&fromDaily=1&seed=${encodeURIComponent(td.tarot_card.seed_used)}`}
            className="paper-link"
          >
            {lang === "zh" ? "用这张牌展开一次完整指引 →" : "Full reading with this card →"}
          </Link>
        </div>

        <div className="paper-frame space-y-2">
          <div className="paper-eyebrow">{t("daily.question")}</div>
          <div style={{ fontSize: "0.92rem", color: "var(--ink)", lineHeight: 1.7 }}>{td.question_seed}</div>
          <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
            {t("daily.question.disclaimer")}
          </div>
        </div>
      </section>

      <details className="paper-grid-cell" style={{ padding: "0.7rem 1rem", fontSize: "0.75rem" }}>
        <summary style={{ cursor: "pointer", color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif", fontWeight: 600 }}>
          {t("daily.basis")}
        </summary>
        <div style={{ marginTop: "0.5rem", color: "var(--ink-soft)", lineHeight: 1.6 }}>
          <div>{t("result.basis.method")}: {payload.calculation_basis.method} · {t("result.basis.rule")}: {payload.calculation_basis.rule_version}</div>
          <div>{lang === "zh" ? "数据源" : "Data source"}: {payload.calculation_basis.input_source}</div>
          <div>{lang === "zh" ? "日期输入" : "Date input"}: {payload.calculation_basis.calendar_input} · {lang === "zh" ? "阳历" : "Solar"}: {payload.calculation_basis.solar_date}</div>
          <div>{lang === "zh" ? "农历" : "Lunar"}: {payload.calculation_basis.lunar_date} {payload.calculation_basis.jie_qi && `· ${payload.calculation_basis.jie_qi}`}</div>
          <div>{t("result.basis.limits")}: {payload.calculation_basis.limits}</div>
        </div>
      </details>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "cinnabar" | "verdigris" | "indigo" | "ink" }) {
  const color = tone === "verdigris" ? "var(--verdigris)"
    : tone === "indigo" ? "var(--indigo)"
    : tone === "ink" ? "var(--ink)"
    : "var(--cinnabar)";
  return (
    <div>
      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.65rem", color: "var(--ink-soft)", letterSpacing: "0.1em" }}>{label}</div>
      <div style={{ fontSize: "1rem", fontWeight: 700, color, fontFamily: "'Noto Serif SC', serif", marginTop: "0.15rem" }}>{value}</div>
    </div>
  );
}
