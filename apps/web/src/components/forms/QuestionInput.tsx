/** QuestionInput — 问题输入 + 字数统计 */
import { type FC } from "react";
import { useI18n } from "../../lib/i18n";

interface QuestionInputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  maxLength?: number;
}

export const QuestionInput: FC<QuestionInputProps> = ({
  value, onChange, placeholder, required = false, maxLength = 400,
}) => {
  const { t } = useI18n();

  return (
    <div>
      <label className="paper-label">
        {t("form.question.label")}
        {required && <span style={{ color: "var(--cinnabar)", marginLeft: 4 }}>{t("form.question.required")}</span>}
        {!required && <span style={{ color: "var(--ink-soft)", marginLeft: 4, fontSize: "0.65rem" }}>{t("form.question.optional")}</span>}
      </label>
      <textarea
        className="paper-input"
        style={{ minHeight: 100, resize: "vertical", lineHeight: 1.7 }}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || t("form.question.placeholder")}
        maxLength={maxLength}
      />
      <div className="flex items-center justify-between" style={{ marginTop: "0.3rem" }}>
        <span style={{ fontSize: "0.68rem", color: "var(--ink-soft)" }}>{t("form.question.hint")}</span>
        <span style={{
          fontSize: "0.68rem",
          color: value.length > maxLength ? "var(--cinnabar)" : "var(--ink-soft)",
          fontFamily: "'JetBrains Mono', monospace",
        }}>
          {value.length}/{maxLength} {t("form.question.chars")}
        </span>
      </div>
    </div>
  );
};
