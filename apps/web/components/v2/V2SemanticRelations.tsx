"use client";
import { useMemo, useState } from "react";
import type { LivingOrganizationScene } from "../../lib/live-organization";
import { resolveV2CharacterPresentation } from "../../lib/v2/character-mission-presentation";
import { buildV2HandoffMotionDescriptor } from "../../lib/v2/character-semantic-motion";
import { useReducedMotion } from "../../hooks/useReducedMotion";
import { V2CharacterMiniature } from "./V2CharacterMiniature";
import { Provenance, RecordFields, RelatedLink, StatusLabel, TruthBadge, formatV2Date, v2Styles as s } from "./V2Primitives";
import styles from "./V2SemanticRelations.module.css";

export function V2SemanticRelations({ scene, onSelectEmployee }: { scene: LivingOrganizationScene; onSelectEmployee: (key: string) => void }) {
  const [selected, setSelected] = useState<string | null>(null);
  const reduced = useReducedMotion();
  const handoff = scene.deterministic.handoffs.find((item) => item.activity_id === selected);
  const sender = scene.deterministic.employees.find((item) => item.position_key === handoff?.previous_position_key);
  const receiver = scene.deterministic.employees.find((item) => item.position_key === handoff?.assigned_position_key);
  const descriptor = useMemo(() => handoff && sender && receiver ? buildV2HandoffMotionDescriptor({ handoff,
    sender: resolveV2CharacterPresentation({ positionKey: sender.position_key, title: sender.title, department: sender.department }),
    receiver: resolveV2CharacterPresentation({ positionKey: receiver.position_key, title: receiver.title, department: receiver.department }),
  }) : null, [handoff, sender, receiver]);
  return <section className={s.detail} data-guide="semantic-relations" aria-label="Organizational relationships">
    <span className={s.eyebrow}>Recorded relationships</span><h2>Work moving through the organization</h2><p>Select a recorded assignment to inspect its direction. The emphasis illustrates the event; it does not represent physical travel or elapsed transfer time.</p>
    <div className={s.toolbar}><label>Recorded handoff<select value={selected ?? ""} onChange={(event) => setSelected(event.target.value || null)}><option value="">Choose a recorded assignment</option>{scene.deterministic.handoffs.map((item) => <option key={item.activity_id} value={item.activity_id}>{item.previous_position_key} → {item.assigned_position_key} · {formatV2Date(item.occurred_at)}</option>)}</select></label></div>
    {handoff ? <div><StatusLabel value={handoff.status} /><p>{formatV2Date(handoff.occurred_at)}</p><div className={styles.transfer} data-supported={Boolean(descriptor?.supported)} data-reduced-motion={reduced} data-canonical-state-writable="false" data-physical-presence-claimed="false">
      <button type="button" disabled={!sender} onClick={() => onSelectEmployee(handoff.previous_position_key)}>{sender ? <V2CharacterMiniature positionKey={sender.position_key} title={sender.title} department={sender.department} /> : handoff.previous_position_key}<span>{sender?.title ?? handoff.previous_position_key}</span></button>
      <div className={styles.path} aria-label={`Assignment from ${handoff.previous_position_key} to ${handoff.assigned_position_key}`}><span>Assignment →</span>{descriptor?.supported ? <i key={handoff.activity_id} aria-hidden="true" /> : null}</div>
      <button type="button" disabled={!receiver} onClick={() => onSelectEmployee(handoff.assigned_position_key)}>{receiver ? <V2CharacterMiniature positionKey={receiver.position_key} title={receiver.title} department={receiver.department} /> : handoff.assigned_position_key}<span>{receiver?.title ?? handoff.assigned_position_key}</span></button>
    </div>{!descriptor?.supported ? <p>Static relation only: {descriptor?.limitation ?? "employee presentation unavailable"}.</p> : null}<Provenance label="Handoff lineage"><RecordFields values={{ activity_id: handoff.activity_id, work_item_id: handoff.work_item_id, canonical_basis: handoff.canonical_basis, causation_activity_id: handoff.causation_activity_id, presentation_truth: descriptor?.truth }} /></Provenance></div> : <p>No assignment selected. No semantic animation is active.</p>}
    <h3>Conversations</h3><p>Coverage: {scene.coverage.conversations}. Participant relations do not imply physical attendance.</p><ul className={s.list}>{scene.deterministic.conversations.map((item) => <li className={s.row} key={item.conversation_id}><div><strong>{item.summary}</strong><div className={styles.participants} data-conversation-state={item.status}>{item.participant_position_keys.map((key) => <button key={key} type="button" onClick={() => onSelectEmployee(key)}>{scene.deterministic.employees.find((employee) => employee.position_key === key)?.title ?? key}</button>)}</div><p>{item.status} · Authority effect: {item.authority_effect} · Transcript {item.transcript_persisted ? "recorded; not supplied here" : "not persisted"}</p><Provenance label="Conversation lifecycle"><RecordFields values={{ conversation_id: item.conversation_id, work_item_id: item.work_item_id, opened_activity_id: item.opened_activity_id, latest_activity_id: item.latest_activity_id, opened_at: item.opened_at, lifecycle_at: item.lifecycle_at, canonical_basis: item.canonical_basis }} /></Provenance></div></li>)}</ul>
    <h3>Board & shared friction</h3>{scene.deterministic.decisions.filter((item) => item.required_owner_action && item.is_current).map((item) => <div className={styles.authority} key={item.decision_id}><TruthBadge kind="authority" /><RelatedLink href={`/cockpit/v2/decisions?decision=${encodeURIComponent(item.decision_id)}`}>{item.title}</RelatedLink><StatusLabel value={item.status} /></div>)}
    <ul className={s.list}>{scene.deterministic.blockers.map((item) => <li className={s.row} key={item.blocker_id}><div><strong>{item.title}</strong><p>{item.description}</p><small>{item.severity} · {item.status}{item.requires_human_action ? " · Human action required" : ""}</small></div></li>)}</ul>
    <Provenance label="Inspectable spatial objects and room state">{scene.deterministic.smart_objects.map((item) => <RecordFields key={item.object_key} values={{ object: item.label, state: item.state, metric: item.metric_label, value: item.metric_value, canonical_basis: item.canonical_basis }} />)}<RecordFields values={{ rooms: scene.deterministic.rooms, coverage: scene.coverage }} /></Provenance>
  </section>;
}
