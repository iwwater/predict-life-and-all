// /almanac — 老黄历: 交互式月历 + 每日宜忌冲煞吉神星宿（「古籍×仪器」纸墨风格）
import { useEffect, useState, useMemo, useCallback } from "react";
import {
  fetchAlmanac, fetchAlmanacMonth,
  type AlmanacPayload, type AlmanacMonthPayload, type AlmanacMonthDay,
} from "../lib/api";
import { EmptyBox, SkeletonBlock } from "../components/ui";

// ── 农历日序 ─────────────────────────────────────────────────────────
const LUNAR_DAY_NAMES = ["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
  "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
  "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"];
const MONTH_NAMES = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"];
const WEEKDAYS = ["日","一","二","三","四","五","六"];

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}
function getFirstDayOfWeek(year: number, month: number): number {
  return new Date(year, month - 1, 1).getDay();
}

// ── 主组件 ───────────────────────────────────────────────────────────
export function Almanac() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState(now.getDate());
  const [monthData, setMonthData] = useState<AlmanacMonthPayload | null>(null);
  const [dayData, setDayData] = useState<AlmanacPayload | null>(null);
  const [loadingMonth, setLoadingMonth] = useState(false);
  const [loadingDay, setLoadingDay] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setLoadingMonth(true); setErr(null);
    fetchAlmanacMonth(year, month).then(setMonthData).catch((e) => setErr(String(e?.message || e))).finally(() => setLoadingMonth(false));
  }, [year, month]);

  useEffect(() => {
    setLoadingDay(true);
    const dateStr = `${year}-${String(month).padStart(2,"0")}-${String(selectedDay).padStart(2,"0")}`;
    fetchAlmanac(dateStr).then(setDayData).catch((e) => setErr(String(e?.message || e))).finally(() => setLoadingDay(false));
  }, [year, month, selectedDay]);

  const goPrevMonth = useCallback(() => {
    if (month === 1) { setYear((y) => y - 1); setMonth(12); } else setMonth((m) => m - 1);
    setSelectedDay(1);
  }, [month]);
  const goNextMonth = useCallback(() => {
    if (month === 12) { setYear((y) => y + 1); setMonth(1); } else setMonth((m) => m + 1);
    setSelectedDay(1);
  }, [month]);
  const goToday = useCallback(() => {
    const n = new Date(); setYear(n.getFullYear()); setMonth(n.getMonth() + 1); setSelectedDay(n.getDate());
  }, []);

  const calendarDays = useMemo(() => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDow = getFirstDayOfWeek(year, month);
    const cells: Array<{ solarDay: number; dayData?: AlmanacMonthDay }> = [];
    for (let i = 0; i < firstDow; i++) cells.push({ solarDay: 0 });
    for (let d = 1; d <= daysInMonth; d++) {
      const md = monthData?.days?.find((dd) => dd.solar_day === d);
      cells.push({ solarDay: d, dayData: md });
    }
    return cells;
  }, [year, month, monthData]);

  const isToday = (d: number) => d === now.getDate() && month === now.getMonth() + 1 && year === now.getFullYear();

  if (err && !monthData && !dayData) {
    return <EmptyBox>加载老黄历失败: {err}</EmptyBox>;
  }

  return (
    <div className="space-y-5">
      {/* 页眉 */}
      <header>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.65rem", color: "var(--cinnabar)", letterSpacing: "0.2em" }}>
          ALMANAC · 老黄历
        </div>
        <h1 className="paper-title" style={{ marginTop: "0.35rem" }}>
          <span className="stamp" />
          <span>{year}年{MONTH_NAMES[month - 1]}</span>
          <span className="sub">{dayData?.lunar?.date_str || ""}</span>
        </h1>
        <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "0.3rem", fontFamily: "'Noto Serif SC', serif" }}>
          {dayData?.lunar?.year_in_ganzhi}年 · {dayData?.lunar?.year_shengxiao}年
          {dayData?.jie_qi_note && <span style={{ marginLeft: "0.5rem", color: "var(--verdigris)" }}>· {dayData.jie_qi_note}</span>}
        </div>
      </header>

      {/* ── 交互式月历 ── */}
      <section className="paper-frame">
        {/* 月份导航 */}
        <div className="flex items-center justify-between mb-4">
          <button onClick={goPrevMonth} className="paper-btn-ghost" style={{ fontSize: "0.78rem" }}>← 上月</button>
          <div className="flex items-center gap-3">
            <span style={{ fontFamily: "'Noto Serif SC', serif", fontWeight: 700, fontSize: "1.1rem", color: "var(--ink)" }}>
              {year}年{MONTH_NAMES[month - 1]}
            </span>
            <button onClick={goToday} className="paper-link" style={{ fontSize: "0.7rem" }}>回今天</button>
          </div>
          <button onClick={goNextMonth} className="paper-btn-ghost" style={{ fontSize: "0.78rem" }}>下月 →</button>
        </div>

        {/* 星期头 */}
        <div className="grid grid-cols-7 mb-1">
          {WEEKDAYS.map((wd, i) => (
            <div key={wd} className="text-center text-[10px] font-semibold py-1.5"
              style={{ color: i === 0 || i === 6 ? "var(--cinnabar)" : "var(--ink-soft)" }}>
              {wd}
            </div>
          ))}
        </div>

        {/* 日期网格 */}
        {loadingMonth ? (
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: 35 }).map((_, i) => (<SkeletonBlock key={i} height={64} />))}
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((cell, idx) => {
              if (cell.solarDay === 0) return <div key={`empty-${idx}`} className="aspect-square" />;
              const d = cell.dayData;
              const active = cell.solarDay === selectedDay;
              const today = isToday(cell.solarDay);
              const isHuangdao = d?.is_huangdao;
              const isHeidao = d && !d.is_huangdao && !!d.zhi_xing;

              return (
                <button key={cell.solarDay} onClick={() => setSelectedDay(cell.solarDay)}
                  className="aspect-square flex flex-col items-center justify-center transition-colors"
                  style={{
                    background: active ? "rgba(176,58,46,0.08)" : today ? "rgba(90,112,88,0.06)" : "transparent",
                    border: active ? "1px solid var(--cinnabar)" : today ? "1px solid var(--verdigris)" : "1px solid transparent",
                    borderRadius: "4px",
                  }}>
                  <span style={{
                    fontSize: "0.8rem", fontWeight: 600,
                    color: active ? "var(--cinnabar)" : today ? "var(--verdigris)" : "var(--ink)",
                  }}>{cell.solarDay}</span>
                  <span style={{ fontSize: "0.6rem", color: "var(--ink-soft)", lineHeight: 1.1 }}>
                    {d?.lunar_day === 1 ? `${d.lunar_month}月` : (d?.lunar_day ? LUNAR_DAY_NAMES[d.lunar_day - 1] : "") || d?.lunar_day}
                  </span>
                  {d?.day_ganzhi && (
                    <span style={{ fontSize: "0.55rem", color: "var(--ink-soft)", opacity: 0.7 }}>{d.day_ganzhi}</span>
                  )}
                  {d?.zhi_xing && (
                    <span style={{
                      fontSize: "0.55rem", padding: "0 2px", borderRadius: "2px",
                      color: isHuangdao ? "var(--verdigris)" : "var(--cinnabar)",
                      background: isHuangdao ? "rgba(90,112,88,0.1)" : "rgba(176,58,46,0.06)",
                    }}>{d.zhi_xing}</span>
                  )}
                  {d?.chong_shengxiao && (
                    <span style={{ fontSize: "0.52rem", color: "var(--cinnabar)", opacity: 0.7 }}>冲{d.chong_shengxiao}</span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* 图例 */}
        <div className="flex items-center gap-4 mt-3 pt-3 text-[10px]" style={{ borderTop: "1px solid var(--rule)" }}>
          <span className="flex items-center gap-1" style={{ color: "var(--verdigris)" }}>
            <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "2px", background: "rgba(90,112,88,0.2)" }} /> 黄道吉日
          </span>
          <span className="flex items-center gap-1" style={{ color: "var(--cinnabar)" }}>
            <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "2px", background: "rgba(176,58,46,0.12)" }} /> 黑道
          </span>
          <span style={{ color: "var(--ink-soft)" }}>点击日期查看详情</span>
        </div>
      </section>

      {/* ── 选中日详情 ── */}
      {loadingDay ? (
        <div className="space-y-3">
          <SkeletonBlock height={100} />
          <SkeletonBlock height={80} />
          <SkeletonBlock height={120} />
        </div>
      ) : dayData ? (
        <AlmanacDetail data={dayData} />
      ) : null}
    </div>
  );
}

// ── 黄历详情卡片组 ────────────────────────────────────────────────────
function AlmanacDetail({ data }: { data: AlmanacPayload }) {
  const d = data;
  const isHuangdao = d.jian_chu?.is_huangdao || d.tian_shen?.type === "黄道";

  return (
    <div className="space-y-4">
      {/* 今日概览 */}
      <section className="paper-frame" style={{ borderColor: isHuangdao ? "rgba(90,112,88,0.3)" : "var(--rule)" }}>
        <div className="flex items-start gap-5 flex-wrap">
          <div className="flex flex-col items-center">
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.6rem", color: "var(--ink-soft)", letterSpacing: "0.1em" }}>日柱</div>
            <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "2.4rem", fontWeight: 700, color: isHuangdao ? "var(--verdigris)" : "var(--cinnabar)", lineHeight: 1.2 }}>
              {d.ganzhi.day.full}
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>{d.lunar.year_shengxiao}年 · {d.ganzhi.day.animal}</div>
          </div>

          <div className="flex flex-col gap-1.5">
            <BadgeRow label="日干五行" value={d.wuxing.day_gan} color={d.wuxing.day_gan_color} />
            <BadgeRow label="日支五行" value={d.wuxing.day_zhi} color="var(--ink-soft)" />
            <BadgeRow label="纳音" value={d.na_yin.day} color="var(--cinnabar)" />
          </div>

          <div className="flex flex-col items-center gap-1">
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.6rem", color: "var(--ink-soft)", letterSpacing: "0.1em" }}>建除</div>
            <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.5rem", fontWeight: 700, color: isHuangdao ? "var(--verdigris)" : "var(--cinnabar)" }}>
              {d.jian_chu.name}
            </div>
            <span className="paper-tag" style={{ fontSize: "0.6rem", color: isHuangdao ? "var(--verdigris)" : "var(--cinnabar)", borderColor: isHuangdao ? "rgba(90,112,88,0.4)" : "rgba(176,58,46,0.4)" }}>
              {d.tian_shen.type || d.jian_chu.type}
              {d.tian_shen.luck ? ` · ${d.tian_shen.luck}` : ""}
            </span>
          </div>

          <div className="flex flex-col gap-1 ml-auto text-right">
            <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
              月柱: <span style={{ color: "var(--ink)" }}>{d.ganzhi.month.full}</span>
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
              年柱: <span style={{ color: "var(--ink)" }}>{d.ganzhi.year.full}</span> ({d.lunar.year_shengxiao})
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
              年份纳音: <span style={{ color: "var(--cinnabar)" }}>{d.na_yin.year}</span>
            </div>
          </div>
        </div>
      </section>

      {/* 宜忌 + 吉神凶煞 — 双列 */}
      <div className="grid sm:grid-cols-2 gap-3">
        <section className="paper-frame">
          <div className="paper-eyebrow" style={{ color: "var(--verdigris)" }}>宜</div>
          {d.yi_ji.yi.length > 0 ? (
            <div className="flex flex-wrap gap-1.5" style={{ marginTop: "0.5rem" }}>
              {d.yi_ji.yi.map((item) => (
                <span key={item} className="paper-tag" style={{ color: "var(--verdigris)", borderColor: "rgba(90,112,88,0.35)", fontSize: "0.7rem" }}>{item}</span>
              ))}
            </div>
          ) : <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>今日无特别宜事</div>}
        </section>

        <section className="paper-frame">
          <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>忌</div>
          {d.yi_ji.ji.length > 0 ? (
            <div className="flex flex-wrap gap-1.5" style={{ marginTop: "0.5rem" }}>
              {d.yi_ji.ji.map((item) => (
                <span key={item} className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.35)", fontSize: "0.7rem" }}>{item}</span>
              ))}
            </div>
          ) : <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>今日无忌事</div>}
        </section>

        <section className="paper-frame">
          <div className="paper-eyebrow">吉神</div>
          {d.shen_sha.ji_shen.length > 0 ? (
            <div className="flex flex-wrap gap-1.5" style={{ marginTop: "0.5rem" }}>
              {d.shen_sha.ji_shen.map((s) => (
                <span key={s} className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)", fontSize: "0.7rem" }}>{s}</span>
              ))}
            </div>
          ) : <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>—</div>}
        </section>

        <section className="paper-frame">
          <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>凶煞</div>
          {d.shen_sha.xiong_sha.length > 0 ? (
            <div className="flex flex-wrap gap-1.5" style={{ marginTop: "0.5rem" }}>
              {d.shen_sha.xiong_sha.map((s) => (
                <span key={s} className="paper-tag" style={{ color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.25)", fontSize: "0.7rem" }}>{s}</span>
              ))}
            </div>
          ) : <div style={{ fontSize: "0.75rem", color: "var(--verdigris)" }}>今日无凶煞 · 较为清净</div>}
        </section>
      </div>

      {/* 冲煞 + 胎神 + 星宿 — 三列 */}
      <div className="grid sm:grid-cols-3 gap-3">
        <section className="paper-frame">
          <div className="paper-eyebrow">冲煞</div>
          <div className="space-y-1.5" style={{ marginTop: "0.3rem", fontSize: "0.82rem" }}>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--ink-soft)" }}>冲</span>
              <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>
                {d.chong_sha.chong}{d.chong_sha.chong_shengxiao && ` (${d.chong_sha.chong_shengxiao})`}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--ink-soft)" }}>煞</span>
              <span style={{ color: "var(--ink)" }}>{d.chong_sha.sha}方</span>
            </div>
          </div>
        </section>

        <section className="paper-frame">
          <div className="paper-eyebrow">胎神 & 方位</div>
          <div className="space-y-1.5" style={{ marginTop: "0.3rem", fontSize: "0.82rem" }}>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--ink-soft)" }}>胎神</span><span style={{ color: "var(--ink)" }}>{d.tai_shen || "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--ink-soft)" }}>阴贵</span><span style={{ color: "var(--ink)" }}>{d.yin_gui || "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--ink-soft)" }}>日太岁</span><span style={{ color: "var(--ink)" }}>{d.tai_sui.day || "—"}</span>
            </div>
          </div>
        </section>

        <section className="paper-frame">
          <div className="paper-eyebrow">二十八星宿</div>
          <div style={{ marginTop: "0.3rem" }}>
            <div className="flex items-center gap-2">
              <span style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.2rem", fontWeight: 700, color: "var(--ink)" }}>{d.xing_xiu.name}</span>
              <span className="paper-tag" style={{
                fontSize: "0.6rem",
                color: d.xing_xiu.luck === "吉" ? "var(--verdigris)" : d.xing_xiu.luck === "凶" ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: d.xing_xiu.luck === "吉" ? "rgba(90,112,88,0.4)" : d.xing_xiu.luck === "凶" ? "rgba(176,58,46,0.4)" : "var(--rule)",
              }}>{d.xing_xiu.luck}</span>
            </div>
            {d.xing_xiu.song && (
              <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", marginTop: "0.25rem", lineHeight: 1.5 }}>
                {d.xing_xiu.song.length > 80 ? d.xing_xiu.song.slice(0, 80) + "…" : d.xing_xiu.song}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* 彭祖百忌 */}
      <section className="paper-frame">
        <div className="paper-eyebrow">彭祖百忌</div>
        <div className="grid sm:grid-cols-2 gap-3" style={{ marginTop: "0.3rem", fontSize: "0.82rem" }}>
          <div className="flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
            <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>干忌</span>
            <span>{d.pengzu_baiji.gan || "—"}</span>
          </div>
          <div className="flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
            <span className="paper-tag" style={{ fontSize: "0.6rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.3)" }}>支忌</span>
            <span>{d.pengzu_baiji.zhi || "—"}</span>
          </div>
        </div>
      </section>

      {/* 节令 */}
      {(d.shu_jiu || d.jie_qi) && (
        <section className="paper-grid-cell" style={{ padding: "0.6rem 1rem", fontSize: "0.82rem" }}>
          <div className="flex items-center gap-2 flex-wrap">
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.6rem", color: "var(--cinnabar)", letterSpacing: "0.1em" }}>节令</span>
            {d.shu_jiu && <span className="paper-tag" style={{ color: "var(--indigo)", borderColor: "rgba(47,72,88,0.35)", fontSize: "0.7rem" }}>{d.shu_jiu}</span>}
            {d.jie && <span className="paper-tag" style={{ color: "var(--verdigris)", borderColor: "rgba(90,112,88,0.35)", fontSize: "0.7rem" }}>{d.jie}</span>}
          </div>
        </section>
      )}

      {/* 数据源说明 */}
      <details className="paper-grid-cell" style={{ padding: "0.6rem 1rem", fontSize: "0.72rem" }}>
        <summary style={{ cursor: "pointer", color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif", fontWeight: 600 }}>数据源与限制</summary>
        <div className="space-y-1" style={{ marginTop: "0.4rem", color: "var(--ink-soft)", lineHeight: 1.6 }}>
          <div>方法: {d.calculation_basis.method}</div>
          <div>规则版本: {d.calculation_basis.rule_version}</div>
          <div>数据源: {d.calculation_basis.input_source}</div>
          <div>限制: {d.calculation_basis.limits}</div>
        </div>
      </details>
    </div>
  );
}

function BadgeRow({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-2" style={{ fontSize: "0.75rem" }}>
      <span style={{ color: "var(--ink-soft)", minWidth: "56px" }}>{label}</span>
      <span className="paper-tag" style={{ fontSize: "0.7rem", color, borderColor: color + "44" }}>{value}</span>
    </div>
  );
}
