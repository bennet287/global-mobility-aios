"use client";
import { useCallback, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2Read } from "../../hooks/useV2Read";
import { getLatestAustriaOrganizationReplay, getLatestAustriaOrganizationReplayState, getLatestAustriaOrganizationReplayStateDiff, getLatestAustriaOrganizationEnvironmentalMemory } from "../../lib/live-organization";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import { EmptyState, Provenance, ReadState, RecordFields, RelatedLink, StatusLabel, TruthBadge, V2PageHeader, formatV2Date, v2Styles as s } from "./V2Primitives";

function ReplayState({ cursor }: { cursor: string }) {
  const load = useCallback(() => getLatestAustriaOrganizationReplayState(cursor), [cursor]);
  const read = useV2Read(load);
  const state = read.data;
  return <section className={s.detail}><TruthBadge kind="historical" /><h2>As of this event</h2><ReadState {...read} hasData={Boolean(state)} onRetry={() => void read.refresh()} />{state ? <><p>{formatV2Date(state.cursor_occurred_at)} · {state.reconstruction_posture}</p><p>Unsupported: {state.unsupported_dimensions.join(", ") || "None reported"}.</p><p>{state.unapplied_transition_count} unapplied transitions.</p>
    <h3>Work assignments</h3><div className={s.tableScroll} tabIndex={0} role="region" aria-label="Historical work assignments"><table><thead><tr><th>Work item</th><th>Assigned position</th><th>Status</th><th>Coverage</th></tr></thead><tbody>{state.work_items.map((item) => <tr key={item.work_item_id}><td>{item.work_item_id}</td><td>{item.assigned_position_key}</td><td>{item.status}</td><td>{item.coverage_state}</td></tr>)}</tbody></table></div>
    <h3>Decision state</h3><ul className={s.list}>{state.decisions.map((item) => <li className={s.row} key={item.decision_id}><div><strong>{item.decision_type}</strong><small>{item.authority_level} · {item.coverage_state}</small><RelatedLink href={`/cockpit/v2/decisions?decision=${encodeURIComponent(item.decision_id)}`}>Inspect current record</RelatedLink></div><StatusLabel value={item.status} /></li>)}</ul>
    <Provenance label="Supported historical records"><RecordFields values={{ supported_dimensions: state.supported_dimensions, blockers: state.blockers, human_requests: state.human_requests, conversations: state.conversations, cursor_activity_id: state.cursor_activity_id, contract_version: state.contract_version }} /></Provenance>
  </> : null}</section>;
}

function ReplayCompare({ from, to }: { from: string; to: string }) {
  const load = useCallback(() => getLatestAustriaOrganizationReplayStateDiff(from, to), [from, to]);
  const read = useV2Read(load);
  const data = read.data;
  return <section className={s.detail}><TruthBadge kind="historical" /><h2>Compare A → B</h2><ReadState {...read} hasData={Boolean(data)} onRetry={() => void read.refresh()} />{data ? <><p>{formatV2Date(data.from_cursor.occurred_at)} → {formatV2Date(data.to_cursor.occurred_at)}</p><p>{data.changed_entity_count} changed entities · {data.comparison_posture}</p><p>Unsupported: {data.unsupported_dimensions.join(", ") || "None reported"}.</p>{(["work_items", "blockers", "decisions", "human_requests", "conversations"] as const).map((dimension) => <section key={dimension}><h3>{dimension.replaceAll("_", " ")}</h3>{data[dimension].length ? data[dimension].map((delta) => <Provenance key={delta.entity_id} label={`${delta.change_kind} · ${delta.entity_id}`}><p>Changed fields: {delta.changed_fields.join(", ") || "No fields supplied"}</p><RecordFields values={{ before: delta.before, after: delta.after }} /></Provenance>) : <p>No changes returned in this dimension.</p>}</section>)}<Provenance label="Comparison coverage"><RecordFields values={{ comparison_basis: data.comparison_basis, supported_dimensions: data.supported_dimensions, unchanged_entities_omitted: data.unchanged_entities_omitted, from_cursor: data.from_cursor, to_cursor: data.to_cursor }} /></Provenance></> : null}</section>;
}

function EnvironmentalMemory() {
  const read = useV2Read(getLatestAustriaOrganizationEnvironmentalMemory);
  const memory = read.data?.established ? read.data.memory : null;
  return <section className={s.detail}><TruthBadge kind="memory" /><h2>Environmental Memory</h2><p>Aggregate event patterns in a bounded window. Read-only, non-authoritative and non-predictive.</p><ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />{memory ? <><p>{memory.window_event_count} events · {formatV2Date(memory.window_start)} → {formatV2Date(memory.window_end)}</p><div className={s.tableScroll} tabIndex={0} role="region" aria-label="Event-kind counts"><table><thead><tr><th>Event kind</th><th>Events</th></tr></thead><tbody>{memory.kind_aggregates.map((item) => <tr key={item.event_kind}><td>{item.event_kind}</td><td>{item.event_count}</td></tr>)}</tbody></table></div><h3>Recorded handoff paths</h3><ul className={s.list}>{memory.path_frequencies.map((item) => <li className={s.row} key={`${item.previous_position_key}/${item.assigned_position_key}`}><div><strong>{item.previous_position_key} → {item.assigned_position_key}</strong><p>{item.handoff_count} handoffs across {item.work_item_count} work items · {item.coverage_state}</p></div></li>)}</ul><Provenance label="Memory coverage and temporal buckets"><RecordFields values={{ coverage: memory.coverage, unsupported_dimensions: memory.unsupported_dimensions, hourly_event_buckets: memory.timeline, department_event_counts: memory.heat_cells }} /></Provenance></> : !read.loading && !read.error ? <EmptyState title="Memory not established" detail="No historical pattern is invented when the aggregate is unavailable." /> : null}</section>;
}

export function V2HistoryWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2Read(getLatestAustriaOrganizationReplay);
  const params = useSearchParams();
  const [cursor, setCursor] = useState<string | null>(null);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [compare, setCompare] = useState<{ from: string; to: string } | null>(null);
  const [mode, setMode] = useState<"timeline" | "memory">("timeline");
  const replay = read.data?.established ? read.data.replay : null;
  const events = replay?.events.filter((event) => !params.get("work") || event.work_item_id === params.get("work")) ?? [];
  const selectedCursor = params.get("event") ?? cursor;
  const event = events.find((item) => item.activity_id === selectedCursor);
  useV2SearchItems(events.map((item) => ({ kind: "Event", label: item.title, description: item.summary, icon: "history", href: `/cockpit/v2/history?event=${encodeURIComponent(item.activity_id)}` })));
  return <V2Shell activeItem="History" backendOnline={health?.status === "ok"}>
    <V2PageHeader eyebrow="Understand how it happened" title="History & replay" description="Reconstruct supported state, compare moments, and distinguish memory from now."><button type="button" onClick={() => void read.refresh()}>Refresh timeline</button></V2PageHeader>
    <div className={s.toolbar}><button type="button" aria-pressed={mode === "timeline"} onClick={() => setMode("timeline")}>Timeline</button><button type="button" aria-pressed={mode === "memory"} onClick={() => setMode("memory")}>Environmental Memory</button><RelatedLink href="/cockpit/v2/organization">Return to now</RelatedLink></div>
    {mode === "memory" ? <EnvironmentalMemory /> : <><ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />{replay ? <><p>{replay.returned_events} of {replay.total_events} events returned{replay.truncated ? " · truncated history" : ""}{params.get("work") ? " · filtered to linked work" : ""}.</p><Provenance label="Historical coverage"><RecordFields values={replay.coverage} /></Provenance>
      <div className={s.toolbar}><label>Compare A<select value={from} onChange={(e) => setFrom(e.target.value)}><option value="">Choose an event</option>{events.map((item) => <option value={item.activity_id} key={item.activity_id}>{item.stream_sequence} · {item.title}</option>)}</select></label><label>Compare B<select value={to} onChange={(e) => setTo(e.target.value)}><option value="">Choose an event</option>{events.map((item) => <option value={item.activity_id} key={item.activity_id}>{item.stream_sequence} · {item.title}</option>)}</select></label><button type="button" disabled={!from || !to || from === to} onClick={() => setCompare({ from, to })}>Compare states</button>{compare ? <button type="button" onClick={() => setCompare(null)}>Close comparison</button> : null}</div>
      {compare ? <ReplayCompare from={compare.from} to={compare.to} /> : <div className={s.split}><nav aria-label="Replay events"><ol className={s.list}>{events.map((item) => <li key={item.activity_id}><button type="button" className={s.row} aria-pressed={selectedCursor === item.activity_id} onClick={() => { setCursor(item.activity_id); const next = new URLSearchParams(params.toString()); next.set("event", item.activity_id); window.history.replaceState(null, "", `?${next}`); }}><div><small>{formatV2Date(item.occurred_at)}</small><strong>{item.title}</strong><small>{item.coverage_state}</small></div></button></li>)}</ol></nav><div>{event ? <><article className={s.detail}><TruthBadge kind="historical" /><h2>{event.title}</h2><p>{event.summary}</p><Provenance label="Event lineage"><RecordFields values={event} /></Provenance></article><ReplayState cursor={event.activity_id} /></> : <EmptyState title="Choose an event" detail="The replay uses only supported historical dimensions. It does not infer historical evidence, presence or risk state." />}</div></div>}
    </> : !read.loading && !read.error ? <EmptyState title="Replay not established" detail="No history was returned for the current organization." /> : null}</>}
  </V2Shell>;
}
