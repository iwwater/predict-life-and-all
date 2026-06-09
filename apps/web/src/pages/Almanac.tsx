// /almanac — 老黄历: 交互式月历 + 每日宜忌冲煞吉神星宿
import { useEffect, useState, useMemo, useCallback } from "react";
import {
  fetchAlmanac, fetchAlmanacMonth,
  type AlmanacPayload, type AlmanacMonthPayload, type AlmanacMonthDay,
} from "../lib/api";
import { COLOR, EmptyBox, SkeletonBlock } from "../components/ui";
import { Reveal } from "../components/Interactions";
import { BaGuaRing, AuspiciousClouds, PlanetSymbols } from "../components/MysticElements";

// ── 工具函数 ─────────────────────────────────────────────────────────
const MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];
const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

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

  // 加载整月数据
  useEffect(() => {
    setLoadingMonth(true);
    setErr(null);
    fetchAlmanacMonth(year, month)
      .then(setMonthData)
      .catch((e) => setErr(String(e?.message || e)))
      .finally(() => setLoadingMonth(false));
  }, [year, month]);

  // 加载选中日详情
  useEffect(() => {
    setLoadingDay(true);
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(selectedDay).padStart(2, "0")}`;
    fetchAlmanac(dateStr)
      .then(setDayData)
      .catch((e) => setErr(String(e?.message || e)))
      .finally(() => setLoadingDay(false));
  }, [year, month, selectedDay]);

  const goPrevMonth = useCallback(() => {
    if (month === 1) { setYear((y) => y - 1); setMonth(12); }
    else setMonth((m) => m - 1);
    setSelectedDay(1);
  }, [month]);

  const goNextMonth = useCallback(() => {
    if (month === 12) { setYear((y) => y + 1); setMonth(1); }
    else setMonth((m) => m + 1);
    setSelectedDay(1);
  }, [month]);

  const goToday = useCallback(() => {
    const n = new Date();
    setYear(n.getFullYear());
    setMonth(n.getMonth() + 1);
    setSelectedDay(n.getDate());
  }, []);

  // 构建日历网格
  const calendarDays = useMemo(() => {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDow = getFirstDayOfWeek(year, month);
    const cells: Array<{ solarDay: number; dayData?: AlmanacMonthDay }> = [];

    // 填充前置空白
    for (let i = 0; i < firstDow; i++) cells.push({ solarDay: 0 });

    for (let d = 1; d <= daysInMonth; d++) {
      const md = monthData?.days?.find((dd) => dd.solar_day === d);
      cells.push({ solarDay: d, dayData: md });
    }
    return cells;
  }, [year, month, monthData]);

  const isToday = (d: number) =>
    d === now.getDate() && month === now.getMonth() + 1 && year === now.getFullYear();

  if (err && !monthData && !dayData) {
    return <EmptyBox>加载老黄历失败: {err}</EmptyBox>;
  }

  return (
    <div className="space-y-6">
      {/* 八卦环 + 祥云背景 */}
      <div className="fixed right-0 bottom-0 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <BaGuaRing size={280} spinning />
      </div>
      <div className="fixed right-8 top-8 pointer-events-none opacity-[0.08] z-0" aria-hidden>
        <AuspiciousClouds />
      </div>

      {/* 页眉 */}
      <Reveal>
        <header className="relative">
          <div className="absolute right-0 top-0 opacity-30">
            <PlanetSymbols size={13} />
          </div>
          <div className="text-[10px] uppercase tracking-[0.4em]" style={{ color: COLOR.gold }}>
            Chinese Almanac · 老黄历
          </div>
          <h1 className="text-2xl mt-2 font-display" style={{ color: COLOR.ink }}>
            {year}年{MONTH_NAMES[month - 1]} · 农历{dayData?.lunar?.date_str || ""}
          </h1>
          <div className="text-xs mt-1 flex items-center gap-3 flex-wrap" style={{ color: COLOR.muted }}>
            <span>{dayData?.lunar?.year_in_ganzhi}年</span>
            <span>·</span>
            <span>{dayData?.lunar?.year_shengxiao}年</span>
            {dayData?.jie_qi_note && (
              <>
                <span>·</span>
                <span style={{ color: COLOR.jade }}>{dayData.jie_qi_note}</span>
              </>
            )}
          </div>
        </header>
      </Reveal>

      {/* ── 交互式月历 ── */}
      <Reveal delayMs={80}>
        <section className="card-raised relative overflow-hidden">
          {/* 月份导航 */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={goPrevMonth} className="btn-ghost text-xs tap" style={{ padding: "4px 10px" }}>
              ← 上月
            </button>
            <div className="flex items-center gap-3">
              <span className="text-lg font-display" style={{ color: COLOR.goldBright }}>
                {year}年{MONTH_NAMES[month - 1]}
              </span>
              <button onClick={goToday} className="text-[10px] tap" style={{ color: COLOR.gold }}>
                回今天
              </button>
            </div>
            <button onClick={goNextMonth} className="btn-ghost text-xs tap" style={{ padding: "4px 10px" }}>
              下月 →
            </button>
          </div>

          {/* 星期头 */}
          <div className="grid grid-cols-7 mb-1">
            {WEEKDAYS.map((wd, i) => (
              <div key={wd} className="text-center text-[10px] font-semibold py-1.5"
                style={{ color: i === 0 || i === 6 ? COLOR.goldDim : COLOR.muted }}>
                {wd}
              </div>
            ))}
          </div>

          {/* 日期网格 */}
          {loadingMonth ? (
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: 35 }).map((_, i) => (
                <SkeletonBlock key={i} height={68} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((cell, idx) => {
                if (cell.solarDay === 0) {
                  return <div key={`empty-${idx}`} className="aspect-square" />;
                }

                const d = cell.dayData;
                const active = cell.solarDay === selectedDay;
                const today = isToday(cell.solarDay);
                const isHuangdao = d?.is_huangdao;
                const isHeidao = d && !d.is_huangdao && !!d.zhi_xing;

                return (
                  <button
                    key={cell.solarDay}
                    onClick={() => setSelectedDay(cell.solarDay)}
                    className={`tap aspect-square flex flex-col items-center justify-center rounded-lg transition-all
                      ${active ? "ring-1" : "hover:bg-surface/60"}`}
                    style={{
                      background: active
                        ? `linear-gradient(135deg, rgba(201,162,75,0.18), rgba(201,162,75,0.06))`
                        : today
                          ? "rgba(79,179,160,0.08)"
                          : "transparent",
                      borderColor: active ? COLOR.gold : today ? COLOR.jadeDim : "transparent",
                      border: active ? `1px solid ${COLOR.gold}` : today ? `1px solid ${COLOR.jadeDim}` : "1px solid transparent",
                    }}
                  >
                    {/* 公历日期 */}
                    <span className="text-xs font-semibold" style={{
                      color: active ? COLOR.goldBright : today ? COLOR.jade : COLOR.ink,
                    }}>
                      {cell.solarDay}
                    </span>

                    {/* 农历日期 */}
                    <span className="text-[9px] leading-none mt-0.5" style={{
                      color: active ? COLOR.goldDim : COLOR.muted,
                    }}>
                      {d?.lunar_day === 1
                        ? `${d.lunar_month}月`
                        : (d?.lunar_day ? ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                           "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                           "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"][d.lunar_day - 1] : "") || d?.lunar_day}
                    </span>

                    {/* 干支简写 */}
                    {d?.day_ganzhi && (
                      <span className="text-[8px] mt-0.5" style={{ color: COLOR.goldDim }}>
                        {d.day_ganzhi}
                      </span>
                    )}

                    {/* 建除+黄道黑道标识 */}
                    {d?.zhi_xing && (
                      <span className="text-[8px] leading-tight px-1 rounded-sm mt-0.5" style={{
                        color: isHuangdao ? COLOR.jade : COLOR.danger,
                        background: isHuangdao ? "rgba(79,179,160,0.12)" : "rgba(200,85,61,0.08)",
                      }}>
                        {d.zhi_xing}
                      </span>
                    )}

                    {/* 冲生肖 */}
                    {d?.chong_shengxiao && (
                      <span className="text-[7px] mt-0.5" style={{ color: COLOR.danger }}>
                        冲{d.chong_shengxiao}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* 图例 */}
          <div className="flex items-center gap-4 mt-3 pt-3 border-t text-[10px]" style={{ borderColor: COLOR.lineSoft }}>
            <span className="flex items-center gap-1" style={{ color: COLOR.jade }}>
              <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgba(79,179,160,0.25)" }} /> 黄道吉日
            </span>
            <span className="flex items-center gap-1" style={{ color: COLOR.danger }}>
              <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgba(200,85,61,0.15)" }} /> 黑道
            </span>
            <span style={{ color: COLOR.muted }}>点击日期查看详情</span>
          </div>
        </section>
      </Reveal>

      {/* ── 选中日详情 ── */}
      {loadingDay ? (
        <div className="space-y-4">
          <SkeletonBlock height={100} />
          <SkeletonBlock height={80} />
          <SkeletonBlock height={120} />
        </div>
      ) : dayData ? (
        <div className="space-y-4">
          <AlmanacDetail data={dayData} />
        </div>
      ) : null}
    </div>
  );
}

// ── 黄历详情卡片组 ────────────────────────────────────────────────────
function AlmanacDetail({ data }: { data: AlmanacPayload }) {
  const d = data;
  const isHuangdao = d.jian_chu?.is_huangdao || d.tian_shen?.type === "黄道";

  return (
    <>
      {/* 今日概览横幅 */}
      <Reveal delayMs={120}>
        <section
          className="card-raised relative overflow-hidden"
          style={{
            background: isHuangdao
              ? `linear-gradient(135deg, rgba(79,179,160,0.10), rgba(22,27,34,0.6))`
              : `linear-gradient(135deg, rgba(201,162,75,0.10), rgba(22,27,34,0.6))`,
            borderColor: isHuangdao ? "rgba(79,179,160,0.3)" : COLOR.line,
          }}
        >
          {/* 装饰线条 */}
          <svg aria-hidden className="absolute right-0 top-0 h-full w-24 opacity-20 pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
            <circle cx="80" cy="50" r="70" fill="none" stroke={isHuangdao ? "var(--jade)" : "var(--gold-dim)"} strokeWidth="0.4" />
            <circle cx="80" cy="50" r="45" fill="none" stroke={isHuangdao ? "var(--jade)" : "var(--gold-dim)"} strokeWidth="0.3" />
          </svg>

          <div className="relative z-10 flex items-start gap-6 flex-wrap">
            {/* 中央: 干支柱 + 五行 + 建除 */}
            <div className="flex items-center gap-5 flex-wrap">
              {/* 日柱大字号 */}
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>日柱</span>
                <span className="font-display text-4xl mt-1" style={{
                  color: isHuangdao ? COLOR.jade : COLOR.goldBright,
                  textShadow: isHuangdao
                    ? "0 0 20px rgba(79,179,160,0.25)"
                    : "0 0 20px rgba(229,188,94,0.25)",
                }}>
                  {d.ganzhi.day.full}
                </span>
                <span className="text-[10px] mt-0.5" style={{ color: COLOR.muted }}>
                  {d.lunar.year_shengxiao}年 · {d.ganzhi.day.animal}
                </span>
              </div>

              {/* 五行 + 纳音 */}
              <div className="flex flex-col gap-1.5">
                <BadgeRow label="日干五行" value={d.wuxing.day_gan} color={d.wuxing.day_gan_color} />
                <BadgeRow label="日支五行" value={d.wuxing.day_zhi} color={COLOR.muted} />
                <BadgeRow label="纳音" value={d.na_yin.day} color={COLOR.goldDim} />
              </div>

              {/* 建除 + 黄道/黑道 */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.muted }}>建除</span>
                <span className="text-2xl font-display" style={{
                  color: isHuangdao ? COLOR.jade : COLOR.danger,
                }}>
                  {d.jian_chu.name}
                </span>
                <span className="tag text-[10px]" style={{
                  color: isHuangdao ? COLOR.jade : COLOR.danger,
                  borderColor: isHuangdao ? "rgba(79,179,160,0.4)" : "rgba(200,85,61,0.4)",
                  background: isHuangdao ? "rgba(79,179,160,0.10)" : "rgba(200,85,61,0.08)",
                }}>
                  {d.tian_shen.type || d.jian_chu.type}
                  {d.tian_shen.luck ? ` · ${d.tian_shen.luck}` : ""}
                </span>
                {d.tian_shen.name && (
                  <span className="text-[10px]" style={{ color: COLOR.muted }}>
                    {d.tian_shen.name}
                  </span>
                )}
              </div>
            </div>

            {/* 右侧: 月柱 + 年柱 */}
            <div className="flex flex-col gap-1 ml-auto text-right">
              <div className="text-[10px]" style={{ color: COLOR.muted }}>
                月柱: <span style={{ color: COLOR.ink }}>{d.ganzhi.month.full}</span>
              </div>
              <div className="text-[10px]" style={{ color: COLOR.muted }}>
                年柱: <span style={{ color: COLOR.ink }}>{d.ganzhi.year.full}</span>
                <span className="ml-1">({d.lunar.year_shengxiao})</span>
              </div>
              <div className="text-[10px]" style={{ color: COLOR.muted }}>
                年份纳音: <span style={{ color: COLOR.goldDim }}>{d.na_yin.year}</span>
              </div>
            </div>
          </div>
        </section>
      </Reveal>

      {/* 宜忌 + 吉神凶煞 — 双列 */}
      <div className="grid sm:grid-cols-2 gap-4">
        {/* 宜 */}
        <Reveal delayMs={160}>
          <section className="card-raised h-full">
            <div className="text-[10px] uppercase tracking-widest mb-3" style={{ color: COLOR.jade }}>宜</div>
            {d.yi_ji.yi.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {d.yi_ji.yi.map((item) => (
                  <span key={item} className="tag text-[11px]" style={{
                    color: COLOR.jade,
                    borderColor: "rgba(79,179,160,0.35)",
                    background: "rgba(79,179,160,0.08)",
                  }}>
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-xs" style={{ color: COLOR.muted }}>今日无特别宜事</div>
            )}
          </section>
        </Reveal>

        {/* 忌 */}
        <Reveal delayMs={180}>
          <section className="card-raised h-full">
            <div className="text-[10px] uppercase tracking-widest mb-3" style={{ color: COLOR.danger }}>忌</div>
            {d.yi_ji.ji.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {d.yi_ji.ji.map((item) => (
                  <span key={item} className="tag text-[11px]" style={{
                    color: COLOR.danger,
                    borderColor: "rgba(200,85,61,0.35)",
                    background: "rgba(200,85,61,0.06)",
                  }}>
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-xs" style={{ color: COLOR.muted }}>今日无忌事</div>
            )}
          </section>
        </Reveal>

        {/* 吉神 */}
        <Reveal delayMs={200}>
          <section className="card-raised">
            <div className="text-[10px] uppercase tracking-widest mb-3" style={{ color: COLOR.gold }}>吉神</div>
            {d.shen_sha.ji_shen.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {d.shen_sha.ji_shen.map((s) => (
                  <span key={s} className="tag text-[11px]" style={{
                    color: COLOR.goldBright,
                    borderColor: "rgba(229,188,94,0.35)",
                    background: "rgba(229,188,94,0.08)",
                  }}>
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-xs" style={{ color: COLOR.muted }}>—</div>
            )}
          </section>
        </Reveal>

        {/* 凶煞 */}
        <Reveal delayMs={220}>
          <section className="card-raised">
            <div className="text-[10px] uppercase tracking-widest mb-3" style={{ color: COLOR.danger }}>凶煞</div>
            {d.shen_sha.xiong_sha.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {d.shen_sha.xiong_sha.map((s) => (
                  <span key={s} className="tag text-[11px]" style={{
                    color: COLOR.danger,
                    borderColor: "rgba(200,85,61,0.3)",
                    background: "rgba(200,85,61,0.05)",
                  }}>
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-xs" style={{ color: COLOR.jade }}>今日无凶煞 · 较为清净</div>
            )}
          </section>
        </Reveal>
      </div>

      {/* 冲煞 + 胎神 + 星宿 — 三列 */}
      <div className="grid sm:grid-cols-3 gap-4">
        {/* 冲煞 */}
        <Reveal delayMs={240}>
          <section className="card-raised">
            <div className="text-[10px] uppercase tracking-widest mb-2" style={{ color: COLOR.gold }}>冲煞</div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLOR.muted }}>冲</span>
                <span style={{ color: COLOR.danger, fontWeight: 600 }}>
                  {d.chong_sha.chong}
                  {d.chong_sha.chong_shengxiao && ` (${d.chong_sha.chong_shengxiao})`}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLOR.muted }}>煞</span>
                <span style={{ color: COLOR.ink }}>{d.chong_sha.sha}方</span>
              </div>
              {d.chong_sha.chong_desc && (
                <div className="text-[10px] mt-1" style={{ color: COLOR.muted }}>
                  {d.chong_sha.chong_desc}
                </div>
              )}
            </div>
          </section>
        </Reveal>

        {/* 胎神 + 阴贵 */}
        <Reveal delayMs={260}>
          <section className="card-raised">
            <div className="text-[10px] uppercase tracking-widest mb-2" style={{ color: COLOR.gold }}>胎神 & 方位</div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLOR.muted }}>胎神</span>
                <span style={{ color: COLOR.ink }}>{d.tai_shen || "—"}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLOR.muted }}>阴贵</span>
                <span style={{ color: COLOR.ink }}>{d.yin_gui || "—"}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLOR.muted }}>日太岁</span>
                <span style={{ color: COLOR.ink }}>{d.tai_sui.day || "—"}</span>
              </div>
            </div>
          </section>
        </Reveal>

        {/* 星宿 */}
        <Reveal delayMs={280}>
          <section className="card-raised">
            <div className="text-[10px] uppercase tracking-widest mb-2" style={{ color: COLOR.gold }}>二十八星宿</div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xl font-display" style={{ color: COLOR.goldBright }}>
                {d.xing_xiu.name}
              </span>
              <span className="tag text-[10px]" style={{
                color: d.xing_xiu.luck === "吉" ? COLOR.jade : d.xing_xiu.luck === "凶" ? COLOR.danger : COLOR.inkSoft,
                borderColor: d.xing_xiu.luck === "吉" ? "rgba(79,179,160,0.4)" : d.xing_xiu.luck === "凶" ? "rgba(200,85,61,0.4)" : "var(--line)",
              }}>
                {d.xing_xiu.luck}
              </span>
            </div>
            {d.xing_xiu.song && (
              <div className="text-[10px] leading-relaxed" style={{ color: COLOR.muted }}>
                {d.xing_xiu.song.length > 80
                  ? d.xing_xiu.song.slice(0, 80) + "…"
                  : d.xing_xiu.song}
              </div>
            )}
          </section>
        </Reveal>
      </div>

      {/* 彭祖百忌 */}
      <Reveal delayMs={300}>
        <section className="card-raised">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.gold }}>彭祖百忌</span>
            <span className="text-[9px]" style={{ color: COLOR.muted }}>逐日提醒, 宜避开</span>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2" style={{ color: COLOR.inkSoft }}>
              <span className="tag text-[10px]" style={{
                color: COLOR.goldBright,
                borderColor: "rgba(229,188,94,0.35)",
              }}>
                干忌
              </span>
              <span>{d.pengzu_baiji.gan || "—"}</span>
            </div>
            <div className="flex items-center gap-2" style={{ color: COLOR.inkSoft }}>
              <span className="tag text-[10px]" style={{
                color: COLOR.goldBright,
                borderColor: "rgba(229,188,94,0.35)",
              }}>
                支忌
              </span>
              <span>{d.pengzu_baiji.zhi || "—"}</span>
            </div>
          </div>
        </section>
      </Reveal>

      {/* 数九/节气 */}
      {(d.shu_jiu || d.jie_qi) && (
        <Reveal delayMs={320}>
          <section className="card-raised">
            <div className="flex items-center gap-2 flex-wrap text-sm">
              <span className="text-[10px] uppercase tracking-widest" style={{ color: COLOR.gold }}>节令</span>
              {d.shu_jiu && (
                <span className="tag" style={{ color: COLOR.azure, borderColor: "rgba(91,141,239,0.35)" }}>
                  {d.shu_jiu}
                </span>
              )}
              {d.jie && (
                <span className="tag" style={{ color: COLOR.jade, borderColor: "rgba(79,179,160,0.35)" }}>
                  {d.jie}
                </span>
              )}
            </div>
          </section>
        </Reveal>
      )}

      {/* 数据源说明 */}
      <Reveal delayMs={340}>
        <details className="card-raised text-xs">
          <summary className="cursor-pointer" style={{ color: COLOR.goldBright }}>数据源与限制</summary>
          <div className="mt-2 space-y-1 leading-relaxed" style={{ color: COLOR.muted }}>
            <div>方法: {d.calculation_basis.method}</div>
            <div>规则版本: {d.calculation_basis.rule_version}</div>
            <div>数据源: {d.calculation_basis.input_source}</div>
            <div>限制: {d.calculation_basis.limits}</div>
          </div>
        </details>
      </Reveal>
    </>
  );
}

function BadgeRow({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span style={{ color: COLOR.muted, minWidth: 56 }}>{label}</span>
      <span className="tag text-[11px]" style={{ color, borderColor: color + "44" }}>
        {value}
      </span>
    </div>
  );
}
