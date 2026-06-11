// 风水专区: 八宅明镜 + 玄空飞星 合璧仪表板（「古籍×仪器」纸墨风格）
import { useState } from "react";
import { computeChartMulti } from "../lib/api";
import type { Birth, ChartResult, Method } from "../lib/types";
import { CITY_PRESETS, cityOptionLabel } from "../lib/cities";
import { DIRECTIONS_8 } from "../lib/compass";
import { ChartRenderer } from "../components/charts";
import { CompassDial } from "../components/CompassDial";
import { ProgressArc } from "../components/Interactions";

interface FSForm {
  year: number; month: number; day: number;
  hour: number; minute: number;
  gender: "male" | "female" | "unspecified";
  city: string;
  sittingDir: string;
  constructionYear: number;
}

const DEFAULT_FORM: FSForm = {
  year: 1990, month: 5, day: 15,
  hour: 8, minute: 30,
  gender: "unspecified",
  city: "上海",
  sittingDir: "正东",
  constructionYear: new Date().getFullYear(),
};

type FSTab = "bazhai" | "xuankong";

export function FengShui() {
  const [form, setForm] = useState<FSForm>(DEFAULT_FORM);
  const [charts, setCharts] = useState<Record<string, ChartResult> | null>(null);
  const [activeTab, setActiveTab] = useState<FSTab>("bazhai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cityInfo = CITY_PRESETS.find((c) => c.name === form.city) || CITY_PRESETS[0];
  const sittingInfo = DIRECTIONS_8.find((d) => d.code === form.sittingDir) || DIRECTIONS_8[2];
  const methods: Method[] = ["bazhai", "xuankong"];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setError(null); setLoading(true);
    const birth: Birth = {
      year: form.year, month: form.month, day: form.day,
      hour: form.hour, minute: form.minute,
      gender: form.gender, calendar: "gregorian",
      lat: cityInfo.lat, lng: cityInfo.lng, tz: cityInfo.tz, is_leap_month: false,
    };
    try {
      const results: Record<string, ChartResult> = {};
      for (const method of methods) {
        const options = {
          mode: method === "bazhai" ? "residential_bazhai" : "residential_xuankong",
          subject: "home_fengshui",
          sitting: sittingInfo.sans,
          construction_year: form.constructionYear,
        };
        const r = await computeChartMulti([method], birth, options);
        results[method] = r[method];
      }
      setCharts(results); setActiveTab("bazhai");
    } catch (err: any) { setError(String(err?.message || err)); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />风水专区</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>
          八宅明镜 + 玄空飞星 — 宅命相配、三元九运、飞星旺衰
        </p>
      </header>

      <form onSubmit={handleSubmit} className="paper-frame space-y-4">
        <h3 className="paper-section"><span className="num">壹</span>住宅与居住者</h3>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {(["year","month","day","hour","minute"] as const).map((key) => (
            <div key={key}>
              <label className="paper-label">{{ year:"出生年", month:"月", day:"日", hour:"时", minute:"分" }[key]}</label>
              <input className="paper-input" type="number" value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: parseInt(e.target.value, 10) || 0 })} />
            </div>
          ))}
          <div>
            <label className="paper-label">性别</label>
            <select className="paper-input" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value as any })}>
              <option value="male">男</option>
              <option value="female">女</option>
              <option value="unspecified">未指定</option>
            </select>
          </div>
        </div>

        <div>
          <label className="paper-label">出生城市</label>
          <select className="paper-input" style={{ maxWidth: "20rem" }} value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
            {CITY_PRESETS.map((c) => (
              <option key={`${c.province || c.region}-${c.name}`} value={c.name}>{cityOptionLabel(c)}</option>
            ))}
          </select>
          <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.25rem" }}>
            {cityInfo.name}: {cityInfo.lat.toFixed(2)}, {cityInfo.lng.toFixed(2)}, {cityInfo.tz}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="paper-label">建造/入伙年份</label>
            <input className="paper-input" type="number" value={form.constructionYear}
              onChange={(e) => setForm({ ...form, constructionYear: parseInt(e.target.value, 10) || form.year })} />
          </div>
          <div>
            <label className="paper-label">坐山/门向方位</label>
            <div className="paper-frame" style={{ background: "var(--paper)" }}>
              <CompassDial value={form.sittingDir} onChange={(code) => setForm({ ...form, sittingDir: code })} size={240} />
              <div style={{ fontSize: "0.65rem", textAlign: "center", color: "var(--ink-soft)", marginTop: "0.25rem" }}>
                选定: <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>{form.sittingDir}</span> · 玄空 {sittingInfo.sans}山
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3" style={{ borderTop: "1px solid var(--rule)", paddingTop: "0.75rem" }}>
          <button type="button" className="paper-btn-ghost" onClick={() => { setForm(DEFAULT_FORM); setCharts(null); }}>重置</button>
          <button type="submit" className="paper-btn" disabled={loading}>
            {loading ? (<span className="inline-flex items-center gap-2"><ProgressArc value={0.6} size={16} />排盘中...</span>) : "风水排盘"}
          </button>
        </div>
        {error && <div className="paper-error">{error}</div>}
      </form>

      {charts && (
        <div className="space-y-4">
          {charts.bazhai && charts.xuankong && <CombinedSummary bazhai={charts.bazhai} xuankong={charts.xuankong} />}

          <div className="flex gap-2">
            {(["bazhai","xuankong"] as FSTab[]).map((tab) => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className="paper-tag" style={{
                  color: activeTab === tab ? "var(--cinnabar)" : "var(--ink-soft)",
                  borderColor: activeTab === tab ? "var(--cinnabar)" : "var(--rule)",
                  fontSize: "0.82rem", fontWeight: 600, padding: "0.35rem 1rem", cursor: "pointer",
                }}>
                {tab === "bazhai" ? "八宅明镜" : "玄空飞星"}
              </button>
            ))}
          </div>

          {activeTab === "bazhai" && charts.bazhai && <ChartRenderer chart={charts.bazhai} />}
          {activeTab === "xuankong" && charts.xuankong && <ChartRenderer chart={charts.xuankong} />}
        </div>
      )}

      {!charts && (
        <section className="paper-frame" style={{ opacity: 0.65 }}>
          <h3 className="paper-section"><span className="num">凡</span>关于风水专区</h3>
          <div className="paper-body">
            <p>风水专区整合八宅明镜与玄空飞星两种古典风水体系。</p>
            <ul style={{ marginTop: "0.5rem", fontSize: "0.82rem", color: "var(--ink-soft)", lineHeight: 1.9, paddingLeft: "1.2rem" }}>
              <li><strong style={{ color: "var(--ink)" }}>八宅明镜</strong> — 根据居住者出生年份起命卦，分东四/西四命，按各卦大游年歌定八星方位。</li>
              <li><strong style={{ color: "var(--ink)" }}>玄空飞星</strong> — 按建造年份定三元九运，以24山坐向起运盘/山盘/向盘飞星，断旺山旺向等格局。</li>
            </ul>
            <p style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "var(--ink-soft)" }}>以上为传统文化参考，不等于完整风水布局，重大决定请咨询专业人士。</p>
          </div>
        </section>
      )}
    </div>
  );
}

function CombinedSummary({ bazhai, xuankong }: { bazhai: ChartResult; xuankong: ChartResult }) {
  const br = bazhai.raw || {}; const xr = xuankong.raw || {};
  const lifeGua = br.life_gua || "?";
  const isEast = br.is_east ? "东四命" : "西四命";
  const houseGua = br.house_gua;
  const match = br.house_resident_match;
  const pattern = xr.pattern || "?"; const period = xr.period || "?";

  return (
    <section className="paper-frame">
      <h3 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>风水合参 · 宅命总览</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" style={{ marginTop: "0.5rem", fontSize: "0.78rem" }}>
        <MiniStat label="命卦" value={lifeGua} sub={isEast} tone="cinnabar" />
        <MiniStat label="宅卦" value={houseGua || "未指定坐向"} sub={houseGua ? (br.house_is_east ? "东四宅" : "西四宅") : ""} tone="indigo" />
        <MiniStat label="宅命相配" value={match ? (match.matched ? "✓ 相配" : "✗ 不配") : "—"} sub={match?.level || ""} tone={match?.matched ? "verdigris" : "cinnabar"} />
        <MiniStat label="玄空格局" value={pattern} sub={period} tone="cinnabar" />
      </div>
      {match?.description && (
        <div style={{ marginTop: "0.5rem", fontSize: "0.78rem", lineHeight: 1.7, color: "var(--ink-soft)", borderLeft: "3px solid var(--cinnabar)", paddingLeft: "0.75rem" }}>
          {match.description}
        </div>
      )}
    </section>
  );
}

function MiniStat({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: string }) {
  const color = tone === "verdigris" ? "var(--verdigris)" : tone === "indigo" ? "var(--indigo)" : tone === "cinnabar" ? "var(--cinnabar)" : "var(--ink)";
  return (
    <div className="paper-grid-cell" style={{ padding: "0.5rem 0.75rem" }}>
      <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: "0.88rem", fontWeight: 700, color, fontFamily: "'Noto Serif SC', serif", marginTop: "0.15rem" }}>{value}</div>
      {sub && <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.1rem" }}>{sub}</div>}
    </div>
  );
}
