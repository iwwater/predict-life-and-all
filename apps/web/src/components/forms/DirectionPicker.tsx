/** DirectionPicker — 坐向选择（8方向 + 建造年份） */
import { type FC } from "react";
import { DIRECTIONS_8 } from "../../lib/compass";
import { useI18n } from "../../lib/i18n";

interface DirectionPickerProps {
  sittingDir: string;
  constructionYear: number;
  onSittingChange: (v: string) => void;
  onYearChange: (v: number) => void;
  showYear?: boolean;
}

export const DirectionPicker: FC<DirectionPickerProps> = ({
  sittingDir, constructionYear, onSittingChange, onYearChange, showYear = true,
}) => {
  const { t, lang } = useI18n();

  return (
    <div className="grid sm:grid-cols-2 gap-3">
      <div>
        <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>
          {t("form.direction.label")}
        </label>
        <p style={{ fontSize: "0.68rem", color: "var(--ink-soft)", marginBottom: "0.35rem" }}>
          {t("form.direction.desc")}
        </p>
        <select className="paper-input" value={sittingDir} onChange={(e) => onSittingChange(e.target.value)}>
          {DIRECTIONS_8.map((d) => (
            <option key={d.code} value={d.code}>{d.code} · {d.sans}山 · {d.range}</option>
          ))}
        </select>
        <div className="paper-tag" style={{ marginTop: "0.35rem" }}>
          {DIRECTIONS_8.find((d) => d.code === sittingDir)?.sans || "子"} 山
        </div>
      </div>
      {showYear && (
        <div>
          <label className="paper-label" style={{ marginBottom: "0.3rem", display: "block" }}>
            {t("form.direction.year")}
          </label>
          <input className="paper-input" type="number" value={constructionYear}
            onChange={(e) => onYearChange(parseInt(e.target.value, 10) || new Date().getFullYear())} />
          <div className="paper-tag" style={{ marginTop: "0.35rem" }}>
            {lang === "zh" ? `三元九运·${Math.floor((constructionYear - 1864) / 20) + 1 || 8} 运` : `Period ${Math.floor((constructionYear - 1864) / 20) + 1 || 8}`}
          </div>
        </div>
      )}
    </div>
  );
};
