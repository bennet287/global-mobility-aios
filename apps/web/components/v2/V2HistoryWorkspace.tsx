"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2HistoryReplay, useV2ReplayCursor } from "../../hooks/useV2HistoryReplay";
import {
  buildV2HistoryPortfolio,
  historyEventDestination,
  replayDiffGroups,
  replayStateGroups,
  selectV2HistoryEvent,
  summarizeV2ReplayState,
} from "../../lib/v2/history-replay";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import {
  V2DataState,
  V2Inspector,
  V2MetricGroup,
  V2ObjectRow,
  V2PageHeader,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
  V2Surface,
  V2TimelineRow,
  V2TruthBadge,
  formatV2Timestamp,
} from "./ui/V2Primitives";
import styles from "./V2HistoryWorkspace.module.css";

export function V2HistoryWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2HistoryReplay();
  const params = useSearchParams();
  const router = useRouter();
  const cursorId = params.get("cursor");
  const compareFromId = params.get("from");
  const portfolio = useMemo(() => buildV2HistoryPortfolio(read.latest), [read.latest]);
  const selected = selectV2HistoryEvent(portfolio.events, cursorId);
  const compareFrom = selectV2HistoryEvent(portfolio.events, compareFromId);
  const cursorRead = useV2ReplayCursor(selected?.activity_id ?? null, compareFrom?.activity_id ?? null);
  const stateSummary = summarizeV2ReplayState(cursorRead.state);
  const inspectorTarget = useRef<HTMLDivElement>(null);
  const selectionOrigin = useRef<HTMLElement | null>(null);

  useV2SearchItems(portfolio.events.map((event) => ({
    id: event.activity_id,
    kind: "Event" as const,
    icon: "history" as const,
    label: event.title,
    description: `${event.event_kind} · ${event.coverage_state} · ${formatV2Timestamp(event.occurred_at)}`,
    href: historyEventDestination(event.activity_id),
  })));

  useEffect(() => {
    if (selected) inspectorTarget.current?.focus();
  }, [selected]);

  function navigate(mutator: (next: URLSearchParams) => void, push = false) {
    const next = new URLSearchParams(params.toString());
    mutator(next);
    const suffix = next.toString();
    const href = `/cockpit/v2/history${suffix ? `?${suffix}` : ""}`;
    if (push) router.push(href, { scroll: false });
    else router.replace(href, { scroll: false });
  }

  function selectEvent(activityId: string) {
    selectionOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    navigate((next) => {
      next.set("cursor", activityId);
      if (next.get("from") === activityId) next.delete("from");
    }, true);
  }

  function setComparison(activityId: string) {
    navigate((next) => {
      if (activityId && activityId !== selected?.activity_id) next.set("from", activityId);
      else next.delete("from");
    });
  }

  function closeInspector() {
    navigate((next) => {
      next.delete("cursor");
      next.delete("from");
    });
    requestAnimationFrame(() => selectionOrigin.current?.focus());
  }

  return (
    <V2Shell activeItem="History" backendOnline={health?.status === "ok"}>
      <div className={`aios-v2-content ${styles.page}`}>
        <V2PageHeader
          eyebrow="Temporal transparency"
          title="History"
          description="Replay recorded semantic Activity, inspect an explicit as-of cursor, and compare two proven cursor states without manufacturing missing history."
          actions={<button type="button" onClick={() => void read.refresh()}>Refresh History</button>}
        />

        {read.loading && !read.latest ? <V2DataState state={{ kind: "loading", label: "Loading canonical replay…" }} /> : null}
        {read.error && !read.latest ? <V2DataState state={{ kind: "unavailable", label: "Canonical replay unavailable", detail: read.error, onRetry: () => void read.refresh() }} /> : null}
        {read.latest && read.error ? <V2DataState state={{ kind: "stale", label: "Replay refresh failed", detail: read.error, lastLoadedAt: read.loadedAt, onRetry: () => void read.refresh() }} /> : null}
        {read.latest && !read.latest.established ? <V2DataState state={{ kind: "unavailable", label: "Replay not established", detail: "No bounded canonical replay is established for this Austria organization projection. AIOS does not synthesize a history from current state." }} /> : null}

        {portfolio.established ? (
          <>
            <V2ProvenanceDisclosure title="History source & coverage posture">
              <p>Loaded {formatV2Timestamp(read.loadedAt)} · Replay generated {formatV2Timestamp(portfolio.generatedAt)} · Contract {portfolio.contractVersion ?? "Not supplied"}.</p>
              <p>Activity basis: {portfolio.activityHistoryBasis ?? "Not supplied"}. Coverage begins: {formatV2Timestamp(portfolio.activityHistoryCoverageStart)}. Pre-epoch history: {portfolio.preEpochHistory ?? "Not supplied"}.</p>
              <p>Evidence history: {portfolio.evidenceHistory ?? "Not supplied"} · Risk escalation history: {portfolio.riskEscalationHistory ?? "Not supplied"} · Source snapshot history: {portfolio.sourceSnapshotHistory ?? "Not supplied"} · Conversation history: {portfolio.conversationHistory ?? "Not supplied"}.</p>
              <p>Canonical projection: {String(portfolio.canonicalProjection)} · Authoritative: {String(portfolio.authoritative)} · Mutations allowed: {String(portfolio.mutationsAllowed)}.</p>
            </V2ProvenanceDisclosure>

            <V2MetricGroup
              label="History replay readout"
              items={[
                { label: "Returned events", value: portfolio.returnedEvents },
                { label: "Total events", value: portfolio.totalEvents },
                { label: "Activity history established", value: portfolio.activityHistoryEstablished ? "Yes" : "No" },
                { label: "Replay truncated", value: portfolio.truncated ? "Yes" : "No" },
              ]}
            />

            {portfolio.truncated ? <V2DataState state={{ kind: "partial", label: "Bounded replay window", unavailableSources: ["Events outside the returned replay window"] }} /> : null}

            {portfolio.events.length ? (
              <div className={styles.workspace}>
                <V2Surface className={styles.timeline} label="Canonical Activity replay">
                  <V2SectionHeader eyebrow="Recorded sequence" title="Activity timeline" description="Returned replay order and stream sequence are preserved. Coverage labels remain explicit at each event." />
                  <div className={styles.eventList} aria-label="History events">
                    {portfolio.events.map((event) => (
                      <V2TimelineRow
                        key={event.activity_id}
                        title={`#${event.stream_sequence} · ${event.title}`}
                        summary={`${event.event_kind} · ${event.summary}`}
                        occurredAt={event.occurred_at}
                        coverage={event.coverage_state}
                        selected={selected?.activity_id === event.activity_id}
                        onSelect={() => selectEvent(event.activity_id)}
                      />
                    ))}
                  </div>
                </V2Surface>

                <div className={styles.inspectorSlot} ref={inspectorTarget} tabIndex={-1}>
                  {selected ? (
                    <V2Inspector title={selected.title} description="Historical inspection only. This cursor does not mutate or replace current organization state." onClose={closeInspector}>
                      <div className={styles.badgeLine}>
                        <V2TruthBadge kind="historical" />
                        <V2StateBadge label={selected.event_kind} />
                        <V2StateBadge label={selected.coverage_state} tone={selected.coverage_state === "covered" ? "neutral" : "warning"} />
                      </div>

                      <V2ProvenanceDisclosure title="Activity cursor identity" technical>
                        <dl className={styles.definitionList}>
                          <dt>Activity ID</dt><dd>{selected.activity_id}</dd>
                          <dt>Stream sequence</dt><dd>{selected.stream_sequence}</dd>
                          <dt>Occurred at</dt><dd>{formatV2Timestamp(selected.occurred_at)}</dd>
                          <dt>Activity class</dt><dd>{selected.activity_class}</dd>
                          <dt>Activity type</dt><dd>{selected.activity_type}</dd>
                          <dt>Actor</dt><dd>{selected.actor_type}:{selected.actor_id}</dd>
                          <dt>Position</dt><dd>{selected.position_key ?? "Not supplied"}</dd>
                          <dt>Department</dt><dd>{selected.department ?? "Not supplied"}</dd>
                          <dt>Authority</dt><dd>{selected.authority_level ?? "Not supplied"}</dd>
                          <dt>WorkItem</dt><dd>{selected.work_item_id ?? "Not supplied"}</dd>
                          <dt>Source</dt><dd>{selected.source_object_type}:{selected.source_object_id}{selected.source_object_version ? `@${selected.source_object_version}` : ""}</dd>
                          <dt>Causation Activity</dt><dd>{selected.causation_activity_id ?? "Not supplied"}</dd>
                          <dt>Supersedes Activity</dt><dd>{selected.supersedes_activity_id ?? "Not supplied"}</dd>
                        </dl>
                        <p>Timestamp, ordering and styling do not prove presence, urgency, success, completion, approval, conversation or physical movement.</p>
                      </V2ProvenanceDisclosure>

                      <div className={styles.compareControl}>
                        <label htmlFor="history-compare-from">Compare from Activity</label>
                        <select id="history-compare-from" value={compareFrom?.activity_id ?? ""} onChange={(event) => setComparison(event.target.value)}>
                          <option value="">No comparison</option>
                          {portfolio.events.filter((event) => event.activity_id !== selected.activity_id).map((event) => <option value={event.activity_id} key={event.activity_id}>#{event.stream_sequence} · {event.title}</option>)}
                        </select>
                        <span>Comparison is explicit cursor-to-cursor state diff only; Q8 does not classify change as better or worse.</span>
                      </div>

                      <V2SectionHeader level={3} title="As-of reconstructed state" />
                      {cursorRead.stateLoading ? <V2DataState state={{ kind: "loading", label: "Reconstructing as-of state…" }} /> : null}
                      {cursorRead.stateError ? <V2DataState state={{ kind: "unavailable", label: "As-of state unavailable", detail: cursorRead.stateError }} /> : null}
                      {cursorRead.state && stateSummary ? (
                        <div className={styles.stateSection} data-replay-semantic-rendering="historical-cursor">
                          <V2MetricGroup
                            label="As-of state readout"
                            items={[
                              { label: "Work items", value: stateSummary.workItemCount },
                              { label: "Blockers", value: stateSummary.blockerCount },
                              { label: "Decisions", value: stateSummary.decisionCount },
                              { label: "Human requests", value: stateSummary.humanRequestCount },
                              { label: "Conversations", value: stateSummary.conversationCount },
                              { label: "Unapplied transitions", value: stateSummary.unappliedTransitionCount },
                            ]}
                          />
                          <V2ProvenanceDisclosure title="Reconstruction posture" technical>
                            <p>Cursor coverage: {stateSummary.cursorCoverageState} · Reconstruction: {stateSummary.reconstructionPosture}.</p>
                            <p>Supported dimensions: {stateSummary.supportedDimensions.join(", ") || "None supplied"}.</p>
                            <p>Unsupported dimensions: {stateSummary.unsupportedDimensions.join(", ") || "None supplied"}.</p>
                            <p>Canonical projection: {String(stateSummary.canonicalProjection)} · Authoritative: {String(stateSummary.authoritative)} · Mutations allowed: {String(stateSummary.mutationsAllowed)}.</p>
                          </V2ProvenanceDisclosure>
                          <div className={styles.entityGroups}>
                            {replayStateGroups(cursorRead.state).map((group) => group.rows.length ? (
                              <div key={group.label} className={styles.entityGroup}>
                                <strong>{group.label}</strong>
                                {group.rows.map((row) => <V2ObjectRow key={`${group.label}:${row.id}`} title={row.id} description={`${row.semantic.label} · ${row.coverageState} · ${formatV2Timestamp(row.lastOccurredAt)}`} />)}
                              </div>
                            ) : null)}
                          </div>
                          <p className={styles.truthNote}>Phase 7H semantics are historical cursor truth only. “Completed”, “resolved”, “approved”, “rejected”, request lifecycle and conversation lifecycle labels describe reconstructed state at this cursor; they do not claim the same state is true now, and they do not imply physical presence, movement, quality, causality or authority beyond the canonical record.</p>
                        </div>
                      ) : null}

                      {compareFrom ? (
                        <div className={styles.diffSection}>
                          <V2SectionHeader level={3} title="Cursor comparison" description={`From #${compareFrom.stream_sequence} to #${selected.stream_sequence}.`} />
                          {cursorRead.diffLoading ? <V2DataState state={{ kind: "loading", label: "Comparing cursor states…" }} /> : null}
                          {cursorRead.diffError ? <V2DataState state={{ kind: "unavailable", label: "Cursor comparison unavailable", detail: cursorRead.diffError }} /> : null}
                          {cursorRead.diff ? (
                            <>
                              <V2MetricGroup
                                label="Replay comparison readout"
                                items={[
                                  { label: "Changed entities", value: cursorRead.diff.changed_entity_count },
                                  { label: "Unchanged omitted", value: cursorRead.diff.unchanged_entities_omitted ? "Yes" : "No" },
                                  { label: "From unapplied transitions", value: cursorRead.diff.from_cursor.unapplied_transition_count },
                                  { label: "To unapplied transitions", value: cursorRead.diff.to_cursor.unapplied_transition_count },
                                ]}
                              />
                              <V2ProvenanceDisclosure title="Comparison posture" technical>
                                <p>{cursorRead.diff.comparison_posture}</p>
                                <p>Basis: {cursorRead.diff.comparison_basis}.</p>
                                <p>Supported dimensions: {cursorRead.diff.supported_dimensions.join(", ") || "None supplied"}.</p>
                                <p>Unsupported dimensions: {cursorRead.diff.unsupported_dimensions.join(", ") || "None supplied"}.</p>
                                <p>Canonical projection: {String(cursorRead.diff.canonical_projection)} · Authoritative: {String(cursorRead.diff.authoritative)} · Mutations allowed: {String(cursorRead.diff.mutations_allowed)}.</p>
                              </V2ProvenanceDisclosure>
                              <div className={styles.diffGroups}>
                                {replayDiffGroups(cursorRead.diff).map((group) => group.items.length ? (
                                  <div key={group.label} className={styles.diffGroup}>
                                    <strong>{group.label}</strong>
                                    {group.items.map((delta) => <V2ObjectRow key={`${group.label}:${delta.entityId}`} title={delta.entityId} description={`${delta.changeKind} · fields: ${delta.changedFields.join(", ") || "None supplied"}`} />)}
                                  </div>
                                ) : null)}
                              </div>
                              <p className={styles.truthNote}>Q8 reports only the backend-proven field deltas. It does not infer improvement, deterioration, causality, urgency or authority from the comparison.</p>
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </V2Inspector>
                  ) : cursorId ? (
                    <V2DataState state={{ kind: "unavailable", label: "Selected Activity was not returned", detail: "The requested Activity cursor is outside this loaded replay. AIOS will not substitute a nearby event." }} />
                  ) : (
                    <V2Surface kind="inset" className={styles.placeholder} label="History inspection">
                      <V2SectionHeader title="Choose an Activity cursor" description="Select a recorded replay event to reconstruct bounded as-of state and optionally compare two explicit cursors." />
                      <p>History is read-only temporal transparency. Current canonical organization state is not changed.</p>
                    </V2Surface>
                  )}
                </div>
              </div>
            ) : (
              <V2DataState state={{ kind: "empty", label: "No replay events returned", detail: "The bounded replay is established but returned no semantic Activity events. This is not a claim that the organization has no historical activity outside coverage." }} />
            )}
          </>
        ) : null}
      </div>
    </V2Shell>
  );
}
