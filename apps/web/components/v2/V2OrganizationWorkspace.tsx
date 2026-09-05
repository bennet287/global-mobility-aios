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
import { V2EmployeeInspector } from "./V2EmployeeInspector";
import { V2LivingHqVisualStage } from "./V2LivingHqVisualStage";
import { V2MissionRoomPanel } from "./V2MissionRoomPanel";
import { V2MissionStrip } from "./V2MissionStrip";
import { V2Shell } from "./V2Shell";

export function V2OrganizationWorkspace() {
  const router = useRouter();
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const {
    loading: roomLoading,
    error: roomError,
    employees: sceneEmployees,
    refresh: refreshRoom,
    missionRoomFor,
    employeeInspectorFor,
  } = useV2MissionRoomInspector();

  const [selectedMissionKey, setSelectedMissionKey] = useState<string | null>(null);
  const [selectedPositionKey, setSelectedPositionKey] = useState<string | null>(null);
  const [selectedWing, setSelectedWing] = useState<HqWingKey | null>("atrium");

  const hqCharacterLayout = useMemo(
    () =>
      buildV2HqCharacterLayout(
        sceneEmployees,
        data?.organization.zones ?? [],
      ),
    [sceneEmployees, data?.organization.zones],
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

  return (
    <V2Shell activeItem="Organization" backendOnline={health?.status === "ok"}>
      <div className="aios-v2-content">
        <section className="aios-v2-hero aios-v2-hero-compact" aria-labelledby="aios-v2-organization-title">
          <span className="aios-v2-kicker">Organization · governed spatial view</span>
          <h1 id="aios-v2-organization-title">One organization. Two representations.</h1>
          <p>
            The architectural world and the structured organization below are read-only presentations of the connected Living Organization scene. Open a wing to inspect its governed detail route; employee selection changes view focus only.
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

        <V2LivingHqVisualStage
          characters={hqCharacters}
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

        <section className="aios-v2-structured-fallback" aria-labelledby="aios-v2-structured-title">
          <header className="aios-v2-section-heading">
            <div>
              <span>Accessible equivalent</span>
              <strong id="aios-v2-structured-title">Structured organization</strong>
            </div>
            <small>Available independently of the spatial renderer.</small>
          </header>

          {loading ? (
            <div className="aios-v2-empty-line" role="status">Loading structured organization…</div>
          ) : data?.organization.established ? (
            <div className="aios-v2-structured-grid">
              {data.organization.zones.map((zone) => (
                <section key={zone.wingKey}>
                  <strong>{zone.label}</strong>
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
                </section>
              ))}
            </div>
          ) : (
            <div className="aios-v2-empty-line" role="status">No structured Living Organization scene is established.</div>
          )}
        </section>
      </div>
    </V2Shell>
  );
}
