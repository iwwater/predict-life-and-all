// LLM Key 管理(浏览器本地 zustand persist;不出前端)
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { LLMConfig, LLMProvider } from "../lib/types";

interface KeysState {
  config: LLMConfig;
  setProvider: (p: LLMProvider) => void;
  setApiKey: (k: string) => void;
  setBaseUrl: (u: string) => void;
  setModel: (m: string) => void;
  hasKey: () => boolean;
  reset: () => void;
}

const DEFAULT: LLMConfig = {
  provider: "openai",
  apiKey: "",
  baseUrl: "https://api.openai.com/v1",
  model: "gpt-4o-mini",
};

export const useKeys = create<KeysState>()(
  persist(
    (set, get) => ({
      config: DEFAULT,
      setProvider: (p) => set({ config: { ...get().config, provider: p } }),
      setApiKey: (k) => set({ config: { ...get().config, apiKey: k } }),
      setBaseUrl: (u) => set({ config: { ...get().config, baseUrl: u } }),
      setModel: (m) => set({ config: { ...get().config, model: m } }),
      hasKey: () => !!get().config.apiKey,
      reset: () => set({ config: DEFAULT }),
    }),
    { name: "mystic-hub-keys" },
  ),
);
