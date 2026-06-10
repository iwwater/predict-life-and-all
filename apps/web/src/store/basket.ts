/** 合参篮 Store — 用户可在各术法独立页把结果"加入合参篮"，再到 /aggregate 合参
 *
 * 存于 zustand (内存 + localStorage 持久化)
 * 格式: { items: [{ method, chart, birth, addedAt }] }
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Birth, ChartResult, Method } from "../lib/types";

export interface BasketEntry {
  method: Method;
  chart: ChartResult | null;     // 可为 null（仅登记术法，尚未计算）
  birth: Birth | null;           // 该术法使用的出生数据（供合参页复用）
  addedAt: number;
}

interface BasketState {
  items: BasketEntry[];
  /** 添加或更新 */
  add: (entry: BasketEntry) => void;
  /** 按 method 移除 */
  remove: (method: Method) => void;
  /** 清空 */
  clear: () => void;
  /** 检查是否已在篮中 */
  has: (method: Method) => boolean;
}

export const useBasket = create<BasketState>()(
  persist(
    (set, get) => ({
      items: [],
      add(entry) {
        set((s) => {
          const idx = s.items.findIndex((it) => it.method === entry.method);
          if (idx >= 0) {
            const next = [...s.items];
            next[idx] = entry;
            return { items: next };
          }
          return { items: [...s.items, entry] };
        });
      },
      remove(method) {
        set((s) => ({ items: s.items.filter((it) => it.method !== method) }));
      },
      clear() {
        set({ items: [] });
      },
      has(method) {
        return get().items.some((it) => it.method === method);
      },
    }),
    {
      name: "mystic-hub-basket",
      version: 0,
    },
  ),
);
