/** SpreadSelector — 塔罗/雷诺曼牌阵选择网格 */
import { type FC } from "react";
import type { TarotSpread } from "../../lib/types";
import { useI18n } from "../../lib/i18n";

export interface SpreadOption {
  code: string;
  label: string;
  desc: string;
  cards?: number;
}

interface SpreadSelectorProps {
  value: string;
  onChange: (v: string) => void;
  spreads: SpreadOption[];
}

export const SpreadSelector: FC<SpreadSelectorProps> = ({ value, onChange, spreads }) => {
  const { t } = useI18n();

  return (
    <div>
      <label className="paper-label" style={{ marginBottom: "0.4rem", display: "block" }}>
        {t("form.spread.label")}
      </label>
      <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginBottom: "0.5rem" }}>
        {t("form.spread.desc")}
      </p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {spreads.map((sp) => {
          const on = value === sp.code;
          return (
            <button key={sp.code} type="button" onClick={() => onChange(sp.code)}
              className="paper-grid-cell text-left"
              style={{
                borderColor: on ? "var(--cinnabar)" : "var(--rule)",
                borderWidth: on ? 2 : 1,
                background: on ? "rgba(176,58,46,0.04)" : "var(--paper)",
                cursor: "pointer",
                padding: "0.65rem",
              }}>
              <div className="flex items-center justify-between">
                <span style={{
                  fontFamily: "'Noto Serif SC', serif",
                  fontWeight: on ? 700 : 500,
                  fontSize: "0.88rem",
                  color: on ? "var(--cinnabar)" : "var(--ink)",
                }}>{sp.label}</span>
                {sp.cards != null && (
                  <span style={{
                    fontSize: "0.65rem", color: "var(--ink-soft)",
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>{sp.cards} 张</span>
                )}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.2rem", lineHeight: 1.4 }}>
                {sp.desc}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

/** 塔罗牌阵选项 */
export const TAROT_SPREAD_OPTIONS: SpreadOption[] = [
  { code: "celtic_cross", label: "凯尔特十字", desc: "10张·全面深入", cards: 10 },
  { code: "three_time", label: "三张牌·时", desc: "过去·现在·未来", cards: 3 },
  { code: "three_mind", label: "三张牌·心", desc: "身·心·灵", cards: 3 },
  { code: "single", label: "单张牌", desc: "快速指引", cards: 1 },
  { code: "relationship_cross", label: "关系十字", desc: "双方互动·纽带", cards: 5 },
  { code: "career_path", label: "事业路径", desc: "方向·阻碍·机会", cards: 5 },
  { code: "choice_two", label: "二择一", desc: "两难抉择", cards: 5 },
];

/** 雷诺曼牌阵选项 */
export const LENORMAND_SPREAD_OPTIONS: SpreadOption[] = [
  { code: "three_time", label: "三张牌", desc: "过去·现在·未来", cards: 3 },
  { code: "single", label: "单张牌", desc: "快速指引", cards: 1 },
  { code: "celtic_cross", label: "十字阵", desc: "5张·深入", cards: 5 },
];
