import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import type { LivingSceneSelection } from "../lib/living-organization-renderer-policy";

type InspectorModel = {
  eyebrow: string;
  title: string;
  primary: string;
  secondary: string;
  basis: string;
  lineage: string;
  evidence: string;
  authority: string;
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
      lineage: "No entity selected · no canonical lineage implied by scene focus.",
      evidence: "No evidence context selected.",
      authority: "View only · no command boundary crossed.",
    };
  }

  if (selection.entityType === "department") {
    const zone = renderModel.departmentZones.find(({ department }) => department.department_key === selection.entityKey);
    const currentWork = zone?.workItems.filter((item) => item.status !== "completed") ?? [];
    const evidenceValid = zone?.workItems.filter((item) => item.specialist_evidence_valid === true).length ?? 0;
    return {
      eyebrow: "Department projection · view only",
      title: selection.label,
      primary: zone ? `${zone.department.employee_count} employees · ${zone.department.work_item_count} work items` : "Department projection unavailable",
      secondary: zone ? `${zone.department.active_blocker_count} active blockers` : "No additional projected context",
      basis: zone?.department.canonical_basis ?? "Selection references the governed department projection.",
      lineage: zone ? `${currentWork.length} non-completed WorkItems remain in this department projection.` : "Department WorkItem lineage unavailable.",
      evidence: zone ? `${evidenceValid}/${zone.workItems.length} projected WorkItems carry specialist evidence-valid state.` : "Department evidence context unavailable.",
      authority: "Department focus does not assign work, change ownership, or grant authority.",
    };
  }

  if (selection.entityType === "employee") {
    const slot = renderModel.employeeSlots.find(({ employee }) => employee.position_key === selection.entityKey);
    const workItem = slot?.workItem ?? null;
    return {
      eyebrow: "AI position projection · view only",
      title: slot?.employee.title ?? selection.label,
      primary: slot ? `${format(slot.employee.semantic_state)} semantic state · ${format(slot.presentation.state)} presentation state` : "Position projection unavailable",
      secondary: workItem ? `${workItem.title} · ${format(workItem.status)}` : "No WorkItem projected for this position · no physical presence claim",
      basis: slot?.presentation.rationale ?? "Selection references the governed employee presentation mapping and does not assert physical presence.",
      lineage: workItem ? `WorkItem ${workItem.work_item_id} · parent ${workItem.parent_work_item_id ?? "root"} · ${workItem.objective_key ?? "no objective key"}` : "No WorkItem lineage projected for this AI position.",
      evidence: workItem?.specialist_evidence_valid == null ? "Specialist evidence validity not established in this projection." : workItem.specialist_evidence_valid ? "Specialist evidence validity is projected as valid." : `Specialist evidence validity is not valid${workItem.specialist_evidence_reason ? ` · ${workItem.specialist_evidence_reason}` : ""}.`,
      authority: slot ? `${slot.employee.authority_level} employee authority · WorkItem ${workItem?.authority_level ?? "authority unavailable"}` : "Authority context unavailable.",
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
      lineage: room ? `Room key ${room.room_key} · type ${format(room.room_type)}.` : "Room lineage unavailable.",
      evidence: room?.room_type === "evidence_lab" ? "Evidence Lab metrics summarize governed scene projection; they do not create or certify evidence." : "No evidence claim is created by chamber selection.",
      authority: room?.room_type === "board_room" ? "Board-room focus exposes governance context only; it does not constitute Board action." : "Chamber focus has no operational authority.",
    };
  }

  const object = renderModel.smartObjects.find((candidate) => candidate.object_key === selection.entityKey);
  return {
    eyebrow: "Smart-object projection · view only",
    title: selection.label,
    primary: object ? `${format(object.state)} · ${format(object.object_type)}` : "Smart-object projection unavailable",
    secondary: object?.metric_value == null ? "No projected metric · presentation object creates no operational authority" : `${object.metric_label}: ${object.metric_value} · presentation object creates no operational authority`,
    basis: object?.canonical_basis ?? "Selection references the governed smart-object projection.",
    lineage: object ? `Object key ${object.object_key} · projection_only=${String(object.projection_only)}.` : "Smart-object lineage unavailable.",
    evidence: "Smart-object metrics are presentation of governed projection data, not evidence artifacts.",
    authority: "Smart-object focus cannot invoke tools, mutate work, or grant authority.",
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
      <div className="living-hq-entity-inspector-drilldown" aria-label="Contextual drill-down" data-read-only="true">
        <div>
          <span>Lineage</span>
          <small>{model.lineage}</small>
        </div>
        <div>
          <span>Evidence posture</span>
          <small>{model.evidence}</small>
        </div>
        <div>
          <span>Authority boundary</span>
          <small>{model.authority}</small>
        </div>
      </div>
      <footer>
        <span>Selection contract · department / employee / room / smart_object</span>
        <span>Presentation only · no authority</span>
        <span>Contextual drill-down · read only</span>
      </footer>
    </aside>
  );
}
