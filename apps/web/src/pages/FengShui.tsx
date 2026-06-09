// 风水专区: 八宅明镜 + 玄空飞星 合璧仪表板
import { useState } from "react";
import { computeChartMulti } from "../lib/api";
import type { Birth, ChartResult, Method } from "../lib/types";
import { CITY_PRESETS, cityOptionLabel } from "../lib/cities";
import { DIRECTIONS_8 } from "../lib/compass";
import { COLOR } from "../components/ui";
import { ChartRenderer } from "../components/charts";
import { CompassDial } from "../components/CompassDial";
import { Reveal, ProgressArc } from "../components/Interactions";
import { BaGuaRing, CompassRing } from "../components/MysticElements";

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
    e.preventDefault();
    setError(null);
    setLoading(true);
    const birth: Birth = {
      year: form.year, month: form.month, day: form.day,
      hour: form.hour, minute: form.minute,
      gender: form.gender,
      calendar: "gregorian",
      lat: cityInfo.lat, lng: cityInfo.lng,
      tz: cityInfo.tz,
      is_leap_month: false,
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
      setCharts(results);
      setActiveTab("bazhai");
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* 八卦环 + 罗盘背景装饰 */}
      <div className="fixed right-0 bottom-0 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <BaGuaRing size={300} spinning />
      </div>
      <div className="fixed left-0 top-1/4 pointer-events-none opacity-[0.03] z-0" aria-hidden>
        <CompassRing size={260} />
      </div>

      {/* Header with Reveal */}
      <Reveal>
        <header>
          <h1 className="text-2xl font-display" style={{ color: COLOR.goldBright }}>
            风水专区
          </h1>
          <p className="text-sm mt-1" style={{ color: COLOR.muted }}>
            八宅明镜 + 玄空飞星 — 宅命相配、三元九运、飞星旺衰
          </p>
        </header>
      </Reveal>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="card space-y-4">
        <h3 className="text-lg" style={{ color: COLOR.goldBright }}>住宅与居住者</h3>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {(["year", "month", "day", "hour", "minute"] as const).map((key) => (
            <div key={key}>
              <label className="label">{{ year: "出生年", month: "月", day: "日", hour: "时", minute: "分" }[key]}</label>
              <input
                className="input"
                type="number"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: parseInt(e.target.value, 10) || 0 })}
              />
            </div>
          ))}
          <div>
            <label className="label">性别</label>
            <select className="input" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value as any })}>
              <option value="male">男</option>
              <option value="female">女</option>
              <option value="unspecified">未指定</option>
            </select>
          </div>
        </div>

        <div className="mt-3">
          <label className="label">出生城市</label>
          <select className="input max-w-md" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
            {CITY_PRESETS.map((c) => (
              <option key={`${c.province || c.region}-${c.name}`} value={c.name}>
                {cityOptionLabel(c)}
              </option>
            ))}
          </select>
          <div className="text-[10px] mt-1" style={{ color: COLOR.muted }}>
            {cityInfo.name}: {cityInfo.lat.toFixed(2)}, {cityInfo.lng.toFixed(2)}, {cityInfo.tz}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-3 mt-4">
          <div>
            <label className="label">建造/入伙年份</label>
            <input
              className="input"
              type="number"
              value={form.constructionYear}
              onChange={(e) => setForm({ ...form, constructionYear: parseInt(e.target.value, 10) || form.year })}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="label">坐山/门向方位 — 8 方位罗盘</label>
            <div className="card card-highlight" style={{ background: "rgba(8,10,15,0.35)", border: "1px solid var(--line)" }}>
              <CompassDial value={form.sittingDir} onChange={(code) => setForm({ ...form, sittingDir: code })} size={280} />
              <div className="text-[10px] mt-2 text-center" style={{ color: COLOR.muted }}>
                选定后: <span style={{ color: COLOR.goldBright }}>{form.sittingDir}</span> · 玄空 {sittingInfo.sans}山
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" className="btn-ghost tap" onClick={() => { setForm(DEFAULT_FORM); setCharts(null); }}>
            重置
          </button>
          <button type="submit" className="btn-primary gold-sweep-host" disabled={loading}>
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <ProgressArc value={0.6} size={18} />
                排盘中...
              </span>
            ) : "风水排盘"}
          </button>
        </div>
        {error && (
          <div className="p-3 rounded text-sm" style={{ background: "rgba(200,85,61,0.1)", color: COLOR.danger }}>
            {error}
          </div>
        )}
      </form>

      {/* Results */}
      {charts && (
        <div className="space-y-4">
          {/* Combined Summary */}
          {charts.bazhai && charts.xuankong && <CombinedSummary bazhai={charts.bazhai} xuankong={charts.xuankong} />}

          {/* Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("bazhai")}
              className={`px-4 py-2 rounded text-sm font-semibold transition ${activeTab === "bazhai" ? "" : "opacity-60"}`}
              style={{
                background: activeTab === "bazhai" ? "rgba(201,162,75,0.10)" : "transparent",
                border: `1px solid ${activeTab === "bazhai" ? COLOR.gold : COLOR.lineSoft}`,
                color: activeTab === "bazhai" ? COLOR.goldBright : COLOR.muted,
              }}
            >
              八宅明镜
            </button>
            <button
              onClick={() => setActiveTab("xuankong")}
              className={`px-4 py-2 rounded text-sm font-semibold transition ${activeTab === "xuankong" ? "" : "opacity-60"}`}
              style={{
                background: activeTab === "xuankong" ? "rgba(91,141,239,0.10)" : "transparent",
                border: `1px solid ${activeTab === "xuankong" ? COLOR.azure : COLOR.lineSoft}`,
                color: activeTab === "xuankong" ? COLOR.azure : COLOR.muted,
              }}
            >
              玄空飞星
            </button>
          </div>

          {/* Chart Display */}
          {activeTab === "bazhai" && charts.bazhai && <ChartRenderer chart={charts.bazhai} />}
          {activeTab === "xuankong" && charts.xuankong && <ChartRenderer chart={charts.xuankong} />}
        </div>
      )}

      {/* Getting Started */}
      {!charts && (
        <div className="card card-highlight" style={{ opacity: 0.6 }}>
          <h3 className="text-sm mb-2" style={{ color: COLOR.gold }}>
            关于风水专区
          </h3>
          <p className="text-sm leading-relaxed mb-3" style={{ color: COLOR.inkSoft }}>
            风水专区整合八宅明镜与玄空飞星两种古典风水体系。
          </p>
          <ul className="text-xs space-y-2" style={{ color: COLOR.muted }}>
            <li>
              <strong style={{ color: COLOR.gold }}>八宅明镜</strong> — 根据居住者出生年份起命卦，分东四/西四命，按各卦大游年歌定八星（生气/天医/延年/伏位/祸害/六煞/五鬼/绝命）方位。有坐向时可结合宅卦做宅命相配分析。
            </li>
            <li>
              <strong style={{ color: COLOR.azure }}>玄空飞星</strong> — 按建造年份定三元九运，以24山坐向起运盘/山盘/向盘飞星，以五星生克定各星旺衰（旺/生/退/死/煞），判断旺山旺向/双星到向/上山下水等格局。
            </li>
          </ul>
          <p className="text-xs mt-3" style={{ color: COLOR.muted }}>
            以上为传统文化参考，不等于完整风水布局，重大决定请咨询专业人士。填入出生信息与坐向年份后开始排盘。
          </p>
        </div>
      )}
    </div>
  );
}

/** Combined summary card across both feng shui methods */
function CombinedSummary({ bazhai, xuankong }: { bazhai: ChartResult; xuankong: ChartResult }) {
  const br = bazhai.raw || {};
  const xr = xuankong.raw || {};

  const lifeGua = br.life_gua || "?";
  const isEast = br.is_east ? "东四命" : "西四命";
  const houseGua = br.house_gua;
  const match = br.house_resident_match;
  const pattern = xr.pattern || "?";
  const period = xr.period || "?";

  return (
    <div className="card card-highlight" style={{ borderColor: COLOR.goldDim }}>
      <h3 className="text-sm mb-3" style={{ color: COLOR.goldBright }}>
        风水合参 · 宅命总览
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <SummaryItem label="命卦" value={lifeGua} sub={isEast} tone="gold" />
        <SummaryItem
          label="宅卦"
          value={houseGua || "未指定坐向"}
          sub={houseGua ? (br.house_is_east ? "东四宅" : "西四宅") : ""}
          tone="azure"
        />
        <SummaryItem
          label="宅命相配"
          value={match ? (match.matched ? "✓ 相配" : "✗ 不配") : "—"}
          sub={match?.level || ""}
          tone={match?.matched ? "jade" : "danger"}
        />
        <SummaryItem label="玄空格局" value={pattern} sub={period} tone="gold" />
      </div>
      {match?.description && (
        <div className="mt-3 text-xs leading-relaxed p-2 rounded" style={{ background: "rgba(8,10,15,0.4)", color: COLOR.inkSoft, borderLeft: `3px solid ${COLOR.goldDim}` }}>
          {match.description}
        </div>
      )}
    </div>
  );
}

function SummaryItem({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: string }) {
  const toneColor = tone === "jade" ? COLOR.jade : tone === "danger" ? COLOR.danger : tone === "azure" ? COLOR.azure : COLOR.gold;
  return (
    <div className="p-2 rounded" style={{ background: "rgba(8,10,15,0.3)", border: `1px solid ${COLOR.lineSoft}` }}>
      <div className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>{label}</div>
      <div className="text-sm font-semibold mt-1" style={{ color: toneColor }}>{value}</div>
      {sub && <div className="text-[10px] mt-0.5" style={{ color: COLOR.muted }}>{sub}</div>}
    </div>
  );
}
