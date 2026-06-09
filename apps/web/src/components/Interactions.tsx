// 通用交互原子:useInView + Reveal + Starfield + SubjectGlyph
// 设计目标: 0 依赖,全部用 React + CSS animation;轻量、克制、不喧宾夺主
import { useEffect, useMemo, useRef, useState } from "react";

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

// 包裹子元素, 视口可见时播放 reveal-up 动画
export function Reveal({
  children,
  delayMs = 0,
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
    <div
      ref={ref}
      className={`reveal-up ${inView ? "" : "opacity-0"} ${className}`}
      style={{ animationDelay: inView ? `${delayMs}ms` : undefined, ...style }}
    >
      {children}
    </div>
  );
}

// 星空背景: 用 CSS 实现,SVG 圆点 + 慢漂移, 极轻量
export function Starfield({ count = 70, className = "" }: { count?: number; className?: string }) {
  const stars = useMemo(() => {
    return Array.from({ length: count }).map((_, i) => {
      const x = (i * 73) % 100;          // 0-100 %
      const y = ((i * 137) % 97) + 1;    // 0-100 %
      const r = (i % 7 === 0) ? 1.4 : (i % 3 === 0 ? 1.0 : 0.6);
      const op = 0.25 + ((i * 19) % 60) / 100; // 0.25 - 0.85
      const dur = 4 + ((i * 31) % 50) / 10;    // 4 - 9 s
      const delay = ((i * 11) % 70) / 10;      // 0 - 7 s
      return { x, y, r, op, dur, delay, i };
    });
  }, [count]);

  return (
    <div
      aria-hidden
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
        {stars.map((s) => (
          <circle
            key={s.i}
            cx={`${s.x}%`}
            cy={`${s.y}%`}
            r={s.r}
            fill="#E6E1D3"
            style={{
              opacity: s.op,
              animation: `twinkle ${s.dur}s ease-in-out ${s.delay}s infinite`,
            }}
          />
        ))}
      </svg>
      {/* 渐隐边缘,避免和正文抢眼 */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 70% 60% at 50% 30%, transparent 50%, var(--bg-deep) 95%)",
        }}
      />
      <style>{`
        @keyframes twinkle {
          0%, 100% { opacity: var(--o, 0.5); }
          50% { opacity: 0.15; }
        }
      `}</style>
    </div>
  );
}

// 主体意图图标(命 / 卜 / 风水 / 西方),SVG 一致线条 + 古意
export function SubjectGlyph({
  glyph,
  size = 22,
  color = "currentColor",
  className = "",
}: {
  glyph: "self" | "annual" | "decision" | "relationship" | "career" | "wealth" | "lost" | "home" | "tarot" | "lenormand";
  size?: number;
  color?: string;
  className?: string;
}) {
  const s = size;
  const sw = 1.3;
  const common = { width: s, height: s, viewBox: "0 0 24 24", fill: "none", stroke: color, strokeWidth: sw, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, className };
  switch (glyph) {
    case "self":
      return ( // 山/日 一体
        <svg {...common}>
          <circle cx="12" cy="9" r="3.2" />
          <path d="M3 19l5-7 4 5 3-3 6 5" />
        </svg>
      );
    case "annual":
      return ( // 流转
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3" />
          <path d="M14.5 9.5l-3 2.5-2-1.5" />
        </svg>
      );
    case "decision":
      return ( // 分叉
        <svg {...common}>
          <circle cx="12" cy="12" r="2.2" />
          <path d="M12 14.2L5.5 20M12 14.2L18.5 20" />
        </svg>
      );
    case "relationship":
      return ( // 双方
        <svg {...common}>
          <circle cx="8" cy="9" r="2.5" />
          <circle cx="16" cy="9" r="2.5" />
          <path d="M3 19c1-3 3-4 5-4M21 19c-1-3-3-4-5-4" />
        </svg>
      );
    case "career":
      return ( // 阶梯
        <svg {...common}>
          <path d="M4 20h4v-5h4V10h4V5h4" />
          <circle cx="20" cy="5" r="1.2" fill={color} stroke="none" />
        </svg>
      );
    case "wealth":
      return ( // 钱币
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v8M9.5 10h4.5c.8 0 1.5.5 1.5 1.2s-.7 1.3-1.5 1.3h-3c-.8 0-1.5.6-1.5 1.3S9.2 15 10 15h5" />
        </svg>
      );
    case "lost":
      return ( // 寻
        <svg {...common}>
          <circle cx="10.5" cy="10.5" r="5.5" />
          <path d="M15 15l4.5 4.5" />
          <path d="M10.5 7.5v3M10.5 13v.01" />
        </svg>
      );
    case "home":
      return ( // 宅
        <svg {...common}>
          <path d="M3 11l9-7 9 7" />
          <path d="M5 10v10h14V10" />
          <path d="M10 20v-6h4v6" />
        </svg>
      );
    case "tarot":
      return ( // 牌
        <svg {...common}>
          <rect x="6" y="3.5" width="12" height="17" rx="1.5" />
          <path d="M9 7h6M9 11l3 2 3-2M9 16h6" />
        </svg>
      );
    case "lenormand":
      return ( // 牌阵
        <svg {...common}>
          <rect x="3.5" y="4" width="7" height="11" rx="1" />
          <rect x="13.5" y="4" width="7" height="11" rx="1" />
          <rect x="8.5" y="14" width="7" height="6" rx="1" />
        </svg>
      );
  }
}

// 进度条 (排盘时显示)
export function ProgressArc({ value, size = 96, label }: { value: number; size?: number; label?: string }) {
  const r = size / 2 - 6;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="spin-slow-rev" style={{ opacity: 0.15 }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--gold)" strokeWidth="0.6" strokeDasharray="2 6" />
      </svg>
      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth="3" />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="var(--gold-bright)" strokeWidth="3" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - v)}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="font-display text-lg" style={{ color: "var(--gold-bright)" }}>{Math.round(v * 100)}%</div>
        {label && <div className="text-[10px] mt-0.5" style={{ color: "var(--muted)" }}>{label}</div>}
      </div>
    </div>
  );
}

// 金尘粒子: 漂浮的金色微光粒子,营造奢华感
export function GoldDust({ count = 25, className = "" }: { count?: number; className?: string }) {
  const particles = useMemo(() => {
    return Array.from({ length: count }).map((_, i) => {
      const left = ((i * 67 + 13) % 100);
      const size = (i % 5 === 0) ? 2.5 : (i % 3 === 0 ? 1.8 : 1.2);
      const dur = 5 + ((i * 23) % 40) / 10;   // 5-9s
      const delay = ((i * 41) % 80) / 10;      // 0-8s
      const drift = ((i % 2 === 0) ? 1 : -1) * (15 + (i * 17) % 40);
      return { left, size, dur, delay, drift, i };
    });
  }, [count]);

  return (
    <div aria-hidden className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}>
      {particles.map((p) => (
        <div
          key={p.i}
          className="gold-dust-particle absolute rounded-full"
          style={{
            left: `${p.left}%`,
            bottom: "-4px",
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: `radial-gradient(circle, rgba(229,188,94,0.9) 0%, rgba(201,162,75,0.3) 60%, transparent 100%)`,
            boxShadow: `0 0 ${p.size * 3}px rgba(229,188,94,0.4)`,
            "--dust-dur": `${p.dur}s`,
            "--dust-delay": `${p.delay}s`,
            ["--dust-drift" as string]: `${p.drift}px`,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

// 装饰分段线: 中钻 + 两侧金线
export function OrnamentalDivider({ className = "" }: { className?: string }) {
  return (
    <div className={`ornamental-divider ${className}`}>
      <span className="ornamental-diamond" />
    </div>
  );
}
