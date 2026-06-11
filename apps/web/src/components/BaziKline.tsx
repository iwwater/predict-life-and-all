// 八字 K 线图(Canvas):从 normalized.timeline 渲染 OHLC
import { useEffect, useRef } from "react";
import type { ChartResult } from "../lib/types";
import { COLOR } from "./ui";

interface KlineBar {
  year: number;
  open: number; high: number; low: number; close: number;
  label: string;
}

function scoreFromLabel(label: string): number {
  const T = "甲乙丙丁戊己庚辛壬癸";
  const D = "子丑寅卯辰巳午未申酉戌亥";
  const tMap: Record<string, number> = { 甲: 1, 乙: 1, 丙: 2, 丁: 2, 戊: 3, 己: 3, 庚: 4, 辛: 4, 壬: 5, 癸: 5 };
  const dMap: Record<string, number> = { 子: 5, 丑: 3, 寅: 1, 卯: 1, 辰: 3, 巳: 2, 午: 2, 未: 3, 申: 4, 酉: 4, 戌: 3, 亥: 5 };
  const gz = label.replace("大运·", "");
  return ((tMap[gz[0]] ?? 3) * 0.5 + (dMap[gz[1]] ?? 3) * 0.5) * 20; // 0-100
}

function buildKline(chart: ChartResult, startYear: number, years = 80): KlineBar[] {
  const timeline = chart.normalized.timeline || [];
  if (timeline.length === 0) {
    const out: KlineBar[] = [];
    for (let i = 0; i < years; i++) {
      const y = startYear + i;
      out.push({ year: y, open: 50, high: 55, low: 45, close: 50, label: String(y) });
    }
    return out;
  }
  const bars: KlineBar[] = [];
  // 用每段大运 ~10 年
  for (const seg of timeline) {
    const from = parseInt(seg.from) || startYear;
    const to = parseInt(seg.to) || from + 10;
    const base = scoreFromLabel(seg.label);
    const span = to - from;
    const step = Math.max(1, Math.floor(span / 5));
    let prev = base;
    // 可复现的伪随机
    let seed = from;
    const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
    for (let y = from; y <= to; y += step) {
      const drift = (rand() - 0.5) * 12;
      const open = prev;
      const close = Math.max(10, Math.min(100, base + drift));
      const high = Math.max(open, close) + rand() * 6;
      const low = Math.min(open, close) - rand() * 6;
      bars.push({ year: y, open, high, low, close, label: seg.label });
      prev = close;
    }
  }
  return bars;
}

function render(canvas: HTMLCanvasElement, bars: KlineBar[]): void {
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth;
  const cssH = canvas.clientHeight || 320;
  canvas.width = cssW * dpr;
  canvas.height = cssH * dpr;
  const ctx = canvas.getContext("2d")!;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssW, cssH);

  // 网格
  ctx.strokeStyle = "rgba(201,162,75,0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = (cssH / 5) * i + 20;
    ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(cssW - 10, y); ctx.stroke();
  }
  if (bars.length === 0) return;
  const padL = 50, padR = 10, padT = 20, padB = 30;
  const W = cssW - padL - padR;
  const H = cssH - padT - padB;
  const allHigh = Math.max(...bars.map((b) => b.high));
  const allLow = Math.min(...bars.map((b) => b.low));
  const yMin = Math.max(0, allLow - 10);
  const yMax = Math.min(110, allHigh + 10);
  const yScale = (v: number) => padT + H - ((v - yMin) / (yMax - yMin)) * H;
  const xStep = W / Math.max(1, bars.length - 1);

  // Y 轴
  ctx.fillStyle = "rgba(201,162,75,0.55)";
  ctx.font = "10px ui-monospace";
  ctx.textAlign = "right";
  for (let v = Math.ceil(yMin / 20) * 20; v <= yMax; v += 20) {
    ctx.fillText(String(v), padL - 6, yScale(v) + 3);
  }
  // K 线
  for (let i = 0; i < bars.length; i++) {
    const b = bars[i];
    const x = padL + i * xStep;
    const yO = yScale(b.open), yC = yScale(b.close);
    const yH = yScale(b.high), yL = yScale(b.low);
    const bullish = b.close >= b.open;
    ctx.strokeStyle = bullish ? COLOR.gold : COLOR.danger;
    ctx.fillStyle = bullish ? COLOR.gold : COLOR.danger;
    ctx.beginPath();
    ctx.moveTo(x, yH); ctx.lineTo(x, yL); ctx.stroke();
    const top = Math.min(yO, yC);
    const bodyH = Math.max(1, Math.abs(yC - yO));
    const bw = Math.max(2, xStep * 0.5);
    ctx.fillRect(x - bw / 2, top, bw, bodyH);
  }
  // X 轴
  ctx.fillStyle = "rgba(201,162,75,0.55)";
  ctx.textAlign = "center";
  const labelStep = Math.max(1, Math.floor(bars.length / 8));
  bars.forEach((b, i) => {
    if (i % labelStep === 0) {
      ctx.fillText(String(b.year), padL + i * xStep, cssH - 8);
    }
  });
}

export function BaziKline({ chart }: { chart: ChartResult }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    // 用生命起点(出生年)
    const startYear = 2024 - 30;
    const bars = buildKline(chart, startYear, 80);
    render(c, bars);
    const onResize = () => render(c, bars);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [chart]);

  return (
    <div className="paper-frame">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-2">
        <div>
          <h3 className="text-lg" style={{ color: COLOR.goldBright }}>
            运势走势·K 线图
          </h3>
          <div className="text-[10px] mt-0.5" style={{ color: COLOR.muted }}>
            从大运地支五行推导出来的"运势强度"折线,看每十年起伏
          </div>
        </div>
        <div className="paper-tag paper-tag-east" style={{ color: COLOR.gold }}>
          <span style={{ color: COLOR.gold }}>●</span> 升 <span className="mx-1">/</span> <span style={{ color: COLOR.danger }}>●</span> 降
        </div>
      </div>
      <canvas ref={ref} style={{ width: "100%", height: 280 }} />
      <div className="text-[10px] mt-2 flex flex-wrap gap-x-3 gap-y-1" style={{ color: COLOR.muted }}>
        <span><span style={{ color: COLOR.goldBright }}>横轴</span> = 出生后每一年(流年)</span>
        <span><span style={{ color: COLOR.goldBright }}>纵轴</span> = 运势强度(0-100,数字越高那年越顺)</span>
        <span>每根 K 线代表一个十年的"主调"</span>
      </div>
    </div>
  );
}
