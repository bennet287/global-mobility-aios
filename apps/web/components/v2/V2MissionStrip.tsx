import type { V2MissionSummary } from "../../lib/v2/owner-organization";

export function V2MissionStrip({
  missions,
  loading,
  selectedMissionKey = null,
  onSelectMission,
}: {
  missions: V2MissionSummary[];
  loading: boolean;
  selectedMissionKey?: string | null;
  onSelectMission?: (missionKey: string) => void;
}) {
  return (
    <section className="aios-v2-missions" aria-labelledby="aios-v2-missions-title">
      <header className="aios-v2-section-heading">
        <div>
          <span>Mission state</span>
          <strong id="aios-v2-missions-title">Current Missions</strong>
        </div>
        <small>Participant counts describe the Mission projection; they are not presence claims.</small>
      </header>

      {loading ? (
        <div className="aios-v2-empty-line" role="status">Loading canonical Mission projection…</div>
      ) : missions.length ? (
        <div className="aios-v2-mission-list">
          {missions.map((mission) => {
            const selected = selectedMissionKey === mission.missionKey;
            const body = (
              <>
                <div className="aios-v2-mission-object-state">
                  <span>{mission.state.replaceAll("_", " ")}</span>
                  {mission.phaseKey ? <small>{mission.phaseKey.replaceAll("_", " ")}</small> : null}
                </div>
                <strong>{mission.title}</strong>
                <div className="aios-v2-mission-object-metrics">
                  <span>{mission.participantCount} participant{mission.participantCount === 1 ? "" : "s"}</span>
                  <span>{mission.blockerCount} blocker{mission.blockerCount === 1 ? "" : "s"}</span>
                  <span>{mission.decisionCount} decision{mission.decisionCount === 1 ? "" : "s"}</span>
                </div>
                {onSelectMission ? <em>{selected ? "Mission Room selected" : "Open Mission Room"}</em> : null}
              </>
            );

            if (onSelectMission) {
              return (
                <button
                  aria-pressed={selected}
                  className="aios-v2-mission-object aios-v2-mission-select"
                  data-selected={String(selected)}
                  data-state={mission.state}
                  key={mission.missionKey}
                  onClick={() => onSelectMission(mission.missionKey)}
                  type="button"
                >
                  {body}
                </button>
              );
            }

            return (
              <article className="aios-v2-mission-object" data-state={mission.state} key={mission.missionKey}>
                {body}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="aios-v2-empty-line" role="status">No Mission projection is established for the connected Living Organization scene.</div>
      )}
    </section>
  );
}
