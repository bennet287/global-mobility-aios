export function SectionTitle({ label, title, detail }: { label: string; title: string; detail?: string }) {
  return (
    <div className="section-title">
      <span>{label}</span>
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : null}
    </div>
  );
}
