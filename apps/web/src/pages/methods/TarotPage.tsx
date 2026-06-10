/** TarotPage — 塔罗独立排盘页
 *  不需生辰,只需选牌阵+问题
 */
import { type FormEvent, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import type { TossResult } from "../../components/forms/CoinTossInput";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG, emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { SpreadSelector, TAROT_SPREAD_OPTIONS } from "../../components/forms/SpreadSelector";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";

export function TarotPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.tarot;
  const [question, setQuestion] = useState("");
  const [spread, setSpread] = useState(cfg.defaultSpread);
  const [fixSeed, setFixSeed] = useState(false);
  const [seed, setSeed] = useState("");
  const [mode, setMode] = useState(cfg.defaultMode);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("tarot"));

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const birth = emptyBirth();
      const chart = await computeChart({
        method: "tarot", birth,
        options: {
          mode,
          spread: spread as any,
          question: question || "今日指引",
          seed: fixSeed && seed ? seed : undefined,
        },
      });
      storeAndNavigate("tarot", birth, [chart], spread, question);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [question, spread, fixSeed, seed, mode, navigate, basketAdd]);

  function storeAndNavigate(method: any, birth: Birth, charts: ChartResult[], spreadVal: string, q: string) {
    const hid = crypto.randomUUID();
    useHistory.getState().add({
      id: hid, ts: Date.now(), birth, methods: [method],
      charts: { [method]: charts[0] },
      question: q || undefined,
      subject: "tarot_guidance" as any,
      modeByMethod: { [method]: mode },
      spread: spreadVal as any,
      tags: deriveTags([method], "tarot_guidance"),
      favorite: false, reflection: null,
    });
    sessionStorage.setItem("mystic:result_id", hid);
    sessionStorage.setItem("mystic:result", JSON.stringify({
      birth, charts: { [method]: charts[0] }, methods: [method], question: q,
    }));
    navigate(`/result?ts=${Date.now()}`);
  }

  function addToBasket() {
    basketAdd({ method: "tarot", chart: null, birth: emptyBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("method.tarot.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {t("method.tarot.desc")}
        </p>
      </header>

      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.single")}</p>

        {/* 牌阵 */}
        <SpreadSelector value={spread} onChange={(v) => setSpread(v as typeof spread)} spreads={TAROT_SPREAD_OPTIONS} />

        {/* 模式 */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
          <div className="flex gap-1.5">
            {cfg.availableModes.map((m) => (
              <button key={m.value} type="button" onClick={() => setMode(m.value)}
                className="paper-tag" style={{
                  cursor: "pointer", fontSize: "0.72rem",
                  color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)",
                  borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)",
                }}>{m.label}</button>
            ))}
          </div>
        </div>

        {/* 固定种子 */}
        <div>
          <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.78rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <input type="checkbox" checked={fixSeed} onChange={(e) => setFixSeed(e.target.checked)} />
            {t("form.seed.hint")}
          </label>
          {fixSeed && <input className="paper-input" style={{ maxWidth: 160, marginTop: "0.3rem" }} value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="42" />}
        </div>

        {/* 问题 */}
        <QuestionInput value={question} onChange={setQuestion} required />
      </section>

      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket}
        submitLabel={lang === "zh" ? "抽牌" : "Draw Cards"} />

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {t("method.notice")}
      </p>
    </form>
  );
}
