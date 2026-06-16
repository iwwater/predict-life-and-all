/** 各术法专属输入配置 — 前端镜像 divination/aggregation/method_inputs.py
 *  每个页面用此配置决定显示哪些表单字段
 */
import type { Method, TarotSpread } from "./types";

export interface MethodFormConfig {
  /** 方法 ID */
  id: Method;
  /** 是否需要出生信息: true=必须, false=不需要, "conditional"=某些模式需要, "minimal"=仅需年月日 */
  needsBirth: boolean | "conditional" | "minimal";
  /** 需要展示的出生字段 */
  birthFields: string[];
  /** 是否需要经纬度/时区 */
  needsLocation: boolean;
  /** 是否需要问题输入 */
  needsQuestion: boolean;
  /** 是否需要牌阵选择 (tarot/lenormand) */
  needsSpread: boolean;
  /** 是否需要坐向选择 (xuankong/bazhai) */
  needsDirection: boolean;
  /** 是否需要手动摇卦 (liuyao manual_coin) */
  needsCoinToss: boolean;
  /** 是否需要固定种子 */
  needsSeed: boolean;
  /** 是否需要名字输入 */
  needsName: boolean;
  /** 是否需要父母生肖 (tieban) */
  needsZodiac: boolean;
  /** 默认模式 */
  defaultMode: string;
  /** 可选模式列表 */
  availableModes: { value: string; label: string }[];
  /** 默认牌阵 */
  defaultSpread: TarotSpread;
  /** API options 中的额外字段 */
  extraOptions?: Record<string, any>;
}

/** 八字通用出生字段 */
const FULL_BIRTH = ["year", "month", "day", "hour", "minute", "gender", "city"];

export const METHOD_INPUT_CONFIG: Record<string, MethodFormConfig> = {
  // ── Group A: full birth ──────────────────────────────────────────────
  bazi: {
    id: "bazi",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "gender", "city"],
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "natal",
    availableModes: [
      { value: "natal", label: "本命盘" },
      { value: "annual_luck", label: "流年运" },
    ],
    defaultSpread: "single",
  },
  bazi_v2: {
    id: "bazi_v2",
    needsBirth: true,
    birthFields: FULL_BIRTH,
    needsLocation: true,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "natal",
    availableModes: [
      { value: "natal", label: "本命精算" },
      { value: "annual_luck", label: "流年精算" },
    ],
    defaultSpread: "single",
  },
  ziwei: {
    id: "ziwei",
    needsBirth: true,
    birthFields: FULL_BIRTH,
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "natal",
    availableModes: [
      { value: "natal", label: "本命盘" },
      { value: "annual", label: "流年盘" },
    ],
    defaultSpread: "single",
  },
  western: {
    id: "western",
    needsBirth: true,
    birthFields: FULL_BIRTH,
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "natal",
    availableModes: [
      { value: "natal", label: "本命盘" },
      { value: "transit", label: "行运盘" },
    ],
    defaultSpread: "single",
  },
  vedic: {
    id: "vedic",
    needsBirth: true,
    birthFields: FULL_BIRTH,
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "natal",
    availableModes: [
      { value: "natal", label: "本命盘" },
      { value: "dasha", label: "大运流年" },
    ],
    defaultSpread: "single",
  },
  qimen: {
    id: "qimen",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "city"],
    needsLocation: true,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "hour_qimen",
    availableModes: [
      { value: "hour_qimen", label: "时家奇门" },
      { value: "minute_qimen", label: "刻家奇门" },
    ],
    defaultSpread: "single",
  },

  // ── Group B: basic birth (no lat/lng) ────────────────────────────────
  chenggu: {
    id: "chenggu",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "gender"],
    needsLocation: false,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "chenggu",
    availableModes: [{ value: "chenggu", label: "称骨算" }],
    defaultSpread: "single",
  },
  liuren: {
    id: "liuren",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "gender"],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "liuren_divination",
    availableModes: [{ value: "liuren_divination", label: "占卜" }],
    defaultSpread: "single",
  },
  tieban: {
    id: "tieban",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "gender", "city"],
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: true,
    defaultMode: "tieban_base",
    availableModes: [{ value: "tieban_base", label: "铁板条文" }],
    defaultSpread: "single",
  },

  // ── Group C: no birth, card/spread ───────────────────────────────────
  tarot: {
    id: "tarot",
    needsBirth: false,
    birthFields: [],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: true,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: true,
    needsName: false,
    needsZodiac: false,
    defaultMode: "reflective",
    availableModes: [
      { value: "reflective", label: "自省" },
      { value: "quick", label: "快速" },
      { value: "deep", label: "深探" },
    ],
    defaultSpread: "celtic_cross",
  },
  lenormand: {
    id: "lenormand",
    needsBirth: false,
    birthFields: [],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: true,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: true,
    needsName: false,
    needsZodiac: false,
    defaultMode: "lenormand_spread",
    availableModes: [{ value: "lenormand_spread", label: "雷诺曼" }],
    defaultSpread: "three_line",
  },

  // ── Group D: no birth, coin/seed ─────────────────────────────────────
  liuyao: {
    id: "liuyao",
    needsBirth: "conditional" as const,
    birthFields: ["year", "month", "day", "hour", "minute", "gender"],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: true,
    needsSeed: true,
    needsName: false,
    needsZodiac: false,
    defaultMode: "time_qigua",
    availableModes: [
      { value: "time_qigua", label: "时间起卦" },
      { value: "manual_coin", label: "手动摇卦" },
      { value: "number_qigua", label: "数字起卦" },
    ],
    defaultSpread: "single",
  },
  meihua: {
    id: "meihua",
    needsBirth: "conditional" as const,
    birthFields: ["year", "month", "day", "hour", "minute", "gender"],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: true,
    needsName: false,
    needsZodiac: false,
    defaultMode: "time_qigua",
    availableModes: [
      { value: "time_qigua", label: "时间起卦" },
      { value: "number_qigua", label: "数字起卦" },
      { value: "external_omen", label: "外应起卦" },
    ],
    defaultSpread: "single",
  },

  // ── Group E: no birth, space only ────────────────────────────────────
  xuankong: {
    id: "xuankong",
    needsBirth: false,
    birthFields: [],
    needsLocation: false,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: true,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "residential_xuankong",
    availableModes: [{ value: "residential_xuankong", label: "住宅玄空" }],
    defaultSpread: "single",
    extraOptions: { period: 8 },
  },

  // ── Group F: birth + space ───────────────────────────────────────────
  bazhai: {
    id: "bazhai",
    needsBirth: true,
    birthFields: ["year", "month", "day", "hour", "minute", "gender", "city"],
    needsLocation: true,
    needsQuestion: false,
    needsSpread: false,
    needsDirection: true,
    needsCoinToss: false,
    needsSeed: false,
    needsName: false,
    needsZodiac: false,
    defaultMode: "residential_bazhai",
    availableModes: [{ value: "residential_bazhai", label: "住宅八宅" }],
    defaultSpread: "single",
  },

  // ── Group G: minimal birth ───────────────────────────────────────────
  numerology: {
    id: "numerology",
    needsBirth: "minimal" as const,
    birthFields: ["year", "month", "day"],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: false,
    needsName: true,
    needsZodiac: false,
    defaultMode: "numerology",
    availableModes: [
      { value: "numerology", label: "生命灵数" },
      { value: "year_cycle", label: "流年运" },
    ],
    defaultSpread: "single",
  },

  // ── Group H: 小六壬 ────────────────────────────────────────────────
  xiaoliuren: {
    id: "xiaoliuren",
    needsBirth: "conditional" as const,
    birthFields: ["month", "day", "hour"],
    needsLocation: false,
    needsQuestion: true,
    needsSpread: false,
    needsDirection: false,
    needsCoinToss: false,
    needsSeed: true,
    needsName: false,
    needsZodiac: false,
    defaultMode: "time_xiaoliuren",
    availableModes: [
      { value: "time_xiaoliuren", label: "月日时掌诀" },
      { value: "number_xiaoliuren", label: "数字掌诀" },
    ],
    defaultSpread: "single",
  },
};

/** 获取默认空 Birth 对象（用于不需要生辰的术法） */
export function emptyBirth() {
  return {
    year: 2000, month: 1, day: 1,
    hour: 12, minute: 0,
    gender: "unspecified" as const,
    calendar: "gregorian" as const,
    lat: null as number | null, lng: null as number | null,
    tz: "Asia/Shanghai",
    is_leap_month: false,
  };
}
