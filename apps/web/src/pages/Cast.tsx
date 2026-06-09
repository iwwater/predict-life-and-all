// 排盘页: 4 步引导式 stepper
//   1. 命主(出生信息)  2. 意图(想测什么)  3. 术数(选法)  4. 起法 + 提问(参数 + 提交)
// Cut 交互感: 每步独立 panel, 顶部进度条 + 步骤徽标, 上一步/下一步切换有 reveal-up 动画
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchCases, fetchMethods, computeChartMulti, computeMultiWithValidation } from "../lib/api";
import type { Birth, Case, Method, MethodMeta, Subject, TarotSpread } from "../lib/types";
import { CITY_PRESETS, CITY_REGIONS, cityOptionLabel, findCityByLatLng } from "../lib/cities";
import { DIRECTIONS_8 } from "../lib/compass";
import { METHOD_PLAIN, SUBJECTS, TAROT_SPREADS } from "../lib/method-info";
import { COLOR, SkeletonBlock } from "../components/ui";
import { useHistory, deriveTags } from "../store/history";
import { Reveal, ProgressArc } from "../components/Interactions";
import { StarArray } from "../components/MysticElements";
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
  fixSeed: false,
  seed: "",
  question: "",
  fatherZodiac: "",
  motherZodiac: "",
};

type StepKey = "subject" | "birth" | "methods" | "params";

const SUBJECT_GLYPH: Record<Subject, "self" | "annual" | "decision" | "relationship" | "career" | "wealth" | "lost" | "home" | "tarot" | "lenormand"> = {
  self_life: "self",
  annual_luck: "annual",
  decision: "decision",
  relationship: "relationship",
  career: "career",
  wealth: "wealth",
  lost_item: "lost",
  home_fengshui: "home",
  tarot_guidance: "tarot",
  lenormand_guidance: "lenormand",
};

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
  const [cases, setCases] = useState<Case[]>([]);
  const [form, setForm] = useState<FormState>(DEFAULT);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMore, setShowMore] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    fetchMethods().then(setMethods).catch(() => setMethods([]));
    fetchCases().then(setCases).catch(() => setCases([]));
  }, []);

  useEffect(() => {
    const m = params.get("methods");
    const fromCase = params.get("fromCase");
    const fromHistory = params.get("fromHistory");
    const subjectParam = params.get("subject");
    const spreadParam = params.get("spread");
    const seedParam = params.get("seed");
    if (m) setForm((f) => ({ ...f, selected: m.split(",") as Method[] }));
    if (fromCase) {
      const c = cases.find((x) => x.id === fromCase);
      if (c) {
        const city = findCityByLatLng(c.lat, c.lng);
        setForm((f) => ({
          ...f,
          year: c.year, month: c.month, day: c.day,
          hour: c.hour, minute: c.minute,
          gender: c.gender,
          city: city?.name || f.city,
        }));
      }
    }
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
        // 加载历史后跳到末步, 方便改一两个参数就重排
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
  }, [params, cases]);

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
  const recommendedSet = new Set(recommendedIds);
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

    // Check if selected methods benefit from multi-compute with cross-validation
    const validationMethods = ["bazi_v2", "bazi", "ziwei", "western"];
    const hasValidationEligible = form.selected.filter((m) => validationMethods.includes(m)).length >= 2;

    try {
      let charts: Record<string, any>;
      let enhancedData: Record<string, any> | undefined;

      if (hasValidationEligible) {
        // Use the new multi-compute endpoint with cross-validation
        const result = await computeMultiWithValidation(
          form.selected as Method[],
          birth,
          form.subject,
          true, // do_validate
        );
        charts = result.charts || {};
        enhancedData = {
          cross_validation: result.cross_validation,
          peach_blossom: result.peach_blossom,
          relationship_timing: result.relationship_timing,
          fate_modification: result.fate_modification,
        };
      } else {
        // Fall back to parallel single-method calls
        charts = await computeChartMulti(form.selected as Method[], birth, {
          subject: form.subject,
          modeByMethod: form.modeByMethod,
          spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
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
      // If multi endpoint fails, fall back to old approach
      if (hasValidationEligible && err.message?.includes("422")) {
        try {
          const charts = await computeChartMulti(form.selected as Method[], birth, {
            subject: form.subject,
            modeByMethod: form.modeByMethod,
            spread: form.selected.includes("tarot") ? form.tarotSpread : undefined,
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
      {/* 星辰装饰 */}
      <div className="absolute right-0 top-0 opacity-[0.08] pointer-events-none" aria-hidden>
        <StarArray count={5} size={16} />
      </div>

      {/* 步骤 panel 切换: 每次变化用 reveal-up 重新入场 */}
      <Reveal key={step.key} className="">
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
            recommendedSet={recommendedSet}
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
      </Reveal>

      {error && (
        <div className="p-3 rounded text-sm reveal-up" style={{ background: "rgba(200,85,61,0.10)", color: COLOR.danger, border: "1px solid rgba(200,85,61,0.35)" }}>
          {error}
        </div>
      )}

      {/* 底部: 上一步 / 下一步 或 排盘 */}
      <div className="sticky bottom-0 -mx-4 sm:-mx-6 px-4 sm:px-6 py-3 backdrop-blur-md flex items-center justify-between gap-3"
        style={{ background: "rgba(8,10,15,0.78)", borderTop: "1px solid var(--line)" }}>
        <div className="flex items-center gap-2 text-xs" style={{ color: COLOR.muted }}>
          {submitting ? (
            <>
              <ProgressArc value={0.4} size={28} />
              <span>{t("cast.submitting")}</span>
            </>
          ) : (
            <>
              <span>{lang === "zh" ? "当前选" : "Selected"} <span style={{ color: COLOR.goldBright }}>{form.selected.length}</span> {lang === "zh" ? "法" : "methods"}</span>
              <span>·</span>
              <span>{subjectInfo.label}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className="btn-ghost tap" onClick={() => setForm(DEFAULT)}>{t("cast.reset")}</button>
          {stepIdx > 0 && (
            <button type="button" className="btn-ghost tap" onClick={goPrev}>{t("cast.prev")}</button>
          )}
          {stepIdx < STEPS.length - 1 ? (
            <button type="button" className="btn-primary gold-sweep-host" disabled={!canNext} onClick={goNext}>
              {t("cast.next")}
            </button>
          ) : (
            <button type="submit" className="btn-primary gold-sweep-host" disabled={submitting || !canSubmit}>
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
              className="flex-1 min-w-0 text-left px-2 py-1.5 rounded transition tap"
              style={{
                color: active ? COLOR.goldBright : done ? COLOR.inkSoft : COLOR.muted,
                background: active ? "rgba(201,162,75,0.10)" : "transparent",
                border: `1px solid ${active ? COLOR.gold : done ? COLOR.line : "transparent"}`,
              }}>
              <div className="flex items-center gap-1.5">
                <span
                  className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] shrink-0"
                  style={{
                    background: done ? COLOR.jade : active ? COLOR.gold : "rgba(255,255,255,0.06)",
                    color: done || active ? COLOR.bgDeep : COLOR.muted,
                    border: `1px solid ${done ? COLOR.jade : active ? COLOR.gold : COLOR.line}`,
                  }}
                >
                  {done ? "✓" : i + 1}
                </span>
                <span className="text-xs font-display truncate">{s.label}</span>
              </div>
              <div className="text-[10px] mt-0.5 truncate" style={{ color: COLOR.muted }}>{s.hint}</div>
            </button>
          );
        })}
      </div>
      {/* 进度条 */}
      <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--line-soft)" }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.round(pct * 100)}%`,
            background: "linear-gradient(90deg, var(--gold-dim), var(--gold-bright))",
            transition: "width 0.5s cubic-bezier(0.2, 0.7, 0.2, 1)",
          }}
        />
      </div>
    </div>
  );
}

// === Step 1: 意图 ===
function StepSubject({ form, chooseSubject }: { form: FormState; chooseSubject: (s: Subject) => void }) {
  const { t, lang } = useI18n();
  return (
    <section className="card card-highlight space-y-3">
      <header>
        <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{t("cast.ask.subject")}</h2>
        <p className="text-xs mt-1" style={{ color: COLOR.muted }}>{t("cast.ask.subject.desc")}</p>
      </header>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 reveal-stagger">
        {SUBJECTS.map((s) => {
          const on = form.subject === s.key;
          return (
            <button key={s.key} type="button" onClick={() => chooseSubject(s.key)}
              className="p-3 rounded border text-left transition lift-on-hover"
              style={{
                borderColor: on ? COLOR.gold : COLOR.line,
                background: on ? "rgba(201,162,75,0.08)" : "rgba(255,255,255,0.02)",
                boxShadow: on ? "0 0 0 1px var(--gold)" : "none",
              }}>
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold flex items-center gap-1.5" style={{ color: on ? COLOR.goldBright : COLOR.ink }}>
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full"
                    style={{ background: on ? COLOR.goldBright : COLOR.muted, boxShadow: on ? `0 0 8px ${COLOR.gold}` : "none" }}
                  />
                  {s.label}
                </div>
                <span className="text-[9px] opacity-60" style={{ color: COLOR.muted }}>{t("cast.step.subject")}</span>
              </div>
              <div className="text-xs mt-1.5 leading-snug" style={{ color: COLOR.muted }}>{s.desc}</div>
              {on && <div className="text-[10px] mt-1.5" style={{ color: COLOR.jade }}>{lang === "zh" ? "默认推惹" : "Recommended"} {s.methods.slice(0, 2).join(" · ")} …</div>}
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
    <section className="card card-highlight space-y-3">
      <header>
        <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{t("cast.birth.title")}</h2>
        <p className="text-xs mt-1" style={{ color: COLOR.muted }}>{t("cast.birth.desc")}</p>
      </header>
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {(["year", "month", "day", "hour", "minute"] as const).map((key) => (
          <div key={key}>
            <label className="label">{{ year: t("cast.birth.year"), month: t("cast.birth.month"), day: t("cast.birth.day"), hour: t("cast.birth.hour"), minute: t("cast.birth.minute") }[key]}</label>
            <input className="input" type="number" value={form[key]} onChange={(e) => setForm({ ...form, [key]: parseInt(e.target.value, 10) || 0 })} />
          </div>
        ))}
        <div>
          <label className="label">{t("cast.birth.gender")}</label>
          <select className="input" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value as any })}>
            <option value="male">{t("cast.gender.male")}</option>
            <option value="female">{t("cast.gender.female")}</option>
            <option value="unspecified">{t("cast.gender.unspec")}</option>
          </select>
        </div>
      </div>
      <div className="mt-1">
        <label className="label">{t("cast.birth.city")}</label>
        <select className="input max-w-md" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
          {CITY_REGIONS.map((r) => (
            <optgroup key={r.key} label={r.label}>
              {CITY_PRESETS.filter((c) => c.region === r.key).map((c) => (
                <option key={`${c.province || c.region}-${c.name}`} value={c.name}>{cityOptionLabel(c)}</option>
              ))}
            </optgroup>
          ))}
        </select>
        {cityInfo && (
          <div className="text-[10px] mt-1 inline-flex items-center gap-2 px-2 py-1 rounded"
            style={{ color: COLOR.muted, background: "rgba(255,255,255,0.03)", border: "1px solid var(--line-soft)" }}>
            <span style={{ color: COLOR.jade }}>●</span>
            {cityInfo.name} · {cityInfo.lat.toFixed(2)}°N, {cityInfo.lng.toFixed(2)}°E · {cityInfo.tz}
          </div>
        )}
      </div>
    </section>
  );
}

// === Step 3: 术数 ===
function StepMethods({
  form, subjectInfo, orderedMethods, recommendedSet, toggle, showMore, setShowMore,
}: {
  form: FormState;
  subjectInfo: typeof SUBJECTS[number];
  orderedMethods: MethodMeta[];
  recommendedSet: Set<string>;
  toggle: (m: Method) => void;
  showMore: boolean;
  setShowMore: (v: boolean | ((p: boolean) => boolean)) => void;
}) {
  const { t, lang } = useI18n();
  return (
    <section className="card card-highlight space-y-3">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{t("cast.methods.title")}</h2>
          <p className="text-xs mt-1" style={{ color: COLOR.muted }}>{lang === "zh" ? `已按「${subjectInfo.label}」默认推惹前 4 法,点按复选 / 取消。` : `Default 4 methods recommended for "${subjectInfo.label}". Click to toggle.`}</p>
        </div>
        <span className="text-[10px] inline-flex items-center gap-1 px-2 py-1 rounded" style={{ background: "rgba(91,141,239,0.08)", color: COLOR.azure, border: "1px solid rgba(91,141,239,0.30)" }}>
          {subjectInfo.label} · {subjectInfo.desc}
        </span>
      </header>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 reveal-stagger">
        {orderedMethods.filter((m) => recommendedSet.has(m.id)).map((m) => {
          const on = form.selected.includes(m.id);
          const plain = METHOD_PLAIN[m.id];
          return (
            <MethodTile key={m.id} m={m} plain={plain} on={on} toggle={toggle} modeByMethod={form.modeByMethod} />
          );
        })}
      </div>
      {orderedMethods.filter((m) => !recommendedSet.has(m.id)).length > 0 && (
        <>
          <button type="button" onClick={() => setShowMore((v) => !v)}
            className="text-xs flex items-center gap-1 tap"
            style={{ color: COLOR.gold }}>
            <span className="inline-block transition-transform" style={{ transform: showMore ? "rotate(90deg)" : "none" }}>▶</span>
            {showMore ? t("cast.methods.less") : `${t("cast.methods.more")} (${orderedMethods.filter((m) => !recommendedSet.has(m.id)).length})`}
          </button>
          {showMore && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 reveal-stagger">
              {orderedMethods.filter((m) => !recommendedSet.has(m.id)).map((m) => {
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
      className="p-3 rounded border text-left lift-on-hover tap relative overflow-hidden"
      style={{
        borderColor: on ? COLOR.gold : COLOR.line,
        background: on ? "rgba(201,162,75,0.08)" : "rgba(255,255,255,0.02)",
        boxShadow: on ? "0 0 0 1px var(--gold)" : "none",
      }}>
      <div className="flex items-center justify-between mb-1">
        <div className="text-sm font-semibold" style={{ color: on ? COLOR.goldBright : COLOR.ink }}>{m.name_zh}</div>
        <span className="inline-block w-2 h-2 rounded-full" style={{
          background: on ? COLOR.jade : "rgba(255,255,255,0.10)",
          boxShadow: on ? `0 0 8px ${COLOR.jade}` : "none",
        }} />
      </div>
      <div className="text-xs leading-snug" style={{ color: COLOR.muted }}>{plain?.tagline}</div>
      {on && (
        <div className="text-[10px] mt-1.5" style={{ color: COLOR.jade }}>
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
        <section className="card card-highlight space-y-4">
          <header>
            <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{t("cast.params.title")}</h2>
            <p className="text-xs mt-1" style={{ color: COLOR.muted }}>{t("cast.params.desc")}</p>
          </header>
          {showTieban && (
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="label">{lang === "zh" ? "父生肖 (可选·用于条文校验)" : "Father Zodiac (optional)"}</label>
                <select className="input" value={form.fatherZodiac} onChange={(e) => setForm({ ...form, fatherZodiac: e.target.value })}>
                  <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
                  {["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"].map((z) => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">{lang === "zh" ? "母生肖 (可选·用于条文校验)" : "Mother Zodiac (optional)"}</label>
                <select className="input" value={form.motherZodiac} onChange={(e) => setForm({ ...form, motherZodiac: e.target.value })}>
                  <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
                  {["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"].map((z) => (
                    <option key={z} value={z}>{z}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
          {showTarot && (
            <div>
              <label className="label">{lang === "zh" ? "塔罗牌阵" : "Tarot Spread"}</label>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 reveal-stagger">
                {TAROT_SPREADS.map((sp) => {
                  const on = form.tarotSpread === sp.code;
                  const recommended = sp.subjects.includes(form.subject);
                  return (
                    <button key={sp.code} type="button" onClick={() => setForm({ ...form, tarotSpread: sp.code })}
                      className="p-3 rounded border text-left lift-on-hover tap"
                      style={{
                        borderColor: on ? COLOR.gold : recommended ? `${COLOR.jade}80` : COLOR.line,
                        background: on ? "rgba(201,162,75,0.08)" : "rgba(255,255,255,0.02)",
                        boxShadow: on ? "0 0 0 1px var(--gold)" : "none",
                      }}>
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-semibold" style={{ color: on ? COLOR.goldBright : COLOR.ink }}>{sp.label}</div>
                        {recommended && !on && <span className="text-[9px]" style={{ color: COLOR.jade }}>{lang === "zh" ? "推荐" : "Rec"}</span>}
                      </div>
                      <div className="text-xs mt-1" style={{ color: COLOR.muted }}>{sp.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {showSitting && (
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="label">{lang === "zh" ? "坐山/门向代表方位" : "Sitting/Facing Direction"}</label>
                <select className="input" value={form.sittingDir} onChange={(e) => setForm({ ...form, sittingDir: e.target.value })}>
                  {DIRECTIONS_8.map((d) => <option key={d.code} value={d.code}>{d.code} · {d.sans}山</option>)}
                </select>
              </div>
              <div>
                <label className="label">{lang === "zh" ? "建造/入伙年份" : "Construction Year"}</label>
                <input className="input" type="number" value={form.constructionYear} onChange={(e) => setForm({ ...form, constructionYear: parseInt(e.target.value, 10) || form.year })} />
              </div>
            </div>
          )}
          {showSeed && (
            <div>
              <label className="label">{lang === "zh" ? "固定种子" : "Fixed Seed"}</label>
              <div className="flex gap-3 items-center flex-wrap">
                <label className="text-sm flex items-center gap-2 tap">
                  <input type="checkbox" checked={form.fixSeed} onChange={(e) => setForm({ ...form, fixSeed: e.target.checked })} />
                  {lang === "zh" ? "固定本次随机/数字起法(可复现)" : "Lock random seed (reproducible)"}
                </label>
                {form.fixSeed && <input className="input max-w-[160px]" value={form.seed} onChange={(e) => setForm({ ...form, seed: e.target.value })} placeholder="例如 42" />}
              </div>
            </div>
          )}
        </section>
      )}
      {!hasAnyParam && (
        <section className="card card-highlight text-xs" style={{ color: COLOR.muted }}>
          {lang === "zh" ? "所选术数不需要额外起法参数,直接提问即可。" : "Selected methods need no extra parameters — just ask your question."}
        </section>
      )}

      <section className="card card-highlight space-y-2">
        <header>
          <label className="label">{t("cast.question.label")}</label>
        </header>
        <textarea className="input min-h-[100px]" value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
          placeholder={sample} />
        <div className="flex items-center justify-between gap-2">
          <div className="text-[10px]" style={{ color: COLOR.muted }}>{t("cast.question.help")}</div>
          <div className="text-[10px]" style={{ color: form.question.length > 200 ? COLOR.goldBright : COLOR.muted }}>
            {form.question.length}/400
          </div>
        </div>
      </section>
    </div>
  );
}
