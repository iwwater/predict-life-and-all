/** ChengguPage — 称骨独立排盘页（基础生辰，无经纬度） */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG } from "../../lib/method-inputs";
import { BirthForm, type BirthState, type CityInfo } from "../../components/forms/BirthForm";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";
import { CITY_PRESETS } from "../../lib/cities";

export function ChengguPage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.chenggu;
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add); const inBasket = useBasket((s) => s.has("chenggu"));
  const cityInfo = useMemo<CityInfo>(() => { const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0]; return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz }; }, [birth.city]);

  function buildBirth(): Birth {
    return { year: birth.year, month: birth.month, day: birth.day, hour: birth.hour, minute: birth.minute, gender: birth.gender, calendar: "gregorian", lat: null, lng: null, tz: "Asia/Shanghai" };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({ method: "chenggu", birth: b, options: { mode: cfg.defaultMode } });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth: b, methods: ["chenggu"], charts: { chenggu: chart }, subject: "self_life" as any, modeByMethod: { chenggu: cfg.defaultMode }, tags: deriveTags(["chenggu"], "self_life"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth: b, charts: { chenggu: chart }, methods: ["chenggu"] }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [birth, navigate]);

  function addToBasket() { basketAdd({ method: "chenggu", chart: null, birth: buildBirth(), addedAt: Date.now() }); }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.chenggu.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.chenggu.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.birth")}</p>
        <BirthForm showFields={cfg.birthFields} birth={birth} cityInfo={cityInfo} onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "称骨算" : "Weigh Bones"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
    </form>
  );
}
