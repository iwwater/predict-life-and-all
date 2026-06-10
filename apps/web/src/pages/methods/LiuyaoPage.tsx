/** LiuyaoPage — 六爻独立排盘页
 *  时间起卦需生辰,手动摇卦需铜钱,数字起卦只需问题+种子
 */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG } from "../../lib/method-inputs";
import { BirthForm, type BirthState, type CityInfo } from "../../components/forms/BirthForm";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { CoinTossInput, type TossResult } from "../../components/forms/CoinTossInput";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";
import { CITY_PRESETS } from "../../lib/cities";

const DEFAULT_TOSSES: TossResult[] = ["old_yin", "young_yin", "young_yang", "young_yin", "old_yang", "young_yang"];

export function LiuyaoPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.liuyao;
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState(cfg.defaultMode);
  const [tosses, setTosses] = useState<TossResult[]>(DEFAULT_TOSSES);
  const [fixSeed, setFixSeed] = useState(false);
  const [seed, setSeed] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("liuyao"));

  const cityInfo = useMemo<CityInfo>(() => {
    const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0];
    return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz };
  }, [birth.city]);

  const needsBirth = mode === "time_qigua";

  function buildBirth(): Birth {
    if (!needsBirth) return {
      year: 2000, month: 1, day: 1, hour: 12, minute: 0,
      gender: "unspecified", calendar: "gregorian",
      lat: null, lng: null, tz: "Asia/Shanghai",
    };
    return {
      year: birth.year, month: birth.month, day: birth.day,
      hour: birth.hour, minute: birth.minute,
      gender: birth.gender, calendar: "gregorian",
      lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz,
    };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const b = buildBirth();
      const chart = await computeChart({
        method: "liuyao", birth: b,
        options: {
          mode,
          question: question || "问事",
          seed: fixSeed && seed ? seed : undefined,
          ...(mode === "manual_coin" ? { tosses } : {}),
        },
      });
      storeAndNavigate("liuyao", b, [chart]);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [birth, question, mode, tosses, fixSeed, seed, navigate]);

  function storeAndNavigate(method: any, b: Birth, charts: ChartResult[]) {
    const hid = crypto.randomUUID();
    useHistory.getState().add({
      id: hid, ts: Date.now(), birth: b, methods: [method],
      charts: { [method]: charts[0] },
      question: question || undefined,
      subject: "decision" as any,
      modeByMethod: { [method]: mode },
      tags: deriveTags([method], "decision"),
      favorite: false, reflection: null,
    });
    sessionStorage.setItem("mystic:result_id", hid);
    sessionStorage.setItem("mystic:result", JSON.stringify({
      birth: b, charts: { [method]: charts[0] }, methods: [method], question,
    }));
    navigate(`/result?ts=${Date.now()}`);
  }

  function addToBasket() {
    basketAdd({ method: "liuyao", chart: null, birth: buildBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("method.liuyao.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {t("method.liuyao.desc")}
        </p>
      </header>

      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>

        {/* 起法模式 */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
          <p style={{ fontSize: "0.68rem", color: "var(--ink-soft)", marginBottom: "0.4rem" }}>{t("form.mode.desc")}</p>
          <div className="flex gap-1.5 flex-wrap">
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

        {/* 条件渲染: 生辰 或 摇卦 */}
        {needsBirth ? (
          <div>
            <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.birth.title")}</label>
            <p style={{ fontSize: "0.68rem", color: "var(--ink-soft)", marginBottom: "0.4rem" }}>
              {t("form.birth.desc")}
            </p>
            <BirthForm showFields={cfg.birthFields} birth={birth} cityInfo={cityInfo}
              onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
          </div>
        ) : mode === "manual_coin" ? (
          <CoinTossInput tosses={tosses} onChange={setTosses} />
        ) : (
          <div>
            <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.seed.label")}</label>
            <input className="paper-input" style={{ maxWidth: 200 }} value={seed}
              onChange={(e) => { setSeed(e.target.value); setFixSeed(true); }}
              placeholder="输入数字 / 留空随机" />
          </div>
        )}

        {/* 问题（必填） */}
        <QuestionInput value={question} onChange={setQuestion} required
          placeholder={lang === "zh" ? "一事一问，写清楚你测的事。" : "One clear question per hexagram."} />
      </section>

      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket}
        submitLabel={lang === "zh" ? "起卦" : "Cast Hexagram"} />

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {t("method.notice")}
      </p>
    </form>
  );
}
