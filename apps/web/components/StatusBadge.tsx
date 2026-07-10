import { statusTone, titleCase } from "../lib/utils";

export function StatusBadge({ value }: { value: string | undefined | null }) {
  const tone = statusTone(value);
  return <span className={`status-badge ${tone}`}>{titleCase(value)}</span>;
}
