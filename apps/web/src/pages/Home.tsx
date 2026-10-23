import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchDaily, fetchMethods, type DailyPayload } from "../lib/api";
import { METHOD_PLAIN } from "../lib/method-info";
import { CATEGORY_BY_ID, FALLBACK_METHOD_META } from "../lib/method-registry";
import type { MethodMeta } from "../lib/types";
import { useHistory } from "../store/history";

// 卡片兜底数据 / 分类角标 / 面包屑标签统一由 method-registry.ts 单一真源派生
const METHOD_FALLBACK = FALLBACK_METHOD_META;
const CATEGORY = CATEGORY_BY_ID;

export function Home() {
  const [methods, setMethods] = useState<MethodMeta[]>([]);
  const [daily, setDaily] = useState<DailyPayload | null>(null);
  const [activeCategory, setActiveCategory] = useState("全部");
  const historyItems = useHistory((s) => s.items);

  useEffect(() => {
    fetchMethods().then(setMethods).catch(() => setMethods([]));
    const last = historyItems.find((it) => it.birth?.year);
    const birth = last
      ? {
          year: last.birth.year,
          month: last.birth.month,
          day: last.birth.day,
          hour: last.birth.hour,
          minute: last.birth.minute,
          gender: last.birth.gender,
          calendar: "gregorian" as const,
          lat: last.birth.lat ?? null,
          lng: last.birth.lng ?? null,
          tz: last.birth.tz,
          is_leap_month: false,
        }
      : undefined;
    fetchDaily(undefined, birth).then(setDaily).catch(() => setDaily(null));
  }, [historyItems]);

  const visibleMethods = useMemo(() => {
    // 后端 methods 列表不包含 dream 等非 engine 方法，但前端有独立页面，需合并补齐
    const source =
      methods.length > 0
        ? [
            ...methods,
            ...METHOD_FALLBACK.filter(
              (fb) => !methods.some((m) => m.id === fb.id),
            ),
          ]
        : METHOD_FALLBACK;
    const preferred = [
      "bazi",
      "ziwei",
      "tieban",
      "chenggu",
      "qimen",
      "liuyao",
      "meihua",
      "liuren",
      "xiaoliuren",
      "qian",
      "hepan",
      "tarot",
      "western",
      "vedic",
      "bazhai",
      "xuankong",
      "numerology",
      "lenormand",
      "dream",
    ];
    const ordered = preferred
      .map((id) => source.find((m) => m.id === id))
      .filter(Boolean) as MethodMeta[];
    return activeCategory === "全部"
      ? ordered
      : ordered.filter(
          (m) => (CATEGORY[m.id] || m.school).split(" ")[0] === activeCategory,
        );
  }, [methods, activeCategory]);

  const categoryTabs = useMemo(() => {
    const order = ["命", "卜", "相", "山", "杂"];
    const present = new Set(
      (methods.length > 0
        ? [...methods, ...METHOD_FALLBACK.filter((fb) => !methods.some((m) => m.id === fb.id))]
        : METHOD_FALLBACK
      ).map((m) => (CATEGORY[m.id] || m.school).split(" ")[0]),
    );
    return ["全部", ...order.filter((c) => present.has(c))];
  }, [methods]);

  return (
    <div className="mystic-home">
      <section className="mystic-stage">
        <div className="mystic-stage-copy">
          <div className="mystic-eyebrow">Computed to the minute · 精算如仪</div>
          <h1 className="mystic-display">
            知命,
            <br />
            而后 <b>从容</b>
          </h1>
          <p className="mystic-latin-line">Nineteen arts of East &amp; West, computed not guessed.</p>
          <div className="mystic-cta-row">
            <Link className="mystic-cta" to="/m/bazi">
              <span />
              起盘
            </Link>
            <Link className="mystic-quiet-link" to="/reading">
              直接问一句
            </Link>
            <a className="mystic-quiet-link" href="#arts">
              浏览术数
            </a>
            <Link className="mystic-quiet-link" to="/heshen">
              收入卷宗合参
            </Link>
          </div>
        </div>

        <Instrument />
      </section>

      {daily && <DailyRibbon payload={daily} />}

      <section className="mystic-section" id="arts">
        <div className="mystic-section-head">
          <h2>术数</h2>
          <span>The Nineteen Arts</span>
        </div>

        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            marginBottom: "1rem",
          }}
        >
          {categoryTabs.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                border: "1px solid var(--ink-soft, #9c8f7a)",
                borderRadius: "999px",
                background: activeCategory === cat ? "var(--cinnabar, #c8102e)" : "transparent",
                color: activeCategory === cat ? "#fff" : "var(--ink, #2b2b2b)",
                padding: "0.45rem 1rem",
                minHeight: "40px",
                fontSize: "0.86rem",
                cursor: "pointer",
                fontFamily: "'Noto Serif SC', serif",
                letterSpacing: "0.08em",
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="mystic-arts">
          {visibleMethods.map((method) => {
            const plain = METHOD_PLAIN[method.id as keyof typeof METHOD_PLAIN];
            return (
              <Link className="mystic-art" key={method.id} to={`/m/${method.id}`}>
                <span className="mystic-art-cat">{CATEGORY[method.id] || method.school}</span>
                <span className="mystic-art-name">
                  {method.name_zh}
                  <i>{method.name_en}</i>
                </span>
                <span className="mystic-art-hint">{plain?.tagline || "观盘"} →</span>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function DailyRibbon({ payload }: { payload: DailyPayload }) {
  const td = payload.today;
  return (
    <section className="mystic-daily-ribbon">
      <span>今日 · {payload.date}</span>
      <strong>
        {td.ganzhi_day} · {td.day_wuxing} · {td.tarot_card.name}
      </strong>
      <Link to="/daily">今日个人化 →</Link>
    </section>
  );
}

function Instrument() {
  const mountain = "子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥壬";
  const ticks = Array.from({ length: 72 }, (_, i) => i);
  const microTicks = Array.from({ length: 60 }, (_, i) => i);

  return (
    <div className="mystic-instrument" aria-hidden="true">
      <svg viewBox="0 0 600 600" role="img">
        <defs>
          <linearGradient id="mysticGold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#d6be8a" />
            <stop offset="1" stopColor="#8c7548" />
          </linearGradient>
        </defs>

        <g className="mystic-ring-slow">
          <circle cx="300" cy="300" r="272" />
          <circle cx="300" cy="300" r="238" className="thin" />
          {ticks.map((i) => {
            const a = (i * 5 * Math.PI) / 180;
            const length = i % 3 ? 5 : 11;
            return (
              <line
                key={i}
                x1={300 + Math.sin(a) * 272}
                y1={300 - Math.cos(a) * 272}
                x2={300 + Math.sin(a) * (272 - length)}
                y2={300 - Math.cos(a) * (272 - length)}
                className={i % 3 ? "minor" : "major"}
              />
            );
          })}
          {Array.from(mountain).map((char, i) => {
            const a = (i * 15 * Math.PI) / 180;
            const x = 300 + Math.sin(a) * 253;
            const y = 300 - Math.cos(a) * 253;
            return (
              <text key={char + i} x={x} y={y} transform={`rotate(${i * 15} ${x} ${y})`}>
                {char}
              </text>
            );
          })}
        </g>

        <g className="mystic-ring-rev">
          <circle cx="300" cy="300" r="196" className="middle" />
          <circle cx="300" cy="300" r="170" className="thin" />
          {microTicks.map((i) => {
            const a = (i * 6 * Math.PI) / 180;
            return (
              <line
                key={i}
                x1={300 + Math.sin(a) * 196}
                y1={300 - Math.cos(a) * 196}
                x2={300 + Math.sin(a) * 190}
                y2={300 - Math.cos(a) * 190}
                className="minor"
              />
            );
          })}
        </g>

        <g className="mystic-ring-static">
          <circle cx="300" cy="300" r="128" />
          <circle cx="300" cy="300" r="124" className="thin" />
          <circle cx="300" cy="300" r="86" className="thin" />
          <circle cx="300" cy="300" r="30" className="middle" />
          <line x1="300" y1="300" x2="300" y2="118" className="needle" />
          <circle cx="300" cy="300" r="2.5" className="hub" />
        </g>
      </svg>
    </div>
  );
}
