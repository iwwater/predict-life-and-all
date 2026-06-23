import { useMemo, useState } from "react";

export type StaggerOpts = {
  interval?: number;
  initialDelay?: number;
  easing?: string;
  maxTotal?: number;
};

export type StaggerStyle = {
  opacity: number;
  animationDelay: string;
  animationDuration: string;
  animationTimingFunction: string;
};

const FADE_DURATION_MS = 600;

export function useStaggeredReveal(
  itemCount: number,
  opts?: StaggerOpts,
): {
  getDelay: (i: number) => string;
  getStyle: (i: number) => StaggerStyle;
  reset: () => void;
  totalDuration: number;
} {
  const initialDelay = opts?.initialDelay ?? 0;
  const requestedInterval = opts?.interval ?? 80;
  const easing = opts?.easing ?? "ease-out";
  const maxTotal = opts?.maxTotal;

  const interval = useMemo(() => {
    if (itemCount <= 1) return requestedInterval;
    if (maxTotal == null) return requestedInterval;
    const requestedTotal =
      initialDelay + (itemCount - 1) * requestedInterval + FADE_DURATION_MS;
    if (requestedTotal <= maxTotal) return requestedInterval;
    const accelerated =
      (maxTotal - initialDelay - FADE_DURATION_MS) / (itemCount - 1);
    return Math.max(0, accelerated);
  }, [itemCount, initialDelay, requestedInterval, maxTotal]);

  const totalDuration = useMemo(() => {
    if (itemCount <= 0) return 0;
    return initialDelay + Math.max(0, itemCount - 1) * interval + FADE_DURATION_MS;
  }, [itemCount, initialDelay, interval]);

  const [, setVersion] = useState(0);

  function getDelay(i: number): string {
    return `${initialDelay + i * interval}ms`;
  }

  function getStyle(i: number): StaggerStyle {
    return {
      opacity: 0,
      animationDelay: `${initialDelay + i * interval}ms`,
      animationDuration: `${FADE_DURATION_MS}ms`,
      animationTimingFunction: easing,
    };
  }

  function reset(): void {
    setVersion((v) => v + 1);
  }

  return { getDelay, getStyle, reset, totalDuration };
}

if (import.meta.env.DEV) {
  if (typeof document !== "undefined") {
    const probe = document.createElement("div");
    probe.dataset.staggerProbe = "useStaggeredReveal";
    document.body.appendChild(probe);

    const count = 4;
    const interval = 80;
    const initialDelay = 0;
    const fade = 600;
    const delay0 = `${initialDelay + 0 * interval}ms`;
    const delay3 = `${initialDelay + 3 * interval}ms`;
    const totalDuration = initialDelay + (count - 1) * interval + fade;
    console.log("[useStaggeredReveal] probe", {
      count,
      interval,
      delay0,
      delay3,
      totalDuration,
    });
    const expected = initialDelay + (count - 1) * interval + fade;
    if (totalDuration !== expected) {
      console.warn("[useStaggeredReveal] interval math mismatch", totalDuration);
    }
    probe.remove();
  }
}
