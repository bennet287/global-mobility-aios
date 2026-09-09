import type { CSSProperties } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

type RoomDescriptor = {
  key: string;
  label: string;
  eyebrow: string;
  purpose: string;
  roomType: "mission" | "evidence" | "board";
};

function roomDescriptor(
  room: LivingSceneRenderModel["missionRoom"],
  roomType: RoomDescriptor["roomType"],
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
  };
}

export function LivingOrganizationFlagshipArchitecture({
  renderModel,
}: {
  renderModel: LivingSceneRenderModel;
}) {
  const rooms = [
    roomDescriptor(renderModel.missionRoom, "mission"),
    roomDescriptor(renderModel.evidenceLab, "evidence"),
    roomDescriptor(renderModel.boardRoom, "board"),
  ].filter((room): room is RoomDescriptor => room !== null);

  return (
    <section
      className="living-hq-architecture"
      aria-labelledby="living-hq-architecture-title"
      data-presentation-only="true"
      data-authority="none"
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
            </div>
            <footer>
              <span>Canonical room</span>
              <small>selection/view only</small>
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
        These chambers and infrastructure forms are presentation-only spatial organization. They do not assert physical
        occupancy, employee location, room activity, work routing, availability, or authority beyond the canonical scene contract.
      </p>
    </section>
  );
}
