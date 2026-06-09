// 关于页:定位 + 免责 + LLM 设置
import { COLOR } from "../components/ui";
import { Settings } from "../components/Settings";
import { FlowerOfLife, MetatronCube } from "../components/MysticElements";

export function About() {
  return (
    <div className="space-y-6 max-w-3xl relative">
      {/* 神圣几何背景装饰 */}
      <div className="fixed right-0 top-1/4 pointer-events-none opacity-[0.04] z-0" aria-hidden>
        <FlowerOfLife size={240} />
      </div>
      <div className="fixed right-12 bottom-8 pointer-events-none opacity-[0.03] z-0" aria-hidden>
        <MetatronCube size={200} />
      </div>

      <section className="card card-highlight relative overflow-hidden">
        {/* Decorative top glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-px pointer-events-none"
          style={{ background: `linear-gradient(90deg, transparent, ${COLOR.gold}60, transparent)` }} />
        <h2 className="text-2xl mb-3" style={{ color: COLOR.goldBright }}>关于 Mystic Hub</h2>
        <p className="text-sm leading-relaxed" style={{ color: COLOR.inkSoft }}>
          Mystic Hub 是一个面向研究 / 兴趣 / 自我反思的玄学工具。
          集成十四种术数(命 / 卜 / 风水 / 西方)，统一排盘接口 + 多 LLM 流式解读。
          全栈 MIT/BSD 许可，零 AGPL，可闭源商用。
        </p>
      </section>

      <section className="card card-highlight">
        <div className="flex items-center gap-2 mb-2">
          <span style={{ color: COLOR.goldDim, fontSize: "8px" }}>◆</span>
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>免责声明（全文）</h3>
        </div>
        <ul className="text-sm space-y-2 list-disc pl-5" style={{ color: COLOR.inkSoft }}>
          <li>本站所有排盘与解读，以传统文化象征视角呈现，<strong>非科学预测</strong>。</li>
          <li>不构成医疗诊断、法律意见、投资建议或任何专业判断。</li>
          <li>重大决定（健康 / 法律 / 财务 / 关系）请结合现实并咨询专业人士。</li>
          <li>危机话题（如自杀 / 自残）会被自动转介至心理援助热线，不进行盘面解读。</li>
          <li>不放大焦虑：解读措辞克制（用"倾向"避免"注定"），凶用"需留意"不用"大凶"。</li>
        </ul>
      </section>

      <section className="card card-highlight">
        <div className="flex items-center gap-2 mb-3">
          <span style={{ color: COLOR.goldDim, fontSize: "8px" }}>◆</span>
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>LLM 解读设置</h3>
        </div>
        <Settings />
      </section>

      <section className="card-raised card-highlight text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div className="flex items-center gap-2 mb-1">
          <span style={{ color: COLOR.jade }}>◆</span>
          <span style={{ color: COLOR.inkSoft, fontWeight: 600 }}>技术栈与合规</span>
        </div>
        <div>FastAPI · lunar-python · py-iztro · skyfield · React 18 + Vite + Tailwind · Zustand · marked</div>
        <div>13 个 engine / 中西合参 / 危机 block / 绝对化用语软化，详见源码。</div>
        <div>开源自托管：全部依赖 MIT/BSD，无 AGPL。</div>
      </section>
    </div>
  );
}
