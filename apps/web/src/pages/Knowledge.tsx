// 玄学知识馆: 古典文献 · 五行详解 · 神煞大全 · 领域知识 · 职业五行（「古籍×仪器」纸墨风格）
import { useState, useMemo, useEffect } from "react";
import { WUXING_COLORS, WUXING_GLYPHS } from "../components/MysticElements";
import {
  fetchKnowledgeMethods,
  fetchBooks,
  type KnowledgeMethodsResponse,
  type BookEntry,
} from "../lib/api";

// ── 五行详解 ──────────────────────────────────────────────────────
const WUXING_DETAIL: Record<string, {
  name: string; direction: string; season: string; organ: string; taste: string;
  emotion: string; virtue: string; planet: string; animal: string; number: string;
  traits: string[]; generate: string; control: string; controlledBy: string;
}> = {
  木: { name:"木", direction:"东", season:"春", organ:"肝", taste:"酸", emotion:"怒", virtue:"仁", planet:"木星", animal:"青龙", number:"3/8",
    traits: ["生长","向上","条达","仁慈","创造力"], generate:"水生木", control:"木克土", controlledBy:"金克木" },
  火: { name:"火", direction:"南", season:"夏", organ:"心", taste:"苦", emotion:"喜", virtue:"礼", planet:"火星", animal:"朱雀", number:"2/7",
    traits: ["温热","明亮","上升","热情","行动力"], generate:"木生火", control:"火克金", controlledBy:"水克火" },
  土: { name:"土", direction:"中", season:"长夏", organ:"脾", taste:"甘", emotion:"思", virtue:"信", planet:"土星", animal:"勾陈", number:"5/10",
    traits: ["承载","生化","收纳","诚信","稳重"], generate:"火生土", control:"土克水", controlledBy:"木克土" },
  金: { name:"金", direction:"西", season:"秋", organ:"肺", taste:"辛", emotion:"悲", virtue:"义", planet:"金星", animal:"白虎", number:"4/9",
    traits: ["收敛","肃杀","变革","刚毅","决断力"], generate:"土生金", control:"金克木", controlledBy:"火克金" },
  水: { name:"水", direction:"北", season:"冬", organ:"肾", taste:"咸", emotion:"恐", virtue:"智", planet:"水星", animal:"玄武", number:"1/6",
    traits: ["滋润","下行","寒凉","智慧","洞察力"], generate:"金生水", control:"水克火", controlledBy:"土克水" },
};

const WUXING_KEYS = ["木","火","土","金","水"];

// ── 神煞大全 ──────────────────────────────────────────────────────
const SHENSHA_LIST = [
  { name:"天乙贵人", category:"贵人", desc:"最大的吉神，逢之主遇难有贵人相助，逢凶化吉。", condition:"甲戊见牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，庚辛逢虎马" },
  { name:"文昌贵人", category:"贵人", desc:"主学业、文书、科甲功名。", condition:"甲日见巳，乙日见午，丙日见申，丁日见酉，戊日见申，己日见酉，庚日见亥，辛日见子，壬日见寅，癸日见卯" },
  { name:"天德贵人", category:"贵人", desc:"主一生吉利，荣华富贵。", condition:"正月丁，二月申，三月壬，四月辛，五月亥，六月甲，七月癸，八月寅，九月丙，十月乙，十一月巳，十二月庚" },
  { name:"月德贵人", category:"贵人", desc:"与天德并称，主福气深厚。", condition:"寅午戌月见丙，申子辰月见壬，亥卯未月见甲，巳酉丑月见庚" },
  { name:"将星", category:"事业", desc:"主权柄威势，有领导才能。", condition:"寅午戌见午，巳酉丑见酉，申子辰见子，亥卯未见卯" },
  { name:"华盖", category:"才华", desc:"主艺术才华、孤独清高，利学术研究。", condition:"寅午戌见戌，巳酉丑见丑，申子辰见辰，亥卯未见未" },
  { name:"桃花", category:"姻缘", desc:"主容貌秀丽、人缘好、异性缘佳。", condition:"寅午戌见卯，巳酉丑见午，申子辰见酉，亥卯未见子" },
  { name:"羊刃", category:"凶煞", desc:"主刚强激烈，易有刑伤。", condition:"甲见卯，乙见寅，丙戊见午，丁己见巳，庚见酉，辛见申，壬见子，癸见亥" },
  { name:"驿马", category:"变动", desc:"主奔波走动、迁移旅行。", condition:"寅午戌见申，巳酉丑见亥，申子辰见寅，亥卯未见巳" },
  { name:"学堂", category:"学业", desc:"主学业有成、聪慧好学。", condition:"甲见亥，乙见午，丙戊见寅，丁己见酉，庚见巳，辛见子，壬见申，癸见卯" },
  { name:"天厨", category:"福气", desc:"主食禄丰厚、生活优裕。", condition:"甲见巳，乙见午，丙见子，丁见巳，戊见午，己见酉，庚见亥，辛见子，壬见寅，癸见卯" },
  { name:"红鸾", category:"姻缘", desc:"主婚姻喜事，与天喜并称婚庆双星。", condition:"子见卯，丑见寅，寅见丑，卯见子，辰见亥，巳见戌，午见酉，未见申，申见未，酉见午，戌见巳，亥见辰" },
];

// ── 经典文献 ──────────────────────────────────────────────────────
const CLASSICAL_CITATIONS = [
  { text:"日主旺则能任财官，宜克宜泄。身强者事业上有担当力，能承受压力。", source:"《渊海子平·卷一·论日主》", category:"命理" },
  { text:"用神有力则命格高，人生层次较高，关键节点能抓住机会。", source:"《渊海子平·卷一·论用神》", category:"命理" },
  { text:"财多身弱，富屋贫人：财虽多但身弱不胜财，看得到拿不到。宜守不宜攻。", source:"《渊海子平·论用神》", category:"财运" },
  { text:"食神制杀，英雄独压万人：七杀有制化为权，贵气十足。", source:"《渊海子平·论格局》", category:"格局" },
  { text:"伤官见官，为祸百端：伤官与正官同见，多是非口舌。", source:"《渊海子平·论格局》", category:"格局" },
  { text:"正官一位，清透无伤，为官清廉有权威。", source:"《三命通会·卷六·论正官》", category:"官运" },
  { text:"金白水清，相涵为贵：庚辛金见壬癸水，相生有情，主聪明俊秀。", source:"《三命通会·卷六·论金》", category:"五行" },
  { text:"火炎土燥，万物不生：火旺而无水润土，性格急躁，事业难成。", source:"《三命通会·卷六·论火》", category:"五行" },
  { text:"藤萝系甲，可春可秋：乙木见甲木为依附，柔中带刚。", source:"《滴天髓》", category:"干支" },
  { text:"阳刃驾杀，威震边疆：阳刃与七杀相配，主武将之命。", source:"《滴天髓》", category:"格局" },
  { text:"魁罡格者，聪明果断，但易刚愎自用。", source:"《三命通会·论魁罡》", category:"格局" },
  { text:"桃花驿马并见，风流潇洒，游走四方。", source:"《三命通会·论驿马》", category:"姻缘" },
];

// ── 职业五行 ──────────────────────────────────────────────────────
const PROFESSION_ELEMENTS = [
  { element:"木", professions:["教师","作家","医生","中医","园艺","环保","出版","传媒"], reason:"木主生发，宜教育、医疗、文化事业" },
  { element:"火", professions:["演艺","主持","广告","美发","厨师","餐饮","能源","科技"], reason:"火主炎上，宜舞台、传播、能源行业" },
  { element:"土", professions:["房地产","建筑","土木","陶瓷","农业","金融","保险","仓储"], reason:"土主承载，宜地产、建筑、金融业" },
  { element:"金", professions:["法律","公安","军人","机械","汽车","银行","会计","五金"], reason:"金主肃杀，宜政法、金融、制造业" },
  { element:"水", professions:["航运","贸易","旅游","记者","销售","水利","演艺","情报"], reason:"水主润下，宜流通、贸易、传媒行业" },
];

// ── 节气体质 ──────────────────────────────────────────────────────
const JIEQI_HEALTH = [
  { jieqi:"立春", element:"木", tips:"养肝护肝，早睡早起，情绪舒缓" },
  { jieqi:"立夏", element:"火", tips:"养心安神，午休养心，清淡饮食" },
  { jieqi:"立秋", element:"金", tips:"养肺润燥，收敛神气，少辛增酸" },
  { jieqi:"立冬", element:"水", tips:"养肾藏精，早卧晚起，避寒就温" },
];

type TabKey = "wuxing" | "shensha" | "classical" | "profession" | "wellness" | "books";

const tabs: { key: TabKey; label: string }[] = [
  { key:"wuxing", label:"五行详解" },
  { key:"shensha", label:"神煞大全" },
  { key:"classical", label:"经典文摘" },
  { key:"profession", label:"职业适配" },
  { key:"wellness", label:"节气养生" },
  { key:"books", label:"📚 文献书单" },
];

export function Knowledge() {
  const [tab, setTab] = useState<TabKey>("wuxing");

  return (
    <div className="space-y-5">
      <header>
        <h1 className="paper-title"><span className="stamp" />玄学知识馆</h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>
          五行生克 · 神煞大全 · 经典文摘 · 职业适配 · 节气体质 — 传统文化知识集
        </p>
      </header>

      {/* Tab 切换 */}
      <div className="flex flex-wrap gap-1.5">
        {tabs.map((t) => {
          const on = tab === t.key;
          return (
            <button key={t.key} type="button" onClick={() => setTab(t.key)}
              className="paper-tag" style={{
                fontSize: "0.82rem", fontWeight: 600, cursor: "pointer", padding: "0.35rem 0.85rem",
                color: on ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: on ? "var(--cinnabar)" : "var(--rule)",
              }}>
              {t.label}
            </button>
          );
        })}
      </div>

      <div key={tab} className="animate-fade-in">
        {tab === "wuxing" && <WuxingTab />}
        {tab === "shensha" && <ShenshaTab />}
        {tab === "classical" && <ClassicalTab />}
        {tab === "profession" && <ProfessionTab />}
        {tab === "wellness" && <WellnessTab />}
        {tab === "books" && <BooksTab />}
      </div>
    </div>
  );
}

function WuxingTab() {
  const [selected, setSelected] = useState("木");
  const detail = WUXING_DETAIL[selected];

  return (
    <div className="space-y-4">
      <section className="paper-frame">
        <h3 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>五行相生相克</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2" style={{ marginTop: "0.5rem" }}>
          {WUXING_KEYS.map((wx) => {
            const on = selected === wx;
            return (
              <button key={wx} type="button" onClick={() => setSelected(wx)}
                className="paper-grid-cell text-center" style={{
                  padding: "0.6rem", cursor: "pointer",
                  borderColor: on ? (WUXING_COLORS[wx] || "var(--cinnabar)") : "var(--rule)",
                  background: on ? `${WUXING_COLORS[wx]}10` : "var(--paper)",
                }}>
                <div style={{ fontSize: "1.5rem" }}>{WUXING_GLYPHS[wx]}</div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, fontFamily: "'Noto Serif SC', serif", color: on ? (WUXING_COLORS[wx] || "var(--cinnabar)") : "var(--ink-soft)", marginTop: "0.15rem" }}>{wx}</div>
              </button>
            );
          })}
        </div>
      </section>

      {detail && (
        <section className="paper-frame">
          <div className="flex items-center gap-3" style={{ marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "2rem" }}>{WUXING_GLYPHS[selected]}</span>
            <div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: WUXING_COLORS[selected] }}>{detail.name}</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>{detail.traits.join(" · ")}</p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2" style={{ fontSize: "0.8rem" }}>
            <DetailBlock label="方位" value={detail.direction} />
            <DetailBlock label="季节" value={detail.season} />
            <DetailBlock label="脏腑" value={detail.organ} />
            <DetailBlock label="五味" value={detail.taste} />
            <DetailBlock label="情志" value={detail.emotion} />
            <DetailBlock label="五德" value={detail.virtue} />
            <DetailBlock label="行星" value={detail.planet} />
            <DetailBlock label="神兽" value={detail.animal} />
          </div>
          <div className="paper-hr" />
          <div className="grid sm:grid-cols-3 gap-2" style={{ fontSize: "0.75rem" }}>
            <div className="paper-grid-cell" style={{ padding: "0.4rem 0.6rem", color: "var(--verdigris)", borderColor: "rgba(90,112,88,0.25)" }}>{detail.generate}</div>
            <div className="paper-grid-cell" style={{ padding: "0.4rem 0.6rem", color: "var(--cinnabar)", borderColor: "rgba(176,58,46,0.25)" }}>{detail.control}</div>
            <div className="paper-grid-cell" style={{ padding: "0.4rem 0.6rem", color: "var(--indigo)", borderColor: "rgba(47,72,88,0.25)" }}>受制: {detail.controlledBy}</div>
          </div>
        </section>
      )}
    </div>
  );
}

function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="paper-grid-cell" style={{ padding: "0.4rem 0.6rem" }}>
      <div style={{ fontSize: "0.6rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif", marginTop: "0.1rem" }}>{value}</div>
    </div>
  );
}

function ShenshaTab() {
  const categories = useMemo(() => {
    const cats = new Map<string, typeof SHENSHA_LIST>();
    for (const s of SHENSHA_LIST) {
      if (!cats.has(s.category)) cats.set(s.category, []);
      cats.get(s.category)!.push(s);
    }
    return Array.from(cats.entries());
  }, []);

  const catGlyphs: Record<string, string> = {
    贵人: "☰", 事业: "☲", 才华: "☴", 姻缘: "☱", 学业: "☵", 福气: "☷", 变动: "☳", 凶煞: "☶",
  };

  return (
    <div className="space-y-4">
      {categories.map(([cat, items]) => (
        <section key={cat} className="paper-frame">
          <h3 className="paper-section">
            <span className="num">{catGlyphs[cat] || "○"}</span>{cat}
          </h3>
          <div className="grid sm:grid-cols-2 gap-2">
            {items.map((s) => (
              <div key={s.name} className="paper-grid-cell" style={{
                padding: "0.5rem 0.75rem",
                borderColor: cat === "凶煞" ? "rgba(176,58,46,0.2)" : "var(--rule)",
              }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: cat === "凶煞" ? "var(--cinnabar)" : "var(--ink)", fontFamily: "'Noto Serif SC', serif", marginBottom: "0.2rem" }}>{s.name}</div>
                <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.5, marginBottom: "0.3rem" }}>{s.desc}</p>
                <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>
                  <span style={{ color: "var(--cinnabar)", opacity: 0.7 }}>查法:</span> {s.condition}
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function ClassicalTab() {
  return (
    <section className="paper-frame">
      <h3 className="paper-title"><span className="stamp" />古典文献精粹</h3>
      <p className="paper-body" style={{ fontSize: "0.75rem" }}>选自《渊海子平》《三命通会》《滴天髓》等经典，经现代解读重新阐释。</p>
      <div className="grid sm:grid-cols-2 gap-2" style={{ marginTop: "0.75rem" }}>
        {CLASSICAL_CITATIONS.map((item, i) => (
          <div key={i} className="paper-grid-cell" style={{ padding: "0.5rem 0.75rem", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "3px", height: "100%", background: "var(--cinnabar)", opacity: 0.4 }} />
            <div style={{ fontSize: "0.78rem", color: "var(--ink-soft)", lineHeight: 1.7, paddingLeft: "0.4rem" }}>"{item.text}"</div>
            <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.35rem", paddingLeft: "0.4rem", fontFamily: "'Noto Serif SC', serif" }}>
              {item.source}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProfessionTab() {
  return (
    <div className="space-y-3">
      {PROFESSION_ELEMENTS.map((pe) => (
        <section key={pe.element} className="paper-frame" style={{ borderLeft: `3px solid ${WUXING_COLORS[pe.element] || "var(--cinnabar)"}` }}>
          <div className="flex items-center gap-3" style={{ marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "1.5rem" }}>{WUXING_GLYPHS[pe.element]}</span>
            <div>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: WUXING_COLORS[pe.element] }}>五行属{pe.element}</h3>
              <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>{pe.reason}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {pe.professions.map((p) => (
              <span key={p} className="paper-tag" style={{
                color: WUXING_COLORS[pe.element],
                borderColor: `${WUXING_COLORS[pe.element]}40`,
                fontSize: "0.72rem",
              }}>{p}</span>
            ))}
          </div>
        </section>
      ))}
      <div style={{ fontSize: "0.65rem", color: "var(--ink-soft)", opacity: 0.6 }}>以上职业分类基于五行属性象征推导，不代表科学职业测评。</div>
    </div>
  );
}

function WellnessTab() {
  return (
    <section className="paper-frame">
      <h3 className="paper-title"><span className="stamp" />四时养生要略</h3>
      <p className="paper-body" style={{ fontSize: "0.78rem" }}>
        《黄帝内经·四气调神大论》:"夫四时阴阳者，万物之根本也。所以圣人春夏养阳，秋冬养阴。"
      </p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2" style={{ marginTop: "0.75rem" }}>
        {JIEQI_HEALTH.map((jq) => (
          <div key={jq.jieqi} className="paper-grid-cell text-center" style={{
            padding: "0.75rem", borderColor: `${WUXING_COLORS[jq.element]}30`,
          }}>
            <div style={{ fontSize: "1.5rem", marginBottom: "0.2rem" }}>{WUXING_GLYPHS[jq.element]}</div>
            <div style={{ fontSize: "0.88rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: WUXING_COLORS[jq.element], marginBottom: "0.3rem" }}>
              {jq.jieqi} · 属{jq.element}
            </div>
            <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.5 }}>{jq.tips}</p>
          </div>
        ))}
      </div>
      <div className="paper-grid-cell" style={{ padding: "0.6rem 0.85rem", fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "0.75rem", lineHeight: 1.8 }}>
        <strong style={{ color: "var(--cinnabar)" }}>四季食疗原则：</strong>
        春省酸增甘以养脾气（木旺克土），夏省苦增辛以养肺气（火旺克金），
        秋省辛增酸以养肝气（金旺克木），冬省咸增苦以养心气（水旺克火）。
        此五行相制之理，源自《千金要方》。
      </div>
    </section>
  );
}

// ── 📚 文献书单（古籍推荐） ───────────────────────────────────────────
function BooksTab() {
  const [methods, setMethods] = useState<KnowledgeMethodsResponse | null>(null);
  const [method, setMethod] = useState<string>("");
  const [books, setBooks] = useState<BookEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  // 加载术法清单
  useEffect(() => {
    let alive = true;
    fetchKnowledgeMethods()
      .then((res) => {
        if (!alive) return;
        setMethods(res);
        const first = res.methods.find((m) => (res.summary[m]?.total ?? 0) > 0);
        if (first) setMethod(first);
      })
      .catch((e) => setError(String(e)));
    return () => { alive = false; };
  }, []);

  // 切换术法或筛选时拉书单
  useEffect(() => {
    if (!method) return;
    let alive = true;
    setLoading(true);
    setError(null);
    fetchBooks(method, { maxPriority: 3, verifiedOnly })
      .then((res) => {
        if (!alive) return;
        setBooks(res.books);
      })
      .catch((e) => alive && setError(String(e)))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [method, verifiedOnly]);

  const summary = methods?.summary[method];
  const methodLabel = methods?.labels[method] ?? method;
  const star = (n: number) => "★".repeat(n) + "☆".repeat(3 - n);

  return (
    <div className="space-y-4">
      {/* 顶部：术法选择 + 摘要 */}
      <section className="paper-frame">
        <h3 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>📚 古典文献推荐</h3>
        <p className="paper-body" style={{ fontSize: "0.75rem", marginTop: "0.3rem", color: "var(--ink-soft)" }}>
          按术法分组；优先级 1=必修(★★★) / 2=进阶(★★) / 3=拓展(★)。
          推荐以公共领域版本为主，详见各条 <code>online_resources</code>。
        </p>

        <div className="flex flex-wrap items-center gap-2" style={{ marginTop: "0.7rem" }}>
          <select
            value={method}
            onChange={(e) => { setMethod(e.target.value); setOpenIdx(null); }}
            className="paper-tag"
            style={{ fontSize: "0.82rem", padding: "0.35rem 0.7rem", cursor: "pointer" }}
          >
            {methods?.methods.map((m) => (
              <option key={m} value={m}>
                {methods.labels[m] ?? m} ({methods.summary[m]?.total ?? 0} 本)
              </option>
            ))}
          </select>

          <label className="paper-tag" style={{ fontSize: "0.75rem", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
            />
            仅显示已验证
          </label>

          {summary && (
            <div className="paper-tag" style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
              已验证 {summary.verified}/{summary.total} 本 ·
              朝代: {Object.entries(summary.dynasties).slice(0, 4).map(([d, n]) => `${d} ${n}`).join(" · ")}
            </div>
          )}
        </div>
      </section>

      {/* 错误提示 */}
      {error && (
        <div className="paper-grid-cell" style={{ padding: "0.6rem 0.85rem", borderColor: "rgba(176,58,46,0.3)", color: "var(--cinnabar)", fontSize: "0.8rem" }}>
          ⚠ 加载失败: {error}
        </div>
      )}

      {/* 书单 */}
      <div className="space-y-2">
        {loading && (
          <div className="paper-grid-cell" style={{ padding: "1rem", textAlign: "center", color: "var(--ink-soft)", fontSize: "0.8rem" }}>
            正在加载…
          </div>
        )}

        {!loading && books.length === 0 && (
          <div className="paper-grid-cell" style={{ padding: "1rem", textAlign: "center", color: "var(--ink-soft)", fontSize: "0.8rem" }}>
            当前筛选下无书单；请尝试切换术法或取消"仅显示已验证"。
          </div>
        )}

        {books.map((b, i) => {
          const open = openIdx === i;
          const isVerified = !!b.verified_examples;
          return (
            <div key={`${b.title}-${i}`} className="paper-frame" style={{ padding: "0.6rem 0.85rem" }}>
              {/* 标题行 */}
              <button
                type="button"
                onClick={() => setOpenIdx(open ? null : i)}
                className="w-full text-left flex items-start justify-between gap-2"
                style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
              >
                <div className="flex-1">
                  <div style={{ fontSize: "0.95rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: "var(--ink)" }}>
                    {b.title}
                    <span style={{ fontSize: "0.72rem", color: "var(--cinnabar)", marginLeft: "0.5rem", letterSpacing: "0.05em" }}>
                      {star(b.priority)}
                    </span>
                    {isVerified && (
                      <span style={{ fontSize: "0.62rem", color: "var(--verdigris)", marginLeft: "0.4rem", border: "1px solid var(--verdigris)", padding: "0 0.3rem", borderRadius: "0.2rem" }}>
                        ✓ 已验证
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>
                    {b.dynasty} · {b.author} · {b.difficulty}
                  </div>
                </div>
                <span style={{ fontSize: "0.8rem", color: "var(--ink-soft)", flexShrink: 0, transition: "transform 0.2s", transform: open ? "rotate(180deg)" : "none" }}>
                  ▾
                </span>
              </button>

              {/* 折叠详情 */}
              {open && (
                <div className="animate-fade-in" style={{ marginTop: "0.6rem", fontSize: "0.78rem", color: "var(--ink)", lineHeight: 1.7 }}>
                  <p style={{ marginBottom: "0.5rem" }}>{b.description}</p>

                  {b.key_chapters.length > 0 && (
                    <div style={{ marginBottom: "0.4rem" }}>
                      <span style={{ color: "var(--cinnabar)", fontSize: "0.7rem", opacity: 0.8 }}>▸ 核心篇章: </span>
                      <span style={{ fontFamily: "'Noto Serif SC', serif" }}>{b.key_chapters.join(" · ")}</span>
                    </div>
                  )}

                  {isVerified && (
                    <div style={{ marginBottom: "0.4rem", padding: "0.4rem 0.6rem", background: "rgba(90,112,88,0.08)", borderRadius: "0.2rem", fontSize: "0.72rem" }}>
                      <span style={{ color: "var(--verdigris)", fontWeight: 600 }}>✓ 验证: </span>
                      {b.verified_examples}
                    </div>
                  )}

                  {b.online_resources && b.online_resources.length > 0 && (
                    <div style={{ marginBottom: "0.4rem", fontSize: "0.72rem" }}>
                      <span style={{ color: "var(--cinnabar)", opacity: 0.8 }}>▸ 在线资源: </span>
                      <span style={{ color: "var(--ink-soft)" }}>{b.online_resources.join(" / ")}</span>
                    </div>
                  )}

                  {b.book_file && (
                    <div style={{ marginBottom: "0.4rem", fontSize: "0.72rem", color: "var(--ink-soft)" }}>
                      <span style={{ color: "var(--cinnabar)", opacity: 0.8 }}>▸ 本地文件: </span>
                      <code style={{ fontFamily: "'JetBrains Mono', monospace" }}>docs/{b.book_file}</code>
                    </div>
                  )}

                  {b.notes && (
                    <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "var(--ink-soft)", fontStyle: "italic", borderLeft: "2px solid var(--rule)", paddingLeft: "0.6rem" }}>
                      {b.notes}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 版权声明 */}
      <div className="paper-grid-cell" style={{ padding: "0.6rem 0.85rem", fontSize: "0.68rem", color: "var(--ink-soft)", lineHeight: 1.7 }}>
        <strong style={{ color: "var(--cinnabar)" }}>⚖ 版权：</strong>
        平台仅推荐公共领域 (public domain) 或已获合法授权的古籍版本；
        建议读者通过 <em>书格 (shuge.org)</em>、<em>殆知阁 (daizhige.org)</em>、<em>中国国家图书馆</em> 等
        公益数字图书馆获取扫描版，或购买正版纸本以支持古籍数字化。
        本平台所有推断仅供文化研究与娱乐参考，<strong>不构成</strong>医疗、投资、婚姻、法律等决策依据。
      </div>
    </div>
  );
}
