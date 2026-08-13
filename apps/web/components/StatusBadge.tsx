import { statusTone, titleCase } from "../lib/utils";

export function StatusBadge({ value }: { value: string | undefined | null }) {
  const tone = statusTone(value);
  const label = titleCase(value);
  return <span className={`status-badge ${tone}`} aria-label={`Status: ${label}`}>{label}</span>;
}
