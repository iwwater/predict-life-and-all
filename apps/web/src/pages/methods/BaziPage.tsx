/** BaziPage v2 — 八字专页（展示型）
 *  闭环：排盘台（生辰界格表单）→ 四柱大字 → 五行雷达 → 旺衰三印 → 大运横轴 → 解读
 *  依据: 前端重构指示v2 §三·命类
 */
import { type FormEvent, useState, useCallback, useMemo, useEffect } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { BirthForm, type CityInfo } from "../../components/forms/BirthForm";
import { ElementsRadar } from "../../components/ElementsRadar";
import { Jargon } from "../../components/Jargon";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { CITY_PRESETS } from "../../lib/cities";
import { COLOR } from "../../components/ui";

export function BaziPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("bazi"));

  // 从全局记忆初始化
  const b = birthStore.birth;
  const [year, setYear] = useState(b.year);
  const [month, setMonth] = useState(b.month);
  const [day, setDay] = useState(b.day);
  const [hour, setHour] = useState(b.hour);
  const [minute, setMinute] = useState(b.minute);
  const [gender, setGender] = useState<"male" | "female" | "unspecified">(b.gender);
  const [city, setCity] = useState(b.city || "上海");

  // 高级选项
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [useZiShi, setUseZiShi] = useState(false);
  const [useTrueSolar, setUseTrueSolar] = useState(false);
  const [mode, setMode] = useState("natal");

  // 状态
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cityInfo = useMemo<CityInfo>(() => {
    const c = CITY_PRESETS.find((x) => x.name === city) || CITY_PRESETS[0];
    return { name: c.name, lat: c.lat, lng: c.lng, tz: c.tz };
  }, [city]);

  // 全局记忆同步：表单变更时更新 store
  const syncBirth = useCallback(() => {
    birthStore.setBirth({
      year, month, day, hour, minute, gender,
      calendar: "gregorian",
      lat: cityInfo.lat, lng: cityInfo.lng,
      tz: cityInfo.tz, city,
    });
  }, [year, month, day, hour, minute, gender, city, cityInfo, birthStore]);

  useEffect(() => { syncBirth(); }, []); // 首次同步

  const buildBirth = useCallback((): Birth => ({
    year, month, day, hour, minute, gender,
    calendar: "gregorian",
    lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz,
    is_leap_month: false,
  }), [year, month, day, hour, minute, gender, cityInfo]);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    syncBirth();
    try {
      const birth = buildBirth();
      const result = await computeChart({
        method: "bazi", birth,
        options: { mode },
      });
      setChart(result);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [buildBirth, mode, useZiShi, useTrueSolar, syncBirth]);

  const addToBasket = () => {
    basketAdd({ method: "bazi", chart, birth: buildBirth(), addedAt: Date.now() });
  };

  const r = chart?.raw;
  const pillars = r?.pillars || {};
  const pd: any[] = r?.pillar_details || [];
  const timeline = chart?.normalized.timeline || [];
  const score = r?.strength_score as number | undefined;
  const sb = r?.strength_basis as any;

  return (
    <div className="space-y-6">
      {/* 排盘台标题 */}
      <header>
        <h1 className="paper-title">
          <span className="stamp" />
          {lang === "zh" ? "八字排盘" : "Ba Zi"}
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {lang === "zh"
            ? "四柱八字，年柱为根、月柱为苗、日柱为花、时柱为果。日主即你自己。"
            : "Four Pillars of Destiny. Year=roots, Month=seedling, Day=blossom, Hour=fruit."}
        </p>
      </header>

      {/* 生辰表单 — 界格风格 */}
      <form onSubmit={submit} className="paper-frame space-y-4">
        <h2 className="paper-eyebrow">{lang === "zh" ? "命主信息" : "Birth Info"}</h2>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <Field label={lang === "zh" ? "年" : "Year"}>
            <input className="paper-input" type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value) || 0)} />
          </Field>
          <Field label={lang === "zh" ? "月" : "Month"}>
            <input className="paper-input" type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value) || 0)} min={1} max={12} />
          </Field>
          <Field label={lang === "zh" ? "日" : "Day"}>
            <input className="paper-input" type="number" value={day} onChange={(e) => setDay(parseInt(e.target.value) || 0)} min={1} max={31} />
          </Field>
          <Field label={lang === "zh" ? "时" : "Hour"}>
            <input className="paper-input" type="number" value={hour} onChange={(e) => setHour(parseInt(e.target.value) || 0)} min={0} max={23} />
          </Field>
          <Field label={lang === "zh" ? "分" : "Min"}>
            <input className="paper-input" type="number" value={minute} onChange={(e) => setMinute(parseInt(e.target.value) || 0)} min={0} max={59} />
          </Field>
          <Field label={lang === "zh" ? "性别" : "Sex"}>
            <select className="paper-input" value={gender} onChange={(e) => setGender(e.target.value as any)}>
              <option value="male">{lang === "zh" ? "男" : "Male"}</option>
              <option value="female">{lang === "zh" ? "女" : "Female"}</option>
              <option value="unspecified">{lang === "zh" ? "未指定" : "—"}</option>
            </select>
          </Field>
        </div>
        {/* 城市 */}
        <div>
          <label className="paper-label">{lang === "zh" ? "出生地" : "Birthplace"}</label>
          <select className="paper-input" style={{ maxWidth: "20rem" }} value={city} onChange={(e) => setCity(e.target.value)}>
            {CITY_PRESETS.map((c) => (
              <option key={`${c.name}-${c.lat}`} value={c.name}>{c.name}</option>
            ))}
          </select>
          <span className="paper-tag" style={{ marginLeft: "0.5rem" }}>
            {cityInfo.lat.toFixed(2)}°N, {cityInfo.lng.toFixed(2)}°E · {cityInfo.tz}
          </span>
        </div>

        {/* 高级选项折叠区 */}
        <div>
          <button type="button" className="paper-link" onClick={() => setShowAdvanced(!showAdvanced)}
            style={{ fontSize: "0.75rem" }}>
            {showAdvanced ? "−" : "+"} {lang === "zh" ? "高级选项（子时 / 真太阳时）" : "Advanced (Zi Hour / True Solar)"}
          </button>
          {showAdvanced && (
            <div className="mt-3 p-3 space-y-2" style={{ background: "var(--paper-2)", border: "1px solid var(--rule)", borderRadius: 4 }}>
              <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.8rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <input type="checkbox" checked={useZiShi} onChange={(e) => setUseZiShi(e.target.checked)} />
                {lang === "zh" ? "子时换日（23点为日界）" : "Zi Hour as day boundary (23:00 = next day)"}
              </label>
              <label style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.8rem", color: "var(--ink)", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <input type="checkbox" checked={useTrueSolar} onChange={(e) => setUseTrueSolar(e.target.checked)} />
                {lang === "zh" ? "真太阳时校正（按经度换算）" : "True solar time (longitude-adjusted)"}
              </label>
            </div>
          )}
        </div>

        {/* 排盘按钮 */}
        <div className="flex items-center gap-3">
          <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 120 }}>
            {loading ? (lang === "zh" ? "排盘中…" : "Casting…") : (lang === "zh" ? "排八字盘" : "Cast Ba Zi")}
          </button>
        </div>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {/* 盘面结果 — 闭环展示 */}
      {chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 四柱大字 — 页面主角 */}
          <section className="paper-frame">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.1rem", color: "var(--cinnabar)", fontWeight: 600 }}>
                <Jargon term="四柱" />
              </h2>
              <span className="paper-tag" style={{ borderColor: "rgba(176,58,46,0.3)", color: "var(--cinnabar)" }}>
                <Jargon term="日主" mode="plain" /> {r?.day_master || "—"}
              </span>
            </div>
            <div className="grid grid-cols-4 gap-2 sm:gap-3">
              {[
                { key: "year", term: "年柱", desc: lang === "zh" ? "祖辈·根" : "Ancestors" },
                { key: "month", term: "月柱", desc: lang === "zh" ? "父母·苗" : "Parents" },
                { key: "day", term: "日柱", desc: lang === "zh" ? "自己·花" : "Self" },
                { key: "hour", term: "时柱", desc: lang === "zh" ? "子女·果" : "Children" },
              ].map((col) => {
                const gz: string = (pillars as any)[col.key] || "??";
                const detail = pd.find((d: any) => d.label === col.key);
                const hs = detail?.hidden_stems || [];
                const shigan = detail?.ten_god_stem || "";
                return (
                  <div key={col.key} className="text-center rounded-sm p-3"
                    style={{ background: "var(--paper-2)", border: "1px solid var(--rule)" }}>
                    <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", letterSpacing: "0.1em", marginBottom: "0.3rem" }}>
                      <Jargon term={col.term} override={{ plain: col.desc, hint: "" }} />
                    </div>
                    <div style={{
                      fontFamily: "'Noto Serif SC', serif",
                      fontSize: "clamp(1.8rem, 5vw, 3rem)",
                      fontWeight: 700,
                      color: "var(--cinnabar)",
                      lineHeight: 1.2,
                    }}>
                      {gz[0] || "?"}
                    </div>
                    <div style={{
                      fontFamily: "'Noto Serif SC', serif",
                      fontSize: "clamp(1.8rem, 5vw, 3rem)",
                      fontWeight: 700,
                      color: "var(--ink)",
                      lineHeight: 1.2,
                    }}>
                      {gz[1] || "?"}
                    </div>
                    {hs.length > 0 && (
                      <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.25rem" }}>
                        {lang === "zh" ? "藏" : "H"}:{hs.join("/")}
                      </div>
                    )}
                    {shigan && (
                      <div style={{ fontSize: "0.6rem", color: "var(--verdigris)", marginTop: "0.15rem" }}>
                        {shigan}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          {/* 旺衰三印 + 五行雷达 */}
          <div className="grid sm:grid-cols-2 gap-4">
            {/* 旺衰三印 */}
            {sb && (
              <section className="paper-frame space-y-3">
                <h3 className="paper-eyebrow">{lang === "zh" ? "旺衰多因子" : "Strength Factors"}</h3>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { key: "得令", en: "Season", val: sb.month_strength ?? 0, hint: lang === "zh" ? "月令是否生扶日主" : "Month supports Day Master?" },
                    { key: "得地", en: "Earth", val: (sb.peer_count ?? 0) + (sb.resource_count ?? 0), hint: lang === "zh" ? "地支根气与印比数" : "Branch roots & support count" },
                    { key: "得势", en: "Force", val: sb.output_count ?? 0, hint: lang === "zh" ? "食伤泄秀流通之势" : "Output flow & expression" },
                  ].map((f) => {
                    const lit = typeof f.val === "number" && f.val > 0;
                    return (
                      <div key={f.key} className="text-center p-2 rounded-sm"
                        style={{
                          border: `1px solid ${lit ? "var(--cinnabar)" : "var(--rule)"}`,
                          background: lit ? "rgba(176,58,46,0.06)" : "var(--paper)",
                        }}>
                        <div style={{ fontSize: "0.9rem", fontWeight: 700, color: lit ? "var(--cinnabar)" : "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
                          {f.key}
                        </div>
                        <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>
                          {f.en}
                        </div>
                        <div style={{ fontSize: "0.65rem", color: lit ? "var(--cinnabar)" : "var(--ink-soft)", marginTop: "0.2rem" }}>
                          {f.hint}
                        </div>
                        {lit && (
                          <div style={{
                            width: "0.55rem", height: "0.55rem", borderRadius: "50%",
                            background: "var(--cinnabar)", margin: "0.3rem auto 0", opacity: 0.7,
                          }} />
                        )}
                      </div>
                    );
                  })}
                </div>
                {typeof score === "number" && (
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginBottom: "0.3rem" }}>
                      {lang === "zh" ? "日主身强评分" : "Day Master Strength"}
                    </div>
                    <div style={{ height: 6, background: "var(--rule)", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{
                        height: "100%", borderRadius: 3,
                        width: `${Math.min(score, 100)}%`,
                        background: score < 30 ? "#c44" : score < 55 ? "#ca8a04" : score < 75 ? "#16a34a" : "#2563eb",
                        transition: "width 0.6s",
                      }} />
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace", marginTop: "0.2rem", display: "block" }}>
                      {score}/100
                    </span>
                  </div>
                )}
              </section>
            )}

            {/* 五行雷达 */}
            <section className="paper-frame flex justify-center">
              <ElementsRadar elements={chart.normalized.elements || {}} variant="five"
                title={`${r?.day_master || "—"} ${lang === "zh" ? "五行配比" : "Elements"}`} />
            </section>
          </div>

          {/* 大运横轴 */}
          {timeline.length > 0 && (
            <section className="paper-frame space-y-2">
              <h3 className="paper-eyebrow">
                <Jargon term="大运" /> · {lang === "zh" ? "十年一步大运" : "10-Year Luck Cycles"}
              </h3>
              <div className="flex overflow-x-auto gap-1.5 pb-2" style={{ scrollbarWidth: "thin" }}>
                {timeline.map((t, i) => (
                  <div key={i} className="text-center px-3 py-2 rounded-sm shrink-0"
                    style={{
                      minWidth: 80,
                      background: i === 0 ? "rgba(176,58,46,0.08)" : "var(--paper-2)",
                      border: `1px solid ${i === 0 ? "var(--cinnabar)" : "var(--rule)"}`,
                    }}>
                    <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                      {t.label}
                    </div>
                    <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
                      {t.from}–{t.to}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 当前运势 */}
          {r?.current_luck?.decade_ganzhi && (
            <section className="paper-frame">
              <div className="paper-eyebrow">{lang === "zh" ? "当前运势" : "Current Luck"}</div>
              <div style={{ fontSize: "0.85rem", color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                {lang === "zh" ? "大运" : "Cycle"} {r.current_luck.decade_ganzhi}
                ({r.current_luck.decade_from}–{r.current_luck.decade_to})
                {" · "}{r.current_luck.annual_label}
              </div>
            </section>
          )}

          {/* 底部操作栏 */}
          <div className="flex items-center justify-between gap-3 flex-wrap"
            style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              engine: {chart.engine} · {chart.elapsed_ms}ms
            </div>
            <div className="flex gap-2">
              <button type="button" className="paper-btn-ghost" onClick={addToBasket}
                style={{ fontSize: "0.78rem" }} disabled={inBasket}>
                {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" className="paper-btn" onClick={() => setChart(null)}
                style={{ fontSize: "0.78rem" }}>
                {lang === "zh" ? "重新排盘" : "Recast"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 初始状态引导 */}
      {!chart && !loading && (
        <section className="paper-frame" style={{ textAlign: "center", padding: "2rem 1rem" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
            {lang === "zh"
              ? "生辰信息已从全局记忆带入，可直接排盘或修改后重排。"
              : "Birth info loaded from global memory. Edit or cast directly."}
          </div>
        </section>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="paper-label">{label}</label>
      {children}
    </div>
  );
}
