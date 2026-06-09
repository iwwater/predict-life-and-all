/** ReadingForm — 12 术法聚合解读通用表单
 *
 * FORM-001: 通用 Reading 表单，适配 /api/reading
 * FORM-002: 出生信息组件（年、月、日、时、分、性别、地点）
 * FORM-003: 问题输入组件
 * FORM-004: 合盘表单（本人 + 对方 birth）
 * FORM-005: 风水表单（朝向、类型、城市、入住时间）
 * FORM-006: 决策表单（具体问题、备选方案、所在地）
 * FORM-007: 年度运势表单（目标年份）
 * FORM-008: 今日运势表单（当前日期 + 问题）
 * FORM-009: 表单校验
 * FORM-010: 提交到 /api/reading
 * FORM-011: loading 状态
 * FORM-012: 错误提示
 */
import { useState, useCallback, type FormEvent } from "react";
import { COLOR } from "./ui";
import type { Birth, ReadingAPIRequest, ReadingDepth } from "../lib/types";

// ── 12 standard goal types ────────────────────────────────────────────────

const GOAL_OPTIONS = [
  { value: "", label: "自动识别", icon: "🤖" },
  { value: "general_life", label: "本命格局", icon: "🔮", desc: "综合命盘·整体人生" },
  { value: "career", label: "事业工作", icon: "💼", desc: "创业·跳槽·职场发展" },
  { value: "wealth", label: "财运", icon: "💰", desc: "投资·收入·理财" },
  { value: "relationship", label: "感情姻缘", icon: "💕", desc: "恋爱·婚姻·桃花" },
  { value: "compatibility", label: "合盘分析", icon: "💞", desc: "两人合不合·配对" },
  { value: "yearly", label: "年度运势", icon: "📅", desc: "流年·全年运势" },
  { value: "monthly", label: "月运", icon: "🌙", desc: "本月运势" },
  { value: "daily", label: "今日运势", icon: "☀️", desc: "今日·日运" },
  { value: "decision", label: "重大决策", icon: "⚖️", desc: "该不该·要不要" },
  { value: "timing", label: "时机分析", icon: "⏰", desc: "什么时候·最佳时机" },
  { value: "fengshui", label: "风水调理", icon: "🏠", desc: "住宅·搬家·方位" },
  { value: "health_reflection", label: "健康自省", icon: "🧘", desc: "压力·睡眠·身心状态" },
];

// ── Props ──────────────────────────────────────────────────────────────────

export interface ReadingFormProps {
  onSubmit: (req: ReadingAPIRequest) => void;
  loading: boolean;
  error: string | null;
}

export interface FormData {
  question: string;
  goal: string;
  depth: ReadingDepth;
  // Birth
  year: string; month: string; day: string; hour: string; minute: string;
  gender: "male" | "female" | "unspecified";
  calendar: "gregorian" | "lunar";
  lat: string; lng: string; tz: string;
  // Target birth (compatibility)
  t_year: string; t_month: string; t_day: string; t_hour: string; t_minute: string;
  t_gender: "male" | "female" | "unspecified";
  t_lat: string; t_lng: string; t_tz: string;
  showTargetBirth: boolean;
  // Space (fengshui)
  sitting: string; construction_year: string; address: string;
  showSpace: boolean;
  // Decision
  alternatives: string;
  // Yearly
  target_year: string;
}

const DEFAULT_FORM: FormData = {
  question: "", goal: "", depth: "standard",
  year: "1990", month: "6", day: "15", hour: "8", minute: "0",
  gender: "male", calendar: "gregorian",
  lat: "31.23", lng: "121.47", tz: "Asia/Shanghai",
  t_year: "", t_month: "", t_day: "", t_hour: "", t_minute: "",
  t_gender: "female", t_lat: "", t_lng: "", t_tz: "Asia/Shanghai",
  showTargetBirth: false, showSpace: false,
  sitting: "", construction_year: "", address: "",
  alternatives: "", target_year: String(new Date().getFullYear()),
};

// ── Field helpers ──────────────────────────────────────────────────────────

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] uppercase tracking-widest" style={{ color: COLOR.muted }}>
        {label}
      </label>
      {children}
      {hint && <span className="text-[9px]" style={{ color: COLOR.goldDim }}>{hint}</span>}
    </div>
  );
}

function Input({ value, onChange, placeholder, type = "text", className = "" }: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string; className?: string;
}) {
  return (
    <input
      type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className={`text-sm rounded-lg px-3 py-2 border bg-transparent outline-none focus:ring-1 transition ${className}`}
      style={{
        borderColor: "var(--line)", color: "var(--ink)",
        background: "rgba(22,27,34,0.6)",
      }}
    />
  );
}

function Select({ value, onChange, options }: {
  value: string; onChange: (v: string) => void; options: { value: string; label: string }[];
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className="text-sm rounded-lg px-3 py-2 border bg-transparent outline-none focus:ring-1 transition"
      style={{
        borderColor: "var(--line)", color: "var(--ink)",
        background: "rgba(22,27,34,0.8)",
      }}>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

// ── Birth sub-component ────────────────────────────────────────────────────

function BirthFields({ prefix, f, set }: {
  prefix: string; f: FormData; set: (patch: Partial<FormData>) => void;
}) {
  const isTarget = prefix === "t_";
  const year = isTarget ? f.t_year : f.year;
  const month = isTarget ? f.t_month : f.month;
  const day = isTarget ? f.t_day : f.t_day;
  const hour = isTarget ? f.t_hour : f.hour;
  const minute = isTarget ? f.t_minute : f.minute;
  const gender = isTarget ? f.t_gender : f.gender;
  const lat = isTarget ? f.t_lat : f.lat;
  const lng = isTarget ? f.t_lng : f.lng;
  const tz = isTarget ? f.t_tz : f.tz;

  const update = (k: string, v: string) => set({ [`${prefix}${k}`]: v } as any);

  return (
    <div className="space-y-3 p-4 rounded-xl border" style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.3)" }}>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        <Field label="年"><Input value={year} onChange={(v) => update("year", v)} type="number" /></Field>
        <Field label="月"><Input value={month} onChange={(v) => update("month", v)} type="number" /></Field>
        <Field label="日"><Input value={day} onChange={(v) => update("day", v)} type="number" /></Field>
        <Field label="时"><Input value={hour} onChange={(v) => update("hour", v)} type="number" /></Field>
        <Field label="分"><Input value={minute} onChange={(v) => update("minute", v)} type="number" /></Field>
        <Field label="性别">
          <Select value={gender} onChange={(v) => update("gender", v)}
            options={[
              { value: "male", label: "男" }, { value: "female", label: "女" },
              { value: "unspecified", label: "不限" },
            ]} />
        </Field>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Field label="纬度" hint="如 31.23">
          <Input value={lat} onChange={(v) => update("lat", v)} placeholder="31.23" />
        </Field>
        <Field label="经度" hint="如 121.47">
          <Input value={lng} onChange={(v) => update("lng", v)} placeholder="121.47" />
        </Field>
        <Field label="时区" hint="Asia/Shanghai">
          <Input value={tz} onChange={(v) => update("tz", v)} placeholder="Asia/Shanghai" />
        </Field>
        <Field label="历法">
          <Select value={f.calendar} onChange={(v) => set({ calendar: v as "gregorian" | "lunar" })}
            options={[{ value: "gregorian", label: "公历" }, { value: "lunar", label: "农历" }]} />
        </Field>
      </div>
    </div>
  );
}

// ── Main Form ──────────────────────────────────────────────────────────────

export function ReadingForm({ onSubmit, loading, error }: ReadingFormProps) {
  const [f, setF] = useState<FormData>(DEFAULT_FORM);
  const [errors, setErrors] = useState<string[]>([]);

  const update = useCallback((patch: Partial<FormData>) => {
    setF((prev) => ({ ...prev, ...patch }));
  }, []);

  // FORM-009: Validation
  const validate = useCallback((): boolean => {
    const e: string[] = [];
    if (!f.question.trim()) e.push("请输入您的问题");
    if (f.question.trim().length < 2) e.push("问题至少 2 个字符");
    // Birth validation: if year is provided, validate ranges
    const y = parseInt(f.year);
    if (f.year && (isNaN(y) || y < 1500 || y > 2100)) e.push("出生年份应在 1500-2100 之间");
    const m = parseInt(f.month);
    if (f.month && (isNaN(m) || m < 1 || m > 12)) e.push("出生月份应在 1-12 之间");
    const d = parseInt(f.day);
    if (f.day && (isNaN(d) || d < 1 || d > 31)) e.push("出生日期应在 1-31 之间");
    setErrors(e);
    return e.length === 0;
  }, [f.question, f.year, f.month, f.day]);

  const handleSubmit = useCallback((e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const birth: Birth | null = f.year ? {
      year: parseInt(f.year), month: parseInt(f.month), day: parseInt(f.day),
      hour: parseInt(f.hour), minute: parseInt(f.minute),
      gender: f.gender, calendar: f.calendar,
      lat: f.lat ? parseFloat(f.lat) : null,
      lng: f.lng ? parseFloat(f.lng) : null,
      tz: f.tz,
    } : null;

    const targetBirth: Birth | null = (f.showTargetBirth && f.t_year) ? {
      year: parseInt(f.t_year), month: parseInt(f.t_month), day: parseInt(f.t_day),
      hour: parseInt(f.t_hour), minute: parseInt(f.t_minute),
      gender: f.t_gender, calendar: "gregorian",
      lat: f.t_lat ? parseFloat(f.t_lat) : null,
      lng: f.t_lng ? parseFloat(f.t_lng) : null,
      tz: f.t_tz,
    } : null;

    const space = f.showSpace ? {
      sitting: f.sitting || null,
      construction_year: f.construction_year ? parseInt(f.construction_year) : null,
      address: f.address || null,
    } : null;

    // Enrich question with context from special fields
    let question = f.question.trim();
    if (f.alternatives && f.goal === "decision") {
      question = `${question}（备选方案：${f.alternatives}）`;
    }
    if (f.target_year && (f.goal === "yearly" || f.goal === "monthly")) {
      question = `${question}（目标年份：${f.target_year}）`;
    }

    const req: ReadingAPIRequest = {
      goal: f.goal || null,
      question,
      birth,
      target_birth: targetBirth,
      space,
      depth: f.depth,
    };
    onSubmit(req);
  }, [f, validate, onSubmit]);

  const showBirth = f.goal !== "daily";
  const showTarget = f.showTargetBirth || f.goal === "compatibility";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* ── Goal selector ── */}
      <div>
        <label className="text-xs uppercase tracking-widest mb-2 block" style={{ color: COLOR.gold }}>
          {"> 分析领域（可选，留空则自动识别）"}
        </label>
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
          {GOAL_OPTIONS.map((g) => (
            <button key={g.value} type="button"
              onClick={() => update({ goal: g.value, showTargetBirth: g.value === "compatibility", showSpace: g.value === "fengshui" })}
              className={`text-left p-2.5 rounded-lg border transition text-xs ${f.goal === g.value ? "ring-1" : ""}`}
              style={{
                borderColor: f.goal === g.value ? COLOR.gold : COLOR.lineSoft,
                background: f.goal === g.value ? "rgba(201,162,75,0.08)" : "rgba(22,27,34,0.3)",
                color: f.goal === g.value ? COLOR.goldBright : COLOR.inkSoft,
              }}>
              <div className="text-base mb-0.5">{g.icon}</div>
              <div className="font-semibold">{g.label}</div>
              {g.desc && <div className="text-[9px] mt-0.5" style={{ color: COLOR.muted }}>{g.desc}</div>}
            </button>
          ))}
        </div>
      </div>

      {/* ── Question input (FORM-003) ── */}
      <Field label="您的问题" hint="用自然语言描述您想了解的方面">
        <textarea value={f.question} onChange={(e) => update({ question: e.target.value })}
          placeholder="例如：我该换工作吗？今年财运怎么样？这个房子风水如何？我和TA合不合？..."
          rows={3}
          className="text-sm rounded-lg px-3 py-2 border bg-transparent outline-none focus:ring-1 transition resize-y"
          style={{ borderColor: COLOR.line, color: COLOR.ink, background: "rgba(22,27,34,0.6)" }} />
      </Field>

      {/* ── Birth info (FORM-002) ── */}
      {showBirth && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs uppercase tracking-widest" style={{ color: COLOR.gold }}>
              {"> 出生信息（可选，不填则使用默认值）"}
            </label>
            {f.goal === "compatibility" && (
              <button type="button" onClick={() => update({ showTargetBirth: !f.showTargetBirth })}
                className="text-[10px] px-2 py-1 rounded border" style={{ borderColor: COLOR.goldDim, color: COLOR.goldBright }}>
                {f.showTargetBirth ? "隐藏对方信息" : "+ 添加对方出生信息"}
              </button>
            )}
          </div>
          <BirthFields prefix="" f={f} set={update} />
        </div>
      )}

      {/* ── Target birth (FORM-004) ── */}
      {f.showTargetBirth && (
        <div>
          <label className="text-xs uppercase tracking-widest mb-2 block" style={{ color: COLOR.jade }}>
            {"> 对方出生信息"}
          </label>
          <BirthFields prefix="t_" f={f} set={update} />
        </div>
      )}

      {/* ── Fengshui-specific (FORM-005) ── */}
      {(f.showSpace || f.goal === "fengshui") && (
        <div className="p-4 rounded-xl border space-y-2" style={{ borderColor: COLOR.jadeDim, background: "rgba(22,27,34,0.3)" }}>
          <label className="text-xs uppercase tracking-widest block" style={{ color: COLOR.jade }}>
            {"> 空间信息（风水用）"}
          </label>
          <div className="grid grid-cols-3 gap-2">
            <Field label="坐向"><Input value={f.sitting} onChange={(v) => update({ sitting: v })} placeholder="如 坐北朝南" /></Field>
            <Field label="建造年份"><Input value={f.construction_year} onChange={(v) => update({ construction_year: v })} type="number" /></Field>
            <Field label="地址"><Input value={f.address} onChange={(v) => update({ address: v })} placeholder="可选" /></Field>
          </div>
        </div>
      )}

      {/* ── Decision-specific (FORM-006) ── */}
      {f.goal === "decision" && (
        <div className="p-4 rounded-xl border space-y-2" style={{ borderColor: COLOR.azureDim, background: "rgba(22,27,34,0.3)" }}>
          <label className="text-xs uppercase tracking-widest block" style={{ color: COLOR.azure }}>
            {"> 决策详情"}
          </label>
          <Field label="备选方案（可选）" hint="帮助系统更准确地分析">
            <Input value={f.alternatives} onChange={(v) => update({ alternatives: v })} placeholder="如：留在当前公司 vs 加入新团队" />
          </Field>
        </div>
      )}

      {/* ── Yearly/Monthly-specific (FORM-007) ── */}
      {(f.goal === "yearly" || f.goal === "monthly") && (
        <div className="p-4 rounded-xl border space-y-2" style={{ borderColor: COLOR.goldDim, background: "rgba(22,27,34,0.3)" }}>
          <Field label="目标年份">
            <Input value={f.target_year} onChange={(v) => update({ target_year: v })} type="number" />
          </Field>
        </div>
      )}

      {/* ── Depth selector ── */}
      <div className="flex items-center gap-4">
        <label className="text-xs uppercase tracking-widest" style={{ color: COLOR.muted }}>
          报告深度：
        </label>
        {(["free", "standard", "premium"] as ReadingDepth[]).map((d) => (
          <button key={d} type="button" onClick={() => update({ depth: d })}
            className={`text-xs px-3 py-1.5 rounded-lg border transition ${f.depth === d ? "ring-1" : ""}`}
            style={{
              borderColor: f.depth === d ? COLOR.gold : COLOR.lineSoft,
              background: f.depth === d ? "rgba(201,162,75,0.1)" : "transparent",
              color: f.depth === d ? COLOR.goldBright : COLOR.muted,
            }}>
            {{ free: "免费", standard: "标准", premium: "深度" }[d]}
          </button>
        ))}
      </div>

      {/* ── FORM-009: Validation errors ── */}
      {errors.length > 0 && (
        <div className="p-3 rounded-lg text-xs space-y-1" style={{ background: "rgba(200,85,61,0.08)", border: "1px solid rgba(200,85,61,0.35)", color: COLOR.danger }}>
          {errors.map((err, i) => <div key={i}>⚠ {err}</div>)}
        </div>
      )}

      {/* ── FORM-012: API errors ── */}
      {error && (
        <div className="p-3 rounded-lg text-xs" style={{ background: "rgba(200,85,61,0.08)", border: "1px solid rgba(200,85,61,0.35)", color: COLOR.danger }}>
          ⚠ 请求失败：{error}
        </div>
      )}

      {/* ── Submit ── */}
      <button type="submit" disabled={loading}
        className="w-full py-3 rounded-xl font-semibold text-sm transition disabled:opacity-50"
        style={{
          background: loading ? "rgba(201,162,75,0.2)" : `linear-gradient(135deg, ${COLOR.gold} 0%, ${COLOR.goldBright} 100%)`,
          color: loading ? COLOR.goldDim : "#0a0a0a",
        }}>
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <span className="inline-block w-4 h-4 rounded-full border-2 border-dashed spin-slow"
              style={{ borderColor: COLOR.gold }} />
            12 术法计算中...
          </span>
        ) : (
          "🔮 开始综合分析（12 术法合参）"
        )}
      </button>
      <p className="text-[9px] text-center" style={{ color: COLOR.muted }}>
        一次输入，系统自动调用 12 种术法交叉验证 · 包含免责声明
      </p>
    </form>
  );
}
