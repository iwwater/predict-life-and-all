// 404:「古籍×仪器」风格
import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      {/* 404 编号 */}
      <div style={{
        fontFamily: "'Cinzel', serif",
        fontSize: "6rem",
        color: "var(--rule)",
        lineHeight: 1,
        letterSpacing: "0.08em",
        userSelect: "none",
      }}>
        404
      </div>

      {/* 释义 */}
      <div className="flex items-center justify-center gap-2 flex-wrap" style={{ marginTop: "0.5rem" }}>
        <span className="paper-tag paper-tag-east" style={{ fontSize: "0.68rem" }}>无明</span>
        <span className="paper-tag paper-tag-west" style={{ fontSize: "0.68rem" }}>Void</span>
      </div>

      <h1 style={{
        fontFamily: "'Noto Serif SC', serif",
        fontWeight: 700,
        fontSize: "1.5rem",
        color: "var(--ink)",
        marginTop: "1.25rem",
        letterSpacing: "0.08em",
      }}>
        此页不在命盘之中
      </h1>

      <p style={{
        fontSize: "0.88rem",
        color: "var(--ink-soft)",
        maxWidth: "28rem",
        margin: "0.75rem auto 0",
        lineHeight: 1.8,
        fontFamily: "'Noto Serif SC', serif",
      }}>
        你所寻之境不在八卦之内，亦不落黄道十二宫。<br />
        或许是星象偏移，或许是卦爻未成——请折返，另寻他途。
      </p>

      {/* 返回链接 */}
      <div className="flex items-center justify-center gap-3" style={{ marginTop: "1.5rem" }}>
        <Link to="/" className="paper-btn">
          返回首页
        </Link>
        <Link to="/cast" className="paper-btn-ghost">
          排盘问事
        </Link>
      </div>

      {/* 卦辞引用 */}
      <div style={{
        fontSize: "0.72rem",
        color: "var(--rule)",
        marginTop: "2rem",
        fontFamily: "'Noto Serif SC', serif",
        letterSpacing: "0.05em",
      }}>
        「眇能视，跛能履，履虎尾，咥人，凶」——《易·履卦》
      </div>
    </div>
  );
}
