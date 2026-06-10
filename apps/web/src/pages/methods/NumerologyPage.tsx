/** NumerologyPage — 生命灵数独立排盘页
 *  只需年月日 + 名字(可选)
 */
import { type FormEvent, useState, useCallback } from "react";
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

export function NumerologyPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.numerology;
  const [year, setYear] = useState(1990);
  const [month, setMonth] = useState(6);
  const [day, setDay] = useState(15);
  const [name, setName] = useState("");
  const [mode, setMode] = useState(cfg.defaultMode);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("numerology"));

  function buildBirth(): Birth {
    return {
      year, month, day, hour: 12, minute: 0,
      gender: "unspecified", calendar: "gregorian",
      lat: null, lng: null, tz: "Asia/Shanghai",
    };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({
        method: "numerology", birth: b,
        options: {
          mode,
          question: question || undefined,
          ...(name ? { name } : {}),
        },
      });
      storeAndNavigate("numerology", b, [chart]);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [year, month, day, name, mode, question, navigate]);

  function storeAndNavigate(method: any, b: Birth, charts: ChartResult[]) {
    const hid = crypto.randomUUID();
    useHistory.getState().add({
      id: hid, ts: Date.now(), birth: b, methods: [method],
      charts: { [method]: charts[0] },
      question: question || undefined,
      subject: "self_life" as any,
      modeByMethod: { [method]: mode },
      tags: deriveTags([method], "self_life"),
      favorite: false, reflection: null,
    });
    sessionStorage.setItem("mystic:result_id", hid);
    sessionStorage.setItem("mystic:result", JSON.stringify({
      birth: b, charts: { [method]: charts[0] }, methods: [method], question,
    }));
    navigate(`/result?ts=${Date.now()}`);
  }

  function addToBasket() {
    basketAdd({ method: "numerology", chart: null, birth: buildBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("method.numerology.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {t("method.numerology.desc")}
        </p>
      </header>

      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.single")}</p>

        {/* 年月日 — 最简出生 */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.birth.title")}</label>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="paper-label">{t("form.birth.year")}</label>
              <input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value, 10) || 0)} />
            </div>
            <div>
              <label className="paper-label">{t("form.birth.month")}</label>
              <input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value, 10) || 0)} min={1} max={12} />
            </div>
            <div>
              <label className="paper-label">{t("form.birth.day")}</label>
              <input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value, 10) || 0)} min={1} max={31} />
            </div>
          </div>
        </div>

        {/* 名字（可选） */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.name.label")}</label>
          <input className="paper-input" style={{ maxWidth: 300 }} value={name}
            onChange={(e) => setName(e.target.value)} placeholder={lang === "zh" ? "中文名 / 英文名" : "Your name"} />
        </div>

        {/* 模式 */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
          <div className="flex gap-1.5">
            {cfg.availableModes.map((m) => (
              <button key={m.value} type="button" onClick={() => setMode(m.value)}
                className="paper-tag" style={{
                  cursor: "pointer", fontSize: "0.75rem",
                  color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)",
                  borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)",
                }}>{m.label}</button>
            ))}
          </div>
        </div>

        {/* 问题 */}
        <QuestionInput value={question} onChange={setQuestion} />
      </section>

      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket}
        submitLabel={lang === "zh" ? "推算灵数" : "Calculate"} />

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {t("method.notice")}
      </p>
    </form>
  );
}
