/** XiaoliurenPage — 小六壬独立排盘页（月日时掌诀 / 数字掌诀） */
import { type FormEvent, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { computeChart } from "../../lib/api";
import { METHOD_INPUT_CONFIG, emptyBirth } from "../../lib/method-inputs";
import { QuestionInput } from "../../components/forms/QuestionInput";
import { MethodSubmitBar } from "../../components/forms/MethodSubmitBar";
import { useI18n } from "../../lib/i18n";
import { useHistory, deriveTags } from "../../store/history";
import { useBasket } from "../../store/basket";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

export function XiaoliurenPage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const cfg = METHOD_INPUT_CONFIG.xiaoliuren;
  const [mode, setMode] = useState(cfg.defaultMode);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [day, setDay] = useState(new Date().getDate());
  const [hour, setHour] = useState(new Date().getHours());
  const [numbers, setNumbers] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const basketAdd = useBasket((s) => s.add); const inBasket = useBasket((s) => s.has("xiaoliuren"));

  const isTimeMode = mode === "time_xiaoliuren";

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    try {
      const birth = isTimeMode
        ? { year: 2000, month, day, hour, minute: 0, gender: "unspecified" as const, calendar: "lunar" as const, lat: null as number | null, lng: null as number | null, tz: "Asia/Shanghai" }
        : emptyBirth();
      const chart = await computeChart({ method: "xiaoliuren", birth, options: { mode, question: question || "问事", seed: !isTimeMode && numbers ? numbers : undefined } });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth, methods: ["xiaoliuren"], charts: { xiaoliuren: chart }, question: question || undefined, subject: "decision" as any, modeByMethod: { xiaoliuren: mode }, tags: deriveTags(["xiaoliuren"], "decision"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth, charts: { xiaoliuren: chart }, methods: ["xiaoliuren"], question }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [mode, month, day, hour, numbers, question, navigate]);

  function addToBasket() {
    const birth = isTimeMode
      ? { year: 2000, month, day, hour, minute: 0, gender: "unspecified" as const, calendar: "lunar" as const, lat: null as number | null, lng: null as number | null, tz: "Asia/Shanghai" }
      : emptyBirth();
    basketAdd({ method: "xiaoliuren", chart: null, birth, addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header><h1 className="paper-title"><span className="stamp" />{t("method.xiaoliuren.title")}</h1><p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("method.xiaoliuren.desc")}</p></header>
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("method.formTitle")}</h2>
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{t("form.mode.label")}</label>
          <div className="flex gap-1.5">{cfg.availableModes.map((m) => (<button key={m.value} type="button" onClick={() => setMode(m.value)} className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: mode === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: mode === m.value ? "var(--cinnabar)" : "var(--rule)" }}>{m.label}</button>))}</div>
        </div>
        {isTimeMode ? (
          <div className="grid grid-cols-3 gap-3">
            <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "月（农历）" : "Month (Lunar)"}</label><input className="paper-input" type="number" min={1} max={12} value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 1)} /></div>
            <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "日（农历）" : "Day (Lunar)"}</label><input className="paper-input" type="number" min={1} max={30} value={day} onChange={(e) => setDay(parseInt(e.target.value) || 1)} /></div>
            <div><label className="paper-label" style={{ marginBottom: "0.2rem", display: "block" }}>{lang === "zh" ? "时辰" : "Hour"}</label><select className="paper-input" value={hour} onChange={(e) => setHour(parseInt(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => {
                const h = i * 2;
                const names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
                return <option key={i} value={h}>{names[i]}时 ({h}:00-{(h + 2) % 24}:00)</option>;
              })}
            </select></div>
          </div>
        ) : (
          <div><label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>{lang === "zh" ? "三数起课" : "Three Numbers"}</label><input className="paper-input" style={{ maxWidth: 240 }} value={numbers} onChange={(e) => setNumbers(e.target.value)} placeholder={lang === "zh" ? "输入 3 个数字，如 3 7 5 / 留空随机" : "3 numbers, e.g. 3 7 5 / leave blank for random"} /></div>
        )}
        <QuestionInput value={question} onChange={setQuestion} required placeholder={lang === "zh" ? "你要问什么事？（出行/寻物/决策...）" : "What do you want to ask? (travel/lost items/decisions...)"} />
      </section>
      <MethodSubmitBar loading={loading} error={error} inBasket={inBasket} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "掐小六壬" : "Cast Xiao Liu Ren"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
      <MethodSourcesPanel method="xiaoliuren" />
    </form>
  );
}
