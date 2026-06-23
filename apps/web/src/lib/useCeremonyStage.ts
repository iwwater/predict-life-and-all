import { useCallback, useState } from "react";

export type Stage<T> = {
  id: string;
  label: string;
  labelEn?: string;
  data: T;
};

export type CeremonyResult<S extends readonly Stage<unknown>[]> = {
  stage: S[number] | null;
  advance: () => void;
  reset: () => void;
  isLast: boolean;
  index: number;
  total: number;
};

export function useCeremonyStage<S extends readonly Stage<unknown>[]>(
  stages: S,
): CeremonyResult<S> {
  const [index, setIndex] = useState<number>(-1);
  const total = stages.length;

  const advance = useCallback(() => {
    setIndex((i) => {
      if (i >= stages.length - 1) return i;
      return i + 1;
    });
  }, [stages.length]);

  const reset = useCallback(() => {
    setIndex(-1);
  }, []);

  const stage = index >= 0 && index < stages.length ? stages[index] : null;
  const isLast = index === stages.length - 1;

  return { stage, advance, reset, isLast, index, total };
}

if (import.meta.env.DEV) {
  const probeStages = [
    { id: "a", label: "A", data: 1 },
    { id: "b", label: "B", data: 2 },
    { id: "c", label: "C", data: 3 },
  ] as const;
  const probe = useCeremonyStage(probeStages);
  probe.advance();
  probe.advance();
  probe.advance();
  if (!probe.isLast) {
    console.warn("[useCeremonyStage] isLast should be true after 3 advances");
  }
  if (probe.index !== 2) {
    console.warn("[useCeremonyStage] index should be 2 after 3 advances");
  }
  probe.advance();
  if (probe.index !== 2) {
    console.warn("[useCeremonyStage] advance should clamp at last index");
  }
  probe.reset();
  if (probe.stage !== null) {
    console.warn("[useCeremonyStage] reset should make stage null");
  }
}