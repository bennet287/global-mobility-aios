import type { V2EmployeeInspectorModel } from "../../lib/v2/mission-room-inspector";
import {
  V2AuthorityBadge,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
} from "./ui/V2Primitives";
import { V2CharacterMiniature } from "./V2CharacterMiniature";

function blockerRelation(
  model: V2EmployeeInspectorModel,
  accountablePositionKey: string | null,
): string {
  return accountablePositionKey === model.employee?.position_key
    ? "Accountable position"
    : "Linked WorkItem";
}

function blockerDueLabel(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

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
      data-blocker-details-claimed={model.blockerCoverageSupported ? "true" : "false"}
      data-blocker-resolution-claimed="false"
      data-causal-block-claimed="false"
      data-locomotion-claimed="false"
      data-mutations-allowed={String(model.mutationsAllowed)}
      data-presence-claimed="false"
    >
      <V2SectionHeader
        actions={<button type="button" onClick={onClose}>Close</button>}
        eyebrow="Employee Inspector"
        id="aios-v2-employee-inspector-title"
        title={employee.title}
      />

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
          <V2AuthorityBadge level={employee.authority_level} />
        </div>
        <div>
          <span>Organization state</span>
          <strong>{employee.organization_status}</strong>
        </div>
      </div>

      <section className="aios-v2-inspector-state" aria-label="Canonical presentation state">
        <span>Canonical presentation state</span>
        <V2StateBadge label={employee.semantic_state.replaceAll("_", " ")} />
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
          <strong>{model.blockerCoverageSupported ? model.blockerIds.length : "Unavailable"}</strong>
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

      {model.blockerCoverageSupported ? (
        model.blockers.length ? (
          <section
            aria-label="Canonical blocker details"
            className="aios-v2-inspector-missions"
            data-canonical-blocker-details="true"
          >
            <span>Canonical blockers</span>
            <ul>
              {model.blockers.map((blocker) => {
                const due = blockerDueLabel(blocker.due_at);
                return (
                  <li
                    data-blocker-id={blocker.blocker_id}
                    data-blocker-severity={blocker.severity}
                    data-blocker-status={blocker.status}
                    key={blocker.blocker_id}
                  >
                    <strong>{blocker.title}</strong>
                    <small>
                      {blocker.severity} · {blocker.blocker_type} · {blocker.status}
                    </small>
                    {blocker.description ? <p>{blocker.description}</p> : null}
                    <small>
                      Relationship: {blockerRelation(model, blocker.accountable_position_key)}
                    </small>
                    <small>
                      Human action: {blocker.requires_human_action ? "required" : "not required"}
                      {blocker.overdue ? " · overdue" : ""}
                      {due ? ` · due ${due}` : ""}
                    </small>
                  </li>
                );
              })}
            </ul>
            <small>
              Canonical blocker records describe governed work constraints. They do not establish physical activity, causal body movement, or blocker resolution.
            </small>
          </section>
        ) : (
          <div className="aios-v2-empty-line" role="status">
            No canonical blocker is linked to this employee under the current blocker coverage.
          </div>
        )
      ) : (
        <div
          className="aios-v2-source-warning"
          data-blocker-coverage={model.blockerCoverageState}
          role="status"
        >
          <div>
            <strong>Blocker details unavailable.</strong>
            <span>
              Coverage: {model.blockerCoverageState}. AIOS will not infer blocker title, type, severity or accountability from the employee work-state badge.
            </span>
          </div>
        </div>
      )}

      {model.activeMissionKeys.length ? (
        <div className="aios-v2-inspector-missions">
          <span>Mission membership</span>
          <ul>
            {model.activeMissionKeys.map((missionKey) => <li key={missionKey}>{missionKey}</li>)}
          </ul>
        </div>
      ) : null}

      <p>Roster identity is not physical presence.</p>
      <V2ProvenanceDisclosure title="Presentation truth">
        <footer className="aios-v2-inspector-truth">
          <strong>Roster identity is not physical presence.</strong>
          <span>Presence claimed: no</span>
          <span>Locomotion claimed: no</span>
          <span>Blocker resolution claimed: no</span>
          <span>Mutation: {model.mutationsAllowed ? "allowed by source posture" : "disabled"}</span>
        </footer>
      </V2ProvenanceDisclosure>
    </aside>
  );
}
