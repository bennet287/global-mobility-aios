import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";

function shortPosition(value: string): string {
  return value.replaceAll("_", " ");
}

export function LivingOrganizationFlagshipRoster({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  return (
    <section
      className="living-hq-department-deck"
      aria-labelledby="living-hq-department-deck-title"
      data-presentation-only="true"
      data-presence-claimed="false"
      data-locomotion-allowed="false"
    >
      <header>
        <div>
          <span>HQ presentation layer · canonical state mapped</span>
          <strong id="living-hq-department-deck-title" role="heading" aria-level={4}>Department character deck</strong>
        </div>
        <small>{renderModel.departmentZones.length} departments · {renderModel.employeeSlots.length} AI positions</small>
      </header>

      <div className="living-hq-department-grid">
        {renderModel.departmentZones.map((zone) => (
          <article
            key={zone.department.department_key}
            className="living-hq-department-pod"
            data-department-key={zone.department.department_key}
          >
            <header>
              <div className="living-hq-department-mark" aria-hidden="true" />
              <div>
                <strong>{zone.department.label}</strong>
                <small>{zone.employeeSlots.length} positions · {zone.workItems.length} work items</small>
              </div>
            </header>

            <div className="living-hq-character-row" role="list" aria-label={`${zone.department.label} AI positions`}>
              {zone.employeeSlots.map(({ employee, presentation }, employeeIndex) => (
                <div
                  key={employee.position_key}
                  className="living-hq-character"
                  data-character-state={presentation.state}
                  data-character-motion={presentation.motion}
                  data-character-variant={String((employeeIndex + zone.zoneIndex) % 4)}
                  role="listitem"
                  title={presentation.rationale}
                >
                  <div className="living-hq-character-figure" aria-hidden="true">
                    <i className="living-hq-character-aura" />
                    <i className="living-hq-character-chair" />
                    <i className="living-hq-character-body" />
                    <i className="living-hq-character-head" />
                    <i className="living-hq-character-hair" />
                    <i className="living-hq-character-visor" />
                    <i className="living-hq-character-console" />
                  </div>
                  <div className="living-hq-character-copy">
                    <strong>{employee.title}</strong>
                    <span>{shortPosition(employee.position_key)}</span>
                    <small>{presentation.state.replaceAll("_", " ")}</small>
                  </div>
                </div>
              ))}
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
        Miniature figures are stationary presentation cues derived from canonical semantic state. They do not assert physical presence,
        locomotion, conversation, availability, or new work beyond the scene contract.
      </footer>
    </section>
  );
}
