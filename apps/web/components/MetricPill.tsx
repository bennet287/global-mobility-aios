import { compactNumber, Tone } from "../lib/utils";

export function MetricPill({ label, value, tone = "neutral" }: { label: string; value: number | string; tone?: Tone }) {
  return (
    <div className={`metric-pill ${tone}`}>
      <span>{label}</span>
      <strong>{typeof value === "number" ? compactNumber(value) : value}</strong>
    </div>
  );
}
