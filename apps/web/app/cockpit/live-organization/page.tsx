"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import {
  type AustriaLiveOrganizationLatest,
  getLatestAustriaLiveOrganization,
  synthesizeAustriaOwner,
} from "../../../lib/live-organization";
import { titleCase } from "../../../lib/utils";

function positionLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function latencyLabel(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Not recorded";
  return `${value} ms`;
}

function timeLabel(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function AustriaLiveOrganizationPage() {
  const { health, error: healthError } = useBackendStatus();
  const [latest, setLatest] = useState<AustriaLiveOrganizationLatest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [commandSubmitting, setCommandSubmitting] = useState(false);
  const [commandMessage, setCommandMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setLatest(await getLatestAustriaLiveOrganization());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Live organization data is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const snapshot = latest?.snapshot ?? null;
  const canSynthesize = Boolean(
    snapshot
    && snapshot.root_status === "running"
    && snapshot.ready_for_owner_synthesis
    && snapshot.owner_synthesis === null,
  );

  const specialistStatus = useMemo(() => {
    if (!snapshot) return { valid: 0, total: 0 };
    return {
      valid: snapshot.specialist_outputs.filter((item) => item.evidence_valid).length,
      total: snapshot.specialist_outputs.length,
    };
  }, [snapshot]);

  const runOwnerSynthesis = async () => {
    if (!snapshot || !canSynthesize) return;
    setCommandSubmitting(true);
    setCommandMessage(null);
    try {
      const result = await synthesizeAustriaOwner(snapshot.root_work_item_id);
      setCommandMessage(
        result.replayed
          ? "The existing bounded owner synthesis was replayed without creating duplicate evidence."
          : "The Mobility Operations Lead synthesis was persisted and moved the cycle to human review.",
      );
      await load();
    } catch (commandError) {
      setCommandMessage(
        commandError instanceof Error
          ? commandError.message
          : "The bounded owner-synthesis command was rejected.",
      );
    } finally {
      setCommandSubmitting(false);
    }
  };

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
        title="Live Organization"
        kicker="Global Mobility AIOS Cockpit · Austria L.1"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command" aria-labelledby="live-organization-state-title">
        <div className="cockpit-command-copy">
          <div className="cockpit-live-line">
            <span className="cockpit-live-dot" aria-hidden="true" />
            <span>Persisted organization cycle</span>
            <small>{snapshot ? `Updated ${timeLabel(snapshot.generated_at)}` : "No simulated state"}</small>
          </div>
          <h2 id="live-organization-state-title">
            {snapshot ? titleCase(snapshot.cycle_status) : "Austria live cycle not yet established"}
          </h2>
          <p>
            This Cockpit surface reads the canonical Austria owner/specialist cycle only from persisted AIOS records.
            It does not manufacture completion, evidence, runtime status, or authority for presentation.
          </p>
          <div className="cockpit-command-actions">
            <button
              className="premium-button primary"
              type="button"
              disabled={!canSynthesize || commandSubmitting}
              onClick={() => void runOwnerSynthesis()}
            >
              {commandSubmitting ? "Recording owner synthesis…" : "Record bounded owner synthesis"}
            </button>
            <button className="premium-button ghost" type="button" onClick={() => void load()}>
              Refresh persisted state
            </button>
          </div>
        </div>

        <aside className="cockpit-command-state" aria-label="Live organization authority posture">
          <span>Authority posture</span>
          <strong>{snapshot ? titleCase(snapshot.authority_posture) : "Not established"}</strong>
          <p>
            {snapshot
              ? `Provider/model authority: ${snapshot.provider_model_authority ? "present" : "none"}. External action: ${snapshot.external_action_authorized ? "authorized" : "not authorized"}.`
              : "No objective record is currently available to project an authority posture."}
          </p>
          <div className="cockpit-state-rule">
            <i aria-hidden="true" />
            <span>Backend readiness and authority gates remain authoritative</span>
          </div>
        </aside>

        <div className="cockpit-command-metrics" aria-label="Austria live organization metrics">
          <article><strong>{snapshot ? specialistStatus.valid : "—"}</strong><span>Valid specialist outputs</span></article>
          <article><strong>{snapshot?.blockers.length ?? "—"}</strong><span>Active blockers</span></article>
          <article><strong>{snapshot?.activity_count ?? "—"}</strong><span>Durable activities</span></article>
          <article><strong>{snapshot ? latencyLabel(snapshot.total_latency_ms) : "—"}</strong><span>Specialist latency</span></article>
          <article><strong>{snapshot?.total_retry_count ?? "—"}</strong><span>Recorded retries</span></article>
        </div>
      </section>

      {error ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Live organization data unavailable.</strong><span>{error}</span>
        </div>
      ) : null}
      {commandMessage ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Owner command.</strong><span>{commandMessage}</span>
        </div>
      ) : null}

      {!loading && !error && !snapshot ? (
        <section className="cockpit-surface" aria-labelledby="live-cycle-empty-title">
          <header className="cockpit-surface-header compact">
            <div><span className="premium-label">Persisted truth</span><h3 id="live-cycle-empty-title">No Austria cycle exists yet</h3></div>
          </header>
          <div className="cockpit-empty-line">
            No persisted J/K/L Austria objective is available. The Cockpit does not simulate a live organization cycle to fill this view.
          </div>
        </section>
      ) : null}

      {snapshot ? (
        <>
          <section className="cockpit-primary-grid">
            <article className="cockpit-surface" aria-labelledby="live-cycle-title">
              <header className="cockpit-surface-header compact">
                <div>
                  <span className="premium-label">Owner-led cycle</span>
                  <h3 id="live-cycle-title">{snapshot.objective_key}</h3>
                </div>
                <span className="cockpit-surface-status"><i aria-hidden="true" />{titleCase(snapshot.root_status)}</span>
              </header>

              <div className="live-activity-list">
                <article>
                  <time>Owner</time>
                  <span className="activity-mark decision" aria-hidden="true" />
                  <div>
                    <strong>{positionLabel(snapshot.owner_position_key)}</strong>
                    <p>{snapshot.owner_synthesis ? snapshot.owner_synthesis.recommendation : "Owner synthesis has not been materialized."}</p>
                    <small>{snapshot.authority_level} · {titleCase(snapshot.owner_synthesis_state)}</small>
                  </div>
                </article>
                {snapshot.specialist_outputs.map((specialist) => (
                  <article key={specialist.work_item_id}>
                    <time>{specialist.evidence_valid ? "Current" : "Hold"}</time>
                    <span className={`activity-mark ${specialist.evidence_valid ? "decision" : "warning"}`} aria-hidden="true" />
                    <div>
                      <strong>{positionLabel(specialist.position_key)}</strong>
                      <p>{specialist.evidence_reason || "Current K.1 execution evidence resolves to durable AgentRun and execution-attempt lineage."}</p>
                      <small>
                        {titleCase(specialist.status)} · {latencyLabel(specialist.latency_ms)} · {specialist.retry_count ?? 0} retries · confidence {specialist.confidence ?? "—"}
                      </small>
                    </div>
                  </article>
                ))}
              </div>
            </article>

            <article className="cockpit-surface owner-attention" aria-labelledby="live-authority-title">
              <header className="cockpit-surface-header compact">
                <div><span className="premium-label">Authority & readiness</span><h3 id="live-authority-title">Bounded execution state</h3></div>
              </header>

              <div className={`owner-attention-state ${canSynthesize ? "needs-attention" : "clear"}`}>
                <span className="attention-emblem" aria-hidden="true">{canSynthesize ? "!" : "✓"}</span>
                <div>
                  <strong>{canSynthesize ? "Owner synthesis is ready for a Board-authorized command." : titleCase(snapshot.owner_synthesis_state)}</strong>
                  <p>
                    {snapshot.owner_synthesis
                      ? "The owner result is persisted, remains human-review gated, and grants no external-action authority."
                      : snapshot.ready_for_owner_synthesis
                        ? "Both required specialist outputs are current and provenance-valid."
                        : "The backend readiness gate has not authorized owner synthesis."}
                  </p>
                </div>
              </div>

              <div className="attention-rows">
                <div><span>Root WorkItem</span><strong>{snapshot.root_work_item_id.slice(0, 8)}</strong></div>
                <div><span>Specialist evidence</span><strong>{specialistStatus.valid}/{specialistStatus.total}</strong></div>
                <div><span>Provider/model authority</span><strong>{snapshot.provider_model_authority ? "Present" : "None"}</strong></div>
                <div><span>External action</span><strong>{snapshot.external_action_authorized ? "Authorized" : "Not authorized"}</strong></div>
              </div>

              {!snapshot.ready_for_owner_synthesis && snapshot.readiness_reasons.length ? (
                <div className="owner-human-lane">
                  <span>Readiness reasons</span>
                  {snapshot.readiness_reasons.map((reason) => <div key={reason}><strong>{reason}</strong></div>)}
                </div>
              ) : null}
            </article>
          </section>

          <section className="cockpit-secondary-grid">
            <article className="cockpit-surface" aria-labelledby="live-provenance-title">
              <header className="cockpit-surface-header compact">
                <div><span className="premium-label">Truth provenance</span><h3 id="live-provenance-title">What this L.1 cycle actually knows</h3></div>
              </header>
              <div className="operational-intelligence-grid">
                <div className="cockpit-lane"><header><span>Domain Evidence</span><strong>{snapshot.domain_evidence_refs.length}</strong></header><p>{snapshot.domain_evidence_refs.length ? "Persisted domain Evidence references are attached." : "Not connected in this L.1 slice; no Evidence is fabricated by the UI."}</p></div>
                <div className="cockpit-lane"><header><span>VerifiedRules</span><strong>{snapshot.verified_rule_refs.length}</strong></header><p>{snapshot.verified_rule_refs.length ? "Persisted verified-rule references are attached." : "Not connected in this L.1 slice; regulatory truth is not implied."}</p></div>
                <div className="cockpit-lane"><header><span>Autonomy profile</span><strong>{snapshot.autonomy_profile_state ? titleCase(snapshot.autonomy_profile_state) : "None"}</strong></header><p>No model or provider receives authority from this projection.</p></div>
                <div className="cockpit-lane"><header><span>Owner disposition</span><strong>{snapshot.owner_synthesis ? titleCase(snapshot.owner_synthesis.disposition) : "Pending"}</strong></header><p>{snapshot.owner_synthesis?.human_review_required ? "Human review is required." : "No completed owner disposition is currently asserted."}</p></div>
              </div>
            </article>

            <article className="cockpit-surface" aria-labelledby="live-blockers-title">
              <header className="cockpit-surface-header compact">
                <div><span className="premium-label">Blocked work</span><h3 id="live-blockers-title">Current objective blockers</h3></div>
                <span className="live-activity-total">{snapshot.blockers.length}</span>
              </header>
              {snapshot.blockers.length ? (
                <ul className="cockpit-lane-list">
                  {snapshot.blockers.map((blocker) => (
                    <li key={blocker.blocker_id}>
                      <span>{titleCase(blocker.severity)}</span>
                      <strong>{blocker.title}</strong>
                      <small>{titleCase(blocker.status)} · {positionLabel(blocker.accountable_position_key || "unassigned")} · human action {blocker.requires_human_action ? "required" : "not required"}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="cockpit-empty-line">No active blocker is persisted for this Austria objective.</div>
              )}
            </article>
          </section>
        </>
      ) : null}
    </WorkspaceShell>
  );
}
