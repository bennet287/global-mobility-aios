import type { CSSProperties, ReactNode } from "react";
import type {
  V2AmbientCharacterRendererDescriptor,
  V2AmbientRendererAction,
} from "../../lib/v2/ambient-character-renderer";
import styles from "./V2AmbientCharacterSurface.module.css";

export interface V2AmbientCharacterSurfaceProps {
  readonly presentation: V2AmbientCharacterRendererDescriptor;
  readonly children?: ReactNode;
  readonly className?: string;
}

const MODE_CLASS_KEYS: Readonly<Record<"ambient" | "reduced-motion" | "static", string>> =
  Object.freeze({
    ambient: "modeAmbient",
    "reduced-motion": "modeReducedMotion",
    static: "modeStatic",
  });

const PHASE_SLOT_CLASS_KEYS: Readonly<Record<number, string>> = Object.freeze({
  0: "phaseSlot0",
  1: "phaseSlot1",
  2: "phaseSlot2",
  3: "phaseSlot3",
});

const ROOT_ACTION_KEYS = Object.freeze([
  "blink",
  "focus-glow",
  "device-idle",
  "selection-emphasis",
] as const);

type AmbientStyle = CSSProperties & {
  "--amb-blink-cycle"?: string;
  "--amb-breath-cycle"?: string;
  "--amb-posture-cycle"?: string;
  "--amb-drift-cycle"?: string;
  "--amb-device-cycle"?: string;
};

function actionFor(
  actions: readonly V2AmbientRendererAction[],
  key: V2AmbientRendererAction["key"],
): V2AmbientRendererAction | undefined {
  return actions.find((action) => action.key === key);
}

function actionCycleMs(action: V2AmbientRendererAction | undefined): string | undefined {
  if (!action) return undefined;
  return `${Math.max(action.durationMs, action.minIntervalMs)}ms`;
}

function rootActionClasses(actions: readonly V2AmbientRendererAction[]): string[] {
  const classes: string[] = [];
  for (const key of ROOT_ACTION_KEYS) {
    const action = actionFor(actions, key);
    if (action) classes.push(styles[action.cssClass] ?? "");
  }
  return classes.filter(Boolean);
}

function firstDriftAction(
  actions: readonly V2AmbientRendererAction[],
): V2AmbientRendererAction | undefined {
  return actionFor(actions, "prop-idle") ?? actionFor(actions, "gaze-shift");
}

export function V2AmbientCharacterSurface({
  presentation,
  children,
  className,
}: V2AmbientCharacterSurfaceProps) {
  const valid =
    !!presentation &&
    typeof presentation === "object" &&
    presentation.kind === "ambient-character-renderer";

  if (!valid) {
    return <div className={className}>{children}</div>;
  }

  const truth = presentation.truth;
  const breathing = actionFor(presentation.actions, "breathing");
  const posture = actionFor(presentation.actions, "micro-posture");
  const drift = firstDriftAction(presentation.actions);
  const blink = actionFor(presentation.actions, "blink");
  const device = actionFor(presentation.actions, "device-idle");

  const inlineStyle: AmbientStyle = {
    "--amb-blink-cycle": actionCycleMs(blink),
    "--amb-breath-cycle": actionCycleMs(breathing),
    "--amb-posture-cycle": actionCycleMs(posture),
    "--amb-drift-cycle": actionCycleMs(drift),
    "--amb-device-cycle": actionCycleMs(device),
  };

  const rootClassName = [
    styles.root,
    styles[MODE_CLASS_KEYS[presentation.mode]],
    styles[PHASE_SLOT_CLASS_KEYS[presentation.phaseSlot]],
    ...rootActionClasses(presentation.actions),
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClassName}
      style={inlineStyle}
      data-ambient-renderer="true"
      data-ambient-mode={presentation.mode}
      data-phase-slot={String(presentation.phaseSlot)}
      data-ambient-actions={presentation.actions.map((action) => action.key).join(",")}
      data-presentation-only={String(presentation.presentationOnly)}
      data-semantic-animation-active={String(truth.semanticAnimationActive)}
      data-canonical-state-writable={String(truth.canonicalStateWritable)}
      data-physical-presence-claimed={String(truth.physicalPresenceClaimed)}
      data-physical-location-claimed={String(truth.physicalLocationClaimed)}
      data-physical-travel-claimed={String(truth.physicalTravelClaimed)}
      data-conversation-claimed={String(truth.conversationClaimed)}
      data-collaboration-claimed={String(truth.collaborationClaimed)}
      data-work-activity-claimed={String(truth.workActivityClaimed)}
      data-completion-claimed={String(truth.completionClaimed)}
      data-handoff-claimed={String(truth.handoffClaimed)}
      data-blocker-resolution-claimed={String(truth.blockerResolutionClaimed)}
    >
      <div
        className={[
          styles.breathLayer,
          breathing ? styles[breathing.cssClass] : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div
          className={[
            styles.postureLayer,
            posture ? styles[posture.cssClass] : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <div
            className={[
              styles.driftLayer,
              drift ? styles[drift.cssClass] : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

export default V2AmbientCharacterSurface;
