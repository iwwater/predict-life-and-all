/** AggregatePage — 多法合参聚合页: 勾选多种术法 + 共享/独立参数 → 批量计算 → 交叉验证 */
import { type FormEvent, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { Birth, Method } from "../lib/types";
import { computeChartMulti } from "../lib/api";
import { METHOD_INPUT_CONFIG } from "../lib/method-inputs";
import { BirthForm, type BirthState, type CityInfo } from "../components/forms/BirthForm";
import { QuestionInput } from "../components/forms/QuestionInput";
import { MethodSubmitBar } from "../components/forms/MethodSubmitBar";
import { useI18n } from "../lib/i18n";
import { useHistory, deriveTags } from "../store/history";
import { useBasket } from "../store/basket";
import { CITY_PRESETS } from "../lib/cities";

type MethodGroup = { key: string; label: string; accent: string; methods: Method[] };

const METHOD_GROUPS: MethodGroup[] = [
  { key: "east", label: "东方命理", accent: "var(--verdigris)", methods: ["bazi", "bazi_v2", "ziwei", "qimen", "liuren", "liuyao", "meihua", "xiaoliuren", "chenggu", "tieban"] },
  { key: "west", label: "西方占卜", accent: "var(--indigo)", methods: ["western", "vedic", "tarot", "lenormand", "numerology"] },
  { key: "fengshui", label: "风水堪舆", accent: "var(--cinnabar)", methods: ["bazhai", "xuankong"] },
];

const METHOD_LABELS: Record<string, string> = {
  bazi: "八字", bazi_v2: "八字·精算", ziwei: "紫微斗数", qimen: "奇门遁甲",
  liuyao: "六爻", meihua: "梅花易数", xiaoliuren: "小六壬", chenggu: "称骨", liuren: "大六壬", tieban: "铁板神数",
  western: "西方占星", vedic: "吠陀占星", tarot: "塔罗", lenormand: "雷诺曼", numerology: "生命灵数",
  bazhai: "八宅明镜", xuankong: "玄空飞星",
};

export function AggregatePage() {
  const { t, lang } = useI18n(); const navigate = useNavigate();
  const basketItems = useBasket((s) => s.items);
  const basketClear = useBasket((s) => s.clear);

  const [selected, setSelected] = useState<Set<Method>>(new Set());
  const [birth, setBirth] = useState<BirthState>({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: "male", city: "上海" });
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const cityInfo = useMemo<CityInfo>(() => { const c = CITY_PRESETS.find((x) => x.name === birth.city) || CITY_PRESETS[0]; return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz }; }, [birth.city]);

  const needsBirth = useMemo(() => {
    return Array.from(selected).some((m) => {
      const cfg = METHOD_INPUT_CONFIG[m];
      return cfg?.needsBirth === true || cfg?.needsBirth === "conditional" || cfg?.needsBirth === "minimal";
    });
  }, [selected]);

  const birthMethods = useMemo(() => {
    return Array.from(selected).filter((m) => {
      const cfg = METHOD_INPUT_CONFIG[m];
      return cfg?.needsBirth === true || cfg?.needsBirth === "conditional" || cfg?.needsBirth === "minimal";
    });
  }, [selected]);

  function toggleMethod(m: Method) {
    setSelected((prev) => { const next = new Set(prev); if (next.has(m)) next.delete(m); else next.add(m); return next; });
  }

  function importBasket() {
    setSelected(new Set(basketItems.map((it) => it.method)));
  }

  function buildBirth(): Birth {
    return { year: birth.year, month: birth.month, day: birth.day, hour: birth.hour, minute: birth.minute, gender: birth.gender, calendar: "gregorian", lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz };
  }

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null);
    if (selected.size < 2) { setError(lang === "zh" ? "请至少选择 2 个术法" : "Please select at least 2 methods"); return; }
    setLoading(true);
    try {
      const b = buildBirth();
      const methods = Array.from(selected);
      const charts = await computeChartMulti(methods, b, { question: question || undefined });
      const hid = crypto.randomUUID();
      useHistory.getState().add({ id: hid, ts: Date.now(), birth: b, methods, charts, question: question || undefined, subject: "self_life", modeByMethod: {}, tags: deriveTags(methods, "self_life"), favorite: false, reflection: null });
      sessionStorage.setItem("mystic:result_id", hid);
      sessionStorage.setItem("mystic:result", JSON.stringify({ birth: b, charts, methods, question }));
      navigate(`/result?ts=${Date.now()}`);
    } catch (err: any) { setError(String(err?.message || err)); } finally { setLoading(false); }
  }, [selected, birth, question, navigate]);

  function addToBasket() {
    for (const m of selected) basketItems.find((it) => it.method === m) || useBasket.getState().add({ method: m as Method, chart: null, birth: buildBirth(), addedAt: Date.now() });
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />{t("aggregate.title")}</h1>
        <p style={{ fontSize: "0.83rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>{t("aggregate.desc")}</p>
      </header>

      {/* 合参篮快捷导入 */}
      {basketItems.length >= 2 && (
        <div className="paper-frame flex items-center justify-between flex-wrap gap-2" style={{ padding: "0.6rem 1rem" }}>
          <span style={{ fontSize: "0.78rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
            {t("basket.title")}: {basketItems.length} 个术法
          </span>
          <div className="flex gap-2">
            <button type="button" className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} onClick={importBasket}>{lang === "zh" ? "一键导入" : "Import"}</button>
            <button type="button" className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} onClick={basketClear}>{t("basket.clear")}</button>
          </div>
        </div>
      )}

      {/* 术法选择网格 */}
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{t("aggregate.selectMethods")}</h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("aggregate.selectMethods.hint")}</p>
        {METHOD_GROUPS.map((group) => (
          <div key={group.key}>
            <div style={{ fontSize: "0.7rem", color: group.accent, fontWeight: 600, marginBottom: "0.4rem", fontFamily: "'Noto Serif SC', serif", letterSpacing: "0.1em" }}>{group.label}</div>
            <div className="flex flex-wrap gap-1.5">
              {group.methods.map((m) => {
                const sel = selected.has(m);
                const cfg = METHOD_INPUT_CONFIG[m];
                const birthLabel = cfg?.needsBirth === false ? "无生辰" : cfg?.needsBirth === "conditional" ? "条件生辰" : cfg?.needsBirth === "minimal" ? "仅日期" : "需生辰";
                return (
                  <button key={m} type="button" onClick={() => toggleMethod(m)}
                    className="paper-tag" style={{
                      cursor: "pointer", fontSize: "0.72rem",
                      color: sel ? "var(--cinnabar)" : "var(--ink-soft)",
                      borderColor: sel ? "var(--cinnabar)" : "var(--rule)",
                      background: sel ? "rgba(176,58,46,0.05)" : "var(--paper)",
                    }}>
                    {METHOD_LABELS[m] || m}
                    <span style={{ fontSize: "0.6rem", opacity: 0.6, marginLeft: "0.3rem" }}>({birthLabel})</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
        <div style={{ fontSize: "0.72rem", color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>
          {lang === "zh" ? "已选 " : "Selected: "}{selected.size} {lang === "zh" ? "个术法" : " methods"}
        </div>
      </section>

      {/* 共享参数区 */}
      {selected.size >= 2 && (
        <section className="paper-frame space-y-4">
          <h2 className="paper-eyebrow">{lang === "zh" ? "共享参数" : "Shared Parameters"}</h2>
          {needsBirth ? (
            <>
              <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
                {t("aggregate.sharedBirth.hint")}{birthMethods.map((m) => METHOD_LABELS[m] || m).join("、")}
              </p>
              <BirthForm showFields={["year", "month", "day", "hour", "minute", "gender", "city"]} birth={birth} cityInfo={cityInfo} onChange={(p) => setBirth((prev) => ({ ...prev, ...p }))} />
            </>
          ) : (
            <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{t("aggregate.noBirthNeeded")}</p>
          )}
          <QuestionInput value={question} onChange={setQuestion} />
        </section>
      )}

      <MethodSubmitBar loading={loading} error={error} inBasket={false} onAddToBasket={addToBasket} submitLabel={lang === "zh" ? "合参排盘" : "Aggregate Cast"} />
      <p className="paper-source" style={{ fontSize: "0.6rem", textAlign: "center" }}>{t("method.notice")}</p>
    </form>
  );
}
