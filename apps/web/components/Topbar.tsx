"use client";

const WORKSPACE_STATE_LABELS = {
  idle: "CONNECTING",
  loading: "CONNECTING",
  ready: "READY",
  partial: "PARTIAL",
  offline: "DEGRADED",
} as const;

const WORKSPACE_STATE_DESCRIPTIONS = {
  idle: "Workspace data is being resolved.",
  loading: "Workspace data is being refreshed.",
  ready: "All required workspace signals loaded successfully.",
  partial: "The workspace is usable, but one or more signals are unavailable.",
  offline: "The backend is unavailable or cannot be reached.",
} as const;

export function Topbar({
  title,
  kicker,
  loadStatus,
  onRefresh,
}: {
  title: string;
  kicker: string;
  loadStatus: "idle" | "loading" | "ready" | "partial" | "offline";
  onRefresh: () => void;
}) {
  const stateLabel = WORKSPACE_STATE_LABELS[loadStatus];
  const stateDescription = WORKSPACE_STATE_DESCRIPTIONS[loadStatus];

  return (
    <header className="topbar">
      <div>
        <span className="page-kicker">{kicker}</span>
        <h1>{title}</h1>
      </div>
      <div className="topbar-actions">
        <span
          className={`workspace-state ${loadStatus}`}
          role="status"
          aria-live="polite"
          aria-label={`${stateLabel}. ${stateDescription}`}
          title={stateDescription}
        >
          <i aria-hidden="true" />
          {stateLabel}
        </span>
        <button className="button secondary" type="button" onClick={onRefresh} disabled={loadStatus === "loading"}>
          {loadStatus === "loading" ? (
            <span className="button-spinner" aria-hidden="true" />
          ) : (
            "Refresh"
          )}
        </button>
      </div>
    </header>
  );
}
