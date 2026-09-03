import type { V2EmployeeInspectorModel } from "../../lib/v2/mission-room-inspector";
import { V2CharacterMiniature } from "./V2CharacterMiniature";

export function V2EmployeeInspector({
  model,
  onClose,
}: {
  model: V2EmployeeInspectorModel | null;
  onClose: () => void;
}) {
  if (!model) {
    return (
      <aside className="aios-v2-employee-inspector empty" aria-label="Employee Inspector">
        <div className="aios-v2-empty-line" role="status">
          Select a rostered Mission participant to inspect canonical employee state.
        </div>
      </aside>
    );
  }

  if (!model.established || !model.employee) {
    return (
      <aside className="aios-v2-employee-inspector" aria-label="Employee Inspector">
        <header className="aios-v2-inspector-header">
          <div>
            <span>Employee Inspector</span>
            <strong>Unsupported employee</strong>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <div className="aios-v2-empty-line" role="status">{model.limitation}</div>
      </aside>
    );
  }

  const employee = model.employee;

  return (
    <aside
      className="aios-v2-employee-inspector"
      aria-labelledby="aios-v2-employee-inspector-title"
      data-presence-claimed="false"
      data-locomotion-claimed="false"
      data-mutations-allowed={String(model.mutationsAllowed)}
    >
      <header className="aios-v2-inspector-header">
        <div>
          <span>Employee Inspector</span>
          <strong id="aios-v2-employee-inspector-title">{employee.title}</strong>
        </div>
        <button type="button" onClick={onClose}>Close</button>
      </header>

      <V2CharacterMiniature
        department={employee.department}
        positionKey={employee.position_key}
        title={employee.title}
        variant="inspector"
      />

      <div className="aios-v2-inspector-identity">
        <div>
          <span>Position key</span>
          <strong>{employee.position_key}</strong>
        </div>
        <div>
          <span>Department</span>
          <strong>{employee.department}</strong>
        </div>
        <div>
          <span>Authority</span>
          <strong>{employee.authority_level}</strong>
        </div>
        <div>
          <span>Organization state</span>
          <strong>{employee.organization_status}</strong>
        </div>
      </div>

      <section className="aios-v2-inspector-state" aria-label="Canonical presentation state">
        <span>Canonical presentation state</span>
        <strong>{employee.semantic_state.replaceAll("_", " ")}</strong>
        <p>{employee.state_reason}</p>
        <small>
          {employee.work_status
            ? "Linked work status: " + employee.work_status.replaceAll("_", " ")
            : "No linked WorkItem status is exposed for this employee."}
        </small>
      </section>

      <section className="aios-v2-inspector-links" aria-label="Linked canonical records">
        <div>
          <span>Missions</span>
          <strong>{model.activeMissionKeys.length}</strong>
        </div>
        <div>
          <span>Blockers</span>
          <strong>{model.blockerIds.length}</strong>
        </div>
        <div>
          <span>Decisions</span>
          <strong>{model.decisionIds.length}</strong>
        </div>
        <div>
          <span>Handoffs</span>
          <strong>{model.handoffActivityIds.length}</strong>
        </div>
      </section>

      {model.activeMissionKeys.length ? (
        <div className="aios-v2-inspector-missions">
          <span>Mission membership</span>
          <ul>
            {model.activeMissionKeys.map((missionKey) => <li key={missionKey}>{missionKey}</li>)}
          </ul>
        </div>
      ) : null}

      <footer className="aios-v2-inspector-truth">
        <strong>Roster identity is not physical presence.</strong>
        <span>Presence claimed: no</span>
        <span>Locomotion claimed: no</span>
        <span>Mutation: {model.mutationsAllowed ? "allowed by source posture" : "disabled"}</span>
      </footer>
    </aside>
  );
}
