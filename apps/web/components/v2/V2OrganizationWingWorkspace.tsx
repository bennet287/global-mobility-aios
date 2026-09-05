"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2MissionRoomInspector } from "../../hooks/useV2MissionRoomInspector";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import { buildV2HqCharacterLayout } from "../../lib/v2/hq-character-layout";
import {
  resolveHqVisualStageLayout,
  type HqWingCharacterInput,
  type HqWingKey,
  type HqWingMetricInput,
} from "../../lib/v2/hq-visual-presentation";
import { V2EmployeeInspector } from "./V2EmployeeInspector";
import { V2MissionRoomPanel } from "./V2MissionRoomPanel";
import { V2MissionStrip } from "./V2MissionStrip";
import { V2Shell } from "./V2Shell";
import { V2WingFocusPanel } from "./V2WingFocusPanel";

export function V2OrganizationWingWorkspace({ wingKey }: { readonly wingKey: HqWingKey }) {
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

  const hqCharacterLayout = useMemo(
    () => buildV2HqCharacterLayout(sceneEmployees, data?.organization.zones ?? []),
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

  const visualLayout = useMemo(
    () => resolveHqVisualStageLayout({ metrics: hqWingMetrics, characters: hqCharacters }),
    [hqWingMetrics, hqCharacters],
  );

  const zone = visualLayout.zones.find((candidate) => candidate.wingKey === wingKey) ?? null;
  const sourceZone = data?.organization.zones.find((candidate) => candidate.wingKey === wingKey) ?? null;

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

  const retryAll = async () => {
    await Promise.all([refresh(), refreshRoom()]);
  };

  const title = zone?.label ?? "Organization wing";

  return (
    <V2Shell activeItem="Organization" backendOnline={health?.status === "ok"}>
      <div className="aios-v2-content">
        <Link href="/cockpit/v2/organization" className="aios-v2-kicker">
          ← Living Organization
        </Link>

        <section className="aios-v2-hero aios-v2-hero-compact" aria-labelledby="aios-v2-wing-title">
          <span className="aios-v2-kicker">Organization · governed wing detail</span>
          <h1 id="aios-v2-wing-title">{title}</h1>
          <p>
            This is a dedicated read-only presentation route for one governed HQ wing. It may expose mapped departments, roster counts, work counts, blockers, placed character presentations and supported Missions, but it does not claim physical presence or write canonical state.
          </p>
        </section>

        {error || roomError ? (
          <div className="aios-v2-source-warning" role="alert">
            <div>
              <strong>Some wing data could not be loaded.</strong>
              <span>{[error, roomError].filter(Boolean).join(" · ")}</span>
            </div>
            <button onClick={() => void retryAll()} type="button">Retry</button>
          </div>
        ) : null}

        {data?.partial ? (
          <div className="aios-v2-source-warning" role="status">
            <div>
              <strong>Partial wing view.</strong>
              <span>Unavailable: {data.unavailableSources.join(", ")}.</span>
            </div>
          </div>
        ) : null}

        {loading || roomLoading ? (
          <div className="aios-v2-empty-line" role="status">Loading governed wing detail…</div>
        ) : zone ? (
          <V2WingFocusPanel
            missionCount={data?.organization.missionCount ?? 0}
            mode="detail"
            onSelectCharacter={setSelectedPositionKey}
            selectedPositionKey={selectedPositionKey}
            zone={zone}
          />
        ) : (
          <div className="aios-v2-empty-line" role="status">Wing presentation unavailable.</div>
        )}

        {wingKey !== "atrium" && selectedPositionKey ? (
          <section aria-label="Selected employee detail">
            <V2EmployeeInspector
              model={employeeInspector}
              onClose={() => setSelectedPositionKey(null)}
            />
          </section>
        ) : null}

        <section className="aios-v2-structured-fallback" aria-labelledby="aios-v2-wing-departments-title">
          <header className="aios-v2-section-heading">
            <div>
              <span>Canonical mapping</span>
              <strong id="aios-v2-wing-departments-title">Mapped departments</strong>
            </div>
            <small>Only departments supplied by the connected Organization projection are shown.</small>
          </header>

          {loading ? (
            <div className="aios-v2-empty-line" role="status">Loading department mapping…</div>
          ) : sourceZone?.departments.length ? (
            <div className="aios-v2-structured-grid">
              {sourceZone.departments.map((department) => (
                <section key={department.key}>
                  <strong>{department.label}</strong>
                  <ul>
                    <li>
                      <span>{department.employeeRosterCount} rostered</span>
                      <small>{department.workItemCount} work · {department.activeBlockerCount} blockers</small>
                    </li>
                  </ul>
                </section>
              ))}
            </div>
          ) : (
            <div className="aios-v2-empty-line" role="status">
              No canonical department is mapped to this presentation wing.
            </div>
          )}
        </section>

        {wingKey === "atrium" ? (
          <>
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
                onSelectEmployee={setSelectedPositionKey}
                selectedPositionKey={selectedPositionKey}
              />
              <V2EmployeeInspector
                model={employeeInspector}
                onClose={() => setSelectedPositionKey(null)}
              />
            </div>
          </>
        ) : null}
      </div>
    </V2Shell>
  );
}
