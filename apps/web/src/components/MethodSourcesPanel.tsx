/** MethodSourcesPanel — 各专页"文献出处"折叠面板
 *
 * Props:
 *   method       术法标识 ("bazi" / "ziwei" / ...)
 *   maxPriority  最大优先级 (1=必修, 2=进阶, 3=拓展). 默认 2.
 *
 * Fetches GET /api/knowledge/books?method=...&max_priority=...
 * Renders paper-frame style collapsible panel.
 */
import { useEffect, useState } from "react";
import { fetchBooks, type BookEntry } from "../lib/api";

interface Props {
  method: string;
  maxPriority?: number;
}

export function MethodSourcesPanel({ method, maxPriority = 2 }: Props) {
  const [open, setOpen] = useState(false);
  const [books, setBooks] = useState<BookEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetched, setFetched] = useState(false);

  // 折叠时按需 fetch；展开则不再重复拉
  useEffect(() => {
    if (!open || fetched) return;
    let alive = true;
    setLoading(true);
    setError(null);
    fetchBooks(method, { maxPriority })
      .then((res) => {
        if (!alive) return;
        setBooks(res.books);
        setFetched(true);
      })
      .catch((e: unknown) => alive && setError(String(e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [open, method, maxPriority, fetched]);

  const star = (n: number) => "★".repeat(n) + "☆".repeat(3 - n);

  return (
    <section className="paper-frame" data-testid="method-sources-panel">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left flex items-center justify-between gap-2"
        style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
        aria-expanded={open}
      >
        <h3 className="paper-eyebrow" style={{ color: "var(--cinnabar)", margin: 0 }}>
          📚 文献出处{books.length > 0 ? `（${books.length} 本）` : ""}
        </h3>
        <span
          style={{
            fontSize: "0.85rem",
            color: "var(--ink-soft)",
            transition: "transform 0.2s",
            transform: open ? "rotate(180deg)" : "none",
            flexShrink: 0,
          }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="animate-fade-in" style={{ marginTop: "0.6rem" }}>
          {loading && (
            <div
              className="paper-grid-cell"
              style={{ padding: "0.85rem", textAlign: "center", color: "var(--ink-soft)", fontSize: "0.85rem" }}
            >
              <span className="paper-pulse" style={{ display: "inline-block", marginRight: "0.5rem", verticalAlign: "middle" }} />
              正在加载文献…
            </div>
          )}

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
              <span>⚠ 文献加载失败: {error}</span>
              <button
                type="button"
                onClick={() => {
                  setFetched(false);
                  setError(null);
                }}
                style={{
                  background: "transparent",
                  border: "1px solid var(--cinnabar)",
                  color: "var(--cinnabar)",
                  padding: "0.18rem 0.6rem",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  borderRadius: "0.18rem",
                  fontFamily: "inherit",
                }}
              >
                重试
              </button>
            </div>
          )}

          {!loading && !error && books.length === 0 && (
            <div
              className="paper-grid-cell"
              style={{ padding: "0.8rem", textAlign: "center", color: "var(--ink-soft)", fontSize: "0.78rem" }}
            >
              暂无古籍条目
            </div>
          )}

          {books.map((b, i) => {
            const isVerified = !!b.verified_examples;
            return (
              <div
                key={`${b.title}-${i}`}
                className="paper-grid-cell"
                style={{ padding: "0.55rem 0.8rem", marginBottom: "0.4rem" }}
              >
                <div
                  style={{
                    fontSize: "0.9rem",
                    fontWeight: 700,
                    fontFamily: "'Noto Serif SC', serif",
                    color: "var(--ink)",
                  }}
                >
                  {b.title}
                  <span
                    style={{
                      fontSize: "0.65rem",
                      color: "var(--cinnabar)",
                      marginLeft: "0.5rem",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {star(b.priority)}
                  </span>
                  {isVerified && (
                    <span
                      style={{
                        fontSize: "0.6rem",
                        color: "var(--verdigris)",
                        marginLeft: "0.4rem",
                        border: "1px solid var(--verdigris)",
                        padding: "0 0.3rem",
                        borderRadius: "0.2rem",
                      }}
                    >
                      ✓ 已验证
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "0.68rem", color: "var(--ink-soft)", marginTop: "0.15rem" }}>
                  {b.dynasty} · {b.author} · {b.difficulty}
                </div>
                <p
                  style={{
                    fontSize: "0.74rem",
                    color: "var(--ink)",
                    lineHeight: 1.55,
                    marginTop: "0.3rem",
                    marginBottom: 0,
                  }}
                >
                  {b.description}
                </p>
                {b.key_chapters.length > 0 && (
                  <div
                    style={{
                      marginTop: "0.35rem",
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.25rem",
                    }}
                  >
                    {b.key_chapters.map((ch) => (
                      <span
                        key={ch}
                        className="paper-tag"
                        style={{
                          fontSize: "0.62rem",
                          padding: "0.05rem 0.45rem",
                          color: "var(--ink-soft)",
                          borderColor: "var(--rule)",
                        }}
                      >
                        {ch}
                      </span>
                    ))}
                  </div>
                )}
                {isVerified && (
                  <div
                    style={{
                      marginTop: "0.3rem",
                      padding: "0.3rem 0.55rem",
                      background: "rgba(90,112,88,0.08)",
                      borderRadius: "0.2rem",
                      fontSize: "0.68rem",
                    }}
                  >
                    <span style={{ color: "var(--verdigris)", fontWeight: 600 }}>✓ 验证: </span>
                    <span style={{ color: "var(--ink-soft)" }}>{b.verified_examples}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default MethodSourcesPanel;