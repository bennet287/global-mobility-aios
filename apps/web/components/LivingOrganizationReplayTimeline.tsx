"use client";

import { useState } from "react";

import {
  getLatestAustriaOrganizationReplayState,
  getLatestAustriaOrganizationReplayStateDiff,
  type OrganizationReplay,
  type OrganizationReplayState,
  type OrganizationReplayStateDiff,
  type OrganizationReplayStateDelta,
} from "../lib/live-organization";
import { titleCase } from "../lib/utils";

function replayTime(value: string): string {
  return `${value.slice(0, 16).replace("T", " ")} UTC`;
}

function shortId(value: string | null): string {
  return value ? value.slice(0, 8) : "—";
}

function coverageLabel(value: string): string {
  if (value === "covered") return "Covered";
  if (value === "pre_epoch_partial") return "Pre-epoch · partial";
  if (value === "partial_no_epoch") return "Partial · no epoch";
  return titleCase(value);
}

type ReplayDiffStatusState = {
  status: string;
  coverage_state: string;
};

function ReplayDiffList({
  label,
  items,
}: {
  label: string;
  items: OrganizationReplayStateDelta<ReplayDiffStatusState>[];
}) {
  return (
    <article>
      <span>{label}</span>
      {items.length ? items.map((item) => (
        <div key={item.entity_id} data-replay-delta={item.entity_id} data-replay-change-kind={item.change_kind}>
          <strong>{shortId(item.entity_id)} · {titleCase(item.change_kind)}</strong>
          <small>
            {(item.before?.status ?? "not known")} → {(item.after?.status ?? "not known")}
            {item.changed_fields.length ? ` · ${item.changed_fields.join(" · ")}` : " · projection membership changed"}
          </small>
        </div>
      )) : <small>No supported changes in this dimension.</small>}
    </article>
  );
}

export function LivingOrganizationReplayTimeline({ replay }: { replay: OrganizationReplay }) {
  const [selectedState, setSelectedState] = useState<OrganizationReplayState | null>(null);
  const [stateLoading, setStateLoading] = useState(false);
  const [stateError, setStateError] = useState<string | null>(null);
  const [comparisonStartActivityId, setComparisonStartActivityId] = useState<string | null>(null);
  const [comparison, setComparison] = useState<OrganizationReplayStateDiff | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const incompleteEvents = replay.events.filter((event) => event.coverage_state !== "covered");
  const coverage = replay.coverage;
  const coverageState = coverage.activity_history_established ? "established" : "partial";

  async function inspectState(activityId: string) {
    setStateLoading(true);
    setStateError(null);
    try {
      const state = await getLatestAustriaOrganizationReplayState(activityId);
      if (state.root_work_item_id !== replay.root_work_item_id) {
        setSelectedState(null);
        setStateError("Historical state root changed during inspection. Refresh before comparing temporal state.");
        return;
      }
      setSelectedState(state);
    } catch (error) {
      setSelectedState(null);
      setStateError(error instanceof Error ? error.message : "Historical state is unavailable.");
    } finally {
      setStateLoading(false);
    }
  }

  function setComparisonStart(activityId: string) {
    setComparisonStartActivityId(activityId);
    setComparison(null);
    setComparisonError(null);
  }

  async function compareFromStart(toActivityId: string) {
    if (!comparisonStartActivityId) return;
    setComparisonLoading(true);
    setComparisonError(null);
    try {
      const next = await getLatestAustriaOrganizationReplayStateDiff(
        comparisonStartActivityId,
        toActivityId,
      );
      if (next.root_work_item_id !== replay.root_work_item_id) {
        setComparison(null);
        setComparisonError("Temporal comparison root changed during inspection. Refresh before comparing state.");
        return;
      }
      if (
        next.from_cursor.activity_id !== comparisonStartActivityId
        || next.to_cursor.activity_id !== toActivityId
      ) {
        setComparison(null);
        setComparisonError("Temporal comparison cursor identity changed during inspection.");
        return;
      }
      setComparison(next);
    } catch (error) {
      setComparison(null);
      setComparisonError(error instanceof Error ? error.message : "Temporal comparison is unavailable.");
    } finally {
      setComparisonLoading(false);
    }
  }

  return (
    <section
      className="living-replay-shell"
      aria-labelledby="living-replay-title"
      data-replay-authoritative={String(replay.authoritative)}
      data-replay-mutates-work={String(replay.mutations_allowed)}
      data-replay-coverage={coverageState}
    >
      <header className="living-replay-header">
        <div>
          <span className="premium-label">M.8.3 · Temporal State Comparison / Diff V1</span>
          <h3 id="living-replay-title">Replay / Temporal Organization</h3>
          <p>
            Ordered persisted semantic Activity for the latest Austria WorkItem tree, explicit M.8.2 as-of inspection,
            and bounded comparison between two proven Activity-cursor states. Diffing reuses reconstructed state; it does
            not create another timeline, infer missing history, read current rows as past truth, or mutate AIOS.
          </p>
        </div>
        <div className="living-replay-contract">
          <span>{replay.contract_version}</span>
          <strong>{replay.returned_events} / {replay.total_events} events</strong>
          <small>{replay.truncated ? "Newest bounded window · truncated" : "Complete returned window"}</small>
        </div>
      </header>

      <div className="living-replay-coverage" role="status">
        <div>
          <span>Coverage posture</span>
          <strong>{coverage.activity_history_established ? "Explicit epoch established" : "Partial Activity coverage"}</strong>
          <small>
            {coverage.activity_history_coverage_start
              ? `Authoritative curated Activity from ${replayTime(coverage.activity_history_coverage_start)} forward.`
              : "No explicit Activity coverage epoch exists; all historical completeness claims remain unavailable."}
          </small>
        </div>
        <div>
          <span>Pre-epoch history</span>
          <strong>{titleCase(coverage.pre_epoch_history)}</strong>
          <small>{incompleteEvents.length} returned event{incompleteEvents.length === 1 ? "" : "s"} outside complete coverage.</small>
        </div>
        <div>
          <span>Conversation truth</span>
          <strong>Lifecycle only</strong>
          <small>Transcript content is not persisted and is never reconstructed.</small>
        </div>
        <div>
          <span>Known replay gaps</span>
          <strong>Risk + source history unavailable</strong>
          <small>{coverage.risk_escalation_history} · {coverage.source_snapshot_history}</small>
        </div>
      </div>

      <ol className="living-replay-timeline" aria-label="Canonical organization replay events">
        {replay.events.map((event) => (
          <li
            key={event.activity_id}
            data-replay-event={event.activity_id}
            data-replay-kind={event.event_kind}
            data-replay-coverage-state={event.coverage_state}
          >
            <div className="living-replay-time">
              <time dateTime={event.occurred_at}>{replayTime(event.occurred_at)}</time>
              <span>{coverageLabel(event.coverage_state)}</span>
            </div>
            <i aria-hidden="true" />
            <article>
              <header>
                <span>{titleCase(event.event_kind)} · seq {event.stream_sequence}</span>
                <small>{event.activity_type}</small>
              </header>
              <strong>{event.title}</strong>
              <p>{event.summary}</p>
              <footer>
                <span>{event.actor_type}:{event.actor_id}</span>
                <span>Work {shortId(event.work_item_id)}</span>
                <span>Source {event.source_object_type}:{shortId(event.source_object_id)}</span>
                {event.causation_activity_id ? <span>Causation {shortId(event.causation_activity_id)}</span> : null}
                {event.supersedes_activity_id ? <span>Supersedes {shortId(event.supersedes_activity_id)}</span> : null}
              </footer>
              <div className="living-replay-event-actions">
                <button
                  className="living-replay-state-button"
                  type="button"
                  onClick={() => void inspectState(event.activity_id)}
                  disabled={stateLoading}
                >
                  Inspect state here
                </button>
                <button
                  className="living-replay-state-button"
                  type="button"
                  onClick={() => setComparisonStart(event.activity_id)}
                  aria-pressed={comparisonStartActivityId === event.activity_id}
                  disabled={comparisonLoading}
                >
                  {comparisonStartActivityId === event.activity_id ? "Comparison start" : "Set compare start"}
                </button>
                {comparisonStartActivityId && comparisonStartActivityId !== event.activity_id ? (
                  <button
                    className="living-replay-state-button"
                    type="button"
                    onClick={() => void compareFromStart(event.activity_id)}
                    disabled={comparisonLoading}
                  >
                    Compare from start
                  </button>
                ) : null}
              </div>
            </article>
          </li>
        ))}
      </ol>

      {comparisonStartActivityId && !comparison && !comparisonError ? (
        <div className="living-replay-diff-hint" data-replay-comparison-start={comparisonStartActivityId}>
          <strong>Comparison start set at {shortId(comparisonStartActivityId)}.</strong>
          <span>Select another persisted Activity and choose “Compare from start”.</span>
        </div>
      ) : null}

      {comparisonError ? (
        <div className="living-replay-state-error" role="status">
          <strong>Temporal comparison unavailable.</strong>
          <span>{comparisonError}</span>
        </div>
      ) : null}

      {comparison ? (
        <section
          className="living-replay-diff"
          aria-labelledby="living-replay-diff-title"
          data-replay-diff-authoritative={String(comparison.authoritative)}
          data-replay-diff-mutates-work={String(comparison.mutations_allowed)}
          data-replay-diff-posture={comparison.comparison_posture}
        >
          <header>
            <div>
              <span>M.8.3 · Two-cursor canonical projection diff</span>
              <strong id="living-replay-diff-title">
                What changed from {shortId(comparison.from_cursor.activity_id)} → {shortId(comparison.to_cursor.activity_id)}
              </strong>
            </div>
            <small>{titleCase(comparison.comparison_posture)} · {comparison.changed_entity_count} changed entities</small>
          </header>

          <div className="living-replay-state-summary">
            <div><strong>{comparison.work_items.length}</strong><span>WorkItem deltas</span></div>
            <div><strong>{comparison.blockers.length}</strong><span>blocker deltas</span></div>
            <div><strong>{comparison.decisions.length}</strong><span>decision deltas</span></div>
            <div><strong>{comparison.human_requests.length}</strong><span>human deltas</span></div>
            <div><strong>{comparison.conversations.length}</strong><span>conversation deltas</span></div>
            <div><strong>{comparison.changed_entity_count}</strong><span>changed entities</span></div>
          </div>

          <div className="living-replay-diff-grid">
            <ReplayDiffList label="WORKITEMS" items={comparison.work_items} />
            <ReplayDiffList label="BLOCKERS" items={comparison.blockers} />
            <ReplayDiffList label="DECISIONS" items={comparison.decisions} />
            <ReplayDiffList label="HUMAN REQUESTS" items={comparison.human_requests} />
            <ReplayDiffList label="CONVERSATIONS" items={comparison.conversations} />
          </div>

          <footer>
            <strong>Comparison truth boundary</strong>
            <span>{comparison.unsupported_dimensions.join(" · ")}</span>
            <small>
              This compares two M.8.2 projections only. Added/removed means membership differs between those projections;
              it does not invent creation, deletion, transcript, deadline, evidence-content, risk-escalation, or source history.
              Unchanged entities are omitted.
            </small>
          </footer>
        </section>
      ) : null}

      {stateError ? (
        <div className="living-replay-state-error" role="status">
          <strong>Historical state unavailable.</strong>
          <span>{stateError}</span>
        </div>
      ) : null}

      {selectedState ? (
        <section
          className="living-replay-state"
          aria-labelledby="living-replay-state-title"
          data-replay-state-authoritative={String(selectedState.authoritative)}
          data-replay-state-mutates-work={String(selectedState.mutations_allowed)}
          data-replay-state-posture={selectedState.reconstruction_posture}
        >
          <header>
            <div>
              <span>M.8.2 · Activity-cursor reconstruction</span>
              <strong id="living-replay-state-title">Organization state at {shortId(selectedState.cursor_activity_id)}</strong>
            </div>
            <small>{replayTime(selectedState.cursor_occurred_at)} · {titleCase(selectedState.reconstruction_posture)}</small>
          </header>

          <div className="living-replay-state-summary">
            <div><strong>{selectedState.work_items.length}</strong><span>known WorkItems</span></div>
            <div><strong>{selectedState.blockers.length}</strong><span>known blockers</span></div>
            <div><strong>{selectedState.decisions.length}</strong><span>known decisions</span></div>
            <div><strong>{selectedState.human_requests.length}</strong><span>human requests</span></div>
            <div><strong>{selectedState.conversations.length}</strong><span>conversations</span></div>
            <div><strong>{selectedState.unapplied_transition_count}</strong><span>unapplied transitions</span></div>
          </div>

          <div className="living-replay-state-grid">
            <article>
              <span>WORKITEM STATE</span>
              {selectedState.work_items.length ? selectedState.work_items.map((item) => (
                <div key={item.work_item_id} data-historical-work-item={item.work_item_id}>
                  <strong>{shortId(item.work_item_id)} · {titleCase(item.status)}</strong>
                  <small>{item.assigned_position_key} · {item.department} · {coverageLabel(item.coverage_state)}</small>
                </div>
              )) : <small>No WorkItem creation Activity is known at this cursor.</small>}
            </article>

            <article>
              <span>GOVERNED ATTENTION</span>
              {selectedState.blockers.map((item) => (
                <div key={item.blocker_id}>
                  <strong>Blocker {shortId(item.blocker_id)} · {titleCase(item.status)}</strong>
                  <small>{item.blocker_type} · {item.severity} · {coverageLabel(item.coverage_state)}</small>
                </div>
              ))}
              {selectedState.decisions.map((item) => (
                <div key={item.decision_id}>
                  <strong>Decision {shortId(item.decision_id)} · {titleCase(item.status)}</strong>
                  <small>{item.decision_type} · {item.authority_level} · {coverageLabel(item.coverage_state)}</small>
                </div>
              ))}
              {selectedState.human_requests.map((item) => (
                <div key={item.request_id}>
                  <strong>Human request {shortId(item.request_id)} · {titleCase(item.status)}</strong>
                  <small>{item.request_type} · role {item.required_role} · {coverageLabel(item.coverage_state)}</small>
                </div>
              ))}
              {!selectedState.blockers.length && !selectedState.decisions.length && !selectedState.human_requests.length
                ? <small>No supported governed-attention creation Activity is known at this cursor.</small>
                : null}
            </article>

            <article>
              <span>COLLABORATION LIFECYCLE</span>
              {selectedState.conversations.length ? selectedState.conversations.map((item) => (
                <div key={item.conversation_id}>
                  <strong>{item.conversation_id} · {titleCase(item.status)}</strong>
                  <small>Lifecycle only · transcript not reconstructed · {coverageLabel(item.coverage_state)}</small>
                </div>
              )) : <small>No conversation lifecycle Activity is known at this cursor.</small>}
            </article>
          </div>

          <footer>
            <strong>Unsupported at this reconstruction version</strong>
            <span>{selectedState.unsupported_dimensions.join(" · ")}</span>
            <small>
              State is derived from persisted semantic Activity up to the selected cursor. Current domain rows are not
              read as historical state, and missing creation/transition history remains partial or unapplied.
            </small>
          </footer>
        </section>
      ) : null}

      {!replay.events.length ? (
        <div className="living-replay-empty">
          No persisted semantic Activity exists for this WorkItem tree. Replay does not synthesize a timeline.
        </div>
      ) : null}

      <footer className="living-replay-boundary">
        <strong>Temporal truth boundary</strong>
        <span>
          OrganizationActivity is the replay source. Current RiskEscalation records and SourceSnapshot references are not
          reverse-engineered into historical events where no semantic Activity adapter exists.
        </span>
      </footer>
    </section>
  );
}
