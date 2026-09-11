import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

const CLOSED_STATES = new Set(["completed", "resolved", "closed", "cancelled", "canceled", "dismissed"]);

function isOpenState(value: string): boolean {
  return !CLOSED_STATES.has(value.toLowerCase());
}

type Reaction = {
  key: string;
  kind: "handoff" | "conversation" | "blocker" | "decision" | "human-action" | "board-risk";
  label: string;
  count: number;
  emphasis: "coordination" | "attention" | "governance";
};

export function LivingOrganizationEventReactions({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const openHandoffs = renderModel.handoffs.filter((handoff) => isOpenState(handoff.status));
  const openConversations = renderModel.conversations.filter((conversation) => isOpenState(conversation.status));
  const openBlockers = renderModel.blockers.filter((blocker) => isOpenState(blocker.status));
  const currentDecisions = renderModel.decisions.filter((decision) => decision.is_current);
  const openHumanActions = renderModel.humanActions.filter((request) => isOpenState(request.status));
  const boardRisks = renderModel.riskEscalations.filter(
    (risk) => risk.requires_board_attention && isOpenState(risk.status),
  );

  const reactions: Reaction[] = [
    { key: "handoff", kind: "handoff", label: "Canonical handoff", count: openHandoffs.length, emphasis: "coordination" },
    { key: "conversation", kind: "conversation", label: "Governed conversation", count: openConversations.length, emphasis: "coordination" },
    { key: "blocker", kind: "blocker", label: "Open blocker", count: openBlockers.length, emphasis: "attention" },
    { key: "decision", kind: "decision", label: "Current decision", count: currentDecisions.length, emphasis: "governance" },
    { key: "human-action", kind: "human-action", label: "Human action", count: openHumanActions.length, emphasis: "governance" },
    { key: "board-risk", kind: "board-risk", label: "Board-attention risk", count: boardRisks.length, emphasis: "governance" },
  ].filter((reaction) => reaction.count > 0);

  return (
    <div
      className="living-hq-event-reactions"
      aria-label="Canonical organizational event reactions"
      data-presentation-only="true"
      data-authority="none"
      data-locomotion-allowed="false"
      data-reaction-source="canonical-only"
      data-reaction-count={reactions.length}
      data-handoff-count={openHandoffs.length}
      data-conversation-count={openConversations.length}
      data-blocker-count={openBlockers.length}
      data-decision-count={currentDecisions.length}
      data-human-action-count={openHumanActions.length}
      data-board-risk-count={boardRisks.length}
    >
      {reactions.map((reaction) => (
        <div
          key={reaction.key}
          className="living-hq-event-reaction"
          data-reaction-kind={reaction.kind}
          data-reaction-emphasis={reaction.emphasis}
          data-canonical-count={reaction.count}
        >
          <i aria-hidden="true" />
          <span>
            <strong>{reaction.count}</strong>
            <small>{reaction.label}</small>
          </span>
        </div>
      ))}
      {!reactions.length ? <span className="living-hq-event-reactions-empty">No active canonical event reaction</span> : null}
    </div>
  );
}
