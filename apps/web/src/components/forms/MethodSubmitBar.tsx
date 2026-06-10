/** MethodSubmitBar — 提交按钮 + loading + error + 加入合参篮 */
import { type FC } from "react";
import { useI18n } from "../../lib/i18n";
import { ProgressArc } from "../Interactions";

interface MethodSubmitBarProps {
  loading: boolean;
  error: string | null;
  /** 是否在合参篮中 */
  inBasket: boolean;
  onAddToBasket: () => void;
  submitLabel?: string;
}

export const MethodSubmitBar: FC<MethodSubmitBarProps> = ({
  loading, error, inBasket, onAddToBasket, submitLabel,
}) => {
  const { t } = useI18n();

  return (
    <div className="space-y-3">
      {error && (
        <div className="paper-error">{error}</div>
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap"
        style={{ padding: "0.75rem 0", borderTop: "1px solid var(--rule)" }}>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="inline-flex items-center gap-2" style={{ fontSize: "0.78rem", color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}>
              <ProgressArc value={0.3} size={22} />
              {t("form.submitting")}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={onAddToBasket}
            className="paper-btn-ghost" style={{ fontSize: "0.72rem" }}>
            {inBasket ? t("basket.added") : t("basket.add")}
          </button>
          <button type="submit" disabled={loading}
            className="paper-btn" style={{ fontSize: "0.85rem" }}>
            {submitLabel || t("form.submit")}
          </button>
        </div>
      </div>
    </div>
  );
};
