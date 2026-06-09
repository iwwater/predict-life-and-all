export type Gender = "male" | "female" | "unspecified";
export type School = "east" | "west";
export type Method =
  | "bazi" | "bazi_v2" | "ziwei" | "qimen" | "liuyao" | "meihua" | "chenggu"
  | "bazhai" | "xuankong"
  | "western" | "vedic" | "tarot" | "numerology"
  | "lenormand" | "liuren" | "tieban"
  | "cross_validator" | "hour_calibrator" | "compatibility";

export type Subject =
  | "self_life" | "annual_luck" | "career" | "relationship" | "wealth"
  | "decision" | "lost_item" | "home_fengshui" | "tarot_guidance"
  | "lenormand_guidance";

export type TarotSpread =
  | "single" | "three_time" | "three_mind" | "choice_two"
  | "relationship_cross" | "career_path" | "celtic_cross";

export interface Birth {
  year: number; month: number; day: number;
  hour: number; minute: number;
  gender: Gender;
  calendar: "gregorian" | "lunar";
  lat?: number | null; lng?: number | null;
  tz: string;
  is_leap_month?: boolean;
}

export interface MethodMeta {
  id: Method;
  school: School;
  name_zh: string;
  name_en: string;
  group: string;
  needs: string[];
  engine: string;
  subjects?: Subject[];
  modes?: string[];
  default_mode?: string;
  required_inputs?: Record<string, string[]>;
  recommended_for?: string[];
}

export interface ChartResult {
  method: Method;
  school: School;
  engine: string;
  normalized: {
    elements?: Record<string, number>;
    timeline?: Array<{ from: string; to: string; label: string; score: number | null }>;
  };
  raw: Record<string, any>;
  elapsed_ms?: number;
}

export interface Case {
  id: string; name_zh: string; name_en: string;
  year: number; month: number; day: number;
  hour: number; minute: number;
  lat: number; lng: number; tz: string;
  gender: "male" | "female";
  note: string;
}

export type InterpretEvent =
  | { type: "delta"; text: string }
  | { type: "done"; meta: { blocked: boolean; softened_terms: string[]; methods: string[]; flags: string[] } }
  | { type: "error"; text: string };

export interface ComputeRequest {
  method: Method;
  birth: Birth;
  options?: {
    mode?: string;
    subject?: Subject;
    spread?: TarotSpread;
    seed?: number | string | null;
    question?: string;
    period?: number;
    sitting?: string | null;
    construction_year?: number;
    method_inputs?: Record<string, any>;
  };
}

export interface InterpretRequest {
  charts: ChartResult[];
  question?: string;
  client?: "mock" | "anthropic";
}

export type LLMProvider = "openai" | "claude" | "gemini" | "deepseek" | "packy" | "custom";

export interface LLMConfig {
  provider: LLMProvider;
  apiKey: string;
  baseUrl?: string;
  model: string;
}

export const SANS_24 = [
  "壬", "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳",
  "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥",
] as const;
export type San = typeof SANS_24[number];
