// 隐私政策页 (P2-8 GDPR 最小合规)
// 简洁中文隐私政策, 说明数据收集与用户权利

export function PrivacyPolicy() {
  return (
    <div className="space-y-6 max-w-3xl">
      <section className="paper-frame">
        <h2 className="paper-title">
          <span className="stamp" />
          隐私政策
        </h2>
        <div className="paper-body" style={{ marginTop: "0.75rem" }}>
          <p>本隐私政策说明 Mystic Hub 如何收集、使用和保护您的信息。</p>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">一</span>我们收集的信息
        </h3>
        <div className="paper-body">
          <p>
            <strong>出生信息</strong>（出生年月日时、性别、经纬度）：仅用于排盘计算，
            不关联真实身份。出生时间精度降至时辰（2 小时），经纬度精度降至 0.1 度。
          </p>
          <p>
            <strong>占卜问题</strong>：您输入的咨询文本，仅用于本次解读会话。
          </p>
          <p>
            <strong>会话标识</strong>：匿名随机 ID，不含个人身份信息。
          </p>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">二</span>我们如何使用信息
        </h3>
        <div className="paper-body">
          <ul style={{ fontSize: "0.85rem", lineHeight: 1.9 }}>
            <li>出生信息仅用于排盘算法，不作身份识别</li>
            <li>占卜问题仅传递给 LLM 进行解读，不用于训练</li>
            <li>服务器不持久化出生数据到数据库</li>
            <li>不向第三方出售或分享任何用户数据</li>
          </ul>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">三</span>数据存储与保护
        </h3>
        <div className="paper-body">
          <p>
            出生数据仅在会话期间保留于内存，会话结束后清除。
            历史记录存储在您本地浏览器中。
            传输层使用 HTTPS 加密。
          </p>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">四</span>您的权利
        </h3>
        <div className="paper-body">
          <p>根据 GDPR，您享有以下权利：</p>
          <ul style={{ fontSize: "0.85rem", lineHeight: 1.9 }}>
            <li><strong>访问权</strong>（第 15 条）：查看我们保留的您的数据 — <code>GET /api/users/me/data</code></li>
            <li><strong>删除权</strong>（第 17 条）：请求删除您的数据 — <code>POST /api/users/me/delete</code></li>
            <li><strong>限制处理权</strong>（第 18 条）：限制我们对您数据的处理</li>
            <li><strong>数据可携权</strong>（第 20 条）：以结构化格式导出您的数据</li>
          </ul>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">五</span>免责声明
        </h3>
        <div className="paper-body">
          <p>
            本站所有排盘与解读以传统文化象征视角呈现，<strong>非科学预测</strong>。
            不构成医疗诊断、法律意见、投资建议或任何专业判断。
            重大决定请结合现实并咨询专业人士。
          </p>
        </div>
      </section>

      <section className="paper-frame">
        <h3 className="paper-section">
          <span className="num">六</span>联系我们
        </h3>
        <div className="paper-body">
          <p>
            如对隐私政策有疑问，请联系：
            <br />
            Email: privacy@mystichub.app
          </p>
          <p style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "1rem" }}>
            最后更新：2026-06-20
          </p>
        </div>
      </section>

      <section className="paper-fanli">
        <div className="paper-fanli-title">法律依据</div>
        <p>
          本隐私政策依据 EU General Data Protection Regulation (GDPR) 2016/679
          及《中华人民共和国个人信息保护法》制定。
        </p>
      </section>
    </div>
  );
}
