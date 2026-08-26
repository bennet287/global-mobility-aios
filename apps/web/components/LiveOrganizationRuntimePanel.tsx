"use client";

import Link from "next/link";

import type { AustriaLiveActivity } from "../lib/live-organization";
import type { AustriaOrganizationPresenceSnapshot, OrganizationPositionPresence } from "../lib/organization-presence";
import { titleCase } from "../lib/utils";
import { SurfaceState } from "./SurfaceState";

function positionLabel(value: string | null | undefined): string {
  if (!value) return "Unassigned";
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

export function LiveOrganizationRuntimePanel({
  rootWorkItemId,
  presence,
  presenceError,
  activities,
}: {
  rootWorkItemId: string;
  presence: AustriaOrganizationPresenceSnapshot | null;
  presenceError: string | null;
  activities: AustriaLiveActivity[];
}) {
  const presenceMatchesCycle = presence?.root_work_item_id === rootWorkItemId;
  const positions = presence && presenceMatchesCycle ? presence.positions : [];
  const executingCount = positions.filter((item) => item.presence_state === "executing").length;
  const freshHeartbeatCount = positions.filter((item) => item.heartbeat_state === "fresh").length;
  const staleHeartbeatCount = positions.filter((item) => item.heartbeat_state === "stale").length;
  const recentActivities = activities.slice(0, 5);

  return (
    <section className="live-runtime-grid" aria-label="Live organization runtime and durable activity">
      <article className="cockpit-surface live-runtime-presence" aria-labelledby="live-runtime-presence-title">
        <header className="cockpit-surface-header compact">
          <div>
            <span className="premium-label">Munder M6 · AIOS-owned</span>
            <h3 id="live-runtime-presence-title">Employee execution presence</h3>
          </div>
          <Link className="live-runtime-detail-link" href="/cockpit/live-organization/presence">
            Inspect presence
          </Link>
        </header>

        {presenceError ? (
          <SurfaceState
            kind="error"
            title="Presence projection unavailable"
            description={presenceError}
            compact
          />
        ) : presence && !presenceMatchesCycle ? (
          <SurfaceState
            kind="blocked"
            title="Presence refresh is out of sync"
            description="The latest presence projection belongs to a different Austria root WorkItem than this Live Organization snapshot. No presence state is merged across cycles; refresh to reconcile the two canonical reads."
            compact
          />
        ) : !presence ? (
          <SurfaceState
            kind="empty"
            title="Presence not established"
            description="No execution-derived presence projection is available for this Austria cycle. The Cockpit does not infer employee availability from UI state or provider activity."
            compact
          />
        ) : (
          <>
            <div className="live-runtime-presence-summary" aria-label="Execution presence summary">
              <div><strong>{executingCount}</strong><span>Recorded executing</span></div>
              <div><strong>{freshHeartbeatCount}</strong><span>Fresh checkpoints</span></div>
              <div><strong>{staleHeartbeatCount}</strong><span>Stale checkpoints</span></div>
            </div>
            <div className="live-runtime-presence-list">
              {positions.map((item) => (
                <div className="live-runtime-presence-row" key={item.work_item_id}>
                  <span className={`employee-presence-indicator ${item.presence_state}`} aria-hidden="true" />
                  <div>
                    <strong>{positionLabel(item.position_key)}</strong>
                    <small>
                      {presenceLabel(item)} · heartbeat {titleCase(item.heartbeat_state)} · observed {timeLabel(item.observed_at)}
                    </small>
                  </div>
                </div>
              ))}
            </div>
            <p className="live-runtime-boundary">
              Execution presence is backed by durable OrganizationExecutionAttempt state. Heartbeat fresh/stale is backed only by bounded AIOS worker-checkpoint leases; it is not continuous online/offline liveness, provider health, authority, autonomy, or external-action permission.
            </p>
          </>
        )}
      </article>

      <article className="cockpit-surface live-runtime-activity" aria-labelledby="live-runtime-activity-title">
        <header className="cockpit-surface-header compact">
          <div>
            <span className="premium-label">Durable event projection</span>
            <h3 id="live-runtime-activity-title">Organization activity stream</h3>
          </div>
          <span className="live-activity-total">{activities.length}</span>
        </header>

        {recentActivities.length ? (
          <ol className="live-runtime-activity-list">
            {recentActivities.map((activity) => (
              <li key={activity.activity_id}>
                <span className={`activity-mark ${activity.physical_activity_class === "decision" ? "decision" : "warning"}`} aria-hidden="true" />
                <div>
                  <strong>{activity.title}</strong>
                  <p>{activity.summary}</p>
                  <small>
                    {timeLabel(activity.occurred_at)} · {positionLabel(activity.position_key || activity.actor_id)} · {titleCase(activity.physical_activity_class)}
                  </small>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <SurfaceState
            kind="empty"
            title="No durable activity recorded"
            description="This panel renders persisted OrganizationActivity records only. It does not synthesize chat bubbles, tool calls, motion, or busywork when the canonical activity stream is empty."
            compact
          />
        )}
      </article>
    </section>
  );
}
