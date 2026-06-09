// 八字 K 线图(Canvas)—— 把人生大运时间轴转成"价格曲线",灵感来自 life-kline。
// 输入:chart.raw.pillars + chart.normalized.timeline(大运) + 简易"流年评分"算法
// 输出:HTMLCanvasElement,渲染 OHLC 风格的"运势 K 线"
import type { ChartResult } from "./types";

interface KlineBar {
  year: number;
  open: number; high: number; low: number; close: number;
  label: string; // 大运标签
}

function ganZhiWuxingScore(gz: string): number {
  // 简易五行打分:天干 0.5 + 地支 0.5,落到 wood/fire/earth/metal/water
  const T = "甲乙丙丁戊己庚辛壬癸";
  const D = "子丑寅卯辰巳午未申酉戌亥";
  const tMap: Record<string, number> = { 甲: 1, 乙: 1, 丙: 2, 丁: 2, 戊: 3, 己: 3, 庚: 4, 辛: 4, 壬: 5, 癸: 5 };
  const dMap: Record<string, number> = { 子: 5, 丑: 3, 寅: 1, 卯: 1, 辰: 3, 巳: 2, 午: 2, 未: 3, 申: 4, 酉: 4, 戌: 3, 亥: 5 };
  const t = gz[0], d = gz[1];
  return (tMap[t] ?? 3) * 0.5 + (dMap[d] ?? 3) * 0.5; // 1~5
}

export function buildKline(chart: ChartResult, startYear: number, years: number = 80): KlineBar[] {
  const timeline = chart.normalized.timeline || [];
  // 如果有 timeline,逐大运给基线;否则从 2024 起算用流年干支推
  const bars: KlineBar[] = [];
  if (timeline.length === 0) {
    // 兜底:每年一个 10 年窗口
    for (let i = 0; i < years; i++) {
      const y = startYear + i;
      bars.push({
        year: y,
        open: 50, high: 55, low: 45, close: 50,
        label: String(y),
      });
    }
    return bars;
  }
  // 用大运段,每段 ~10 年,内部做"中→开→收"波动
  for (const seg of timeline) {
    const from = parseInt(seg.from) || startYear;
    const to = parseInt(seg.to) || from + 10;
    const base = ganZhiWuxingScore(seg.label.replace("大运·", "")) * 20; // 20~100
    const span = to - from;
    const step = Math.max(1, Math.floor(span / 5));
    let prev = base;
    for (let y = from; y <= to; y += step) {
      const drift = (Math.random() - 0.5) * 12;
      const open = prev;
      const close = Math.max(10, Math.min(100, base + drift));
      const high = Math.max(open, close) + Math.random() * 6;
      const low = Math.min(open, close) - Math.random() * 6;
      bars.push({ year: y, open, high, low, close, label: seg.label });
      prev = close;
    }
  }
  return bars;
}

export function renderKline(canvas: HTMLCanvasElement, bars: KlineBar[]): void {
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth, cssH = canvas.clientHeight || 320;
  canvas.width = cssW * dpr;
  canvas.height = cssH * dpr;
  const ctx = canvas.getContext("2d")!;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssW, cssH);

  // 背景网格
  ctx.strokeStyle = "rgba(212, 175, 106, 0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = (cssH / 5) * i + 20;
    ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(cssW - 10, y); ctx.stroke();
  }

  if (bars.length === 0) return;
  const padL = 50, padR = 10, padT = 20, padB = 30;
  const W = cssW - padL - padR;
  const H = cssH - padT - padB;
  const allHigh = Math.max(...bars.map(b => b.high));
  const allLow  = Math.min(...bars.map(b => b.low));
  const yMin = Math.max(0, allLow - 10);
  const yMax = Math.min(110, allHigh + 10);
  const yScale = (v: number) => padT + H - ((v - yMin) / (yMax - yMin)) * H;
  const xStep = W / Math.max(1, bars.length - 1);

  // Y 轴标签
  ctx.fillStyle = "rgba(212, 175, 106, 0.5)";
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
    ctx.strokeStyle = bullish ? "#d4af6a" : "#8b3a3a";
    ctx.fillStyle   = bullish ? "#d4af6a" : "#8b3a3a";
    // 影线
    ctx.beginPath();
    ctx.moveTo(x, yH); ctx.lineTo(x, yL); ctx.stroke();
    // 实体
    const top = Math.min(yO, yC);
    const bodyH = Math.max(1, Math.abs(yC - yO));
    const bw = Math.max(2, xStep * 0.5);
    ctx.fillRect(x - bw / 2, top, bw, bodyH);
  }

  // X 轴年份
  ctx.fillStyle = "rgba(212, 175, 106, 0.5)";
  ctx.textAlign = "center";
  const labelStep = Math.max(1, Math.floor(bars.length / 8));
  bars.forEach((b, i) => {
    if (i % labelStep === 0) {
      ctx.fillText(String(b.year), padL + i * xStep, cssH - 8);
    }
  });
}
