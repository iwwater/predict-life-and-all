// 共享盘面底部操作栏 — 2026-10: 把 9 份手工复制的本地 ChartFooter 收成一份,
// 并在盘面下方直接带 AI 解读 (市面同类应用的通例: 出盘即出解读; 之前只有
// /result 一条路径有解读, 而多数方法页并不跳 /result)。
import type { ChartResult } from "../lib/types";
import { useI18n } from "../lib/i18n";
import { Interpretation } from "./Interpretation";
import { MethodSourcesPanel } from "./MethodSourcesPanel";
import { Button } from "./ui";

interface ChartFooterProps {
  chart: ChartResult;
  /** 方法 id, 用于文献出处面板 */
  method?: string;
  inBasket: boolean;
  onBasket: () => void;
  onReset: () => void;
  /** 「重来」按钮文案, 各方法页习惯不同 (重新排盘/起盘/起卦/推算/合盘) */
  recastLabel?: string;
  /** 求测者所问, 缺省则不向解读引擎传问题 */
  question?: string;
  /** 关掉自动解读 (默认开) */
  withReading?: boolean;
}

export function ChartFooter({
  chart,
  method,
  inBasket,
  onBasket,
  onReset,
  recastLabel,
  question,
  withReading = true,
}: ChartFooterProps) {
  const { lang } = useI18n();
  return (
    <div>
      <div
        className="flex items-center justify-between gap-3 flex-wrap"
        style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}
      >
        <div className="paper-mono" style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
          engine: {chart?.engine ?? "—"} · {chart?.elapsed_ms ?? "—"}ms
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBasket}
            disabled={inBasket}
            type="button"
          >
            {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
          </Button>
          <Button variant="primary" size="sm" onClick={onReset} type="button">
            {recastLabel || (lang === "zh" ? "重新排盘" : "Recast")}
          </Button>
        </div>
        {method && <MethodSourcesPanel method={method} />}
      </div>

      {withReading && chart && (
        <div style={{ marginTop: "1.25rem" }}>
          <Interpretation charts={[chart]} question={question || ""} />
        </div>
      )}
    </div>
  );
}
