import type { CSSProperties } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

function archetypeFor(positionKey: string, title: string, department: string): string {
  const value = `${positionKey} ${title} ${department}`.toLowerCase();
  if (/ceo|chief executive/.test(value)) return "executive";
  if (/cto|technology|engineering|architect|developer|security/.test(value)) return "technology";
  if (/legal|regulat|evidence|compliance|policy|immigration/.test(value)) return "evidence";
  if (/operations|coo|coordination|readiness|document/.test(value)) return "operations";
  if (/finance|cfo|account/.test(value)) return "finance";
  if (/human|hr|recruit|culture/.test(value)) return "people";
  return "specialist";
}

export function LivingOrganizationIntegratedWorkforce({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const employees = renderModel.departmentZones.flatMap((zone) =>
    zone.employeeSlots.map((slot, employeeIndex) => ({
      ...slot,
      zoneIndex: zone.zoneIndex,
      employeeIndex,
      departmentKey: zone.department.department_key,
    })),
  );

  return (
    <div
      className="living-hq-world-workforce"
      aria-label="Canonical miniature workforce integrated into the office world"
      data-presentation-only="true"
      data-presence-claimed="false"
      data-physical-location-claimed="false"
      data-locomotion-allowed="false"
    >
      {employees.map(({ employee, presentation, workItem, zoneIndex, employeeIndex, departmentKey }, index) => {
        const archetype = archetypeFor(employee.position_key, employee.title, employee.department);
        const x = 12 + ((zoneIndex * 23 + employeeIndex * 11 + index * 7) % 72);
        const y = 45 + ((zoneIndex * 13 + employeeIndex * 17 + index * 5) % 34);
        const humanVariant = (zoneIndex + employeeIndex + index) % 6;
        return (
          <div
            key={employee.position_key}
            className="living-hq-world-person"
            data-position-key={employee.position_key}
            data-department-key={departmentKey}
            data-live-semantic-state={employee.semantic_state}
            data-character-state={presentation.state}
            data-character-motion={presentation.motion}
            data-character-archetype={archetype}
            data-human-variant={humanVariant}
            data-work-item-bound={workItem ? "true" : "false"}
            style={{ "--world-person-x": `${x}%`, "--world-person-y": `${y}%` } as CSSProperties}
            title={`${employee.title} · ${presentation.state.replaceAll("_", " ")}`}
          >
            <span className="living-hq-world-desk" aria-hidden="true"><i /><b /><em /></span>
            <span className="living-hq-world-figure" aria-hidden="true">
              <i className="living-hq-world-shadow" />
              <i className="living-hq-world-leg living-hq-world-leg-left" />
              <i className="living-hq-world-leg living-hq-world-leg-right" />
              <i className="living-hq-world-torso" />
              <i className="living-hq-world-shirt" />
              <i className="living-hq-world-jacket living-hq-world-jacket-left" />
              <i className="living-hq-world-jacket living-hq-world-jacket-right" />
              <i className="living-hq-world-arm living-hq-world-arm-left" />
              <i className="living-hq-world-arm living-hq-world-arm-right" />
              <i className="living-hq-world-neck" />
              <i className="living-hq-world-head" />
              <i className="living-hq-world-ear living-hq-world-ear-left" />
              <i className="living-hq-world-ear living-hq-world-ear-right" />
              <i className="living-hq-world-hair" />
              <i className="living-hq-world-face" />
              <i className="living-hq-world-state" />
            </span>
          </div>
        );
      })}
    </div>
  );
}
