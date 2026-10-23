/** ZiweiPalaceBrowser — 十二宫点选浏览器
 *
 *  盘面 SVG 是静态图, 而「点宫看详情」是市面紫微应用(iztro / 文墨天机)的标配交互。
 *  这里用文本芯片做宫位入口: 点某宫 → 右侧(窄屏下方)展开该宫主星/辅星/杂曜、
 *  长生十二神与四化标记, 数据全部来自 chart.raw.palaces, 不额外请求。
 */
import { useMemo, useState } from "react";

interface ZiweiPalace {
  name?: string;
  index?: number;
  heavenly_stem?: string;
  earthly_branch?: string;
  major_stars?: string[];
  minor_stars?: string[];
  adjective_stars?: string[];
  changsheng12?: string;
  boshi12?: string;
  jiangqian12?: string;
  suiqian12?: string;
  is_body_palace?: boolean;
  is_body?: boolean;
}

/** 四化顺序: 禄 / 权 / 科 / 忌 */
const SIHUA_NAMES = ["禄", "权", "科", "忌"] as const;
const SIHUA_COLORS = ["var(--verdigris)", "#9a6a1f", "#2f5d8a", "var(--cinnabar)"];

export function ZiweiPalaceBrowser({
  palaces,
  soul,
  body,
  fiveElements,
  fourTransformations,
  mingGong,
  isZh = true,
}: {
  palaces: ZiweiPalace[];
  soul?: string;
  body?: string;
  fiveElements?: string;
  fourTransformations?: Record<string, string[]>;
  mingGong?: string;
  isZh?: boolean;
}) {
  const [selected, setSelected] = useState<number>(() => {
    const idx = palaces.findIndex((p) => p.name === "命宫" || p.name === mingGong);
    return idx >= 0 ? idx : 0;
  });

  // 星曜 → 四化标记(以流年四化为准, 这是市面应用默认展示的那一组)
  const sihuaMap = useMemo(() => {
    const map = new Map<string, { label: string; color: string }>();
    const yearly = fourTransformations?.yearly || [];
    yearly.forEach((star, i) => {
      if (i < SIHUA_NAMES.length && star) {
        map.set(star, { label: SIHUA_NAMES[i], color: SIHUA_COLORS[i] });
      }
    });
    return map;
  }, [fourTransformations]);

  if (!palaces.length) return null;

  const cur = palaces[selected] || palaces[0];
  const Star = ({ name, tone }: { name: string; tone?: string }) => {
    const sihua = sihuaMap.get(name);
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.2rem",
          fontSize: "0.76rem",
          padding: "0.12rem 0.4rem",
          borderRadius: "3px",
          border: `1px solid ${tone || "var(--rule)"}`,
          color: tone || "var(--ink)",
          fontFamily: "'Noto Serif SC', serif",
        }}
      >
        {name}
        {sihua && (
          <span
            title={isZh ? `四化·${sihua.label}` : `Si Hua ${sihua.label}`}
            style={{ fontSize: "0.6rem", color: "#fff", background: sihua.color, borderRadius: "2px", padding: "0 0.18rem" }}
          >
            {sihua.label}
          </span>
        )}
      </span>
    );
  };

  return (
    <div style={{ borderTop: "1px dashed var(--rule)", paddingTop: "0.9rem" }}>
      <div className="flex items-center justify-between gap-2 flex-wrap" style={{ marginBottom: "0.6rem" }}>
        <h3 style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--ink)", fontFamily: "'Noto Serif SC', serif" }}>
          {isZh ? "点宫看详情" : "Palace detail"}
        </h3>
        <span style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>
          {fiveElements || ""}
          {soul ? ` · ${isZh ? "命主" : "Soul"} ${soul}` : ""}
          {body ? ` · ${isZh ? "身主" : "Body"} ${body}` : ""}
        </span>
      </div>

      {/* 宫位芯片 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(74px, 1fr))", gap: "0.35rem", marginBottom: "0.8rem" }}>
        {palaces.map((p, i) => {
          const active = i === selected;
          const isMing = p.name === "命宫" || p.name === mingGong;
          return (
            <button
              key={i}
              type="button"
              onClick={() => setSelected(i)}
              aria-pressed={active}
              style={{
                minHeight: 44,
                padding: "0.3rem 0.2rem",
                borderRadius: "3px",
                cursor: "pointer",
                background: active ? "rgba(176,58,46,0.08)" : "var(--paper-2)",
                border: `1px solid ${active ? "var(--cinnabar)" : isMing ? "#c9a227" : "var(--rule)"}`,
              }}
            >
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: active ? "var(--cinnabar)" : "var(--ink)" }}>
                {p.name}
                {p.is_body_palace || p.is_body ? <span style={{ color: "var(--verdigris)", fontSize: "0.6rem" }}> ·身</span> : null}
              </div>
              <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>
                {p.heavenly_stem || ""}{p.earthly_branch || ""}
              </div>
            </button>
          );
        })}
      </div>

      {/* 选中宫详情 */}
      <div className="p-3 rounded-sm" style={{ border: "1px solid var(--rule)", background: "var(--paper-2)" }}>
        <div className="flex items-baseline justify-between gap-2 flex-wrap" style={{ marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "0.86rem", fontWeight: 600, color: "var(--cinnabar)", fontFamily: "'Noto Serif SC', serif" }}>
            {cur.name}{cur.heavenly_stem || ""}{cur.earthly_branch || ""}
          </span>
          <span style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
            {isZh ? "第" : "No."}{selected + 1}{isZh ? "宫" : ""}
            {cur.is_body_palace || cur.is_body ? (isZh ? " · 身宫" : " · Body") : ""}
          </span>
        </div>

        {[
          { label: isZh ? "主星" : "Major", stars: cur.major_stars || [], tone: "var(--cinnabar)" },
          { label: isZh ? "辅星" : "Minor", stars: cur.minor_stars || [] },
          { label: isZh ? "杂曜" : "Others", stars: cur.adjective_stars || [] },
        ].map((row) => (
          <div key={row.label} className="flex items-start gap-2" style={{ marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.66rem", color: "var(--ink-soft)", minWidth: 34, flexShrink: 0, paddingTop: "0.15rem" }}>
              {row.label}
            </span>
            <div className="flex gap-1 flex-wrap">
              {row.stars.length ? (
                row.stars.map((s) => <Star key={s} name={s} tone={row.tone} />)
              ) : (
                <span style={{ fontSize: "0.68rem", color: "var(--ink-soft)", paddingTop: "0.15rem" }}>—</span>
              )}
            </div>
          </div>
        ))}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(96px, 1fr))", gap: "0.3rem", marginTop: "0.6rem", borderTop: "1px dashed var(--rule)", paddingTop: "0.5rem" }}>
          {[
            { k: isZh ? "长生" : "Stage", v: cur.changsheng12 },
            { k: isZh ? "博士" : "Boshi", v: cur.boshi12 },
            { k: isZh ? "将前" : "Jiangqian", v: cur.jiangqian12 },
            { k: isZh ? "岁前" : "Suiqian", v: cur.suiqian12 },
          ]
            .filter((x) => x.v)
            .map((x) => (
              <div key={x.k} style={{ fontSize: "0.68rem", color: "var(--ink)" }}>
                <span style={{ color: "var(--ink-soft)" }}>{x.k}: </span>
                {x.v}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
