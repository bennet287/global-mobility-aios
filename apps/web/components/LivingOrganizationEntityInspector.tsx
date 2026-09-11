import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import type { LivingSceneSelection } from "../lib/living-organization-renderer-policy";

type InspectorModel = {
  eyebrow: string;
  title: string;
  primary: string;
  secondary: string;
  basis: string;
};

function format(value: string): string {
  return value.replaceAll("_", " ");
}

function buildInspectorModel(
  selection: LivingSceneSelection | null,
  renderModel: LivingSceneRenderModel,
): InspectorModel {
  if (!selection) {
    return {
      eyebrow: "Spatial entity focus · view only",
      title: "Select an HQ entity to inspect its governed projection.",
      primary: `${renderModel.departmentZones.length} departments · ${renderModel.employeeSlots.length} AI positions`,
      secondary: `${renderModel.smartObjects.length} smart objects · pointer selection can inspect a department, AI position, chamber, or smart object without claiming presence or authority.`,
      basis: "Selection is local presentation state derived from the existing governed render-model projection.",
    };
  }

  if (selection.entityType === "department") {
    const zone = renderModel.departmentZones.find(({ department }) => department.department_key === selection.entityKey);
    return {
      eyebrow: "Department projection · view only",
      title: selection.label,
      primary: zone ? `${zone.department.employee_count} employees · ${zone.department.work_item_count} work items` : "Department projection unavailable",
      secondary: zone ? `${zone.department.active_blocker_count} active blockers` : "No additional projected context",
      basis: zone?.department.canonical_basis ?? "Selection references the governed department projection.",
    };
  }

  if (selection.entityType === "employee") {
    const slot = renderModel.employeeSlots.find(({ employee }) => employee.position_key === selection.entityKey);
    return {
      eyebrow: "AI position projection · view only",
      title: slot?.employee.title ?? selection.label,
      primary: slot ? `${format(slot.employee.semantic_state)} semantic state · ${format(slot.presentation.state)} presentation state` : "Position projection unavailable",
      secondary: slot?.workItem ? `${slot.workItem.title} · ${format(slot.workItem.status)}` : "No WorkItem projected for this position · no physical presence claim",
      basis: slot?.presentation.rationale ?? "Selection references the governed employee presentation mapping and does not assert physical presence.",
    };
  }

  if (selection.entityType === "room") {
    const rooms = [renderModel.missionRoom, renderModel.evidenceLab, renderModel.boardRoom].filter(Boolean);
    const room = rooms.find((candidate) => candidate?.room_key === selection.entityKey) ?? null;
    return {
      eyebrow: "Chamber projection · view only",
      title: selection.label,
      primary: room ? `${format(room.state)} · ${room.metric_label}: ${room.metric_value}` : "Room projection unavailable",
      secondary: "Governed scene data only · not occupancy evidence.",
      basis: room?.canonical_basis ?? "Selection references the governed room projection.",
    };
  }

  const object = renderModel.smartObjects.find((candidate) => candidate.object_key === selection.entityKey);
  return {
    eyebrow: "Smart-object projection · view only",
    title: selection.label,
    primary: object ? `${format(object.state)} · ${format(object.object_type)}` : "Smart-object projection unavailable",
    secondary: object?.metric_value == null ? "No projected metric · presentation object creates no operational authority" : `${object.metric_label}: ${object.metric_value} · presentation object creates no operational authority`,
    basis: object?.canonical_basis ?? "Selection references the governed smart-object projection.",
  };
}

export function LivingOrganizationEntityInspector({
  selection,
  renderModel,
}: {
  selection: LivingSceneSelection | null;
  renderModel: LivingSceneRenderModel;
}) {
  const model = buildInspectorModel(selection, renderModel);

  return (
    <aside
      className="living-hq-entity-inspector"
      aria-label="Living HQ entity inspector"
      data-selection-state={selection ? "selected" : "none"}
      data-presentation-only="true"
      data-authority="none"
      data-presence-claimed="false"
    >
      <div className="living-hq-entity-inspector-heading">
        <span>{model.eyebrow}</span>
        <strong>{model.title}</strong>
      </div>
      <div className="living-hq-entity-inspector-context">
        <p>{model.primary}</p>
        <small>{model.secondary}</small>
      </div>
      <div className="living-hq-entity-inspector-basis">
        <span>Governed basis</span>
        <small>{model.basis}</small>
      </div>
      <footer>
        <span>Selection contract · department / employee / room / smart_object</span>
        <span>Presentation only · no authority</span>
      </footer>
    </aside>
  );
}
