import type { V2VisibleMissionCollaborationCollection } from "../../lib/v2/visible-mission-collaboration";
import styles from "./V2CanonicalConversationSignal.module.css";

export function V2CanonicalMissionCollaborationSignal({
  collaborations,
  variant,
}: {
  readonly collaborations: V2VisibleMissionCollaborationCollection;
  readonly variant: "spatial" | "structured";
}) {
  if (!collaborations.supported) {
    return (
      <div
        className="aios-v2-source-warning"
        data-active-collaboration-claimed="false"
        data-conversation-coverage={collaborations.conversationCoverageState}
        data-mission-collaboration-coverage="unavailable"
        data-mission-coverage={collaborations.missionCoverageState}
        data-physical-presence-claimed="false"
        role="status"
      >
        <div>
          <strong>Mission coordination evidence unavailable.</strong>
          <span>{collaborations.limitation}</span>
        </div>
      </div>
    );
  }

  const open = collaborations.items.filter((item) => item.conversationStatus === "open");
  if (!open.length) return null;

  return (
    <section
      aria-label="Governed Mission coordination evidence"
      className={`${styles.root} ${variant === "spatial" ? styles.spatial : ""}`}
      data-active-collaboration-claimed="false"
      data-aios-v2-mission-collaboration="governed-coordination"
      data-coordination-count={String(open.length)}
      data-live-speech-claimed="false"
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-variant={variant}
    >
      <header className={styles.header}>
        <strong>Governed Mission coordination</strong>
        <span>{open.length} active lifecycle {open.length === 1 ? "link" : "links"}</span>
      </header>
      <ul className={styles.list}>
        {open.slice(0, 3).map((item) => (
          <li
            className={styles.item}
            data-conversation-id={item.conversationId}
            data-mission-key={item.missionKey}
            key={`${item.missionKey}:${item.conversationId}`}
          >
            <strong>{item.missionTitle}</strong>
            <small>{item.summary}</small>
            <small>
              {item.participants.map((participant) => participant.title).join(" · ")}
              {` · WorkItem ${item.workItemId}`}
            </small>
          </li>
        ))}
      </ul>
      <small className={styles.truth}>
        Canonical coordination evidence only · Mission topology scopes the work · exact conversation participants supply the coordination relation · not live teamwork · not co-location
      </small>
    </section>
  );
}
