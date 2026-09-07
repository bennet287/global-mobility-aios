"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2MissionRoomInspector } from "../../hooks/useV2MissionRoomInspector";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import { buildV2HqCharacterLayout } from "../../lib/v2/hq-character-layout";
import type {
  HqWingCharacterInput,
  HqWingKey,
  HqWingMetricInput,
} from "../../lib/v2/hq-visual-presentation";
import { buildLatestV2VisibleHandoff } from "../../lib/v2/visible-handoff";
import { V2CanonicalHandoffSignal } from "./V2CanonicalHandoffSignal";
import { V2EmployeeInspector } from "./V2EmployeeInspector";
import { V2LivingHqVisualStage } from "./V2LivingHqVisualStage";
import { V2MissionRoomPanel } from "./V2MissionRoomPanel";
import { V2MissionStrip } from "./V2MissionStrip";
import styles from "./V2OrganizationWorkspace.module.css";
import { V2Shell } from "./V2Shell";

type OrganizationRepresentation = "spatial" | "structured";

export function V2OrganizationWorkspace() {
  const router = useRouter();
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const {
    loading: roomLoading,
    error: roomError,
    employees: sceneEmployees,
    handoffs: sceneHandoffs,
    handoffCoverage,
    refresh: refreshRoom,
    missionRoomFor,
    employeeInspectorFor,
  } = useV2MissionRoomInspector();

  const [selectedMissionKey, setSelectedMissionKey] = useState<string | null>(null);
  const [selectedPositionKey, setSelectedPositionKey] = useState<string | null>(null);
  const [selectedWing, setSelectedWing] = useState<HqWingKey | null>("atrium");
  const [representation, setRepresentation] =
    useState<OrganizationRepresentation>("spatial");

  const hqCharacterLayout = useMemo(
    () =>
      buildV2HqCharacterLayout(
        sceneEmployees,
        data?.organization.zones ?? [],
      ),
    [sceneEmployees, data?.organization.zones],
  );

  const visibleHandoff = useMemo(
    () =>
      buildLatestV2VisibleHandoff({
        handoffs: sceneHandoffs,
        employees: sceneEmployees,
        coverageState: handoffCoverage,
      }),
    [handoffCoverage, sceneEmployees, sceneHandoffs],
  );

  const hqCharacters = useMemo<readonly HqWingCharacterInput[]>(
    () => [
      ...hqCharacterLayout.placements.map((placement) => ({
        positionKey: placement.positionKey,
        title: placement.title,
        department: placement.department,
        presentationWing: placement.wingKey,
      })),
      ...hqCharacterLayout.unplaced.map((employee) => ({
        positionKey: employee.positionKey,
        title: employee.title,
        department: employee.department,
        presentationWing: null,
      })),
    ],
    [hqCharacterLayout],
  );

  const hqWingMetrics = useMemo<readonly HqWingMetricInput[]>(
    () =>
      (data?.organization.zones ?? []).map((zone) => ({
        wingKey: zone.wingKey,
        departmentCount: zone.departments.length,
        employeeCount: zone.employeeRosterCount,
        workItemCount: zone.workItemCount,
        activeBlockerCount: zone.activeBlockerCount,
      })),
    [data?.organization.zones],
  );

  const missionRoom = useMemo(
    () => missionRoomFor(selectedMissionKey),
    [missionRoomFor, selectedMissionKey],
  );

  const employeeInspector = useMemo(
    () => employeeInspectorFor(selectedPositionKey),
    [employeeInspectorFor, selectedPositionKey],
  );

  const selectMission = (missionKey: string) => {
    setSelectedMissionKey(missionKey);
    setSelectedPositionKey(null);
  };

  const selectEmployee = (positionKey: string) => {
    setSelectedPositionKey(positionKey);
    const placement = hqCharacterLayout.placements.find(
      (candidate) => candidate.positionKey === positionKey,
    );
    if (placement) setSelectedWing(placement.wingKey);
  };

  const openWing = (wingKey: HqWingKey) => {
    setSelectedWing(wingKey);
    router.push(`/cockpit/v2/organization/wing/${wingKey}`);
  };

  const retryAll = async () => {
    await Promise.all([refresh(), refreshRoom()]);
  };

  const structuredOrganization = (
    <section
      aria-labelledby="aios-v2-structured-title"
      className={`aios-v2-structured-fallback ${styles.structuredFallback}`}
      data-v2-organization-representation="structured"
      data-view-placement={representation === "structured" ? "primary" : "equivalent"}
    >
      <header className="aios-v2-section-heading">
        <div>
          <span>{representation === "structured" ? "Renderer-free view" : "Accessible equivalent"}</span>
          <h2 className={styles.sectionTitle} id="aios-v2-structured-title">Structured organization</h2>
        </div>
        <small>Available independently of the spatial renderer.</small>
      </header>

      {loading ? (
        <div className="aios-v2-empty-line" role="status">Loading structured organization…</div>
      ) : data?.organization.established ? (
        <>
          <V2CanonicalHandoffSignal
            model={visibleHandoff}
            reducedMotion
            variant="structured"
          />

          <div className="aios-v2-structured-grid">
            {data.organization.zones.map((zone) => {
              const placements = hqCharacterLayout.placements.filter(
                (placement) => placement.wingKey === zone.wingKey,
              );
              return (
                <section className={styles.structuredZone} key={zone.wingKey}>
                  <div className={styles.zoneHeader}>
                    <div>
                      <h3>{zone.label}</h3>
                      <small>
                        {zone.employeeRosterCount} rostered · {zone.workItemCount} work · {zone.activeBlockerCount} blockers
                      </small>
                    </div>
                    <button onClick={() => openWing(zone.wingKey)} type="button">
                      Open details
                    </button>
                  </div>

                  <div className={styles.structuredGroup}>
                    <strong>Departments</strong>
                    {zone.departments.length ? (
                      <ul>
                        {zone.departments.map((department) => (
                          <li key={department.key}>
                            <span>{department.label}</span>
                            <small>
                              {department.employeeRosterCount} rostered · {department.workItemCount} work · {department.activeBlockerCount} blockers
                            </small>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>No canonical department mapped.</p>
                    )}
                  </div>

                  <div className={styles.structuredGroup}>
                    <strong>Mapped roster</strong>
                    {placements.length ? (
                      <ul className={styles.employeeList}>
                        {placements.map((placement) => (
                          <li key={placement.positionKey}>
                            <button
                              aria-pressed={selectedPositionKey === placement.positionKey}
                              className={styles.employeeButton}
                              data-selected={selectedPositionKey === placement.positionKey ? "true" : "false"}
                              onClick={() => selectEmployee(placement.positionKey)}
                              type="button"
                            >
                              <span>{placement.title || placement.positionKey}</span>
                              <small>{placement.department} · presentation mapping only</small>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>No rostered employee is mapped to this presentation wing.</p>
                    )}
                  </div>
                </section>
              );
            })}
          </div>

          {hqCharacterLayout.unplaced.length ? (
            <section className={styles.unplacedRoster} aria-labelledby="aios-v2-unplaced-roster-title">
              <div>
                <span>Truth-preserving limitation</span>
                <h3 id="aios-v2-unplaced-roster-title">Unplaced roster</h3>
                <p>
                  These rostered employees remain intentionally outside the architectural mapping because AIOS has no unique exact department-to-wing basis.
                </p>
              </div>
              <ul className={styles.employeeList}>
                {hqCharacterLayout.unplaced.map((employee) => (
                  <li key={employee.positionKey}>
                    <button
                      aria-pressed={selectedPositionKey === employee.positionKey}
                      className={styles.employeeButton}
                      data-selected={selectedPositionKey === employee.positionKey ? "true" : "false"}
                      onClick={() => selectEmployee(employee.positionKey)}
                      type="button"
                    >
                      <span>{employee.title || employee.positionKey}</span>
                      <small>{employee.department} · {employee.reason.replaceAll("-", " ")}</small>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      ) : (
        <div className="aios-v2-empty-line" role="status">No structured Living Organization scene is established.</div>
      )}

      <div className={styles.truthNote} role="note">
        Structured view is presentation-only. Wing mapping is not physical location, roster identity is not presence, and selecting a row changes inspection context only.
      </div>
    </section>
  );

  return (
    <V2Shell activeItem="Organization" backendOnline={health?.status === "ok"}>
      <div className="aios-v2-content">
        <section className="aios-v2-hero aios-v2-hero-compact" aria-labelledby="aios-v2-organization-title">
          <span className="aios-v2-kicker">Organization · governed spatial view</span>
          <h1 id="aios-v2-organization-title">One organization. Two representations.</h1>
          <p>
            The architectural world and the structured organization are read-only presentations of the connected Living Organization scene. Choose Structured to work without mounting the Living HQ renderer; either representation preserves the same governed source and truth boundaries.
          </p>
        </section>

        {error || roomError ? (
          <div className="aios-v2-source-warning" role="alert">
            <div>
              <strong>Some Organization data could not be loaded.</strong>
              <span>{[error, roomError].filter(Boolean).join(" · ")}</span>
            </div>
            <button onClick={() => void retryAll()} type="button">Retry</button>
          </div>
        ) : null}

        {data?.partial ? (
          <div className="aios-v2-source-warning" role="status">
            <div>
              <strong>Partial organization view.</strong>
              <span>Unavailable: {data.unavailableSources.join(", ")}.</span>
            </div>
          </div>
        ) : null}

        <fieldset
          aria-describedby="aios-v2-representation-note"
          className={styles.representationControl}
          data-representation={representation}
        >
          <legend>Organization representation</legend>
          <div className={styles.representationOptions}>
            <label data-active={representation === "spatial" ? "true" : "false"}>
              <input
                checked={representation === "spatial"}
                name="aios-v2-organization-representation"
                onChange={() => setRepresentation("spatial")}
                type="radio"
                value="spatial"
              />
              <span>Spatial</span>
            </label>
            <label data-active={representation === "structured" ? "true" : "false"}>
              <input
                checked={representation === "structured"}
                name="aios-v2-organization-representation"
                onChange={() => setRepresentation("structured")}
                type="radio"
                value="structured"
              />
              <span>Structured</span>
            </label>
          </div>
          <small id="aios-v2-representation-note">
            Local view preference only · no canonical mutation · Structured mode does not mount the Living HQ stage.
          </small>
        </fieldset>

        {representation === "spatial" ? (
          <V2LivingHqVisualStage
            characters={hqCharacters}
            handoff={visibleHandoff}
            loading={loading || roomLoading}
            missionCount={data?.organization.missionCount ?? 0}
            onSelectCharacter={(positionKey, wingKey) => {
              setSelectedWing(wingKey);
              selectEmployee(positionKey);
            }}
            onSelectWing={openWing}
            organizationLabel="Living Organization"
            sceneEstablished={data?.organization.established ?? false}
            selectedPositionKey={selectedPositionKey}
            selectedWing={selectedWing}
            wingMetrics={hqWingMetrics}
          />
        ) : structuredOrganization}

        <V2MissionStrip
          loading={loading}
          missions={data?.missions || []}
          onSelectMission={selectMission}
          selectedMissionKey={selectedMissionKey}
        />

        <div className="aios-v2-mission-inspection-layout">
          <V2MissionRoomPanel
            loading={roomLoading}
            model={missionRoom}
            onSelectEmployee={selectEmployee}
            selectedPositionKey={selectedPositionKey}
          />
          <V2EmployeeInspector
            model={employeeInspector}
            onClose={() => setSelectedPositionKey(null)}
          />
        </div>

        {representation === "spatial" ? structuredOrganization : null}
      </div>
    </V2Shell>
  );
}
