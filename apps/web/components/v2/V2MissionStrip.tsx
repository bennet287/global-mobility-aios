import type { V2MissionSummary } from "../../lib/v2/owner-organization";

export function V2MissionStrip({
  missions,
  loading,
}: {
  missions: V2MissionSummary[];
  loading: boolean;
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
          {missions.map((mission) => (
            <article className="aios-v2-mission-object" data-state={mission.state} key={mission.missionKey}>
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
            </article>
          ))}
        </div>
      ) : (
        <div className="aios-v2-empty-line" role="status">No Mission projection is established for the connected Living Organization scene.</div>
      )}
    </section>
  );
}
