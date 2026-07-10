export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function MetricSkeleton() {
  return (
    <div className="metric-pill">
      <Skeleton className="skeleton-text-sm" />
      <Skeleton className="skeleton-number" />
    </div>
  );
}

export function CaseRowSkeleton() {
  return (
    <div className="case-row">
      <Skeleton className="skeleton-identity" />
      <Skeleton className="skeleton-text" />
      <Skeleton className="skeleton-text" />
      <Skeleton className="skeleton-badge" />
    </div>
  );
}

export function ActionCardSkeleton() {
  return (
    <div className="action-card">
      <Skeleton className="skeleton-text-xs" />
      <Skeleton className="skeleton-title" />
      <Skeleton className="skeleton-paragraph" />
    </div>
  );
}
