// 前后端 API 客户端(对齐 server/api/* 路径 `/api/*` —— 不是 `/api/v1/*`)
import type {
  Method, MethodMeta, ChartResult,
  ComputeRequest, InterpretEvent, Birth,
  EventCase, CaseCreateRequest, CaseContextRequest, CaseCastRequest,
  CaseVersionRequest, CastResponse,
} from "./types";

// ── Enhanced result types ───────────────────────────────────────────
export interface CrossValidationResult {
  ensemble_score?: number;
  confidence?: number;
  agreement_matrix?: Record<string, number>;
  domain_checks?: Record<string, any>;
  cross_checks?: any[];
  overall_assessment?: string;
}

export interface PeachBlossomResult {
  index?: number;
  level?: string;
  timing?: string;
  details?: Record<string, any>;
}

export interface FateModificationPlan {
  element_balance?: Record<string, any>;
  remedies?: Record<string, any>;
  action_windows?: any[];
  daily_practices?: string[];
  mutable_patterns?: string[];
  fixed_patterns?: string[];
  career_advice?: any;
  relationship_advice?: any;
  health_advice?: any;
}

export interface CompatibilityResult {
  // Single-method fields
  compatibility_score?: number;
  total_score?: number;
  level?: string;
  interpretation?: string;
  breakdown?: Record<string, any>;
  advice?: string[];

  // Multi-method fields
  ensemble_score?: number;
  method_scores?: Array<{method: string; score: number; weight: number}>;
  results?: Record<string, any>;

  // Synastry-specific
  overlays?: Record<string, any>;
  cross_aspects?: any[];
  composite_chart?: Record<string, any>;
  scoring?: Record<string, any>;

  // Timing
  elapsed_ms?: number;
}

export interface MultiMethodCompatibilityResult {
  ensemble_score: number;
  method_scores: Array<{method: string; score: number; weight: number}>;
  results: Record<string, CompatibilityResult>;
  elapsed_ms?: number;
}

export interface MultiComputeResult {
  charts: Record<string, ChartResult>;
  cross_validation?: CrossValidationResult;
  peach_blossom?: PeachBlossomResult;
  relationship_timing?: any;
  fate_modification?: FateModificationPlan;
  elapsed_ms?: number;
}

// ── Dream · 解梦 ─────────────────────────────────────────
export interface DreamMatch {
  symbol: string;
  category: string;
  score: number;
  interpretation: string;
  classic_text: string;
  matched_contexts?: string[];
  context_meanings?: string[];
}

export interface DreamResult {
  dream_text: string;
  keywords: string[];
  matches: DreamMatch[];
  summary: string;
  overall_luck: string;
}

export interface DreamCorpusStats {
  total_entries: number;
  categories: Record<string, number>;
  classic_sources: string[];
}

/** 客户端梦境匹配 (使用本地 dream engine) */
export function interpretDream(dreamText: string, topN: number = 5): Promise<DreamResult> {
  // 优先用后端 /api/knowledge/dream (如果存在), 否则本地
  return jsonFetch<DreamResult>(`${BASE}/knowledge/dream`, {
    method: "POST",
    body: JSON.stringify({ dream_text: dreamText, top_n: topN }),
  }).catch(() => {
    // 本地 fallback - 通过动态 import 调用
    return localDreamInterpret(dreamText, topN);
  });
}

/** 本地梦境匹配 (fallback) */
async function localDreamInterpret(dreamText: string, topN: number): Promise<DreamResult> {
  // 简化版 - 实际使用本地 dream engine
  // 通过 fetch 调用 /api/compute 走 dream engine
  return {
    dream_text: dreamText,
    keywords: [],
    matches: [],
    summary: "本地解梦引擎暂未启用, 请确保后端 /api/knowledge/dream 端点可用",
    overall_luck: "未知",
  };
}

/** 获取语料统计 */
export function getCorpusStats(): DreamCorpusStats {
  return {
    total_entries: 48,
    categories: {
      "天象": 6,
      "动物": 9,
      "行为": 9,
      "身体": 5,
      "物品": 7,
      "植物": 3,
      "地理": 4,
      "鬼神": 3,
      "颜色": 3,
      "天象/动物": 1,
    },
    classic_sources: ["《周公解梦》", "《梦占逸旨》", "《梦溪笔谈》"],
  };
}

// ── Knowledge · 古籍书单 ─────────────────────────────────────────
export interface BookEntry {
  title: string;
  dynasty: string;
  author: string;
  priority: number;
  difficulty: string;
  description: string;
  key_chapters: string[];
  verified_examples?: string;
  online_resources?: string[];
  book_file?: string;
  notes?: string;
}

export interface BookListResponse {
  method: string;
  books: BookEntry[];
}

export interface MethodSummary {
  total: number;
  verified: number;
  dynasties: Record<string, number>;
  method_label: string;
}

export interface KnowledgeMethodsResponse {
  methods: string[];
  labels: Record<string, string>;
  summary: Record<string, MethodSummary>;
}

/** GET /api/knowledge/methods — 返回术法列表 + 中文标签 + 摘要统计 */
export async function fetchKnowledgeMethods(): Promise<KnowledgeMethodsResponse> {
  return jsonFetch<KnowledgeMethodsResponse>(`${BASE}/knowledge/methods`);
}

/** GET /api/knowledge/books?method=...&max_priority=...&verified_only=... */
export async function fetchBooks(
  method?: string,
  opts: { maxPriority?: number; verifiedOnly?: boolean } = {},
): Promise<BookListResponse> {
  const params = new URLSearchParams();
  if (method) params.set("method", method);
  params.set("max_priority", String(opts.maxPriority ?? 3));
  if (opts.verifiedOnly) params.set("verified_only", "true");
  return jsonFetch<BookListResponse>(`${BASE}/knowledge/books?${params}`);
}

const BASE = "/api";

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!r.ok) {
    const detail = await r.text().catch(() => "");
    throw new Error(`HTTP ${r.status}: ${detail || r.statusText}`);
  }
  return r.json() as Promise<T>;
}

export async function fetchMethods(): Promise<MethodMeta[]> {
  return jsonFetch<MethodMeta[]>(`${BASE}/methods`);
}

export async function fetchPrompt(method: Method | string): Promise<{ method: string; template: string }> {
  return jsonFetch(`${BASE}/prompts/${method}`);
}

/* ── Birth-time rectification ──────────────────────────────── */
export interface RectifyCandidate {
  branch: string;
  hour: number;
  label: string;
  score: number;
  confidence: "low" | "medium" | "high";
  evidence: string[];
  chart_summary: Record<string, unknown>;
}

export interface RectifyResponse {
  status: string;
  birth_time_accuracy: string;
  candidates: RectifyCandidate[];
  best?: RectifyCandidate;
  second?: RectifyCandidate;
  confidence_level: "low" | "medium" | "high";
  next_question?: { prompt: string; options: string[] };
  common_conclusions: string[];
  main_differences: string[];
  uncertainty_note: string;
  elapsed_ms: number;
}

export interface RectifyRequest {
  birth: Birth;
  birth_time_accuracy: "exact" | "approximate" | "period" | "unknown";
  approximate_hour?: number;
  day_period?: "morning" | "afternoon" | "evening" | "night";
  known_events: Array<{ year: number; month?: number; category: string; description?: string }>;
  keep_top_n?: number;
}

export async function rectifyBirthTime(req: RectifyRequest): Promise<RectifyResponse> {
  return jsonFetch<RectifyResponse>(`${BASE}/birth-time/rectify`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function createEventCase(req: CaseCreateRequest): Promise<EventCase> {
  return jsonFetch<EventCase>(`${BASE}/cases`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function updateEventCaseContext(caseId: string, req: CaseContextRequest): Promise<EventCase> {
  return jsonFetch<EventCase>(`${BASE}/cases/${caseId}/context`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function castEventCase(
  caseId: string,
  req: CaseCastRequest,
  idempotencyKey: string,
): Promise<CastResponse> {
  return jsonFetch<CastResponse>(`${BASE}/cases/${caseId}/cast`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(req),
  });
}

export async function fetchEventCaseResult(caseId: string): Promise<CastResponse> {
  return jsonFetch<CastResponse>(`${BASE}/cases/${caseId}/result`);
}

export async function createEventCaseVersion(caseId: string, req: CaseVersionRequest): Promise<EventCase> {
  return jsonFetch<EventCase>(`${BASE}/cases/${caseId}/versions`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function computeChart(req: ComputeRequest): Promise<ChartResult> {
  return jsonFetch<ChartResult>(`${BASE}/compute`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function computeChartMulti(
  methods: Method[], birth: Birth, options?: Record<string, any>,
): Promise<Record<string, ChartResult>> {
  // Strip multi-method metadata that individual /api/compute calls don't accept
  const modeByMethod: Record<string, string> = options?.modeByMethod || {};
  const cleanBase = { ...options };
  delete cleanBase.methods;
  delete cleanBase.modeByMethod;

  const entries = await Promise.all(methods.map(async (m) => {
    // Pick the per-method mode if specified, otherwise use the generic mode or fall back to base options
    const perOptions: Record<string, any> = { ...cleanBase };
    if (modeByMethod[m]) {
      perOptions.mode = modeByMethod[m];
    }
    const c = await computeChart({ method: m, birth, options: perOptions });
    return [m, c] as const;
  }));
  return Object.fromEntries(entries) as Record<string, ChartResult>;
}

export interface DailyTarotCard {
  position: string;
  position_meaning: string;
  name: string;
  orient: string;
  keywords: string;
  seed_used: string;
}

export interface DailyPayload {
  date: string;
  today: {
    ganzhi_day: string;
    ganzhi_year: string;
    shengxiao: string;
    day_wuxing: string;
    lunar_date: string;
    jie_qi: string;
    tarot_card: DailyTarotCard;
    question_seed: string;
  };
  user?: { day_master: string; day_wuxing: string };
  interaction?: {
    relation: string;
    label: string;
    focus: string;
    action: string;
    watch: string;
    subject_hint: string;
  };
  calculation_basis: {
    method: string;
    rule_version: string;
    input_source: string;
    calendar_input: string;
    solar_date: string;
    lunar_date: string;
    jie_qi: string;
    limits: string;
  };
}

/** 多法排盘 + 交叉验证:调用 /api/compute/multi */
export async function computeMultiWithValidation(
  methods: Method[],
  birth: Birth,
  subject?: string,
  doValidate?: boolean,
): Promise<MultiComputeResult> {
  return jsonFetch<MultiComputeResult>(`${BASE}/compute/multi`, {
    method: "POST",
    body: JSON.stringify({
      methods,
      birth,
      subject: subject || "self_life",
      do_validate: doValidate ?? true,
    }),
  });
}

/** 时辰校准:调用 /api/calibrate/hour */
export async function calibrateHour(
  birth: Birth,
  knownTraits?: string[],
  knownCareer?: string,
  knownEvents?: string[],
): Promise<any> {
  return jsonFetch(`${BASE}/calibrate/hour`, {
    method: "POST",
    body: JSON.stringify({
      birth,
      known_traits: knownTraits || null,
      known_career: knownCareer || null,
      known_events: knownEvents || null,
    }),
  });
}

/** 性格反向推定时辰:调用 /api/estimate/traits */
export async function estimateTraits(traits: string[]): Promise<any> {
  return jsonFetch(`${BASE}/estimate/traits`, {
    method: "POST",
    body: JSON.stringify({ traits }),
  });
}

/** 八字合婚/兼容性:调用 /api/compatibility */
export async function computeCompatibility(
  chart1Birth: Birth,
  chart2Birth: Birth,
  method?: string,
  methods?: string[],
): Promise<CompatibilityResult> {
  const body: Record<string, any> = {
    chart1_birth: chart1Birth,
    chart2_birth: chart2Birth,
  };
  if (methods && methods.length >= 2) {
    body.methods = methods;
    body.method = methods[0];
  } else {
    body.method = method || "bazi_v2";
  }
  return jsonFetch<CompatibilityResult>(`${BASE}/compatibility`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** 多法合盘:调用 /api/compatibility with multiple methods */
export async function computeMultiCompatibility(
  chart1Birth: Birth,
  chart2Birth: Birth,
  methods: string[],
): Promise<MultiMethodCompatibilityResult> {
  return jsonFetch<MultiMethodCompatibilityResult>(`${BASE}/compatibility`, {
    method: "POST",
    body: JSON.stringify({
      chart1_birth: chart1Birth,
      chart2_birth: chart2Birth,
      methods,
      method: methods[0] || "bazi_v2",
    }),
  });
}

export async function fetchDaily(date?: string, birth?: Birth): Promise<DailyPayload> {
  if (birth) {
    return jsonFetch<DailyPayload>(`${BASE}/daily`, {
      method: "POST",
      body: JSON.stringify({ date, birth }),
    });
  }
  const qs = date ? `?date=${encodeURIComponent(date)}` : "";
  return jsonFetch<DailyPayload>(`${BASE}/daily${qs}`);
}

/** 流式解读:SSE/NDJSON 解析。返回 AsyncGenerator。 */
export async function* streamInterpret(
  payload: { charts: ChartResult[]; question?: string; client?: "mock" | "anthropic"; enhancedData?: Record<string, any> },
  signal?: AbortSignal,
): AsyncGenerator<InterpretEvent, void, void> {
  const body: Record<string, any> = { client: "mock", ...payload };
  if (payload.enhancedData) {
    body.enhanced_data = payload.enhancedData;
  }
  delete (body as any).enhancedData;
  const r = await fetch(`${BASE}/interpret`, {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok || !r.body) {
    const t = await r.text().catch(() => "");
    throw new Error(`HTTP ${r.status}: ${t.slice(0, 200)}`);
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      try {
        const j = JSON.parse(line);
        yield j as InterpretEvent;
      } catch { /* 跳过坏行 */ }
    }
  }
}

// ── 老黄历类型 ───────────────────────────────────────────────────────
export interface AlmanacPayload {
  solar_date: string;
  lunar: {
    year: number;
    month: number;
    day: number;
    is_leap: boolean;
    date_str: string;
    year_in_ganzhi: string;
    month_in_ganzhi: string;
    day_in_ganzhi: string;
    year_shengxiao: string;
    day_shengxiao: string;
  };
  ganzhi: {
    year: { full: string; gan: string; zhi: string; animal: string };
    month: { full: string; gan: string; zhi: string };
    day: { full: string; gan: string; zhi: string; animal: string };
  };
  wuxing: { day_gan: string; day_zhi: string; day_gan_color: string };
  na_yin: { day: string; year: string };
  yi_ji: { yi: string[]; ji: string[] };
  shen_sha: { ji_shen: string[]; xiong_sha: string[] };
  chong_sha: { chong: string; chong_desc: string; chong_shengxiao: string; sha: string };
  tian_shen: { name: string; type: string; luck: string };
  jian_chu: { name: string; type: string; is_huangdao: boolean };
  xing_xiu: { name: string; luck: string; song: string };
  pengzu_baiji: { gan: string; zhi: string };
  tai_shen: string;
  tai_sui: { day: string; year: string };
  yin_gui: string;
  jie_qi: string;
  jie: string;
  shu_jiu: string;
  jie_qi_note: string;
  calculation_basis: Record<string, string>;
}

export interface AlmanacMonthDay {
  solar_day: number;
  lunar_day: number;
  lunar_month: number;
  day_ganzhi: string;
  day_gan: string;
  day_wuxing: string;
  zhi_xing: string;
  is_huangdao: boolean;
  chong_shengxiao: string;
  sha: string;
  yi: string[];
  ji: string[];
  ji_shen: string[];
  xiong_sha: string[];
  jie_qi: string;
  lunar_date_short: string;
  error?: string;
}

export interface AlmanacMonthPayload {
  year: number;
  month: number;
  days: AlmanacMonthDay[];
}

/** 获取单日老黄历 */
export async function fetchAlmanac(date?: string): Promise<AlmanacPayload> {
  const qs = date ? `?date=${encodeURIComponent(date)}` : "";
  return jsonFetch<AlmanacPayload>(`${BASE}/almanac${qs}`);
}

/** 获取整月黄历概览 */
export async function fetchAlmanacMonth(year: number, month: number): Promise<AlmanacMonthPayload> {
  return jsonFetch<AlmanacMonthPayload>(`${BASE}/almanac/month?year=${year}&month=${month}`);
}

// ── Reading API ────────────────────────────────────────────────────────────

import type { ReadingResult, ReadingAPIRequest } from "./types";

/** POST /api/reading — 12 术法聚合解读。 */
export async function fetchReading(req: ReadingAPIRequest): Promise<ReadingResult> {
  return jsonFetch<ReadingResult>(`${BASE}/reading`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── Compass API ──────────────────────────────────────────────────────────────

export interface CompassReading {
  sans: string;
  direction: string;
  azimuth_deg: number;
  device: string;
  note?: string;
}

export interface CompassSession {
  session_id: string;
  direction_hint: string;
  target_sans: string;
  target_direction: string;
  samples: number[];
  readings: CompassReading[];
  result_sans: string;
  result_direction: string;
  result_azimuth: number;
  std_dev: number;
  quality: "high" | "medium" | "low";
  created_at: number;
  closed: boolean;
}

export async function createCompassSession(directionHint: string): Promise<CompassSession> {
  return jsonFetch<CompassSession>(`${BASE}/compass/sessions`, {
    method: "POST",
    body: JSON.stringify({ direction_hint: directionHint, sample_count: 5 }),
  });
}

export async function addCompassSample(
  sessionId: string, azimuthDeg: number,
): Promise<{ added: number; samples_count: number; closed: boolean }> {
  return jsonFetch(`${BASE}/compass/sessions/${sessionId}/samples`, {
    method: "POST",
    body: JSON.stringify({ azimuth_deg: azimuthDeg }),
  });
}

export async function getCompassSession(sessionId: string): Promise<CompassSession> {
  return jsonFetch<CompassSession>(`${BASE}/compass/sessions/${sessionId}`);
}

export async function convertAzimuth(
  azimuthDeg: number,
): Promise<{ azimuth_deg: number; sans: string; sans_zh: string; direction: string; trigram: string; element: string; fengshui_tip: string }> {
  return jsonFetch(`${BASE}/compass/convert/${azimuthDeg}`);
}

// ── Sprint 3.1: 三通道测量 ───────────────────────────────────────────────

export interface CompassMeasureRequest {
  magnetic_heading_deg?: number;
  physical_compass_sans?: string;
  manual_azimuth_deg?: number;
  map_direction?: string;
  lat?: number;
  lng?: number;
  declination_deg?: number;
  north_ref?: string;
  samples?: number[];
}

export interface CompassMeasureResponse {
  input_channel: string;
  raw_heading: number;
  north_ref: string;
  declination_deg: number;
  declination_source: string;
  true_heading: number;
  sans: string;
  alt_sans?: string;
  sans_zh: string;
  trigram: string;
  element: string;
  direction: string;
  dual_candidate: boolean;
  distance_to_boundary: number;
  quality: string;
  tip: string;
  fengshui_warning?: string;
}

/** POST /api/compass/measure — 三通道罗盘测量. */
export async function measureCompass(req: CompassMeasureRequest): Promise<CompassMeasureResponse> {
  return jsonFetch<CompassMeasureResponse>(`${BASE}/compass/measure`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── Sprint 3.3: 罗盘 → 风水 端到端 ─────────────────────────────────────

export interface CompassFengShuiRequest extends CompassMeasureRequest {
  birth_year: number;
  gender?: string;
  construction_year?: number;
  period?: number;
  facing?: string;
}

export interface CompassFengShuiResponse {
  sitting: string;
  sitting_zh: string;
  direction: string;
  true_heading: number;
  declination_deg: number;
  quality: string;
  dual_candidate: boolean;
  alt_sitting?: string;
  fengshui_warning?: string;
  bazhai?: Record<string, any>;
  xuankong?: Record<string, any>;
  fengshui_summary: string;
}

/** POST /api/compass/fengshui — 罗盘→风水端到端. */
export async function compassFengShui(req: CompassFengShuiRequest): Promise<CompassFengShuiResponse> {
  return jsonFetch<CompassFengShuiResponse>(`${BASE}/compass/fengshui`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ── Sprint 3.1: 24 山列表 ──────────────────────────────────────────────

export interface MountainMeta {
  sans: string;
  sans_zh: string;
  center_deg: number;
  from_deg: number;
  to_deg: number;
  trigram: string;
  element: string;
  tip: string;
}

/** GET /api/compass/24-mountains — 24 山完整元数据. */
export async function fetch24Mountains(): Promise<{ mountains: MountainMeta[]; total: number }> {
  return jsonFetch(`${BASE}/compass/24-mountains`);
}
