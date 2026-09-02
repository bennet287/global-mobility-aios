"use client";

import type { OrganizationReplay } from "../lib/live-organization";
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

export function LivingOrganizationReplayTimeline({ replay }: { replay: OrganizationReplay }) {
  const incompleteEvents = replay.events.filter((event) => event.coverage_state !== "covered");
  const coverage = replay.coverage;
  const coverageState = coverage.activity_history_established ? "established" : "partial";

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
          <span className="premium-label">M.8.1 · Canonical Replay Timeline V1</span>
          <h3 id="living-replay-title">Replay / Temporal Organization</h3>
          <p>
            Ordered persisted semantic Activity for the latest Austria WorkItem tree. Replay does not interpolate,
            backfill, reconstruct chat transcripts, or mutate AIOS. Missing history remains explicitly missing.
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
            </article>
          </li>
        ))}
      </ol>

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
