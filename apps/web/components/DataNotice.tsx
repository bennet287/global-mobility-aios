import { InlineNotice } from "./InlineNotice";

export function DataNotice<T>({ label, data }: { label: string; data: { data: T | null; error: string | null } }) {
  if (!data.error) return null;
  return <InlineNotice label={label} detail={data.error} />;
}
