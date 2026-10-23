/** BaziLuckTimeline — 大运 / 流年 时间轴
 *
 *  八字页原来只把 8 步大运平铺成一条横轴, 且高亮永远落在第一步(用 i===0 判断),
 *  用户看不出"我现在在哪一步"。这里:
 *   - 按当前年份定位所处大运并高亮(朱框 + 「现在」标记), 自动滚到可见位置
 *   - 点任一大运, 下方展开这十年的流年干支与虚岁, 当前年再单独标出
 *  数据来自 chart.raw.horoscope.yearly(引擎已算好的 90 年)与 normalized.timeline。
 */
import { useEffect, useMemo, useRef, useState } from "react";

interface LuckCycle {
  from: string;
  to: string;
  label: string;
  score?: number | null;
}

interface YearItem {
  year: number;
  ganzhi: string;
}

const s = {
  chip: {
    minWidth: 78,
    padding: "0.35rem 0.5rem",
    borderRadius: 3,
    cursor: "pointer",
    textAlign: "center" as const,
    flexShrink: 0,
  },
  mono: { fontFamily: "'JetBrains Mono', monospace" },
};

export function BaziLuckTimeline({
  timeline,
  yearly,
  birthYear,
  isZh = true,
}: {
  timeline: LuckCycle[];
  yearly?: YearItem[];
  birthYear?: number;
  isZh?: boolean;
}) {
  const nowYear = new Date().getFullYear();
  const currentIdx = useMemo(
    () =>
      timeline.findIndex((t) => Number(t.from) <= nowYear && nowYear <= Number(t.to)),
    [timeline, nowYear],
  );
  const [picked, setPicked] = useState<number>(currentIdx >= 0 ? currentIdx : 0);
  const activeRef = useRef<HTMLButtonElement | null>(null);
  const stripRef = useRef<HTMLDivElement | null>(null);

  // 初次渲染把「当前大运」滚到中间, 免得手机上默认看到 1997 年
  useEffect(() => {
    const strip = stripRef.current;
    const el = activeRef.current;
    if (!strip || !el) return;
    const target = el.offsetLeft - strip.clientWidth / 2 + el.clientWidth / 2;
    strip.scrollTo({ left: Math.max(0, target) });
  }, [timeline.length]);

  if (!timeline.length) return null;

  const cur = timeline[picked];
  const years = (yearly || []).filter(
    (y) => cur && Number(cur.from) <= y.year && y.year <= Number(cur.to),
  );

  return (
    <div className="space-y-2">
      <div
        ref={stripRef}
        className="flex overflow-x-auto gap-1.5 pb-2"
        style={{ scrollbarWidth: "thin" }}
      >
        {timeline.map((t, i) => {
          const isNow = i === currentIdx;
          const isPicked = i === picked;
          return (
            <button
              key={i}
              ref={isNow ? activeRef : undefined}
              type="button"
              onClick={() => setPicked(i)}
              aria-pressed={isPicked}
              style={{
                ...s.chip,
                background: isPicked ? "rgba(176,58,46,0.08)" : "var(--paper-2)",
                border: `1px solid ${isPicked ? "var(--cinnabar)" : isNow ? "#c9a227" : "var(--rule)"}`,
              }}
            >
              <div style={{ fontSize: "0.72rem", fontWeight: 600, color: isPicked ? "var(--cinnabar)" : "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                {t.label}
              </div>
              <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", ...s.mono }}>
                {t.from}–{t.to}
              </div>
              {isNow && (
                <div style={{ fontSize: "0.62rem", color: "#9a6a1f" }}>{isZh ? "现在" : "now"}</div>
              )}
            </button>
          );
        })}
      </div>

      {years.length === 0 && (
        <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>
          {isZh ? "该段流年不在引擎计算范围内。" : "Annual pillars unavailable for this cycle."}
        </div>
      )}

      {years.length > 0 && (
        <div>
          <div style={{ fontSize: "0.66rem", color: "var(--ink-soft)", marginBottom: "0.3rem" }}>
            {isZh ? `${cur.label} 期间的流年` : `Annual pillars in ${cur.label}`}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(62px, 1fr))", gap: "0.25rem" }}>
            {years.map((y) => {
              const isThisYear = y.year === nowYear;
              return (
                <div
                  key={y.year}
                  style={{
                    padding: "0.25rem 0.15rem",
                    textAlign: "center",
                    borderRadius: 3,
                    background: isThisYear ? "rgba(201,162,39,0.14)" : "var(--paper-2)",
                    border: `1px solid ${isThisYear ? "#c9a227" : "var(--rule)"}`,
                  }}
                >
                  <div style={{ fontSize: "0.68rem", fontWeight: 600, color: isThisYear ? "#9a6a1f" : "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
                    {y.ganzhi}
                  </div>
                  <div style={{ fontSize: "0.64rem", color: "var(--ink-soft)", ...s.mono }}>
                    {y.year}
                    {birthYear ? ` · ${y.year - birthYear + 1}` : ""}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
