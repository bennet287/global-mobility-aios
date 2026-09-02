import { compactNumber, Tone } from "../lib/utils";

export function MetricPill({
  label,
  value,
  tone = "neutral",
  className = "",
}: {
  label: string;
  value: number | string;
  tone?: Tone;
  className?: string;
}) {
  return (
    <div className={`metric-pill ${tone} ${className}`.trim()}>
      <span>{label}</span>
      <strong>{typeof value === "number" ? compactNumber(value) : value}</strong>
    </div>
  );
}
