// Jargon: 渲染"专业术语 + 大白话"（「古籍×仪器」纸墨风格）
import { useState, type ReactNode } from "react";
import { gloss } from "../lib/glossary";

interface JargonProps {
  term: string;
  suffix?: ReactNode;
  className?: string;
  style?: React.CSSProperties;
  mode?: "inline" | "block" | "plain";
  override?: { plain: string; hint?: string };
  tooltip?: boolean;
}

export function Jargon({ term, suffix, className, style, mode = "inline", override, tooltip = true }: JargonProps) {
  const [showTip, setShowTip] = useState(false);
  const g = override || gloss(term);
  const plain = g?.plain;
  const hint = g?.hint;

  const baseStyle: React.CSSProperties = {
    cursor: tooltip && hint ? "help" : "default",
    borderBottom: tooltip && hint ? "1px dotted var(--cinnabar)" : "none",
    textDecoration: "none",
    ...style,
  };

  if (mode === "plain" && plain) {
    return (
      <span className={className} style={style}>
        <span style={baseStyle}
          onMouseEnter={() => setShowTip(true)} onMouseLeave={() => setShowTip(false)}
          onFocus={() => setShowTip(true)} onBlur={() => setShowTip(false)}
          tabIndex={tooltip && hint ? 0 : -1}>
          {plain}
          {tooltip && hint && showTip && <Tip text={hint} />}
        </span>
        {suffix}
      </span>
    );
  }

  if (mode === "block") {
    return (
      <span className={className} style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-start", gap: 2, ...style }}>
        <span style={{ ...style, ...baseStyle }}
          onMouseEnter={() => setShowTip(true)} onMouseLeave={() => setShowTip(false)}
          tabIndex={tooltip && hint ? 0 : -1}>
          {term}
          {tooltip && hint && showTip && <Tip text={hint} />}
        </span>
        {plain && <span style={{ fontSize: "0.62rem", fontWeight: 400, color: "var(--ink-soft)" }}>{plain}</span>}
        {suffix}
      </span>
    );
  }

  return (
    <span className={className} style={style}>
      <span style={baseStyle}
        onMouseEnter={() => setShowTip(true)} onMouseLeave={() => setShowTip(false)}
        tabIndex={tooltip && hint ? 0 : -1}>{term}</span>
      {plain && (
        <span style={{ marginLeft: "0.35rem", fontWeight: 400, color: "var(--ink-soft)", fontSize: "0.85em" }}>· {plain}</span>
      )}
      {tooltip && hint && showTip && <Tip text={hint} />}
      {suffix}
    </span>
  );
}

function Tip({ text }: { text: string }) {
  return (
    <span role="tooltip" className="absolute z-50 px-2 py-1.5 rounded text-xs font-normal" style={{
      left: 0, top: "calc(100% + 6px)", minWidth: 180, maxWidth: 280,
      background: "var(--paper)", color: "var(--ink)",
      border: "1px solid var(--rule)",
      whiteSpace: "normal", lineHeight: 1.5, pointerEvents: "none",
      fontFamily: "'Noto Serif SC', serif",
    }}>{text}</span>
  );
}

interface JargonBoxProps {
  title: string;
  items: Array<{ term: string; plain: string; hint?: string }>;
}

export function JargonBox({ title, items }: JargonBoxProps) {
  return (
    <div className="paper-grid-cell" style={{ padding: "0.5rem 0.75rem", fontSize: "0.75rem" }}>
      <div style={{ fontWeight: 600, color: "var(--cinnabar)", marginBottom: "0.3rem", fontFamily: "'Noto Serif SC', serif" }}>{title}</div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {items.map((it) => (
          <span key={it.term}>
            <span style={{ color: "var(--ink-soft)" }}>{it.term}</span>
            <span style={{ margin: "0 0.25rem" }}>·</span>
            <span style={{ color: "var(--ink)" }}>{it.plain}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
