// 单法说明页（「古籍×仪器」纸墨风格）
import { Link, useParams } from "react-router-dom";

const META: Record<string, { name: string; group: string; intro: string; refs: string[] }> = {
  bazi: { name: "八字四柱", group: "命", intro: "以年、月、日、时四柱干支为基础，推演命主五行喜忌与大运流年走势。", refs: ["《子平真诠》", "《滴天髓》", "《穷通宝鉴》"] },
  ziwei: { name: "紫微斗数", group: "命", intro: "以出生时辰定命宫，按十四主星入十二宫，推断格局与运势。", refs: ["《紫微斗数全书》", "《飞星紫微斗数》"] },
  qimen: { name: "奇门遁甲", group: "卜", intro: "时家奇门:以三元九局 + 九星/八门/八神/三奇六仪，断事之机与吉凶。", refs: ["《神奇之门》", "《开悟之门》"] },
  liuyao: { name: "六爻", group: "卜", intro: "摇卦得本卦与变卦，以世爻/应爻/用神/原神/忌神断事。", refs: ["《卜筮正宗》", "《火珠林》"] },
  meihua: { name: "梅花易数", group: "卜", intro: "起卦方式灵活(时辰/数字/声音)，主互变三卦体用五行生克决断。", refs: ["《梅花易数》(邵雍)"] },
  chenggu: { name: "称骨", group: "命", intro: "按生辰干支查骨重表，得总骨重档次，附固定批语。", refs: ["袁天罡称骨算命(公版口诀)"] },
  bazhai: { name: "八宅", group: "风水", intro: "按年命起卦分东四/西四命，定八方吉凶(生气/延年/天医/伏位/五鬼/六煞/祸害/绝命)。", refs: ["《八宅明镜》"] },
  xuankong: { name: "玄空飞星", group: "风水", intro: "按元运 + 山向，九宫飞布运/山/向三星，断旺山旺向/上山下水等格局。", refs: ["《沈氏玄空学》", "《地理辨正疏》"] },
  western: { name: "西方占星", group: "西方", intro: "黄道十二星座 + 行星落位 + 上升/天顶 + 宫位 + 相位。", refs: ["《占星学》相关著作"] },
  vedic: { name: "吠陀占星", group: "西方", intro: "印度恒星黄道系统(Jyotish)，Lahiri ayanamsa 偏移，27 Nakshatra。", refs: ["Brihat Parashara Hora Shastra"] },
  tarot: { name: "塔罗", group: "西方", intro: "78 张牌(22 大阿卡那 + 56 小阿卡那)，单/三/凯尔特十字牌阵。", refs: ["Waite / Thoth Tarot 体系"] },
  numerology: { name: "数字命理", group: "西方", intro: "毕达哥拉斯体系:生命灵数由生日逐位求和，化至 1-9 或主数 11/22/33。", refs: ["Pythagorean Numerology"] },
  lenormand: { name: "雷诺曼", group: "西方", intro: "36 张牌，无逆位，牌义高度依赖邻近牌的修饰(组合解读)，偏向日常具体占卜。", refs: ["Petit Lenormand (1799)", "法国/德国传统学派"] },
  liuren: { name: "大六壬", group: "卜", intro: "三式之首: 天地盘 + 四课三传 + 十二天将，以月将加时决断人事吉凶。", refs: ["《大六壬大全》", "《六壬断案》", "《六壬指南》"] },
  tieban: { name: "铁板神数", group: "命", intro: "中华五大神数之一: 生辰八字经天干太玄数编码得条文集数，查考约 12,000 条命理诗文。父母生肖校验定刻分。", refs: ["《铁板神数》(邵雍皇极经世体系)", "《皇极经世》"] },
};

export function MethodInfo() {
  const { id } = useParams();
  const m = (id || "").toLowerCase();
  const meta = META[m];

  if (!meta) {
    return (
      <div className="paper-empty" style={{ padding: "2rem 0" }}>
        <p>未知术数: <code className="paper-mono">{id}</code></p>
        <Link to="/" className="paper-btn-ghost" style={{ marginTop: "0.75rem", display: "inline-flex" }}>← 回首页</Link>
      </div>
    );
  }

  return (
    <article className="space-y-4 max-w-2xl">
      <header>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.65rem", color: "var(--cinnabar)", letterSpacing: "0.2em" }}>
          {meta.group}
        </div>
        <h1 className="paper-title" style={{ marginTop: "0.2rem" }}>
          <span className="stamp" />{meta.name}
        </h1>
      </header>

      <p style={{ fontSize: "0.88rem", color: "var(--ink-soft)", lineHeight: 1.8, fontFamily: "'Noto Serif SC', serif" }}>
        {meta.intro}
      </p>

      <section className="paper-frame">
        <h4 className="paper-eyebrow">文献依据</h4>
        <ul style={{ fontSize: "0.82rem", color: "var(--ink-soft)", lineHeight: 2, paddingLeft: "1.2rem", marginTop: "0.3rem", listStyle: "disc", fontFamily: "'Noto Serif SC', serif" }}>
          {meta.refs.map((r) => <li key={r}>{r}</li>)}
        </ul>
      </section>

      <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)", lineHeight: 1.7 }}>
        以上为文化与符号象征视角的参考，非科学预测。重大决定请结合现实并咨询专业人士。
      </div>

      <Link to={`/cast?methods=${m}`} className="paper-btn" style={{ display: "inline-flex" }}>用此法排盘 →</Link>
    </article>
  );
}
