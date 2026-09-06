"use client";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2MissionsWorkspace } from "../../hooks/useV2MissionsWorkspace";
import { filterMissions, missionCoverageUnavailable, missionDestination, selectMission, type V2MissionDetail } from "../../lib/v2/missions-workspace";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import { V2AuthorityBadge, V2DataState, V2Inspector, V2ObjectRow, V2PageHeader, V2ProvenanceDisclosure, V2SectionHeader, V2StateBadge, V2Surface, V2TruthBadge, formatV2Timestamp } from "./ui/V2Primitives";

/** Replaceable Q5 composition seam for Kimi; Q4 contracts own presentation. */
export function V2MissionDetails({ detail, onClose }: { detail: V2MissionDetail; onClose: () => void }) {
  const { mission } = detail;
  return <V2Inspector title={mission.title} description="Read-only Mission projection. Participants are rostered roles, not presence claims." onClose={onClose}>
    <V2StateBadge label={mission.state} /><p>Objective: {mission.objective_key}. Phase: {mission.phase_key ?? "Not supplied"}.</p>
    {detail.unavailable.length ? <V2DataState state={{ kind: "partial", label: "Mission detail is incomplete", unavailableSources: detail.unavailable }} /> : null}
    <V2Surface kind="authority"><V2SectionHeader title="Human requests" level={3} />{detail.humanRequests.length ? detail.humanRequests.map((item) => <V2ObjectRow key={item.request_id} title={item.title} description={item.instructions} trailing={<V2AuthorityBadge level={item.required_role} required />} />) : <p>No linked human requests returned. This does not establish that no action is needed.</p>}</V2Surface>
    <V2SectionHeader title="Participants" level={3} description={`${detail.participants.length} of ${mission.participant_position_keys.length} linked roles returned.`} />
    {detail.participants.map((item) => <V2ObjectRow key={item.position_key} title={item.title} description={`${item.department} · ${item.state_reason}`} trailing={<V2StateBadge label={item.semantic_state} />} />)}
    <V2SectionHeader title="Work items" level={3} description={`${detail.workItems.length} of ${mission.work_item_ids.length} linked work items returned.`} />
    {detail.workItems.map((item) => <V2ObjectRow key={item.work_item_id} title={item.title} description={`Assigned to ${item.assigned_position_key} · Priority: ${item.priority} · Due: ${formatV2Timestamp(item.due_at)}`} trailing={<V2StateBadge label={item.status} />} />)}
    <V2SectionHeader title="Blockers" level={3} description={`${mission.blocker_count} in the Mission projection; ${detail.blockers.length} linked records returned.`} />
    {detail.blockers.map((item) => <V2ObjectRow key={item.blocker_id} title={item.title} description={`${item.description} · ${item.severity}`} trailing={<V2StateBadge label={item.status} />} />)}
    <V2SectionHeader title="Decisions" level={3} description={`${mission.decision_count} in the Mission projection; ${detail.decisions.length} linked records returned.`} />
    {detail.decisions.map((item) => <V2Surface key={item.decision_id} kind="inset"><V2ObjectRow title={item.title} description={item.question} trailing={<V2StateBadge label={item.is_current ? item.status : "Superseded"} />} /><V2AuthorityBadge level={item.authority_level} required={item.is_current && item.required_owner_action} /><p><V2TruthBadge kind="recommendation" /> {item.recommendation}</p></V2Surface>)}
    <Link href="/cockpit/decisions">Open Decision Explorer</Link>
    <V2SectionHeader title="Conversations" level={3} description="Recorded lifecycle and participants; no inferred transcript or physical meeting." />
    {detail.conversations.map((item) => <V2ObjectRow key={item.conversation_id} title={item.summary} description={`${item.participant_position_keys.join(", ")} · ${formatV2Timestamp(item.lifecycle_at)}`} trailing={<V2StateBadge label={item.status} />} />)}
    <V2SectionHeader title="Recorded handoffs" level={3} description="Assignment events, not physical movement or inferred completion." />
    {detail.handoffs.map((item) => <V2ObjectRow key={item.activity_id} title={`${item.previous_position_key} → ${item.assigned_position_key}`} description={formatV2Timestamp(item.occurred_at)} trailing={<V2StateBadge label={item.status} />} />)}
    <V2ProvenanceDisclosure title="Mission lineage and coverage"><dl><dt>Mission key</dt><dd>{mission.mission_key}</dd><dt>Root work item</dt><dd>{mission.root_work_item_id}</dd><dt>Canonical basis</dt><dd>{mission.canonical_basis}</dd><dt>Unreturned work items</dt><dd>{detail.missingWorkIds.join(", ") || "None"}</dd><dt>Unreturned participants</dt><dd>{detail.missingParticipantKeys.join(", ") || "None"}</dd></dl><p>Evidence contents, full Activity history, sponsor identity and dependency completeness are not supplied by this Mission read. No percentage progress or next action is inferred.</p><pre>{JSON.stringify({ relationships: detail.relationships, handoff_lineage: detail.handoffs, conversation_lineage: detail.conversations }, null, 2)}</pre></V2ProvenanceDisclosure>
  </V2Inspector>;
}

export function V2MissionsWorkspace() {
  const read = useV2MissionsWorkspace();
  const { health } = useBackendStatus();
  const params = useSearchParams(); const router = useRouter();
  const selectedKey = params.get("mission"); const query = params.get("q") ?? ""; const state = params.get("state") ?? "";
  const missions = read.scene?.deterministic.missions ?? [];
  const filtered = filterMissions(missions, query, state);
  const detail = read.scene && selectedKey ? selectMission(read.scene, selectedKey) : null;
  const inspector = useRef<HTMLDivElement>(null); const origin = useRef<HTMLElement | null>(null);
  const results = useRef<HTMLElement>(null);
  useV2SearchItems(read.error ? [] : missions.map((mission) => ({ id: mission.mission_key, kind: "Mission" as const, icon: "missions" as const, label: mission.title, description: `${mission.state} · ${mission.objective_key}`, href: missionDestination(mission.mission_key) })));
  useEffect(() => { if (selectedKey && origin.current) inspector.current?.focus(); }, [selectedKey]);
  function updateQuery(name: string, value: string) { const next = new URLSearchParams(params.toString()); if (value) next.set(name, value); else next.delete(name); router.replace(`/cockpit/v2/missions${next.size ? `?${next}` : ""}`, { scroll: false }); }
  function close() { updateQuery("mission", ""); if (origin.current?.isConnected) origin.current.focus(); else results.current?.focus(); }
  return <V2Shell activeItem="Missions" backendOnline={health?.status === "ok"}><div className="aios-v2-content">
    <V2PageHeader eyebrow="Purpose and governed work" title="Missions" description="Inspect Mission state, linked work and the records that need attention." actions={<button type="button" onClick={() => void read.refresh()}>Refresh Missions</button>} />
    {read.loading ? <V2DataState state={{ kind: "loading", label: read.received ? "Refreshing Mission source…" : "Loading Missions…" }} /> : null}
    {read.error ? <V2DataState state={read.scene ? { kind: "stale", label: "Mission refresh failed", detail: read.error, lastLoadedAt: read.loadedAt, onRetry: () => void read.refresh() } : { kind: "unavailable", label: "Mission source unavailable", detail: read.error, onRetry: () => void read.refresh() }} /> : null}
    {!read.loading && !read.error && read.received && !read.scene ? <V2DataState state={{ kind: "empty", label: "Mission projection not established", detail: "The source reports no established Living Organization scene. No Mission is inferred." }} /> : null}
    {read.scene ? <>{missionCoverageUnavailable(read.scene) ? <V2DataState state={{ kind: "unavailable", label: "Mission coverage unavailable", detail: "Returned records may be inspected, but Mission completeness cannot be assessed." }} /> : null}<V2ProvenanceDisclosure title="Source scope"><p>Scope: {read.scene.scope}. Generated {formatV2Timestamp(read.scene.generated_at)}.</p><p>This is the bounded latest Austria Living Organization projection, not a global Mission catalogue.</p><pre>{JSON.stringify(read.scene.coverage, null, 2)}</pre></V2ProvenanceDisclosure>
      <V2Surface kind="inset"><label>Search returned Missions <input type="search" value={query} onChange={(event) => updateQuery("q", event.target.value)} /></label><label>Mission state <select value={state} onChange={(event) => updateQuery("state", event.target.value)}><option value="">All returned states</option>{[...new Set([...missions.map((item) => item.state), ...(state ? [state] : [])])].sort().map((value) => <option key={value} value={value}>{value}</option>)}</select></label><p>{filtered.length} of {missions.length} returned Missions match.</p></V2Surface>
      <section ref={results} tabIndex={-1} aria-label="Mission results">{filtered.map((mission) => <V2ObjectRow key={mission.mission_key} title={mission.title} description={`${mission.participant_position_keys.length} linked roles · ${mission.blocker_count} projected blockers`} trailing={<V2StateBadge label={mission.state} />} selected={mission.mission_key === selectedKey} onSelect={() => { origin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null; const next = new URLSearchParams(params.toString()); next.set("mission", mission.mission_key); router.push(`/cockpit/v2/missions?${next}`, { scroll: false }); }} />)}</section>
      {!filtered.length && !missionCoverageUnavailable(read.scene) ? <V2DataState state={{ kind: "empty", label: missions.length ? "No Missions match these filters" : "No Missions returned", detail: "This describes only the current result set, not all organizational work." }} /> : null}
      <div ref={inspector} tabIndex={-1}>{detail ? <V2MissionDetails detail={detail} onClose={close} /> : selectedKey ? <V2DataState state={{ kind: "unavailable", label: "Selected Mission not returned", detail: "The exact Mission key is outside this snapshot. Another Mission will not be substituted." }} /> : null}</div>
    </> : null}
  </div></V2Shell>;
}
