import type { CSSProperties } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

const ACTIVE_STATES = new Set(["working", "blocked", "awaiting_owner", "queued"]);

export function LivingOrganizationDepartmentFabric({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  return (
    <section
      className="living-hq-department-fabric"
      aria-label="Canonical department neighborhoods and coordination"
      data-presentation-only="true"
      data-authority="none"
      data-coordination-source="canonical-only"
    >
      <header>
        <div>
          <span>Whole-organization fabric</span>
          <strong>{renderModel.departmentZones.length} canonical departments</strong>
        </div>
        <small>{renderModel.departmentCoordinations.length} cross-department coordination links</small>
      </header>

      <div className="living-hq-department-neighborhoods" aria-label="Canonical department neighborhoods">
        {renderModel.departmentZones.map((zone, index) => {
          const activeEmployees = zone.employeeSlots.filter(({ employee }) => ACTIVE_STATES.has(employee.semantic_state)).length;
          const blockedEmployees = zone.employeeSlots.filter(({ employee }) => employee.semantic_state === "blocked").length;
          return (
            <article
              key={zone.department.department_key}
              className="living-hq-department-neighborhood"
              data-department-key={zone.department.department_key}
              data-active-employees={activeEmployees}
              data-blocked-employees={blockedEmployees}
              style={{ "--department-index": index } as CSSProperties}
            >
              <i aria-hidden="true" />
              <div>
                <strong>{zone.department.label}</strong>
                <small>{zone.employeeSlots.length} employees · {zone.workItems.length} WorkItems</small>
              </div>
              <span>{activeEmployees} active{blockedEmployees ? ` · ${blockedEmployees} blocked` : ""}</span>
            </article>
          );
        })}
      </div>

      <div className="living-hq-department-coordination" aria-label="Canonical cross-department coordination">
        {renderModel.departmentCoordinations.length ? (
          renderModel.departmentCoordinations.map((coordination) => (
            <article
              key={coordination.key}
              data-source-department={coordination.sourceDepartment}
              data-target-department={coordination.targetDepartment}
              data-handoff-count={coordination.handoffCount}
              data-conversation-count={coordination.conversationCount}
            >
              <span>{coordination.sourceLabel}</span>
              <i aria-hidden="true" />
              <span>{coordination.targetLabel}</span>
              <small>
                {coordination.handoffCount ? `${coordination.handoffCount} handoff${coordination.handoffCount === 1 ? "" : "s"}` : ""}
                {coordination.handoffCount && coordination.conversationCount ? " · " : ""}
                {coordination.conversationCount ? `${coordination.conversationCount} conversation${coordination.conversationCount === 1 ? "" : "s"}` : ""}
              </small>
            </article>
          ))
        ) : (
          <p data-empty-coordination="true">No canonical cross-department handoff or conversation is projected right now.</p>
        )}
      </div>

      <p className="living-hq-department-fabric-truth">
        Department neighborhoods come from the canonical Living Organization projection. Coordination links appear only when canonical handoff or governed conversation records connect employees from different departments; shared Mission membership alone never creates a link.
      </p>
    </section>
  );
}
