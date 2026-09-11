import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

function shortPosition(value: string): string {
  return value.replaceAll("_", " ");
}

function characterArchetype(positionKey: string, title: string, department: string): string {
  const haystack = `${positionKey} ${title} ${department}`.toLowerCase();
  if (/ceo|chief executive/.test(haystack)) return "executive";
  if (/cto|engineering|architect|developer|technology|security|ciso|soc/.test(haystack)) return "technology";
  if (/legal|regulat|evidence|compliance|counsel|policy|immigration/.test(haystack)) return "evidence";
  if (/operations|coo|coordination|readiness|document/.test(haystack)) return "operations";
  if (/finance|cfo|account|financial/.test(haystack)) return "finance";
  if (/human|hr|recruit|culture|chro/.test(haystack)) return "people";
  if (/product|design|creative|marketing|sales|comms|cpo|cmo/.test(haystack)) return "product";
  return "specialist";
}

function accessoryFor(archetype: string): string {
  switch (archetype) {
    case "executive": return "brief";
    case "technology": return "headset";
    case "evidence": return "folio";
    case "operations": return "tablet";
    case "finance": return "ledger";
    case "people": return "notebook";
    case "product": return "sketch";
    default: return "badge";
  }
}

export function LivingOrganizationFlagshipRoster({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  return (
    <section
      className="living-hq-department-deck living-hq-workforce"
      aria-labelledby="living-hq-department-deck-title"
      data-presentation-only="true"
      data-presence-claimed="false"
      data-locomotion-allowed="false"
      data-workforce-art="integrated-miniatures"
    >
      <header>
        <div>
          <span>Live workforce projection · canonical state mapped</span>
          <strong id="living-hq-department-deck-title" role="heading" aria-level={4}>Miniature workforce</strong>
        </div>
        <small>{renderModel.departmentZones.length} departments · {renderModel.employeeSlots.length} AI positions</small>
      </header>

      <div className="living-hq-workforce-neighborhoods">
        {renderModel.departmentZones.map((zone) => (
          <article
            key={zone.department.department_key}
            className="living-hq-workforce-neighborhood"
            data-department-key={zone.department.department_key}
          >
            <header>
              <i className="living-hq-workforce-department-light" aria-hidden="true" />
              <div>
                <strong>{zone.department.label}</strong>
                <small>{zone.employeeSlots.length} positions · {zone.workItems.length} WorkItems</small>
              </div>
            </header>

            <div className="living-hq-workforce-floor" role="list" aria-label={`${zone.department.label} AI positions`}>
              {zone.employeeSlots.map(({ employee, presentation, workItem }, employeeIndex) => {
                const archetype = characterArchetype(employee.position_key, employee.title, employee.department);
                return (
                  <div
                    key={employee.position_key}
                    className="living-hq-workforce-person"
                    data-character-state={presentation.state}
                    data-character-motion={presentation.motion}
                    data-character-archetype={archetype}
                    data-character-variant={String((employeeIndex + zone.zoneIndex) % 5)}
                    data-work-item-bound={workItem ? "true" : "false"}
                    role="listitem"
                    title={presentation.rationale}
                  >
                    <div className="living-hq-workforce-scene" aria-hidden="true">
                      <i className="living-hq-workforce-desk" />
                      <i className="living-hq-workforce-monitor" />
                      <i className="living-hq-workforce-seat" />
                      <div className="living-hq-workforce-figure">
                        <i className="living-hq-workforce-shadow" />
                        <i className="living-hq-workforce-leg living-hq-workforce-leg-left" />
                        <i className="living-hq-workforce-leg living-hq-workforce-leg-right" />
                        <i className="living-hq-workforce-torso" />
                        <i className="living-hq-workforce-arm living-hq-workforce-arm-left" />
                        <i className="living-hq-workforce-arm living-hq-workforce-arm-right" />
                        <i className="living-hq-workforce-head" />
                        <i className="living-hq-workforce-hair" />
                        <i className="living-hq-workforce-face" />
                        <i className={`living-hq-workforce-accessory living-hq-workforce-accessory-${accessoryFor(archetype)}`} />
                      </div>
                      <i className="living-hq-workforce-state-beacon" />
                    </div>
                    <div className="living-hq-workforce-label">
                      <strong>{employee.title}</strong>
                      <span>{shortPosition(employee.position_key)}</span>
                      <small>{presentation.state.replaceAll("_", " ")}{workItem ? ` · ${workItem.status.replaceAll("_", " ")}` : ""}</small>
                    </div>
                  </div>
                );
              })}
              {!zone.employeeSlots.length ? (
                <div className="living-hq-character-empty">
                  <strong>No projected positions</strong>
                  <small>Canonical scene has no employees mapped to this department.</small>
                </div>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      <footer>
        Miniature employees are differentiated presentation figures bound to canonical employee and WorkItem state. Placement does not assert physical presence or location; locomotion remains disallowed, and conversation or handoff behavior appears only when governed records support it.
      </footer>
    </section>
  );
}
