import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useBirthStore } from "../store/birth";
import {
  castEventCase,
  createEventCase,
  createEventCaseVersion,
  updateEventCaseContext,
  type CompassFengShuiResponse,
} from "../lib/api";
import type { CastResponse, EventCase } from "../lib/types";
import { ReadingReportView } from "../components/ReadingReportView";

const DEPTH_OPTIONS = [
  { value: "free", label: "快速" },
  { value: "standard", label: "标准" },
  { value: "premium", label: "深度" },
] as const;

export function Cases() {
  const navigate = useNavigate();
  const routerLocation = useLocation();
  const birthStore = useBirthStore();
  const [question, setQuestion] = useState("接下来三个月，我是否适合推进这件事？");
  const [target, setTarget] = useState("");
  const [timeHorizon, setTimeHorizon] = useState("未来三个月");
  const [location, setLocation] = useState(birthStore.birth.city || "");
  const [depth, setDepth] = useState<(typeof DEPTH_OPTIONS)[number]["value"]>("standard");
  const [eventCase, setEventCase] = useState<EventCase | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<CastResponse | null>(null);
  const [changedCondition, setChangedCondition] = useState("");
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // CompassPage 注入的待消费数据
  const [pendingFengShui, setPendingFengShui] = useState<CompassFengShuiResponse | null>(null);
  const [pendingSitting, setPendingSitting] = useState<string | null>(null);
  const [pendingDirection, setPendingDirection] = useState<string | null>(null);

  // 消费 CompassPage 通过 navigate state 传来的待处理数据
  useEffect(() => {
    const state = (routerLocation.state || {}) as {
      pendingSitting?: string;
      pendingFengShui?: CompassFengShuiResponse;
      pendingDirection?: string;
    };
    const navFeng = state.pendingFengShui;
    const navSitting = state.pendingSitting;
    const navDir = state.pendingDirection;
    // 兜底: 从 localStorage 读取 (旧入口或刷新后)
    let storedFeng: CompassFengShuiResponse | null = null;
    let storedSitting: string | null = null;
    try {
      const raw = localStorage.getItem("pending_fengshui");
      if (raw) storedFeng = JSON.parse(raw) as CompassFengShuiResponse;
      storedSitting = localStorage.getItem("pending_sitting");
    } catch {
      // 忽略 localStorage 解析错误
    }
    const feng = navFeng || storedFeng;
    const sitting = navSitting || storedSitting;
    const dir = navDir || feng?.direction || null;
    if (feng) {
      setPendingFengShui(feng);
      // 预填问题与目标
      setQuestion(
        (prev) =>
          prev ||
          `我现住的房子坐${sitting || feng.sitting}向${dir || feng.direction || ""}, 这次合参想了解近期迁居/调整布局的吉凶.`,
      );
      setTarget((prev) => prev || `坐${sitting || feng.sitting}`);
      setLocation((prev) => prev || birthStore.birth.city || "");
      // 消费后清掉 (避免下次进入页面误用)
      localStorage.removeItem("pending_fengshui");
    }
    if (sitting) {
      setPendingSitting(sitting);
      localStorage.removeItem("pending_sitting");
    }
    if (dir) setPendingDirection(dir);
    // 路由历史清空 state, 避免刷新再次触发
    if (navFeng || navSitting) {
      window.history.replaceState({}, document.title, routerLocation.pathname);
    }
  }, [routerLocation.state, routerLocation.pathname, birthStore.birth.city]);

  const selectedCount = useMemo(() => Object.keys(answers).length, [answers]);
  const missingRequired = useMemo(() => {
    if (!eventCase) return 0;
    return eventCase.minimal_questions.filter((q) => q.required && !answers[q.id]).length;
  }, [answers, eventCase]);

  async function createCase(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading("create");
    setError(null);
    setResult(null);
    setAnswers({});
    try {
      const next = await createEventCase({
        question: question.trim(),
        birth: birthStore.toApiBirth(),
        target: target.trim() || null,
        time_horizon: timeHorizon.trim() || null,
        location: location.trim() || null,
        current_city: birthStore.birth.city || null,
      });
      setEventCase(next);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(null);
    }
  }

  async function submitContext() {
    if (!eventCase) return;
    setLoading("context");
    setError(null);
    try {
      const next = await updateEventCaseContext(eventCase.case_id, {
        answers,
        birth: birthStore.toApiBirth(),
        constraints: {
          target: target.trim() || null,
          time_horizon: timeHorizon.trim() || null,
          location: location.trim() || null,
        },
      });
      setEventCase(next);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(null);
    }
  }

  async function castCase() {
    if (!eventCase) return;
    setLoading("cast");
    setError(null);
    try {
      const key = `case-${eventCase.case_id}-v${eventCase.version}`;
      const next = await castEventCase(eventCase.case_id, { depth }, key);
      setEventCase(next.case);
      setResult(next);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(null);
    }
  }

  async function createVersion() {
    if (!eventCase || !changedCondition.trim()) return;
    setLoading("version");
    setError(null);
    try {
      const next = await createEventCaseVersion(eventCase.case_id, {
        changed_condition: changedCondition.trim(),
      });
      setEventCase(next);
      setAnswers({});
      setResult(null);
      setChangedCondition("");
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-6">
      <header className="paper-frame">
        <div className="paper-eyebrow">Event Case</div>
        <h1 className="paper-title" style={{ marginTop: "0.25rem" }}>
          <span className="stamp" />
          <span>问事档案</span>
        </h1>
        <p style={{ color: "var(--ink-soft)", fontSize: "0.82rem", lineHeight: 1.8, marginTop: "0.5rem" }}>
          一事一档：先记录问题和现实条件，再回答系统追问，最后固定一次合参结果。当前为本地演示存储，刷新或重启后端后档案可能消失。
        </p>
      </header>

      {/* pending fengshui 注入提示 */}
      {pendingFengShui && (
        <div
          className="paper-frame flex flex-col gap-2 p-4"
          style={{ background: "var(--paper)", borderColor: "var(--cinnabar)" }}
        >
          <div className="flex items-center gap-2 flex-wrap">
            <span className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "var(--cinnabar)" }}>
              罗盘已注入
            </span>
            <span style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>
              来自 CompassPage 的风水上下文已自动带入问题与目标,可直接调整后立档
            </span>
            <button
              type="button"
              className="paper-btn-ghost text-sm"
              onClick={() => {
                setPendingFengShui(null);
                setPendingSitting(null);
                setPendingDirection(null);
              }}
            >
              清除
            </button>
          </div>
          <div style={{ fontSize: "0.76rem", color: "var(--ink-soft)", lineHeight: 1.7 }}>
            坐山: <strong style={{ color: "var(--ink)" }}>{pendingSitting || pendingFengShui.sitting}</strong>
            {pendingFengShui.sitting_zh && ` (${pendingFengShui.sitting_zh})`}
            {" · "}朝向: {pendingDirection || pendingFengShui.direction}
            {" · "}精度: {pendingFengShui.quality}
            {pendingFengShui.dual_candidate && (
              <span style={{ color: "var(--cinnabar)" }}> · 临界角双候选</span>
            )}
          </div>
          {pendingFengShui.bazhai?.命卦 && (
            <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
              八宅命卦: {pendingFengShui.bazhai.命卦}
              {pendingFengShui.xuankong?.格局 && ` · 玄空: ${pendingFengShui.xuankong.格局}`}
            </div>
          )}
        </div>
      )}

      {/* birth time accuracy nudge */}
      {birthStore.birth.birth_time_accuracy !== "exact" && (
        <div className="paper-frame flex items-center gap-4 p-4" style={{ background: "var(--paper)" }}>
          <div className="text-2xl">🕐</div>
          <div className="flex-1">
            <div style={{ fontSize: "0.82rem", fontWeight: 600 }}>出生时辰未校正</div>
            <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>
              当前使用 {birthStore.birth.birth_time_accuracy === "approximate" ? "大概时辰" : birthStore.birth.birth_time_accuracy === "period" ? "粗略时间段" : "未确认时辰"}，
              校正后可提高部分术法精度
            </div>
          </div>
          <button
            type="button"
            className="paper-btn-ghost text-sm"
            onClick={() => navigate("/birth-time")}
          >
            去校正 →
          </button>
        </div>
      )}

      <form onSubmit={createCase} className="paper-frame space-y-4">
        <div>
          <label className="paper-eyebrow">第一步：立档</label>
          <textarea
            className="paper-input"
            style={{ minHeight: 96, marginTop: "0.5rem" }}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="把问题写成一个具体事件，例如：我是否应该接受这个 offer？"
          />
        </div>

        <div className="grid md:grid-cols-3 gap-3">
          <input className="paper-input" value={target} onChange={(e) => setTarget(e.target.value)} placeholder="对象/目标，可选" />
          <input className="paper-input" value={timeHorizon} onChange={(e) => setTimeHorizon(e.target.value)} placeholder="时间范围" />
          <input className="paper-input" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="地点，可选" />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button type="submit" className="paper-btn" disabled={loading === "create"}>
            {loading === "create" ? "立档中..." : "创建问事档案"}
          </button>
          <span className="paper-source">
            使用全站出生信息：{birthStore.birth.year}-{birthStore.birth.month}-{birthStore.birth.day} {birthStore.birth.hour}:00
          </span>
        </div>
      </form>

      {eventCase && (
        <section className="paper-frame space-y-4">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div>
              <div className="paper-eyebrow">第二步：补足语境</div>
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 700, color: "var(--ink)", marginTop: "0.2rem" }}>
                {eventCase.case_id} · v{eventCase.version}
              </h2>
            </div>
            <span className="paper-tag">{eventCase.status}</span>
          </div>

          {eventCase.minimal_questions.length > 0 ? (
            <div className="space-y-4">
              {eventCase.minimal_questions.map((q) => (
                <div key={q.id}>
                  <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "0.86rem", fontWeight: 600, marginBottom: "0.5rem" }}>
                    {q.prompt}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {q.options.map((option) => (
                      <button
                        key={option}
                        type="button"
                        className="paper-tag"
                        onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: option }))}
                        style={{
                          cursor: "pointer",
                          color: answers[q.id] === option ? "var(--cinnabar)" : "var(--ink-soft)",
                          borderColor: answers[q.id] === option ? "var(--cinnabar)" : "var(--rule)",
                        }}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <button type="button" className="paper-btn-ghost" onClick={submitContext} disabled={loading === "context" || missingRequired > 0}>
                {loading === "context" ? "提交中..." : `提交追问答案 (${selectedCount}/${eventCase.minimal_questions.length})`}
              </button>
            </div>
          ) : (
            <div className="paper-empty" style={{ padding: "1rem", fontSize: "0.78rem", color: "var(--ink-soft)" }}>
              这个问题暂不需要额外追问，可以直接固定起盘。
            </div>
          )}
        </section>
      )}

      {eventCase && (
        <section className="paper-frame space-y-4">
          <div className="paper-eyebrow">第三步：固定结果</div>
          <div className="flex items-center gap-2 flex-wrap">
            {DEPTH_OPTIONS.map((item) => (
              <button
                key={item.value}
                type="button"
                className="paper-tag"
                onClick={() => setDepth(item.value)}
                style={{
                  cursor: "pointer",
                  color: depth === item.value ? "var(--cinnabar)" : "var(--ink-soft)",
                  borderColor: depth === item.value ? "var(--cinnabar)" : "var(--rule)",
                }}
              >
                {item.label}
              </button>
            ))}
            <button type="button" className="paper-btn" onClick={castCase} disabled={loading === "cast"}>
              {loading === "cast" ? "合参中..." : "固定本次合参结果"}
            </button>
          </div>
          <p className="paper-source">
            同一个档案版本会使用固定 Idempotency-Key，重复点击不会生成多份不同结果。
          </p>
        </section>
      )}

      {error && <div className="paper-error">{error}</div>}

      {result && (
        <div className="space-y-5">
          <ReadingReportView result={result.result} />

          <section className="paper-frame space-y-3">
            <div className="paper-eyebrow">条件变化</div>
            <p style={{ color: "var(--ink-soft)", fontSize: "0.76rem", lineHeight: 1.7 }}>
              如果现实条件变了，不覆盖旧结果，而是基于当前档案生成新版本再重新合参。
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <input
                className="paper-input"
                style={{ flex: "1 1 260px" }}
                value={changedCondition}
                onChange={(e) => setChangedCondition(e.target.value)}
                placeholder="例如：对方已经给了正式 offer，薪资比预期低"
              />
              <button type="button" className="paper-btn-ghost" onClick={createVersion} disabled={loading === "version" || !changedCondition.trim()}>
                {loading === "version" ? "生成中..." : "生成新版本"}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
