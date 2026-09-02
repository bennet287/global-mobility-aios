"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { LivingOrganizationSceneView } from "../../../components/LivingOrganizationScene";
import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import {
  type AustriaLiveOrganizationLatest,
  type LivingOrganizationSceneLatest,
  LiveOrganizationRequestError,
  getLatestAustriaLiveOrganization,
  getLatestAustriaLivingScene,
  synthesizeAustriaOwner,
} from "../../../lib/live-organization";
import { titleCase } from "../../../lib/utils";

type LiveOrganizationLoadError = {
  status: number | null;
  message: string;
};

function positionLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function latencyLabel(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Not recorded";
  return `${value} ms`;
}

function tokenLabel(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Not recorded";
  return new Intl.NumberFormat().format(value);
}

function costLabel(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Not recorded";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 6,
  }).format(value);
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

function unavailableTitle(error: LiveOrganizationLoadError | null): string {
  if (error?.status === 401) return "Board authentication required";
  if (error?.status === 403) return "Board access not permitted";
  if (error) return "Live organization unavailable";
  return "Austria live cycle not yet established";
}

function errorLabel(error: LiveOrganizationLoadError): string {
  if (error.status === 401) return "Board authentication required.";
  if (error.status === 403) return "Board transparency access denied.";
  return "Live organization data unavailable.";
}

export default function AustriaLiveOrganizationPage() {
  const { health, error: healthError } = useBackendStatus();
  const [latest, setLatest] = useState<AustriaLiveOrganizationLatest | null>(null);
  const [sceneLatest, setSceneLatest] = useState<LivingOrganizationSceneLatest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<LiveOrganizationLoadError | null>(null);
  const [sceneError, setSceneError] = useState<LiveOrganizationLoadError | null>(null);
  const [commandSubmitting, setCommandSubmitting] = useState(false);
  const [commandMessage, setCommandMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSceneError(null);
    try {
      const persisted = await getLatestAustriaLiveOrganization();
      setLatest(persisted);
      try {
        setSceneLatest(await getLatestAustriaLivingScene());
      } catch (sceneLoadError) {
        setSceneLatest(null);
        setSceneError(
          sceneLoadError instanceof LiveOrganizationRequestError
            ? { status: sceneLoadError.status, message: sceneLoadError.message }
            : {
                status: null,
                message: sceneLoadError instanceof Error ? sceneLoadError.message : "Living Organization scene is unavailable.",
              },
        );
      }
    } catch (loadError) {
      setLatest(null);
      setSceneLatest(null);
      setError(
        loadError instanceof LiveOrganizationRequestError
          ? { status: loadError.status, message: loadError.message }
          : {
              status: null,
              message: loadError instanceof Error ? loadError.message : "Live organization data is unavailable.",
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
  const scene = sceneLatest?.scene ?? null;
  const sceneMismatch = Boolean(
    snapshot
    && scene
    && scene.root_work_item_id !== snapshot.root_work_item_id,
  );
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

  const runtimeSummary = useMemo(() => {
    const qualities = snapshot?.specialist_outputs
      .map((item) => item.runtime_quality)
      .filter((quality) => quality != null) ?? [];
    const tokenSamples = qualities
      .map((quality) => quality.total_tokens)
      .filter((value): value is number => value !== null);
    const costSamples = qualities
      .map((quality) => quality.estimated_cost_usd)
      .filter((value): value is number => value !== null);
    return {
      observed: qualities.length,
      totalTokens: tokenSamples.length ? tokenSamples.reduce((sum, value) => sum + value, 0) : null,
      estimatedCostUsd: costSamples.length ? costSamples.reduce((sum, value) => sum + value, 0) : null,
      freshGrounded: qualities.filter((quality) => quality.fresh_retrieval_provenance_present).length,
      fallbackCount: qualities.filter((quality) => quality.fallback_to_template).length,
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
      : error || sceneError || sceneMismatch || healthError
        ? "partial"
        : "ready";

  const heroTitle = snapshot
    ? titleCase(snapshot.cycle_status)
    : loading
      ? "Loading persisted Austria cycle"
      : unavailableTitle(error);

  const authorityState = snapshot
    ? titleCase(snapshot.authority_posture)
    : loading
      ? "Loading"
      : error?.status === 401
        ? "Authentication required"
        : error?.status === 403
          ? "Access denied"
          : error
            ? "Unavailable"
            : "Not established";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Live Organization"
        kicker="Global Mobility AIOS Cockpit · M.7.1 Organization Lenses + Owner view commands"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command" aria-labelledby="live-organization-state-title">
        <div className="cockpit-command-copy">
          <div className="cockpit-live-line">
            <span className="cockpit-live-dot" aria-hidden="true" />
            <span>Persisted organization cycle</span>
            <small>
              {snapshot
                ? `Updated ${timeLabel(snapshot.generated_at)}`
                : loading
                  ? "Loading persisted state"
                  : error
                    ? "Persisted state unavailable"
                    : "No simulated state"}
            </small>
          </div>
          <h2 id="live-organization-state-title">{heroTitle}</h2>
          <p>
            {error
              ? "The Cockpit could not read the canonical Austria owner/specialist projection, so it does not infer whether a live cycle exists, what its authority posture is, or whether work is ready."
              : "This Cockpit surface reads the canonical Austria owner/specialist cycle only from persisted AIOS records. It does not manufacture completion, evidence, runtime status, or authority for presentation."}
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
          <strong>{authorityState}</strong>
          <p>
            {snapshot
              ? `Provider/model authority: ${snapshot.provider_model_authority ? "present" : "none"}. External action: ${snapshot.external_action_authorized ? "authorized" : "not authorized"}.`
              : error
                ? "No authority posture is inferred while the persisted projection is unavailable."
                : loading
                  ? "Waiting for the authoritative persisted projection."
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
          <strong>{errorLabel(error)}</strong><span>{error.message}</span>
        </div>
      ) : null}
      {commandMessage ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Owner command.</strong><span>{commandMessage}</span>
        </div>
      ) : null}

      {sceneError ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Scene projection unavailable.</strong><span>{sceneError.message}</span>
        </div>
      ) : null}
      {sceneMismatch ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Scene projection changed during refresh.</strong>
          <span>The scene root does not match the current persisted cycle, so the Cockpit does not render mixed canonical states. Refresh to reconcile.</span>
        </div>
      ) : null}

      {snapshot && scene && !sceneMismatch ? <LivingOrganizationSceneView scene={scene} /> : null}
      {snapshot && !scene && !sceneError && !loading ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Living Organization scene not established.</strong>
          <span>The canonical L cycle is available, but no scene projection was returned. The Cockpit does not synthesize one locally.</span>
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
                <div className="cockpit-lane"><header><span>SourceSnapshots</span><strong>{snapshot.source_snapshot_refs.length}</strong></header><p>{snapshot.source_snapshot_refs.length ? "Persisted official-source snapshot provenance is attached; this view does not claim retrieval freshness." : "No SourceSnapshot provenance is attached to the current specialist outputs; freshness is not implied."}</p></div>
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

          <section className="cockpit-surface" aria-labelledby="live-activity-lineage-title">
            <header className="cockpit-surface-header compact">
              <div>
                <span className="premium-label">Durable activity lineage</span>
                <h3 id="live-activity-lineage-title">Persisted organizational activity</h3>
              </div>
              <span className="live-activity-total">{snapshot.activities.length}</span>
            </header>
            {snapshot.activities.length ? (
              <div className="live-activity-list">
                {snapshot.activities.map((activity) => (
                  <article key={activity.activity_id}>
                    <time>{timeLabel(activity.occurred_at)}</time>
                    <span className={`activity-mark ${activity.board_inspectable ? "decision" : "warning"}`} aria-hidden="true" />
                    <div>
                      <strong>{activity.title}</strong>
                      <p>{activity.summary}</p>
                      <small>
                        {positionLabel(activity.position_key || activity.actor_id)} · {titleCase(activity.role)} · {titleCase(activity.activity_type)}
                        {activity.work_item_id ? ` · WorkItem ${activity.work_item_id.slice(0, 8)}` : ""}
                      </small>
                      <small>
                        {activity.trace_id ? `Trace ${activity.trace_id}` : "No trace identifier"} ·{" "}
                        {activity.causation_activity_id
                          ? `Caused by ${activity.causation_activity_id.slice(0, 8)}`
                          : "No persisted causation link"}
                      </small>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="cockpit-empty-line">No durable OrganizationActivity is persisted for this objective yet.</div>
            )}
            <div className="cockpit-empty-line">
              This view renders only canonical AIOS OrganizationActivity lineage. Provider transcripts, tool logs, and donor event streams are not promoted to organizational truth.
            </div>
          </section>

          <section className="cockpit-surface" aria-labelledby="live-runtime-quality-title">
            <header className="cockpit-surface-header compact">
              <div>
                <span className="premium-label">Runtime economics & quality</span>
                <h3 id="live-runtime-quality-title">Persisted specialist runtime signals</h3>
              </div>
              <span className="live-activity-total">{runtimeSummary.observed}/{snapshot.specialist_outputs.length}</span>
            </header>
            <div className="operational-intelligence-grid">
              <div className="cockpit-lane"><header><span>Total tokens</span><strong>{tokenLabel(runtimeSummary.totalTokens)}</strong></header><p>Summed only from specialist runtime-quality records that persisted token usage.</p></div>
              <div className="cockpit-lane"><header><span>Estimated provider cost</span><strong>{costLabel(runtimeSummary.estimatedCostUsd)}</strong></header><p>Derived only from persisted provider estimates; missing costs are not inferred as zero.</p></div>
              <div className="cockpit-lane"><header><span>Fresh retrieval provenance</span><strong>{runtimeSummary.freshGrounded}/{runtimeSummary.observed}</strong></header><p>Counts runtime records that explicitly preserve fresh-retrieval provenance.</p></div>
              <div className="cockpit-lane"><header><span>Template fallback</span><strong>{runtimeSummary.fallbackCount}</strong></header><p>Observed fallback is a runtime-quality signal, not an authority or correctness decision.</p></div>
            </div>
            {snapshot.specialist_outputs.map((specialist) => {
              const quality = specialist.runtime_quality;
              return (
                <div className="attention-rows" key={`runtime-${specialist.work_item_id}`}>
                  <div><span>{positionLabel(specialist.position_key)}</span><strong>{quality ? titleCase(quality.provider_outcome) : "Not recorded"}</strong></div>
                  <div><span>Runtime</span><strong>{quality ? `${quality.response_provider || quality.configured_provider || "Unknown provider"} · ${quality.response_model || quality.configured_model || "unknown model"}` : "Not recorded"}</strong></div>
                  <div><span>Tokens / cost</span><strong>{quality ? `${tokenLabel(quality.total_tokens)} · ${costLabel(quality.estimated_cost_usd)}` : "Not recorded"}</strong></div>
                  <div><span>Grounding</span><strong>{quality ? titleCase(quality.grounding_state) : "Not recorded"}</strong></div>
                </div>
              );
            })}
            <div className="cockpit-empty-line">
              Telemetry is presentation evidence only. It does not create OrganizationActivity, grant provider/model authority, or authorize external action.
            </div>
          </section>
        </>
      ) : null}
    </WorkspaceShell>
  );
}
