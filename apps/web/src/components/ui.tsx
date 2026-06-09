// 公共 SVG / 视觉工具
// 颜色 token(与设计计划书 §7 对应;组件里直接用 var(--xxx))

export const COLOR = {
  bgDeep: "#080A0F",
  surface: "#161B22",
  ink: "#E6E1D3",
  inkSoft: "#C8C2B0",
  muted: "#8A8F98",
  gold: "#C9A24B",
  goldDim: "#8A6E32",
  goldBright: "#E5BC5E",
  jade: "#4FB3A0",
  jadeDim: "#36766A",
  azure: "#5B8DEF",
  azureDim: "#3A6BC2",
  danger: "#C8553D",
  ok: "#5AA469",
  line: "rgba(201, 162, 75, 0.25)",
  lineSoft: "rgba(201, 162, 75, 0.10)",
} as const;

export function SchoolChip({ school }: { school: "east" | "west" }) {
  return school === "east"
    ? <span className="tag tag-east">东方</span>
    : <span className="tag tag-west">西方</span>;
}

export function GroupChip({ group }: { group: string }) {
  return <span className="tag">{group}</span>;
}

export function Stat({ label, value, tone }: { label: string; value: string; tone?: "gold" | "jade" | "azure" | "ink" }) {
  const color = tone === "jade" ? "var(--jade)"
    : tone === "azure" ? "var(--azure)"
    : tone === "ink" ? "var(--ink)"
    : "var(--gold)";
  return (
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-widest" style={{ color: "var(--muted)" }}>{label}</span>
      <span className="text-sm font-semibold mt-0.5" style={{ color }}>{value}</span>
    </div>
  );
}

export function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-md p-3 text-sm border"
      style={{ background: "rgba(200, 85, 61, 0.08)", borderColor: "rgba(200, 85, 61, 0.35)", color: "var(--ink-soft)" }}
    >
      {children}
    </div>
  );
}

export function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-md p-6 text-center text-sm"
      style={{ background: "rgba(22, 27, 34, 0.4)", border: "1px dashed var(--line)", color: "var(--muted)" }}
    >
      {children}
    </div>
  );
}

export function SkeletonBlock({ height = 120 }: { height?: number }) {
  return (
    <div
      className="rounded-md skeleton-shimmer"
      style={{ height, border: "1px solid var(--line-soft)" }}
    />
  );
}
