/** DreamPage — 周公解梦专页
 *  设计要点: 新中式 / 宣纸墨色 / 折叠梦境条目
 *  闭环: 输入梦境 → 关键词提取 → Top N 匹配 → 经典解读 → 文献出处
 *  v2: 历史梦境记录(localStorage) + 加载骨架 + 错误重试
 */
import { useState, useCallback, useEffect, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { interpretDream, getCorpusStats, type DreamMatch } from "../lib/api";
import { MethodSourcesPanel } from "../components/MethodSourcesPanel";

type DreamResult = {
  dream_text: string;
  keywords: string[];
  matches: DreamMatch[];
  summary: string;
  overall_luck: string;
};

const HISTORY_KEY = "mystic:dream-history";
const MAX_HISTORY = 8;

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.slice(0, MAX_HISTORY) : [];
  } catch {
    return [];
  }
}

function saveHistory(text: string) {
  try {
    const cur = loadHistory();
    const next = [text, ...cur.filter((t) => t !== text)].slice(0, MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
  } catch {
    /* 忽略 quota 错误 */
  }
}

function clearHistory() {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    /* 忽略 */
  }
}

const EXAMPLE_DREAMS = [
  "我梦见一条龙在天上飞",
  "梦见自己牙齿脱落",
  "梦见大水涌来,差点被淹",
  "梦中骑马奔驰,心情愉悦",
  "梦见佛祖对我微笑",
  "梦见白色的花朵盛开",
];

export function DreamPage() {
  const [dreamText, setDreamText] = useState("");
  const [result, setResult] = useState<DreamResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openMatchIdx, setOpenMatchIdx] = useState<number | null>(0);
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const stats = getCorpusStats();

  const submit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const trimmed = dreamText.trim();
      if (!trimmed) {
        setError("请输入梦境描述");
        return;
      }
      if (trimmed.length < 4) {
        setError("梦境描述至少 4 个字");
        return;
      }
      setError(null);
      setLoading(true);
      try {
        const r = await interpretDream(trimmed, 5);
        setResult(r as DreamResult);
        saveHistory(trimmed);
        setHistory(loadHistory());
        setOpenMatchIdx(0);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    },
    [dreamText],
  );

  const useExample = (text: string) => {
    setDreamText(text);
    setError(null);
  };

  const useHistory = (text: string) => {
    setDreamText(text);
    setError(null);
    setResult(null);
  };

  const handleClearHistory = () => {
    clearHistory();
    setHistory([]);
  };

  const luckColor = (luck: string) => {
    if (luck.includes("大吉")) return "var(--verdigris)";
    if (luck.includes("吉")) return "#4FB3A0";
    if (luck.includes("凶")) return "var(--cinnabar)";
    return "var(--ink-soft)";
  };

  return (
    <div className="space-y-5">
      <header>
        <h1 className="paper-title">
          <span className="stamp" />周公解梦
        </h1>
        <p style={{ fontSize: "0.92rem", color: "var(--ink-soft)", marginTop: "0.3rem", lineHeight: 1.7 }}>
          输入梦境描述 · 基于《周公解梦》《梦占逸旨》《梦溪笔谈》自动匹配解读
        </p>
        <div style={{ fontSize: "0.78rem", color: "var(--ink-soft)", marginTop: "0.3rem", opacity: 0.85 }}>
          收录 <strong style={{ color: "var(--cinnabar)" }}>{stats.total_entries}</strong> 条梦境 ·
          {" "}{Object.keys(stats.categories).length} 大类 ·
          {" "}{stats.classic_sources.length} 部古典文献
        </div>
      </header>

      <form onSubmit={submit} className="paper-frame space-y-3" style={{ padding: "0.85rem" }}>
        <label className="paper-label">梦境描述</label>
        <textarea
          className="paper-input"
          value={dreamText}
          onChange={(e) => setDreamText(e.target.value)}
          placeholder="例如: 我梦见一条龙在天上飞, 然后下起了大雨..."
          rows={4}
          style={{
            width: "100%",
            resize: "vertical",
            minHeight: 96,
            fontFamily: "inherit",
            fontSize: "0.95rem",
            lineHeight: 1.7,
            padding: "0.6rem 0.8rem",
          }}
        />

        {/* 示例梦境快捷填充 */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
          <span style={{ fontSize: "0.74rem", color: "var(--ink-soft)", alignSelf: "center", marginRight: "0.2rem" }}>
            示例:
          </span>
          {EXAMPLE_DREAMS.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => useExample(ex)}
              disabled={loading}
              style={{
                fontSize: "0.78rem",
                padding: "0.18rem 0.55rem",
                background: "transparent",
                border: "1px solid var(--rule)",
                borderRadius: "0.18rem",
                color: "var(--ink-soft)",
                cursor: loading ? "wait" : "pointer",
                fontFamily: "inherit",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--cinnabar)";
                e.currentTarget.style.color = "var(--cinnabar)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--rule)";
                e.currentTarget.style.color = "var(--ink-soft)";
              }}
            >
              {ex.length > 14 ? `${ex.slice(0, 12)}…` : ex}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="submit"
            disabled={loading}
            className="paper-tag"
            style={{
              fontSize: "0.92rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
              padding: "0.55rem 1.3rem",
              background: loading ? "var(--ink-soft)" : "var(--cinnabar)",
              color: "var(--paper)",
              borderColor: loading ? "var(--ink-soft)" : "var(--cinnabar)",
              letterSpacing: "0.15em",
            }}
          >
            {loading ? (
              <>
                <span className="paper-pulse" style={{ marginRight: "0.4rem", verticalAlign: "middle" }} />
                解读中…
              </>
            ) : (
              <>🔮 开始解梦</>
            )}
          </button>
          <span style={{ fontSize: "0.76rem", color: "var(--ink-soft)", opacity: 0.85 }}>
            提示: 描述具体事物（如动物、物品、行为）效果更佳
          </span>
        </div>

        {error && (
          <div
            className="paper-grid-cell"
            style={{
              padding: "0.6rem 0.85rem",
              borderColor: "rgba(176,58,46,0.3)",
              color: "var(--cinnabar)",
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.5rem",
            }}
          >
            <span>⚠ {error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              style={{
                background: "transparent",
                border: "1px solid var(--cinnabar)",
                color: "var(--cinnabar)",
                padding: "0.15rem 0.55rem",
                fontSize: "0.78rem",
                cursor: "pointer",
                borderRadius: "0.15rem",
                fontFamily: "inherit",
              }}
            >
              关闭
            </button>
          </div>
        )}
      </form>

      {/* 历史梦境记录 */}
      {history.length > 0 && (
        <section className="paper-frame" style={{ padding: "0.85rem" }}>
          <div className="flex items-center justify-between mb-2">
            <h3 className="paper-eyebrow" style={{ color: "var(--ink-soft)" }}>
              最近的梦境
            </h3>
            <button
              type="button"
              onClick={handleClearHistory}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--ink-soft)",
                fontSize: "0.74rem",
                cursor: "pointer",
                fontFamily: "inherit",
                textDecoration: "underline",
                textUnderlineOffset: "3px",
              }}
            >
              清空
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            {history.map((h, i) => (
              <button
                key={`${h}-${i}`}
                type="button"
                onClick={() => useHistory(h)}
                style={{
                  background: "transparent",
                  border: "1px solid var(--rule)",
                  padding: "0.45rem 0.7rem",
                  textAlign: "left",
                  fontFamily: "inherit",
                  fontSize: "0.86rem",
                  color: "var(--ink)",
                  cursor: "pointer",
                  borderRadius: "0.18rem",
                  transition: "all 0.2s ease",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--paper-2)";
                  e.currentTarget.style.borderColor = "var(--cinnabar)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.borderColor = "var(--rule)";
                }}
                title={h}
              >
                {h.length > 50 ? `${h.slice(0, 48)}…` : h}
              </button>
            ))}
          </div>
        </section>
      )}

      {loading && (
        <div className="space-y-3 animate-fade-in">
          <section className="paper-frame" style={{ padding: "0.85rem" }}>
            <div className="flex items-center gap-3">
              <span className="paper-pulse" />
              <span style={{ fontSize: "0.92rem", color: "var(--ink-soft)" }}>
                正在检索 {stats.total_entries} 条古籍梦境…
              </span>
            </div>
            {/* 加载骨架 */}
            <div style={{ marginTop: "0.8rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    height: "3.4rem",
                    background: "linear-gradient(90deg, var(--paper-2), var(--paper), var(--paper-2))",
                    backgroundSize: "200% 100%",
                    animation: "ink-pulse 1.6s ease-in-out infinite",
                    borderRadius: "0.2rem",
                    opacity: 0.6,
                  }}
                />
              ))}
            </div>
          </section>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-3 animate-fade-in">
          {/* 综合摘要 */}
          <section className="paper-frame" style={{ padding: "0.85rem" }}>
            <div className="flex items-baseline gap-3 flex-wrap">
              <h3
                className="paper-eyebrow"
                style={{
                  color: luckColor(result.overall_luck),
                  fontSize: "0.95rem",
                  letterSpacing: "0.2em",
                }}
              >
                {result.overall_luck}
              </h3>
              <span style={{ fontSize: "0.78rem", color: "var(--ink-soft)", opacity: 0.85 }}>
                关键词: {result.keywords.slice(0, 6).join(" · ") || "无"}
              </span>
            </div>
            <p style={{ fontSize: "0.95rem", marginTop: "0.55rem", lineHeight: 1.85 }}>{result.summary}</p>
          </section>

          {/* Top N 匹配 */}
          {result.matches.length === 0 ? (
            <section className="paper-empty">
              <p style={{ fontSize: "0.92rem" }}>
                未匹配到已收录的梦境符号。建议尝试更具体的描述（如提及动物、物品、行为、颜色）。
              </p>
              <div style={{ marginTop: "0.8rem", display: "flex", flexWrap: "wrap", gap: "0.4rem", justifyContent: "center" }}>
                {EXAMPLE_DREAMS.slice(0, 3).map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => useExample(ex)}
                    style={{
                      fontSize: "0.82rem",
                      padding: "0.3rem 0.7rem",
                      background: "transparent",
                      border: "1px solid var(--rule)",
                      borderRadius: "0.2rem",
                      color: "var(--ink-soft)",
                      cursor: "pointer",
                      fontFamily: "inherit",
                    }}
                  >
                    试试: {ex}
                  </button>
                ))}
              </div>
            </section>
          ) : (
            result.matches.map((m, i) => {
              const open = openMatchIdx === i;
              return (
                <div key={`${m.symbol}-${i}`} className="paper-frame" style={{ padding: "0.85rem" }}>
                  <button
                    type="button"
                    onClick={() => setOpenMatchIdx(open ? null : i)}
                    className="w-full text-left flex items-start justify-between gap-3"
                    style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
                  >
                    <div className="flex-1">
                      <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", flexWrap: "wrap" }}>
                        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, fontFamily: "'Noto Serif SC', serif", color: "var(--ink)" }}>
                          {m.symbol}
                        </h3>
                        <span style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
                          {m.category}
                        </span>
                        <span style={{ fontSize: "0.7rem", color: luckColor(result.overall_luck) }}>
                          匹配度 {(m.score * 100).toFixed(0)}%
                        </span>
                        {m.matched_contexts && m.matched_contexts.length > 0 && (
                          <span style={{ fontSize: "0.65rem", color: "var(--verdigris)", border: "1px solid var(--verdigris)", padding: "0 0.3rem", borderRadius: "0.2rem" }}>
                            ✓ 情境匹配
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)", marginTop: "0.2rem" }}>
                        出处: {m.classic_text}
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: "0.9rem",
                        color: "var(--ink-soft)",
                        flexShrink: 0,
                        transition: "transform 0.2s",
                        transform: open ? "rotate(180deg)" : "none",
                      }}
                    >
                      ▾
                    </span>
                  </button>

                  {open && (
                    <div className="animate-fade-in" style={{ marginTop: "0.65rem", fontSize: "0.83rem", lineHeight: 1.7 }}>
                      <p style={{ marginBottom: "0.6rem" }}>{m.interpretation}</p>

                      {m.context_meanings && m.context_meanings.length > 0 && (
                        <div style={{ marginBottom: "0.5rem" }}>
                          <div style={{ fontSize: "0.7rem", color: "var(--cinnabar)", opacity: 0.8, marginBottom: "0.3rem" }}>
                            ▸ 情境解读
                          </div>
                          {m.context_meanings.map((cm: string, j: number) => (
                            <div
                              key={j}
                              className="paper-grid-cell"
                              style={{ padding: "0.4rem 0.6rem", marginBottom: "0.3rem", fontSize: "0.78rem", borderLeft: "2px solid var(--verdigris)" }}
                            >
                              <span style={{ fontFamily: "'Noto Serif SC', serif", color: "var(--ink)" }}>
                                {m.matched_contexts?.[j] ?? ""}
                              </span>
                              <span style={{ color: "var(--ink-soft)", marginLeft: "0.5rem" }}>{cm}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontStyle: "italic", marginTop: "0.5rem", borderLeft: "2px solid var(--rule)", paddingLeft: "0.5rem" }}>
                        ⚠ 本解读基于古典文献, 仅供文化参考与娱乐。
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 免责声明 */}
      <div
        className="paper-grid-cell"
        style={{
          padding: "0.6rem 0.85rem",
          fontSize: "0.68rem",
          color: "var(--ink-soft)",
          lineHeight: 1.7,
        }}
      >
        <strong style={{ color: "var(--cinnabar)" }}>⚖ 版权与免责：</strong>
        解梦数据整理自公共领域古籍（《周公解梦》《梦占逸旨》《梦溪笔谈》）,
        仅供文化研究与娱乐参考。
        梦境与现实无科学因果关系, 重要决策请勿依赖梦境解读。
      </div>

      {/* 文献出处 */}
      <MethodSourcesPanel method="dream" />
    </div>
  );
}
