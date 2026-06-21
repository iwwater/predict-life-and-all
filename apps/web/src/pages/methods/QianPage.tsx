/** QianPage — 观音/关帝灵签独立页 */
import { type FormEvent, useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { computeChart } from "../../lib/api";
import { emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";

type QianType = "guanyin" | "guandi";

export function QianPage() {
  const { lang } = useI18n();
  const navigate = useNavigate();
  const [question, setQuestion] = useState("");
  const [qianType, setQianType] = useState<QianType>("guanyin");
  const [manual, setManual] = useState(false);
  const [qianNumber, setQianNumber] = useState("1");
  const [fixSeed, setFixSeed] = useState(false);
  const [seed, setSeed] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("qian"));

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const birth = emptyBirth();
      const chart = await computeChart({
        method: "qian",
        birth,
        options: {
          mode: manual ? "manual_number" : "random_draw",
          qian_type: qianType,
          qian_number: manual ? Number(qianNumber) : undefined,
          seed: fixSeed && seed ? seed : undefined,
          question: question || "今日一签",
        },
      });
      const hid = crypto.randomUUID();
      useHistory.getState().add({
        id: hid, ts: Date.now(), birth, methods: ["qian"], charts: { qian: chart },
        question: question || undefined, subject: "qian_guidance" as any,
        modeByMethod: { qian: manual ? "manual_number" : "random_draw" },
        tags: deriveTags(["qian"], "qian_guidance" as any),
        favorite: false, reflection: null,
      });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth, charts: { qian: chart }, methods: ["qian"], question }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [fixSeed, manual, navigate, qianNumber, qianType, question, seed]);

  function addToBasket() {
    basketAdd({ method: "qian", chart: null, birth: emptyBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "灵签" : "Qian Oracle"}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {lang === "zh" ? "支持观音灵签、关帝灵签；可随机抽签，也可录入实体签号。" : "Guanyin and Guandi qian oracle, random draw or manual number."}
        </p>
      </header>

      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "起签" : "Draw"}</h2>
        <div className="flex gap-2 flex-wrap">
          {[
            { v: "guanyin", l: "观音灵签" },
            { v: "guandi", l: "关帝灵签" },
          ].map((opt) => (
            <button key={opt.v} type="button" onClick={() => setQianType(opt.v as QianType)}
              className="paper-tag" style={{
                cursor: "pointer",
                color: qianType === opt.v ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: qianType === opt.v ? "var(--cinnabar)" : "var(--rule)",
              }}>{opt.l}</button>
          ))}
        </div>

        <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.78rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <input type="checkbox" checked={manual} onChange={(e) => setManual(e.target.checked)} />
          {lang === "zh" ? "我已有实体签号，直接录入" : "I already have a qian number"}
        </label>
        {manual ? (
          <input className="paper-input" style={{ maxWidth: 160 }} type="number" min={1} max={100} value={qianNumber} onChange={(e) => setQianNumber(e.target.value)} />
        ) : (
          <div>
            <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.78rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <input type="checkbox" checked={fixSeed} onChange={(e) => setFixSeed(e.target.checked)} />
              {lang === "zh" ? "固定 seed（复盘可重现）" : "Lock seed"}
            </label>
            {fixSeed && <input className="paper-input" style={{ maxWidth: 160, marginTop: "0.3rem" }} value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="42" />}
          </div>
        )}

        <QuestionInput value={question} onChange={setQuestion} required={false} />
      </section>

      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "抽签" : "Draw"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {lang === "zh" ? "灵签仅供传统文化参考，基础条目会在结果中标明。" : "For cultural reference only. Base catalog entries are labelled."}
      </p>
      <MethodSourcesPanel method="qian" />
    </form>
  );
}
