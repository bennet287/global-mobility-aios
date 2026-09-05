"use client";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2Read } from "../../hooks/useV2Read";
import { getLatestAustriaLivingScene } from "../../lib/live-organization";
import { buildV2EmployeeInspectorModel, buildV2MissionRoomModel } from "../../lib/v2/mission-room-inspector";
import { V2EmployeeInspector } from "./V2EmployeeInspector";
import { V2MissionRoomPanel } from "./V2MissionRoomPanel";
import { V2Shell } from "./V2Shell";
import { useV2SearchItems } from "./V2NavigationContext";
import { EmptyState, Provenance, ReadState, RecordFields, RelatedLink, StatusLabel, V2PageHeader, v2Styles as s } from "./V2Primitives";

export function V2MissionsWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2Read(getLatestAustriaLivingScene);
  const params = useSearchParams();
  const [selected, setSelected] = useState<string | null>(null);
  const [employee, setEmployee] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [state, setState] = useState("all");
  const scene = read.data?.established ? read.data.scene : null;
  const missions = scene?.deterministic.missions ?? [];
  useV2SearchItems(missions.map((item) => ({ kind: "Mission", label: item.title, description: item.state, icon: "missions", href: `/cockpit/v2/missions?mission=${encodeURIComponent(item.mission_key)}` })));
  const current = params.get("mission") ?? selected ?? missions[0]?.mission_key ?? null;
  const mission = missions.find((item) => item.mission_key === current);
  const room = useMemo(() => scene && current ? buildV2MissionRoomModel(scene, current) : null, [scene, current]);
  const inspector = useMemo(() => scene && employee ? buildV2EmployeeInspectorModel(scene, employee) : null, [scene, employee]);
  const work = scene?.deterministic.work_items.filter((item) => mission?.work_item_ids.includes(item.work_item_id)) ?? [];
  const relationships = scene?.deterministic.relationships.filter((item) => mission?.work_item_ids.includes(item.source_id) || mission?.work_item_ids.includes(item.target_id)) ?? [];
  const conversations = scene?.deterministic.conversations.filter((item) => mission?.work_item_ids.includes(item.work_item_id)) ?? [];
  const visible = missions.filter((item) => (state === "all" || item.state === state) && `${item.title} ${item.objective_key}`.toLowerCase().includes(query.toLowerCase()));
  return <V2Shell activeItem="Missions" backendOnline={health?.status === "ok"}>
    <V2PageHeader eyebrow="Purpose into work" title="Missions" description="Follow the objective, the people responsible, and what is needed next."><button type="button" onClick={() => void read.refresh()}>Refresh</button></V2PageHeader>
    <ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />
    <div className={s.toolbar}><label>Find a Mission<input type="search" value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>State<select value={state} onChange={(e) => setState(e.target.value)}><option value="all">All states</option>{[...new Set(missions.map((item) => item.state))].map((value) => <option key={value}>{value}</option>)}</select></label><span>{visible.length} of {missions.length} returned</span></div>
    {!read.loading && !read.error && !visible.length ? <EmptyState title={scene ? "No matching Missions" : "No Mission scene established"} detail="Change the filter or return after a governed objective is established." /> : null}
    <div className={s.split}><nav aria-label="Missions"><ul className={s.list}>{visible.map((item) => <li key={item.mission_key}><button type="button" className={s.row} aria-pressed={item.mission_key === current} onClick={() => { setSelected(item.mission_key); setEmployee(null); window.history.replaceState(null, "", `?mission=${encodeURIComponent(item.mission_key)}`); }}><div><strong>{item.title}</strong><small>{item.participant_position_keys.length} participants · {item.blocker_count} blockers</small></div><StatusLabel value={item.state} /></button></li>)}</ul></nav>
      {mission && scene ? <article className={s.detail} data-guide="mission-detail"><StatusLabel value={mission.state} /><h2>{mission.title}</h2><p>Objective: {mission.objective_key}</p><p>Phase: {mission.phase_key ?? "Not supplied"}</p>
        <RelatedLink href={`/cockpit/v2/organization?mission=${encodeURIComponent(mission.mission_key)}`}>Open Mission Room</RelatedLink><RelatedLink href={`/cockpit/v2/history?work=${encodeURIComponent(mission.root_work_item_id)}`}>Mission history</RelatedLink>
        <V2MissionRoomPanel model={room} loading={read.loading} onSelectEmployee={setEmployee} selectedPositionKey={employee} />
        <V2EmployeeInspector model={inspector} onClose={() => setEmployee(null)} />
        <h3>Work & next step</h3><ul className={s.list}>{work.map((item) => <li className={s.row} key={item.work_item_id}><div><strong>{item.title}</strong><small>{item.assigned_position_key} · {item.authority_level}</small><p>{item.specialist_evidence_reason ?? "No next-action instruction supplied in this work projection."}</p></div><StatusLabel value={item.status} /></li>)}</ul>
        <h3>Conversation context</h3>{conversations.length ? conversations.map((item) => <section key={item.conversation_id}><strong>{item.summary}</strong><p>{item.status} · {item.participant_position_keys.join(", ")}</p><p>Transcript {item.transcript_persisted ? "recorded; content not supplied here" : "not persisted"}. Authority effect: {item.authority_effect}.</p></section>) : <p>No linked conversation was returned.</p>}
        <h3>Evidence & decisions</h3>{room?.decisions.map((decision) => <RelatedLink key={decision.decision_id} href={`/cockpit/v2/decisions?decision=${encodeURIComponent(decision.decision_id)}`}>{decision.title}</RelatedLink>)}<RelatedLink href="/cockpit/v2/evidence">Inspect governed Evidence</RelatedLink>
        <Provenance label="Dependencies & Mission provenance"><RecordFields values={{ mission_key: mission.mission_key, root_work_item_id: mission.root_work_item_id, canonical_basis: mission.canonical_basis, relationships, coverage: scene.coverage }} /></Provenance>
      </article> : current && !read.loading && !read.error ? <EmptyState title="Mission not in the returned scene" detail="The selection is preserved; another Mission has not been silently substituted." /> : null}
    </div>
  </V2Shell>;
}
