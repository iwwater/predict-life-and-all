// 合盘页: 双人出生输入 → 选择方法 → 查看合盘报告（「古籍×仪器」纸墨风格）
import { useState, useMemo } from "react";
import { computeCompatibility, computeMultiCompatibility } from "../lib/api";
import type { Birth, Method } from "../lib/types";
import { CITY_PRESETS, CITY_REGIONS, cityOptionLabel } from "../lib/cities";
import { CompatibilityReport } from "../components/CompatibilityReport";
import { useI18n } from "../lib/i18n";

interface PersonForm {
  name: string;
  year: number; month: number; day: number;
  hour: number; minute: number;
  gender: "male" | "female" | "unspecified";
  city: string;
}

const DEFAULT_PERSON: PersonForm = {
  name: "", year: 1990, month: 6, day: 15, hour: 12, minute: 0, gender: "female", city: "上海",
};

export function Compatibility() {
  const { t, lang } = useI18n();
  const [stepIdx, setStepIdx] = useState(0);
  const [personA, setPersonA] = useState<PersonForm>({ ...DEFAULT_PERSON, name: "Ta" });
  const [personB, setPersonB] = useState<PersonForm>({ ...DEFAULT_PERSON, name: "Ta", gender: "male" });
  const [selectedMethod, setSelectedMethod] = useState("bazi_v2");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const personACity = useMemo(() => CITY_PRESETS.find((x) => x.name === personA.city) || CITY_PRESETS[0], [personA.city]);
  const personBCity = useMemo(() => CITY_PRESETS.find((x) => x.name === personB.city) || CITY_PRESETS[0], [personB.city]);

  function birthFromPerson(p: PersonForm): Birth {
    return {
      year: p.year, month: p.month, day: p.day, hour: p.hour, minute: p.minute,
      gender: p.gender, calendar: "gregorian",
      lat: CITY_PRESETS.find((c) => c.name === p.city)?.lat ?? 31.23,
      lng: CITY_PRESETS.find((c) => c.name === p.city)?.lng ?? 121.47,
      tz: CITY_PRESETS.find((c) => c.name === p.city)?.tz ?? "Asia/Shanghai",
      is_leap_month: false,
    };
  }

  async function handleCompute() {
    setError(null); setSubmitting(true);
    try {
      const b1 = birthFromPerson(personA); const b2 = birthFromPerson(personB);
      if (selectedMethod === "both") {
        const r = await computeMultiCompatibility(b1, b2, ["bazi_v2", "western"]);
        setResult(r);
      } else {
        const r = await computeCompatibility(b1, b2, selectedMethod);
        setResult(r);
      }
      setStepIdx(3);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setSubmitting(false); }
  }

  const steps = [
    { key: "personA" as const, label: lang === "zh" ? "Ta" : "A", hint: lang === "zh" ? "第一位出生信息" : "First person" },
    { key: "personB" as const, label: lang === "zh" ? "Ta" : "B", hint: lang === "zh" ? "第二位出生信息" : "Second person" },
    { key: "method" as const, label: lang === "zh" ? "方法" : "Method", hint: lang === "zh" ? "选择合盘方法" : "Select method" },
    { key: "result" as const, label: lang === "zh" ? "合盘" : "Result", hint: lang === "zh" ? "查看结果" : "View results" },
  ];

  const goNext = () => setStepIdx((i) => Math.min(steps.length - 1, i + 1));
  const goPrev = () => setStepIdx((i) => Math.max(0, i - 1));
  const displaySteps = result ? steps : steps.filter((s) => s.key !== "result");
  const adjustedIdx = result ? stepIdx : Math.min(stepIdx, 2);

  return (
    <div className="space-y-5">
      {/* Stepper */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          {displaySteps.map((s, i) => {
            const done = i < adjustedIdx || (i === 3 && !!result);
            const active = i === adjustedIdx;
            return (
              <button key={s.key} type="button" onClick={() => {
                if (s.key === "result" && !result) return;
                const origIdx = result ? i : i;
                setStepIdx(origIdx);
              }}
                className="flex-1 min-w-0 text-left px-2 py-1.5 transition-colors"
                style={{
                  color: active ? "var(--cinnabar)" : done ? "var(--ink)" : "var(--ink-soft)",
                  border: `1px solid ${active ? "var(--cinnabar)" : done ? "var(--rule)" : "transparent"}`,
                  borderRadius: "4px",
                  fontFamily: "'Noto Serif SC', serif",
                }}>
                <div className="flex items-center gap-1.5">
                  <span className="inline-flex items-center justify-center shrink-0" style={{
                    width: "20px", height: "20px", borderRadius: "50%", fontSize: "0.62rem",
                    color: done || active ? "#fff" : "var(--ink-soft)",
                    background: done ? "var(--verdigris)" : active ? "var(--cinnabar)" : "var(--paper)",
                    border: `1px solid ${done ? "var(--verdigris)" : active ? "var(--cinnabar)" : "var(--rule)"}`,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>{done ? "✓" : i + 1}</span>
                  <span style={{ fontSize: "0.78rem", fontWeight: 600 }} className="truncate">{s.label}</span>
                </div>
                <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.15rem" }} className="truncate">{s.hint}</div>
              </button>
            );
          })}
        </div>
        <div className="paper-progress"><div className="paper-progress-bar" style={{ width: `${result ? 100 : Math.round(((adjustedIdx + 1) / 3) * 100)}%` }} /></div>
      </div>

      {/* Step content */}
      <div key={steps[stepIdx].key} className="animate-fade-in">
        {steps[stepIdx].key === "personA" && <PersonCard title="第一位 · Ta" person={personA} setPerson={setPersonA} cityInfo={personACity} />}
        {steps[stepIdx].key === "personB" && <PersonCard title="第二位 · Ta" person={personB} setPerson={setPersonB} cityInfo={personBCity} />}
        {steps[stepIdx].key === "method" && <MethodSelector selected={selectedMethod} onSelect={setSelectedMethod} />}
        {steps[stepIdx].key === "result" && result && (
          <CompatibilityReport result={result} personAName={personA.name || "A"} personBName={personB.name || "B"} />
        )}
      </div>

      {steps[stepIdx].key === "result" && !result && (
        <div className="paper-empty" style={{ padding: "2rem 0" }}>
          <p style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>{t("compat.noResult")}</p>
          <p style={{ fontSize: "0.75rem" }}>{t("compat.noResult.hint")}</p>
        </div>
      )}

      {error && <div className="paper-error">{error}</div>}

      {/* Footer nav */}
      <div className="sticky bottom-0 -mx-4 sm:-mx-6 px-4 sm:px-6 py-3 flex items-center justify-between gap-3"
        style={{ background: "var(--paper)", borderTop: "1px solid var(--rule)" }}>
        <div className="flex items-center gap-2" style={{ fontSize: "0.75rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
          {submitting ? (
            <span style={{ color: "var(--cinnabar)" }}>… {t("compat.computing")}</span>
          ) : (
            <>
              <span style={{ color: "var(--ink)", fontWeight: 600 }}>{personA.name || "A"}</span>
              <span>×</span>
              <span style={{ color: "var(--ink)", fontWeight: 600 }}>{personB.name || "B"}</span>
              <span>·</span>
              <span>{selectedMethod === "bazi_v2" ? t("compat.bazi") : selectedMethod === "western" ? t("compat.western") : t("compat.both")}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {stepIdx > 0 && steps[stepIdx].key !== "result" && (
            <button type="button" className="paper-btn-ghost" onClick={goPrev}>{t("cast.prev")}</button>
          )}
          {steps[stepIdx].key === "result" ? (
            <button type="button" className="paper-btn" onClick={() => { setResult(null); setStepIdx(0); }}>{t("compat.retry")}</button>
          ) : stepIdx < 2 ? (
            <button type="button" className="paper-btn" onClick={goNext}>{t("cast.next")}</button>
          ) : (
            <button type="button" className="paper-btn" disabled={submitting} onClick={handleCompute}>
              {submitting ? t("compat.computing") : t("compat.compute")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function PersonCard({ title, person, setPerson, cityInfo }: {
  title: string; person: PersonForm; setPerson: React.Dispatch<React.SetStateAction<PersonForm>>; cityInfo: typeof CITY_PRESETS[0];
}) {
  const { t, lang } = useI18n();
  return (
    <section className="paper-frame space-y-3">
      <h2 className="paper-title"><span className="stamp" />{title}</h2>
      <div>
        <label className="paper-label">{lang === "zh" ? "姓名/称呼" : "Name"}</label>
        <input className="paper-input" style={{ maxWidth: "16rem" }} type="text" value={person.name}
          onChange={(e) => setPerson({ ...person, name: e.target.value })}
          placeholder={lang === "zh" ? "例如：小明" : "e.g. John"} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {(["year","month","day","hour","minute"] as const).map((key) => (
          <div key={key}>
            <label className="paper-label">{{ year: t("cast.birth.year"), month: t("cast.birth.month"), day: t("cast.birth.day"), hour: t("cast.birth.hour"), minute: t("cast.birth.minute") }[key]}</label>
            <input className="paper-input" type="number" value={person[key]}
              onChange={(e) => setPerson({ ...person, [key]: parseInt(e.target.value, 10) || 0 })} />
          </div>
        ))}
        <div>
          <label className="paper-label">{t("cast.birth.gender")}</label>
          <select className="paper-input" value={person.gender} onChange={(e) => setPerson({ ...person, gender: e.target.value as any })}>
            <option value="male">{t("cast.gender.male")}</option>
            <option value="female">{t("cast.gender.female")}</option>
            <option value="unspecified">{t("cast.gender.unspec")}</option>
          </select>
        </div>
      </div>
      <div>
        <label className="paper-label">{t("cast.birth.city")}</label>
        <select className="paper-input" style={{ maxWidth: "20rem" }} value={person.city} onChange={(e) => setPerson({ ...person, city: e.target.value })}>
          {CITY_REGIONS.map((r) => (
            <optgroup key={r.key} label={r.label}>
              {CITY_PRESETS.filter((c) => c.region === r.key).map((c) => (
                <option key={`${c.province || c.region}-${c.name}`} value={c.name}>{cityOptionLabel(c)}</option>
              ))}
            </optgroup>
          ))}
        </select>
        {cityInfo && (
          <div className="paper-grid-cell" style={{ marginTop: "0.3rem", padding: "0.3rem 0.6rem", fontSize: "0.65rem", color: "var(--ink-soft)", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ color: "var(--verdigris)", fontWeight: 700 }}>●</span>
            {cityInfo.name} · {cityInfo.lat.toFixed(2)}°N, {cityInfo.lng.toFixed(2)}°E · {cityInfo.tz}
          </div>
        )}
      </div>
    </section>
  );
}

function MethodSelector({ selected, onSelect }: { selected: string; onSelect: (m: string) => void }) {
  const { t, lang } = useI18n();
  const methods = [
    { id: "bazi_v2", name: t("compat.bazi"), desc: t("compat.bazi.desc"), school: "east" as const },
    { id: "western", name: t("compat.western"), desc: t("compat.western.desc"), school: "west" as const },
    { id: "both", name: t("compat.both"), desc: t("compat.both.desc"), school: "both" as const },
  ];
  return (
    <section className="paper-frame space-y-3">
      <h2 className="paper-title"><span className="stamp" />{lang === "zh" ? "选择合盘方法" : "Select Synastry Method"}</h2>
      <div className="grid sm:grid-cols-3 gap-3">
        {methods.map((m) => {
          const on = selected === m.id;
          return (
            <button key={m.id} type="button" onClick={() => onSelect(m.id)}
              className="paper-grid-cell text-left" style={{
                padding: "0.75rem", borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
              }}>
              <div style={{ fontSize: "0.88rem", fontWeight: 700, color: on ? "var(--cinnabar)" : "var(--ink)", fontFamily: "'Noto Serif SC', serif", marginBottom: "0.25rem" }}>{m.name}</div>
              <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.5 }}>{m.desc}</div>
              {on && <div style={{ marginTop: "0.4rem", fontSize: "0.65rem", color: "var(--verdigris)" }}>✓ {lang === "zh" ? "已选择" : "Selected"}</div>}
            </button>
          );
        })}
      </div>
    </section>
  );
}
