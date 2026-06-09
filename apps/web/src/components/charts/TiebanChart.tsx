// 铁板神数: 四柱编码 → 条文集数 → 分类条文
import type { ChartResult } from "../../lib/types";
import { COLOR, Stat } from "../ui";

const ZODIAC_12 = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];

export function TiebanChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const pillars = r.four_pillars || {};
  const encoding = r.encoding || {};
  const stems = encoding.stems || {};
  const branches = encoding.branches || {};
  const verseResult = r.verse_result || {};
  const verses = verseResult.matched_verses || [];
  const keFen = r.ke_fen || {};
  const basis = r.calculation_basis || {};

  // Group verses by category
  const grouped: Record<string, typeof verses> = {};
  for (const v of verses) {
    const cat = v.category || "其他";
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(v);
  }

  const verification = verseResult.verification || {};

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            铁板神数 · 条文
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className="tag tag-east">五大神数</span>
            <span className="tag" style={{ background: "rgba(201,162,75,0.10)", color: COLOR.gold }}>
              集数 {r.verse_set_number}
            </span>
          </div>
        </div>

        {/* Key numbers */}
        <div className="flex gap-4 text-xs flex-wrap">
          <Stat label="基数" value={String(r.base_number || "—")} tone="gold" />
          <Stat label="刻分" value={`第${keFen.ke || "?"}刻${keFen.fen || "?"}分`} tone="azure" />
          <Stat label="条文集数" value={String(r.verse_set_number || "—")} tone="gold" />
        </div>
      </div>

      {/* Four Pillars & Encoding Table */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          四柱编码
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 天干数 + 地支太玄数
          </span>
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}>
                <th className="text-left py-2 pr-4" style={{ color: COLOR.muted }}></th>
                <th className="text-left py-2 pr-4" style={{ color: COLOR.muted }}>年柱</th>
                <th className="text-left py-2 pr-4" style={{ color: COLOR.muted }}>月柱</th>
                <th className="text-left py-2 pr-4" style={{ color: COLOR.muted }}>日柱</th>
                <th className="text-left py-2 pr-4" style={{ color: COLOR.muted }}>时柱</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}>
                <td className="py-1.5 pr-4" style={{ color: COLOR.muted }}>干支</td>
                {["year", "month", "day", "hour"].map((k) => (
                  <td key={k} className="py-1.5 pr-4" style={{ color: COLOR.ink }}>
                    {pillars[k] || "?"}
                  </td>
                ))}
              </tr>
              <tr style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}>
                <td className="py-1.5 pr-4" style={{ color: COLOR.muted }}>天干</td>
                {["year", "month", "day", "hour"].map((k) => {
                  const s = stems[k];
                  return (
                    <td key={k} className="py-1.5 pr-4" style={{ color: COLOR.gold }}>
                      {s?.gan || "?"} → {s?.num ?? "?"}
                    </td>
                  );
                })}
              </tr>
              <tr>
                <td className="py-1.5 pr-4" style={{ color: COLOR.muted }}>地支</td>
                {["year", "month", "day", "hour"].map((k) => {
                  const b = branches[k];
                  return (
                    <td key={k} className="py-1.5 pr-4" style={{ color: COLOR.azure }}>
                      {b?.zhi || "?"}({b?.type || "?"}) → {b?.num ?? "?"}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-[10px]" style={{ color: COLOR.muted }}>
          基数 = 年干×1000 + 月干×100 + 日干×10 + 时干 + Σ地支太玄数 = {r.base_number}
        </div>
      </div>

      {/* Verse Cards */}
      <div className="card">
        <h4 className="text-sm mb-3" style={{ color: COLOR.gold }}>
          匹配条文 ({verseResult.total_matched || 0} 条)
          <span className="text-[10px] ml-2 font-normal" style={{ color: COLOR.muted }}>
            — 范围: {verseResult.verse_set_range || "—"}
          </span>
        </h4>

        {Object.keys(grouped).length === 0 ? (
          <div className="text-sm" style={{ color: COLOR.muted }}>
            无匹配条文，请检查出生数据或尝试输入父母生肖进行校验。
          </div>
        ) : (
          <div className="space-y-3">
            {Object.entries(grouped).map(([category, catVerses]) => (
              <div key={category}>
                <div
                  className="text-xs font-semibold mb-2 px-2 py-0.5 inline-block rounded"
                  style={{ background: "rgba(201,162,75,0.10)", color: COLOR.gold }}
                >
                  {category}
                </div>
                <div className="space-y-2">
                  {catVerses.map((v: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 rounded-md text-sm leading-relaxed"
                      style={{
                        background: "rgba(8,10,15,0.4)",
                        borderLeft: `3px solid ${COLOR.goldDim}`,
                      }}
                    >
                      <div className="flex items-start gap-2">
                        <span
                          className="text-[10px] mt-0.5 px-1 rounded shrink-0"
                          style={{ background: "rgba(201,162,75,0.15)", color: COLOR.gold }}
                        >
                          {v.number}
                        </span>
                        <span style={{ color: COLOR.inkSoft }}>{v.text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Verification note */}
        {verification.note && (
          <div
            className="mt-4 p-2 rounded text-xs"
            style={{ background: "rgba(91,141,239,0.06)", border: `1px solid ${COLOR.lineSoft}` }}
          >
            <span style={{ color: COLOR.azure }}>校验: </span>
            <span style={{ color: COLOR.inkSoft }}>{verification.note}</span>
          </div>
        )}
      </div>

      {/* Calculation Basis */}
      <details className="text-[10px] space-y-1" style={{ color: COLOR.muted }}>
        <summary className="cursor-pointer" style={{ color: COLOR.goldBright }}>
          算法说明
        </summary>
        <p>输入: {basis.input_source || "—"}</p>
        <p>编码规则: {basis.encoding_rule || "—"}</p>
        {Array.isArray(basis.limits) && basis.limits.map((l: string, i: number) => (
          <p key={i} className="opacity-70">• {l}</p>
        ))}
      </details>
    </div>
  );
}
