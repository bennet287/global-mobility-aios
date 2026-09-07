import {
  buildV2VisibleHandoffVisualization,
  type V2VisibleHandoffModel,
} from "../../lib/v2/visible-handoff";
import { V2CharacterArtPrototype } from "./V2CharacterArtPrototype";
import styles from "./V2CanonicalHandoffSignal.module.css";

export type V2CanonicalHandoffSignalProps = {
  readonly model: V2VisibleHandoffModel | null;
  readonly reducedMotion: boolean;
  readonly variant: "spatial" | "structured";
};

function endpointLabel(
  endpoint: V2VisibleHandoffModel["sender"] | V2VisibleHandoffModel["receiver"],
  fallbackPositionKey: string,
): string {
  return endpoint?.title?.trim() || fallbackPositionKey;
}

function occurredAtLabel(value: string): string {
  return value.replace("T", " ").replace(/Z$/, " UTC");
}

export function V2CanonicalHandoffSignal({
  model,
  reducedMotion,
  variant,
}: V2CanonicalHandoffSignalProps) {
  if (!model) return null;

  const visualization = buildV2VisibleHandoffVisualization(
    model,
    variant === "structured" ? true : reducedMotion,
  );
  const semanticVisualization = visualization?.supported === true ? visualization : null;
  const semanticSupported = semanticVisualization !== null;

  // Spatial semantic treatment is allowed only when the sealed Phase 2E/2O
  // descriptors support this exact canonical event. Structured UI keeps the
  // canonical relation readable even when character treatment is unsupported.
  if (variant === "spatial" && !semanticSupported) return null;

  const senderLabel = endpointLabel(
    model.sender,
    model.canonicalHandoff.previous_position_key,
  );
  const receiverLabel = endpointLabel(
    model.receiver,
    model.canonicalHandoff.assigned_position_key,
  );
  const visualizationMode = semanticVisualization?.mode ?? "unsupported";
  const signalClassName = `${styles.signal} ${
    variant === "spatial" ? styles.spatial : styles.structured
  }`;

  return (
    <section
      aria-label={`Recorded canonical handoff from ${senderLabel} to ${receiverLabel}`}
      className={signalClassName}
      data-aios-v2-handoff-signal={variant}
      data-canonical-event="true"
      data-canonical-state-writable="false"
      data-handoff-activity-id={model.canonicalHandoff.activity_id}
      data-handoff-coverage={model.truth.canonicalCoverageState}
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-physical-travel-claimed="false"
      data-presentation-only="true"
      data-semantic-animation-supported={semanticSupported ? "true" : "false"}
      data-visualization-mode={visualizationMode}
    >
      <header className={styles.header}>
        <span className={styles.eyebrow}>Recorded canonical handoff</span>
        <strong>{senderLabel} → {receiverLabel}</strong>
      </header>

      <div
        aria-label={`Assignment direction from ${senderLabel} to ${receiverLabel}`}
        className={styles.flow}
        data-visualization-mode={visualizationMode}
      >
        <div className={styles.endpoint} data-handoff-role="sender">
          <span aria-hidden="true" className={styles.endpointMarker} />
          {semanticVisualization && semanticVisualization.senderPresentationKey !== "unresolved" ? (
            <span aria-hidden="true" className={styles.avatar}>
              <V2CharacterArtPrototype
                presentationKey={semanticVisualization.senderPresentationKey}
                variant="compact"
              />
            </span>
          ) : null}
          <span className={styles.endpointText}>
            <small>From</small>
            <strong>{senderLabel}</strong>
            <small>{model.canonicalHandoff.previous_position_key}</small>
          </span>
        </div>

        <div className={styles.relation}>
          <div aria-hidden="true" className={styles.track}>
            <span className={styles.trackLine} />
            <span className={styles.traveler} />
          </div>
          <div className={styles.workObject} data-handoff-role="work-object">
            <small>Assignment event</small>
            <strong>{model.canonicalHandoff.status}</strong>
            <span>{variant === "structured"
              ? `Work item ${model.canonicalHandoff.work_item_id}`
              : "Canonical work relation"}</span>
          </div>
        </div>

        <div className={styles.endpoint} data-handoff-role="receiver">
          <span aria-hidden="true" className={styles.endpointMarker} />
          {semanticVisualization && semanticVisualization.receiverPresentationKey !== "unresolved" ? (
            <span aria-hidden="true" className={styles.avatar}>
              <V2CharacterArtPrototype
                presentationKey={semanticVisualization.receiverPresentationKey}
                variant="compact"
              />
            </span>
          ) : null}
          <span className={styles.endpointText}>
            <small>To</small>
            <strong>{receiverLabel}</strong>
            <small>{model.canonicalHandoff.assigned_position_key}</small>
          </span>
        </div>
      </div>

      <div className={styles.meta}>
        <span>Activity · {model.canonicalHandoff.activity_id}</span>
        <time dateTime={model.canonicalHandoff.occurred_at}>
          {occurredAtLabel(model.canonicalHandoff.occurred_at)}
        </time>
      </div>

      <details className={styles.provenance}>
        <summary>Canonical provenance</summary>
        <dl>
          <div>
            <dt>Work item</dt>
            <dd>{model.canonicalHandoff.work_item_id}</dd>
          </div>
          <div>
            <dt>Coverage</dt>
            <dd>{model.truth.canonicalCoverageState}</dd>
          </div>
          <div>
            <dt>Canonical basis</dt>
            <dd>{model.canonicalHandoff.canonical_basis}</dd>
          </div>
        </dl>
      </details>

      <p className={styles.truth}>
        Canonical event · presentation relation only · no physical travel,
        presence, conversation, completion or canonical mutation is claimed.
      </p>

      {variant === "structured" && !semanticSupported ? (
        <p className={styles.limitation}>
          Character semantic treatment is unavailable for this recorded event;
          the canonical sender-to-receiver relation remains readable here.
        </p>
      ) : null}
    </section>
  );
}
