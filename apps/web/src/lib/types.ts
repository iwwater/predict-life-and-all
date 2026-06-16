export type Gender = "male" | "female" | "unspecified";
export type School = "east" | "west";
export type Method =
  | "bazi" | "bazi_v2" | "ziwei" | "qimen" | "liuyao" | "meihua" | "chenggu"
  | "bazhai" | "xuankong"
  | "western" | "vedic" | "tarot" | "numerology"
  | "lenormand" | "liuren" | "tieban" | "xiaoliuren" | "hepan"
  | "cross_validator" | "hour_calibrator" | "compatibility";

export type Subject =
  | "self_life" | "annual_luck" | "career" | "relationship" | "wealth"
  | "decision" | "lost_item" | "home_fengshui" | "tarot_guidance"
  | "lenormand_guidance";

export type TarotSpread =
  | "single" | "three_time" | "three_mind" | "choice_two"
  | "relationship_cross" | "career_path" | "celtic_cross"
  | "three_line" | "five_cross" | "nine_square" | "grand_tableau";

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

// User-created event cases. This is not the removed celebrity-case dataset.
export type CaseStatus = "draft" | "context_ready" | "officially_cast";

export interface MinimalQuestion {
  id: string;
  prompt: string;
  options: string[];
  required: boolean;
}

export interface EventCase {
  case_id: string;
  parent_case_id?: string | null;
  event_type: string;
  question: string;
  subject?: string | null;
  target?: string | null;
  time_horizon?: string | null;
  location?: string | null;
  status: CaseStatus;
  version: number;
  intent: Record<string, any>;
  minimal_questions: MinimalQuestion[];
  birth?: Birth | null;
  space?: Record<string, any> | null;
  context: Record<string, any>;
  constraints: Record<string, any>;
  result_session_id?: string | null;
  created_at: number;
  updated_at: number;
}

export interface CaseCreateRequest {
  question: string;
  goal?: string | null;
  birth?: Birth | null;
  subject?: string | null;
  target?: string | null;
  time_horizon?: string | null;
  location?: string | null;
  current_city?: string | null;
}

export interface CaseContextRequest {
  answers?: Record<string, any>;
  birth?: Birth | null;
  space?: Record<string, any> | null;
  constraints?: Record<string, any>;
}

export interface CaseCastRequest {
  depth?: ReadingDepth;
  methods?: string[] | null;
  method_options?: Record<string, any> | null;
}

export interface CaseVersionRequest {
  question?: string | null;
  changed_condition: string;
  context_updates?: Record<string, any>;
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
    partner?: Birth;
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

// ── /api/reading types ─────────────────────────────────────────────────────

export type ReadingDepth = "free" | "standard" | "premium";

export interface ReadingAPIRequest {
  goal?: string | null;
  question: string;
  birth?: Birth | null;
  target_birth?: Birth | null;
  space?: {
    sitting?: string | null;
    period?: number | null;
    construction_year?: number | null;
    address?: string | null;
  } | null;
  method_options?: Record<string, any> | null;
  methods?: string[] | null;
  depth?: ReadingDepth;
  language?: "zh" | "en";
}

export type Dimension = "long_term" | "current_cycle" | "relationship" | "one_question" | "space";

export type TimeScope =
  | "short_term"
  | "medium_term"
  | "long_term"
  | "current_cycle"
  | "one_question"
  | "space";

export interface DivinationSignal {
  method: string;
  domain: string;
  signal_key: string;
  polarity: "positive" | "negative" | "neutral" | "mixed";
  strength: number;
  evidence: string;
  confidence: number;
  /** 5 维职责分派 (方案 §十三): long_term/current_cycle/relationship/one_question/space */
  dimension?: Dimension | null;
  /** 时间范围: short_term/medium_term/long_term/current_cycle/one_question/space */
  time_scope?: TimeScope | null;
  advice?: string | null;
}

export interface ConsensusItem {
  domain: string;
  theme: string;
  supporting_methods: string[];
  weight_strength: number;
  explanation: string;
}

export interface ConflictItem {
  domain: string;
  severity: "low" | "medium" | "high";
  positive_methods: string[];
  negative_methods: string[];
  neutral_methods: string[];
  conflict_explanation: string;
  resolution: string;
}

export interface ValidationResult {
  consensus: ConsensusItem[];
  conflicts: ConflictItem[];
  overall_score: number;
  confidence: number;
  confidence_level: "low" | "medium" | "medium_high" | "high";
  risks: string[];
  timing?: Record<string, any> | null;
  action_advice: string[];
  /** 5 维 0-100 分数 (long_term/current_cycle/relationship/one_question/space) */
  dim_scores?: Record<Dimension, number>;
  /** 每维有效信号数 */
  dim_signals_count?: Record<Dimension, number>;
  /** 按维度分组的共识 */
  per_dim_consensus?: Record<Dimension, ConsensusItem[]>;
}

export interface ReadingReport {
  free: string;
  standard: string;
  premium: string;
}

export interface DimBreakdown {
  score: number;
  signals_count: number;
  top_signal?: DivinationSignal | null;
  summary?: string;
}

export interface ReadingResult {
  session_id: string;
  intent: Record<string, any>;
  methods_used: string[];
  signals: DivinationSignal[];
  consensus: ConsensusItem[];
  conflicts: ConflictItem[];
  validation: ValidationResult;
  report: ReadingReport;
  disclaimer: string;
  elapsed_ms: number;
  errors: Array<{ method: string; error: string }>;
  is_unlocked_standard: boolean;
  is_unlocked_premium: boolean;
  safety_flags: string[];
  safety_downgrades: string[];
  /** 5 维分解 */
  dim_breakdown?: Record<Dimension, DimBreakdown>;
}

export interface CastResponse {
  case: EventCase;
  result: ReadingResult;
  idempotent: boolean;
}

export const METHOD_LABELS_ZH: Record<string, string> = {
  bazi_v2: "八字",
  ziwei: "紫微",
  qimen: "奇门",
  liuyao: "六爻",
  meihua: "梅花",
  fengshui: "风水",
  bazhai: "八宅",
  xuankong: "玄空",
  western: "西方占星",
  vedic: "吠陀占星",
  tarot: "塔罗",
  numerology: "数字命理",
  liuren: "大六壬",
  xiaoliuren: "小六壬",
  tieban: "铁板",
  lenormand: "雷诺曼",
  hepan: "合盘",
};
