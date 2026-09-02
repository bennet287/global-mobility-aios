"use client";

import type { OrganizationEnvironmentalMemory } from "../lib/live-organization";
import { titleCase } from "../lib/utils";

function shortTime(value: string): string {
  return value.slice(0, 16).replace("T", " ") + " UTC";
}

function routeLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export function LivingOrganizationEnvironmentalMemory({
  memory,
}: {
  memory: OrganizationEnvironmentalMemory;
}) {
  const maxHeat = Math.max(1, ...memory.heat_cells.map((item) => item.event_count));
  const maxTimeline = Math.max(1, ...memory.timeline.map((item) => item.event_count));

  return (
    <section
      className="living-environmental-memory"
      aria-labelledby="living-environmental-memory-title"
      data-environmental-authoritative={String(memory.authoritative)}
      data-environmental-predictive={String(memory.predictive)}
      data-environmental-mutates-work={String(memory.mutations_allowed)}
      data-environmental-canonical-projection={String(memory.canonical_projection)}
    >
      <header className="living-environmental-memory-header">
        <div>
          <span className="premium-label">M.9.1 · Structured Environmental Memory Baseline</span>
          <h3 id="living-environmental-memory-title">Historical routing & activity memory</h3>
          <p>
            Deterministic aggregates from the sealed M.8 Replay window. This surface summarizes persisted history;
            it does not predict future movement, infer presence, create authority, or mutate AIOS.
          </p>
        </div>
        <div className="living-environmental-memory-contract">
          <span>{memory.contract_version}</span>
          <strong>{memory.window_event_count} replay events</strong>
          <small>{memory.coverage.replay_truncated ? "Bounded window · truncated" : "Complete returned Replay window"}</small>
        </div>
      </header>

      <div className="living-environmental-memory-summary" aria-label="Environmental memory summary">
        <article><strong>{memory.path_frequencies.length}</strong><span>routing paths</span></article>
        <article><strong>{memory.path_frequencies.reduce((sum, item) => sum + item.handoff_count, 0)}</strong><span>handoffs</span></article>
        <article><strong>{memory.heat_cells.length}</strong><span>heat cells</span></article>
        <article><strong>{memory.timeline.length}</strong><span>time buckets</span></article>
        <article><strong>{memory.coverage.activity_history_established ? "Yes" : "Partial"}</strong><span>coverage epoch</span></article>
      </div>

      <div className="living-environmental-memory-grid">
        <article className="living-environmental-memory-panel">
          <header>
            <span>Routing memory</span>
            <small>{memory.coverage.path_history}</small>
          </header>
          <div className="living-environmental-path-list">
            {memory.path_frequencies.length ? memory.path_frequencies.map((path) => (
              <div
                key={path.previous_position_key + ":" + path.assigned_position_key}
                data-environmental-path={path.previous_position_key + ":" + path.assigned_position_key}
                data-environmental-path-coverage={path.coverage_state}
              >
                <strong>{routeLabel(path.previous_position_key)} → {routeLabel(path.assigned_position_key)}</strong>
                <span>{path.handoff_count} handoff{path.handoff_count === 1 ? "" : "s"} · {path.work_item_count} WorkItem{path.work_item_count === 1 ? "" : "s"}</span>
                <small>{shortTime(path.first_occurred_at)} → {shortTime(path.last_occurred_at)} · {titleCase(path.coverage_state)}</small>
              </div>
            )) : (
              <p>No governed assignment path exists in the returned Replay window.</p>
            )}
          </div>
        </article>

        <article className="living-environmental-memory-panel">
          <header>
            <span>Activity heatmap</span>
            <small>department × persisted event kind</small>
          </header>
          <div className="living-environmental-heat-list">
            {memory.heat_cells.map((cell) => (
              <div key={cell.department + ":" + cell.event_kind} data-environmental-heat={cell.department + ":" + cell.event_kind}>
                <div><strong>{cell.department}</strong><span>{titleCase(cell.event_kind)}</span></div>
                <progress max={maxHeat} value={cell.event_count} aria-label={cell.department + " " + cell.event_kind + " activity"} />
                <small>{cell.event_count} events · {cell.covered_event_count} covered</small>
              </div>
            ))}
          </div>
        </article>

        <article className="living-environmental-memory-panel">
          <header>
            <span>Temporal density</span>
            <small>UTC hour buckets from persisted Replay</small>
          </header>
          <div className="living-environmental-timeline-list">
            {memory.timeline.map((bucket) => (
              <div key={bucket.bucket_start} data-environmental-bucket={bucket.bucket_start}>
                <div><strong>{shortTime(bucket.bucket_start)}</strong><span>{titleCase(bucket.coverage_state)}</span></div>
                <progress max={maxTimeline} value={bucket.event_count} aria-label={"Activity at " + bucket.bucket_start} />
                <small>
                  {bucket.event_count} total · {bucket.handoff_count} handoff · {bucket.blocker_count} blocker · {bucket.decision_count} decision · {bucket.conversation_count} conversation
                </small>
              </div>
            ))}
          </div>
        </article>
      </div>

      <footer className="living-environmental-memory-boundary">
        <strong>Historical aggregate truth boundary</strong>
        <span>{memory.unsupported_dimensions.join(" · ")}</span>
        <small>
          Canonical source projection: yes. Authority: none. Prediction: none. Mutation: none. Environmental memory is a perception aid, not a new truth store.
        </small>
      </footer>
    </section>
  );
}
