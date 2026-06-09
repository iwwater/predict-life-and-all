// /daily - 每日个人化摘要
// v1 增长主线:
//   - 拉后端 /api/daily(无生日时 GET,有生日时 POST)
//   - 展示今日日柱 + 用户日主 + 五行互动 + 今日塔罗 + 今日一问
//   - 模板化呈现,不调 LLM;温和语言,不预测
//   - 没有生日时给"录入生日"入口(到 /cast)
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchDaily, type DailyPayload } from "../lib/api";
import { useHistory, deriveTags } from "../store/history";
import type { Birth } from "../lib/types";
import { COLOR, EmptyBox, SkeletonBlock } from "../components/ui";
import { SUBJECTS, TAROT_SPREADS } from "../lib/method-info";
import { OrnamentalDivider } from "../components/Interactions";
import { AuspiciousClouds, PlanetSymbols } from "../components/MysticElements";
import { useI18n } from "../lib/i18n";

const SUBJECT_LABEL: Record<string, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<string, string>,
);

const SPREAD_LABEL: Record<string, string> = TAROT_SPREADS.reduce(
  (acc, s) => ({ ...acc, [s.code]: s.label }),
  {} as Record<string, string>,
);

const RELATION_TONE: Record<string, string> = {
  比和: COLOR.jade,
  印: COLOR.azure,
  食伤: COLOR.goldBright,
  官杀: COLOR.danger,
  财: COLOR.goldBright,
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
    // 取最近一次有完整生日的 entry 作为 birth
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
  const tone = it ? RELATION_TONE[it.relation] || COLOR.goldBright : COLOR.goldBright;
  const hasBirth = !!u;

  return (
    <div className="space-y-5">
      <div className="relative">
        <div className="absolute right-0 -top-2 opacity-[0.15] pointer-events-none" aria-hidden>
          <AuspiciousClouds />
        </div>
      </div>
      <header>
        <div className="text-[10px] uppercase tracking-[0.4em]" style={{ color: COLOR.gold }}>
          {t("daily.title")}
        </div>
        <h1 className="text-2xl mt-2 font-display" style={{ color: COLOR.ink }}>
          {payload.date} · {td.ganzhi_day} {t("cast.birth.day")}
        </h1>
        <div className="text-xs mt-1" style={{ color: COLOR.muted }}>
          {td.lunar_date}
          {td.jie_qi && <span className="ml-2">· {td.jie_qi}</span>}
          {td.shengxiao && <span className="ml-2">· {td.shengxiao}{lang === "zh" ? "年" : ""}</span>}
        </div>
      </header>

      <section className="card-raised card-highlight grid sm:grid-cols-3 gap-3 text-sm">
        <Stat label={lang === "zh" ? "日柱" : "Day Pillar"} value={td.ganzhi_day} />
        <Stat label={t("intro.wuXing")} value={td.day_wuxing} tone="jade" />
        <Stat label={lang === "zh" ? "年柱" : "Year Pillar"} value={td.ganzhi_year} tone="azure" />
      </section>

      {hasBirth ? (
        <section className="card-raised card-highlight space-y-3">
          <div className="flex items-center gap-3 flex-wrap text-sm">
            <span style={{ color: COLOR.muted }}>{lang === "zh" ? "你的日主" : "Your Day Master"}</span>
            <span className="text-base font-semibold" style={{ color: COLOR.ink }}>{u!.day_master}</span>
            <span className="tag" style={{ color: COLOR.jade }}>{u!.day_wuxing}</span>
            <span style={{ color: COLOR.muted }}>·</span>
            <span style={{ color: COLOR.muted }}>{lang === "zh" ? "今日五行" : "Today's Element"}</span>
            <span className="text-base font-semibold" style={{ color: COLOR.ink }}>{td.day_wuxing}</span>
            <span className="ml-auto tag" style={{ background: `${tone}22`, color: tone, borderColor: tone }}>
              {it!.label}
            </span>
          </div>
          <div className="text-sm leading-relaxed" style={{ color: COLOR.inkSoft }}>{it!.action}</div>
          <div className="text-xs" style={{ color: COLOR.muted }}>{lang === "zh" ? "提醒" : "Note"}: {it!.watch}</div>
          {it!.subject_hint && (
            <div className="pt-2 border-t" style={{ borderColor: COLOR.lineSoft }}>
              <Link
                to={`/cast?subject=${it!.subject_hint}&fromDaily=1`}
                className="text-sm inline-flex items-center gap-1"
                style={{ color: COLOR.goldBright }}
              >
                {lang === "zh" ? `顺着"${SUBJECT_LABEL[it!.subject_hint] || it!.subject_hint}"去看一次 →` : `Explore "${SUBJECT_LABEL[it!.subject_hint] || it!.subject_hint}" →`}
              </Link>
            </div>
          )}
        </section>
      ) : (
        <section className="card-raised text-sm flex items-center justify-between gap-3 flex-wrap card-highlight">
          <div style={{ color: COLOR.inkSoft }}>
            {t("daily.noBirth")}
          </div>
          <Link to="/cast" className="btn-primary text-xs">{t("daily.enterBirth")}</Link>
        </section>
      )}

      <section className="grid sm:grid-cols-2 gap-4">
        <div className="card-raised card-highlight space-y-2">
          <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.gold }}>{t("daily.tarot")}</div>
          <div className="flex items-baseline gap-2 flex-wrap">
            <div className="text-xl font-display" style={{ color: COLOR.ink }}>{td.tarot_card.name}</div>
            <div className="tag" style={{
              color: td.tarot_card.orient === "正位" ? COLOR.jade : COLOR.muted,
              borderColor: td.tarot_card.orient === "正位" ? COLOR.jade : COLOR.line,
            }}>{td.tarot_card.orient}</div>
          </div>
          <div className="text-xs" style={{ color: COLOR.muted }}>{td.tarot_card.keywords}</div>
          <div className="text-[10px]" style={{ color: COLOR.muted }}>
            seed: {td.tarot_card.seed_used}
            {hasBirth ? ` · ${lang === "zh" ? "已按出生日稳定" : "personalized by birth"}` : ` · ${lang === "zh" ? "全网统一" : "shared globally"}`}
          </div>
          <Link
            to={`/cast?subject=tarot_guidance&spread=single&fromDaily=1&seed=${encodeURIComponent(td.tarot_card.seed_used)}`}
            className="text-xs inline-block"
            style={{ color: COLOR.goldBright }}
          >
            {lang === "zh" ? "用这张牌展开一次完整指引 →" : "Full reading with this card →"}
          </Link>
        </div>

        <div className="card-raised card-highlight space-y-2">
          <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.gold }}>{t("daily.question")}</div>
          <div className="text-base leading-relaxed" style={{ color: COLOR.inkSoft }}>{td.question_seed}</div>
          <div className="text-[10px]" style={{ color: COLOR.muted }}>
            {t("daily.question.disclaimer")}
          </div>
        </div>
      </section>

      <details className="card-raised text-xs">
        <summary className="cursor-pointer" style={{ color: COLOR.goldBright }}>{t("daily.basis")}</summary>
        <div className="mt-2 space-y-1 leading-relaxed" style={{ color: COLOR.muted }}>
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

function Stat({ label, value, tone }: { label: string; value: string; tone?: "gold" | "jade" | "azure" | "ink" }) {
  const color = tone === "jade" ? COLOR.jade
    : tone === "azure" ? COLOR.azure
    : tone === "ink" ? COLOR.ink
    : COLOR.goldBright;
  return (
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>{label}</span>
      <span className="text-lg font-semibold mt-0.5" style={{ color }}>{value}</span>
    </div>
  );
}
