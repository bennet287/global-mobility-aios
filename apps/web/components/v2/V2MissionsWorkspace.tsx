"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import {
  buildV2MissionPortfolio,
  filterMissionSummaries,
  missionDestination,
  missionSourceUnavailable,
  selectMissionSummary,
} from "../../lib/v2/missions-workspace";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import {
  V2DataState,
  V2Inspector,
  V2MetricGroup,
  V2ObjectRow,
  V2PageHeader,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
  V2Surface,
  formatV2Timestamp,
} from "./ui/V2Primitives";
import styles from "./V2MissionsWorkspace.module.css";

export function V2MissionsWorkspace() {
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const { health } = useBackendStatus();
  const params = useSearchParams();
  const router = useRouter();
  const selectedKey = params.get("mission");
  const query = params.get("q") ?? "";
  const state = params.get("state") ?? "";
  const portfolio = data ? buildV2MissionPortfolio(data) : null;
  const missions = portfolio?.missions ?? [];
  const filteredMissions = filterMissionSummaries(missions, query, state);
  const selectedMission = selectMissionSummary(missions, selectedKey);
  const inspectorTarget = useRef<HTMLDivElement>(null);
  const selectionOrigin = useRef<HTMLElement | null>(null);

  useV2SearchItems(missions.map((mission) => ({
    id: mission.missionKey,
    kind: "Mission" as const,
    icon: "missions" as const,
    label: mission.title,
    description: `${mission.state}${mission.phaseKey ? ` · ${mission.phaseKey}` : ""}`,
    href: missionDestination(mission.missionKey),
  })));

  useEffect(() => {
    if (selectedKey && selectedMission) inspectorTarget.current?.focus();
  }, [selectedKey, selectedMission]);

  function replaceParam(name: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(name, value);
    else next.delete(name);
    const suffix = next.toString();
    router.replace(`/cockpit/v2/missions${suffix ? `?${suffix}` : ""}`, { scroll: false });
  }

  function selectMission(missionKey: string) {
    selectionOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const next = new URLSearchParams(params.toString());
    next.set("mission", missionKey);
    router.push(`/cockpit/v2/missions?${next.toString()}`, { scroll: false });
  }

  function closeInspector() {
    replaceParam("mission", "");
    requestAnimationFrame(() => selectionOrigin.current?.focus());
  }

  const sceneUnavailable = data ? missionSourceUnavailable(data) : false;
  const established = data?.organization.established === true && !sceneUnavailable;

  return (
    <V2Shell activeItem="Missions" backendOnline={health?.status === "ok"}>
      <div className={`aios-v2-content ${styles.page}`}>
        <V2PageHeader
          eyebrow="Owner portfolio"
          title="Missions"
          description="See the returned work portfolio, then inspect the canonical basis without turning selection into action."
          actions={<button type="button" onClick={() => void refresh()}>Refresh Missions</button>}
        />

        {loading && !data ? <V2DataState state={{ kind: "loading", label: "Loading Mission portfolio…" }} /> : null}
        {error && !data ? <V2DataState state={{ kind: "unavailable", label: "Mission portfolio unavailable", detail: error, onRetry: () => void refresh() }} /> : null}
        {data && error ? <V2DataState state={{ kind: "stale", label: "Mission refresh failed", detail: error, lastLoadedAt: data.loadedAt, onRetry: () => void refresh() }} /> : null}
        {data && sceneUnavailable ? <V2DataState state={{ kind: "unavailable", label: "Living Organization Mission source unavailable", detail: "The governed Owner read could not retrieve the Living Organization scene. No zero-Mission conclusion is made.", onRetry: () => void refresh() }} /> : null}
        {data && !sceneUnavailable && !data.organization.established ? <V2DataState state={{ kind: "unavailable", label: "Mission projection not established", detail: "The Living Organization source returned no established scene. AIOS does not fabricate a Mission portfolio." }} /> : null}

        {data && established && portfolio ? (
          <>
            {data.partial ? <V2DataState state={{ kind: "partial", label: "Partial Owner source coverage", unavailableSources: data.unavailableSources }} /> : null}

            <V2ProvenanceDisclosure title="Mission source posture">
              <p>Loaded {formatV2Timestamp(data.loadedAt)} from the governed Owner read path.</p>
              <p>Scene generated: {formatV2Timestamp(data.organization.generatedAt)} · Contract: {data.organization.contractVersion ?? "Not supplied"}.</p>
              <p>Canonical authority: {data.organization.canonicalAuthority ?? "Not supplied"}. This UI remains read-only.</p>
            </V2ProvenanceDisclosure>

            <V2MetricGroup
              label="Mission portfolio readout"
              items={[
                { label: "Returned Missions", value: portfolio.returnedMissionCount },
                { label: "With blockers", value: portfolio.missionsWithBlockers },
                { label: "With decisions", value: portfolio.missionsWithDecisions },
                { label: "Rostered participants", value: portfolio.rosteredParticipants, hint: "Roster relation, not presence" },
              ]}
            />

            {missions.length ? (
              <div className={styles.workspace}>
                <V2Surface className={styles.portfolio} label="Mission portfolio">
                  <V2SectionHeader
                    eyebrow="Returned portfolio"
                    title="Mission records"
                    description="Exact supplied states and literal counts only."
                  />
                  <div className={styles.filters}>
                    <label>
                      <span>Filter Missions</span>
                      <input aria-label="Filter Missions" type="search" value={query} onChange={(event) => replaceParam("q", event.target.value)} />
                    </label>
                    <label>
                      <span>State</span>
                      <select aria-label="Mission state" value={state} onChange={(event) => replaceParam("state", event.target.value)}>
                        <option value="">All returned states</option>
                        {[...new Set(missions.map((mission) => mission.state))].sort().map((value) => <option key={value} value={value}>{value}</option>)}
                      </select>
                    </label>
                  </div>
                  <div className={styles.list} aria-label="Mission records">
                    {filteredMissions.map((mission) => (
                      <V2ObjectRow
                        key={mission.missionKey}
                        title={mission.title}
                        description={`${mission.phaseKey ? `Phase: ${mission.phaseKey} · ` : ""}${mission.participantCount} rostered participants · ${mission.blockerCount} blockers · ${mission.decisionCount} decisions`}
                        trailing={<V2StateBadge label={mission.state} />}
                        selected={selectedKey === mission.missionKey}
                        onSelect={() => selectMission(mission.missionKey)}
                      />
                    ))}
                  </div>
                  {!filteredMissions.length ? <V2DataState state={{ kind: "empty", label: "No returned Missions match these filters", detail: "The filter result is empty; this does not describe work outside the governed Mission projection." }} /> : null}
                </V2Surface>

                <div className={styles.inspectorSlot} ref={inspectorTarget} tabIndex={-1}>
                  {selectedMission ? (
                    <V2Inspector
                      title={selectedMission.title}
                      description="Read-only Mission inspection. Selection changes view context only."
                      onClose={closeInspector}
                    >
                      <div className={styles.stateLine}>
                        <span>Recorded state</span>
                        <V2StateBadge label={selectedMission.state} />
                      </div>
                      <p className={styles.phase}>Phase: {selectedMission.phaseKey ?? "Not supplied"}</p>
                      <V2MetricGroup
                        label="Selected Mission readout"
                        items={[
                          { label: "Participants", value: selectedMission.participantCount, hint: "Rostered, not present" },
                          { label: "Blockers", value: selectedMission.blockerCount },
                          { label: "Decisions", value: selectedMission.decisionCount },
                        ]}
                      />
                      <V2ProvenanceDisclosure title="Mission provenance" technical>
                        <dl className={styles.definitionList}>
                          <dt>Mission key</dt><dd>{selectedMission.missionKey}</dd>
                          <dt>Root WorkItem</dt><dd>{selectedMission.rootWorkItemId}</dd>
                          <dt>Canonical basis</dt><dd>{selectedMission.canonicalBasis}</dd>
                        </dl>
                        <p>Roster counts are not physical presence. No progress percentage, completion, urgency, authority or next action is inferred.</p>
                      </V2ProvenanceDisclosure>
                    </V2Inspector>
                  ) : selectedKey ? (
                    <V2DataState state={{ kind: "unavailable", label: "Selected Mission was not returned", detail: "The exact Mission key is outside this loaded portfolio. AIOS will not substitute another record." }} />
                  ) : (
                    <V2Surface kind="inset" className={styles.placeholder} label="Mission inspection">
                      <V2SectionHeader title="Inspect a Mission" description="Choose a returned Mission to reveal its supplied state, literal counts and canonical basis." />
                      <p>Selection is presentation-only and cannot mutate AIOS.</p>
                    </V2Surface>
                  )}
                </div>
              </div>
            ) : (
              <V2DataState state={{ kind: "empty", label: "No Missions returned", detail: "The established Living Organization projection returned an empty Mission collection." }} />
            )}
          </>
        ) : null}
      </div>
    </V2Shell>
  );
}
