"use client";

import { V2Icon } from "./V2Icon";
import styles from "./V2ThemeControl.module.css";

export const V2_THEME_STORAGE_KEY = "aios-v2-theme";

export type V2ThemePreference = "system" | "light" | "dark";

export function isV2ThemePreference(value: string | null): value is V2ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

export function V2ThemeControl({
  value,
  onChange,
}: {
  value: V2ThemePreference;
  onChange: (value: V2ThemePreference) => void;
}) {
  return (
    <label className={styles.control} title={`Theme: ${value}`}>
      <V2Icon name="theme" width={16} height={16} />
      <span className={styles.label}>Theme</span>
      <select
        aria-label="AIOS V2 theme"
        value={value}
        onChange={(event) => {
          const next = event.target.value;
          if (isV2ThemePreference(next)) onChange(next);
        }}
      >
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
