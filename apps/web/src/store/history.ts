// 排盘历史(浏览器本地 zustand;不存 LLM Key)
// v1:扩展字段 subject/modeByMethod/spread/tags/favorite/reflection,
//    加 persist.version + migrate 给旧数据补默认值。
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Birth, ChartResult, Method, Subject, TarotSpread } from "../lib/types";

export type ReflectionVerdict = "accurate" | "inaccurate" | "pending";

export interface Reflection {
  verdict: ReflectionVerdict;
  note?: string;
  at: number;
}

export interface HistoryEntry {
  id: string;
  ts: number;
  birth: Birth;
  methods: Method[];
  charts: Record<string, ChartResult>;
  question?: string;
  // v1 新增
  subject?: Subject;
  modeByMethod?: Partial<Record<Method, string>>;
  spread?: TarotSpread;
  tags?: string[];
  favorite?: boolean;
  reflection?: Reflection | null;
}

// 派生 tags:把主题+方法拍平,方便后续 history 页筛选
export function deriveTags(methods: Method[], subject?: Subject): string[] {
  const out: string[] = [];
  if (subject) out.push(subject);
  for (const m of methods) out.push(m);
  return Array.from(new Set(out));
}

interface HistoryState {
  items: HistoryEntry[];
  add: (e: HistoryEntry) => void;
  remove: (id: string) => void;
  clear: () => void;
  toggleFavorite: (id: string) => void;
  setReflection: (id: string, reflection: Reflection | null) => void;
  update: (id: string, patch: Partial<HistoryEntry>) => void;
}

const MAX = 30;

function patchItem(items: HistoryEntry[], id: string, patch: (it: HistoryEntry) => HistoryEntry): HistoryEntry[] {
  return items.map((it) => (it.id === id ? patch(it) : it));
}

export const useHistory = create<HistoryState>()(
  persist(
    (set, get) => ({
      items: [],
      add: (e) => {
        const items = [e, ...get().items].slice(0, MAX);
        set({ items });
      },
      remove: (id) => set({ items: get().items.filter((i) => i.id !== id) }),
      clear: () => set({ items: [] }),
      toggleFavorite: (id) =>
        set({ items: patchItem(get().items, id, (it) => ({ ...it, favorite: !it.favorite })) }),
      setReflection: (id, reflection) =>
        set({ items: patchItem(get().items, id, (it) => ({ ...it, reflection })) }),
      update: (id, patch) =>
        set({ items: patchItem(get().items, id, (it) => ({ ...it, ...patch })) }),
    }),
    {
      name: "mystic-hub-history",
      version: 1,
      // 给 v0 数据补默认值;旧字段保留,新字段填空。
      migrate: (raw: any, _fromVersion: number) => {
        if (!raw || typeof raw !== "object") return { items: [] };
        const items = Array.isArray(raw.items) ? raw.items : [];
        const migrated = items.map((it: any) => ({
          id: String(it.id ?? crypto.randomUUID()),
          ts: Number(it.ts ?? Date.now()),
          birth: it.birth,
          methods: Array.isArray(it.methods) ? it.methods : [],
          charts: it.charts ?? {},
          question: it.question,
          subject: it.subject,
          modeByMethod: it.modeByMethod,
          spread: it.spread,
          tags: Array.isArray(it.tags)
            ? it.tags
            : deriveTags(Array.isArray(it.methods) ? it.methods : [], it.subject),
          favorite: Boolean(it.favorite),
          reflection: it.reflection ?? null,
        }));
        return { items: migrated };
      },
    },
  ),
);
