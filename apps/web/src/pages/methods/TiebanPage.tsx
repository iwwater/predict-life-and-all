/** TiebanPage — 铁板神数独立排盘页 */
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
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

export function TiebanPage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.tieban;
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [fatherZodiac, setFatherZodiac] = useState(""); const [motherZodiac, setMotherZodiac] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add); const inBasket = useBasket((s) => s.has("tieban"));
  const cityInfo = useMemo<CityInfo>(() => { const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0]; return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz }; }, [birth.city]);
  const ZODIACS = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"];

  function buildBirth(): Birth {
    return { year: birth.year, month: birth.month, day: birth.day, hour: birth.hour, minute: birth.minute, gender: birth.gender, calendar: "gregorian", lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({ method: "tieban", birth: b, options: { mode: cfg.defaultMode, method_inputs: { father_zodiac: fatherZodiac || undefined, mother_zodiac: motherZodiac || undefined } } });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth: b, methods: ["tieban"], charts: { tieban: chart }, subject: "self_life" as any, modeByMethod: { tieban: cfg.defaultMode }, tags: deriveTags(["tieban"], "self_life"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth: b, charts: { tieban: chart }, methods: ["tieban"] }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [birth, fatherZodiac, motherZodiac, navigate]);

  function addToBasket() { basketAdd({ method: "tieban", chart: null, birth: buildBirth(), addedAt: Date.now() }); }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.tieban.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.tieban.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.birth")}</p>
        <BirthForm showFields={cfg.birthFields} birth={birth} cityInfo={cityInfo} onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="paper-label">{t("form.zodiac.father")}</label>
            <select className="paper-input" value={fatherZodiac} onChange={(e) => setFatherZodiac(e.target.value)}>
              <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
              {ZODIACS.map((z) => <option key={z} value={z}>{z}</option>)}
            </select>
          </div>
          <div>
            <label className="paper-label">{t("form.zodiac.mother")}</label>
            <select className="paper-input" value={motherZodiac} onChange={(e) => setMotherZodiac(e.target.value)}>
              <option value="">{lang === "zh" ? "不指定" : "Unspecified"}</option>
              {ZODIACS.map((z) => <option key={z} value={z}>{z}</option>)}
            </select>
          </div>
        </div>
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "铁板考刻" : "Cast Tie Ban"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
      <MethodSourcesPanel method="tieban" />
    </form>
  );
}
