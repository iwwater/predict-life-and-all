// 错误边界: 捕获渲染异常, 显示神秘错误页
import { Component, type ReactNode, type ErrorInfo } from "react";
import { COLOR } from "./ui";
import { YinYang } from "./MysticElements";

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
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center relative">
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-[0.05]">
            <YinYang size={200} />
          </div>
          <div className="relative z-10 space-y-4 max-w-md mx-auto px-4">
            <div className="text-6xl font-display text-shimmer" style={{ fontFamily: "'Cinzel', serif" }}>
              ⚡
            </div>
            <h1 className="text-xl font-display" style={{ color: COLOR.goldBright }}>
              卦象紊乱 · Chart Corruption
            </h1>
            <p className="text-sm leading-relaxed" style={{ color: COLOR.inkSoft }}>
              排盘引擎遇到了意料之外的波动。这可能是临时性的星象干扰，请尝试刷新页面。
            </p>
            <p className="text-xs leading-relaxed" style={{ color: COLOR.inkSoft }}>
              The casting engine encountered an unexpected fluctuation. This may be a temporary celestial disturbance. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="text-left">
                <summary className="text-[10px] cursor-pointer" style={{ color: COLOR.muted }}>
                  Technical Details
                </summary>
                <pre className="mt-2 text-[10px] p-3 rounded overflow-auto max-h-40"
                  style={{ background: "rgba(8,10,15,0.8)", color: COLOR.danger, border: "1px solid var(--line)" }}>
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <button
              type="button"
              className="btn-primary gold-sweep-host text-sm px-6 py-3 mt-4"
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = "/"; }}
            >
              ✦ 返回首页 / Return Home
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
