import { Tone } from "../lib/utils";

export function InlineNotice({ label, detail, tone = "warn" }: { label: string; detail: string; tone?: Tone }) {
  return (
    <div className={`inline-notice ${tone}`}>
      <strong>{label}</strong>
      <span>{detail}</span>
    </div>
  );
}

export function DataNotice<T>({ label, data }: { label: string; data: { data: T | null; error: string | null } }) {
  if (!data.error) return null;
  return <InlineNotice label={label} detail={data.error} tone="bad" />;
}
