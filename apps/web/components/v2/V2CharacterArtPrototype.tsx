"use client";

import { useId } from "react";

import {
  CHARACTER_ART_ACCENT_PALETTE,
  resolveCharacterArtPrototype,
  type CharacterArtAccentToken,
  type CharacterArtPrototypeModel,
} from "../../lib/v2/character-art-prototype";

import styles from "./V2CharacterArtPrototype.module.css";

export type V2CharacterArtPrototypeVariant = "compact" | "inspector";

export type V2CharacterArtPrototypeProps = {
  readonly presentationKey: string;
  readonly variant?: V2CharacterArtPrototypeVariant;
  readonly labelledBy?: string;
};

function accentColors(token: CharacterArtAccentToken) {
  return CHARACTER_ART_ACCENT_PALETTE[token] ?? CHARACTER_ART_ACCENT_PALETTE.silver;
}

function JacketShape({
  model,
  jacketFill,
  surfaceFill,
}: {
  model: CharacterArtPrototypeModel;
  jacketFill: string;
  surfaceFill: string;
}) {
  const accent = accentColors(model.accent);

  switch (model.archetype) {
    case "ceo":
      return (
        <g>
          <path d="M26 82 Q28 74 42 73 H78 Q92 74 94 82 L98 142 Q96 153 84 154 H36 Q24 153 22 142 Z" fill={jacketFill} stroke={accent.soft} />
          <path d="M48 74 L42 96 L52 101 L60 82 L68 101 L78 96 L72 74" fill="#171c26" stroke={accent.primary} />
          <path d="M27 88 Q20 106 24 128" stroke="#171c26" strokeWidth="12" strokeLinecap="round" fill="none" />
          <path d="M93 88 Q100 106 96 128" stroke="#171c26" strokeWidth="12" strokeLinecap="round" fill="none" />
          <circle cx="24" cy="130" r="5" fill={surfaceFill} />
          <circle cx="96" cy="130" r="5" fill={surfaceFill} />
        </g>
      );
    case "cto":
      return (
        <g>
          <path d="M30 82 Q32 75 44 73 H76 Q88 75 90 82 L94 142 Q92 151 82 152 H38 Q28 151 26 142 Z" fill={jacketFill} stroke={accent.soft} />
          <path d="M43 74 L39 111 L59 119 L81 109 L77 74" fill="none" stroke={accent.primary} strokeDasharray="3 3" />
          <path d="M49 74 L45 86 L60 90 L75 85 L71 74" fill="#171c26" stroke={accent.primary} />
          <path d="M31 88 Q25 105 28 124" stroke="#171c26" strokeWidth="10" strokeLinecap="round" fill="none" />
          <path d="M89 88 Q95 105 92 124" stroke="#171c26" strokeWidth="10" strokeLinecap="round" fill="none" />
          <circle cx="28" cy="126" r="4.5" fill={surfaceFill} />
          <circle cx="92" cy="126" r="4.5" fill={surfaceFill} />
        </g>
      );
    case "regulatory-compliance":
      return (
        <g>
          <path d="M34 82 Q36 76 46 75 H74 Q84 76 86 82 L89 140 Q87 150 78 151 H42 Q33 150 31 140 Z" fill={jacketFill} stroke={accent.soft} />
          <path d="M52 76 L48 91 L60 97 L72 91 L68 76" fill="#1b202b" stroke={accent.primary} />
          <path d="M34 89 Q29 106 32 125" stroke="#1b202b" strokeWidth="11" strokeLinecap="round" fill="none" />
          <path d="M86 89 Q91 106 88 125" stroke="#1b202b" strokeWidth="11" strokeLinecap="round" fill="none" />
          <circle cx="32" cy="127" r="4.5" fill={surfaceFill} />
          <circle cx="88" cy="127" r="4.5" fill={surfaceFill} />
        </g>
      );
    case "operations":
      return (
        <g>
          <path d="M31 82 Q33 76 44 75 H76 Q87 76 89 82 L92 141 Q90 150 80 151 H40 Q30 150 28 141 Z" fill={jacketFill} stroke={accent.soft} />
          <path d="M52 76 L48 89 L60 94 L72 89 L68 76" fill="#1b202b" stroke={accent.primary} />
          <path d="M31 89 Q25 105 30 121" stroke="#1b202b" strokeWidth="11" strokeLinecap="round" fill="none" />
          <path d="M89 89 Q95 105 90 121" stroke="#1b202b" strokeWidth="11" strokeLinecap="round" fill="none" />
          <line x1="25" y1="117" x2="35" y2="115" stroke={accent.primary} strokeWidth="2" />
          <line x1="95" y1="117" x2="85" y2="115" stroke={accent.primary} strokeWidth="2" />
          <circle cx="30" cy="123" r="4.5" fill={surfaceFill} />
          <circle cx="90" cy="123" r="4.5" fill={surfaceFill} />
        </g>
      );
    default:
      return (
        <g>
          <path d="M36 82 Q38 77 46 76 H74 Q82 77 84 82 L87 140 Q85 149 76 150 H44 Q35 149 33 140 Z" fill={jacketFill} stroke="rgba(136,150,171,0.18)" />
          <path d="M54 77 L52 87 L60 90 L68 87 L66 77" fill="#1b202b" />
          <path d="M36 89 Q31 106 34 125" stroke="#1b202b" strokeWidth="10" strokeLinecap="round" fill="none" />
          <path d="M84 89 Q89 106 86 125" stroke="#1b202b" strokeWidth="10" strokeLinecap="round" fill="none" />
          <circle cx="34" cy="127" r="4.5" fill={surfaceFill} />
          <circle cx="86" cy="127" r="4.5" fill={surfaceFill} />
        </g>
      );
  }
}

function HeadShape({ archetype, surfaceFill }: { archetype: CharacterArtPrototypeModel["archetype"]; surfaceFill: string }) {
  if (archetype === "regulatory-compliance") return <ellipse cx="60" cy="50" rx="22" ry="24" fill={surfaceFill} />;
  if (archetype === "neutral-professional") return <ellipse cx="60" cy="50" rx="21" ry="23" fill={surfaceFill} />;
  const path = archetype === "ceo"
    ? "M36 56 Q36 28 60 24 Q84 28 84 56 Q84 70 72 74 H48 Q36 70 36 56 Z"
    : archetype === "cto"
      ? "M38 56 Q38 30 60 26 Q82 30 82 56 Q82 68 74 72 H46 Q38 68 38 56 Z"
      : "M38 52 Q38 28 60 26 Q82 28 82 52 Q82 68 72 72 H48 Q38 68 38 52 Z";
  return <path d={path} fill={surfaceFill} />;
}

function HairShape({ model }: { model: CharacterArtPrototypeModel }) {
  const accent = accentColors(model.accent);
  switch (model.archetype) {
    case "ceo":
      return <g><path d="M36 44 Q36 20 60 18 Q84 20 84 44 L82 36 Q78 24 60 22 Q42 24 38 36 Z" fill="#352f2c" /><line x1="48" y1="22" x2="42" y2="38" stroke="#211c1a" /></g>;
    case "cto":
      return <g><path d="M38 42 Q38 22 60 20 Q82 22 82 42 L80 34 L78 26 L60 22 L42 26 L40 34 Z" fill="#2e3240" /><line x1="68" y1="24" x2="72" y2="36" stroke={accent.primary} opacity="0.45" /></g>;
    case "regulatory-compliance":
      return <path d="M40 44 Q40 24 60 22 Q80 24 80 44 L78 36 Q74 26 60 24 Q46 26 42 36 Z" fill="#3b3531" />;
    case "operations":
      return <path d="M40 44 Q40 26 60 24 Q80 26 80 44 L78 38 Q76 28 60 26 Q44 28 42 38 Z" fill="#35312d" />;
    default:
      return <path d="M42 44 Q42 28 60 26 Q78 28 78 44 L76 38 Q74 30 60 28 Q46 30 44 38 Z" fill="#3e3e42" />;
  }
}

function PropShape({ model, compact }: { model: CharacterArtPrototypeModel; compact: boolean }) {
  const accent = accentColors(model.accent);
  switch (model.archetype) {
    case "ceo":
      return <g className={styles.propIdle}><rect x="86" y="100" width="16" height="22" rx="2" fill="#151a24" stroke={accent.primary} />{!compact ? <line x1="90" y1="107" x2="98" y2="107" stroke={accent.primary} opacity="0.55" /> : null}</g>;
    case "cto":
      return <g transform="rotate(-8 92 110)"><g className={styles.propIdle}><rect x="84" y="99" width="18" height="16" rx="2" fill="#121722" stroke={accent.primary} />{!compact ? <path d="M88 110 V104 M92 110 V106 M96 110 V102" stroke={accent.primary} /> : null}</g></g>;
    case "regulatory-compliance":
      return <g className={styles.propIdle}><rect x="22" y="106" width="14" height="18" rx="1" fill="#e8e3d8" stroke={accent.primary} />{!compact ? <path d="M25 112 H33 M25 116 H31 M25 120 H33" stroke={accent.primary} opacity="0.55" /> : null}</g>;
    case "operations":
      return <g className={styles.propIdle}><rect x="84" y="108" width="12" height="14" rx="2" fill="#151a24" stroke={accent.primary} />{!compact ? <circle cx="90" cy="115" r="2.5" fill="none" stroke={accent.primary} /> : null}</g>;
    default:
      return null;
  }
}

function mouthPathFor(archetype: CharacterArtPrototypeModel["archetype"]): string {
  if (archetype === "ceo") return "M54 60 Q60 62 66 60";
  if (archetype === "cto") return "M54 60 H66";
  if (archetype === "regulatory-compliance") return "M55 60 Q60 61 65 60";
  if (archetype === "operations") return "M54 59 Q60 63 66 59";
  return "M55 60 H65";
}

function CharacterSvg({ model, variant }: { model: CharacterArtPrototypeModel; variant: V2CharacterArtPrototypeVariant }) {
  const inspector = variant === "inspector";
  const accent = accentColors(model.accent);
  const paintIdSeed = useId().replaceAll(":", "");
  const plinthId = `cap-plinth-${paintIdSeed}`;
  const jacketId = `cap-jacket-${paintIdSeed}`;
  const surfaceId = `cap-surface-${paintIdSeed}`;
  const jacketFill = `url(#${jacketId})`;
  const surfaceFill = `url(#${surfaceId})`;

  return (
    <svg viewBox="0 0 120 180" className={styles.characterSvg} aria-hidden="true" focusable="false">
      <defs>
        <radialGradient id={plinthId}><stop offset="0%" stopColor="rgba(0,0,0,0.34)" /><stop offset="100%" stopColor="rgba(0,0,0,0)" /></radialGradient>
        <linearGradient id={jacketId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2a2f3d" /><stop offset="100%" stopColor="#171c26" /></linearGradient>
        <linearGradient id={surfaceId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#d4c7b7" /><stop offset="100%" stopColor="#b9a996" /></linearGradient>
      </defs>
      <ellipse cx="60" cy="170" rx="34" ry="6" fill={`url(#${plinthId})`} />
      <JacketShape model={model} jacketFill={jacketFill} surfaceFill={surfaceFill} />
      <rect x="52" y="68" width="16" height="10" rx="4" fill={surfaceFill} />
      <HeadShape archetype={model.archetype} surfaceFill={surfaceFill} />
      <HairShape model={model} />
      {inspector ? (
        <>
          <g className={styles.eyeGroup}><ellipse cx="50" cy="50" rx="2.4" ry="2.8" fill="#2a2f3d" /><ellipse cx="70" cy="50" rx="2.4" ry="2.8" fill="#2a2f3d" /><circle cx="50.8" cy="49.2" r="0.8" fill="#fff" opacity="0.7" /><circle cx="70.8" cy="49.2" r="0.8" fill="#fff" opacity="0.7" /></g>
          <path d={mouthPathFor(model.archetype)} stroke="#8f8172" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          <circle cx="45" cy="95" r="2.2" fill={accent.primary} opacity="0.9" />
        </>
      ) : <g><circle cx="50" cy="50" r="1.8" fill="#2a2f3d" /><circle cx="70" cy="50" r="1.8" fill="#2a2f3d" /></g>}
      {inspector || model.prop !== "none" ? <PropShape model={model} compact={!inspector} /> : null}
    </svg>
  );
}

export function V2CharacterArtPrototype({ presentationKey, variant = "compact", labelledBy }: V2CharacterArtPrototypeProps) {
  const model = resolveCharacterArtPrototype({ presentationKey });
  const variantClass = variant === "inspector" ? styles.inspector : styles.compact;
  const archetypeClass = styles[`archetype-${model.archetype}`] ?? "";
  const accentClass = styles[`accent-${model.accent}`] ?? "";

  return (
    <figure
      className={`${styles.root} ${variantClass} ${archetypeClass} ${accentClass}`}
      data-archetype={model.archetype}
      data-silhouette={model.silhouette}
      data-wardrobe={model.wardrobe}
      data-accent={model.accent}
      data-prop={model.prop}
      data-presentation-key={model.presentationKey}
      data-presentation-only="true"
      data-physical-presence-claimed="false"
      data-physical-location-claimed="false"
      data-canonical-state-writable="false"
      data-semantic-animation-active="false"
      aria-label={labelledBy ? undefined : model.accessibilityDescription}
      aria-labelledby={labelledBy}
      role="img"
    >
      <div className={styles.figureStage}><CharacterSvg model={model} variant={variant} /></div>
      {variant === "inspector" ? (
        <figcaption className={styles.caption}>
          <strong>{model.archetype.replaceAll("-", " ")}</strong>
          <span>{model.silhouette.replaceAll("-", " ")} · {model.wardrobe.replaceAll("-", " ")}</span>
          <em>presentation only · semantic motion inactive</em>
        </figcaption>
      ) : null}
    </figure>
  );
}
