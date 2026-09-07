import type { V2VisibleCompletionResolution } from "../../lib/v2/visible-completion-resolution";
import styles from "./V2CanonicalConversationSignal.module.css";

function eventTimestamp(event: V2VisibleCompletionResolution): string {
  if (event.kind === "work_completed") return event.completedAt;
  if (event.kind === "decision_outcome") return event.decidedAt;
  return event.occurredAt;
}

function eventLabel(event: V2VisibleCompletionResolution): string {
  if (event.kind === "work_completed") return "WorkItem completed";
  if (event.kind === "blocker_resolved") return "Blocker resolved";
  if (event.kind === "blocker_waived") return "Blocker waived";
  if (event.kind === "decision_outcome") return `Decision ${event.status}`;
  return "Canonical transition";
}

export function V2CanonicalCompletionResolutionSignal({
  events,
  variant,
}: {
  readonly events: readonly V2VisibleCompletionResolution[];
  readonly variant: "spatial" | "structured";
}) {
  if (!events.length) return null;

  return (
    <section
      aria-label="Canonical completion and resolution evidence"
      className={`${styles.root} ${variant === "spatial" ? styles.spatial : ""}`}
      data-aios-v2-completion-resolution="canonical-evidence"
      data-canonical-mutation-allowed="false"
      data-completion-inferred-from-animation="false"
      data-locomotion-claimed="false"
      data-physical-celebration-claimed="false"
      data-physical-presence-claimed="false"
      data-variant={variant}
    >
      <header className={styles.header}>
        <strong>Completed / resolved evidence</strong>
        <span>{events.length} canonical {events.length === 1 ? "transition" : "transitions"}</span>
      </header>

      {events.slice(0, 4).map((event) => (
        <div
          className={styles.item}
          data-transition-kind={event.kind}
          key={
            event.kind === "work_completed"
              ? `work:${event.workItemId}`
              : event.kind === "decision_outcome"
                ? `decision:${event.decisionId}`
                : `blocker:${event.blockerId}:${event.kind}`
          }
        >
          <strong>{event.title}</strong>
          <small>
            {eventLabel(event)} · {new Date(eventTimestamp(event)).toLocaleString()}
          </small>
          {event.kind === "blocker_resolved" || event.kind === "blocker_waived" ? (
            <small>{event.outcomeSummary} · {event.resolverLabel}</small>
          ) : null}
        </div>
      ))}

      <small className={styles.truth}>
        Explicit canonical transition evidence only · no celebration, travel or physical presence · no completion inferred from animation or elapsed time
      </small>
    </section>
  );
}
