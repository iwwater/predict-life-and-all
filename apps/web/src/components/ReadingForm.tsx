/** ReadingForm — 综合解读通用表单（「古籍×仪器」纸墨风格）
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
import type { Birth, ReadingAPIRequest, ReadingDepth } from "../lib/types";

// ── 12 standard goal types（无 emoji）───────────────────────────────────────

const GOAL_OPTIONS = [
  { value: "", label: "自动识别", desc: "系统自动判断" },
  { value: "general_life", label: "本命格局", desc: "综合命盘·整体人生" },
  { value: "career", label: "事业工作", desc: "创业·跳槽·职场发展" },
  { value: "wealth", label: "财运", desc: "投资·收入·理财" },
  { value: "relationship", label: "感情姻缘", desc: "恋爱·婚姻·桃花" },
  { value: "compatibility", label: "合盘分析", desc: "两人合不合·配对" },
  { value: "yearly", label: "年度运势", desc: "流年·全年运势" },
  { value: "monthly", label: "月运", desc: "本月运势" },
  { value: "daily", label: "今日运势", desc: "今日·日运" },
  { value: "decision", label: "重大决策", desc: "该不该·要不要" },
  { value: "timing", label: "时机分析", desc: "什么时候·最佳时机" },
  { value: "fengshui", label: "风水调理", desc: "住宅·搬家·方位" },
  { value: "health_reflection", label: "健康自省", desc: "压力·睡眠·身心状态" },
];

// ── 12 methods with birth requirements ──────────────────────────────────────

const ALL_METHODS = [
  { id: "bazi_v2", label: "八字", needsBirth: true, group: "东方命理" },
  { id: "ziwei", label: "紫微", needsBirth: true, group: "东方命理" },
  { id: "qimen", label: "奇门", needsBirth: true, group: "东方命理" },
  { id: "liuyao", label: "六爻", needsBirth: "conditional", group: "东方命理" },
  { id: "meihua", label: "梅花", needsBirth: "conditional", group: "东方命理" },
  { id: "fengshui", label: "风水", needsBirth: true, group: "风水" },
  { id: "bazhai", label: "八宅", needsBirth: true, group: "风水" },
  { id: "xuankong", label: "玄空", needsBirth: false, group: "风水" },
  { id: "western", label: "西方占星", needsBirth: true, group: "西方" },
  { id: "vedic", label: "吠陀占星", needsBirth: true, group: "西方" },
  { id: "tarot", label: "塔罗", needsBirth: false, group: "西方" },
  { id: "numerology", label: "数字命理", needsBirth: "minimal", group: "西方" },
];

/** Compute which enabled methods actually need birth based on current mode settings */
function methodsNeedingBirth(f: FormData): string[] {
  const needs: string[] = [];
  for (const m of ALL_METHODS) {
    if (!f.enabledMethods.includes(m.id)) continue;
    const nb = m.needsBirth;
    if (nb === false) continue;
    if (nb === "conditional") {
      const mode = m.id === "liuyao" ? f.liuyao_mode : f.meihua_mode;
      if (mode === "time_qigua") needs.push(m.id);
    } else {
      needs.push(m.id);
    }
  }
  return needs;
}

/** Compute which enabled methods explicitly don't need birth */
function methodsNotNeedingBirth(f: FormData): string[] {
  const notNeeds: string[] = [];
  for (const m of ALL_METHODS) {
    if (!f.enabledMethods.includes(m.id)) continue;
    const nb = m.needsBirth;
    if (nb === false) { notNeeds.push(m.id); continue; }
    if (nb === "conditional") {
      const mode = m.id === "liuyao" ? f.liuyao_mode : f.meihua_mode;
      if (mode !== "time_qigua") notNeeds.push(m.id);
    }
  }
  return notNeeds;
}

const METHOD_LABELS: Record<string, string> = Object.fromEntries(
  ALL_METHODS.map(m => [m.id, m.label])
);

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
  // Method-specific options
  liuyao_mode: string; meihua_mode: string;
  tarot_spread: string; tarot_mode: string;
  showAdvanced: boolean;
  // Method toggles (all enabled by default)
  enabledMethods: string[];
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
  liuyao_mode: "time_qigua", meihua_mode: "time_qigua",
  tarot_spread: "celtic_cross", tarot_mode: "reflective",
  showAdvanced: false,
  enabledMethods: ["bazi_v2","ziwei","qimen","liuyao","meihua","fengshui","bazhai","xuankong","western","vedic","tarot","numerology"],
};

// ── Paper-style field helpers ───────────────────────────────────────────

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="paper-label">{label}</label>
      {children}
      {hint && <span style={{ fontSize: "0.58rem", color: "var(--ink-soft)" }}>{hint}</span>}
    </div>
  );
}

function Input({ value, onChange, placeholder, type = "text", className = "" }: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string; className?: string;
}) {
  return (
    <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className={`paper-input ${className}`} />
  );
}

function Select({ value, onChange, options }: {
  value: string; onChange: (v: string) => void; options: { value: string; label: string }[];
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className="paper-input" style={{ cursor: "pointer" }}>
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
  const day = isTarget ? f.t_day : f.day;
  const hour = isTarget ? f.t_hour : f.hour;
  const minute = isTarget ? f.t_minute : f.minute;
  const gender = isTarget ? f.t_gender : f.gender;
  const lat = isTarget ? f.t_lat : f.lat;
  const lng = isTarget ? f.t_lng : f.lng;
  const tz = isTarget ? f.t_tz : f.tz;

  const update = (k: string, v: string) => set({ [`${prefix}${k}`]: v } as any);

  return (
    <div className="paper-frame space-y-3">
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
      methods: f.enabledMethods.length < 12 ? f.enabledMethods : null,
      method_options: {
        liuyao_mode: f.liuyao_mode,
        meihua_mode: f.meihua_mode,
        tarot_spread: f.tarot_spread,
        tarot_mode: f.tarot_mode,
      },
      depth: f.depth,
    };
    onSubmit(req);
  }, [f, validate, onSubmit]);

  const showBirth = f.goal !== "daily";
  const showTarget = f.showTargetBirth || f.goal === "compatibility";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* ── Goal selector ── */}
      <div>
        <label className="paper-label" style={{ marginBottom: "0.5rem", display: "block" }}>
          分析领域（可选，留空则自动识别）
        </label>
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-1.5">
          {GOAL_OPTIONS.map((g) => (
            <button key={g.value} type="button"
              onClick={() => update({ goal: g.value, showTargetBirth: g.value === "compatibility", showSpace: g.value === "fengshui" })}
              className="paper-grid-cell" style={{
                textAlign: "left", cursor: "pointer",
                borderColor: f.goal === g.value ? "var(--cinnabar)" : "var(--rule)",
                background: f.goal === g.value ? "rgba(176,58,46,0.04)" : "transparent",
              }}>
              <div style={{
                fontWeight: 600, fontSize: "0.72rem",
                color: f.goal === g.value ? "var(--cinnabar)" : "var(--ink)",
                fontFamily: "'Noto Serif SC', serif",
              }}>{g.label}</div>
              {g.desc && <div style={{ fontSize: "0.58rem", color: "var(--ink-soft)", marginTop: "0.15rem", lineHeight: 1.3 }}>{g.desc}</div>}
            </button>
          ))}
        </div>
      </div>

      {/* ── Question input (FORM-003) ── */}
      <Field label="您的问题" hint="用自然语言描述您想了解的方面">
        <textarea value={f.question} onChange={(e) => update({ question: e.target.value })}
          placeholder="例如：我该换工作吗？今年财运怎么样？这个房子风水如何？我和TA合不合？..."
          rows={3}
          className="paper-input" style={{ resize: "vertical", lineHeight: 1.7 }} />
      </Field>

      {/* ── Birth info (FORM-002) ── */}
      {showBirth && (
        <div>
          <div className="flex items-center justify-between" style={{ marginBottom: "0.5rem" }}>
            <label className="paper-label" style={{ marginBottom: 0 }}>
              出生信息（可选，不填则使用默认值）
            </label>
            {f.goal === "compatibility" && (
              <button type="button" onClick={() => update({ showTargetBirth: !f.showTargetBirth })}
                className="paper-btn-ghost" style={{ fontSize: "0.62rem" }}>
                {f.showTargetBirth ? "隐藏对方信息" : "+ 添加对方出生信息"}
              </button>
            )}
          </div>
          <BirthFields prefix="" f={f} set={update} />
          {/* Dynamic birth-needed hint */}
          {(() => {
            const needing = methodsNeedingBirth(f);
            const notNeeding = methodsNotNeedingBirth(f);
            const total = f.enabledMethods.length;
            if (needing.length === 0 && total > 0) {
              return (
                <p style={{ fontSize: "0.6rem", color: "var(--verdigris)", marginTop: "0.4rem" }}>
                  ✓ 当前启用的术法均不需要出生信息，可留空直接提交。
                </p>
              );
            }
            if (notNeeding.length > 0) {
              const notLabels = notNeeding.map(id => METHOD_LABELS[id] || id).join("、");
              return (
                <p style={{ fontSize: "0.6rem", color: "var(--ink-soft)", marginTop: "0.4rem" }}>
                  {notLabels} 不需要出生信息；出生信息仅供 {needing.map(id => METHOD_LABELS[id] || id).join("、")} 使用。
                </p>
              );
            }
            return null;
          })()}
        </div>
      )}

      {/* ── Target birth (FORM-004) ── */}
      {f.showTargetBirth && (
        <div>
          <label className="paper-label" style={{ marginBottom: "0.5rem", display: "block", color: "var(--verdigris)" }}>
            对方出生信息
          </label>
          <BirthFields prefix="t_" f={f} set={update} />
        </div>
      )}

      {/* ── Fengshui-specific (FORM-005) ── */}
      {(f.showSpace || f.goal === "fengshui") && (
        <div className="paper-frame space-y-2" style={{ borderColor: "rgba(90,112,88,0.3)" }}>
          <label className="paper-label" style={{ color: "var(--verdigris)" }}>
            空间信息（风水用）
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
        <div className="paper-frame space-y-2" style={{ borderColor: "rgba(47,72,88,0.3)" }}>
          <label className="paper-label" style={{ color: "var(--indigo)" }}>
            决策详情
          </label>
          <Field label="备选方案（可选）" hint="帮助系统更准确地分析">
            <Input value={f.alternatives} onChange={(v) => update({ alternatives: v })} placeholder="如：留在当前公司 vs 加入新团队" />
          </Field>
        </div>
      )}

      {/* ── Yearly/Monthly-specific (FORM-007) ── */}
      {(f.goal === "yearly" || f.goal === "monthly") && (
        <div className="paper-frame space-y-2">
          <Field label="目标年份">
            <Input value={f.target_year} onChange={(v) => update({ target_year: v })} type="number" />
          </Field>
        </div>
      )}

      {/* ── 术法高级设置 ── */}
      <div>
        <button type="button" onClick={() => update({ showAdvanced: !f.showAdvanced })}
          className="paper-label flex items-center gap-1" style={{
            cursor: "pointer", border: "none", background: "none",
            fontSize: "0.72rem", fontFamily: "'Noto Serif SC', serif",
            color: "var(--ink-soft)", marginBottom: f.showAdvanced ? "0.5rem" : "0",
          }}>
          <span style={{ fontSize: "0.8rem" }}>{f.showAdvanced ? "▾" : "▸"}</span>
          术法高级设置（可选）
        </button>
        {f.showAdvanced && (
          <div className="space-y-3" style={{
            border: "1px solid var(--rule)", borderRadius: "4px",
            padding: "0.75rem", background: "rgba(0,0,0,0.01)",
          }}>
            {/* 术法开关 */}
            <div>
              <label className="paper-label" style={{ fontSize: "0.68rem", marginBottom: "0.25rem", display: "block" }}>
                启用术法（已选 {f.enabledMethods.length}/12）
              </label>
              <div className="flex flex-wrap gap-1.5">
                {ALL_METHODS.map((m) => (
                  <button key={m.id} type="button"
                    onClick={() => {
                      const next = f.enabledMethods.includes(m.id)
                        ? f.enabledMethods.filter(x => x !== m.id)
                        : [...f.enabledMethods, m.id];
                      update({ enabledMethods: next });
                    }}
                    className="paper-tag" style={{
                      cursor: "pointer", fontSize: "0.6rem",
                      color: f.enabledMethods.includes(m.id) ? "var(--cinnabar)" : "var(--rule)",
                      borderColor: f.enabledMethods.includes(m.id) ? "var(--cinnabar)" : "var(--rule)",
                      opacity: f.enabledMethods.includes(m.id) ? 1 : 0.5,
                    }}>{m.label}</button>
                ))}
              </div>
            </div>

            {/* 六爻 */}
            <div>
              <label className="paper-label" style={{ fontSize: "0.68rem" }}>六爻 · 起卦方式</label>
              <div className="flex gap-1.5" style={{ marginTop: "0.25rem" }}>
                {[
                  { v: "time_qigua", l: "时间起卦", d: "根据出生时间" },
                  { v: "manual_coin", l: "手动摇卦", d: "自行摇铜钱六次" },
                  { v: "number_qigua", l: "数字起卦", d: "由问题自动生成" },
                ].map((opt) => (
                  <button key={opt.v} type="button" onClick={() => update({ liuyao_mode: opt.v })}
                    className="paper-tag" style={{
                      cursor: "pointer", fontSize: "0.62rem",
                      color: f.liuyao_mode === opt.v ? "var(--cinnabar)" : "var(--ink-soft)",
                      borderColor: f.liuyao_mode === opt.v ? "var(--cinnabar)" : "var(--rule)",
                    }}>{opt.l}</button>
                ))}
              </div>
            </div>
            {/* 梅花 */}
            <div>
              <label className="paper-label" style={{ fontSize: "0.68rem" }}>梅花易数 · 起卦方式</label>
              <div className="flex gap-1.5" style={{ marginTop: "0.25rem" }}>
                {[
                  { v: "time_qigua", l: "时间起卦", d: "根据出生时间" },
                  { v: "number_qigua", l: "数字起卦", d: "由问题自动生成" },
                  { v: "external_omen", l: "外应起卦", d: "以问题文字起卦" },
                ].map((opt) => (
                  <button key={opt.v} type="button" onClick={() => update({ meihua_mode: opt.v })}
                    className="paper-tag" style={{
                      cursor: "pointer", fontSize: "0.62rem",
                      color: f.meihua_mode === opt.v ? "var(--cinnabar)" : "var(--ink-soft)",
                      borderColor: f.meihua_mode === opt.v ? "var(--cinnabar)" : "var(--rule)",
                    }}>{opt.l}</button>
                ))}
              </div>
            </div>
            {/* 塔罗 */}
            <div>
              <label className="paper-label" style={{ fontSize: "0.68rem" }}>塔罗 · 牌阵</label>
              <div className="flex gap-1.5" style={{ marginTop: "0.25rem" }}>
                {[
                  { v: "celtic_cross", l: "凯尔特十字", d: "10张·全面" },
                  { v: "three_card", l: "三张牌", d: "过去·现在·未来" },
                  { v: "single", l: "单张牌", d: "快速指引" },
                  { v: "horseshoe", l: "马蹄阵", d: "7张·趋势" },
                  { v: "star", l: "星形阵", d: "6张·多角度" },
                ].map((opt) => (
                  <button key={opt.v} type="button" onClick={() => update({ tarot_spread: opt.v })}
                    className="paper-tag" style={{
                      cursor: "pointer", fontSize: "0.62rem",
                      color: f.tarot_spread === opt.v ? "var(--cinnabar)" : "var(--ink-soft)",
                      borderColor: f.tarot_spread === opt.v ? "var(--cinnabar)" : "var(--rule)",
                    }}>{opt.l}</button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Depth selector ── */}
      <div className="flex items-center gap-3">
        <span className="paper-label" style={{ marginBottom: 0 }}>报告深度</span>
        {(["free", "standard", "premium"] as ReadingDepth[]).map((d) => (
          <button key={d} type="button" onClick={() => update({ depth: d })}
            className="paper-tag" style={{
              cursor: "pointer",
              color: f.depth === d ? "var(--cinnabar)" : "var(--ink-soft)",
              borderColor: f.depth === d ? "var(--cinnabar)" : "var(--rule)",
            }}>
            {{ free: "速览", standard: "标准", premium: "深度" }[d]}
          </button>
        ))}
      </div>

      {/* ── FORM-009: Validation errors ── */}
      {errors.length > 0 && (
        <div className="paper-error">
          {errors.map((err, i) => <div key={i}>{err}</div>)}
        </div>
      )}

      {/* ── FORM-012: API errors ── */}
      {error && (
        <div className="paper-error">请求失败：{error}</div>
      )}

      {/* ── Submit ── */}
      <button type="submit" disabled={loading}
        className="paper-btn w-full justify-center" style={{ fontSize: "0.88rem" }}>
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <span className="paper-pulse" style={{ width: "1rem", height: "1rem" }} />
            多术法计算中...
          </span>
        ) : (
          "开始综合分析"
        )}
      </button>
      <p className="paper-source" style={{ textAlign: "center", fontSize: "0.6rem" }}>
        一次输入，系统自动调用多种术法交叉验证 · 包含免责声明
      </p>
    </form>
  );
}
