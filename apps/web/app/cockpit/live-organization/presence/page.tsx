"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { SurfaceState } from "../../../../components/SurfaceState";
import { Topbar } from "../../../../components/Topbar";
import { WorkspaceShell } from "../../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../../hooks/useBackendStatus";
import {
  type AustriaOrganizationPresenceLatest,
  type OrganizationPositionPresence,
  OrganizationPresenceRequestError,
  getLatestAustriaOrganizationPresence,
} from "../../../../lib/organization-presence";
import { titleCase } from "../../../../lib/utils";

type PresenceLoadError = {
  status: number | null;
  message: string;
};

function positionLabel(value: string): string {
  return titleCase(value.replaceAll("_", " "));
}

function timeLabel(value?: string | null): string {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not recorded";
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function presenceLabel(item: OrganizationPositionPresence): string {
  if (item.presence_state === "executing") return "Recorded executing";
  if (item.presence_state === "not_executing") return "No active execution";
  return "Presence not established";
}

function presenceDescription(item: OrganizationPositionPresence): string {
  if (item.presence_state === "executing") {
    return "AIOS has a durable running execution attempt for this position. This is execution presence, not an online heartbeat claim.";
  }
  if (item.presence_state === "not_executing") {
    return "AIOS has durable execution history, but no running execution attempt. This does not assert that the employee is online or offline.";
  }
  return "No durable execution attempt has established execution presence for this position.";
}

export default function AustriaEmployeePresencePage() {
  const { health, error: healthError } = useBackendStatus();
  const [latest, setLatest] = useState<AustriaOrganizationPresenceLatest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PresenceLoadError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setLatest(await getLatestAustriaOrganizationPresence());
    } catch (loadError) {
      setLatest(null);
      setError(
        loadError instanceof OrganizationPresenceRequestError
          ? { status: loadError.status, message: loadError.message }
          : {
              status: null,
              message: loadError instanceof Error ? loadError.message : "Organization presence is unavailable.",
            },
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const snapshot = latest?.snapshot ?? null;
  const metrics = useMemo(() => {
    const positions = snapshot?.positions ?? [];
    return {
      executing: positions.filter((item) => item.presence_state === "executing").length,
      observed: positions.filter((item) => item.presence_state !== "not_established").length,
      total: positions.length,
    };
  }, [snapshot]);

  const loadStatus = health?.status !== "ok"
    ? "offline"
    : loading
      ? "loading"
      : error || healthError
        ? "partial"
        : "ready";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Employee Presence"
        kicker="Global Mobility AIOS Cockpit · Live Organization · Munder M6 adaptation"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command employee-presence-hero" aria-labelledby="employee-presence-title">
        <div className="cockpit-command-copy">
          <div className="cockpit-live-line">
            <span className="cockpit-live-dot" aria-hidden="true" />
            <span>AIOS-owned presence projection</span>
            <small>{snapshot ? `Observed ${timeLabel(snapshot.generated_at)}` : "No simulated presence"}</small>
          </div>
          <h2 id="employee-presence-title">
            {snapshot ? "Durable execution presence" : loading ? "Loading durable presence" : "Presence not established"}
          </h2>
          <p>
            This view adapts the Munder Difflin presence mechanic to AIOS-owned truth. A position is shown as executing only when a durable running OrganizationExecutionAttempt exists. Refresh time, animation, model/provider activity, and page visibility never become presence evidence.
          </p>
        </div>

        <aside className="cockpit-command-state" aria-label="Heartbeat capability posture">
          <span>Heartbeat capability</span>
          <strong>{snapshot ? titleCase(snapshot.heartbeat_capability_state) : "Not established"}</strong>
          <p>A real heartbeat lease or freshness signal has not been implemented, so this surface makes no online/offline claim.</p>
          <div className="cockpit-state-rule">
            <i aria-hidden="true" />
            <span>Presence has no authority, autonomy, evidence, or external-action effect</span>
          </div>
        </aside>

        <div className="cockpit-command-metrics" aria-label="Employee presence metrics">
          <article><strong>{snapshot ? metrics.executing : "—"}</strong><span>Recorded executing</span></article>
          <article><strong>{snapshot ? `${metrics.observed}/${metrics.total}` : "—"}</strong><span>Execution-observed positions</span></article>
          <article><strong>{snapshot ? titleCase(snapshot.heartbeat_capability_state) : "—"}</strong><span>Heartbeat</span></article>
        </div>
      </section>

      {error ? (
        <SurfaceState
          kind="error"
          title={error.status === 401 ? "Board authentication required" : error.status === 403 ? "Board access not permitted" : "Employee presence unavailable"}
          description={error.message}
          announce
        />
      ) : null}

      {!loading && !error && !snapshot ? (
        <section className="cockpit-surface" aria-labelledby="presence-empty-title">
          <header className="cockpit-surface-header compact">
            <div><span className="premium-label">Persisted truth</span><h3 id="presence-empty-title">No Austria presence projection yet</h3></div>
          </header>
          <SurfaceState
            kind="empty"
            title="Presence not established"
            description="No persisted Austria Live Organization cycle is available, so the Cockpit does not invent employees, execution presence, or heartbeat state."
          />
        </section>
      ) : null}

      {snapshot ? (
        <section className="cockpit-surface employee-presence-surface" aria-labelledby="presence-grid-title">
          <header className="cockpit-surface-header compact">
            <div>
              <span className="premium-label">Operational presence</span>
              <h3 id="presence-grid-title">Specialist execution presence</h3>
            </div>
            <span className="live-activity-total">{snapshot.positions.length}</span>
          </header>

          <div className="employee-presence-grid">
            {snapshot.positions.map((item) => (
              <article className={`employee-presence-card ${item.presence_state}`} key={item.work_item_id}>
                <header>
                  <span className={`employee-presence-indicator ${item.presence_state}`} aria-hidden="true" />
                  <div>
                    <strong>{positionLabel(item.position_key)}</strong>
                    <span>{presenceLabel(item)}</span>
                  </div>
                </header>
                <p>{presenceDescription(item)}</p>
                <dl>
                  <div><dt>Presence basis</dt><dd>{titleCase(item.presence_basis)}</dd></div>
                  <div><dt>Observed</dt><dd>{timeLabel(item.observed_at)}</dd></div>
                  <div><dt>Execution attempt</dt><dd>{item.execution_attempt_id ? item.execution_attempt_id.slice(0, 8) : "Not recorded"}</dd></div>
                  <div><dt>Attempt state</dt><dd>{item.execution_attempt_status ? titleCase(item.execution_attempt_status) : "Not recorded"}</dd></div>
                  <div><dt>Heartbeat</dt><dd>{titleCase(item.heartbeat_state)}</dd></div>
                  <div><dt>Authority effect</dt><dd>{item.authority_effect ? "Present" : "None"}</dd></div>
                </dl>
              </article>
            ))}
          </div>

          <div className="employee-presence-boundary">
            <strong>Presence boundary</strong>
            <p>
              “Recorded executing” means only that the durable AIOS execution-attempt record is currently running. It is not proof of continuous liveness, a provider connection, human availability, or permission to act. Heartbeat remains explicitly not established.
            </p>
          </div>
        </section>
      ) : null}
    </WorkspaceShell>
  );
}
