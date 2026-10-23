/**
 * 方法注册表 — 单一真源 (Single Source of Truth)
 *
 * 这里定义每个术数方法的「身份」: 名称 / 分类 / 页面路径。
 * 消费方 (Home 卡片、Layout 面包屑、types.ts 报告标签) 一律从这里派生,
 * 新增方法只改这一个文件。内容文案在 method-info.ts (METHOD_PLAIN),
 * 表单定义在 method-inputs.ts — 那两层引用此处的 id, 不重复身份。
 */
import type { Method, MethodMeta, School } from "./types";

export interface MethodIdentity {
  id: Method;
  /** 全名, 用于面包屑与大标题 (八字四柱) */
  name_zh: string;
  /** 短名, 用于报告内联标签 (八字) */
  short_zh: string;
  name_en: string;
  school: School;
  /** 五术分类角标 */
  category: string;
  /** 专页路由 */
  pagePath: string;
}

export const METHOD_REGISTRY: MethodIdentity[] = [
  { id: "bazi", name_zh: "八字四柱", short_zh: "八字", name_en: "Four Pillars", school: "east", category: "命 · Ming", pagePath: "/m/bazi" },
  { id: "ziwei", name_zh: "紫微斗数", short_zh: "紫微", name_en: "Zi Wei Dou Shu", school: "east", category: "命 · Ming", pagePath: "/m/ziwei" },
  { id: "tieban", name_zh: "铁板神数", short_zh: "铁板", name_en: "Iron Plate Numbers", school: "east", category: "命 · Ming", pagePath: "/m/tieban" },
  { id: "chenggu", name_zh: "称骨", short_zh: "称骨", name_en: "Bone Weight", school: "east", category: "命 · Ming", pagePath: "/m/chenggu" },
  { id: "qimen", name_zh: "奇门遁甲", short_zh: "奇门", name_en: "Qi Men Dun Jia", school: "east", category: "卜 · Divination", pagePath: "/m/qimen" },
  { id: "liuyao", name_zh: "六爻", short_zh: "六爻", name_en: "Six Lines", school: "east", category: "卜 · Divination", pagePath: "/m/liuyao" },
  { id: "meihua", name_zh: "梅花易数", short_zh: "梅花", name_en: "Plum Blossom", school: "east", category: "卜 · Divination", pagePath: "/m/meihua" },
  { id: "liuren", name_zh: "大六壬", short_zh: "大六壬", name_en: "Da Liu Ren", school: "east", category: "卜 · Divination", pagePath: "/m/liuren" },
  { id: "xiaoliuren", name_zh: "小六壬", short_zh: "小六壬", name_en: "Xiao Liu Ren", school: "east", category: "卜 · Divination", pagePath: "/m/xiaoliuren" },
  { id: "qian", name_zh: "灵签", short_zh: "灵签", name_en: "Qian Oracle", school: "east", category: "卜 · Divination", pagePath: "/m/qian" },
  { id: "hepan", name_zh: "合盘", short_zh: "合盘", name_en: "Synastry", school: "east", category: "相 · Physiognomy", pagePath: "/m/hepan" },
  { id: "western", name_zh: "西方占星", short_zh: "西方占星", name_en: "Natal Astrology", school: "west", category: "相 · Physiognomy", pagePath: "/m/western" },
  { id: "vedic", name_zh: "吠陀占星", short_zh: "吠陀占星", name_en: "Vedic Astrology", school: "west", category: "相 · Physiognomy", pagePath: "/m/vedic" },
  { id: "numerology", name_zh: "数字命理", short_zh: "数字命理", name_en: "Numerology", school: "west", category: "相 · Physiognomy", pagePath: "/m/numerology" },
  { id: "tarot", name_zh: "塔罗", short_zh: "塔罗", name_en: "Tarot", school: "west", category: "相 · Physiognomy", pagePath: "/m/tarot" },
  { id: "lenormand", name_zh: "雷诺曼", short_zh: "雷诺曼", name_en: "Lenormand", school: "west", category: "相 · Physiognomy", pagePath: "/m/lenormand" },
  { id: "bazhai", name_zh: "八宅", short_zh: "八宅", name_en: "Eight Mansions", school: "east", category: "山 · Feng Shui", pagePath: "/m/bazhai" },
  { id: "xuankong", name_zh: "玄空飞星", short_zh: "玄空", name_en: "Flying Stars", school: "east", category: "山 · Feng Shui", pagePath: "/m/xuankong" },
  { id: "dream", name_zh: "周公解梦", short_zh: "解梦", name_en: "Dream Interpretation", school: "east", category: "杂 · Misc", pagePath: "/m/dream" },
];

/** id → 身份 */
export const METHOD_BY_ID = Object.fromEntries(METHOD_REGISTRY.map((m) => [m.id, m])) as Record<string, MethodIdentity>;

/** 面包屑全名映射 (id → name_zh) */
export const METHOD_NAME_ZH_BY_ID = Object.fromEntries(METHOD_REGISTRY.map((m) => [m.id, m.name_zh])) as Record<string, string>;

/** 无专页、但会出现在报告/合参里的方法标签 */
export const EXTRA_REPORT_LABELS: Record<string, string> = {
  bazi_v2: "八字",
  cross_validator: "交叉验证",
  hour_calibrator: "时辰校准",
  compatibility: "合盘",
  fengshui: "风水",
  shicao: "筮草",
};

/** 报告内联短名标签 (id → short_zh + 无页方法兜底) */
export const METHOD_SHORT_ZH_BY_ID: Record<string, string> = {
  ...Object.fromEntries(METHOD_REGISTRY.map((m) => [m.id, m.short_zh])),
  ...EXTRA_REPORT_LABELS,
};

/** 分类角标 (id → category) */
export const CATEGORY_BY_ID = Object.fromEntries(METHOD_REGISTRY.map((m) => [m.id, m.category])) as Record<string, string>;

/** fetchMethods 失败时的兜底卡片数据 — 由注册表派生 */
export const FALLBACK_METHOD_META: MethodMeta[] = METHOD_REGISTRY.map((m) =>
  m.id === "dream"
    ? ({
        id: m.id,
        name_zh: m.name_zh,
        name_en: m.name_en,
        school: m.school,
        group: "杂·Misc",
        needs: ["dream_text"],
        engine: "self(周公解梦)",
      } as MethodMeta)
    : ({
        id: m.id,
        name_zh: m.name_zh,
        name_en: m.name_en,
        school: m.school,
      } as MethodMeta),
);
