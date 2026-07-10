export function InlineNotice({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="inline-notice">
      <strong>{label}</strong>
      <span>{detail}</span>
    </div>
  );
}

export function DataNotice<T>({ label, data }: { label: string; data: { data: T | null; error: string | null } }) {
  if (!data.error) return null;
  return <InlineNotice label={label} detail={data.error} />;
}
