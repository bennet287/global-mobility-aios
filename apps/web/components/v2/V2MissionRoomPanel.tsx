import type {
  V2MissionRoomModel,
} from "../../lib/v2/mission-room-inspector";
import { V2DataState, V2SectionHeader, V2StateBadge } from "./ui/V2Primitives";
import { V2CharacterMiniature } from "./V2CharacterMiniature";

function timestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "time unavailable";
  return date.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

export function V2MissionRoomPanel({
  model,
  loading,
  selectedPositionKey,
  onSelectEmployee,
}: {
  model: V2MissionRoomModel | null;
  loading: boolean;
  selectedPositionKey: string | null;
  onSelectEmployee: (positionKey: string) => void;
}) {
  return (
    <section className="aios-v2-mission-room" aria-labelledby="aios-v2-mission-room-title">
      <V2SectionHeader eyebrow="Mission Room" id="aios-v2-mission-room-title" title={model?.mission?.title || "Select a Mission"} description="Read-only canonical projection · no inferred conversation or presence" />

      {loading ? (
        <V2DataState state={{ kind: "loading", label: "Loading Mission Room projection…" }} />
      ) : !model ? (
        <div className="aios-v2-empty-line" role="status">
          Select a canonical Mission above to inspect its supported participants, blockers, decisions and handoffs.
        </div>
      ) : !model.established || !model.mission ? (
        <div className="aios-v2-empty-line" role="status">{model.limitation}</div>
      ) : (
        <>
          <div className="aios-v2-mission-room-summary">
            <div>
              <span>State</span>
              <V2StateBadge label={model.mission.state.replaceAll("_", " ")} />
            </div>
            <div>
              <span>Participants</span>
              <strong>{model.participants.length}</strong>
            </div>
            <div>
              <span>Blockers</span>
              <strong>{model.blockerCoverageSupported ? model.blockers.length : "Unavailable"}</strong>
            </div>
            <div>
              <span>Decisions</span>
              <strong>{model.decisions.length}</strong>
            </div>
            <div>
              <span>Handoffs</span>
              <strong>{model.handoffs.length}</strong>
            </div>
          </div>

          <div className="aios-v2-mission-room-grid">
            <section className="aios-v2-room-participants" aria-labelledby="aios-v2-room-participants-title">
              <header>
                <span>Rostered Mission participants</span>
                <strong id="aios-v2-room-participants-title">People</strong>
              </header>

              {model.participants.length ? (
                <div className="aios-v2-room-participant-list">
                  {model.participants.map((participant) => (
                    <button
                      aria-pressed={selectedPositionKey === participant.positionKey}
                      className="aios-v2-room-participant"
                      data-selected={String(selectedPositionKey === participant.positionKey)}
                      key={participant.positionKey}
                      onClick={() => onSelectEmployee(participant.positionKey)}
                      type="button"
                    >
                      <V2CharacterMiniature
                        department={participant.department}
                        positionKey={participant.positionKey}
                        title={participant.title}
                      />
                      <span className="aios-v2-room-participant-copy">
                        <span>{participant.department}</span>
                        <strong>{participant.title}</strong>
                        <small>{participant.authorityLevel} · {participant.semanticState.replaceAll("_", " ")}</small>
                        <em>Rostered participant · character is presentation only · presence not claimed</em>
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <p>No participant positions are supported by this Mission projection.</p>
              )}
            </section>

            <section className="aios-v2-room-signals" aria-labelledby="aios-v2-room-signals-title">
              <header>
                <span>Supported Mission signals</span>
                <strong id="aios-v2-room-signals-title">Canonical links</strong>
              </header>

              <div
                className="aios-v2-room-signal-group"
                data-blocker-coverage={model.blockerCoverageState}
              >
                <span>Blockers</span>
                {!model.blockerCoverageSupported ? (
                  <p>
                    Blocker coverage unavailable · {model.blockerCoverageState}. AIOS will not present an empty blocker list as canonical zero.
                  </p>
                ) : model.blockers.length ? (
                  <ul>
                    {model.blockers.map((blocker) => (
                      <li key={blocker.blocker_id}>
                        <strong>{blocker.title}</strong>
                        <small>{blocker.severity} · {blocker.blocker_type} · {blocker.status}</small>
                      </li>
                    ))}
                  </ul>
                ) : <p>No linked blockers under established canonical blocker coverage.</p>}
              </div>

              <div className="aios-v2-room-signal-group">
                <span>Decisions</span>
                {model.decisions.length ? (
                  <ul>
                    {model.decisions.map((decision) => (
                      <li key={decision.decision_id}>
                        <strong>{decision.title}</strong>
                        <small>{decision.authority_level} · {decision.status}</small>
                      </li>
                    ))}
                  </ul>
                ) : <p>No linked decisions.</p>}
              </div>

              <div className="aios-v2-room-signal-group">
                <span>Handoffs</span>
                {model.handoffs.length ? (
                  <ul>
                    {model.handoffs.slice(0, 6).map((handoff) => (
                      <li key={handoff.activity_id}>
                        <strong>{handoff.previous_position_key} → {handoff.assigned_position_key}</strong>
                        <small>{handoff.status} · {timestamp(handoff.occurred_at)}</small>
                      </li>
                    ))}
                  </ul>
                ) : <p>No linked handoff events.</p>}
              </div>
            </section>
          </div>

          <footer className="aios-v2-room-truth">
            <span>Canonical projection: {model.canonicalProjection ? "yes" : "no"}</span>
            <span>Scene authority: {model.sceneAuthoritative ? "authoritative" : "non-authoritative"}</span>
            <span>Renderer authority: {model.rendererAuthoritative ? "authoritative" : "none"}</span>
            <span>Blocker coverage: {model.blockerCoverageState}</span>
            <span>Mutation: {model.mutationsAllowed ? "allowed" : "disabled"}</span>
          </footer>
        </>
      )}
    </section>
  );
}
