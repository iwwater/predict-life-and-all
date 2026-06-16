import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchDaily, fetchMethods, type DailyPayload } from "../lib/api";
import { METHOD_PLAIN } from "../lib/method-info";
import type { MethodMeta } from "../lib/types";
import { useHistory } from "../store/history";

const METHOD_FALLBACK: MethodMeta[] = [
  { id: "bazi", name_zh: "八字四柱", name_en: "Four Pillars", school: "east" } as MethodMeta,
  { id: "ziwei", name_zh: "紫微斗数", name_en: "Zi Wei Dou Shu", school: "east" } as MethodMeta,
  { id: "tieban", name_zh: "铁板神数", name_en: "Iron Plate Numbers", school: "east" } as MethodMeta,
  { id: "qimen", name_zh: "奇门遁甲", name_en: "Qi Men Dun Jia", school: "east" } as MethodMeta,
  { id: "liuyao", name_zh: "六爻", name_en: "Six Lines", school: "east" } as MethodMeta,
  { id: "meihua", name_zh: "梅花易数", name_en: "Plum Blossom", school: "east" } as MethodMeta,
  { id: "liuren", name_zh: "大六壬", name_en: "Da Liu Ren", school: "east" } as MethodMeta,
  { id: "hepan", name_zh: "合盘", name_en: "Synastry", school: "east" } as MethodMeta,
  { id: "tarot", name_zh: "塔罗", name_en: "Tarot", school: "west" } as MethodMeta,
  { id: "western", name_zh: "西方占星", name_en: "Natal Astrology", school: "west" } as MethodMeta,
  { id: "vedic", name_zh: "吠陀占星", name_en: "Vedic Astrology", school: "west" } as MethodMeta,
  { id: "xuankong", name_zh: "玄空飞星", name_en: "Flying Stars", school: "east" } as MethodMeta,
  { id: "numerology", name_zh: "数字命理", name_en: "Numerology", school: "west" } as MethodMeta,
  { id: "lenormand", name_zh: "雷诺曼", name_en: "Lenormand", school: "west" } as MethodMeta,
];

const CATEGORY: Record<string, string> = {
  bazi: "Ming · 命",
  ziwei: "Ming · 命",
  tieban: "Ming · 命",
  chenggu: "Ming · 命",
  qimen: "Bu · 卜",
  liuyao: "Bu · 卜",
  meihua: "Bu · 卜",
  liuren: "Bu · 卜",
  xiaoliuren: "Bu · 卜",
  hepan: "Xiang · 相",
  tarot: "Xiang · 相",
  lenormand: "Xiang · 相",
  western: "Xiang · 相",
  vedic: "Xiang · 相",
  numerology: "Xiang · 相",
  bazhai: "Shan · 山",
  xuankong: "Shan · 山",
};

export function Home() {
  const [methods, setMethods] = useState<MethodMeta[]>([]);
  const [daily, setDaily] = useState<DailyPayload | null>(null);
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
    const source = methods.length > 0 ? methods : METHOD_FALLBACK;
    const preferred = [
      "bazi",
      "ziwei",
      "tieban",
      "qimen",
      "liuyao",
      "meihua",
      "liuren",
      "hepan",
      "tarot",
      "western",
      "vedic",
      "xuankong",
      "numerology",
      "lenormand",
    ];
    return preferred
      .map((id) => source.find((m) => m.id === id))
      .filter(Boolean) as MethodMeta[];
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
          <p className="mystic-latin-line">Fourteen arts of East &amp; West, computed not guessed.</p>
          <div className="mystic-cta-row">
            <Link className="mystic-cta" to="/m/tieban">
              <span />
              起盘
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
          <span>The Fourteen Arts</span>
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
