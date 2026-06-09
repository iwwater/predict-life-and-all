// 合盘页: 双人出生输入 → 选择方法 → 查看合盘报告
import { useState, useMemo } from "react";
import { computeCompatibility, computeMultiCompatibility } from "../lib/api";
import type { Birth, Method } from "../lib/types";
import { CITY_PRESETS, CITY_REGIONS, cityOptionLabel } from "../lib/cities";
import { COLOR } from "../components/ui";
import { Reveal } from "../components/Interactions";
import { CompatibilityReport } from "../components/CompatibilityReport";
import { YinYang, WuXingRing } from "../components/MysticElements";
import { useI18n } from "../lib/i18n";

interface PersonForm {
  name: string;
  year: number; month: number; day: number;
  hour: number; minute: number;
  gender: "male" | "female" | "unspecified";
  city: string;
}

const DEFAULT_PERSON: PersonForm = {
  name: "",
  year: 1990, month: 6, day: 15,
  hour: 12, minute: 0,
  gender: "female",
  city: "上海",
};

export function Compatibility() {
  const { t, lang } = useI18n();
  const STEPS = [
    { key: "personA" as const, label: t("compat.personA").split(" · ")[0] || "A", hint: lang === "zh" ? "第一位出生信息" : "First person's birth info" },
    { key: "personB" as const, label: t("compat.personB").split(" · ")[0] || "B", hint: lang === "zh" ? "第二位出生信息" : "Second person's birth info" },
    { key: "method" as const, label: lang === "zh" ? "方法" : "Method", hint: lang === "zh" ? "选择合盘方法" : "Select method" },
    { key: "result" as const, label: lang === "zh" ? "合盘" : "Synastry", hint: lang === "zh" ? "查看结果" : "View results" },
  ];
  const [stepIdx, setStepIdx] = useState(0);
  const [personA, setPersonA] = useState<PersonForm>({ ...DEFAULT_PERSON, name: "Ta" });
  const [personB, setPersonB] = useState<PersonForm>({ ...DEFAULT_PERSON, name: "Ta", gender: "male" });
  const [selectedMethod, setSelectedMethod] = useState("bazi_v2");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const COMPAT_METHODS = [
    { id: "bazi_v2", name: t("compat.bazi"), desc: t("compat.bazi.desc"), icon: "☯️", school: "east" },
    { id: "western", name: t("compat.western"), desc: t("compat.western.desc"), icon: "✨", school: "west" },
    { id: "both", name: t("compat.both"), desc: t("compat.both.desc"), icon: "🔮", school: "both" },
  ];

  const step = STEPS[stepIdx];
  const goNext = () => setStepIdx((i) => Math.min(STEPS.length - 1, i + 1));
  const goPrev = () => setStepIdx((i) => Math.max(0, i - 1));

  const personACity = useMemo(
    () => CITY_PRESETS.find((x) => x.name === personA.city) || CITY_PRESETS[0],
    [personA.city],
  );
  const personBCity = useMemo(
    () => CITY_PRESETS.find((x) => x.name === personB.city) || CITY_PRESETS[0],
    [personB.city],
  );

  function birthFromPerson(p: PersonForm): Birth {
    return {
      year: p.year, month: p.month, day: p.day,
      hour: p.hour, minute: p.minute,
      gender: p.gender,
      calendar: "gregorian",
      lat: CITY_PRESETS.find((c) => c.name === p.city)?.lat ?? 31.23,
      lng: CITY_PRESETS.find((c) => c.name === p.city)?.lng ?? 121.47,
      tz: CITY_PRESETS.find((c) => c.name === p.city)?.tz ?? "Asia/Shanghai",
      is_leap_month: false,
    };
  }

  async function handleCompute() {
    setError(null);
    setSubmitting(true);
    try {
      const b1 = birthFromPerson(personA);
      const b2 = birthFromPerson(personB);

      if (selectedMethod === "both") {
        const r = await computeMultiCompatibility(b1, b2, ["bazi_v2", "western"]);
        setResult(r);
      } else {
        const r = await computeCompatibility(b1, b2, selectedMethod);
        setResult(r);
      }
      setStepIdx(3); // jump to result step
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* 阴阳 + 五行环装饰 */}
      <div className="fixed right-8 bottom-8 pointer-events-none opacity-[0.05] z-0" aria-hidden>
        <YinYang size={100} />
      </div>
      <div className="fixed left-8 top-1/3 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <WuXingRing size={200} />
      </div>

      {/* Stepper */}
      <Stepper stepIdx={stepIdx} onJump={(i) => setStepIdx(i)} resultReady={!!result} />

      {/* Step content */}
      <Reveal key={step.key} className="">
        {step.key === "personA" && (
          <PersonCard
            title="第一位 · Ta"
            person={personA}
            setPerson={setPersonA}
            cityInfo={personACity}
          />
        )}
        {step.key === "personB" && (
          <PersonCard
            title="第二位 · Ta"
            person={personB}
            setPerson={setPersonB}
            cityInfo={personBCity}
          />
        )}
        {step.key === "method" && (
          <MethodSelector selected={selectedMethod} onSelect={setSelectedMethod} />
        )}
        {step.key === "result" && result && (
          <CompatibilityReport
            result={result}
            personAName={personA.name || "A"}
            personBName={personB.name || "B"}
          />
        )}
      </Reveal>

      {step.key === "result" && !result && (
        <div className="card text-center py-8" style={{ color: COLOR.muted }}>
          <p className="text-lg mb-2">{t("compat.noResult")}</p>
          <p className="text-xs">{t("compat.noResult.hint")}</p>
        </div>
      )}

      {error && (
        <div className="p-3 rounded text-sm reveal-up" style={{
          background: "rgba(200,85,61,0.10)", color: COLOR.danger,
          border: "1px solid rgba(200,85,61,0.35)",
        }}>
          {error}
        </div>
      )}

      {/* Footer nav */}
      <div className="sticky bottom-0 -mx-4 sm:-mx-6 px-4 sm:px-6 py-3 backdrop-blur-md flex items-center justify-between gap-3"
        style={{ background: "rgba(8,10,15,0.78)", borderTop: "1px solid var(--line)" }}>
        <div className="flex items-center gap-2 text-xs" style={{ color: COLOR.muted }}>
          {submitting ? (
            <span>⏳ {t("compat.computing")}</span>
          ) : (
            <>
              <span style={{ color: COLOR.goldBright }}>{personA.name || "A"}</span>
              <span>×</span>
              <span style={{ color: COLOR.goldBright }}>{personB.name || "B"}</span>
              <span>·</span>
              <span>
                {selectedMethod === "bazi_v2" ? t("compat.bazi") :
                 selectedMethod === "western" ? t("compat.western") : t("compat.both")}
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {stepIdx > 0 && step.key !== "result" && (
            <button type="button" className="btn-ghost tap" onClick={goPrev}>{t("cast.prev")}</button>
          )}
          {step.key === "result" ? (
            <button type="button" className="btn-primary gold-sweep-host" onClick={() => {
              setResult(null);
              setStepIdx(0);
            }}>
              {t("compat.retry")}
            </button>
          ) : stepIdx < 2 ? (
            <button type="button" className="btn-primary gold-sweep-host" onClick={goNext}>
              {t("cast.next")}
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary gold-sweep-host"
              disabled={submitting}
              onClick={handleCompute}
            >
              {submitting ? t("compat.computing") : t("compat.compute")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Stepper ──────────────────────────────────────────────────────────────
function Stepper({ stepIdx, onJump, resultReady }: {
  stepIdx: number;
  onJump: (i: number) => void;
  resultReady: boolean;
}) {
  const { t, lang } = useI18n();
  const steps = [
    { key: "personA", label: lang === "zh" ? "Ta" : "A", hint: lang === "zh" ? "第一位出生信息" : "First person's birth info" },
    { key: "personB", label: lang === "zh" ? "Ta" : "B", hint: lang === "zh" ? "第二位出生信息" : "Second person's birth info" },
    { key: "method", label: lang === "zh" ? "方法" : "Method", hint: lang === "zh" ? "选择合盘方法" : "Select method" },
    { key: "result", label: lang === "zh" ? "合盘" : "Result", hint: lang === "zh" ? "查看结果" : "View results" },
  ];
  const displaySteps = resultReady
    ? steps
    : steps.filter((s) => s.key !== "result");
  const adjustedIdx = resultReady ? stepIdx : Math.min(stepIdx, 2);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        {displaySteps.map((s, i) => {
          const done = i < adjustedIdx || (i === 3 && resultReady);
          const active = i === adjustedIdx;
          return (
            <button key={s.key} type="button" onClick={() => {
              if (s.key === "result" && !resultReady) return;
              onJump(i);
            }}
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
      <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--line-soft)" }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${resultReady ? 100 : Math.round(((adjustedIdx + 1) / 3) * 100)}%`,
            background: "linear-gradient(90deg, var(--gold-dim), var(--gold-bright))",
            transition: "width 0.5s cubic-bezier(0.2, 0.7, 0.2, 1)",
          }}
        />
      </div>
    </div>
  );
}

// ── Person Card ──────────────────────────────────────────────────────────
function PersonCard({ title, person, setPerson, cityInfo }: {
  title: string;
  person: PersonForm;
  setPerson: React.Dispatch<React.SetStateAction<PersonForm>>;
  cityInfo: typeof CITY_PRESETS[0];
}) {
  const { t, lang } = useI18n();
  return (
    <section className="card card-highlight space-y-3">
      <header>
        <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{title}</h2>
        <p className="text-xs mt-1" style={{ color: COLOR.muted }}>{t("cast.birth.desc")}</p>
      </header>

      <div className="mb-3">
        <label className="label">{lang === "zh" ? "姓名/称呼" : "Name/Nickname"}</label>
        <input
          className="input max-w-xs"
          type="text"
          value={person.name}
          onChange={(e) => setPerson({ ...person, name: e.target.value })}
          placeholder={lang === "zh" ? "例如：小明" : "e.g. John"}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {(["year", "month", "day", "hour", "minute"] as const).map((key) => (
          <div key={key}>
            <label className="label">{{ year: t("cast.birth.year"), month: t("cast.birth.month"), day: t("cast.birth.day"), hour: t("cast.birth.hour"), minute: t("cast.birth.minute") }[key]}</label>
            <input
              className="input"
              type="number"
              value={person[key]}
              onChange={(e) => setPerson({ ...person, [key]: parseInt(e.target.value, 10) || 0 })}
            />
          </div>
        ))}
        <div>
          <label className="label">{t("cast.birth.gender")}</label>
          <select className="input" value={person.gender} onChange={(e) => setPerson({ ...person, gender: e.target.value as any })}>
            <option value="male">{t("cast.gender.male")}</option>
            <option value="female">{t("cast.gender.female")}</option>
            <option value="unspecified">{t("cast.gender.unspec")}</option>
          </select>
        </div>
      </div>

      <div>
        <label className="label">{t("cast.birth.city")}</label>
        <select className="input max-w-md" value={person.city} onChange={(e) => setPerson({ ...person, city: e.target.value })}>
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

// ── Method Selector ──────────────────────────────────────────────────────
function MethodSelector({ selected, onSelect }: {
  selected: string;
  onSelect: (m: string) => void;
}) {
  const { t, lang } = useI18n();
  const methods = [
    { id: "bazi_v2", name: t("compat.bazi"), desc: t("compat.bazi.desc"), icon: "☯️", school: "east" },
    { id: "western", name: t("compat.western"), desc: t("compat.western.desc"), icon: "✨", school: "west" },
    { id: "both", name: t("compat.both"), desc: t("compat.both.desc"), icon: "🔮", school: "both" },
  ];
  return (
    <section className="card card-highlight space-y-3">
      <header>
        <h2 className="text-xl font-display" style={{ color: COLOR.goldBright }}>{lang === "zh" ? "选择合盘方法" : "Select Synastry Method"}</h2>
        <p className="text-xs mt-1" style={{ color: COLOR.muted }}>
          {t("compat.method.desc")}
        </p>
      </header>
      <div className="grid sm:grid-cols-3 gap-3">
        {methods.map((m) => {
          const on = selected === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onSelect(m.id)}
              className="p-4 rounded border text-left lift-on-hover tap relative overflow-hidden"
              style={{
                borderColor: on ? COLOR.gold : COLOR.line,
                background: on ? "rgba(201,162,75,0.08)" : "rgba(255,255,255,0.02)",
                boxShadow: on ? "0 0 0 1px var(--gold)" : "none",
              }}
            >
              <div className="text-2xl mb-2">{m.icon}</div>
              <div className="text-sm font-semibold mb-1" style={{ color: on ? COLOR.goldBright : COLOR.ink }}>
                {m.name}
              </div>
              <div className="text-xs leading-snug" style={{ color: COLOR.muted }}>{m.desc}</div>
              {on && (
                <div className="mt-2 text-[10px]" style={{ color: COLOR.jade }}>✓ {lang === "zh" ? "已选择" : "Selected"}</div>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
