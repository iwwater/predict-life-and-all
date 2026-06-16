import React, { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useBirthStore } from "../store/birth";
import { rectifyBirthTime, type RectifyResponse, type RectifyCandidate } from "../lib/api";

type BirthAccuracy = "exact" | "approximate" | "period" | "unknown";
type DayPeriod = "morning" | "afternoon" | "evening" | "night";

interface HistoricalEvent {
  year: number;
  month?: number;
  category: string;
  description?: string;
}

const EVENT_CATEGORIES = [
  { value: "education", label: "升学/考试" },
  { value: "career_start", label: "第一份工作" },
  { value: "career_change", label: "职业变化" },
  { value: "move", label: "搬家/迁居" },
  { value: "relationship", label: "恋爱/感情" },
  { value: "marriage", label: "结婚" },
  { value: "family", label: "家庭变化" },
  { value: "finance", label: "财务明显变化" },
  { value: "entrepreneurship", label: "创业" },
  { value: "health", label: "健康重大事件" },
  { value: "other", label: "其他" },
] as const;

const DAY_PERIODS = [
  { value: "morning" as DayPeriod, label: "早", sub: "6-10点" },
  { value: "afternoon" as DayPeriod, label: "午", sub: "11-15点" },
  { value: "evening" as DayPeriod, label: "晚", sub: "16-20点" },
  { value: "night" as DayPeriod, label: "夜", sub: "21-4点" },
];

/* ─── component ──────────────────────────────────────────── */
export function BirthTimeRectifyPage() {
  const navigate = useNavigate();
  const birthStore = useBirthStore();
  const birth = birthStore.birth;

  const [accuracy, setAccuracy] = useState<BirthAccuracy>("unknown");
  const [approxHour, setApproxHour] = useState(8);
  const [dayPeriod, setDayPeriod] = useState<DayPeriod>("morning");
  const [events, setEvents] = useState<HistoricalEvent[]>([]);
  const [result, setResult] = useState<RectifyResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<RectifyCandidate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextQAnswer, setNextQAnswer] = useState<string | null>(null);

  /* ── event helpers ── */
  function addEvent() {
    setEvents((prev) => [
      ...prev,
      { year: 2010, category: "education", description: "" },
    ]);
  }

  function removeEvent(i: number) {
    setEvents((prev) => prev.filter((_, idx) => idx !== i));
  }

  function updateEvent(i: number, patch: Partial<HistoricalEvent>) {
    setEvents((prev) => prev.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));
  }

  /* ── submit ── */
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedCandidate(null);
    setNextQAnswer(null);
    try {
      const body = {
        birth: birthStore.toApiBirth(),
        birth_time_accuracy: accuracy,
        approximate_hour: accuracy === "approximate" ? approxHour : undefined,
        day_period: accuracy === "period" ? dayPeriod : undefined,
        known_events: events.filter((ev) => ev.year > 1900),
        keep_top_n: 4,
      };
      const data = await rectifyBirthTime(body);
      setResult(data);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  /* ── select candidate ── */
  function handleSelectCandidate(c: RectifyCandidate) {
    setSelectedCandidate(c);
  }

  function handleConfirmAndContinue() {
    if (!selectedCandidate || !result) return;
    // Update birth hour in store — map Chinese branch to hour
    const branchHourMap: Record<string, number> = {
      子: 23, 丑: 1, 寅: 3, 卯: 5, 辰: 7, 巳: 9,
      午: 11, 未: 13, 申: 15, 酉: 17, 戌: 19, 亥: 21,
    };
    const newHour = branchHourMap[selectedCandidate.branch] ?? birth.hour;
    birthStore.setBirth({
      ...birth,
      hour: newHour,
      minute: 0,
      birth_time_accuracy: accuracy,
    });
    navigate("/cases");
  }

  /* ── confidence badge ── */
  const confidenceColor: Record<string, string> = {
    low: "var(--ink-soft)",
    medium: "var(--amber, #b45309)",
    high: "var(--jade, #059669)",
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
      {/* header */}
      <div>
        <h1 className="text-2xl font-serif" style={{ color: "var(--ink)" }}>
          出生时辰校正
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--ink-soft)" }}>
          校时结果用于缩小候选范围，不宣称绝对还原真实出生时间。
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* ── birth info summary ── */}
        <div className="card p-4 flex items-center gap-4">
          <div className="text-3xl">🕐</div>
          <div>
            <div className="font-medium">{birth.year}年{birth.month}月{birth.day}日</div>
            <div className="text-sm" style={{ color: "var(--ink-soft)" }}>
              {birth.gender === "male" ? "男" : birth.gender === "female" ? "女" : "性别未填"}
              {birth.city ? ` · ${birth.city}` : ""}
            </div>
          </div>
        </div>

        {/* ── accuracy mode ── */}
        <div className="card p-4 space-y-3">
          <label className="text-sm font-medium" style={{ color: "var(--ink)" }}>
            出生时间准确度
          </label>
          <div className="grid grid-cols-2 gap-2">
            {([
              ["exact", "准确时辰", "精确到时辰，如 08:30"],
              ["approximate", "大概时辰", "只知道大概，如上午"],
              ["period", "上午/下午/晚上", "只知道白天或晚上"],
              ["unknown", "完全不知道", "不知道哪个时辰"],
            ] as [BirthAccuracy, string, string][]).map(([val, title, desc]) => (
              <button
                key={val}
                type="button"
                onClick={() => setAccuracy(val)}
                className={`btn text-left px-3 py-2 text-sm transition-all ${
                  accuracy === val
                    ? "btn-primary"
                    : "border"
                }`}
                style={accuracy !== val ? { borderColor: "var(--border)", background: "transparent" } : {}}
              >
                <div className="font-medium">{title}</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--ink-soft)" }}>{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* ── approximate: hour slider ── */}
        {accuracy === "approximate" && (
          <div className="card p-4 space-y-3">
            <label className="text-sm font-medium" style={{ color: "var(--ink)" }}>
              大概时辰 — {approxHour}:00 左右
            </label>
            <input
              type="range"
              min={0}
              max={22}
              step={2}
              value={approxHour}
              onChange={(e) => setApproxHour(Number(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-xs" style={{ color: "var(--ink-soft)" }}>
              <span>子时 23:00</span>
              <span>午时 11:00</span>
              <span>亥时 21:00</span>
            </div>
          </div>
        )}

        {/* ── period: day period picker ── */}
        {accuracy === "period" && (
          <div className="card p-4 space-y-3">
            <label className="text-sm font-medium" style={{ color: "var(--ink)" }}>
              大概时间段
            </label>
            <div className="grid grid-cols-4 gap-2">
              {DAY_PERIODS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setDayPeriod(p.value)}
                  className={`btn text-sm py-2 ${dayPeriod === p.value ? "btn-primary" : "border"}`}
                  style={dayPeriod !== p.value ? { borderColor: "var(--border)", background: "transparent" } : {}}
                >
                  {p.label}
                  <span className="block text-xs" style={{ color: "var(--ink-soft)" }}>{p.sub}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── historical events ── */}
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium" style={{ color: "var(--ink)" }}>
              人生事件（可选，最多8条）
            </label>
            <span className="text-xs" style={{ color: "var(--ink-soft)" }}>
              提供3条以上可提高校时准确度
            </span>
          </div>

          {events.map((ev, i) => (
            <div key={i} className="flex gap-2 items-start border-b pb-2" style={{ borderColor: "var(--border)" }}>
              <div className="flex-1 grid grid-cols-3 gap-2">
                <input
                  type="number"
                  min={1950}
                  max={2025}
                  value={ev.year}
                  onChange={(e) => updateEvent(i, { year: Number(e.target.value) })}
                  placeholder="年份"
                  className="input input-bordered text-sm w-full"
                />
                <select
                  value={ev.category}
                  onChange={(e) => updateEvent(i, { category: e.target.value })}
                  className="select select-bordered text-sm w-full"
                >
                  {EVENT_CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={ev.description || ""}
                  onChange={(e) => updateEvent(i, { description: e.target.value })}
                  placeholder="简述（选填）"
                  className="input input-bordered text-sm w-full"
                />
              </div>
              <button
                type="button"
                onClick={() => removeEvent(i)}
                className="btn btn-ghost btn-xs text-error"
              >
                ✕
              </button>
            </div>
          ))}

          {events.length < 8 && (
            <button
              type="button"
              onClick={addEvent}
              className="btn btn-outline btn-sm"
            >
              + 添加事件
            </button>
          )}
        </div>

        {/* ── submit ── */}
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full py-3 text-base"
        >
          {loading ? (
            <span className="paper-pulse" style={{ width: "1.2rem", height: "1.2rem" }} />
          ) : (
            "开始校正"
          )}
        </button>

        {error && (
          <div className="text-sm text-error text-center">{error}</div>
        )}
      </form>

      {/* ── results ── */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-serif" style={{ color: "var(--ink)" }}>
              候选时辰
            </h2>
            <span className="text-xs" style={{ color: "var(--ink-soft)" }}>
              耗时 {result.elapsed_ms}ms · 置信度
              <span style={{ color: confidenceColor[result.confidence_level] }}>
                {" "}{result.confidence_level === "high" ? "高" : result.confidence_level === "medium" ? "中" : "低"}
              </span>
            </span>
          </div>

          {/* uncertainty note */}
          <div className="text-xs px-3 py-2 rounded" style={{ background: "var(--paper)", color: "var(--ink-soft)" }}>
            {result.uncertainty_note}
          </div>

          {/* candidate cards */}
          <div className="space-y-3">
            {result.candidates.map((c, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSelectCandidate(c)}
                className={`card p-4 w-full text-left transition-all ${
                  selectedCandidate?.branch === c.branch ? "ring-2 ring-jade" : ""
                }`}
                style={{
                  "--tw-ring-color": selectedCandidate?.branch === c.branch ? "var(--jade, #059669)" : undefined,
                } as React.CSSProperties}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-serif">{c.branch}时</span>
                      <span className="text-sm" style={{ color: "var(--ink-soft)" }}>{c.label}</span>
                      {i === 0 && (
                        <span className="badge badge-jade text-xs">最可能</span>
                      )}
                    </div>
                    {/* evidence */}
                    <ul className="mt-1 space-y-0.5">
                      {c.evidence.map((ev, j) => (
                        <li key={j} className="text-xs" style={{ color: "var(--ink-soft)" }}>
                          · {ev}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="text-right shrink-0">
                    <div
                      className="text-lg font-bold"
                      style={{ color: confidenceColor[c.confidence] }}
                    >
                      {Math.round(c.score * 100)}
                    </div>
                    <div className="text-xs" style={{ color: "var(--ink-soft)" }}>分</div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* next question */}
          {result.next_question && !nextQAnswer && (
            <div className="card p-4 space-y-3" style={{ background: "var(--paper)" }}>
              <p className="text-sm font-medium" style={{ color: "var(--ink)" }}>
                {result.next_question.prompt}
              </p>
              <div className="flex flex-wrap gap-2">
                {result.next_question.options.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setNextQAnswer(opt)}
                    className="btn btn-outline btn-sm"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* common / differences */}
          {result.common_conclusions.length > 0 && (
            <div className="card p-4 space-y-2 text-sm">
              <div>
                <span className="font-medium">共同基础：</span>
                {result.common_conclusions.join(" ")}
              </div>
              {result.main_differences.length > 0 && (
                <div style={{ color: "var(--ink-soft)" }}>
                  <span className="font-medium">候选差异：</span>
                  {result.main_differences.join(" ")}
                </div>
              )}
            </div>
          )}

          {/* confirm button */}
          {selectedCandidate && (
            <button
              type="button"
              onClick={handleConfirmAndContinue}
              className="btn btn-primary w-full py-3 text-base"
            >
              确认 {selectedCandidate.branch}时，继续问事 →
            </button>
          )}
        </div>
      )}
    </div>
  );
}