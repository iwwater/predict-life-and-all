// 关于页:「古籍×仪器」纸墨风格
import { Settings } from "../components/Settings";

export function About() {
  return (
    <div className="space-y-6 max-w-3xl">
      <section className="paper-frame">
        <h2 className="paper-title"><span className="stamp" />关于 Mystic Hub</h2>
        <div className="paper-body" style={{ marginTop: "0.75rem" }}>
          <p>
            Mystic Hub 是一个面向研究 / 兴趣 / 自我反思的玄学工具。
            集成十四种术数(命 / 卜 / 风水 / 西方)，统一排盘接口 + 多 LLM 流式解读。
            全栈 MIT/BSD 许可，零 AGPL，可闭源商用。
          </p>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section"><span className="num">壹</span>免责声明</h3>
        <ul style={{ fontSize: "0.85rem", color: "var(--ink-soft)", lineHeight: 1.9, paddingLeft: "1.2rem", listStyle: "disc", fontFamily: "'Noto Serif SC', serif" }}>
          <li>本站所有排盘与解读，以传统文化象征视角呈现，<strong style={{ color: "var(--ink)" }}>非科学预测</strong>。</li>
          <li>不构成医疗诊断、法律意见、投资建议或任何专业判断。</li>
          <li>重大决定（健康 / 法律 / 财务 / 关系）请结合现实并咨询专业人士。</li>
          <li>危机话题（如自杀 / 自残）会被自动转介至心理援助热线，不进行盘面解读。</li>
          <li>不放大焦虑：解读措辞克制（用"倾向"避免"注定"），凶用"需留意"不用"大凶"。</li>
        </ul>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section"><span className="num">贰</span>LLM 解读设置</h3>
        <Settings />
      </section>

      <section className="paper-fanli">
        <div className="paper-fanli-title">技术栈与合规</div>
        <p>FastAPI · lunar-python · py-iztro · skyfield · React 18 + Vite + Tailwind · Zustand · marked</p>
        <p style={{ marginTop: "0.3rem" }}>13 个 engine / 中西合参 / 危机 block / 绝对化用语软化，详见源码。</p>
        <p style={{ marginTop: "0.3rem" }}>开源自托管：全部依赖 MIT/BSD，无 AGPL。</p>
      </section>
    </div>
  );
}
