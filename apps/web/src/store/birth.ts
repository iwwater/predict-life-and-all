// 出生信息全局记忆 — 本地持久化，各专页自动带入，可改
// 依据: 前端重构指示v2 §一「出生信息全站记忆一次」
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Birth, Gender } from "../lib/types";

export interface StoredBirth {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  gender: Gender;
  calendar: "gregorian" | "lunar";
  lat: number | null;
  lng: number | null;
  tz: string;
  city?: string;
  is_leap_month?: boolean;
}

const DEFAULT_BIRTH: StoredBirth = {
  year: 1990,
  month: 5,
  day: 15,
  hour: 8,
  minute: 30,
  gender: "male",
  calendar: "gregorian",
  lat: 31.23,
  lng: 121.47,  // 上海
  tz: "Asia/Shanghai",
  city: "上海",
  is_leap_month: false,
};

interface BirthState {
  birth: StoredBirth;
  setBirth: (patch: Partial<StoredBirth>) => void;
  resetBirth: () => void;
  /** 返回符合 Birth 接口的对象，用于 API 调用 */
  toApiBirth: () => Birth;
}

export const useBirthStore = create<BirthState>()(
  persist(
    (set, get) => ({
      birth: { ...DEFAULT_BIRTH },
      setBirth: (patch) => set((s) => ({ birth: { ...s.birth, ...patch } })),
      resetBirth: () => set({ birth: { ...DEFAULT_BIRTH } }),
      toApiBirth: () => {
        const b = get().birth;
        return {
          year: b.year,
          month: b.month,
          day: b.day,
          hour: b.hour,
          minute: b.minute,
          gender: b.gender,
          calendar: b.calendar,
          lat: b.lat ?? null,
          lng: b.lng ?? null,
          tz: b.tz,
          is_leap_month: b.is_leap_month ?? false,
        };
      },
    }),
    {
      name: "mystic-hub-birth",
      version: 1,
    },
  ),
);
