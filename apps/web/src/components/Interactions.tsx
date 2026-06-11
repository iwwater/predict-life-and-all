// 通用交互原子:useInView + Reveal + ProgressArc
// 「古籍×仪器」克制版 — 无星空/金尘/发光,仅保留必要交互
import { useEffect, useRef, useState } from "react";

// 滚动进入视口时触发
export function useInView<T extends HTMLElement>(options: { threshold?: number; once?: boolean } = {}) {
  const { threshold = 0.15, once = true } = options;
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") { setInView(true); return; }
    const obs = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) { setInView(true); if (once) obs.disconnect(); }
          else if (!once) setInView(false);
        }
      },
      { threshold },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold, once]);
  return { ref, inView };
}

// 视口可见时淡入(无动画延迟,克制处理)
export function Reveal({
  children,
  className = "",
  style,
}: {
  children: React.ReactNode;
  delayMs?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  return (
    <div ref={ref} style={{ opacity: inView ? 1 : 0, transition: "opacity 0.3s ease", ...style }} className={className}>
      {children}
    </div>
  );
}

// 进度圆弧 (排盘/加载时显示)
export function ProgressArc({ value, size = 96, label }: { value: number; size?: number; label?: string }) {
  const r = size / 2 - 6;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--rule)" strokeWidth="3" />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="var(--cinnabar)" strokeWidth="3" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - v)}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.9rem", color: "var(--cinnabar)", fontWeight: 700 }}>
          {Math.round(v * 100)}%
        </div>
        {label && <div style={{ fontSize: "0.65rem", marginTop: "0.15rem", color: "var(--ink-soft)" }}>{label}</div>}
      </div>
    </div>
  );
}
