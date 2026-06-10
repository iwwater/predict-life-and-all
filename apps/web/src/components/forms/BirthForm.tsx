/** BirthForm — 出生信息表单（可配置字段可见性）
 *
 * Props:
 *   showFields: 要显示哪些字段（e.g. ["year","month","day","hour","minute","gender","city"]）
 *   birth: { year, month, day, hour, minute, gender, city }
 *   cityInfo: 当前城市信息 { name, lat, lng, tz }
 *   onChange: (patch: Partial<BirthState>) => void
 */
import { type FC } from "react";
import { CITY_PRESETS, CITY_REGIONS, cityOptionLabel } from "../../lib/cities";
import { useI18n } from "../../lib/i18n";

export interface BirthState {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  gender: "male" | "female" | "unspecified";
  city: string;
}

export interface CityInfo {
  name: string;
  lat: number;
  lng: number;
  tz: string;
}

interface BirthFormProps {
  showFields: string[];
  birth: BirthState;
  cityInfo: CityInfo;
  onChange: (patch: Partial<BirthState>) => void;
}

export const BirthForm: FC<BirthFormProps> = ({ showFields, birth, cityInfo, onChange }) => {
  const { t } = useI18n();

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
        {showFields.includes("year") && (
          <Field label={t("form.birth.year")}>
            <input className="paper-input" type="number" value={birth.year} onChange={(e) => onChange({ year: parseInt(e.target.value, 10) || 0 })} />
          </Field>
        )}
        {showFields.includes("month") && (
          <Field label={t("form.birth.month")}>
            <input className="paper-input" type="number" value={birth.month} onChange={(e) => onChange({ month: parseInt(e.target.value, 10) || 0 })} min={1} max={12} />
          </Field>
        )}
        {showFields.includes("day") && (
          <Field label={t("form.birth.day")}>
            <input className="paper-input" type="number" value={birth.day} onChange={(e) => onChange({ day: parseInt(e.target.value, 10) || 0 })} min={1} max={31} />
          </Field>
        )}
        {showFields.includes("hour") && (
          <Field label={t("form.birth.hour")}>
            <input className="paper-input" type="number" value={birth.hour} onChange={(e) => onChange({ hour: parseInt(e.target.value, 10) || 0 })} min={0} max={23} />
          </Field>
        )}
        {showFields.includes("minute") && (
          <Field label={t("form.birth.minute")}>
            <input className="paper-input" type="number" value={birth.minute} onChange={(e) => onChange({ minute: parseInt(e.target.value, 10) || 0 })} min={0} max={59} />
          </Field>
        )}
        {showFields.includes("gender") && (
          <Field label={t("form.birth.gender")}>
            <select className="paper-input" value={birth.gender} onChange={(e) => onChange({ gender: e.target.value as any })}>
              <option value="male">{t("form.birth.genderMale")}</option>
              <option value="female">{t("form.birth.genderFemale")}</option>
              <option value="unspecified">{t("form.birth.genderUnspec")}</option>
            </select>
          </Field>
        )}
      </div>
      {showFields.includes("city") && (
        <div>
          <label className="paper-label">{t("form.birth.city")}</label>
          <select className="paper-input" style={{ maxWidth: "24rem" }} value={birth.city} onChange={(e) => onChange({ city: e.target.value })}>
            {CITY_REGIONS.map((r) => (
              <optgroup key={r.key} label={r.label}>
                {CITY_PRESETS.filter((c) => c.region === r.key).map((c) => (
                  <option key={`${c.province || c.region}-${c.name}`} value={c.name}>{cityOptionLabel(c)}</option>
                ))}
              </optgroup>
            ))}
          </select>
          {cityInfo && (
            <div className="paper-tag" style={{ marginTop: "0.35rem" }}>
              {cityInfo.name} · {cityInfo.lat.toFixed(2)}°N, {cityInfo.lng.toFixed(2)}°E · {cityInfo.tz}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="paper-label">{label}</label>
      {children}
    </div>
  );
}
