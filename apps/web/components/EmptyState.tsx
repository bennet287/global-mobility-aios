export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state" role="status">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}
