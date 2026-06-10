/** VedicPage — 吠陀占星独立排盘页 */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG } from "../../lib/method-inputs";
import { BirthForm, type BirthState, type CityInfo } from "../../components/forms/BirthForm";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";
import { CITY_PRESETS } from "../../lib/cities";

export function VedicPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.vedic;
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [mode, setMode] = useState(cfg.defaultMode);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("vedic"));
  const cityInfo = useMemo<CityInfo>(() => { const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0]; return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz }; }, [birth.city]);

  function buildBirth(): Birth {
    return { year: birth.year, month: birth.month, day: birth.day, hour: birth.hour, minute: birth.minute, gender: birth.gender, calendar: "gregorian", lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({ method: "vedic", birth: b, options: { mode, question: question || undefined } });
      storeAndNavigate("vedic", b, [chart]);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [birth, mode, question, navigate]);

  function storeAndNavigate(method: any, b: Birth, charts: ChartResult[]) {
    const hid = crypto.randomUUID();
    useHistory.getState().add({ id: hid, ts: Date.now(), birth: b, methods: [method], charts: { [method]: charts[0] }, question: question || undefined, subject: "self_life" as any, modeByMethod: { [method]: mode }, tags: deriveTags([method], "self_life"), favorite: false, reflection: null });
    sessionStorage.setItem("mystic:result_id", hid);
    sessionStorage.setItem("mystic:result", JSON.stringify({ birth: b, charts: { [method]: charts[0] }, methods: [method], question }));
    navigate(`/result?ts=${Date.now()}`);
  }

  function addToBasket() { basketAdd({ method: "vedic", chart: null, birth: buildBirth(), addedAt: Date.now() }); }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.vedic.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.vedic.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.birth")}</p>
        <BirthForm showFields={cfg.birthFields} birth={birth} cityInfo={cityInfo} onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
          <div className="flex gap-1.5">{cfg.availableModes.map((m) => (<button key={m.value} type="button" onClick={() => setMode(m.value)} className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>{m.label}</button>))}</div>
        </div>
        <QuestionInput value={question} onChange={setQuestion} />
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "排吠陀盘" : "Cast Vedic"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
    </form>
  );
}
