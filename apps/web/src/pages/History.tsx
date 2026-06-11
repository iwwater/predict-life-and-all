// 历史页: 本地历史记录（「古籍×仪器」纸墨风格）
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useHistory } from "../store/history";
import { EmptyBox } from "../components/ui";
import { Jargon } from "../components/Jargon";
import { SUBJECTS } from "../lib/method-info";
import type { Subject } from "../lib/types";

const SUBJECT_LABEL: Record<Subject, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<Subject, string>,
);

const REFLECT_LABEL: Record<string, string> = {
  accurate: "准", inaccurate: "不准", pending: "待观察",
};

type Filter = Subject | "all";

export function History() {
  const { items, remove, clear } = useHistory();
  const [filter, setFilter] = useState<Filter>("all");

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: items.length };
    for (const it of items) { const k = it.subject || "_none"; c[k] = (c[k] || 0) + 1; }
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    return items.filter((it) => it.subject === filter);
  }, [items, filter]);

  if (items.length === 0) {
    return (
      <EmptyBox>
        还没有问题日志。<Link to="/cast" className="paper-link" style={{ marginLeft: "0.35rem" }}>去排盘 →</Link>
      </EmptyBox>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="paper-title"><span className="stamp" />我的问题日志</h1>
        <button className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} onClick={() => {
          if (confirm("确认清空所有日志？清空后无法恢复。")) clear();
        }}>清空</button>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <FilterChip active={filter === "all"} onClick={() => setFilter("all")} label="全部" count={counts.all} />
        {SUBJECTS.map((s) => {
          const n = counts[s.key] || 0;
          if (n === 0) return null;
          return <FilterChip key={s.key} active={filter === s.key} onClick={() => setFilter(s.key)} label={s.label} count={n} />;
        })}
      </div>

      {filtered.length === 0 ? (
        <EmptyBox>当前筛选下没有条目。</EmptyBox>
      ) : (
        <ul className="space-y-1.5">
          {filtered.map((it) => (
            <li key={it.id} className="paper-grid-cell flex items-start justify-between gap-3" style={{ padding: "0.6rem 0.85rem" }}>
              <div className="min-w-0 flex-1">
                <div style={{ fontSize: "0.82rem", color: "var(--ink)", fontFamily: "'JetBrains Mono', monospace" }}>
                  <span className="paper-mono" style={{ marginRight: "0.35rem", fontSize: "0.62rem" }}>
                    <Jargon term="命主" mode="plain" />
                  </span>
                  {it.birth.year}-{it.birth.month}-{it.birth.day} {it.birth.hour}:{String(it.birth.minute).padStart(2,"0")}
                  <span style={{ marginLeft: "0.5rem", color: "var(--ink-soft)", fontSize: "0.72rem" }}>{it.birth.gender}</span>
                </div>
                <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.25rem" }}>
                  {new Date(it.ts).toLocaleString()}
                  {" · "}{it.methods.map((m) => m).join(" / ")}
                  {it.question && <> · 「{it.question}」</>}
                </div>
                <div className="flex flex-wrap gap-1" style={{ marginTop: "0.3rem" }}>
                  {it.subject && <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>{SUBJECT_LABEL[it.subject] || it.subject}</span>}
                  {it.favorite && <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar)" }}>★ 收藏</span>}
                  {it.reflection && <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>反馈 · {REFLECT_LABEL[it.reflection.verdict] || it.reflection.verdict}</span>}
                  {it.spread && <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--ink-soft)" }}>spread: {it.spread}</span>}
                </div>
              </div>
              <div className="flex flex-col gap-1 shrink-0">
                <button className="paper-btn-ghost" style={{ fontSize: "0.65rem", padding: "0.15rem 0.5rem" }}
                  onClick={() => {
                    sessionStorage.setItem("mystic:result", JSON.stringify({
                      birth: it.birth, question: it.question || "",
                      charts: it.charts, methods: it.methods as any,
                    }));
                    sessionStorage.setItem("mystic:result_id", it.id);
                    window.location.href = `/result?ts=${Date.now()}`;
                  }}>查看</button>
                <button className="paper-btn-ghost" style={{ fontSize: "0.65rem", padding: "0.15rem 0.5rem" }}
                  onClick={() => window.location.href = `/cast?fromHistory=${encodeURIComponent(it.id)}`}>
                  继续追问
                </button>
                <button className="paper-btn-ghost" style={{ fontSize: "0.65rem", padding: "0.15rem 0.5rem", color: "var(--cinnabar)" }}
                  onClick={() => remove(it.id)}>删</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function FilterChip({ active, onClick, label, count }: {
  active: boolean; onClick: () => void; label: string; count: number;
}) {
  return (
    <button type="button" onClick={onClick} className="paper-tag" style={{
      color: active ? "var(--cinnabar)" : "var(--ink-soft)",
      borderColor: active ? "var(--cinnabar)" : "var(--rule)",
      cursor: "pointer", fontSize: "0.72rem",
    }}>
      {label} <span style={{ opacity: 0.5 }}>· {count}</span>
    </button>
  );
}
