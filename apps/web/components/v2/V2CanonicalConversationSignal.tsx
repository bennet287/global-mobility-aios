import type { V2VisibleConversationCollection } from "../../lib/v2/visible-conversation";
import styles from "./V2CanonicalConversationSignal.module.css";

export function V2CanonicalConversationSignal({
  conversations,
  variant,
}: {
  readonly conversations: V2VisibleConversationCollection;
  readonly variant: "spatial" | "structured";
}) {
  if (!conversations.supported) {
    return (
      <div
        className="aios-v2-source-warning"
        data-conversation-coverage={conversations.coverageState}
        data-live-speech-claimed="false"
        data-transcript-claimed="false"
        role="status"
      >
        <div>
          <strong>Conversation lifecycle unavailable.</strong>
          <span>
            Coverage: {conversations.coverageState}. AIOS will not infer dialogue,
            participation, transcript or authority from other scene activity.
          </span>
        </div>
      </div>
    );
  }

  const open = conversations.items.filter((conversation) => conversation.status === "open");
  if (!open.length) return null;

  return (
    <section
      aria-label="Governed conversation lifecycle"
      className={`${styles.root} ${variant === "spatial" ? styles.spatial : ""}`}
      data-aios-v2-conversation="canonical-lifecycle"
      data-conversation-count={String(open.length)}
      data-live-speech-claimed="false"
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-transcript-claimed="false"
      data-variant={variant}
    >
      <header className={styles.header}>
        <strong>Governed conversation lifecycle</strong>
        <span>{open.length} open</span>
      </header>
      <ul className={styles.list}>
        {open.slice(0, 3).map((conversation) => (
          <li className={styles.item} data-conversation-id={conversation.conversationId} key={conversation.conversationId}>
            <strong>{conversation.summary}</strong>
            <small>
              {conversation.participants.map((participant) => participant.title).join(" · ")}
              {` · WorkItem ${conversation.workItemId}`}
            </small>
          </li>
        ))}
      </ul>
      <small className={styles.truth}>
        Canonical lifecycle evidence only · not live speech · not co-location · transcript not persisted · authority effect none
      </small>
    </section>
  );
}
