/** LenormandPage — 雷诺曼独立排盘页（不需生辰） */
import { type FormEvent, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG, emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { SpreadSelector, LENORMAND_SPREAD_OPTIONS } from "../../components/forms/SpreadSelector";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";

export function LenormandPage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.lenormand;
  const [question, setQuestion] = useState("");
  const [spread, setSpread] = useState(cfg.defaultSpread);
  const [fixSeed, setFixSeed] = useState(false); const [seed, setSeed] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add); const inBasket = useBasket((s) => s.has("lenormand"));

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const birth = emptyBirth();
      const chart = await computeChart({ method: "lenormand", birth, options: { mode: cfg.defaultMode, spread: spread as any, question: question || "今日指引", seed: fixSeed && seed ? seed : undefined } });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth, methods: ["lenormand"], charts: { lenormand: chart }, question: question || undefined, subject: "tarot_guidance" as any, modeByMethod: { lenormand: cfg.defaultMode }, spread: spread as any, tags: deriveTags(["lenormand"], "tarot_guidance"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth, charts: { lenormand: chart }, methods: ["lenormand"], question }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [question, spread, fixSeed, seed, navigate]);

  function addToBasket() { basketAdd({ method: "lenormand", chart: null, birth: emptyBirth(), addedAt: Date.now() }); }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.lenormand.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.lenormand.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.single")}</p>
        <SpreadSelector value={spread} onChange={(v) => setSpread(v as typeof spread)} spreads={LENORMAND_SPREAD_OPTIONS} />
        <div>
          <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.78rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}><input type="checkbox" checked={fixSeed} onChange={(e) => setFixSeed(e.target.checked)} />{t("form.seed.hint")}</label>
          {fixSeed && <input className="paper-input" style={{ maxWidth: 160, marginTop: "0.3rem" }} value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="42" />}
        </div>
        <QuestionInput value={question} onChange={setQuestion} required />
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "抽牌" : "Draw"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
    </form>
  );
}
