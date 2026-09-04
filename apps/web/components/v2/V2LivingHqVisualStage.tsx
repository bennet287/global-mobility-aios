"use client";

import { useMemo, type CSSProperties, type ReactNode } from "react";

import {
  isKnownWingKey,
  resolveHqVisualStageLayout,
  type HqWingCharacterInput,
  type HqWingKey,
  type HqWingMetricInput,
  type HqWingVisualLayout,
} from "../../lib/v2/hq-visual-presentation";
import { V2CharacterMiniature } from "./V2CharacterMiniature";
import styles from "./V2LivingHqVisualStage.module.css";

export type HqStageCharacter = HqWingCharacterInput;
export type HqStageWingMetric = HqWingMetricInput;

export type V2LivingHqVisualStageProps = {
  readonly organizationLabel?: string;
  readonly missionCount?: number;
  readonly selectedWing?: HqWingKey | null;
  readonly selectedPositionKey?: string | null;
  readonly characters?: readonly HqStageCharacter[];
  readonly wingMetrics?: readonly HqStageWingMetric[];
  readonly loading?: boolean;
  readonly sceneEstablished?: boolean;
  readonly onSelectWing?: (wingKey: HqWingKey) => void;
  readonly onSelectCharacter?: (
    positionKey: string,
    wingKey: HqWingKey,
  ) => void;
};

function describeZone(zone: HqWingVisualLayout): string {
  const parts: string[] = [];

  if (zone.departmentCount > 0) {
    parts.push(
      `${zone.departmentCount} department${zone.departmentCount === 1 ? "" : "s"}`,
    );
  }
  if (zone.employeeCount > 0) {
    parts.push(`${zone.employeeCount} rostered`);
  }
  if (zone.workItemCount > 0) {
    parts.push(`${zone.workItemCount} work items`);
  }
  if (zone.activeBlockerCount > 0) {
    parts.push(
      `${zone.activeBlockerCount} blocker${zone.activeBlockerCount === 1 ? "" : "s"}`,
    );
  }
  if (zone.characters.length > 0) {
    parts.push(
      `${zone.characters.length} character${zone.characters.length === 1 ? "" : "s"}`,
    );
  }

  return parts.length > 0
    ? parts.join(" · ")
    : "Presentation zone · no mapped content";
}

function SelectableSurface({
  interactive,
  active,
  ariaLabel,
  className,
  onSelect,
  children,
}: {
  readonly interactive: boolean;
  readonly active: boolean;
  readonly ariaLabel: string;
  readonly className: string;
  readonly onSelect: () => void;
  readonly children: ReactNode;
}) {
  if (!interactive) {
    return (
      <div aria-label={ariaLabel} className={className} role="group">
        {children}
      </div>
    );
  }

  return (
    <button
      aria-label={ariaLabel}
      aria-pressed={active}
      className={className}
      onClick={onSelect}
      type="button"
    >
      {children}
    </button>
  );
}

function WingPlatform({
  zone,
  active,
  missionCount,
  onSelectWing,
  onSelectCharacter,
  selectedPositionKey,
}: {
  readonly zone: HqWingVisualLayout;
  readonly active: boolean;
  readonly missionCount: number;
  readonly onSelectWing?: (wingKey: HqWingKey) => void;
  readonly onSelectCharacter?: (
    positionKey: string,
    wingKey: HqWingKey,
  ) => void;
  readonly selectedPositionKey: string | null;
}) {
  const classes = [
    styles.wing,
    styles[zone.accentClass],
    styles[zone.scale],
    active ? styles.wingActive : "",
  ]
    .filter(Boolean)
    .join(" ");

  const zoneLabel = `${zone.label}. ${describeZone(zone)}${
    active ? " · currently selected" : ""
  }`;

  const zoneSummary = (
    <>
      <span className={styles.wingHeader}>
        <strong>{zone.shortLabel}</strong>
        {zone.isHub ? (
          <em className={styles.hubBadge}>
            {missionCount > 0
              ? `${missionCount} mission${missionCount === 1 ? "" : "s"}`
              : "Mission Hub"}
          </em>
        ) : null}
      </span>

      <span className={styles.metrics} aria-hidden="true">
        {zone.departmentCount > 0 ? (
          <span className={styles.metric} data-kind="departments">
            {zone.departmentCount}
            <small>dept</small>
          </span>
        ) : null}
        {zone.employeeCount > 0 ? (
          <span className={styles.metric} data-kind="roster">
            {zone.employeeCount}
            <small>rostered</small>
          </span>
        ) : null}
        {zone.activeBlockerCount > 0 ? (
          <span className={styles.metric} data-kind="blockers">
            {zone.activeBlockerCount}
            <small>blockers</small>
          </span>
        ) : null}
      </span>

      {zone.characters.length === 0 ? (
        <span className={styles.emptyZone} aria-hidden="true">
          <span className={styles.emptyGlyph} />
        </span>
      ) : null}

      <span className={styles.srDescription}>{describeZone(zone)}</span>
    </>
  );

  return (
    <article
      className={classes}
      data-elevation={String(zone.elevation)}
      data-wing={zone.wingKey}
      style={{ "--hq-elevation": `${zone.elevation}px` } as CSSProperties}
    >
      <span className={styles.lightPool} aria-hidden="true" />
      <span className={styles.platformSurface} aria-hidden="true" />

      <SelectableSurface
        active={active}
        ariaLabel={zoneLabel}
        className={styles.wingSelector}
        interactive={Boolean(onSelectWing)}
        onSelect={() => onSelectWing?.(zone.wingKey)}
      >
        {zoneSummary}
      </SelectableSurface>

      {zone.characters.length > 0 ? (
        <ul
          aria-label={`${zone.label} character presentations`}
          className={styles.characterAnchorList}
        >
          {zone.characters.map((character) => {
            const selected = selectedPositionKey === character.positionKey;
            const miniature = (
              <V2CharacterMiniature
                department={character.department}
                positionKey={character.positionKey}
                title={character.title}
                variant="compact"
              />
            );

            return (
              <li
                className={`${styles.characterAnchor}${
                  selected ? ` ${styles.characterSelected}` : ""
                }`}
                key={character.positionKey}
              >
                {onSelectCharacter ? (
                  <button
                    aria-label={`${character.title || character.positionKey} · ${
                      character.department
                    }${selected ? " · selected" : ""}`}
                    aria-pressed={selected}
                    className={styles.characterButton}
                    onClick={() =>
                      onSelectCharacter(character.positionKey, zone.wingKey)
                    }
                    type="button"
                  >
                    {miniature}
                  </button>
                ) : (
                  <div className={styles.characterDisplay}>{miniature}</div>
                )}
              </li>
            );
          })}
        </ul>
      ) : null}
    </article>
  );
}

export function V2LivingHqVisualStage({
  organizationLabel = "Living Organization",
  missionCount = 0,
  selectedWing = null,
  selectedPositionKey = null,
  characters,
  wingMetrics,
  loading = false,
  sceneEstablished = false,
  onSelectWing,
  onSelectCharacter,
}: V2LivingHqVisualStageProps) {
  const layout = useMemo(
    () =>
      resolveHqVisualStageLayout({
        metrics: wingMetrics,
        characters,
      }),
    [wingMetrics, characters],
  );

  const activeWing =
    selectedWing !== null && isKnownWingKey(selectedWing) ? selectedWing : null;
  const visibleMissionCount = Number.isFinite(missionCount)
    ? Math.max(0, Math.floor(missionCount))
    : 0;

  if (loading) {
    return (
      <section
        aria-label="Living HQ visual stage"
        className={styles.stageRoot}
        data-canonical-state-writable="false"
        data-physical-location-claimed="false"
        data-presence-claimed="false"
        data-presentation-only="true"
        data-state="loading"
      >
        <div className={styles.loadingState} role="status">
          <span className={styles.loadingOrb} aria-hidden="true" />
          <strong>Preparing headquarters view…</strong>
          <small>Presentation only · no AIOS mutation</small>
        </div>
      </section>
    );
  }

  if (!sceneEstablished) {
    return (
      <section
        aria-label="Living HQ visual stage"
        className={styles.stageRoot}
        data-canonical-state-writable="false"
        data-physical-location-claimed="false"
        data-presence-claimed="false"
        data-presentation-only="true"
        data-state="unestablished"
      >
        <div className={styles.unestablishedState} role="status">
          <strong>No Living Organization scene is established.</strong>
          <small>
            The visual stage will not fabricate departments, missions, employees,
            placement or presence.
          </small>
        </div>
      </section>
    );
  }

  return (
    <section
      aria-label="Living HQ visual stage"
      className={styles.stageRoot}
      data-canonical-state-writable="false"
      data-physical-location-claimed="false"
      data-presence-claimed="false"
      data-presentation-only="true"
      data-state="established"
    >
      <header className={styles.stageHeader}>
        <div>
          <span className={styles.stageEyebrow}>Headquarters</span>
          <h2 className={styles.stageTitle}>{organizationLabel}</h2>
        </div>
        <div className={styles.stageSummary} aria-live="polite">
          <span>
            <strong>{layout.zones.length}</strong>
            <small>wings</small>
          </span>
          <span>
            <strong>{visibleMissionCount}</strong>
            <small>missions</small>
          </span>
          <span>
            <strong>{layout.totalCharacterCount}</strong>
            <small>placed</small>
          </span>
          <span>
            <strong>{layout.totalUnplacedCharacterCount}</strong>
            <small>unplaced</small>
          </span>
          <span>
            <strong>{layout.totalBlockerCount}</strong>
            <small>blockers</small>
          </span>
        </div>
      </header>

      <div className={styles.stageViewport}>
        <div className={styles.stageFloor} aria-hidden="true">
          <span className={styles.floorGrid} />
          <span className={styles.floorGlow} />
          <span className={styles.decisionChamber}>Decision Chamber</span>
          <span className={styles.collaborationDeck}>Collaboration Deck</span>
        </div>

        <div
          aria-label="Architectural presentation zones"
          className={styles.stageScene}
          role="group"
        >
          {layout.zones.map((zone) => (
            <WingPlatform
              active={activeWing === zone.wingKey}
              key={zone.wingKey}
              missionCount={visibleMissionCount}
              onSelectCharacter={onSelectCharacter}
              onSelectWing={onSelectWing}
              selectedPositionKey={selectedPositionKey}
              zone={zone}
            />
          ))}
        </div>
      </div>

      {layout.unplacedCharacters.length > 0 ? (
        <aside className={styles.unplacedTray} aria-label="Unplaced presentations">
          <div>
            <strong>
              {layout.totalUnplacedCharacterCount} unplaced presentation
              {layout.totalUnplacedCharacterCount === 1 ? "" : "s"}
            </strong>
            <small>
              No presentation wing was supplied. AIOS does not infer one from title,
              authority or department.
            </small>
          </div>
          <ul>
            {layout.unplacedCharacters.map((character) => (
              <li key={character.positionKey}>
                <strong>{character.title || character.positionKey}</strong>
                <small>{character.department || "Department unavailable"}</small>
              </li>
            ))}
          </ul>
        </aside>
      ) : null}

      <footer className={styles.stageFooter}>
        <span className={styles.truthBadge}>
          <span className={styles.truthDot} aria-hidden="true" />
          Presentation only · no physical location claimed
        </span>
        <span className={styles.truthBadge}>
          <span className={styles.truthDot} aria-hidden="true" />
          Presence not claimed · no canonical state written
        </span>
        <span className={styles.truthBadge}>
          <span className={styles.truthDot} aria-hidden="true" />
          Wings supplied by governed presentation assignment
        </span>
      </footer>
    </section>
  );
}
