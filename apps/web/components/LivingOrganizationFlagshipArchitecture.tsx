import type { CSSProperties } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

type RoomDescriptor = {
  key: string;
  label: string;
  eyebrow: string;
  purpose: string;
  roomType: "mission" | "evidence" | "board";
  liveContext: string;
  governancePosture: string;
};

const CLOSED_STATES = new Set(["completed", "resolved", "closed", "cancelled", "canceled"]);

function isOpenState(value: string): boolean {
  return !CLOSED_STATES.has(value.toLowerCase());
}

function roomDescriptor(
  room: LivingSceneRenderModel["missionRoom"],
  roomType: RoomDescriptor["roomType"],
  liveContext: string,
  governancePosture: string,
): RoomDescriptor | null {
  if (!room) return null;
  const copy = {
    mission: {
      eyebrow: "Execution chamber",
      purpose: "Mission coordination projection",
    },
    evidence: {
      eyebrow: "Verification chamber",
      purpose: "Evidence inspection projection",
    },
    board: {
      eyebrow: "Authority chamber",
      purpose: "Board decision projection",
    },
  }[roomType];
  return {
    key: room.room_key,
    label: room.label,
    eyebrow: copy.eyebrow,
    purpose: copy.purpose,
    roomType,
    liveContext,
    governancePosture,
  };
}

export function LivingOrganizationFlagshipArchitecture({
  renderModel,
}: {
  renderModel: LivingSceneRenderModel;
}) {
  const activeMissions = renderModel.missions.filter((mission) => isOpenState(mission.state));
  const openBlockers = renderModel.blockers.filter((blocker) => isOpenState(blocker.status));
  const currentDecisions = renderModel.decisions.filter((decision) => decision.is_current);
  const boardAttentionRisks = renderModel.riskEscalations.filter(
    (risk) => risk.requires_board_attention && isOpenState(risk.status),
  );
  const openHumanActions = renderModel.humanActions.filter((request) => isOpenState(request.status));

  const rooms = [
    roomDescriptor(
      renderModel.missionRoom,
      "mission",
      `${activeMissions.length} active Missions · ${openBlockers.length} open blockers`,
      openBlockers.length
        ? "Blocked work is surfaced from canonical blocker records; this room does not create or route work."
        : "No open blocker route is projected from canonical state.",
    ),
    roomDescriptor(
      renderModel.evidenceLab,
      "evidence",
      `${renderModel.departmentZones.flatMap((zone) => zone.workItems).filter((item) => item.specialist_evidence_valid === true).length} evidence-valid WorkItems projected`,
      "Evidence posture is read-only; the chamber does not certify evidence.",
    ),
    roomDescriptor(
      renderModel.boardRoom,
      "board",
      `${boardAttentionRisks.length} Board-attention risks · ${currentDecisions.length} current decisions · ${openHumanActions.length} open human actions`,
      boardAttentionRisks.length || openHumanActions.length
        ? "Governance demand is surfaced from canonical escalation, decision, and human-action records; no Board action is inferred."
        : "No current canonical Board-attention or human-action demand is projected.",
    ),
  ].filter((room): room is RoomDescriptor => room !== null);

  return (
    <section
      className="living-hq-architecture"
      aria-labelledby="living-hq-architecture-title"
      data-presentation-only="true"
      data-authority="none"
      data-occupancy-claimed="false"
    >
      <header className="living-hq-architecture-header">
        <div>
          <span>Flagship spatial hierarchy · projection only</span>
          <strong id="living-hq-architecture-title" role="heading" aria-level={4}>Executive HQ chambers</strong>
        </div>
        <small>{rooms.length} canonical room projections · {renderModel.smartObjects.length} smart objects</small>
      </header>

      <div className="living-hq-room-axis" aria-label="Canonical Living Organization rooms">
        {rooms.map((room, index) => (
          <article
            key={room.key}
            className={`living-hq-room living-hq-room-${room.roomType}`}
            data-room-key={room.key}
            data-room-type={room.roomType}
            data-occupancy-claimed="false"
            style={{ "--room-order": index } as CSSProperties}
          >
            <div className="living-hq-room-shell" aria-hidden="true">
              <i className="living-hq-room-ceiling" />
              <i className="living-hq-room-wall living-hq-room-wall-left" />
              <i className="living-hq-room-wall living-hq-room-wall-right" />
              <i className="living-hq-room-table" />
              <i className="living-hq-room-light" />
            </div>
            <div className="living-hq-room-copy">
              <span>{room.eyebrow}</span>
              <strong>{room.label}</strong>
              <small>{room.purpose}</small>
              <small>{room.liveContext}</small>
              <small>{room.governancePosture}</small>
            </div>
            <footer>
              <span>Canonical room</span>
              <small>selection/view only · occupancy not asserted</small>
            </footer>
          </article>
        ))}
      </div>

      <div className="living-hq-smart-object-rail" aria-label="Living Organization smart objects">
        <div className="living-hq-smart-object-title">
          <span>Infrastructure rail</span>
          <strong>Smart-object layer</strong>
        </div>
        <div className="living-hq-smart-object-list">
          {renderModel.smartObjects.map((object) => (
            <article
              key={object.object_key}
              data-object-state={object.state}
              data-object-type={object.object_type}
            >
              <i aria-hidden="true" />
              <div>
                <strong>{object.label}</strong>
                <small>{object.object_type.replaceAll("_", " ")}</small>
              </div>
              <span>{object.state.replaceAll("_", " ")}</span>
            </article>
          ))}
        </div>
      </div>

      <p className="living-hq-architecture-truth">
        Mission and Board context above is derived only from canonical Mission, WorkItem, blocker, decision, human-action and risk-escalation records.
        These chambers remain presentation-only spatial organization. They do not assert physical occupancy, employee location, room activity,
        work routing, availability, Board action, or authority beyond the canonical scene contract.
      </p>
    </section>
  );
}
