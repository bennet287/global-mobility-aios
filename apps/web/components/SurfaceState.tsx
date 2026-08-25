"use client";

export type SurfaceStateKind = "empty" | "error" | "blocked" | "not-connected";

export function SurfaceState({
  kind,
  title,
  description,
  compact = false,
  announce = false,
}: {
  kind: SurfaceStateKind;
  title: string;
  description: string;
  compact?: boolean;
  announce?: boolean;
}) {
  return (
    <div
      className={`ui-surface-state ${kind}${compact ? " compact" : ""}`}
      data-surface-state={kind}
      role={announce ? (kind === "error" ? "alert" : "status") : undefined}
      aria-live={announce ? (kind === "error" ? "assertive" : "polite") : undefined}
    >
      <span className="ui-surface-state-mark" aria-hidden="true" />
      <div className="ui-surface-state-copy">
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}
