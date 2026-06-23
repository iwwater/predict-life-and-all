import { useEffect, useRef, useState, type ReactNode } from "react";

export type Phase<T> = {
  id: string;
  label: string;
  labelEn?: string;
  data: T;
  render: (data: T) => ReactNode;
  duration?: number;
};

export type CalculusRevealProps<T> = {
  phases: Phase<T>[];
  stepInterval?: number;
  autoPlay?: boolean;
  onComplete?: () => void;
  maxDuration?: number;
  skippable?: boolean;
  reducedMotion?: "auto" | "always" | "never";
};

type ResolvedReducedMotion = "reduce" | "no-preference";

function resolveReducedMotion(
  mode: "auto" | "always" | "never",
): ResolvedReducedMotion {
  if (mode === "always") return "reduce";
  if (mode === "never") return "no-preference";
  if (typeof window === "undefined" || !window.matchMedia) return "no-preference";
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "reduce"
    : "no-preference";
}

export function CalculusReveal<T>(props: CalculusRevealProps<T>): React.JSX.Element {
  const {
    phases,
    stepInterval = 400,
    autoPlay = true,
    onComplete,
    maxDuration = 4000,
    skippable = true,
    reducedMotion = "auto",
  } = props;

  const total = phases.length;
  const motionMode = resolveReducedMotion(reducedMotion);
  const wantSkip = motionMode === "reduce";
  const [current, setCurrent] = useState<number>(wantSkip ? total - 1 : 0);
  const [finished, setFinished] = useState<boolean>(wantSkip);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (wantSkip) {
      setCurrent(total - 1);
      setFinished(true);
      onCompleteRef.current?.();
      return;
    }
    if (!autoPlay || total === 0) return;

    const interval = Math.max(0, stepInterval);
    const maxSteps = Math.max(0, Math.floor(maxDuration / Math.max(1, interval)) - 1);
    const effectiveSteps = Math.min(total - 1, maxSteps);
    const timers: number[] = [];

    for (let step = 1; step <= effectiveSteps; step++) {
      const id = window.setTimeout(() => {
        setCurrent(step);
      }, step * interval);
      timers.push(id);
    }

    const finishId = window.setTimeout(() => {
      setCurrent(effectiveSteps);
      setFinished(true);
      onCompleteRef.current?.();
    }, (effectiveSteps + 1) * interval);
    timers.push(finishId);

    return () => {
      for (const id of timers) window.clearTimeout(id);
    };
  }, [autoPlay, stepInterval, maxDuration, total, wantSkip]);

  function handleAdvance(): void {
    if (finished) return;
    if (current >= total - 1) {
      setFinished(true);
      onCompleteRef.current?.();
      return;
    }
    setCurrent((c) => c + 1);
  }

  function handleSkip(): void {
    if (finished) return;
    setCurrent(total - 1);
    setFinished(true);
    onCompleteRef.current?.();
  }

  if (total === 0) {
    return <div className="calculus-reveal calculus-reveal--empty" />;
  }

  const phase = phases[Math.min(current, total - 1)];
  const showLabel = !finished && current < total - 1;

  return (
    <div className="calculus-reveal" data-finished={finished ? "true" : "false"}>
      {showLabel && (
        <div className="calculus-reveal__label" aria-live="polite">
          正在{phase.label}…
        </div>
      )}
      <div
        key={phase.id}
        className={`calculus-reveal__stage ${finished ? "is-finished" : "is-revealing"}`}
        style={{ transition: "opacity 200ms ease-out", opacity: 1 }}
      >
        {phase.render(phase.data)}
      </div>
      <div className="calculus-reveal__controls">
        {!autoPlay && !finished && (
          <button
            type="button"
            className="calculus-reveal__btn"
            onClick={handleAdvance}
          >
            下一阶段
          </button>
        )}
        {skippable && !finished && (
          <button
            type="button"
            className="calculus-reveal__btn calculus-reveal__btn--skip"
            onClick={handleSkip}
          >
            跳过动画
          </button>
        )}
      </div>
    </div>
  );
}

if (import.meta.env.DEV) {
  const probePhases: Phase<string>[] = [
    {
      id: "phase-1",
      label: "起年柱",
      data: "year",
      render: (d) => d.toUpperCase(),
    },
    {
      id: "phase-2",
      label: "起月柱",
      data: "month",
      render: (d) => d.toUpperCase(),
    },
  ];
  if (probePhases.length !== 2) {
    console.warn("[CalculusReveal] probe expected 2 phases");
  }
  const rendered1 = probePhases[0].render(probePhases[0].data);
  const rendered2 = probePhases[1].render(probePhases[1].data);
  if (rendered1 !== "YEAR" || rendered2 !== "MONTH") {
    console.warn("[CalculusReveal] probe phase render mismatch", { rendered1, rendered2 });
  }
}