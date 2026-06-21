// 排盘页:「古籍×仪器」4 步引导式 stepper
// 保持所有业务逻辑,仅替换视觉为纸墨风格
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchMethods, computeChartMulti, computeMultiWithValidation } from "../lib/api";
import type { Birth, Method, MethodMeta, Subject, TarotSpread, TarotSystem } from "../lib/types";
import { CITY_PRESETS, CITY_REGIONS, cityOptionLabel, findCityByLatLng } from "../lib/cities";
import { DIRECTIONS_8 } from "../lib/compass";
import { METHOD_PLAIN, SUBJECTS, TAROT_SPREADS, TAROT_SYSTEMS } from "../lib/method-info";
import { SkeletonBlock } from "../components/ui";
import { useHistory, deriveTags } from "../store/history";
import { ProgressArc } from "../components/Interactions";
import { useI18n } from "../lib/i18n";

interface FormState {
  year: number; month: number; day: number;
  hour: number; minute: number;
  gender: "male" | "female" | "unspecified";
  city: string;
  subject: Subject;
  selected: Method[];
  modeByMethod: Partial<Record<Method, string>>;
  sittingDir: string;
  constructionYear: number;
  tarotSpread: TarotSpread;
  tarotSystem: TarotSystem;
  fixSeed: boolean;
  seed: string;
  question: string;
  fatherZodiac: string;
  motherZodiac: string;
}

const DEFAULT_SUBJECT = SUBJECTS[0];
const MAX_RECOMMENDED = 4;
const DEFAULT_SELECTED: Method[] = ["bazi", "western"];
const DEFAULT: FormState = {
  year: 1990, month: 5, day: 15,
  hour: 8, minute: 30,
  gender: "male",
  city: "上海",
  subject: DEFAULT_SUBJECT.key,
  selected: DEFAULT_SELECTED,
  modeByMethod: DEFAULT_SUBJECT.modeByMethod,
  sittingDir: "正东",
  constructionYear: new Date().getFullYear(),
  tarotSpread: "single",
  tarotSystem: "waite",
  fixSeed: false,
  seed: "",
  question: "",
  fatherZodiac: "",
  motherZodiac: "",
};

type StepKey = "subject" | "birth" | "methods" | "params";

export function Cast() {
  const { t, lang } = useI18n();
  const STEPS = [
    { key: "subject" as const, label: t("cast.step.subject"), hint: t("cast.step.subject.hint") },
    { key: "birth" as const,   label: t("cast.step.birth"),   hint: t("cast.step.birth.hint") },
    { key: "methods" as const, label: t("cast.step.methods"), hint: t("cast.step.methods.hint") },
    { key: "params" as const,  label: t("cast.step.params"),  hint: t("cast.step.params.hint") },
  ];
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [methods, setMethods] = useState<MethodMeta[]>([]);
  const [form, setForm] = useState<FormState>(DEFAULT);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMore, setShowMore] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    fetchMethods().then(setMethods).catch(() => setMethods([]));
  }, []);

  useEffect(() => {
    const m = params.get("methods");
    const fromHistory = params.get("fromHistory");
    const subjectParam = params.get("subject");
    const spreadParam = params.get("spread");
    const seedParam = params.get("seed");
    if (m) setForm((f) => ({ ...f, selected: m.split(",") as Method[] }));
    // fromCase removed — celebrity content purged per legal compliance
    if (fromHistory) {
      const it = useHistory.getState().items.find((x) => x.id === fromHistory);
      if (it) {
        const lat = it.birth.lat;
        const lng = it.birth.lng;
        const city = (typeof lat === "number" && typeof lng === "number")
          ? findCityByLatLng(lat, lng)
          : null;
        setForm((f) => ({
          ...f,
          year: it.birth.year, month: it.birth.month, day: it.birth.day,
          hour: it.birth.hour, minute: it.birth.minute,
          gender: it.birth.gender,
          city: city?.name || f.city,
          subject: it.subject || f.subject,
          selected: it.methods,
          modeByMethod: it.modeByMethod || f.modeByMethod,
          tarotSpread: it.spread || f.tarotSpread,
          fixSeed: false, seed: "",
        }));
        setShowMore(false);
        setStepIdx(STEPS.length - 1);
      }
    }
    if (subjectParam) {
      setForm((f) => {
        const next = SUBJECTS.find((s) => s.key === subjectParam);
        if (!next) return f;
        return {
          ...f,
          subject: next.key,
          selected: next.methods.slice(0, MAX_RECOMMENDED),
          modeByMethod: next.modeByMethod,
          tarotSpread: next.defaultSpread || f.tarotSpread,
        };
      });
      setShowMore(false);
    }
    if (spreadParam) {
      setForm((f) => ({ ...f, tarotSpread: spreadParam as TarotSpread }));
    }
    if (seedParam) {
      const n = parseInt(seedParam, 10);
      setForm((f) => ({
        ...f,
        fixSeed: true,
        seed: Number.isFinite(n) ? String(n) : seedParam,
      }));
    }
  }, [params]);

  const cityInfo = useMemo(() => CITY_PRESETS.find((x) => x.name === form.city) || CITY_PRESETS[0], [form.city]);
  const sittingInfo = useMemo(() => DIRECTIONS_8.find((d) => d.code === form.sittingDir) || DIRECTIONS_8[2], [form.sittingDir]);
  const subjectInfo = useMemo(() => SUBJECTS.find((s) => s.key === form.subject) || DEFAULT_SUBJECT, [form.subject]);
  const showSitting = form.selected.includes("xuankong") || form.selected.includes("bazhai");
  const showTarot = form.selected.includes("tarot");
  const showSeed = form.selected.some((m) => ["tarot", "lenormand", "liuyao", "meihua"].includes(m));
  const showTieban = form.selected.includes("tieban");
  const recommendedIds = subjectInfo.methods.slice(0, MAX_RECOMMENDED);
  const overflowIds = subjectInfo.methods.slice(MAX_RECOMMENDED);
  const moreIds = [...overflowIds, ...methods.map((m) => m.id).filter((id) => !subjectInfo.methods.includes(id))];
  const orderedMethods = [
    ...recommendedIds.map((id) => methods.find((m) => m.id === id)).filter(Boolean),
    ...moreIds.map((id) => methods.find((m) => m.id === id)).filter(Boolean),
  ] as MethodMeta[];

  function chooseSubject(subject: Subject) {
    const next = SUBJECTS.find((s) => s.key === subject) || DEFAULT_SUBJECT;
    setForm((f) => ({
      ...f,
      subject: next.key,
      selected: next.methods.slice(0, MAX_RECOMMENDED),
      modeByMethod: next.modeByMethod,
      tarotSpread: next.defaultSpread || f.tarotSpread,
    }));
    setShowMore(false);
  }
  function toggle(method: Method) {
    setForm((f) => ({
      ...f,
      selected: f.selected.includes(method)
        ? f.selected.filter((x) => x !== method)
        : [...f.selected, method],
    }));
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const birth: Birth = {
      year: form.year, month: form.month, day: form.day,
      hour: form.hour, minute: form.minute,
      gender: form.gender,
      calendar: "gregorian",
      lat: cityInfo.lat, lng: cityInfo.lng,
      tz: cityInfo.tz,
      is_leap_month: false,
    };

    const validationMethods = ["bazi_v2", "bazi", "ziwei", "western"];
    const hasValidationEligible = form.selected.filter((m) => validationMethods.includes(m)).length >= 2;

    try {
      let charts: Record<string, any>;
      let enhancedData: Record<string, any> | undefined;

      if (hasValidationEligible) {
        const result = await computeMultiWithValidation(
          form.selected as Method[],
          birth,
          form.subject,
          true,
        );
        charts = result.charts || {};
        enhancedData = {
          cross_validation: result.cross_validation,
          peach_blossom: result.peach_blossom,
          relationship_timing: result.relationship_timing,
          fate_modification: result.fate_modification,
        };
      } else {
        charts = await computeChartMulti(form.selected as Method[], birth, {
          subject: form.subject,
          modeByMethod: form.modeByMethod,
          spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
          tarot_system: form.selected.includes("tarot") ? form.tarotSystem : undefined,
          seed: form.fixSeed && form.seed ? form.seed : undefined,
          question: form.question || undefined,
          father_zodiac: form.fatherZodiac || undefined,
          mother_zodiac: form.motherZodiac || undefined,
          sitting: sittingInfo.sans,
          construction_year: form.constructionYear,
          methods: form.selected,
        });
      }

      const hid = crypto.randomUUID();
      useHistory.getState().add({
        id: hid,
        ts: Date.now(),
        birth,
        methods: form.selected,
        charts,
        question: form.question || undefined,
        subject: form.subject,
        modeByMethod: form.modeByMethod,
        spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
        tags: deriveTags(form.selected, form.subject),
        favorite: false,
        reflection: null,
      });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({
          birth,
          question: form.question || undefined,
          charts,
          methods: form.selected,
          enhancedData: enhancedData || undefined,
        }));
        navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) {
      if (hasValidationEligible && err.message?.includes("422")) {
        try {
          const charts = await computeChartMulti(form.selected as Method[], birth, {
            subject: form.subject,
            modeByMethod: form.modeByMethod,
            spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
            tarot_system: form.selected.includes("tarot") ? form.tarotSystem : undefined,
            seed: form.fixSeed && form.seed ? form.seed : undefined,
            question: form.question || undefined,
            father_zodiac: form.fatherZodiac || undefined,
            mother_zodiac: form.motherZodiac || undefined,
            sitting: sittingInfo.sans,
            construction_year: form.constructionYear,
            methods: form.selected,
          });
          const hid = crypto.randomUUID();
          useHistory.getState().add({
            id: hid, ts: Date.now(), birth, methods: form.selected, charts,
            question: form.question || undefined, subject: form.subject,
            modeByMethod: form.modeByMethod,
            spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
            tags: deriveTags(form.selected, form.subject),
            favorite: false, reflection: null,
          });
          sessionStorage.setItem("mystic:result_id", hid);
          sessionStorage.setItem("mystic:result", JSON.stringify({
            birth, question: form.question || undefined, charts, methods: form.selected,
          }));
          navigate(`/result?ts=${Date.now()}`);
          return;
        } catch (fallbackErr: any) {
          setError(String(fallbackErr?.message || fallbackErr));
        }
      } else {
        setError(String(err?.message || err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (methods.length === 0) {
    return <div className="space-y-4"><SkeletonBlock height={120} /><SkeletonBlock height={300} /></div>;
  }

  const step = STEPS[stepIdx];
  const goNext = () => setStepIdx((i) => Math.min(STEPS.length - 1, i + 1));
  const goPrev = () => setStepIdx((i) => Math.max(0, i - 1));
  const canNext =
    step.key === "subject" ? !!form.subject :
    step.key === "birth" ? form.year > 1900 && form.month >= 1 && form.month <= 12 && form.day >= 1 && form.day <= 31 :
    step.key === "methods" ? form.selected.length > 0 :
    true;
  const canSubmit = form.selected.length > 0;

  return (
    <form onSubmit={submit} className="space-y-5">
      {/* 顶部 stepper */}
      <Stepper stepIdx={stepIdx} onJump={(i) => setStepIdx(i)} />

      {/* 步骤 panel — 每次变化重新挂载 */}
      <div key={step.key} className="animate-fade-in">
        {step.key === "subject" && (
          <StepSubject form={form} chooseSubject={chooseSubject} />
        )}
        {step.key === "birth" && (
          <StepBirth form={form} setForm={setForm} cityInfo={cityInfo} />
        )}
        {step.key === "methods" && (
          <StepMethods
            form={form}
            subjectInfo={subjectInfo}
            orderedMethods={orderedMethods}
            toggle={toggle}
            showMore={showMore}
            setShowMore={setShowMore}
          />
        )}
        {step.key === "params" && (
          <StepParams
            form={form}
            setForm={setForm}
            showTarot={showTarot}
            showSitting={showSitting}
            showSeed={showSeed}
            showTieban={showTieban}
          />
        )}
      </div>

      {error && (
        <div className="paper-error">{error}</div>
      )}

      {/* 底部操作栏 */}
      <div className="sticky bottom-0 -mx-4 sm:-mx-6 px-4 sm:px-6 py-3 flex items-center justify-between gap-3"
        style={{ background: "var(--paper)", borderTop: "1px solid var(--rule)" }}>
        <div className="flex items-center gap-2 text-xs" style={{ color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
          {submitting ? (
            <>
              <ProgressArc value={0.4} size={28} />
              <span>{t("cast.submitting")}</span>
            </>
          ) : (
            <>
              <span>{lang === "zh" ? "已选" : "Selected"} <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>{form.selected.length}</span> {lang === "zh" ? "法" : "methods"}</span>
              <span>·</span>
              <span>{subjectInfo.label}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className="paper-btn-ghost" onClick={() => setForm(DEFAULT)}>{t("cast.reset")}</button>
          {stepIdx > 0 && (
            <button type="button" className="paper-btn-ghost" onClick={goPrev}>{t("cast.prev")}</button>
          )}
          {stepIdx < STEPS.length - 1 ? (
            <button type="button" className="paper-btn" disabled={!canNext} onClick={goNext}>
              {t("cast.next")}
            </button>
          ) : (
            <button type="submit" className="paper-btn" disabled={submitting || !canSubmit}>
              {submitting ? t("cast.submitting") : `${t("cast.submit")} (${form.selected.length} ${lang === "zh" ? "法" : ""})`}
            </button>
          )}
        </div>
      </div>
    </form>
  );
}

// === 顶部 stepper ===
function Stepper({ stepIdx, onJump }: { stepIdx: number; onJump: (i: number) => void }) {
  const { t } = useI18n();
  const steps = [
    { key: "subject", label: t("cast.step.subject"), hint: t("cast.step.subject.hint") },
    { key: "birth",   label: t("cast.step.birth"),   hint: t("cast.step.birth.hint") },
    { key: "methods", label: t("cast.step.methods"), hint: t("cast.step.methods.hint") },
    { key: "params",  label: t("cast.step.params"),  hint: t("cast.step.params.hint") },
  ];
  const pct = (stepIdx + 1) / steps.length;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        {steps.map((s, i) => {
          const done = i < stepIdx;
          const active = i === stepIdx;
          return (
            <button key={s.key} type="button" onClick={() => onJump(i)}
              className="flex-1 min-w-0 text-left px-2.5 py-1.5 rounded-sm transition-colors"
              style={{
                color: active ? "var(--cinnabar)" : done ? "var(--verdigris)" : "var(--ink-soft)",
                background: active ? "rgba(176,58,46,0.05)" : "transparent",
                border: `1px solid ${active ? "var(--cinnabar)" : done ? "var(--verdigris)" : "var(--rule)"}`,
                fontFamily: "'Noto Serif SC', serif",
                cursor: "pointer",
              }}>
              <div className="flex items-center gap-1.5">
                <span
                  className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] shrink-0"
                  style={{
                    background: done ? "var(--verdigris)" : active ? "var(--cinnabar)" : "transparent",
                    color: done || active ? "#fff" : "var(--ink-soft)",
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  {done ? "✓" : i + 1}
                </span>
                <span className="text-xs" style={{ fontWeight: active ? 600 : 400 }}>{s.label}</span>
              </div>
              <div className="text-[10px] mt-0.5 truncate" style={{ color: "var(--ink-soft)" }}>{s.hint}</div>
            </button>
          );
        })}
      </div>
      {/* 进度条 */}
      <div className="paper-progress">
        <div
          className="paper-progress-bar"
          style={{ width: `${Math.round(pct * 100)}%` }}
        />
      </div>
    </div>
  );
}

// === Step 1: 意图 ===
function StepSubject({ form, chooseSubject }: { form: FormState; chooseSubject: (s: Subject) => void }) {
  const { t, lang } = useI18n();
  return (
    <section className="paper-frame space-y-3">
      <header>
        <h2 className="paper-title"><span className="stamp" />{t("cast.ask.subject")}</h2>
        <p style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>{t("cast.ask.subject.desc")}</p>
      </header>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {SUBJECTS.map((s) => {
          const on = form.subject === s.key;
          return (
            <button key={s.key} type="button" onClick={() => chooseSubject(s.key)}
              className="paper-grid-cell text-left"
              style={{
                borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                borderWidth: on ? 2 : 1,
                background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                cursor: "pointer",
                padding: "0.7rem",
              }}>
              <div className="flex items-center justify-between">
                <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.9rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
                  {s.label}
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "0.3rem", lineHeight: 1.5 }}>{s.desc}</div>
              {on && (
                <div style={{ fontSize: "0.68rem", color: "var(--verdigris)", marginTop: "0.3rem", fontFamily: "'JetBrains Mono', monospace" }}>
                  {lang === "zh" ? "默认推荐" : "Recommended"} {s.methods.slice(0, 2).join(" · ")} …
                </div>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}

// === Step 2: 命主 ===
function StepBirth({ form, setForm, cityInfo }: {
  form: FormState;
  setForm: React.Dispatch<React.SetStateAction<FormState>>;
  cityInfo: ReturnType<typeof CITY_PRESETS["find"]>;
}) {
  const { t } = useI18n();
  return (
    <section className="paper-frame space-y-3">
      <header>
        <h2 className="paper-title"><span className="stamp" />{t("cast.birth.title")}</h2>
        <p style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>{t("cast.birth.desc")}</p>
      </header>
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {(["year", "month", "day", "hour", "minute"] as const).map((key) => (
          <div key={key}>
            <label className="paper-label">{{ year: t("cast.birth.year"), month: t("cast.birth.month"), day: t("cast.birth.day"), hour: t("cast.birth.hour"), minute: t("cast.birth.minute") }[key]}</label>
            <input className="paper-input" type="number" value={form[key]} onChange={(e) => setForm({ ...form, [key]: parseInt(e.target.value, 10) || 0 })} />
          </div>
        ))}
        <div>
          <label className="paper-label">{t("cast.birth.gender")}</label>
          <select className="paper-input" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value as any })}>
            <option value="male">{t("cast.gender.male")}</option>
            <option value="female">{t("cast.gender.female")}</option>
            <option value="unspecified">{t("cast.gender.unspec")}</option>
          </select>
        </div>
      </div>
      <div className="mt-1">
        <label className="paper-label">{t("cast.birth.city")}</label>
        <select className="paper-input" style={{ maxWidth: "24rem" }} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
          {CITY_REGIONS.map((r) => (
            <optgroup key={r.key} label={r.label}>
              {CITY_PRESETS.filter((c) => c.region === r.key).map((c) => (
                <option key={`${c.province || c.region}-${c.name}`} value={c.name}>{cityOptionLabel(c)}</option>
              ))}
            </optgroup>
          ))}
        </select>
        {cityInfo && (
          <div className="paper-tag" style={{ marginTop: "0.35rem" }}>
            {cityInfo.name} · {cityInfo.lat.toFixed(2)}°N, {cityInfo.lng.toFixed(2)}°E · {cityInfo.tz}
          </div>
        )}
      </div>
    </section>
  );
}

// === Step 3: 术数 ===
function StepMethods({
  form, subjectInfo, orderedMethods, toggle, showMore, setShowMore,
}: {
  form: FormState;
  subjectInfo: typeof SUBJECTS[number];
  orderedMethods: MethodMeta[];
  toggle: (m: Method) => void;
  showMore: boolean;
  setShowMore: (v: boolean | ((p: boolean) => boolean)) => void;
}) {
  const { t, lang } = useI18n();
  const recommendedIds = subjectInfo.methods.slice(0, MAX_RECOMMENDED);
  const recommended = orderedMethods.filter((m) => recommendedIds.includes(m.id));
  const overflow = orderedMethods.filter((m) => !recommendedIds.includes(m.id));

  return (
    <section className="paper-frame space-y-3">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <h2 className="paper-title"><span className="stamp" />{t("cast.methods.title")}</h2>
          <p style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>
            {lang === "zh" ? `已按「${subjectInfo.label}」默认推荐前 ${MAX_RECOMMENDED} 法，点按复选/取消。` : `Default ${MAX_RECOMMENDED} methods recommended for "${subjectInfo.label}". Click to toggle.`}
          </p>
        </div>
        <span className="paper-tag paper-tag-west" style={{ fontSize: "0.68rem" }}>
          {subjectInfo.label} · {subjectInfo.desc}
        </span>
      </header>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {recommended.map((m) => {
          const on = form.selected.includes(m.id);
          const plain = METHOD_PLAIN[m.id];
          return (
            <MethodTile key={m.id} m={m} plain={plain} on={on} toggle={toggle} modeByMethod={form.modeByMethod} />
          );
        })}
      </div>
      {overflow.length > 0 && (
        <>
          <button type="button" onClick={() => setShowMore((v) => !v)}
            className="paper-link"
            style={{ fontSize: "0.78rem", borderBottom: "none" }}>
            {showMore ? t("cast.methods.less") : `${t("cast.methods.more")} (${overflow.length})`}
          </button>
          {showMore && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {overflow.map((m) => {
                const on = form.selected.includes(m.id);
                const plain = METHOD_PLAIN[m.id];
                return (
                  <MethodTile key={m.id} m={m} plain={plain} on={on} toggle={toggle} modeByMethod={form.modeByMethod} />
                );
              })}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function MethodTile({ m, plain, on, toggle, modeByMethod }: {
  m: MethodMeta;
  plain: typeof METHOD_PLAIN[Method] | undefined;
  on: boolean;
  toggle: (m: Method) => void;
  modeByMethod: Partial<Record<Method, string>>;
}) {
  const { lang } = useI18n();
  return (
    <button key={m.id} type="button" onClick={() => toggle(m.id)}
      className="paper-grid-cell text-left"
      style={{
        borderColor: on ? "var(--cinnabar)" : "var(--rule)",
        borderWidth: on ? 2 : 1,
        background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
        cursor: "pointer",
        padding: "0.7rem",
      }}>
      <div className="flex items-center justify-between mb-1">
        <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.9rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
          {m.name_zh}
        </span>
        <span style={{
          display: "inline-block",
          width: 8, height: 8, borderRadius: "50%",
          background: on ? "var(--cinnabar)" : "var(--rule)",
        }} />
      </div>
      <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.5 }}>{plain?.tagline}</div>
      {on && (
        <div style={{ fontSize: "0.68rem", color: "var(--verdigris)", marginTop: "0.3rem", fontFamily: "'JetBrains Mono', monospace" }}>
          {lang === "zh" ? "起法" : "Mode"}: {modeByMethod[m.id] || m.default_mode}
        </div>
      )}
    </button>
  );
}

// === Step 4: 起法 + 提问 ===
function StepParams({ form, setForm, showTarot, showSitting, showSeed, showTieban }: {
  form: FormState;
  setForm: React.Dispatch<React.SetStateAction<FormState>>;
  showTarot: boolean;
  showSitting: boolean;
  showSeed: boolean;
  showTieban: boolean;
}) {
  const { t, lang } = useI18n();
  const sample = METHOD_PLAIN[form.selected[0]]?.sample || (lang === "zh" ? "请写清楚你要测的事" : "Describe what you want to ask about");
  const hasAnyParam = showTarot || showSitting || showSeed || showTieban;
  return (
    <div className="space-y-5">
      {hasAnyParam && (
        <section className="paper-frame space-y-4">
          <header>
            <h2 className="paper-title"><span className="stamp" />{t("cast.params.title")}</h2>
            <p style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>{t("cast.params.desc")}</p>
          </header>
          {showTieban && (
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="paper-label">{lang === "zh" ? "父生肖 (可选·用于条文校验)" : "Father Zodiac (optional)"}</label>
                <select className="paper-input" value={form.fatherZodiac} onChange={(e) => setForm({ ...form, fatherZodiac: e.target.value })}>
                  <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
                  {["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"].map((z) => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="paper-label">{lang === "zh" ? "母生肖 (可选·用于条文校验)" : "Mother Zodiac (optional)"}</label>
                <select className="paper-input" value={form.motherZodiac} onChange={(e) => setForm({ ...form, motherZodiac: e.target.value })}>
                  <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
                  {["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"].map((z) => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
          {showTarot && (
            <div className="space-y-3">
              <div>
                <label className="paper-label">{lang === "zh" ? "塔罗牌阵" : "Tarot Spread"}</label>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {TAROT_SPREADS.map((sp) => {
                    const on = form.tarotSpread === sp.code;
                    const recommended = sp.subjects.includes(form.subject);
                    return (
                      <button key={sp.code} type="button" onClick={() => setForm({ ...form, tarotSpread: sp.code })}
                        className="paper-grid-cell text-left"
                        style={{
                          borderColor: on ? "var(--cinnabar)" : recommended ? "var(--verdigris)" : "var(--rule)",
                          borderWidth: on ? 2 : 1,
                          background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                          cursor: "pointer",
                          padding: "0.65rem",
                        }}>
                        <div className="flex items-center justify-between">
                          <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.88rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
                            {sp.label}
                          </span>
                          {recommended && !on && (
                            <span style={{ fontSize: "0.65rem", color: "var(--verdigris)", fontFamily: "'JetBrains Mono', monospace" }}>
                              {lang === "zh" ? "推荐" : "Rec"}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.2rem" }}>{sp.desc}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="paper-label">{lang === "zh" ? "解读体系" : "Tarot System"}</label>
                <div className="grid sm:grid-cols-3 gap-2">
                  {TAROT_SYSTEMS.map((sys) => {
                    const on = form.tarotSystem === sys.code;
                    return (
                      <button key={sys.code} type="button" onClick={() => setForm({ ...form, tarotSystem: sys.code })}
                        className="paper-grid-cell text-left"
                        style={{
                          borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                          borderWidth: on ? 2 : 1,
                          background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                          cursor: "pointer",
                          padding: "0.65rem",
                        }}>
                        <div style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: on ? 700 : 500, fontSize: "0.88rem", color: on ? "var(--cinnabar)" : "var(--ink)" }}>
                          {sys.label}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.2rem" }}>{sys.desc}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
          {showSitting && (
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="paper-label">{lang === "zh" ? "坐山/门向代表方位" : "Sitting/Facing Direction"}</label>
                <select className="paper-input" value={form.sittingDir} onChange={(e) => setForm({ ...form, sittingDir: e.target.value })}>
                  {DIRECTIONS_8.map((d) => <option key={d.code} value={d.code}>{d.code} · {d.sans}山</option>)}
                </select>
              </div>
              <div>
                <label className="paper-label">{lang === "zh" ? "建造/入伙年份" : "Construction Year"}</label>
                <input className="paper-input" type="number" value={form.constructionYear} onChange={(e) => setForm({ ...form, constructionYear: parseInt(e.target.value, 10) || form.year })} />
              </div>
            </div>
          )}
          {showSeed && (
            <div>
              <label className="paper-label">{lang === "zh" ? "固定种子" : "Fixed Seed"}</label>
              <div className="flex gap-3 items-center flex-wrap">
                <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.83rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <input type="checkbox" checked={form.fixSeed} onChange={(e) => setForm({ ...form, fixSeed: e.target.checked })} />
                  {lang === "zh" ? "固定本次随机/数字起法(可复现)" : "Lock random seed (reproducible)"}
                </label>
                {form.fixSeed && <input className="paper-input" style={{ maxWidth: 160 }} value={form.seed} onChange={(e) => setForm({ ...form, seed: e.target.value })} placeholder="例如 42" />}
              </div>
            </div>
          )}
        </section>
      )}
      {!hasAnyParam && (
        <section className="paper-grid-cell" style={{ fontSize: "0.83rem", color: "var(--ink-soft)", padding: "1rem" }}>
          {lang === "zh" ? "所选术数不需要额外起法参数，直接提问即可。" : "Selected methods need no extra parameters — just ask your question."}
        </section>
      )}

      <section className="paper-frame space-y-2">
        <label className="paper-label">{t("cast.question.label")}</label>
        <textarea className="paper-input" style={{ minHeight: 100 }} value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
          placeholder={sample} />
        <div className="flex items-center justify-between gap-2">
          <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>{t("cast.question.help")}</div>
          <div style={{ fontSize: "0.68rem", color: form.question.length > 200 ? "var(--cinnabar)" : "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
            {form.question.length}/400
          </div>
        </div>
      </section>
    </div>
  );
}
