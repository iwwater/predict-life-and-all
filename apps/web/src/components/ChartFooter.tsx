// 共享盘面底部操作栏 — 提取自 BaziPage / WesternPage / HePanPage / TarotPage
import { useI18n } from "../lib/i18n";
import { MethodSourcesPanel } from "./MethodSourcesPanel";
import { Button } from "./ui";

interface ChartFooterProps {
  chart: { engine?: string; elapsed_ms?: number; raw?: unknown; normalized?: unknown };
  method: string;
  inBasket: boolean;
  onBasket: () => void;
  onReset: () => void;
}

export function ChartFooter({ chart, method, inBasket, onBasket, onReset }: ChartFooterProps) {
  const { lang } = useI18n();
  return (
    <div
      className="flex items-center justify-between gap-3 flex-wrap"
      style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}
    >
      <div className="paper-mono" style={{ fontSize: "0.7rem", color: "var(--ink-soft)" }}>
        engine: {chart.engine ?? "—"} · {chart.elapsed_ms ?? "—"}ms
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
          {lang === "zh" ? "重新排盘" : "Recast"}
        </Button>
      </div>
      <MethodSourcesPanel method={method} />
    </div>
  );
}
