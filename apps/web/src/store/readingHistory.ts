/** Reading history store (EXP-001~008).
 *
 * EXP-001: 保存 ReadingResult 到 localStorage
 * EXP-002: 用户可以查看历史报告
 * EXP-007: 历史报告可重新打开（保留 reading_id）
 * EXP-008: 历史报告可删除
 */
import type { ReadingResult } from "../lib/types";

const STORAGE_KEY = "mystic_hub_reading_history";
const MAX_HISTORY = 50;

export interface HistoryEntry {
  id: string;           // reading_id = session_id
  savedAt: string;      // ISO timestamp
  question: string;     // from intent
  goal: string;         // intent goal
  goalLabel: string;    // intent goal_label
  score: number;        // overall_score
  result: ReadingResult;
}

export function saveReadingToHistory(result: ReadingResult): void {
  try {
    const history = loadHistory();
    const entry: HistoryEntry = {
      id: result.session_id,
      savedAt: new Date().toISOString(),
      question: result.intent?.question || result.intent?.goal_label || "",
      goal: result.intent?.goal || "general_life",
      goalLabel: result.intent?.goal_label || "综合",
      score: result.validation?.overall_score || 50,
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
