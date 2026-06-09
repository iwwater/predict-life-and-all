// 六爻:6 爻竖排(初→上),本卦 + 变卦并列
// 术语:本卦/变卦/动爻/卦辞/世爻/应爻/纳甲/六神/初爻/上爻
import type { ChartResult } from "../../lib/types";
import { COLOR } from "../ui";
import { Jargon, JargonBox } from "../Jargon";

export function LiuyaoChart({ chart }: { chart: ChartResult }) {
  const r = chart.raw;
  const lines: Array<{ pos: number; yang: boolean; gan_zhi: string }> = r.hex_lines || [];
  const dong: number[] = r.dong_yao || [];
  const benName = r.ben_gua || "?";
  const bianName = r.bian_gua;
  const shen = r.liu_shen || [];
  const shiYao = r.shi_yao;
  const yingYao = r.ying_yao;
  const ordered = [...lines].sort((a, b) => a.pos - b.pos);

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>六爻 · {benName}{bianName ? ` → ${bianName}` : ""}</h3>
          <div className="flex gap-2 text-xs flex-wrap">
            <span className="tag">
              <Jargon term="动爻" mode="plain" /> {dong.join(",") || "—"}
            </span>
            <span className="tag">{r.day_gz || ""} {r.hour_gz || ""}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:gap-8 max-w-lg mx-auto">
          <div className="space-y-1.5">
            <div className="text-xs text-center mb-1" style={{ color: COLOR.muted }}>
              <Jargon term="本卦" mode="plain" />
            </div>
            {ordered.map((l) => {
              const isShi = shiYao === l.pos;
              const isYing = yingYao === l.pos;
              return (
                <div key={l.pos} className="flex items-center gap-2">
                  <div className="w-8 text-[10px]" style={{ color: COLOR.muted }}>
                    {l.pos === 1 ? <Jargon term="初爻" mode="plain" /> :
                     l.pos === 6 ? <Jargon term="上爻" mode="plain" /> :
                     `${l.pos}爻`}
                  </div>
                  <div className="flex-1 h-5 flex items-center">
                    {l.yang
                      ? <div className="w-full h-2 rounded-sm" style={{ background: COLOR.gold }} />
                      : <div className="w-full flex gap-1">
                          <div className="flex-1 h-2 rounded-sm" style={{ background: COLOR.ink }} />
                          <div className="flex-1 h-2 rounded-sm" style={{ background: COLOR.ink }} />
                        </div>}
                  </div>
                  <div className="w-10 text-[10px] text-right font-mono" style={{ color: COLOR.muted }}>{l.gan_zhi}</div>
                  <div className="w-8 text-[10px]" style={{ color: COLOR.jade }}>{shen[l.pos - 1] || ""}</div>
                  {isShi && <span className="text-[9px] font-semibold" style={{ color: COLOR.goldBright }}>世</span>}
                  {isYing && <span className="text-[9px] font-semibold" style={{ color: COLOR.azure }}>应</span>}
                  {dong.includes(l.pos) && <span className="text-[10px]" style={{ color: COLOR.danger }}>○</span>}
                </div>
              );
            })}
          </div>
          <div className="space-y-1.5">
            <div className="text-xs text-center mb-1" style={{ color: COLOR.muted }}>
              <Jargon term="变卦" mode="plain" />
            </div>
            {ordered.map((l) => {
              const isDong = dong.includes(l.pos);
              const newYang = isDong ? !l.yang : l.yang;
              return (
                <div key={l.pos} className="flex items-center gap-2">
                  <div className="w-8 text-[10px]" style={{ color: COLOR.muted }}>
                    {l.pos === 1 ? <Jargon term="初爻" mode="plain" /> :
                     l.pos === 6 ? <Jargon term="上爻" mode="plain" /> :
                     `${l.pos}爻`}
                  </div>
                  <div className="flex-1 h-5 flex items-center">
                    {newYang
                      ? <div className="w-full h-2 rounded-sm" style={{ background: COLOR.gold }} />
                      : <div className="w-full flex gap-1">
                          <div className="flex-1 h-2 rounded-sm" style={{ background: COLOR.ink }} />
                          <div className="flex-1 h-2 rounded-sm" style={{ background: COLOR.ink }} />
                        </div>}
                  </div>
                  {isDong && <span className="text-[10px]" style={{ color: COLOR.danger }}>×</span>}
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[10px]" style={{ color: COLOR.muted }}>
          <span><span style={{ color: COLOR.goldBright }}>世</span> · <Jargon term="世爻" mode="plain" /></span>
          <span><span style={{ color: COLOR.azure }}>应</span> · <Jargon term="应爻" mode="plain" /></span>
          <span>○ / × · <Jargon term="动爻" mode="plain" /></span>
        </div>
      </div>

      <JargonBox
        title="六爻怎么看"
        items={[
          { term: "本卦",  plain: "原本的卦(现状)" },
          { term: "变卦",  plain: "变化后的卦(发展)" },
          { term: "动爻",  plain: "正在变的那一爻" },
          { term: "世爻",  plain: "你自己的位置" },
          { term: "应爻",  plain: "对方/事的位置" },
          { term: "六神",  plain: "6 种神煞(气质)" },
          { term: "纳甲",  plain: "每爻的天干地支" },
        ]}
      />

      <div className="card-raised text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div><Jargon term="卦辞" mode="plain" /> <span style={{ color: COLOR.ink }}>{r.gua_ci || "—"}</span></div>
        <div>六亲: <span style={{ color: COLOR.ink }}>{(r.liu_qin || []).join(" / ") || "—"}</span></div>
        {r.using && <div>用神: <span style={{ color: COLOR.gold }}>{r.using}</span></div>}
        {r.original_god && <div>原神: <span style={{ color: COLOR.jade }}>{r.original_god}</span></div>}
      </div>
    </div>
  );
}
