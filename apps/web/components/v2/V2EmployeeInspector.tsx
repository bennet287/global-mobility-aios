import type { V2EmployeeInspectorModel } from "../../lib/v2/mission-room-inspector";
import {
  V2AuthorityBadge,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
} from "./ui/V2Primitives";
import { V2CharacterMiniature } from "./V2CharacterMiniature";

function blockerRelation(
  model: V2EmployeeInspectorModel,
  accountablePositionKey: string | null,
): string {
  return accountablePositionKey === model.employee?.position_key
    ? "Accountable position"
    : "Linked WorkItem";
}

function utcLabel(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

export function V2EmployeeInspector({
  model,
  onClose,
}: {
  model: V2EmployeeInspectorModel | null;
  onClose: () => void;
}) {
  if (!model) {
    return (
      <aside className="aios-v2-employee-inspector empty" aria-label="Employee Inspector">
        <div className="aios-v2-empty-line" role="status">
          Select a rostered Mission participant to inspect canonical employee state.
        </div>
      </aside>
    );
  }

  if (!model.established || !model.employee) {
    return (
      <aside className="aios-v2-employee-inspector" aria-label="Employee Inspector">
        <header className="aios-v2-inspector-header">
          <div><span>Employee Inspector</span><strong>Unsupported employee</strong></div>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <div className="aios-v2-empty-line" role="status">{model.limitation}</div>
      </aside>
    );
  }

  const employee = model.employee;

  return (
    <aside
      className="aios-v2-employee-inspector"
      aria-labelledby="aios-v2-employee-inspector-title"
      data-active-collaboration-claimed="false"
      data-blocker-details-claimed={model.blockerCoverageSupported ? "true" : "false"}
      data-explicit-completion-resolution-claimed={model.completions.length ? "canonical-records-only" : "none"}
      data-completion-inferred-from-animation="false"
      data-physical-celebration-claimed="false"
      data-board-meeting-claimed="false"
      data-causal-block-claimed="false"
      data-conversation-lifecycle-claimed={model.conversationCoverageSupported ? "true" : "false"}
      data-governed-mission-coordination-claimed={model.collaborationCoverageSupported ? "true" : "false"}
      data-live-speech-claimed="false"
      data-locomotion-claimed="false"
      data-mutations-allowed={String(model.mutationsAllowed)}
      data-physical-location-claimed="false"
      data-presence-claimed="false"
      data-risk-escalation-coverage={model.riskEscalationCoverageState}
      data-transcript-claimed="false"
    >
      <V2SectionHeader
        actions={<button type="button" onClick={onClose}>Close</button>}
        eyebrow="Employee Inspector"
        id="aios-v2-employee-inspector-title"
        title={employee.title}
      />

      <V2CharacterMiniature department={employee.department} positionKey={employee.position_key} title={employee.title} variant="inspector" />

      <div className="aios-v2-inspector-identity">
        <div><span>Position key</span><strong>{employee.position_key}</strong></div>
        <div><span>Department</span><strong>{employee.department}</strong></div>
        <div><span>Authority</span><V2AuthorityBadge level={employee.authority_level} /></div>
        <div><span>Organization state</span><strong>{employee.organization_status}</strong></div>
      </div>

      <section className="aios-v2-inspector-state" aria-label="Canonical presentation state">
        <span>Canonical presentation state</span>
        <V2StateBadge label={employee.semantic_state.replaceAll("_", " ")} />
        <p>{employee.state_reason}</p>
        <small>{employee.work_status ? "Linked work status: " + employee.work_status.replaceAll("_", " ") : "No linked WorkItem status is exposed for this employee."}</small>
      </section>

      <section className="aios-v2-inspector-links" aria-label="Linked canonical records">
        <div><span>Missions</span><strong>{model.activeMissionKeys.length}</strong></div>
        <div><span>Coordination</span><strong>{model.collaborationCoverageSupported ? model.collaborations.length : "Unavailable"}</strong></div>
        <div><span>Risk routes</span><strong>{model.riskEscalationCoverageSupported ? model.escalationRisks.length : "Unavailable"}</strong></div>
        <div><span>Completed / resolved</span><strong>{model.completions.length}</strong></div>
        <div><span>Blockers</span><strong>{model.blockerCoverageSupported ? model.blockerIds.length : "Unavailable"}</strong></div>
        <div><span>Conversations</span><strong>{model.conversationCoverageSupported ? model.conversations.length : "Unavailable"}</strong></div>
        <div><span>Decisions</span><strong>{model.decisionIds.length}</strong></div>
        <div><span>Handoffs</span><strong>{model.handoffActivityIds.length}</strong></div>
      </section>

      {model.completions.length ? (
        <section aria-label="Canonical completion and resolution evidence" className="aios-v2-inspector-missions" data-canonical-completion-resolution="true" data-completion-inferred-from-animation="false" data-physical-celebration-claimed="false">
          <span>Completed / resolved evidence</span>
          <ul>{model.completions.map((event) => {
            const when = event.kind === "work_completed" ? event.completedAt : event.kind === "decision_outcome" ? event.decidedAt : event.occurredAt;
            const label = event.kind === "work_completed" ? "WorkItem completed" : event.kind === "blocker_resolved" ? "Blocker resolved" : event.kind === "blocker_waived" ? "Blocker waived" : event.kind === "decision_outcome" ? `Decision ${event.status}` : "Canonical transition";
            const key = event.kind === "work_completed" ? `work:${event.workItemId}` : event.kind === "decision_outcome" ? `decision:${event.decisionId}` : `blocker:${event.blockerId}:${event.kind}`;
            return <li data-transition-kind={event.kind} key={key}><strong>{event.title}</strong><small>{label}{utcLabel(when) ? ` · ${utcLabel(when)}` : ""}</small>{event.kind === "blocker_resolved" || event.kind === "blocker_waived" ? <><small>{event.outcomeSummary}</small><small>Resolver: {event.resolverLabel}</small></> : null}</li>;
          })}</ul>
          <small>Exact assigned/linked WorkItem transition evidence only. Employee state, animation, elapsed time and Mission membership do not establish completion or resolution; no physical celebration, presence or locomotion is asserted.</small>
        </section>
      ) : null}

      {model.riskEscalationCoverageSupported ? (
        model.escalationRisks.length ? (
          <section aria-label="Canonical risk escalation routes" className="aios-v2-inspector-missions" data-board-meeting-claimed="false" data-canonical-risk-escalation="true" data-physical-presence-claimed="false">
            <span>Risk escalation routes</span>
            <ul>
              {model.escalationRisks.map((risk) => {
                const relationship = risk.accountablePositionKey === employee.position_key
                  ? "Accountable position"
                  : "Escalated-to position";
                return (
                  <li data-risk-id={risk.riskId} key={risk.riskId}>
                    <strong>{risk.title}</strong>
                    <small>{risk.status} · {risk.category} · severity {risk.severity}</small>
                    <small>Relationship: {relationship}</small>
                    <small>Route: {risk.accountableParticipant?.title ?? risk.accountablePositionKey} → {risk.escalatedToParticipant?.title ?? risk.escalatedToPositionKey}</small>
                    <small>{risk.requiresBoardAttention ? "Board attention explicitly required" : "Board attention not asserted"}{risk.isEmergency ? " · emergency" : ""}{utcLabel(risk.createdAt) ? ` · created ${utcLabel(risk.createdAt)}` : ""}</small>
                    <p>{risk.description}</p>
                  </li>
                );
              })}
            </ul>
            <small>Exact canonical risk-routing evidence only. Severity does not imply Board attention, and a route does not establish a Board meeting, approval, physical attendance, room presence or movement.</small>
          </section>
        ) : (
          <div className="aios-v2-empty-line" role="status">No unresolved canonical risk escalation names this employee as the accountable or escalated-to position.</div>
        )
      ) : (
        <div className="aios-v2-source-warning" data-risk-escalation-coverage={model.riskEscalationCoverageState} role="status">
          <div><strong>Risk escalation routes unavailable.</strong><span>Coverage: {model.riskEscalationCoverageState}. AIOS will not infer escalation from severity, shared WorkItems, Mission membership or room placement.</span></div>
        </div>
      )}

      {model.collaborationCoverageSupported ? (
        model.collaborations.length ? (
          <section aria-label="Governed Mission coordination evidence" className="aios-v2-inspector-missions" data-active-collaboration-claimed="false" data-canonical-mission-coordination="true" data-physical-presence-claimed="false">
            <span>Governed Mission coordination</span>
            <ul>{model.collaborations.map((item) => <li data-conversation-id={item.conversationId} data-mission-key={item.missionKey} key={`${item.missionKey}:${item.conversationId}`}><strong>{item.missionTitle}</strong><small>{item.summary}</small><small>{item.conversationStatus} · WorkItem {item.workItemId}</small><small>Exact coordination participants: {item.participants.map((participant) => participant.title).join(" · ")}</small><small>Mission topology scopes the work · canonical conversation WorkItem link supplies coordination evidence{utcLabel(item.lifecycleAt) ? ` · lifecycle ${utcLabel(item.lifecycleAt)}` : ""}</small></li>)}</ul>
            <small>Governed coordination evidence does not establish active teamwork, live speech, co-location, physical presence, completion, or an authority outcome.</small>
          </section>
        ) : <div className="aios-v2-empty-line" role="status">No governed Mission coordination evidence is linked to this employee under established Mission and conversation coverage.</div>
      ) : <div className="aios-v2-source-warning" data-mission-coverage={model.missionCoverageState} role="status"><div><strong>Mission coordination evidence unavailable.</strong><span>Mission coverage: {model.missionCoverageState} · conversation coverage: {model.conversationCoverageState}. AIOS will not infer collaboration from Mission membership, shared WorkItems or room placement.</span></div></div>}

      {model.blockerCoverageSupported ? (
        model.blockers.length ? (
          <section aria-label="Canonical blocker details" className="aios-v2-inspector-missions" data-canonical-blocker-details="true"><span>Canonical blockers</span><ul>{model.blockers.map((blocker) => { const due = utcLabel(blocker.due_at); return <li data-blocker-id={blocker.blocker_id} data-blocker-severity={blocker.severity} data-blocker-status={blocker.status} key={blocker.blocker_id}><strong>{blocker.title}</strong><small>{blocker.severity} · {blocker.blocker_type} · {blocker.status}</small>{blocker.description ? <p>{blocker.description}</p> : null}<small>Relationship: {blockerRelation(model, blocker.accountable_position_key)}</small><small>Human action: {blocker.requires_human_action ? "required" : "not required"}{blocker.overdue ? " · overdue" : ""}{due ? ` · due ${due}` : ""}</small></li>; })}</ul><small>Canonical blocker records describe governed work constraints. Resolution or waiver is claimed only when the explicit transition evidence section has the full canonical timestamp and outcome/resolver tuple; blocker styling itself establishes no physical activity or causal body movement.</small></section>
        ) : <div className="aios-v2-empty-line" role="status">No canonical blocker is linked to this employee under the current blocker coverage.</div>
      ) : <div className="aios-v2-source-warning" data-blocker-coverage={model.blockerCoverageState} role="status"><div><strong>Blocker details unavailable.</strong><span>Coverage: {model.blockerCoverageState}. AIOS will not infer blocker title, type, severity or accountability from the employee work-state badge.</span></div></div>}

      {model.conversationCoverageSupported ? (
        model.conversations.length ? (
          <section aria-label="Governed conversation lifecycle" className="aios-v2-inspector-missions" data-canonical-conversation-details="true" data-live-speech-claimed="false" data-transcript-claimed="false"><span>Governed conversations</span><ul>{model.conversations.map((conversation) => <li data-conversation-id={conversation.conversationId} data-conversation-status={conversation.status} key={conversation.conversationId}><strong>{conversation.summary}</strong><small>{conversation.status} · WorkItem {conversation.workItemId}</small><small>Participants: {conversation.participants.map((participant) => participant.title).join(" · ")}</small><small>Authority effect: none · transcript not persisted{utcLabel(conversation.lifecycleAt) ? ` · lifecycle ${utcLabel(conversation.lifecycleAt)}` : ""}</small></li>)}</ul><small>Conversation lifecycle is canonical communication evidence only. It does not establish live speech, co-location, a persisted transcript, or an authority outcome.</small></section>
        ) : <div className="aios-v2-empty-line" role="status">No governed conversation lifecycle is linked to this employee under established conversation coverage.</div>
      ) : <div className="aios-v2-source-warning" data-conversation-coverage={model.conversationCoverageState} role="status"><div><strong>Conversation lifecycle unavailable.</strong><span>Coverage: {model.conversationCoverageState}. AIOS will not infer dialogue, participation, transcript or authority from other activity.</span></div></div>}

      {model.activeMissionKeys.length ? <div className="aios-v2-inspector-missions"><span>Mission topology membership</span><ul>{model.activeMissionKeys.map((missionKey) => <li key={missionKey}>{missionKey}</li>)}</ul><small>Mission membership scopes the projection only; it is not itself collaboration evidence.</small></div> : null}

      <p>Roster identity is not physical presence.</p>
      <V2ProvenanceDisclosure title="Presentation truth">
        <footer className="aios-v2-inspector-truth">
          <strong>Roster identity is not physical presence.</strong>
          <span>Mission membership alone claims collaboration: no</span>
          <span>Governed coordination evidence claimed: {model.collaborationCoverageSupported ? "supported records only" : "unavailable"}</span>
          <span>Risk escalation routing claimed: {model.riskEscalationCoverageSupported ? "exact accountable/escalated-to records only" : "unavailable"}</span>
          <span>Completion/resolution claimed: {model.completions.length ? "exact canonical transition records only" : "none"}</span><span>Completion inferred from animation: no</span><span>Physical celebration claimed: no</span><span>Board meeting claimed: no</span><span>Approval inferred: no</span><span>Active collaboration claimed: no</span><span>Presence claimed: no</span><span>Locomotion claimed: no</span><span>Live speech claimed: no</span><span>Transcript claimed: no</span><span>Conversation authority effect claimed: no</span>
          <span>Mutation: {model.mutationsAllowed ? "allowed by source posture" : "disabled"}</span>
        </footer>
      </V2ProvenanceDisclosure>
    </aside>
  );
}
