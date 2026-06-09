// 历史页:列历史记录(本地 IndexedDB via zustand persist)
// Cut 4:改"我的问题日志" — 加 subject 筛选 + 继续追问按钮
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useHistory } from "../store/history";
import { COLOR, EmptyBox } from "../components/ui";
import { Jargon } from "../components/Jargon";
import { SUBJECTS } from "../lib/method-info";
import type { Subject } from "../lib/types";
import { GanZhiStripe } from "../components/MysticElements";

const SUBJECT_LABEL: Record<Subject, string> = SUBJECTS.reduce(
  (acc, s) => ({ ...acc, [s.key]: s.label }),
  {} as Record<Subject, string>,
);

const REFLECT_LABEL: Record<string, string> = {
  accurate: "准",
  inaccurate: "不准",
  pending: "待观察",
};

type Filter = Subject | "all";

export function History() {
  const { items, remove, clear } = useHistory();
  const [filter, setFilter] = useState<Filter>("all");

  // 统计每个 subject 的条目数(用于筛选条)
  const counts = useMemo(() => {
    const c: Record<string, number> = { all: items.length };
    for (const it of items) {
      const k = it.subject || "_none";
      c[k] = (c[k] || 0) + 1;
    }
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    return items.filter((it) => it.subject === filter);
  }, [items, filter]);

  if (items.length === 0) {
    return (
      <EmptyBox>
        还没有问题日志。<Link to="/cast" className="underline ml-1" style={{ color: COLOR.gold }}>去排盘 →</Link>
      </EmptyBox>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-1">
        <GanZhiStripe />
      </div>
      <div className="flex items-center justify-between">
        <h2 className="text-lg" style={{ color: COLOR.goldBright }}>我的问题日志</h2>
        <button className="btn-ghost text-xs" onClick={() => {
          if (confirm("确认清空所有日志?清空后无法恢复。")) clear();
        }}>清空</button>
      </div>

      {/* subject 筛选条:只显示有条目的 subject + 全部 */}
      <div className="flex flex-wrap gap-1.5">
        <FilterChip active={filter === "all"} onClick={() => setFilter("all")} label="全部" count={counts.all} />
        {SUBJECTS.map((s) => {
          const n = counts[s.key] || 0;
          if (n === 0) return null;
          return (
            <FilterChip
              key={s.key}
              active={filter === s.key}
              onClick={() => setFilter(s.key)}
              label={s.label}
              count={n}
            />
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <EmptyBox>当前筛选下没有条目。</EmptyBox>
      ) : (
        <ul className="space-y-2">
          {filtered.map((it) => (
            <li key={it.id} className="card card-highlight lift-on-hover flex items-start justify-between gap-3 text-sm">
              <div className="min-w-0 flex-1">
                <div style={{ color: COLOR.ink }}>
                  <span className="text-[10px] mr-1" style={{ color: COLOR.muted }}>
                    <Jargon term="命主" mode="plain" />
                  </span>
                  {it.birth.year}-{it.birth.month}-{it.birth.day} {it.birth.hour}:{String(it.birth.minute).padStart(2, "0")}
                  <span className="ml-2" style={{ color: COLOR.muted }}>{it.birth.gender}</span>
                </div>
                <div className="text-[11px] mt-1" style={{ color: COLOR.muted }}>
                  {new Date(it.ts).toLocaleString()}
                  {" · "}
                  {it.methods.map((m) => m).join(" / ")}
                  {it.question && <> · 「{it.question}」</>}
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {it.subject && (
                    <span className="tag" style={{ background: "rgba(201,162,75,0.12)", color: COLOR.goldBright }}>
                      {SUBJECT_LABEL[it.subject] || it.subject}
                    </span>
                  )}
                  {it.favorite && (
                    <span className="tag" style={{ color: COLOR.goldBright }}>★ 收藏</span>
                  )}
                  {it.reflection && (
                    <span className="tag" style={{ color: COLOR.muted }}>
                      反馈 · {REFLECT_LABEL[it.reflection.verdict] || it.reflection.verdict}
                    </span>
                  )}
                  {it.spread && (
                    <span className="tag" style={{ color: COLOR.muted }}>spread: {it.spread}</span>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-1.5 shrink-0">
                <button className="btn-ghost text-xs"
                  onClick={() => {
                    sessionStorage.setItem("mystic:result", JSON.stringify({
                      birth: it.birth, question: it.question || "",
                      charts: it.charts, methods: it.methods as any,
                    }));
                    sessionStorage.setItem("mystic:result_id", it.id);
                    window.location.href = `/result?ts=${Date.now()}`;
                  }}>查看</button>
                <button className="btn-ghost text-xs"
                  onClick={() => window.location.href = `/cast?fromHistory=${encodeURIComponent(it.id)}`}>
                  继续追问
                </button>
                <button className="btn-ghost text-xs" onClick={() => remove(it.id)}>删</button>
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
    <button type="button" onClick={onClick}
      className="tag"
      style={active
        ? { color: COLOR.goldBright, borderColor: COLOR.gold, background: "rgba(201,162,75,0.10)" }
        : { color: COLOR.muted }}>
      {label} <span style={{ opacity: 0.6 }}>· {count}</span>
    </button>
  );
}
