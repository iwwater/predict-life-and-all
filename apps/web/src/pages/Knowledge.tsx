// 玄学知识馆: 古典文献 · 五行详解 · 神煞大全 · 领域知识 · 职业五行
// 用现有知识库数据(不调 API),搭配神秘学装饰
import { useState, useMemo } from "react";
import { COLOR } from "../components/ui";
import { Reveal } from "../components/Interactions";
import { YinYang, WuXingRing, FlowerOfLife, MetatronCube, WUXING_COLORS, WUXING_GLYPHS, PlanetSymbols } from "../components/MysticElements";

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

const WUXING_KEYS = ["木", "火", "土", "金", "水"];

// ── 神煞大全 ──────────────────────────────────────────────────────
const SHENSHA_LIST = [
  { name:"天乙贵人", category:"贵人", desc:"最大的吉神，逢之主遇难有贵人相助，逢凶化吉。", condition:"甲戊见牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，庚辛逢虎马" },
  { name:"文昌贵人", category:"贵人", desc:"主学业、文书、科甲功名。", condition:"甲日见巳，乙日见午，丙日见申，丁日见酉，戊日见申，己日见酉，庚日见亥，辛日见子，壬日见寅，癸日见卯" },
  { name:"天德贵人", category:"贵人", desc:"主一生吉利，荣华富贵。天德所在之月百事皆宜。", condition:"正月丁，二月申，三月壬，四月辛，五月亥，六月甲，七月癸，八月寅，九月丙，十月乙，十一月巳，十二月庚" },
  { name:"月德贵人", category:"贵人", desc:"与天德并称，主福气深厚。月德入命，女命尤吉。", condition:"寅午戌月见丙，申子辰月见壬，亥卯未月见甲，巳酉丑月见庚" },
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

type TabKey = "wuxing" | "shensha" | "classical" | "profession" | "wellness";

const tabs: { key: TabKey; label: string; icon: string }[] = [
  { key:"wuxing", label:"五行详解", icon:"☯️" },
  { key:"shensha", label:"神煞大全", icon:"⭐" },
  { key:"classical", label:"经典文摘", icon:"📜" },
  { key:"profession", label:"职业适配", icon:"💼" },
  { key:"wellness", label:"节气养生", icon:"🌿" },
];

export function Knowledge() {
  const [tab, setTab] = useState<TabKey>("wuxing");

  return (
    <div className="space-y-6">
      {/* 神圣几何背景 */}
      <div className="fixed right-0 bottom-0 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <FlowerOfLife size={300} />
      </div>
      <div className="fixed -left-16 top-1/4 pointer-events-none opacity-[0.03] z-0" aria-hidden>
        <MetatronCube size={240} />
      </div>

      <Reveal>
        <header>
          <h1 className="text-2xl font-display" style={{ color: COLOR.goldBright }}>玄学知识馆</h1>
          <p className="text-sm mt-1" style={{ color: COLOR.muted }}>
            五行生克 · 神煞大全 · 经典文摘 · 职业适配 · 节气体质 — 传统文化知识集
          </p>
        </header>
      </Reveal>

      {/* Tab 切换 */}
      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => {
          const on = tab === t.key;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all tap"
              style={{
                color: on ? COLOR.goldBright : COLOR.muted,
                background: on ? "rgba(201,162,75,0.10)" : "transparent",
                border: `1px solid ${on ? COLOR.gold : COLOR.lineSoft}`,
              }}
            >
              {t.icon} {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab 内容 */}
      <Reveal key={tab}>
        {tab === "wuxing" && <WuxingTab />}
        {tab === "shensha" && <ShenshaTab />}
        {tab === "classical" && <ClassicalTab />}
        {tab === "profession" && <ProfessionTab />}
        {tab === "wellness" && <WellnessTab />}
      </Reveal>
    </div>
  );
}

// ── 五行Tab ────────────────────────────────────────────────────────
function WuxingTab() {
  const [selected, setSelected] = useState("木");
  const detail = WUXING_DETAIL[selected];

  return (
    <div className="space-y-5">
      {/* 五行环 */}
      <div className="card card-highlight flex flex-col sm:flex-row items-center gap-6">
        <div className="shrink-0">
          <WuXingRing size={180} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-display mb-3" style={{ color: COLOR.goldBright }}>五行相生相克</h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {WUXING_KEYS.map((wx) => {
              const on = selected === wx;
              return (
                <button key={wx} type="button" onClick={() => setSelected(wx)}
                  className="p-3 rounded-lg border text-center tap transition-all"
                  style={{
                    borderColor: on ? WUXING_COLORS[wx] : COLOR.line,
                    background: on ? `${WUXING_COLORS[wx]}15` : "rgba(255,255,255,0.02)",
                    boxShadow: on ? `0 0 12px ${WUXING_COLORS[wx]}30` : "none",
                  }}
                >
                  <div className="text-2xl">{WUXING_GLYPHS[wx]}</div>
                  <div className="text-sm font-semibold mt-1" style={{ color: on ? WUXING_COLORS[wx] : COLOR.inkSoft }}>
                    {wx}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 五行详情 */}
      {detail && (
        <div className="card card-highlight">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">{WUXING_GLYPHS[selected]}</span>
            <div>
              <h3 className="text-xl font-display" style={{ color: WUXING_COLORS[selected] }}>{detail.name}</h3>
              <p className="text-xs" style={{ color: COLOR.muted }}>{detail.traits.join(" · ")}</p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
            <DetailBlock label="方位" value={detail.direction} />
            <DetailBlock label="季节" value={detail.season} />
            <DetailBlock label="脏腑" value={detail.organ} />
            <DetailBlock label="五味" value={detail.taste} />
            <DetailBlock label="情志" value={detail.emotion} />
            <DetailBlock label="五德" value={detail.virtue} />
            <DetailBlock label="行星" value={detail.planet} />
            <DetailBlock label="神兽" value={detail.animal} />
          </div>
          <div className="grid sm:grid-cols-3 gap-2 mt-4 text-xs">
            <div className="p-2 rounded" style={{ background:"rgba(79,179,160,0.08)", border:"1px solid rgba(79,179,160,0.20)", color:COLOR.jade }}>
              {detail.generate}
            </div>
            <div className="p-2 rounded" style={{ background:"rgba(200,85,61,0.08)", border:"1px solid rgba(200,85,61,0.20)", color:COLOR.danger }}>
              {detail.control}
            </div>
            <div className="p-2 rounded" style={{ background:"rgba(91,141,239,0.08)", border:"1px solid rgba(91,141,239,0.20)", color:COLOR.azure }}>
              受制: {detail.controlledBy}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailBlock({ label, value }: { label:string; value:string }) {
  return (
    <div className="p-2 rounded" style={{ background:"rgba(8,10,15,0.3)", border:"1px solid var(--line-soft)" }}>
      <div className="text-[10px] uppercase tracking-widest" style={{ color:COLOR.muted }}>{label}</div>
      <div className="text-sm font-semibold mt-0.5" style={{ color:COLOR.ink }}>{value}</div>
    </div>
  );
}

// ── 神煞Tab ─────────────────────────────────────────────────────────
function ShenshaTab() {
  const categories = useMemo(() => {
    const cats = new Map<string, typeof SHENSHA_LIST>();
    for (const s of SHENSHA_LIST) {
      if (!cats.has(s.category)) cats.set(s.category, []);
      cats.get(s.category)!.push(s);
    }
    return Array.from(cats.entries());
  }, []);

  return (
    <div className="space-y-4">
      {categories.map(([cat, items]) => (
        <div key={cat} className="card card-highlight">
          <h3 className="text-sm mb-3" style={{ color: COLOR.goldBright }}>
            {cat === "贵人" ? "🌟" : cat === "姻缘" ? "💞" : cat === "事业" ? "🏆" : cat === "才华" ? "🎨" : cat === "学业" ? "📚" : cat === "福气" ? "🍀" : cat === "变动" ? "🏃" : "⚠️"} {cat}
          </h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {items.map((s) => (
              <div key={s.name} className="p-3 rounded-lg" style={{
                background: cat === "凶煞" ? "rgba(200,85,61,0.05)" : "rgba(22,27,34,0.5)",
                border: `1px solid ${cat === "凶煞" ? "rgba(200,85,61,0.20)" : "var(--line-soft)"}`,
              }}>
                <div className="text-sm font-semibold mb-1" style={{
                  color: cat === "凶煞" ? COLOR.danger : COLOR.ink,
                }}>{s.name}</div>
                <p className="text-xs leading-snug mb-1.5" style={{ color: COLOR.inkSoft }}>{s.desc}</p>
                <div className="text-[10px]" style={{ color: COLOR.muted }}>
                  <span style={{ color: COLOR.goldDim }}>查法:</span> {s.condition}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── 经典文摘Tab ─────────────────────────────────────────────────────
function ClassicalTab() {
  return (
    <div className="card card-highlight">
      <div className="flex items-center gap-3 mb-4">
        <YinYang size={36} />
        <div>
          <h3 className="text-lg font-display" style={{ color: COLOR.goldBright }}>古典文献精粹</h3>
          <p className="text-xs" style={{ color: COLOR.muted }}>选自《渊海子平》《三命通会》《滴天髓》等经典，经现代解读重新阐释。</p>
        </div>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">
        {CLASSICAL_CITATIONS.map((item, i) => (
          <div key={i} className="p-3 rounded-lg border relative overflow-hidden"
            style={{ borderColor: COLOR.lineSoft, background: "rgba(22,27,34,0.3)" }}>
            <div className="absolute top-0 left-0 w-1 h-full"
              style={{ background: item.category === "命理" ? COLOR.jade :
                               item.category === "格局" ? COLOR.gold :
                               item.category === "财运" ? COLOR.goldBright :
                               item.category === "五行" ? COLOR.azure :
                               item.category === "姻缘" ? "rgba(235,135,165,0.6)" :
                               COLOR.azure }} />
            <div className="text-xs leading-relaxed pl-3" style={{ color: COLOR.inkSoft }}>
              "{item.text}"
            </div>
            <div className="text-[10px] mt-2 pl-3" style={{ color: COLOR.goldDim }}>
              {item.source}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 职业适配Tab ─────────────────────────────────────────────────────
function ProfessionTab() {
  return (
    <div className="space-y-4">
      {PROFESSION_ELEMENTS.map((pe) => (
        <div key={pe.element} className="card card-highlight"
          style={{ borderLeft: `3px solid ${WUXING_COLORS[pe.element] || COLOR.gold}` }}>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">{WUXING_GLYPHS[pe.element]}</span>
            <div>
              <h3 className="text-lg font-display" style={{ color: WUXING_COLORS[pe.element] }}>五行属{pe.element}</h3>
              <p className="text-xs" style={{ color: COLOR.muted }}>{pe.reason}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {pe.professions.map((p) => (
              <span key={p} className="text-xs px-2.5 py-1 rounded-full"
                style={{
                  background: `${WUXING_COLORS[pe.element]}12`,
                  border: `1px solid ${WUXING_COLORS[pe.element]}30`,
                  color: WUXING_COLORS[pe.element],
                }}
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      ))}
      <div className="text-[10px] mt-2" style={{ color: COLOR.muted, opacity: 0.6 }}>
        以上职业分类基于五行属性象征推导，不代表科学职业测评。职业选择请结合个人实际。
      </div>
    </div>
  );
}

// ── 节气养生Tab ─────────────────────────────────────────────────────
function WellnessTab() {
  return (
    <div className="card card-highlight">
      <h3 className="text-lg font-display mb-4" style={{ color: COLOR.jade }}>🌿 四时养生要略</h3>
      <p className="text-xs mb-4 leading-relaxed" style={{ color: COLOR.inkSoft }}>
        《黄帝内经·四气调神大论》:"夫四时阴阳者，万物之根本也。所以圣人春夏养阳，秋冬养阴。"
        以下为四季养生要义，结合五行与脏腑对应。
      </p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {JIEQI_HEALTH.map((jq) => (
          <div key={jq.jieqi} className="p-4 rounded-lg border text-center"
            style={{
              borderColor: `${WUXING_COLORS[jq.element]}30`,
              background: `${WUXING_COLORS[jq.element]}08`,
            }}>
            <div className="text-2xl mb-1">{WUXING_GLYPHS[jq.element]}</div>
            <div className="text-sm font-semibold mb-2" style={{ color: WUXING_COLORS[jq.element] }}>
              {jq.jieqi} · 属{jq.element}
            </div>
            <p className="text-xs leading-snug" style={{ color: COLOR.inkSoft }}>{jq.tips}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 rounded-lg text-xs leading-relaxed"
        style={{ background: "rgba(8,10,15,0.4)", border: "1px solid var(--line-soft)", color: COLOR.inkSoft }}>
        <strong style={{ color: COLOR.goldBright }}>四季食疗原则：</strong>
        春省酸增甘以养脾气（木旺克土），夏省苦增辛以养肺气（火旺克金），
        秋省辛增酸以养肝气（金旺克木），冬省咸增苦以养心气（水旺克火）。
        此五行相制之理，源自《千金要方》。
      </div>
    </div>
  );
}
