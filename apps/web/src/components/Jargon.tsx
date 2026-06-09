// Jargon: 渲染"专业术语 + 大白话" 同一行
//  - 默认显示:  <术语>·<大白话>   (如: 日主·你的主心骨)
//  - hover 时:   出 tooltip,显示 hint
//  - 没查到 GLOSS: 退化为原样术语(不报错)
//
// 设计原则沿用 Cast.tsx 那个哲学:
//   "不是折叠进阶选项,是你通过用户的选择把专业术语翻成大白话"
//
// 这里用户已经看到结果,术语必须出现(没法隐藏),
// 所以:用大白话贴身翻译,而不是折叠

import { useState, type ReactNode } from "react";
import { gloss } from "../lib/glossary";

interface JargonProps {
  term: string;          // 展示的术语(会先去 GLOSS 查;查不到原文)
  suffix?: ReactNode;    // 术语后追加的内容(如" 日主 丙火" 的 " 丙火")
  className?: string;    // 父级样式
  style?: React.CSSProperties;
  // "inline"  (默认): 术语 + 大白话,一行
  // "block":             术语 / 大白话 两行
  // "plain":             只显示大白话(术语在 tooltip 里)
  mode?: "inline" | "block" | "plain";
  // 强制用这个解释(跳过 GLOSS 查表,直接用)
  override?: { plain: string; hint?: string };
  // 是否画 tooltip (默认 true)
  tooltip?: boolean;
}

export function Jargon({ term, suffix, className, style, mode = "inline", override, tooltip = true }: JargonProps) {
  const [showTip, setShowTip] = useState(false);
  const g = override || gloss(term);
  const plain = g?.plain;
  const hint = g?.hint;

  const baseStyle: React.CSSProperties = {
    cursor: tooltip && hint ? "help" : "default",
    borderBottom: tooltip && hint ? "1px dotted currentColor" : "none",
    textDecoration: "none",
    ...style,
  };

  // 模式: plain 只显示大白话(术语进 tooltip),适合列表里太挤
  if (mode === "plain" && plain) {
    return (
      <span className={className} style={style}>
        <span
          style={{ ...baseStyle, color: "var(--muted)" }}
          onMouseEnter={() => setShowTip(true)}
          onMouseLeave={() => setShowTip(false)}
          onFocus={() => setShowTip(true)}
          onBlur={() => setShowTip(false)}
          tabIndex={tooltip && hint ? 0 : -1}
        >
          {plain}
          {tooltip && hint && showTip && <Tip text={hint} />}
        </span>
        {suffix}
      </span>
    );
  }

  // 模式: block 上下两行(适合卡片标题)
  if (mode === "block") {
    return (
      <span className={className} style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-start", gap: 2, ...style }}>
        <span style={{ ...style, ...baseStyle }}
          onMouseEnter={() => setShowTip(true)}
          onMouseLeave={() => setShowTip(false)}
          tabIndex={tooltip && hint ? 0 : -1}>
          {term}
          {tooltip && hint && showTip && <Tip text={hint} />}
        </span>
        {plain && <span className="text-[10px] font-normal" style={{ color: "var(--muted)" }}>{plain}</span>}
        {suffix}
      </span>
    );
  }

  // 模式: inline 一行  "术语·大白话"
  return (
    <span className={className} style={style}>
      <span
        style={baseStyle}
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
        tabIndex={tooltip && hint ? 0 : -1}
      >
        {term}
      </span>
      {plain && (
        <span className="ml-1.5 font-normal" style={{ color: "var(--muted)", fontSize: "0.85em" }}>
          · {plain}
        </span>
      )}
      {tooltip && hint && showTip && <Tip text={hint} />}
      {suffix}
    </span>
  );
}

function Tip({ text }: { text: string }) {
  return (
    <span
      role="tooltip"
      className="absolute z-50 px-2 py-1.5 rounded text-xs font-normal normal-case tracking-normal"
      style={{
        left: 0,
        top: "calc(100% + 6px)",
        minWidth: 180,
        maxWidth: 280,
        background: "rgba(8,10,15,0.96)",
        color: "var(--ink)",
        border: "1px solid rgba(201,162,75,0.35)",
        boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
        whiteSpace: "normal",
        lineHeight: 1.5,
        pointerEvents: "none",
      }}
    >
      {text}
    </span>
  );
}

// 另一种用法: JargonBox 整块卡片,适合放在一个 chart 的顶部,
// 一次性给一组术语做"白话解释面板"
interface JargonBoxProps {
  title: string;
  items: Array<{ term: string; plain: string; hint?: string }>;
}
export function JargonBox({ title, items }: JargonBoxProps) {
  return (
    <div
      className="rounded-md p-2.5 text-xs leading-relaxed"
      style={{
        background: "rgba(201,162,75,0.06)",
        border: "1px dashed rgba(201,162,75,0.3)",
      }}
    >
      <div className="mb-1 font-semibold" style={{ color: "var(--gold-bright)" }}>{title}</div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {items.map((it) => (
          <span key={it.term}>
            <span style={{ color: "var(--muted)" }}>{it.term}</span>
            <span className="mx-1">·</span>
            <span style={{ color: "var(--ink-soft)" }}>{it.plain}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
