import type {
  V2MissionRoomModel,
} from "../../lib/v2/mission-room-inspector";
import { V2DataState, V2SectionHeader, V2StateBadge } from "./ui/V2Primitives";
import { V2CharacterMiniature } from "./V2CharacterMiniature";

function timestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "time unavailable";
  return date.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

export function V2MissionRoomPanel({
  model,
  loading,
  selectedPositionKey,
  onSelectEmployee,
}: {
  model: V2MissionRoomModel | null;
  loading: boolean;
  selectedPositionKey: string | null;
  onSelectEmployee: (positionKey: string) => void;
}) {
  return (
    <section className="aios-v2-mission-room" aria-labelledby="aios-v2-mission-room-title">
      <V2SectionHeader eyebrow="Mission Room" id="aios-v2-mission-room-title" title={model?.mission?.title || "Select a Mission"} description="Read-only canonical projection · Mission topology scopes work; governed coordination, Owner / Board attention and explicit completion/resolution remain evidence, not physical activity" />

      {loading ? (
        <V2DataState state={{ kind: "loading", label: "Loading Mission Room projection…" }} />
      ) : !model ? (
        <div className="aios-v2-empty-line" role="status">
          Select a canonical Mission above to inspect its supported participants, blockers, governed coordination evidence, conversations, decisions, Owner / Board attention and handoffs.
        </div>
      ) : !model.established || !model.mission ? (
        <div className="aios-v2-empty-line" role="status">{model.limitation}</div>
      ) : (
        <>
          <div className="aios-v2-mission-room-summary">
            <div><span>State</span><V2StateBadge label={model.mission.state.replaceAll("_", " ")} /></div>
            <div><span>Participants</span><strong>{model.participants.length}</strong></div>
            <div><span>Coordination</span><strong>{model.collaborationCoverageSupported ? model.collaborations.length : "Unavailable"}</strong></div>
            <div><span>Blockers</span><strong>{model.blockerCoverageSupported ? model.blockers.length : "Unavailable"}</strong></div>
            <div><span>Conversations</span><strong>{model.conversationCoverageSupported ? model.conversations.length : "Unavailable"}</strong></div>
            <div><span>Decisions</span><strong>{model.decisions.length}</strong></div>
            <div data-mission-completion-resolution-count={String(model.completions.length)}><span>Completed / resolved</span><strong>{model.completions.length}</strong></div>
            <div data-mission-board-attention={model.boardAttentionCount === null ? "unavailable" : String(model.boardAttentionCount)}><span>Board attention</span><strong>{model.boardAttentionCount === null ? "Unavailable" : model.boardAttentionCount}</strong></div>
            <div><span>Handoffs</span><strong>{model.handoffs.length}</strong></div>
          </div>

          <div className="aios-v2-mission-room-grid">
            <section className="aios-v2-room-participants" aria-labelledby="aios-v2-room-participants-title">
              <header><span>Mission topology participants</span><strong id="aios-v2-room-participants-title">People</strong></header>
              {model.participants.length ? (
                <div className="aios-v2-room-participant-list">
                  {model.participants.map((participant) => (
                    <button aria-pressed={selectedPositionKey === participant.positionKey} className="aios-v2-room-participant" data-selected={String(selectedPositionKey === participant.positionKey)} key={participant.positionKey} onClick={() => onSelectEmployee(participant.positionKey)} type="button">
                      <V2CharacterMiniature department={participant.department} positionKey={participant.positionKey} title={participant.title} />
                      <span className="aios-v2-room-participant-copy">
                        <span>{participant.department}</span><strong>{participant.title}</strong><small>{participant.authorityLevel} · {participant.semanticState.replaceAll("_", " ")}</small>
                        <em>Topology membership only · character is presentation only · collaboration and presence not claimed</em>
                      </span>
                    </button>
                  ))}
                </div>
              ) : <p>No participant positions are supported by this Mission projection.</p>}
            </section>

            <section className="aios-v2-room-signals" aria-labelledby="aios-v2-room-signals-title">
              <header><span>Supported Mission signals</span><strong id="aios-v2-room-signals-title">Canonical links</strong></header>

              <div className="aios-v2-room-signal-group" data-active-collaboration-claimed="false" data-mission-collaboration-coverage={model.collaborationCoverageSupported ? "supported" : "unavailable"} data-mission-coverage={model.missionCoverageState} data-physical-presence-claimed="false">
                <span>Governed Mission coordination</span>
                {!model.collaborationCoverageSupported ? (
                  <p>Coordination evidence unavailable · Mission coverage {model.missionCoverageState} · conversation coverage {model.conversationCoverageState}. AIOS will not infer collaboration from Mission membership or shared topology.</p>
                ) : model.collaborations.length ? (
                  <ul>{model.collaborations.map((item) => (
                    <li data-conversation-id={item.conversationId} data-mission-key={item.missionKey} key={`${item.missionKey}:${item.conversationId}`}>
                      <strong>{item.summary}</strong><small>{item.conversationStatus} · WorkItem {item.workItemId}</small>
                      <small>Exact coordination participants: {item.participants.map((participant) => participant.title).join(" · ")}</small>
                      <small>Mission basis: {item.canonicalBasis.mission} · coordination basis: canonical conversation WorkItem link · lifecycle {timestamp(item.lifecycleAt)}</small>
                    </li>
                  ))}</ul>
                ) : <p>No governed coordination evidence is linked to this Mission under established Mission and conversation coverage.</p>}
              </div>

              <div className="aios-v2-room-signal-group" data-blocker-coverage={model.blockerCoverageState}>
                <span>Blockers</span>
                {!model.blockerCoverageSupported ? <p>Blocker coverage unavailable · {model.blockerCoverageState}. AIOS will not present an empty blocker list as canonical zero.</p> : model.blockers.length ? (
                  <ul>{model.blockers.map((blocker) => <li key={blocker.blocker_id}><strong>{blocker.title}</strong><small>{blocker.severity} · {blocker.blocker_type} · {blocker.status}</small></li>)}</ul>
                ) : <p>No linked blockers under established canonical blocker coverage.</p>}
              </div>

              <div className="aios-v2-room-signal-group" data-conversation-coverage={model.conversationCoverageState} data-live-speech-claimed="false" data-transcript-claimed="false">
                <span>Governed conversations</span>
                {!model.conversationCoverageSupported ? <p>Conversation lifecycle unavailable · {model.conversationCoverageState}. AIOS will not infer dialogue or participation from unrelated activity.</p> : model.conversations.length ? (
                  <ul>{model.conversations.map((conversation) => <li data-conversation-id={conversation.conversationId} key={conversation.conversationId}><strong>{conversation.summary}</strong><small>{conversation.status} · WorkItem {conversation.workItemId}</small><small>Participants: {conversation.participants.map((participant) => participant.title).join(" · ")}</small><small>Authority effect: none · transcript not persisted · lifecycle {timestamp(conversation.lifecycleAt)}</small></li>)}</ul>
                ) : <p>No governed conversation lifecycle is linked to this Mission.</p>}
              </div>

              <div className="aios-v2-room-signal-group" data-canonical-completion-resolution="true" data-completion-inferred-from-animation="false" data-physical-celebration-claimed="false" data-physical-presence-claimed="false">
                <span>Completed / resolved evidence</span>
                {model.completions.length ? (
                  <ul>{model.completions.map((event) => {
                    const when = event.kind === "work_completed" ? event.completedAt : event.kind === "decision_outcome" ? event.decidedAt : event.occurredAt;
                    const label = event.kind === "work_completed" ? "WorkItem completed" : event.kind === "blocker_resolved" ? "Blocker resolved" : event.kind === "blocker_waived" ? "Blocker waived" : event.kind === "decision_outcome" ? `Decision ${event.status}` : "Canonical transition";
                    const key = event.kind === "work_completed" ? `work:${event.workItemId}` : event.kind === "decision_outcome" ? `decision:${event.decisionId}` : `blocker:${event.blockerId}:${event.kind}`;
                    return <li data-transition-kind={event.kind} key={key}><strong>{event.title}</strong><small>{label} · {timestamp(when)}</small>{event.kind === "blocker_resolved" || event.kind === "blocker_waived" ? <small>{event.outcomeSummary} · {event.resolverLabel}</small> : null}</li>;
                  })}</ul>
                ) : <p>No explicit canonical completion or resolution transition is linked to this Mission.</p>}
                <small>Exact canonical transition fields only · no completion inferred from settled character state, animation, elapsed time or missing markers · no physical celebration or movement.</small>
              </div>

              <div className="aios-v2-room-signal-group">
                <span>Decisions</span>
                {model.decisions.length ? <ul>{model.decisions.map((decision) => <li key={decision.decision_id}><strong>{decision.title}</strong><small>{decision.authority_level} · {decision.status}{decision.required_owner_action ? " · owner action required" : ""}</small></li>)}</ul> : <p>No linked decisions.</p>}
              </div>

              <div className="aios-v2-room-signal-group" data-board-meeting-claimed="false" data-human-action-coverage={model.humanActionCoverageState} data-risk-escalation-coverage={model.riskEscalationCoverageState}>
                <span>Owner / Board attention</span>
                {!model.humanActionCoverageSupported || !model.riskEscalationCoverageSupported ? (
                  <p>Attention evidence is partially unavailable · human actions {model.humanActionCoverageState} · risks {model.riskEscalationCoverageState}. AIOS will not infer Board attention from severity, Mission membership or room placement.</p>
                ) : (
                  <>
                    {model.humanActions.length ? <ul>{model.humanActions.map((request) => <li data-human-action-id={request.requestId} key={request.requestId}><strong>{request.title}</strong><small>{request.status} · required role {request.requiredRole} · priority {request.priority}</small><small>{request.instructions}</small></li>)}</ul> : <p>No active human-action request is linked to this Mission.</p>}
                    {model.riskEscalations.length ? <ul>{model.riskEscalations.map((risk) => <li data-risk-id={risk.riskId} key={risk.riskId}><strong>{risk.title}</strong><small>{risk.status} · {risk.severity} · {risk.accountableParticipant?.title ?? risk.accountablePositionKey} → {risk.escalatedToParticipant?.title ?? risk.escalatedToPositionKey}{risk.requiresBoardAttention ? " · Board attention required" : ""}{risk.isEmergency ? " · emergency" : ""}</small><small>{risk.description}</small></li>)}</ul> : <p>No unresolved risk escalation is linked to this Mission.</p>}
                  </>
                )}
                <small>Canonical attention/routing evidence only · no Board meeting · no approval inferred · no physical attendance or movement.</small>
              </div>

              <div className="aios-v2-room-signal-group"><span>Handoffs</span>{model.handoffs.length ? <ul>{model.handoffs.slice(0, 6).map((handoff) => <li key={handoff.activity_id}><strong>{handoff.previous_position_key} → {handoff.assigned_position_key}</strong><small>{handoff.status} · {timestamp(handoff.occurred_at)}</small></li>)}</ul> : <p>No linked handoff events.</p>}</div>
            </section>
          </div>

          <footer className="aios-v2-room-truth">
            <span>Canonical projection: {model.canonicalProjection ? "yes" : "no"}</span>
            <span>Scene authority: {model.sceneAuthoritative ? "authoritative" : "non-authoritative"}</span>
            <span>Renderer authority: {model.rendererAuthoritative ? "authoritative" : "none"}</span>
            <span>Mission coverage: {model.missionCoverageState}</span><span>Blocker coverage: {model.blockerCoverageState}</span><span>Conversation coverage: {model.conversationCoverageState}</span>
            <span>Human-action coverage: {model.humanActionCoverageState}</span><span>Risk-escalation coverage: {model.riskEscalationCoverageState}</span>
            <span>Completion/resolution basis: exact canonical transition fields only</span><span>Completion inferred from animation: no</span><span>Physical celebration claimed: no</span><span>Board meeting claimed: no</span><span>Approval inferred: no</span><span>Active collaboration claimed: no</span><span>Physical presence claimed: no</span><span>Live speech claimed: no</span><span>Transcript claimed: no</span>
            <span>Mutation: {model.mutationsAllowed ? "allowed" : "disabled"}</span>
          </footer>
        </>
      )}
    </section>
  );
}
