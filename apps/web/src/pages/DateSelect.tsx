// 择日择吉页: 基于老黄历 API 的交互式吉日选择器（「古籍×仪器」纸墨风格）
import { useEffect, useState, useMemo } from "react";
import { fetchAlmanacMonth, type AlmanacMonthPayload } from "../lib/api";
import { SkeletonBlock } from "../components/ui";

const MONTHS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
const WEEKDAYS = ["日","一","二","三","四","五","六"];

interface Purpose {
  key: string; label: string; yiKeywords: string[]; desc: string;
}

const PURPOSES: Purpose[] = [
  { key:"marriage", label:"婚嫁", yiKeywords:["嫁娶","纳采","订婚","结婚","会亲友"], desc:"嫁娶、纳采、订婚宴" },
  { key:"opening", label:"开业", yiKeywords:["开市","开业","开张","交易","立券","签约"], desc:"开业、开市、签合同" },
  { key:"travel", label:"出行", yiKeywords:["出行","远行","旅游","赴任"], desc:"远行、旅游、赴任" },
  { key:"moving", label:"搬家", yiKeywords:["搬家","移徙","入宅","乔迁","安床"], desc:"搬家、入宅、安床" },
  { key:"construction", label:"动土", yiKeywords:["动土","开工","修造","装修","破土"], desc:"动土、开工、修造" },
  { key:"general", label:"通用吉日", yiKeywords:[], desc:"综合宜忌筛选吉日" },
];

const AUSPICIOUS_STARS: Record<string, number> = {
  "天德":3, "月德":3, "天赦":3, "天恩":2, "月恩":2, "天德合":2, "月德合":2,
  "母仓":1, "阳德":1, "阴德":1, "三合":1, "六合":1, "五合":1,
};
const INAUSPICIOUS_STARS: Record<string, number> = {
  "月破":-3, "大耗":-3, "劫煞":-2, "灾煞":-2, "月煞":-2,
  "天火":-2, "天贼":-2, "五虚":-1, "八风":-1, "九空":-1, "土符":-1,
};

export function DateSelect() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [purpose, setPurpose] = useState("general");
  const [monthData, setMonthData] = useState<AlmanacMonthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const purposeInfo = PURPOSES.find((p) => p.key === purpose) || PURPOSES[0];

  useEffect(() => {
    setLoading(true); setError(null);
    fetchAlmanacMonth(year, month).then(setMonthData).catch((e) => setError(String(e?.message || e))).finally(() => setLoading(false));
  }, [year, month]);

  const goPrev = () => { if (month === 1) { setYear((y) => y - 1); setMonth(12); } else setMonth((m) => m - 1); };
  const goNext = () => { if (month === 12) { setYear((y) => y + 1); setMonth(1); } else setMonth((m) => m + 1); };
  const goToday = () => { setYear(now.getFullYear()); setMonth(now.getMonth() + 1); };

  const scoredDays = useMemo(() => {
    if (!monthData?.days) return [];
    return monthData.days.map((day) => {
      let score = 0; const reasons: string[] = [];
      if (day.is_huangdao !== undefined) { const hd = day.is_huangdao; score += hd ? 1.5 : -1; if (hd) reasons.push(`${day.zhi_xing || ""}·黄道`); }
      if (Array.isArray(day.ji_shen)) { for (const star of day.ji_shen) { const add = AUSPICIOUS_STARS[star] || 0.3; if (add > 0) { score += add; reasons.push(star); } } }
      if (Array.isArray(day.xiong_sha)) { for (const star of day.xiong_sha) { score += INAUSPICIOUS_STARS[star] || -0.3; } }
      if (day.chong_shengxiao) score -= 1;
      const yiList = Array.isArray(day.yi) ? day.yi : [];
      const jiList = Array.isArray(day.ji) ? day.ji : [];
      if (purposeInfo.yiKeywords.length > 0) {
        const yiMatch = purposeInfo.yiKeywords.filter((kw) => yiList.some((y: string) => y.includes(kw))).length;
        const jiMatch = purposeInfo.yiKeywords.filter((kw) => jiList.some((j: string) => j.includes(kw))).length;
        score += yiMatch * 2; score -= jiMatch * 3;
        if (yiMatch > 0) reasons.push(`宜${purposeInfo.label}`);
      }
      const date = new Date(monthData.year, monthData.month - 1, day.solar_day);
      if (date.getDay() === 0 || date.getDay() === 6) score += 0.5;
      return { ...day, _score: Math.round(score * 10) / 10, _reasons: reasons.slice(0, 4) };
    }).sort((a, b) => b._score - a._score);
  }, [monthData, purpose]);

  const topDays = scoredDays.filter((d) => d._score >= 2).slice(0, 8);
  const allGoodDays = scoredDays.filter((d) => d._score > 0);
  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDow = new Date(year, month - 1, 1).getDay();

  const dayMap = useMemo(() => {
    const m = new Map<string, typeof scoredDays[0]>();
    for (const d of scoredDays) m.set(String(d.solar_day), d);
    return m;
  }, [scoredDays]);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />择日择吉</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>
          基于建除十二神 · 二十八星宿 · 吉神凶煞 · 宜忌冲煞 · 综合评分
        </p>
      </header>

      {/* 用途选择 */}
      <section className="paper-frame">
        <div className="paper-eyebrow">请选择用途</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2" style={{ marginTop: "0.5rem" }}>
          {PURPOSES.map((p) => {
            const on = purpose === p.key;
            return (
              <button key={p.key} type="button" onClick={() => setPurpose(p.key)}
                className="paper-grid-cell text-left" style={{
                  padding: "0.6rem 0.75rem", cursor: "pointer",
                  borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                  background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: on ? "var(--cinnabar)" : "var(--ink)", fontFamily: "'Noto Serif SC', serif", marginBottom: "0.15rem" }}>{p.label}</div>
                <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{p.desc}</div>
              </button>
            );
          })}
        </div>
      </section>

      {/* 月份导航 + 日历 */}
      <section className="paper-frame">
        <div className="flex items-center justify-between mb-4">
          <button type="button" className="paper-btn-ghost" style={{ fontSize: "0.78rem" }} onClick={goPrev}>← 上月</button>
          <div className="flex items-center gap-3">
            <button type="button" className="paper-link" style={{ fontSize: "0.7rem" }} onClick={goToday}>回到本月</button>
            <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 700, fontSize: "1.1rem", color: "var(--ink)" }}>{year}年 {MONTHS[month - 1]}</span>
          </div>
          <button type="button" className="paper-btn-ghost" style={{ fontSize: "0.78rem" }} onClick={goNext}>下月 →</button>
        </div>

        {loading ? <SkeletonBlock height={320} /> : error ? (
          <div className="paper-error">{error}</div>
        ) : (
          <>
            <div className="grid grid-cols-7 gap-1 mb-2">
              {WEEKDAYS.map((w) => (
                <div key={w} className="text-center py-1" style={{ fontSize: "0.62rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>{w}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: firstDow }).map((_, i) => (<div key={`pad-${i}`} className="aspect-square" />))}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const dayNum = i + 1;
                const dayInfo = dayMap.get(String(dayNum));
                const score = dayInfo?._score ?? 0;
                const isToday = year === now.getFullYear() && month === now.getMonth() + 1 && dayNum === now.getDate();
                const isTop = score >= 3; const isGood = score > 0 && score < 3; const isBad = score < 0;
                return (
                  <button key={dayNum} type="button"
                    className="aspect-square flex flex-col items-center justify-center text-xs transition-colors"
                    style={{
                      borderRadius: "4px",
                      background: isTop ? "rgba(176,58,46,0.1)" : isGood ? "rgba(90,112,88,0.06)" : isBad ? "rgba(176,58,46,0.04)" : "transparent",
                      border: isToday ? "2px solid var(--cinnabar)" : isTop ? "1px solid rgba(176,58,46,0.3)" : "1px solid var(--rule)",
                      color: isTop ? "var(--cinnabar)" : isGood ? "var(--verdigris)" : isBad ? "var(--ink-soft)" : "var(--ink)",
                    }}
                    title={dayInfo?._reasons?.join(", ") || ""}>
                    <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{dayNum}</span>
                    {dayInfo?.zhi_xing && (
                      <span style={{ fontSize: "0.52rem", color: dayInfo.is_huangdao ? "var(--verdigris)" : "var(--cinnabar)", opacity: 0.8 }}>
                        {dayInfo.zhi_xing}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            <div className="paper-hr" style={{ marginTop: "0.6rem" }} />
            <div className="flex items-center gap-4" style={{ fontSize: "0.65rem" }}>
              <LegendDot color="var(--cinnabar)" label="大吉日 (≥3分)" />
              <LegendDot color="var(--verdigris)" label="宜用日 (>0分)" />
              <LegendDot color="var(--ink-soft)" label="平日 (0分)" />
              <LegendDot color="var(--cinnabar)" label="慎用日 (<0分)" style={{ opacity: 0.5 }} />
            </div>
          </>
        )}
      </section>

      {/* Top 吉日 */}
      {topDays.length > 0 && (
        <section className="paper-frame">
          <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>本月推荐 {purposeInfo.label} 吉日 · Top {topDays.length}</div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3" style={{ marginTop: "0.5rem" }}>
            {topDays.map((d, idx) => {
              const date = new Date(monthData!.year, monthData!.month - 1, d.solar_day);
              const mLabel = `${date.getMonth() + 1}/${date.getDate()}`;
              return (
                <div key={d.solar_day} className="paper-grid-cell" style={{
                  padding: "0.6rem 0.75rem",
                  borderColor: idx === 0 ? "var(--cinnabar)" : "var(--rule)",
                  background: idx === 0 ? "rgba(176,58,46,0.04)" : "var(--paper)",
                }}>
                  <div className="flex items-center justify-between" style={{ marginBottom: "0.25rem" }}>
                    <span style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>{mLabel}</span>
                    <span style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>{WEEKDAYS[date.getDay()]}</span>
                  </div>
                  <div className="flex items-center gap-1.5" style={{ marginBottom: "0.15rem" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--cinnabar)", fontWeight: 600 }}>★ {d._score}分</span>
                    {d.zhi_xing && (
                      <span className="paper-tag" style={{
                        fontSize: "0.58rem",
                        color: d.is_huangdao ? "var(--verdigris)" : "var(--cinnabar)",
                        borderColor: d.is_huangdao ? "rgba(90,112,88,0.3)" : "rgba(176,58,46,0.3)",
                      }}>{d.zhi_xing}</span>
                    )}
                  </div>
                  {d._reasons && <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{d._reasons.slice(0, 3).join(" · ")}</div>}
                  {Array.isArray(d.yi) && d.yi.length > 0 && (
                    <div style={{ fontSize: "0.65rem", color: "var(--verdigris)", marginTop: "0.25rem" }}>
                      <span style={{ opacity: 0.6 }}>宜:</span> {d.yi.slice(0, 4).join("、")}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 统计 */}
      {allGoodDays.length > 0 && (
        <section className="paper-grid-cell" style={{ padding: "0.6rem 1rem", fontSize: "0.75rem", color: "var(--ink-soft)" }}>
          <div className="flex items-center gap-4 flex-wrap">
            <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>{purposeInfo.label}统计:</span>
            <span>本月 <strong style={{ color: "var(--ink)" }}>{allGoodDays.length}</strong> 个宜用日</span>
            <span>大吉日 <strong style={{ color: "var(--cinnabar)" }}>{topDays.length}</strong> 个</span>
            <span>总天数 <strong style={{ color: "var(--ink-soft)" }}>{daysInMonth}</strong></span>
          </div>
        </section>
      )}

      <section style={{ fontSize: "0.65rem", color: "var(--ink-soft)", opacity: 0.6, lineHeight: 1.7 }}>
        以上吉日评分依据建除十二神、黄道黑道、吉神凶煞综合计算，仅为传统文化参考。重大日期选择请结合实际情况并咨询专业人士。
      </section>
    </div>
  );
}

function LegendDot({ color, label, style }: { color: string; label: string; style?: React.CSSProperties }) {
  return (
    <div className="flex items-center gap-1.5" style={style}>
      <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: color, display: "inline-block" }} />
      <span>{label}</span>
    </div>
  );
}
