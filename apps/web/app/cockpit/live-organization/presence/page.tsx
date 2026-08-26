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

function heartbeatDescription(item: OrganizationPositionPresence): string {
  if (item.heartbeat_state === "fresh") {
    return "A trusted AIOS worker checkpoint is still inside its bounded freshness lease. This is not continuous online status.";
  }
  if (item.heartbeat_state === "stale") {
    return "The latest trusted worker checkpoint has exceeded its lease. Stale does not mean the employee, provider, or model is offline.";
  }
  if (item.heartbeat_state === "inactive") {
    return "No heartbeat lease is active because there is no running execution attempt.";
  }
  return "The running execution has no durable worker checkpoint lease yet.";
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
      fresh: positions.filter((item) => item.heartbeat_state === "fresh").length,
      stale: positions.filter((item) => item.heartbeat_state === "stale").length,
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
            This view adapts the Munder Difflin presence mechanic to AIOS-owned truth. A position is shown as executing only when a durable running OrganizationExecutionAttempt exists. Heartbeat freshness comes only from trusted worker checkpoints; refresh time, animation, model/provider activity, and page visibility never become presence evidence.
          </p>
        </div>

        <aside className="cockpit-command-state" aria-label="Heartbeat capability posture">
          <span>Heartbeat capability</span>
          <strong>{snapshot ? titleCase(snapshot.heartbeat_capability_state) : "Not established"}</strong>
          <p>A bounded execution-checkpoint lease is available. Fresh/stale describes durable worker-checkpoint freshness only, not continuous online/offline liveness.</p>
          <div className="cockpit-state-rule">
            <i aria-hidden="true" />
            <span>Presence and heartbeat have no authority, autonomy, evidence, or external-action effect</span>
          </div>
        </aside>

        <div className="cockpit-command-metrics" aria-label="Employee presence metrics">
          <article><strong>{snapshot ? metrics.executing : "—"}</strong><span>Recorded executing</span></article>
          <article><strong>{snapshot ? metrics.fresh : "—"}</strong><span>Fresh checkpoints</span></article>
          <article><strong>{snapshot ? metrics.stale : "—"}</strong><span>Stale checkpoints</span></article>
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
                <p>{heartbeatDescription(item)}</p>
                <dl>
                  <div><dt>Presence basis</dt><dd>{titleCase(item.presence_basis)}</dd></div>
                  <div><dt>Execution observed</dt><dd>{timeLabel(item.observed_at)}</dd></div>
                  <div><dt>Execution attempt</dt><dd>{item.execution_attempt_id ? item.execution_attempt_id.slice(0, 8) : "Not recorded"}</dd></div>
                  <div><dt>Attempt state</dt><dd>{item.execution_attempt_status ? titleCase(item.execution_attempt_status) : "Not recorded"}</dd></div>
                  <div><dt>Heartbeat freshness</dt><dd>{titleCase(item.heartbeat_state)}</dd></div>
                  <div><dt>Checkpoint observed</dt><dd>{timeLabel(item.heartbeat_observed_at)}</dd></div>
                  <div><dt>Fresh until</dt><dd>{timeLabel(item.heartbeat_fresh_until)}</dd></div>
                  <div><dt>Authority effect</dt><dd>{item.authority_effect ? "Present" : "None"}</dd></div>
                </dl>
              </article>
            ))}
          </div>

          <div className="employee-presence-boundary">
            <strong>Heartbeat boundary</strong>
            <p>
              A fresh checkpoint means a trusted AIOS worker reached a durable execution checkpoint within the bounded lease. It is not continuous liveness, provider health, human availability, or permission to act. A long blocking provider call can legitimately make the lease stale before execution completes, and stale is not an offline claim.
            </p>
          </div>
        </section>
      ) : null}
    </WorkspaceShell>
  );
}
