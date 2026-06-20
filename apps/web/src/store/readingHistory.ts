/** Reading history store (EXP-001~008).
 *
 * EXP-001: 保存 ReadingResult 到 localStorage
 * EXP-002: 用户可以查看历史报告
 * EXP-007: 历史报告可重新打开(保留 reading_id)
 * EXP-008: 历史报告可删除
 *
 * Sprint 0.1 适配: history entry 不再保存 overall_score 数字,
 * 改为保存整体基调 tone(由 tally_by_scope 累计推得, 与后端 _tone_level 同口径)。
 */
import type { ReadingResult, ScopeTally, Tone } from "../lib/types";

const STORAGE_KEY = "mystic_hub_reading_history";
const MAX_HISTORY = 50;

export interface HistoryEntry {
  id: string;           // reading_id = session_id
  savedAt: string;      // ISO timestamp
  question: string;     // from intent
  goal: string;         // intent goal
  goalLabel: string;    // intent goal_label
  /** 整体基调(替代旧 overall_score 0-100 数字) */
  tone: Tone;
  result: ReadingResult;
}

/** 由 tally_by_scope 累计计票推断整体基调(对齐后端 _tone_level 口径)。
 *  very_positive : sup >= 3 且 warn == 0
 *  positive      : sup >  warn 且 warn == 0
 *  cautious      : warn >= 3 且 sup == 0
 *  negative      : warn >  sup 且 sup == 0
 *  mixed         : 双方均有
 *  neutral       : 双方均 0
 */
export function computeTone(
  tallyByScope: Record<string, ScopeTally> | undefined | null,
): Tone {
  if (!tallyByScope) return "neutral";
  let sup = 0;
  let warn = 0;
  for (const t of Object.values(tallyByScope)) {
    sup += (t.strong_support || 0) + (t.weak_support || 0);
    warn += (t.strong_warn || 0) + (t.weak_warn || 0);
  }
  if (sup === 0 && warn === 0) return "neutral";
  if (sup >= 3 && warn === 0) return "very_positive";
  if (warn >= 3 && sup === 0) return "cautious";
  if (sup > warn && warn === 0) return "positive";
  if (warn > sup && sup === 0) return "negative";
  return "mixed";
}

export function saveReadingToHistory(result: ReadingResult): void {
  try {
    const history = loadHistory();
    const tally = result.validation?.tally_by_scope;
    // 优先用后端给的 tone,否则前端按 tally 自己算
    const tone: Tone =
      (result.validation?.tone as Tone | undefined) ??
      computeTone(tally);
    const entry: HistoryEntry = {
      id: result.session_id,
      savedAt: new Date().toISOString(),
      question: result.intent?.question || result.intent?.goal_label || "",
      goal: result.intent?.goal || "general_life",
      goalLabel: result.intent?.goal_label || "综合",
      tone,
      result,
    };

    // Remove duplicate if exists
    const filtered = history.filter((h) => h.id !== entry.id);
    filtered.unshift(entry);

    // Keep max 50 entries
    const trimmed = filtered.slice(0, MAX_HISTORY);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage full or unavailable — silent fail
  }
}

export function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as HistoryEntry[];
  } catch {
    return [];
  }
}

export function getReadingById(id: string): HistoryEntry | null {
  const history = loadHistory();
  return history.find((h) => h.id === id) || null;
}

export function deleteReadingFromHistory(id: string): void {
  try {
    const history = loadHistory();
    const filtered = history.filter((h) => h.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch {
    // silent fail
  }
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // silent fail
  }
}
