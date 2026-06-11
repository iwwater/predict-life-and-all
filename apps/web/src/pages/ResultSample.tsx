// 「古籍×仪器」结果页 · 风格样张 (静态稿)
// 依据:《前端视觉重设计规范》§2 设计语言 / §3 关键页面落地
// 用途:先做一页交付确认, 再铺全站。本文件只服务"无 sessionStorage 数据"分支,
//       live 数据路径仍在 Result.tsx。
import { Link } from "react-router-dom";

/* ─────────── 静态示例数据(占位,后续接 ChartResult) ─────────── */

const SAMPLE_BIRTH = {
  gregorian: "1990-05-15  08:30",
  solar: "08:18",
  gender: "男",
  place: "上海  31.23°N  121.47°E",
  year_gz: "庚午",
  day_master: "戊土",
  question: "今年事业如何?",
};

const PILLARS = [
  {
    label: "年柱",
    pillar: "庚午",
    ganzhi: ["庚", "午"],
    hidden: ["己·本", "丁·中"],
    shenshen: ["比肩", "劫财"],
    nayin: "路旁土",
  },
  {
    label: "月柱",
    pillar: "辛巳",
    ganzhi: ["辛", "巳"],
    hidden: ["庚·本", "戊·中", "丙·余"],
    shenshen: ["偏印", "食神"],
    nayin: "白蜡金",
  },
  {
    label: "日柱",
    pillar: "戊辰",
    ganzhi: ["戊", "辰"],
    hidden: ["戊·本", "乙·中", "癸·余"],
    shenshen: ["日主", "七杀"],
    nayin: "大林木",
  },
  {
    label: "时柱",
    pillar: "甲寅",
    ganzhi: ["甲", "寅"],
    hidden: ["甲·本", "丙·中", "戊·余"],
    shenshen: ["偏官", "偏财"],
    nayin: "大溪水",
  },
];

const WUXING = [
  { key: "金", v: 3, label: "Metal" },
  { key: "木", v: 3, label: "Wood" },
  { key: "水", v: 1, label: "Water" },
  { key: "火", v: 5, label: "Fire" },
  { key: "土", v: 4, label: "Earth" },
];

const LUCK = [
  { from: "6",  to: "15", ganzhi: "壬午", note: "初运 · 学堂" },
  { from: "16", to: "25", ganzhi: "癸未", note: "建业" },
  { from: "26", to: "35", ganzhi: "甲申", note: "进取" },
  { from: "36", to: "45", ganzhi: "丙戌", note: "火土并旺 · 事业峰" },
  { from: "46", to: "55", ganzhi: "丁亥", note: "泄秀" },
];

const ANNUAL = [
  { y: "2024", gz: "甲辰", note: "财星透 · 守" },
  { y: "2025", gz: "乙巳", note: "七杀动 · 动" },
  { y: "2026", gz: "丙午", note: "印刃并见 · 主升", active: true },
  { y: "2027", gz: "丁未", note: "食伤生财 · 续" },
];

const REMEDIES = [
  {
    cost: "free",
    cat: "行为",
    yi: "宜",
    title: "晨起向东南行,亲近园林木气",
    basis: "日主戊土偏弱,木为官杀,晨行以木气激官贵之机。",
    mech:  "木疏土壅,动则生发",
    src:   "《滴天髓·通神》",
    caution: "忌夜间独行远路,耗泄日主。",
  },
  {
    cost: "free",
    cat: "行为",
    yi: "宜",
    title: "工位南向置暖光灯,午时短晒",
    basis: "巳午火旺为印星,扶日主以收印制食伤之功。",
    mech:  "火印扶身,泄秀归正",
    src:   "《穷通宝鉴·五月戊土》",
  },
  {
    cost: "low",
    cat: "方位",
    yi: "宜",
    title: "书桌坐向取东南,木椅或木质文具",
    basis: "东南为木火通明之方,与命局喜用契合。",
    mech:  "方位取象,木火同明",
    src:   "《八宅明镜·灶口》",
  },
  {
    cost: "low",
    cat: "物",
    yi: "宜",
    title: "随身木梳 / 桃木小件(忌雕龙凤)",
    basis: "木气随身助日主调候,小件即足。",
    mech:  "随身木气,缓补官杀",
    src:   "《沈氏玄空学·七星辅弼》",
    caution: "勿购开光 / 符咒类高价物。本品仅作象征性定位,非医疗或财务建议。",
  },
  {
    cost: "low",
    cat: "色",
    yi: "宜",
    title: "今年丙午,内衬可取浅红 / 暖橙",
    basis: "借流年丙午火势,助印星扶身。",
    mech:  "色助印气,以应天时",
    src:   "传统色相配五行表",
  },
  {
    cost: "medium",
    cat: "位",
    yi: "咨询专业",
    title: "居家东南角设小型绿植架 / 木质书架",
    basis: "补救大运东南宫位木气不足。",
    mech:  "方位补救,木火通明",
    src:   "《八宅明镜·生气方》",
    caution: "建议咨询专业室内设计 / 风水师现场勘宅。",
  },
];

const SOURCES = [
  "《渊海子平》卷三 · 论日主强弱",
  "《滴天髓》通神六义 · 旺衰",
  "《穷通宝鉴》五月戊土 · 调候",
  "《三命通会》· 化气格",
  "《沈氏玄空学》· 兼向替卦",
  "《八宅明镜》· 八游年诀",
];

/* ─────────── 子组件 ─────────── */

function Header() {
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 mb-4 text-sm"
      style={{ color: "var(--ink-soft)" }}
    >
      <div className="flex items-center gap-3 flex-wrap" style={{ color: "var(--ink)" }}>
        <span style={{ color: "var(--ink-soft)" }}>命主</span>
        <span className="paper-mono">{SAMPLE_BIRTH.gregorian}</span>
        <span style={{ color: "var(--ink-soft)" }}>· {SAMPLE_BIRTH.gender}</span>
        <span style={{ color: "var(--ink-soft)" }}>· {SAMPLE_BIRTH.place}</span>
        <span style={{ color: "var(--ink-soft)" }}>· 真太阳时</span>
        <span className="paper-mono">{SAMPLE_BIRTH.solar}</span>
        <span className="paper-seal" style={{ width: "1.5rem", height: "1.5rem", fontSize: "0.7rem", lineHeight: "1.5rem", marginLeft: "0.4rem" }}>
          命
        </span>
        <span style={{ color: "var(--cinnabar)", fontWeight: 600, letterSpacing: "0.08em" }}>
          「{SAMPLE_BIRTH.question}」
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button className="paper-btn-ghost">收藏</button>
        <button className="paper-btn-ghost">反馈</button>
        <button className="paper-btn-ghost">分享</button>
        <Link to="/cast" className="paper-btn-ghost">再排一盘</Link>
      </div>
    </div>
  );
}

function TitleBar() {
  return (
    <div className="flex items-baseline justify-between mb-5 flex-wrap gap-2">
      <h1 className="paper-title">
        <span className="stamp" />
        <span>庚午年命书</span>
        <span className="sub">壬寅集 · 第三六号</span>
      </h1>
      <span className="paper-eyebrow">排盘台·戊所 · 二〇二六年丙午</span>
    </div>
  );
}

function PillarsRow() {
  return (
    <div>
      <div className="paper-section">
        <span className="num">壹</span>四柱八字 · 八字立命
      </div>
      <div className="grid grid-cols-4 gap-2">
        {PILLARS.map((p) => (
          <div key={p.label} className="paper-pillar">
            <div>
              <span className="paper-eyebrow" style={{ display: "block", marginBottom: "0.4rem" }}>
                {p.label}
              </span>
              <div className="ganzhi">
                <span className="tiangan">{p.ganzhi[0]}</span>
                <span className="dizhi">{p.ganzhi[1]}</span>
              </div>
            </div>
            <div className="meta">
              {p.hidden.map((h, i) => (
                <div key={i}>{h}</div>
              ))}
            </div>
            <div className="ten-god">{p.shenshen.join(" · ")}</div>
            <div className="meta" style={{ borderTop: "1px solid var(--rule)", paddingTop: "0.2rem" }}>
              纳音 {p.nayin}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WuxingRadar() {
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const max = 6;
  const r = 88;
  const angles = WUXING.map((_, i) => (Math.PI * 2 * i) / WUXING.length - Math.PI / 2);
  const points = WUXING.map((w, i) => {
    const ratio = Math.min(w.v / max, 1);
    const rr = ratio * r;
    return [cx + Math.cos(angles[i]) * rr, cy + Math.sin(angles[i]) * rr];
  });
  const rings = [0.25, 0.5, 0.75, 1].map((k) =>
    WUXING.map((_, i) => {
      const rr = k * r;
      return [cx + Math.cos(angles[i]) * rr, cy + Math.sin(angles[i]) * rr].join(",");
    }).join(" ")
  );
  const axisLines = WUXING.map((_, i) => {
    return [cx, cy, cx + Math.cos(angles[i]) * r, cy + Math.sin(angles[i]) * r];
  });
  const fillPath = "M " + points.map((p) => p.join(",")).join(" L ") + " Z";
  return (
    <div>
      <div className="paper-section">
        <span className="num">贰</span>五行流转 · 五气布于四时
      </div>
      <div className="paper-grid-cell" style={{ padding: "1rem" }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block", margin: "0 auto" }}>
          {rings.map((d, i) => (
            <polygon key={i} points={d} fill="none" stroke="var(--rule)" strokeWidth="0.5" />
          ))}
          {axisLines.map(([x1, y1, x2, y2], i) => (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--rule)" strokeWidth="0.5" />
          ))}
          <path d={fillPath} fill="var(--cinnabar)" fillOpacity="0.08" stroke="var(--cinnabar)" strokeWidth="1" />
          {WUXING.map((w, i) => {
            const [px, py] = points[i];
            const [lx, ly] = [cx + Math.cos(angles[i]) * (r + 18), cy + Math.sin(angles[i]) * (r + 18)];
            return (
              <g key={w.key}>
                <circle cx={px} cy={py} r="2.4" fill="var(--cinnabar)" />
                <text
                  x={lx}
                  y={ly}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontFamily="Noto Serif SC, serif"
                  fontSize="13"
                  fill="var(--ink)"
                  style={{ letterSpacing: "0.2em" }}
                >
                  {w.key}
                </text>
              </g>
            );
          })}
          {WUXING.map((w, i) => {
            const ratio = Math.min(w.v / max, 1);
            const rr = ratio * r;
            const [px, py] = [cx + Math.cos(angles[i]) * rr, cy + Math.sin(angles[i]) * rr];
            return (
              <text
                key={"n" + w.key}
                x={px + 6}
                y={py - 6}
                fontFamily="JetBrains Mono, monospace"
                fontSize="10"
                fill="var(--ink-soft)"
              >
                {w.v}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

function LuckAndAnnual() {
  return (
    <div>
      <div className="paper-section">
        <span className="num">叁</span>大运流年 · 时之所趋
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="paper-eyebrow" style={{ marginBottom: "0.4rem" }}>大运  起于六岁</div>
          <div className="grid grid-cols-5 gap-px" style={{ background: "var(--rule)" }}>
            {LUCK.map((l, i) => (
              <div key={i} className="paper-grid-cell" style={{ padding: "0.45rem 0.35rem", textAlign: "center" }}>
                <div className="paper-mono" style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
                  {l.from}–{l.to}
                </div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--ink)", fontFamily: "Noto Serif SC, serif" }}>
                  {l.ganzhi}
                </div>
                <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)", letterSpacing: "0.05em" }}>
                  {l.note}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="paper-eyebrow" style={{ marginBottom: "0.4rem" }}>流年  近五年</div>
          <div className="space-y-1.5">
            {ANNUAL.map((a) => (
              <div
                key={a.y}
                className="paper-grid-cell"
                style={{
                  padding: "0.4rem 0.7rem",
                  display: "flex",
                  alignItems: "baseline",
                  gap: "0.7rem",
                  background: a.active ? "rgba(176, 58, 46, 0.05)" : "var(--paper)",
                  borderColor: a.active ? "var(--cinnabar)" : "var(--rule)",
                }}
              >
                <span className="paper-mono" style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>{a.y}</span>
                <span style={{ fontFamily: "Noto Serif SC, serif", fontWeight: 700, color: a.active ? "var(--cinnabar)" : "var(--ink)", minWidth: "2.4rem" }}>
                  {a.gz}
                </span>
                <span style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>{a.note}</span>
                {a.active && (
                  <span className="paper-source" style={{ marginLeft: "auto", borderLeftColor: "var(--cinnabar)" }}>
                    主运
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function CalculationBasis() {
  return (
    <div className="mt-4">
      <div className="paper-section" style={{ marginBottom: "0.5rem" }}>
        <span className="num">肆</span>排盘依据 · 文献校验
      </div>
      <div className="paper-grid-cell" style={{ fontSize: "0.78rem", color: "var(--ink-soft)", lineHeight: 1.85 }}>
        <div>
          <span className="paper-mono" style={{ color: "var(--ink)" }}>方法</span> 八字 · lunar-python · 真太阳时校正
          (经度差 + 均时差,&lt;0.1 分钟)
        </div>
        <div>
          <span className="paper-mono" style={{ color: "var(--ink)" }}>历法</span> 农历 1990 年 4 月 21 日 辰时
          · 公历 1990-05-15 08:30
        </div>
        <div>
          <span className="paper-mono" style={{ color: "var(--ink)" }}>节气</span> 立夏后第十二日, 月令巳火当权
        </div>
        <div>
          <span className="paper-mono" style={{ color: "var(--ink)" }}>边界</span> 子时换日按"晚子"默认; 子时开关(late/early)可在设置里切换。
        </div>
      </div>
    </div>
  );
}

function CommentaryPanel() {
  return (
    <div style={{ display: "flex", gap: "0.85rem", alignItems: "stretch" }}>
      <div className="paper-vertical" style={{ flexShrink: 0 }}>
        庚午年命书 · 事业运次
      </div>
      <div className="flex-1 min-w-0">
        <div className="paper-section">
          <span className="num">伍</span>批文 · 先生断
        </div>

        <div className="paper-body" style={{ marginBottom: "1rem" }}>
          <p>
            戊土日主,生于巳月,火旺印绶当权。年柱庚午、月柱辛巳,印星重重而日主得扶,谓之
            <span style={{ fontWeight: 700 }}>身中而印旺</span>。
            时柱甲寅,七杀透于时上,兼寅中甲木本气、丙火中气、戊土余气,格局有&quot;杀印相生&quot;之象。
          </p>
          <p>
            问今年事业,流年丙午,丙为食神、午为丁火伤官,印星午火与流年午火同气,印刃并见,
            主升迁、声誉、掌权之兆。然午午自刑,冲动月令巳火,印星过旺则泄秀太过,
            <span style={{ fontWeight: 700 }}>宜守而不宜急进</span>,
            待秋金司令,食伤生财,方为名利双收之时。
          </p>
          <p>
            用神取木(财官)与火(印星)并用。木以疏土,火以扶身。
            忌水过重(克火印)、忌金过锐(损木财)。今年忌北行远涉,利东南近取。
          </p>
        </div>

        <div className="paper-section" style={{ marginTop: "1rem" }}>
          <span className="num">陆</span>出处小注 · 有据可考
        </div>
        <ul className="space-y-1.5" style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {SOURCES.map((s, i) => (
            <li key={i}>
              <span className="paper-source">{s}</span>
            </li>
          ))}
        </ul>

        <div className="paper-caution" style={{ marginTop: "1rem" }}>
          ※ 凡论命只作倾向与参照,非断言;若所断与事实相违,以事实为准,勿执迷。
        </div>
      </div>
    </div>
  );
}

function RemedyPanel() {
  return (
    <div>
      <div className="paper-section" style={{ fontSize: "1rem" }}>
        <span className="num">柒</span>化解之法 · free 排前
      </div>
      <p className="paper-body" style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginBottom: "0.85rem" }}>
        以下处方依本盘喜用与九宫叠加而成。free → low → medium 渐次排列,
        仅作象征性调理与方位参考,非医疗、亦非财务方案。
      </p>
      <div>
        {REMEDIES.map((r, i) => (
          <div key={i} className="paper-remedy flex flex-wrap gap-4 items-baseline">
            <div style={{ flex: "0 0 auto", display: "flex", flexDirection: "column", gap: "0.25rem", minWidth: "6rem" }}>
              <span className={r.yi === "宜" ? "yi" : "warn"}>{r.yi}</span>
              <span className="cost">{r.cost}</span>
              <span style={{ fontSize: "0.7rem", color: "var(--ink-soft)", letterSpacing: "0.1em" }}>{r.cat}</span>
            </div>
            <div style={{ flex: 1, minWidth: "20rem" }}>
              <div style={{ fontFamily: "Noto Serif SC, serif", fontWeight: 700, fontSize: "1rem", color: "var(--ink)", marginBottom: "0.3rem", letterSpacing: "0.04em" }}>
                {r.title}
              </div>
              <div style={{ fontSize: "0.83rem", color: "var(--ink)", lineHeight: 1.75, marginBottom: "0.35rem" }}>
                <span className="paper-mono" style={{ color: "var(--ink-soft)", marginRight: "0.5rem" }}>据</span>
                {r.basis}
              </div>
              <div style={{ fontSize: "0.83rem", color: "var(--ink)", lineHeight: 1.75, marginBottom: "0.35rem" }}>
                <span className="paper-mono" style={{ color: "var(--ink-soft)", marginRight: "0.5rem" }}>理</span>
                {r.mech}
                <span className="paper-source" style={{ marginLeft: "0.6rem" }}>{r.src}</span>
              </div>
              {r.caution && (
                <div className="paper-caution" style={{ marginTop: "0.4rem" }}>※ {r.caution}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Fanli() {
  return (
    <div className="paper-fanli">
      <div className="paper-fanli-title">凡 例</div>
      <p>
        一、本平台所排八字、紫微、奇门、六爻、梅花、塔罗诸盘,皆依传统文献与公版定数,以命理、象数、概率之理为用,
        非科学预测,亦不替代医疗、法律、财务与心理专业意见。
      </p>
      <p>
        二、化解之法为象征性调理与方位参照,不构成对任何具体物品、法事、仪式的推荐或保证;凡涉及健康、法律、投资的决定,
        请径询专业人士。
      </p>
      <p>
        三、平台对解读输出经护栏过滤:危机话题仅返回援助渠道;绝对化措辞一律软化为倾向性建议。
        解读依据仅以本盘所呈为限,凡盘面之外皆属杜撰。
      </p>
      <p>
        四、用户出生信息仅在本机浏览器内短期缓存,不入后端数据库;LLM Key 由用户自管,平台不接收。
      </p>
    </div>
  );
}

export function ResultSample() {
  return (
    <div className="paper-page" style={{ padding: "0.5rem 0 1.5rem" }}>
      <Header />

      <div className="paper-frame">
        <div className="paper-compass-bg" aria-hidden />
        <TitleBar />

        <div className="paper-main-grid">
          <div className="space-y-5 min-w-0">
            <PillarsRow />
            <WuxingRadar />
            <LuckAndAnnual />
            <CalculationBasis />
          </div>
          <div className="min-w-0">
            <CommentaryPanel />
          </div>
        </div>

        <div className="paper-hr-double" />

        <RemedyPanel />
      </div>

      <div style={{ marginTop: "1.25rem" }}>
        <Fanli />
      </div>

      <div style={{ marginTop: "1rem", display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "0.5rem", color: "var(--ink-soft)" }}>
        <span className="paper-mono" style={{ fontSize: "0.7rem", letterSpacing: "0.15em" }}>DESIGN SAMPLE · v0</span>
        <span style={{ fontSize: "0.7rem" }}>· 依据《前端视觉重设计规范》交付确认后再铺全站</span>
      </div>
    </div>
  );
}
