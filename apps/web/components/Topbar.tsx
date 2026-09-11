"use client";

import { useEffect, useRef } from "react";

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

const LIVING_HQ_REFRESH_INTERVAL_MS = 6000;

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
  const refreshRef = useRef(onRefresh);
  const statusRef = useRef(loadStatus);

  useEffect(() => {
    refreshRef.current = onRefresh;
  }, [onRefresh]);

  useEffect(() => {
    statusRef.current = loadStatus;
  }, [loadStatus]);

  useEffect(() => {
    if (title !== "Live Organization") return;

    const refreshVisibleProjection = () => {
      if (document.visibilityState !== "visible") return;
      if (statusRef.current === "loading" || statusRef.current === "offline") return;
      refreshRef.current();
    };

    const intervalId = window.setInterval(refreshVisibleProjection, LIVING_HQ_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [title]);

  const liveRefreshEnabled = title === "Live Organization";

  return (
    <header
      className="topbar"
      data-live-refresh={liveRefreshEnabled ? "canonical-poll" : "manual"}
      data-live-refresh-interval-ms={liveRefreshEnabled ? String(LIVING_HQ_REFRESH_INTERVAL_MS) : undefined}
    >
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
        {liveRefreshEnabled ? <small className="topbar-live-refresh">LIVE · 6s</small> : null}
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
