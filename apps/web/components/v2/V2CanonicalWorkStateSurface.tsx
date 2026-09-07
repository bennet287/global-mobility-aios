import type { ReactNode } from "react";

import type { V2VisibleWorkStateModel } from "../../lib/v2/visible-work-state";
import styles from "./V2CanonicalWorkStateSurface.module.css";

export type V2CanonicalWorkStateSurfaceProps = {
  readonly model: V2VisibleWorkStateModel;
  readonly reducedMotion: boolean;
  readonly children: ReactNode;
};

const STATE_CLASS: Readonly<Record<string, string>> = Object.freeze({
  focused_work: "focusedWork",
  blocked_wait: "blockedWait",
  awaiting_attention: "awaitingAttention",
  queued_wait: "queuedWait",
  settled_idle: "settledIdle",
  neutral_static: "neutralStatic",
});

export function V2CanonicalWorkStateSurface({
  model,
  reducedMotion,
  children,
}: V2CanonicalWorkStateSurfaceProps) {
  if (!model.supported || model.kind === null) return <>{children}</>;

  const stateClass = styles[STATE_CLASS[model.presentationState]] ?? styles.neutralStatic;
  const rootClassName = [
    styles.root,
    stateClass,
    reducedMotion ? styles.reducedMotion : "",
  ]
    .filter(Boolean)
    .join(" ");
  const animationActive = !reducedMotion && model.motion !== "none";

  return (
    <span
      className={rootClassName}
      data-aios-v2-work-state="canonical"
      data-blocker-details-claimed="false"
      data-blocker-resolution-claimed="false"
      data-canonical-semantic-state={model.canonicalSemanticState}
      data-canonical-state-source={model.truth.canonicalStateSource}
      data-canonical-state-writable="false"
      data-completion-event-claimed="false"
      data-conversation-claimed="false"
      data-handoff-claimed="false"
      data-locomotion-allowed="false"
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-physical-travel-claimed="false"
      data-presentation-only="true"
      data-semantic-animation-active={animationActive ? "true" : "false"}
      data-work-item-linked={model.truth.workItemRelationPresent ? "true" : "false"}
      data-work-state-kind={model.kind}
      title={`${model.label} · ${model.stateReason}`}
    >
      <span aria-hidden="true" className={styles.stateHalo} data-work-state-part="halo" />
      <span className={styles.character} data-work-state-part="character">{children}</span>
      <span
        className={styles.stateBadge}
        data-state-label={model.kind}
        data-work-state-part="badge"
      >
        {model.shortLabel}
      </span>
    </span>
  );
}