/** HePanPage v2 — 合盘专页
 *  双人输入并排 → 四维档位评级 → 印证/分歧 → 分享卡片
 */
import { type FormEvent, useState, useCallback } from "react";
import type { Birth, ChartResult } from "../lib/types";
import { computeChart } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { useBasket } from "../store/basket";
import { useBirthStore } from "../store/birth";
import { MethodSourcesPanel } from "../components/MethodSourcesPanel";
import { useStaggeredReveal } from "../lib/useStaggeredReveal";

type PersonForm = {
  year: number; month: number; day: number; hour: number; minute: number;
  gender: "male" | "female" | "unspecified";
};

const defaultPerson = (b?: any): PersonForm => ({
  year: b?.year ?? 1990, month: b?.month ?? 6, day: b?.day ?? 15,
  hour: b?.hour ?? 8, minute: b?.minute ?? 0, gender: b?.gender ?? "male",
});

export function HePanPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("hepan"));
  const b = birthStore.birth;

  const [self, setSelf] = useState<PersonForm>(defaultPerson(b));
  const [other, setOther] = useState<PersonForm>(defaultPerson({ ...b, year: 1992, month: 8 }));
  const [hepanType, setHepanType] = useState("bazi");
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true);
    birthStore.setBirth({ year: self.year, month: self.month, day: self.day, hour: self.hour, minute: self.minute, gender: self.gender });
    try {
      const birth1: Birth = { ...self, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz };
      const birth2: Birth = { ...other, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz };
      const result = await computeChart({ method: "hepan", birth: birth1, options: { mode: hepanType, partner: birth2 } });
      setChart(result);
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }, [self, other, hepanType, b, birthStore]);

  const r = chart?.raw;
  const scores = r?.scores || r?.ratings || {};

  // 四维评级 stagger fade-in
  const { getStyle: getRatingStyle } = useStaggeredReveal(4, { interval: 120 });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title"><span className="stamp" />{lang === "zh" ? "合盘" : "Synastry"}</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
          {lang === "zh" ? "双人输入并排，四维档位评级 + 印证/分歧 + 关键相位与合婚要点。" : "Side-by-side dual input. Four ratings, confirmations/conflicts, key aspects."}
        </p>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-5">
        <h2 className="paper-eyebrow">{lang === "zh" ? "双方信息" : "Both Partners"}</h2>

        {/* 己方 */}
        <div>
          <h3 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--ink)", marginBottom: "0.5rem" }}>
            {lang === "zh" ? "本人" : "Self"}
          </h3>
          <PersonFields p={self} onChange={(patch) => setSelf((prev) => ({ ...prev, ...patch }))} lang={lang} />
        </div>

        {/* 对方 */}
        <div style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
          <h3 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--ink)", marginBottom: "0.5rem" }}>
            {lang === "zh" ? "对方" : "Partner"}
          </h3>
          <PersonFields p={other} onChange={(patch) => setOther((prev) => ({ ...prev, ...patch }))} lang={lang} />
        </div>

        {/* 合盘类型 */}
        <div className="flex gap-1.5 flex-wrap">
          {[
            { value: "bazi", labelZh: "八字合婚", labelEn: "Bazi" },
            { value: "ziwei", labelZh: "紫微合盘", labelEn: "Ziwei" },
            { value: "western", labelZh: "西方合盘", labelEn: "Western" },
          ].map((m) => (
            <button key={m.value} type="button" onClick={() => setHepanType(m.value)}
              className="paper-tag" style={{ cursor: "pointer", fontSize: "0.75rem", color: hepanType === m.value ? "var(--cinnabar)" : "var(--ink-soft)", borderColor: hepanType === m.value ? "var(--cinnabar)" : "var(--rule)" }}>
              {lang === "zh" ? m.labelZh : m.labelEn}
            </button>
          ))}
        </div>

        <button type="submit" className="paper-btn" disabled={loading} style={{ minWidth: 140 }}>
          {loading ? (lang === "zh" ? "合盘中…" : "Synastry…") : (lang === "zh" ? "起合盘" : "Cast Synastry")}
        </button>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 四维评级 */}
          <section className="paper-frame">
            <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.8rem" }}>
              {lang === "zh" ? "四维评级" : "Ratings"}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { key: "emotion", labelZh: "情感匹配", labelEn: "Emotion" },
                { key: "wealth", labelZh: "财运契合", labelEn: "Wealth" },
                { key: "health", labelZh: "健康互助", labelEn: "Health" },
                { key: "growth", labelZh: "成长空间", labelEn: "Growth" },
              ].map((dim, i) => {
                const v = scores[dim.key] ?? 0;
                return (
                  <div key={dim.key} className="text-center p-3 rounded-sm animate-fade-in" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)", ...getRatingStyle(i) }}>
                    <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>{lang === "zh" ? dim.labelZh : dim.labelEn}</div>
                    <div style={{ fontSize: "1.6rem", fontWeight: 700, color: v >= 70 ? "var(--verdigris)" : v >= 40 ? "var(--ink)" : "var(--cinnabar)" }}>
                      {v}
                    </div>
                    <div style={{ fontSize: "0.55rem", color: "var(--ink-soft)" }}>
                      {v >= 85 ? (lang === "zh" ? "上等" : "A") : v >= 70 ? (lang === "zh" ? "中上" : "B") : v >= 50 ? (lang === "zh" ? "中等" : "C") : (lang === "zh" ? "待修" : "D")}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* 印证/分歧 */}
          <section className="paper-frame">
            <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.8rem" }}>
              {lang === "zh" ? "印证与分歧" : "Confirmations & Conflicts"}
            </h2>
            <div className="flex gap-3 flex-wrap">
              {(r?.confirmations || []).length > 0 ? (
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontSize: "0.65rem", color: "var(--verdigris)", fontWeight: 600, marginBottom: "0.3rem" }}>
                    {lang === "zh" ? "印证" : "Confirmed"} ({r?.confirmations?.length})
                  </div>
                  <ul style={{ fontSize: "0.7rem", color: "var(--ink)", listStyle: "none", padding: 0 }}>
                    {(r?.confirmations || []).slice(0, 5).map((c: any, i: number) => (
                      <li key={i} style={{ padding: "0.2rem 0", borderBottom: "1px solid var(--rule)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--verdigris)", borderColor: "rgba(74,99,79,0.3)", padding: "0.05rem 0.35rem" }}>
                          {lang === "zh" ? "印证" : "OK"}
                        </span>
                        <span>{typeof c === "string" ? c : c.label || c.desc}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {(r?.conflicts || []).length > 0 ? (
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontSize: "0.65rem", color: "var(--cinnabar)", fontWeight: 600, marginBottom: "0.3rem" }}>
                    {lang === "zh" ? "分歧" : "Conflicts"} ({r?.conflicts?.length})
                  </div>
                  <ul style={{ fontSize: "0.7rem", color: "var(--ink)", listStyle: "none", padding: 0 }}>
                    {(r?.conflicts || []).slice(0, 5).map((c: any, i: number) => (
                      <li key={i} style={{ padding: "0.2rem 0", borderBottom: "1px solid var(--rule)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)", padding: "0.05rem 0.35rem" }}>
                          {lang === "zh" ? "分歧" : "Warn"}
                        </span>
                        <span>{typeof c === "string" ? c : c.label || c.desc}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
            {!(r?.confirmations || []).length && !(r?.conflicts || []).length && (
              <div className="paper-empty">{lang === "zh" ? "合盘数据仍在计算中…" : "Computing synastry details…"}</div>
            )}
          </section>

          <ChartFooter chart={chart} inBasket={inBasket}
            onBasket={() => basketAdd({
              method: "hepan", chart,
              birth: { ...self, calendar: "gregorian", lat: b.lat, lng: b.lng, tz: b.tz } as any,
              addedAt: Date.now(),
            })}
            onReset={() => setChart(null)} />
        </div>
      )}

      <MethodSourcesPanel method="hepan" />
    </div>
  );
}

function PersonFields({ p, onChange, lang }: { p: PersonForm; onChange: (patch: Partial<PersonForm>) => void; lang: string }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
      <div><label className="paper-label">{lang === "zh" ? "年" : "Year"}</label><input className="paper-input" type="number" value={p.year} onChange={(e) => onChange({ year: parseInt(e.target.value) || 0 })} /></div>
      <div><label className="paper-label">{lang === "zh" ? "月" : "Mon"}</label><input className="paper-input" type="number" value={p.month} onChange={(e) => onChange({ month: parseInt(e.target.value) || 0 })} min={1} max={12} /></div>
      <div><label className="paper-label">{lang === "zh" ? "日" : "Day"}</label><input className="paper-input" type="number" value={p.day} onChange={(e) => onChange({ day: parseInt(e.target.value) || 0 })} min={1} max={31} /></div>
      <div><label className="paper-label">{lang === "zh" ? "时" : "Hr"}</label><input className="paper-input" type="number" value={p.hour} onChange={(e) => onChange({ hour: parseInt(e.target.value) || 0 })} min={0} max={23} /></div>
      <div><label className="paper-label">{lang === "zh" ? "分" : "Min"}</label><input className="paper-input" type="number" value={p.minute} onChange={(e) => onChange({ minute: parseInt(e.target.value) || 0 })} /></div>
      <div><label className="paper-label">{lang === "zh" ? "性别" : "Sex"}</label>
        <select className="paper-input" value={p.gender} onChange={(e) => onChange({ gender: e.target.value as any })}>
          <option value="male">{lang === "zh" ? "男" : "M"}</option>
          <option value="female">{lang === "zh" ? "女" : "F"}</option>
        </select>
      </div>
    </div>
  );
}

function ChartFooter({ chart, inBasket, onBasket, onReset }: any) {
  const { lang } = useI18n();
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap" style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
      <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>engine: {chart?.engine} · {chart?.elapsed_ms}ms</div>
      <div className="flex gap-2">
        <button type="button" className="paper-btn-ghost" onClick={onBasket} disabled={inBasket} style={{ fontSize: "0.78rem" }}>
          {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
        </button>
        <button type="button" className="paper-btn" onClick={onReset} style={{ fontSize: "0.78rem" }}>{lang === "zh" ? "重新合盘" : "Recast"}</button>
      </div>
    </div>
  );
}
