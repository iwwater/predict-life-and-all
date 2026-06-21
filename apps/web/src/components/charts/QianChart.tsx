import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";

export function QianChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw || {};
  const quality = r.source_quality === "curated" ? "精校条目" : "基础条目";
  const qualityColor = r.source_quality === "curated" ? COLOR.jade : COLOR.muted;

  return (
    <div className="space-y-4">
      <div className="paper-frame">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            {r.签谱名称 || "灵签"} · 第{r.签号}签
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className="paper-tag paper-tag-west">{r.签等}</span>
            <span className="paper-tag" style={{ color: qualityColor }}>{quality}</span>
          </div>
        </div>
        <div className="mt-3" style={{ color: COLOR.ink, fontFamily: "'Noto Serif SC', serif", fontSize: "1rem", fontWeight: 700 }}>
          {r.签名}
        </div>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: COLOR.inkSoft }}>
          {r.签文}
        </p>
      </div>

      <div className="card-raised">
        <div className="text-xs mb-2" style={{ color: COLOR.muted }}>解签</div>
        <p className="text-sm leading-relaxed" style={{ color: COLOR.ink }}>{r.解签}</p>
        {r.行动建议 && (
          <p className="text-xs leading-relaxed mt-3" style={{ color: COLOR.muted }}>
            行动建议：{r.行动建议}
          </p>
        )}
        <div className="mt-3 text-[10px] leading-relaxed" style={{ color: COLOR.muted }}>
          起法：{r.draw_mode === "manual" ? "签号录入" : "随机抽签"}；seed: {String(r.seed_used ?? "随机")}
        </div>
      </div>
    </div>
  );
}
