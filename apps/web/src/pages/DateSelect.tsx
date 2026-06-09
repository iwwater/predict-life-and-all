// 择日择吉页: 基于老黄历 API 的交互式吉日选择器
// 支持选择用途 (婚嫁/开业/出行/搬家/动土), 筛选吉日, 查看每日宜忌详情
import { useEffect, useState, useMemo, useCallback } from "react";
import { fetchAlmanacMonth, type AlmanacMonthPayload, type AlmanacMonthDay } from "../lib/api";
import { COLOR, SkeletonBlock } from "../components/ui";
import { Reveal } from "../components/Interactions";
import { BaGuaRing, CompassRing, AuspiciousClouds, WUXING_COLORS } from "../components/MysticElements";

const MONTHS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
const WEEKDAYS = ["日","一","二","三","四","五","六"];

interface Purpose {
  key: string; label: string; icon: string;
  yiKeywords: string[]; // 匹配"宜"字段关键词
  desc: string;
}

const PURPOSES: Purpose[] = [
  { key: "marriage", label: "婚嫁", icon: "💒", yiKeywords: ["嫁娶","纳采","订婚","结婚","会亲友"], desc: "嫁娶、纳采、订婚宴" },
  { key: "opening", label: "开业", icon: "🏪", yiKeywords: ["开市","开业","开张","交易","立券","签约"], desc: "开业、开市、签合同" },
  { key: "travel", label: "出行", icon: "✈️", yiKeywords: ["出行","远行","旅游","赴任"], desc: "远行、旅游、赴任" },
  { key: "moving", label: "搬家", icon: "🏠", yiKeywords: ["搬家","移徙","入宅","乔迁","安床"], desc: "搬家、入宅、安床" },
  { key: "construction", label: "动土", icon: "🏗️", yiKeywords: ["动土","开工","修造","装修","破土"], desc: "动土、开工、修造" },
  { key: "general", label: "通用吉日", icon: "✨", yiKeywords: [], desc: "综合宜忌筛选吉日" },
];

// 吉神: 正面加分; 凶神: 减分
const AUSPICIOUS_STARS: Record<string, number> = {
  "天德": 3, "月德": 3, "天赦": 3, "天恩": 2, "月恩": 2, "天德合": 2, "月德合": 2,
  "母仓": 1, "阳德": 1, "阴德": 1, "三合": 1, "六合": 1, "五合": 1,
};
const INAUSPICIOUS_STARS: Record<string, number> = {
  "月破": -3, "大耗": -3, "劫煞": -2, "灾煞": -2, "月煞": -2,
  "天火": -2, "天贼": -2, "五虚": -1, "八风": -1, "九空": -1, "土符": -1,
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
    setLoading(true);
    setError(null);
    fetchAlmanacMonth(year, month)
      .then(setMonthData)
      .catch((e) => setError(String(e?.message || e)))
      .finally(() => setLoading(false));
  }, [year, month]);

  const goPrev = () => {
    if (month === 1) { setYear((y) => y - 1); setMonth(12); }
    else setMonth((m) => m - 1);
  };
  const goNext = () => {
    if (month === 12) { setYear((y) => y + 1); setMonth(1); }
    else setMonth((m) => m + 1);
  };
  const goToday = () => {
    setYear(now.getFullYear()); setMonth(now.getMonth() + 1);
  };

  // 为每天计算适配分数
  const scoredDays = useMemo(() => {
    if (!monthData?.days) return [];
    return monthData.days.map((day) => {
      let score = 0;
      const reasons: string[] = [];

      // 黄道 +1.5, 黑道 -1
      if (day.is_huangdao !== undefined) {
        const isHuangDao = day.is_huangdao;
        score += isHuangDao ? 1.5 : -1;
        if (isHuangDao) reasons.push(`${day.zhi_xing || ""}·黄道`);
      }

      // 吉神加分
      if (Array.isArray(day.ji_shen)) {
        for (const star of day.ji_shen) {
          const add = AUSPICIOUS_STARS[star] || 0.3;
          if (add > 0) { score += add; reasons.push(star); }
        }
      }

      // 凶神减分
      if (Array.isArray(day.xiong_sha)) {
        for (const star of day.xiong_sha) {
          const sub = INAUSPICIOUS_STARS[star] || -0.3;
          if (sub < 0) score += sub;
        }
      }

      // 冲生肖减分
      if (day.chong_shengxiao) score -= 1;

      // 宜忌匹配: 对特定用途 +2/-2
      const yiList = Array.isArray(day.yi) ? day.yi : [];
      const jiList = Array.isArray(day.ji) ? day.ji : [];
      if (purposeInfo.yiKeywords.length > 0) {
        const yiMatch = purposeInfo.yiKeywords.filter((kw) => yiList.some((y: string) => y.includes(kw))).length;
        const jiMatch = purposeInfo.yiKeywords.filter((kw) => jiList.some((j: string) => j.includes(kw))).length;
        score += yiMatch * 2;
        score -= jiMatch * 3;
        if (yiMatch > 0) reasons.push(`宜${purposeInfo.label}`);
      }

      // 星期: 周末小幅加分
      const date = new Date(monthData.year, monthData.month - 1, day.solar_day);
      const dow = date.getDay();
      if (dow === 0 || dow === 6) score += 0.5;

      return { ...day, _score: Math.round(score * 10) / 10, _reasons: reasons.slice(0, 4) };
    }).sort((a, b) => b._score - a._score);
  }, [monthData, purpose]);

  // Top 吉日
  const topDays = scoredDays.filter((d) => d._score >= 2).slice(0, 8);
  // 本月全部吉日
  const allGoodDays = scoredDays.filter((d) => d._score > 0);

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDow = new Date(year, month - 1, 1).getDay();

  const dayMap = useMemo(() => {
    if (!monthData?.days) return new Map<string, typeof scoredDays[0]>();
    const m = new Map<string, typeof scoredDays[0]>();
    for (const d of scoredDays) {
      m.set(String(d.solar_day), d);
    }
    return m;
  }, [scoredDays]);

  return (
    <div className="space-y-6">
      {/* 背景玄学装饰 */}
      <div className="fixed right-0 bottom-0 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <BaGuaRing size={300} spinning />
      </div>
      <div className="fixed left-0 top-1/4 pointer-events-none opacity-[0.03] z-0" aria-hidden>
        <CompassRing size={250} />
      </div>

      {/* 头部 */}
      <Reveal>
        <header className="relative">
          <div className="absolute right-4 top-0 opacity-[0.12] pointer-events-none" aria-hidden>
            <AuspiciousClouds />
          </div>
          <h1 className="text-2xl font-display" style={{ color: COLOR.goldBright }}>择日择吉</h1>
          <p className="text-sm mt-1" style={{ color: COLOR.muted }}>
            基于建除十二神 · 二十八星宿 · 吉神凶煞 · 宜忌冲煞 · 综合评分
          </p>
        </header>
      </Reveal>

      {/* 用途选择 */}
      <section className="card card-highlight">
        <h3 className="text-sm mb-3" style={{ color: COLOR.gold }}>请选择用途</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {PURPOSES.map((p) => {
            const on = purpose === p.key;
            return (
              <button
                key={p.key}
                type="button"
                onClick={() => setPurpose(p.key)}
                className="p-3 rounded-lg border text-left tap lift-on-hover transition-all"
                style={{
                  borderColor: on ? COLOR.gold : COLOR.line,
                  background: on ? "rgba(201,162,75,0.10)" : "rgba(255,255,255,0.02)",
                  boxShadow: on ? "0 0 0 1px var(--gold)" : "none",
                }}
              >
                <div className="text-xl mb-1">{p.icon}</div>
                <div className="text-sm font-semibold" style={{ color: on ? COLOR.goldBright : COLOR.ink }}>
                  {p.label}
                </div>
                <div className="text-[10px] mt-0.5" style={{ color: COLOR.muted }}>{p.desc}</div>
              </button>
            );
          })}
        </div>
      </section>

      {/* 月份导航 + 日历 */}
      <section className="card card-highlight">
        <div className="flex items-center justify-between mb-4">
          <button type="button" className="btn-ghost text-sm tap" onClick={goPrev}>← 上月</button>
          <div className="flex items-center gap-3">
            <button type="button" className="text-xs tap" style={{ color: COLOR.azure }} onClick={goToday}>
              回到本月
            </button>
            <h2 className="text-lg font-display" style={{ color: COLOR.goldBright }}>{year}年 {MONTHS[month - 1]}</h2>
          </div>
          <button type="button" className="btn-ghost text-sm tap" onClick={goNext}>下月 →</button>
        </div>

        {loading ? (
          <SkeletonBlock height={320} />
        ) : error ? (
          <div className="p-4 text-sm" style={{ color: COLOR.danger }}>{error}</div>
        ) : (
          <>
            {/* 星期头 */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {WEEKDAYS.map((w) => (
                <div key={w} className="text-center text-[10px] uppercase tracking-widest py-1" style={{ color: COLOR.muted }}>
                  {w}
                </div>
              ))}
            </div>

            {/* 日期格子 */}
            <div className="grid grid-cols-7 gap-1">
              {/* 填充空白 */}
              {Array.from({ length: firstDow }).map((_, i) => (
                <div key={`pad-${i}`} className="aspect-square" />
              ))}
              {/* 日期 */}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const dayNum = i + 1;
                const dayInfo = dayMap.get(String(dayNum));
                const score = dayInfo?._score ?? 0;
                const isToday = year === now.getFullYear() && month === now.getMonth() + 1 && dayNum === now.getDate();
                const isTop = score >= 3;
                const isGood = score > 0 && score < 3;
                const isAvg = score === 0;
                const isBad = score < 0;

                return (
                  <button
                    key={dayNum}
                    type="button"
                    className="aspect-square rounded-lg flex flex-col items-center justify-center text-xs tap transition-all relative"
                    style={{
                      background: isTop ? "rgba(201,162,75,0.18)" :
                                  isGood ? "rgba(79,179,160,0.08)" :
                                  isBad ? "rgba(200,85,61,0.06)" :
                                  "rgba(255,255,255,0.02)",
                      border: isToday ? `2px solid ${COLOR.gold}` :
                               isTop ? `1px solid ${COLOR.goldDim}` :
                               "1px solid var(--line-soft)",
                      color: isTop ? COLOR.goldBright :
                              isGood ? COLOR.jade :
                              isBad ? COLOR.muted :
                              COLOR.inkSoft,
                    }}
                    title={dayInfo?._reasons?.join(", ") || ""}
                  >
                    <span className="text-sm font-semibold">{dayNum}</span>
                    {dayInfo?.zhi_xing && (
                      <span className="text-[8px] mt-0.5" style={{
                        color: dayInfo.is_huangdao ? COLOR.jade : COLOR.danger,
                        opacity: 0.8,
                      }}>
                        {dayInfo.zhi_xing}
                      </span>
                    )}
                    {isTop && (
                      <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full"
                        style={{ background: COLOR.goldBright, boxShadow: `0 0 4px ${COLOR.gold}` }} />
                    )}
                  </button>
                );
              })}
            </div>

            {/* 图例 */}
            <div className="flex items-center gap-4 mt-3 text-[10px]">
              <LegendItem color={COLOR.goldBright} label="大吉日 (≥3分)" />
              <LegendItem color={COLOR.jade} label="宜用日 (>0分)" />
              <LegendItem color={COLOR.muted} label="平日 (0分)" />
              <LegendItem color={COLOR.danger} label="慎用日 (<0分)" />
            </div>
          </>
        )}
      </section>

      {/* Top 推荐吉日 */}
      {topDays.length > 0 && (
        <section className="card card-highlight">
          <h3 className="text-sm mb-3" style={{ color: COLOR.goldBright }}>
            {purposeInfo.icon} 本月推荐 {purposeInfo.label} 吉日 · Top {topDays.length}
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {topDays.map((d, idx) => {
              const date = new Date(monthData!.year, monthData!.month - 1, d.solar_day);
              const monthDay = `${date.getMonth() + 1}/${date.getDate()}`;
              return (
                <div key={d.solar_day} className="p-3 rounded-lg border" style={{
                  borderColor: idx === 0 ? COLOR.gold : COLOR.line,
                  background: idx === 0 ? "rgba(201,162,75,0.08)" : "rgba(255,255,255,0.02)",
                }}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-semibold" style={{ color: COLOR.ink }}>{monthDay}</span>
                    <span className="text-xl">{WEEKDAYS[date.getDay()]}</span>
                  </div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-xs" style={{ color: COLOR.goldBright }}>★ {d._score}分</span>
                    {d.zhi_xing && (
                      <span className="text-[10px] px-1 rounded" style={{
                        background: d.is_huangdao ? "rgba(79,179,160,0.15)" : "rgba(200,85,61,0.10)",
                        color: d.is_huangdao ? COLOR.jade : COLOR.danger,
                      }}>{d.zhi_xing}</span>
                    )}
                  </div>
                  {d._reasons && d._reasons.length > 0 && (
                    <div className="text-[10px] leading-snug" style={{ color: COLOR.muted }}>
                      {d._reasons.slice(0, 3).join(" · ")}
                    </div>
                  )}
                  {Array.isArray(d.yi) && d.yi.length > 0 && (
                    <div className="text-[10px] mt-1.5 leading-snug" style={{ color: COLOR.jade }}>
                      <span className="opacity-60">宜:</span> {d.yi.slice(0, 4).join("、")}
                    </div>
                  )}
                  {Array.isArray(d.ji) && d.ji.length > 0 && (
                    <div className="text-[10px] mt-0.5 leading-snug" style={{ color: COLOR.danger }}>
                      <span className="opacity-60">忌:</span> {d.ji.slice(0, 3).join("、")}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 本月统计 */}
      {allGoodDays.length > 0 && (
        <section className="card card-highlight text-xs" style={{ color: COLOR.muted }}>
          <div className="flex items-center gap-4 flex-wrap">
            <span style={{ color: COLOR.goldBright }}>{purposeInfo.icon} {purposeInfo.label}统计:</span>
            <span>本月共 <strong style={{ color: COLOR.goldBright }}>{allGoodDays.length}</strong> 个宜用日</span>
            <span>其中大吉日 <strong style={{ color: COLOR.gold }}>{topDays.length}</strong> 个</span>
            <span>总天数 <strong style={{ color: COLOR.inkSoft }}>{daysInMonth}</strong></span>
          </div>
        </section>
      )}

      {/* 免责 */}
      <section className="text-[10px] leading-relaxed" style={{ color: COLOR.muted, opacity: 0.6 }}>
        以上吉日评分依据建除十二神、黄道黑道、吉神凶煞综合计算，仅为传统文化参考。重大日期选择请结合实际情况并咨询专业人士。
      </section>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full" style={{ background: color }} />
      <span>{label}</span>
    </div>
  );
}
