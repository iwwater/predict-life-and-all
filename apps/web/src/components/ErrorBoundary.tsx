// 错误边界: 捕获渲染异常，显示古籍风格错误页（「古籍×仪器」纸墨风格）
import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
          <div className="max-w-md space-y-4" style={{ fontFamily: "'Noto Serif SC', serif" }}>
            <div style={{
              fontFamily: "'Cinzel', serif",
              fontSize: "5rem",
              color: "var(--rule)",
              lineHeight: 1,
            }}>!!</div>

            <h1 style={{
              fontSize: "1.15rem",
              fontWeight: 700,
              color: "var(--cinnabar)",
              letterSpacing: "0.12em",
            }}>
              卦象紊乱 · Chart Corruption
            </h1>

            <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", lineHeight: 1.85 }}>
              排盘引擎遇到了意料之外的波动。这可能是临时性的星象干扰，请尝试刷新页面。
            </p>

            <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.6 }}>
              The casting engine encountered an unexpected fluctuation. This may be a temporary celestial disturbance. Please try refreshing the page.
            </p>

            {this.state.error && (
              <details className="text-left">
                <summary style={{ fontSize: "0.62rem", color: "var(--ink-soft)", cursor: "pointer" }}>
                  Technical Details
                </summary>
                <pre className="paper-mono"
                  style={{
                    marginTop: "0.5rem", fontSize: "0.6rem", padding: "0.6rem",
                    background: "var(--paper-2)", color: "var(--cinnabar)",
                    border: "1px solid var(--rule)", overflow: "auto", maxHeight: "10rem",
                  }}>
                  {this.state.error.message}
                </pre>
              </details>
            )}

            <button
              type="button"
              className="paper-btn"
              style={{ marginTop: "1rem" }}
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = "/"; }}
            >
              返回首页
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
