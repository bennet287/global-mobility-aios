import type { V2VisibleOwnerBoardEscalationCollection } from "../../lib/v2/visible-owner-board-escalation";
import styles from "./V2CanonicalConversationSignal.module.css";

export function V2CanonicalOwnerBoardEscalationSignal({
  escalation,
  variant,
}: {
  readonly escalation: V2VisibleOwnerBoardEscalationCollection;
  readonly variant: "spatial" | "structured";
}) {
  const hasCoverageGap =
    !escalation.humanActionCoverageSupported || !escalation.riskEscalationCoverageSupported;

  if (
    hasCoverageGap &&
    escalation.decisionAttention.length === 0 &&
    escalation.humanActions.length === 0 &&
    escalation.riskEscalations.length === 0
  ) {
    return (
      <div
        className="aios-v2-source-warning"
        data-aios-v2-owner-board-escalation="unavailable"
        data-board-meeting-claimed="false"
        data-human-action-coverage={escalation.humanActionCoverageState}
        data-physical-presence-claimed="false"
        data-risk-escalation-coverage={escalation.riskEscalationCoverageState}
        role="status"
      >
        <div>
          <strong>Owner / Board attention evidence partially unavailable.</strong>
          <span>{escalation.limitation}</span>
        </div>
      </div>
    );
  }

  const boardRisks = escalation.riskEscalations.filter((risk) => risk.requiresBoardAttention);
  const routedRisks = escalation.riskEscalations.slice(0, 3);
  const totalVisible =
    escalation.decisionAttention.length + escalation.humanActions.length + escalation.riskEscalations.length;
  if (!totalVisible && !hasCoverageGap) return null;

  return (
    <section
      aria-label="Canonical Owner and Board attention evidence"
      className={`${styles.root} ${variant === "spatial" ? styles.spatial : ""}`}
      data-aios-v2-owner-board-escalation="canonical-attention"
      data-approval-claimed="false"
      data-board-attention-count={
        escalation.boardAttentionCount === null ? "unavailable" : String(escalation.boardAttentionCount)
      }
      data-board-meeting-claimed="false"
      data-canonical-mutation-allowed="false"
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-variant={variant}
    >
      <header className={styles.header}>
        <strong>Owner / Board attention</strong>
        <span>
          {escalation.boardAttentionCount === null
            ? "partial coverage"
            : `${escalation.boardAttentionCount} canonical attention ${escalation.boardAttentionCount === 1 ? "item" : "items"}`}
        </span>
      </header>

      {escalation.decisionAttention.slice(0, 2).map((decision) => (
        <div className={styles.item} data-decision-id={decision.decisionId} key={`decision:${decision.decisionId}`}>
          <strong>{decision.title}</strong>
          <small>
            Decision attention · {decision.status} · owner {decision.decisionOwnerPosition} · authority {decision.authorityLevel}
          </small>
        </div>
      ))}

      {escalation.humanActions.slice(0, 2).map((request) => (
        <div className={styles.item} data-human-action-id={request.requestId} key={`human:${request.requestId}`}>
          <strong>{request.title}</strong>
          <small>
            Human action · {request.status} · required role {request.requiredRole} · priority {request.priority}
          </small>
        </div>
      ))}

      {routedRisks.map((risk) => (
        <div className={styles.item} data-risk-id={risk.riskId} key={`risk:${risk.riskId}`}>
          <strong>{risk.title}</strong>
          <small>
            Risk route · {risk.accountableParticipant?.title ?? risk.accountablePositionKey} → {risk.escalatedToParticipant?.title ?? risk.escalatedToPositionKey}
            {risk.requiresBoardAttention ? " · Board attention required" : ""}
            {risk.isEmergency ? " · emergency" : ""}
          </small>
        </div>
      ))}

      {hasCoverageGap ? <small className={styles.truth}>{escalation.limitation}</small> : null}
      <small className={styles.truth}>
        Canonical attention and routing evidence only · {boardRisks.length} explicit Board-attention {boardRisks.length === 1 ? "risk" : "risks"} · no Board meeting · no approval inferred · no physical presence or room attendance
      </small>
    </section>
  );
}
