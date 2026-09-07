"use client";

import Link from "next/link";

import type { V2OwnerOrganizationData } from "../../lib/v2/owner-organization";
import { buildV2OwnerSituationSummary } from "../../lib/v2/owner-situation";
import {
  deriveV2OwnerSourceCoverage,
  describeV2CountTruth,
  formatV2CountTruth,
  type V2CountTruth,
} from "../../lib/v2/truth-state";
import { V2AttentionList } from "./V2AttentionList";
import { V2OrganizationBlockout } from "./V2OrganizationBlockout";
import styles from "./V2OwnerSituationRoom.module.css";

function formatUtc(value: string | null): string {
  if (!value) return "No timestamp returned";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Timestamp unavailable";
  return date.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

function metricDisplay(metric: V2CountTruth | null, loading: boolean): string {
  if (loading) return "…";
  return metric ? formatV2CountTruth(metric) : "Unavailable";
}

function metricReturned(metric: V2CountTruth | null, loading: boolean): string {
  if (loading) return "Reading…";
  if (!metric) return "Unavailable";
  if (metric.state === "known") return `${metric.value} returned`;
  return formatV2CountTruth(metric);
}

export function V2OwnerSituationRoom({
  data,
  loading,
  error,
  onRetry,
}: {
  data: V2OwnerOrganizationData | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  const summary = data ? buildV2OwnerSituationSummary(data) : null;
  const coverage = data ? deriveV2OwnerSourceCoverage(data) : null;
  const sourcePosture = loading
    ? "Reading governed sources"
    : error
      ? "Source read unavailable"
      : data?.partial
        ? "Partial source coverage"
        : "Connected source coverage";

  const sourceDetail = loading
    ? "Board, human-action, blocker, Activity and Living Organization reads are in progress."
    : error
      ? "The situation room will not infer missing records."
      : data?.partial
        ? `Unavailable: ${data.unavailableSources.join(", ")}.`
        : "No configured Owner Home source reported an availability failure.";

  return (
    <div className="aios-v2-content">
      <section className={styles.hero} aria-labelledby="aios-v2-owner-home-title">
        <div className={styles.heroCopy}>
          <span className="aios-v2-kicker">Owner Home · situation room</span>
          <h1 id="aios-v2-owner-home-title">Know what needs you before you open the details.</h1>
          <p>
            This view prioritizes governed attention, Mission condition, decision awareness, organization context and recent Activity. It summarizes existing records; it does not create new authority or canonical state.
          </p>
        </div>

        <aside className={styles.sourcePosture} data-state={error ? "error" : data?.partial ? "partial" : "connected"}>
          <span>Source posture</span>
          <strong>{sourcePosture}</strong>
          <p>{sourceDetail}</p>
          {summary ? <small>Loaded {formatUtc(summary.loadedAt)}</small> : null}
        </aside>
      </section>

      <section className={styles.scanLine} aria-label="Owner five-second scan">
        <div className={styles.scanItem} data-state={summary && summary.attentionTotal.value > 0 ? "attention" : "neutral"}>
          <span>Owner attention</span>
          <strong>{metricDisplay(summary?.attentionTotal ?? null, loading)}</strong>
          <small>{summary ? describeV2CountTruth(summary.attentionTotal, "governed attention signals") : "No complete source read yet."}</small>
        </div>
        <div className={styles.scanItem} data-state={summary && summary.blockedMissionCount.value > 0 ? "attention" : "neutral"}>
          <span>Mission blockers</span>
          <strong>{metricDisplay(summary?.blockedMissionCount ?? null, loading)}</strong>
          <small>{summary ? describeV2CountTruth(summary.blockedMissionCount, "Mission records with linked blockers") : "No complete source read yet."}</small>
        </div>
        <div className={styles.scanItem}>
          <span>Decision awareness</span>
          <strong>{metricDisplay(summary?.decisionAttentionCount ?? null, loading)}</strong>
          <small>{summary ? describeV2CountTruth(summary.decisionAttentionCount, "current decision attention records") : "No complete source read yet."}</small>
        </div>
        <div className={styles.scanItem}>
          <span>Recent Activity</span>
          <strong>{metricDisplay(summary?.recentChangeCount ?? null, loading)}</strong>
          <small>{summary?.recentChangeCount.state === "known" && summary.latestChangeAt ? `latest ${formatUtc(summary.latestChangeAt)}` : summary ? describeV2CountTruth(summary.recentChangeCount, "recent Activity records") : "No complete source read yet."}</small>
        </div>
      </section>

      {error ? (
        <div className="aios-v2-source-warning" role="alert">
          <div>
            <strong>Owner situation data could not be loaded.</strong>
            <span>{error}</span>
          </div>
          <button onClick={onRetry} type="button">Retry</button>
        </div>
      ) : null}

      {data?.partial ? (
        <div className="aios-v2-source-warning" role="status">
          <div>
            <strong>Partial situation view.</strong>
            <span>Unavailable: {data.unavailableSources.join(", ")}. Unknown values are not rendered as numeric zero.</span>
          </div>
        </div>
      ) : null}

      <section className={styles.priorityGrid} aria-label="Owner priorities">
        <aside className={styles.attentionPanel} aria-labelledby="aios-v2-attention-title">
          <header className={styles.panelHeader}>
            <div>
              <span>1 · Needs attention</span>
              <h2 id="aios-v2-attention-title">Authority & human review</h2>
            </div>
            <small>{metricReturned(summary?.attentionTotal ?? null, loading)}</small>
          </header>

          <V2AttentionList items={data?.attention || []} loading={loading} countTruth={summary?.attentionTotal ?? null} />

          {summary ? (
            <div className={styles.attentionBreakdown} aria-label="Attention composition">
              <span>{formatV2CountTruth(summary.authorityAttentionCount)} authority</span>
              <span>{formatV2CountTruth(summary.criticalAttentionCount)} critical</span>
              <span>{formatV2CountTruth(summary.humanActionAttentionCount)} human action</span>
              <span>{formatV2CountTruth(summary.blockerAttentionCount)} blocker</span>
              <span>{formatV2CountTruth(summary.riskAttentionCount)} risk</span>
            </div>
          ) : null}
        </aside>

        <section className={styles.missionPanel} aria-labelledby="aios-v2-situation-missions-title">
          <header className={styles.panelHeader}>
            <div>
              <span>2 · Mission condition</span>
              <h2 id="aios-v2-situation-missions-title">What is moving or blocked</h2>
            </div>
            <small>{metricReturned(summary?.missionCount ?? null, loading)}</small>
          </header>

          {loading ? (
            <div className={styles.emptyState} role="status">Reading canonical Mission projection…</div>
          ) : coverage?.livingOrganization === "unavailable" ? (
            <div className={styles.emptyState} role="status">Living Organization source unavailable. No zero-Mission conclusion is made.</div>
          ) : coverage?.livingOrganization === "not_established" ? (
            <div className={styles.emptyState} role="status">No Mission projection is established for the connected Living Organization scene.</div>
          ) : data?.missions.length ? (
            <div className={styles.missionList}>
              {data.missions.slice(0, 4).map((mission) => (
                <article className={styles.missionRow} data-blocked={String(mission.blockerCount > 0)} key={mission.missionKey}>
                  <div className={styles.missionState}>
                    <span>{mission.state.replaceAll("_", " ")}</span>
                    {mission.phaseKey ? <small>{mission.phaseKey.replaceAll("_", " ")}</small> : null}
                  </div>
                  <strong>{mission.title}</strong>
                  <div className={styles.missionMetrics}>
                    <span>{mission.blockerCount} blocker{mission.blockerCount === 1 ? "" : "s"}</span>
                    <span>{mission.decisionCount} decision{mission.decisionCount === 1 ? "" : "s"}</span>
                    <span>{mission.participantCount} participant{mission.participantCount === 1 ? "" : "s"}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState} role="status">The established Living Organization projection returned zero Missions.</div>
          )}

          <Link className={styles.inspectLink} href="/cockpit/v2/organization">Inspect Mission context in Organization</Link>
        </section>
      </section>

      <section className={styles.contextGrid} aria-label="Owner context">
        <article className={styles.organizationPanel} aria-labelledby="aios-v2-situation-organization-title">
          <header className={styles.panelHeader}>
            <div>
              <span>3 · Organization condition</span>
              <h2 id="aios-v2-situation-organization-title">Living Organization</h2>
            </div>
            <Link href="/cockpit/v2/organization">Open Organization</Link>
          </header>

          {summary ? (
            <div className={styles.organizationReadout} aria-label="Organization context summary">
              <span>{formatV2CountTruth(summary.departmentCount)} departments</span>
              <span>{formatV2CountTruth(summary.rosteredEmployeeCount)} rostered</span>
              <span>{formatV2CountTruth(summary.organizationActiveBlockerCount)} active blockers</span>
              <span>{formatV2CountTruth(summary.missionCount)} Missions</span>
            </div>
          ) : null}

          <div className={styles.organizationViewport}>
            <V2OrganizationBlockout compact loading={loading} organization={data?.organization || null} />
          </div>
        </article>

        <article className={styles.activityPanel} aria-labelledby="aios-v2-situation-activity-title">
          <header className={styles.panelHeader}>
            <div>
              <span>4 · Significant change</span>
              <h2 id="aios-v2-situation-activity-title">Recent Activity</h2>
            </div>
            <small>{metricReturned(summary?.recentChangeCount ?? null, loading)}</small>
          </header>

          {loading ? (
            <div className={styles.emptyState} role="status">Reading canonical Activity…</div>
          ) : coverage?.activity === "unavailable" ? (
            <div className={styles.emptyState} role="status">Activity source unavailable. No zero-Activity conclusion is made.</div>
          ) : data?.recentChanges.length ? (
            <ol className={styles.activityList}>
              {data.recentChanges.slice(0, 5).map((change) => (
                <li key={change.id}>
                  <span className={styles.activityMarker} aria-hidden="true" />
                  <div>
                    <strong>{change.title}</strong>
                    <p>{change.summary}</p>
                    <small>
                      {change.activityClass.replaceAll("_", " ")}
                      {change.department ? ` · ${change.department}` : ""}
                      {` · ${formatUtc(change.occurredAt)}`}
                    </small>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className={styles.emptyState} role="status">The available bounded Activity read returned zero recent records.</div>
          )}
        </article>
      </section>

      <div className="aios-v2-foundation-note" role="note">
        Situation-room posture: numeric zero is shown only when the required governed source coverage is available; incomplete metrics remain Unknown, Unavailable, Not established or a proven lower bound. Mission blocker counts come from the canonical projection, employee figures are roster counts rather than presence claims, and this page has no mutation authority.
      </div>
    </div>
  );
}
