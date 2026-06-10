/** BazhaiPage — 八宅明镜独立排盘页（生辰 + 坐向） */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG } from "../../lib/method-inputs";
import { BirthForm, type BirthState, type CityInfo } from "../../components/forms/BirthForm";
import { DirectionPicker } from "../../components/forms/DirectionPicker";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";
import { CITY_PRESETS } from "../../lib/cities";

export function BazhaiPage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.bazhai;
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [sittingDir, setSittingDir] = useState("正东"); const [constructionYear, setConstructionYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add); const inBasket = useBasket((s) => s.has("bazhai"));
  const cityInfo = useMemo<CityInfo>(() => { const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0]; return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz }; }, [birth.city]);

  function buildBirth(): Birth {
    return { year: birth.year, month: birth.month, day: birth.day, hour: birth.hour, minute: birth.minute, gender: birth.gender, calendar: "gregorian", lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({ method: "bazhai", birth: b, options: { mode: cfg.defaultMode, sitting: sittingDir, construction_year: constructionYear } });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth: b, methods: ["bazhai"], charts: { bazhai: chart }, subject: "home_fengshui" as any, modeByMethod: { bazhai: cfg.defaultMode }, tags: deriveTags(["bazhai"], "home_fengshui"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth: b, charts: { bazhai: chart }, methods: ["bazhai"] }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [birth, sittingDir, constructionYear, navigate]);

  function addToBasket() { basketAdd({ method: "bazhai", chart: null, birth: buildBirth(), addedAt: Date.now() }); }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.bazhai.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.bazhai.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.birth")}</p>
        <BirthForm showFields={cfg.birthFields} birth={birth} cityInfo={cityInfo} onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
        <DirectionPicker sittingDir={sittingDir} constructionYear={constructionYear} onSittingChange={setSittingDir} onYearChange={setConstructionYear} showYear />
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "排八宅盘" : "Cast Bazhai"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
    </form>
  );
}
