"use client";

import { useMemo, useState } from "react";

import type { LivingSceneEmployee } from "../../lib/live-organization";
import {
  buildV2HqCharacterLayout,
  getV2HqPlacementsForWing,
} from "../../lib/v2/hq-character-layout";
import type {
  V2ArchitectureWingKey,
  V2OrganizationOverview,
} from "../../lib/v2/owner-organization";
import { V2CharacterMiniature } from "./V2CharacterMiniature";
import styles from "./V2OrganizationBlockout.module.css";

const WING_ORDER: V2ArchitectureWingKey[] = [
  "executive",
  "regulatory",
  "atrium",
  "technology",
  "operations",
];

const EMPTY_EMPLOYEES: readonly LivingSceneEmployee[] = Object.freeze([]);

export function V2OrganizationBlockout({
  organization,
  loading,
  compact = false,
  employees = EMPTY_EMPLOYEES,
  selectedPositionKey = null,
  onSelectEmployee,
}: {
  organization: V2OrganizationOverview | null;
  loading: boolean;
  compact?: boolean;
  employees?: readonly LivingSceneEmployee[];
  selectedPositionKey?: string | null;
  onSelectEmployee?: (positionKey: string) => void;
}) {
  const [selectedWing, setSelectedWing] = useState<V2ArchitectureWingKey>("atrium");

  const zones = organization?.zones || [];
  const selected = useMemo(
    () => zones.find((zone) => zone.wingKey === selectedWing) || zones[0] || null,
    [selectedWing, zones],
  );

  const characterLayout = useMemo(
    () => buildV2HqCharacterLayout(employees, zones),
    [employees, zones],
  );

  const selectedPlacements = useMemo(
    () =>
      selected
        ? getV2HqPlacementsForWing(characterLayout, selected.wingKey)
        : [],
    [characterLayout, selected],
  );

  const headingId = compact ? "aios-v2-hq-preview-title" : "aios-v2-hq-title";

  return (
    <section
      className={"aios-v2-hq-blockout" + (compact ? " compact" : "")}
      aria-labelledby={headingId}
      data-scene-authoritative={String(organization?.sceneAuthoritative ?? false)}
      data-renderer-authoritative={String(organization?.rendererAuthoritative ?? false)}
      data-mutations-allowed={String(organization?.mutationsAllowed ?? false)}
      data-physical-location-claimed="false"
      data-presence-claimed="false"
    >
      <header className="aios-v2-hq-header">
        <div>
          <span>Living Organization</span>
          <strong id={headingId}>Architectural organization blockout</strong>
        </div>
        <small>Department-mapped presentation anchors · location and presence not claimed</small>
      </header>

      {loading ? (
        <div className="aios-v2-hq-loading" role="status">Loading governed Living Organization scene…</div>
      ) : !organization?.established ? (
        <div className="aios-v2-hq-loading" role="status">
          No Living Organization scene is established. The V2 renderer will not fabricate departments, Missions, employees or presence.
        </div>
      ) : (
        <>
          <div className="aios-v2-hq-canvas" data-presentation-topology="aios-v2-office-bible.v1">
            {WING_ORDER.map((wingKey) => {
              const zone = zones.find((candidate) => candidate.wingKey === wingKey);
              if (!zone) return null;
              const active = selected?.wingKey === wingKey;
              const wingPlacements = getV2HqPlacementsForWing(characterLayout, wingKey);
              return (
                <button
                  aria-pressed={active}
                  className={"aios-v2-hq-zone zone-" + wingKey}
                  data-active={String(active)}
                  data-physical-location-claimed="false"
                  key={wingKey}
                  onClick={() => setSelectedWing(wingKey)}
                  type="button"
                >
                  <span>{zone.label}</span>
                  <strong>{zone.departments.length || "—"}</strong>
                  <small>{zone.departments.length ? "mapped departments" : "presentation zone"}</small>

                  {wingPlacements.length ? (
                    <div
                      aria-hidden="true"
                      className={styles.zoneCharacters}
                      data-presentation-placement="department-zone-map"
                    >
                      {wingPlacements.slice(0, 4).map((placement) => (
                        <V2CharacterMiniature
                          department={placement.department}
                          key={placement.positionKey}
                          positionKey={placement.positionKey}
                          title={placement.title}
                        />
                      ))}
                      {wingPlacements.length > 4 ? (
                        <b>+{wingPlacements.length - 4}</b>
                      ) : null}
                    </div>
                  ) : null}

                  {zone.activeBlockerCount > 0 ? (
                    <em>{zone.activeBlockerCount} blocker{zone.activeBlockerCount === 1 ? "" : "s"}</em>
                  ) : null}
                </button>
              );
            })}

            <div className="aios-v2-hq-mission-hub" aria-label="Mission Hub">
              <span>Mission Hub</span>
              <strong>{organization.missionCount}</strong>
              <small>projected Missions</small>
            </div>
          </div>

          <div className="aios-v2-hq-inspector" aria-live="polite">
            <div>
              <span>View focus</span>
              <strong>{selected?.label || "Organization"}</strong>
            </div>
            {selected ? (
              <>
                <p>
                  {selected.departments.length
                    ? selected.departments.map((department) => department.label).join(" · ")
                    : "No canonical department is mapped to this presentation zone."}
                </p>
                <div className="aios-v2-hq-inspector-metrics">
                  <span><strong>{selected.employeeRosterCount}</strong> rostered positions</span>
                  <span><strong>{selected.workItemCount}</strong> work items</span>
                  <span><strong>{selected.activeBlockerCount}</strong> blockers</span>
                </div>
              </>
            ) : null}

            {selectedPlacements.length ? (
              <div className={styles.roster} aria-label={(selected?.label || "Selected wing") + " roster presentations"}>
                <header className={styles.rosterHeader}>
                  <span>Roster presentation</span>
                  <small>Department mapped · physical location not claimed</small>
                </header>
                <div className={styles.rosterList}>
                  {selectedPlacements.map((placement) => {
                    const active = selectedPositionKey === placement.positionKey;
                    const body = (
                      <>
                        <V2CharacterMiniature
                          department={placement.department}
                          positionKey={placement.positionKey}
                          title={placement.title}
                        />
                        <span className={styles.rosterCopy}>
                          <strong>{placement.title}</strong>
                          <small>{placement.department} · {placement.semanticState.replaceAll("_", " ")}</small>
                          <em>Rostered presentation · presence not claimed</em>
                        </span>
                      </>
                    );

                    return onSelectEmployee ? (
                      <button
                        aria-pressed={active}
                        className={styles.rosterPerson}
                        data-selected={String(active)}
                        key={placement.positionKey}
                        onClick={() => onSelectEmployee(placement.positionKey)}
                        type="button"
                      >
                        {body}
                      </button>
                    ) : (
                      <div className={styles.rosterPerson} key={placement.positionKey}>
                        {body}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : selected ? (
              <div className={styles.rosterEmpty}>
                No rostered employee has a unique canonical department mapping to this presentation wing.
              </div>
            ) : null}
          </div>

          {characterLayout.unplaced.length ? (
            <div className={styles.unplaced} role="status">
              <strong>{characterLayout.unplaced.length}</strong>
              <span>
                rostered employee{characterLayout.unplaced.length === 1 ? "" : "s"} remain spatially unplaced because no unique canonical department-to-zone mapping was available.
              </span>
            </div>
          ) : null}
        </>
      )}

      <footer className="aios-v2-hq-truth">
        <span>Scene authority: {organization?.sceneAuthoritative ? "authoritative" : "non-authoritative"}</span>
        <span>Renderer authority: {organization?.rendererAuthoritative ? "authoritative" : "none"}</span>
        <span>Mutation: {organization?.mutationsAllowed ? "allowed" : "disabled"}</span>
        <span>Physical location: not claimed</span>
        <span>Presence: not claimed</span>
      </footer>
    </section>
  );
}
