// 「古籍×仪器」公共组件与设计令牌
// 颜色全部取自 CSS 变量,与 index.css 同步

export const COLOR = {
  // ── 纸墨 token（主） ──
  paper:     "#F4EFE6",
  paper2:    "#EDE6D8",
  ink:       "#2B2620",
  inkSoft:   "#6B6256",
  cinnabar:  "#B03A2E",
  cinnabarDim: "#8E2E25",
  indigo:    "#2F4858",
  verdigris: "#5A7058",
  rule:      "#C9BFA9",
  ruleSoft:  "rgba(201, 191, 169, 0.55)",
  darkBg:    "#1C1915",
  // ── 向后兼容别名（旧代码中的 COLOR.xxx 引用） ──
  gold:       "#B03A2E",
  goldBright: "#B03A2E",
  goldDim:    "#8E2E25",
  jade:       "#5A7058",
  jadeDim:    "rgba(90, 112, 88, 0.5)",
  azure:      "#2F4858",
  azureDim:   "rgba(47, 72, 88, 0.5)",
  danger:     "#B03A2E",
  ok:         "#5A7058",
  muted:      "#6B6256",
  line:       "#C9BFA9",
  lineSoft:   "rgba(201, 191, 169, 0.55)",
  bgDeep:     "#F4EFE6",
  surface:    "#EDE6D8",
} as const;

/* ── 徽标(法系/分组) ── */

export function SchoolChip({ school }: { school: "east" | "west" }) {
  return school === "east"
    ? <span className="paper-tag paper-tag-east">东方</span>
    : <span className="paper-tag paper-tag-west">西方</span>;
}

export function GroupChip({ group }: { group: string }) {
  return <span className="paper-tag">{group}</span>;
}

/* ── 统计数值 ── */

export function Stat({ label, value, tone }: {
  label: string; value: string;
  tone?: "cinnabar" | "verdigris" | "indigo" | "ink" | "gold" | "jade" | "azure" | "danger";
}) {
  const color = tone === "verdigris" ? "var(--verdigris)"
    : tone === "indigo" ? "var(--indigo)"
    : tone === "ink" ? "var(--ink)"
    : tone === "gold" ? "var(--cinnabar)"
    : tone === "jade" ? "var(--verdigris)"
    : tone === "azure" ? "var(--indigo)"
    : tone === "danger" ? "var(--cinnabar)"
    : "var(--cinnabar)";
  return (
    <div className="flex flex-col">
      <span className="paper-mono" style={{ fontSize: "0.65rem", color: "var(--ink-soft)", letterSpacing: "0.15em" }}>
        {label}
      </span>
      <span className="mt-0.5" style={{ fontSize: "0.9rem", fontWeight: 700, color, fontFamily: "'JetBrains Mono', monospace" }}>
        {value}
      </span>
    </div>
  );
}

/* ── 反馈组件 ── */

export function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="paper-error">
      {children}
    </div>
  );
}

export function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="paper-empty">
      {children}
    </div>
  );
}

export function SkeletonBlock({ height = 120 }: { height?: number }) {
  return (
    <div
      className="paper-empty"
      style={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}
    >
      <span className="paper-pulse" />
    </div>
  );
}

/* ── 「古籍×仪器」专用组件 ── */

/** 朱砂小印(标题前缀用) */
export function Stamp({ size = "0.85rem" }: { size?: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: size,
        height: size,
        background: "var(--cinnabar)",
        flexShrink: 0,
        alignSelf: "center",
        borderRadius: 1,
        boxShadow: "inset 0 0 0 1px rgba(176,58,46,0.4)",
      }}
    />
  );
}

/** 朱砂大印(角落/标识用) */
export function Seal({ char, size = "2.6rem" }: { char: string; size?: string }) {
  return (
    <span
      className="paper-seal"
      style={{ width: size, height: size, lineHeight: size, fontSize: `calc(${size} * 0.38)` }}
    >
      {char}
    </span>
  );
}

/** 版框容器 */
export function PaperFrame({ children, className = "", style }: {
  children: React.ReactNode; className?: string; style?: React.CSSProperties;
}) {
  return (
    <div className={`paper-frame ${className}`} style={style}>
      {children}
    </div>
  );
}

/** 页面标题(左侧朱砂印 + 宋体标题 + 下划单线) */
export function PaperTitle({ title, subtitle, stamp }: {
  title: string; subtitle?: string; stamp?: boolean;
}) {
  return (
    <h1 className="paper-title">
      {stamp !== false && <span className="stamp" />}
      <span>{title}</span>
      {subtitle && <span className="sub">{subtitle}</span>}
    </h1>
  );
}

/** 编目区段标题 */
export function PaperSection({ num, children }: {
  num?: string; children: React.ReactNode;
}) {
  return (
    <div className="paper-section">
      {num && <span className="num">{num}</span>}
      <span>{children}</span>
    </div>
  );
}
