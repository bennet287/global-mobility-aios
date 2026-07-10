import { compactNumber, Tone } from "../lib/utils";

export function MetricPill({ label, value, tone = "neutral" }: { label: string; value: number; tone?: Tone }) {
  return (
    <div className={`metric-pill ${tone}`}>
      <span>{label}</span>
      <strong>{compactNumber(value)}</strong>
    </div>
  );
}
