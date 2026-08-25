"use client";

export type OperationalStatusKind = "idle" | "loading" | "ready" | "partial" | "offline";

type OperationalStatusMeta = {
  label: string;
  description: string;
};

export const OPERATIONAL_STATUS_META: Record<OperationalStatusKind, OperationalStatusMeta> = {
  idle: {
    label: "CONNECTING",
    description: "Workspace data is being resolved.",
  },
  loading: {
    label: "CONNECTING",
    description: "Workspace data is being refreshed.",
  },
  ready: {
    label: "READY",
    description: "All required workspace signals loaded successfully.",
  },
  partial: {
    label: "PARTIAL",
    description: "The workspace is usable, but one or more signals are unavailable.",
  },
  offline: {
    label: "DEGRADED",
    description: "The backend is unavailable or cannot be reached.",
  },
};

export function OperationalStatus({ status }: { status: OperationalStatusKind }) {
  const metadata = OPERATIONAL_STATUS_META[status];

  return (
    <span
      className={`ui-operational-status ${status}`}
      data-operational-state={status}
      role="status"
      aria-live="polite"
      aria-label={`${metadata.label}. ${metadata.description}`}
      title={metadata.description}
    >
      <i className="ui-operational-status-dot" aria-hidden="true" />
      <span className="ui-operational-status-label">{metadata.label}</span>
    </span>
  );
}
