/** XuankongPage — 玄空飞星独立排盘页
 *  不需生辰,只需坐向+建造年份+运期
 */
import { type FormEvent, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG, emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { DirectionPicker } from "../../components/forms/DirectionPicker";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";

export function XuankongPage() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.xuankong;
  const [sittingDir, setSittingDir] = useState("子");
  const [constructionYear, setConstructionYear] = useState(new Date().getFullYear());
  const [period, setPeriod] = useState(8);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("xuankong"));

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const birth = emptyBirth();
      const chart = await computeChart({
        method: "xuankong", birth,
        options: {
          mode: cfg.defaultMode,
          sitting: sittingDir,
          construction_year: constructionYear,
          period,
        },
      });
      storeAndNavigate("xuankong", birth, [chart]);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [sittingDir, constructionYear, period, navigate]);

  function storeAndNavigate(method: any, b: Birth, charts: ChartResult[]) {
    const hid = crypto.randomUUID();
    useHistory.getState().add({
      id: hid, ts: Date.now(), birth: b, methods: [method],
      charts: { [method]: charts[0] },
      question: question || undefined,
      subject: "home_fengshui" as any,
      modeByMethod: { [method]: cfg.defaultMode },
      tags: deriveTags([method], "home_fengshui"),
      favorite: false, reflection: null,
    });
    sessionStorage.setItem("mystic:result_id", hid);
    sessionStorage.setItem("mystic:result", JSON.stringify({
      birth: b, charts: { [method]: charts[0] }, methods: [method], question,
    }));
    navigate(`/result?ts=${Date.now()}`);
  }

  function addToBasket() {
    basketAdd({ method: "xuankong", chart: null, birth: emptyBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("method.xuankong.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {t("method.xuankong.desc")}
        </p>
      </header>

      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("method.formDesc.single")}</p>

        {/* 坐向+建造年份 */}
        <DirectionPicker
          sittingDir={sittingDir} constructionYear={constructionYear}
          onSittingChange={setSittingDir} onYearChange={setConstructionYear}
        />

        {/* 运期 */}
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>
            {lang === "zh" ? "三元运期" : "Period"}
          </label>
          <select className="paper-input" style={{ maxWidth: 160 }} value={period}
            onChange={(e) => setPeriod(parseInt(e.target.value, 10))}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((p) => (
              <option key={p} value={p}>{lang === "zh" ? `第${p}运` : `Period ${p}`}</option>
            ))}
          </select>
        </div>

        {/* 问题（可选） */}
        <QuestionInput value={question} onChange={setQuestion} />
      </section>

      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket}
        submitLabel={lang === "zh" ? "排玄空盘" : "Cast Flying Stars"} />

      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>
        {t("method.notice")}
      </p>
    </form>
  );
}
