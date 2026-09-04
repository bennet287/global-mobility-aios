import type {
  V2HqAtmosphereAccentClass,
  V2HqAtmosphereContrastClass,
  V2HqAtmosphereDecorativeField,
  V2HqAtmosphereDepthClass,
  V2HqAtmosphereFloorGlowClass,
  V2HqAtmosphereGlassClass,
  V2HqAtmosphereIlluminationClass,
  V2HqAtmosphereIntensity,
  V2HqAtmospherePresentationDescriptor,
  V2HqAtmosphereTheme,
  V2HqAtmosphereZone,
} from "../../lib/v2/hq-atmosphere-presentation";
import styles from "./V2HqAtmosphereLayer.module.css";

export interface V2HqAtmosphereLayerProps {
  readonly presentation: V2HqAtmospherePresentationDescriptor;
  readonly className?: string;
}

const THEME_CLASS_KEYS: Readonly<Record<V2HqAtmosphereTheme, string>> = Object.freeze({
  neutral: "themeNeutral",
  focused: "themeFocused",
  "low-stimulation": "themeLowStimulation",
  presentation: "themePresentation",
});

const DEPTH_CLASS_KEYS: Readonly<Record<V2HqAtmosphereDepthClass, string>> = Object.freeze({
  "depth-architectural-balanced": "depthArchitecturalBalanced",
  "depth-architectural-defined": "depthArchitecturalDefined",
  "depth-architectural-flat": "depthArchitecturalFlat",
  "depth-architectural-layered": "depthArchitecturalLayered",
});

const ILLUMINATION_CLASS_KEYS: Readonly<Record<V2HqAtmosphereIlluminationClass, string>> =
  Object.freeze({
    "illumination-ambient-soft": "illuminationAmbientSoft",
    "illumination-directional-soft": "illuminationDirectionalSoft",
    "illumination-dim-even": "illuminationDimEven",
    "illumination-presentation-soft": "illuminationPresentationSoft",
  });

const CONTRAST_CLASS_KEYS: Readonly<Record<V2HqAtmosphereContrastClass, string>> = Object.freeze({
  "contrast-balanced": "contrastBalanced",
  "contrast-elevated": "contrastElevated",
  "contrast-reduced": "contrastReduced",
  "contrast-refined-elevated": "contrastRefinedElevated",
});

const GLASS_CLASS_KEYS: Readonly<Record<V2HqAtmosphereGlassClass, string>> = Object.freeze({
  "glass-subtle": "glassSubtle",
  "glass-defined": "glassDefined",
  "glass-minimal": "glassMinimal",
  "glass-polished": "glassPolished",
});

const FLOOR_GLOW_CLASS_KEYS: Readonly<Record<V2HqAtmosphereFloorGlowClass, string>> = Object.freeze({
  "floor-glow-even": "floorGlowEven",
  "floor-glow-focused": "floorGlowFocused",
  "floor-glow-muted": "floorGlowMuted",
  "floor-glow-presentation-even": "floorGlowPresentationEven",
});

const ZONE_CLASS_KEYS: Readonly<Record<V2HqAtmosphereZone, string>> = Object.freeze({
  executive: "zoneExecutive",
  regulatory: "zoneRegulatory",
  atrium: "zoneAtrium",
  technology: "zoneTechnology",
  operations: "zoneOperations",
});

const DECORATIVE_FIELD_CLASS_KEYS: Readonly<Record<V2HqAtmosphereDecorativeField, string>> =
  Object.freeze({
    "decision-chamber": "fieldDecisionChamber",
    "collaboration-deck": "fieldCollaborationDeck",
  });

const ACCENT_CLASS_KEYS: Readonly<Record<V2HqAtmosphereAccentClass, string>> = Object.freeze({
  "accent-warm-neutral": "accentWarmNeutral",
  "accent-cool-teal": "accentCoolTeal",
  "accent-cool-metallic": "accentCoolMetallic",
  "accent-warm-practical": "accentWarmPractical",
  "accent-balanced-central": "accentBalancedCentral",
  "accent-formal-contrast": "accentFormalContrast",
  "accent-soft-shared": "accentSoftShared",
});

const INTENSITY_CLASS_KEYS: Readonly<Record<V2HqAtmosphereIntensity, string>> = Object.freeze({
  low: "intensityLow",
  medium: "intensityMedium",
  high: "intensityHigh",
});

function motionClassFor(mode: "transition-only" | "opacity-only" | "static"): string {
  if (mode === "opacity-only") return styles.motionOpacityOnly;
  if (mode === "static") return styles.motionStatic;
  return styles.motionTransitionOnly;
}

export function V2HqAtmosphereLayer({
  presentation,
  className,
}: V2HqAtmosphereLayerProps) {
  if (
    !presentation ||
    typeof presentation !== "object" ||
    presentation.kind !== "hq-atmosphere-presentation"
  ) {
    return null;
  }

  const truth = presentation.truth;
  const rootClassName = [
    styles.root,
    styles[THEME_CLASS_KEYS[presentation.theme]],
    styles[DEPTH_CLASS_KEYS[presentation.environment.depthClass]],
    styles[ILLUMINATION_CLASS_KEYS[presentation.environment.illuminationClass]],
    styles[CONTRAST_CLASS_KEYS[presentation.environment.contrastClass]],
    styles[GLASS_CLASS_KEYS[presentation.environment.glassClass]],
    styles[FLOOR_GLOW_CLASS_KEYS[presentation.environment.floorGlowClass]],
    motionClassFor(presentation.motion.mode),
    presentation.reducedMotion.enabled ? styles.reducedMotionActive : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      aria-hidden="true"
      className={rootClassName}
      data-atmosphere-theme={presentation.theme}
      data-canonical-state-writable={String(truth.canonicalStateWritable)}
      data-collaboration-claimed={String(truth.collaborationClaimed)}
      data-conversation-claimed={String(truth.conversationClaimed)}
      data-physical-location-claimed={String(truth.physicalLocationClaimed)}
      data-physical-presence-claimed={String(truth.physicalPresenceClaimed)}
      data-presentation-only={String(presentation.presentationOnly)}
      data-reduced-motion={presentation.reducedMotion.enabled ? "true" : "false"}
      data-selected-zone={presentation.selectedZone ?? "none"}
      data-semantic-animation-active={String(truth.semanticAnimationActive)}
      data-urgency-claimed={String(truth.urgencyClaimed)}
      data-work-activity-claimed={String(truth.workActivityClaimed)}
    >
      <div className={styles.depthHaze} />
      <div className={styles.ambientField} />
      {presentation.zones.map((zone) => (
        <div
          className={[
            styles.zoneGlow,
            styles[ZONE_CLASS_KEYS[zone.zone]],
            styles[ACCENT_CLASS_KEYS[zone.accent]],
            styles[INTENSITY_CLASS_KEYS[zone.intensity]],
            zone.selected ? styles.zoneGlowSelected : "",
          ]
            .filter(Boolean)
            .join(" ")}
          data-selected={zone.selected ? "true" : "false"}
          data-zone={zone.zone}
          key={zone.zone}
        />
      ))}
      {presentation.decorativeFields.map((field) => (
        <div
          className={[
            styles.decorativeField,
            styles[DECORATIVE_FIELD_CLASS_KEYS[field.field]],
            styles[ACCENT_CLASS_KEYS[field.accent]],
            styles[INTENSITY_CLASS_KEYS[field.intensity]],
          ]
            .filter(Boolean)
            .join(" ")}
          data-field={field.field}
          data-selection-eligible="false"
          key={field.field}
        />
      ))}
      <div className={styles.atriumCore} />
      <div className={styles.glassReflection} />
      <div className={styles.floorEdge} />
      <div className={styles.vignette} />
    </div>
  );
}

export default V2HqAtmosphereLayer;
