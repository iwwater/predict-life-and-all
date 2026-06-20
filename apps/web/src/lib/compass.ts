// 8 方位 + 24 山(玄空/八宅)映射
// 用户用大白话选「我家大门朝正东」,系统自动转出「卯山 / 震卦」等专业术语,并在旁边用人话解释
// 24 山按 15° 切分;8 方位按 45° 切分,每个 45° 扇区里我们给一个最常用的山
import { SANS_24 } from "./types";

export interface DirectionChoice {
  code: string;          // 「正东」
  range: string;         // 「67.5° – 112.5°」
  sans: string;          // 24 山里的代表(给后端)
  trigram: string;       // 8 卦
  element: string;       // 五行
  hint: string;          // 一句白话(适合啥/避免啥)
}

export const DIRECTIONS_8: DirectionChoice[] = [
  { code: "正北", range: "337.5° – 22.5°",   sans: "子", trigram: "坎", element: "水", hint: "正北方,五行属水,主智慧与事业运" },
  { code: "东北", range: "22.5° – 67.5°",    sans: "艮", trigram: "艮", element: "土", hint: "东北方,五行属土,主稳定与停止(家宅最忌艮位动)" },
  { code: "正东", range: "67.5° – 112.5°",   sans: "卯", trigram: "震", element: "木", hint: "正东方,五行属木,主成长与家庭(传统认为最宜作大门)" },
  { code: "东南", range: "112.5° – 157.5°",  sans: "巽", trigram: "巽", element: "木", hint: "东南方,五行属木,主文昌与学业" },
  { code: "正南", range: "157.5° – 202.5°",  sans: "午", trigram: "离", element: "火", hint: "正南方,五行属火,主名声与心火" },
  { code: "西南", range: "202.5° – 247.5°",  sans: "坤", trigram: "坤", element: "土", hint: "西南方,五行属土,女主位,主家庭与健康" },
  { code: "正西", range: "247.5° – 292.5°",  sans: "酉", trigram: "兑", element: "金", hint: "正西方,五行属金,主口才与喜悦" },
  { code: "西北", range: "292.5° – 337.5°",  sans: "乾", trigram: "乾", element: "金", hint: "西北方,五行属金,男主位,主事业与权威" },
];

// 24 山全表(给后端 sitting 字段用)
export { SANS_24 };

/** 24 山中心角度 (每山 15°, 子山为 0°) */
export const SANS_CENTER_DEG: Record<string, number> = {};
SANS_24.forEach((sans, i) => { SANS_CENTER_DEG[sans] = (i * 15 + 352.5) % 360; });

/** 24 山八卦映射 */
export const SANS_TRIGRAM: Record<string, string> = {
  壬: "坎", 子: "坎", 癸: "坎",
  丑: "艮", 艮: "艮", 寅: "艮",
  甲: "震", 卯: "震", 乙: "震",
  辰: "巽", 巽: "巽", 巳: "巽",
  丙: "离", 午: "离", 丁: "离",
  未: "坤", 坤: "坤", 申: "坤",
  庚: "兑", 酉: "兑", 辛: "兑",
  戌: "乾", 乾: "乾", 亥: "乾",
};

/** 24 山五行映射 */
export const SANS_ELEMENT: Record<string, string> = {
  壬: "水", 子: "水", 癸: "水",
  丑: "土", 艮: "土", 寅: "土",
  甲: "木", 卯: "木", 乙: "木",
  辰: "土", 巽: "木", 巳: "火",
  丙: "火", 午: "火", 丁: "火",
  未: "土", 坤: "土", 申: "金",
  庚: "金", 酉: "金", 辛: "金",
  戌: "土", 乾: "金", 亥: "水",
};

/** 24 山阴阳映射 */
export const SANS_YINYANG: Record<string, string> = {
  壬: "阳", 子: "阳", 癸: "阴",
  丑: "阴", 艮: "阳", 寅: "阳",
  甲: "阳", 卯: "阴", 乙: "阴",
  辰: "阳", 巽: "阴", 巳: "阴",
  丙: "阳", 午: "阳", 丁: "阴",
  未: "阴", 坤: "阳", 申: "阳",
  庚: "阳", 酉: "阴", 辛: "阴",
  戌: "阳", 乾: "阳", 亥: "阴",
};

/** 边界检测结果 */
export interface BoundaryCheck {
  sans: string;
  center_deg: number;
  distance_to_boundary: number;
  is_near_boundary: boolean;
  alternative_sans?: string;
}

/** 检测给定角度是否在 24 山边界附近 (<5°) */
export function checkBoundary(deg: number): BoundaryCheck {
  const normalized = ((deg % 360) + 360) % 360;
  const idx = Math.round(((normalized - 352.5 + 360) % 360) / 15) % 24;
  const sans = SANS_24[idx];
  const center = SANS_CENTER_DEG[sans] ?? 0;
  const halfWidth = 7.5;
  const dist = Math.abs(((normalized - center + 540) % 360) - 180);
  const isNear = dist > (halfWidth - 5);
  const result: BoundaryCheck = {
    sans,
    center_deg: center,
    distance_to_boundary: halfWidth - dist,
    is_near_boundary: isNear,
  };
  if (isNear) {
    const altIdx = normalized > center ? (idx + 1) % 24 : (idx - 1 + 24) % 24;
    result.alternative_sans = SANS_24[altIdx];
  }
  return result;
}

// 根据 24 山字符反查描述(简版,后端拿到后再让 engines 算)
export function describeSans(sans: string): string {
  const idx = SANS_24.indexOf(sans as any);
  if (idx < 0) return sans;
  const map: Record<string, string> = {
    "子": "正北,玄空称子山",
    "癸": "北偏东,玄空称癸山",
    "丑": "东北偏北,玄空称丑山",
    "艮": "东北正中,玄空称艮山",
    "寅": "东北偏东,玄空称寅山",
    "甲": "东偏北,玄空称甲山",
    "卯": "正东,玄空称卯山",
    "乙": "东偏南,玄空称乙山",
    "辰": "东南偏东,玄空称辰山",
    "巽": "东南正中,玄空称巽山",
    "巳": "东南偏南,玄空称巳山",
    "丙": "南偏东,玄空称丙山",
    "午": "正南,玄空称午山",
    "丁": "南偏西,玄空称丁山",
    "未": "西南偏南,玄空称未山",
    "坤": "西南正中,玄空称坤山",
    "申": "西南偏西,玄空称申山",
    "庚": "西偏南,玄空称庚山",
    "酉": "正西,玄空称酉山",
    "辛": "西偏北,玄空称辛山",
    "戌": "西北偏西,玄空称戌山",
    "乾": "西北正中,玄空称乾山",
    "亥": "西北偏北,玄空称亥山",
    "壬": "北偏西,玄空称壬山",
  };
  return map[sans] || sans;
}
