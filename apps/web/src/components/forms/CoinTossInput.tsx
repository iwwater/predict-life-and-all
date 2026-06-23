/** CoinTossInput — 六爻手动摇卦（6次铜钱结果） */
import { type FC, useState } from "react";
import { useI18n } from "../../lib/i18n";

export type TossResult = "old_yang" | "young_yang" | "young_yin" | "old_yin";

export const TOSS_OPTIONS: { value: TossResult; label: string; symbol: string }[] = [
  { value: "old_yang", label: "老阳 ○ (3正)", symbol: "○" },
  { value: "young_yang", label: "少阳 — (2正1反)", symbol: "—" },
  { value: "young_yin", label: "少阴 - - (1正2反)", symbol: "- -" },
  { value: "old_yin", label: "老阴 × (3反)", symbol: "×" },
];

interface CoinTossInputProps {
  tosses: TossResult[];
  onChange: (tosses: TossResult[]) => void;
}

export const CoinTossInput: FC<CoinTossInputProps> = ({ tosses, onChange }) => {
  const { t } = useI18n();

  function setToss(i: number, v: TossResult) {
    const next = [...tosses];
    next[i] = v;
    onChange(next);
  }

  function autoToss() {
    const results: TossResult[] = [];
    for (let i = 0; i < 6; i++) {
      const r = Math.floor(Math.random() * 4);
      results.push(TOSS_OPTIONS[r].value);
    }
    onChange(results);
  }

  return (
    <div>
      <label className="paper-label" style={{ marginBottom: "0.4rem", display: "block" }}>
        {t("form.coin.label")}
      </label>
      <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginBottom: "0.5rem" }}>
        {t("form.coin.desc")}
      </p>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} style={{
            border: "1px solid var(--rule)", borderRadius: "4px",
            padding: "0.45rem", textAlign: "center",
          }}>
            <div style={{
              fontSize: "0.65rem", color: "var(--ink-soft)",
              marginBottom: "0.3rem", fontFamily: "'JetBrains Mono', monospace",
            }}>
              {t("form.coin.tossN").replace("{n}", String(i + 1))}
            </div>
            <select
              className="paper-input"
              style={{ fontSize: "0.7rem", padding: "0.2rem 0.3rem" }}
              value={tosses[i] || ""}
              onChange={(e) => setToss(i, e.target.value as TossResult)}
            >
              <option value="">--</option>
              {TOSS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.symbol} {o.label}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
      <button type="button" onClick={autoToss}
        className="paper-btn-ghost" style={{ marginTop: "0.5rem", fontSize: "0.72rem" }}>
        {t("form.coin.auto")}
      </button>
    </div>
  );
};
