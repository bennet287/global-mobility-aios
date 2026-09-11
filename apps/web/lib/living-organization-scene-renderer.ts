import type {
  LivingOrganizationScene,
  LivingSceneBlocker,
  LivingSceneConversation,
  LivingSceneDecision,
  LivingSceneDepartment,
  LivingSceneEmployee,
  LivingSceneHandoff,
  LivingSceneHumanActionRequest,
  LivingSceneMission,
  LivingSceneRiskEscalation,
  LivingSceneRoom,
  LivingSceneSmartObject,
  LivingSceneWorkItem,
} from "./live-organization";
import {
  deriveLivingEmployeePresentation,
  type LivingEmployeePresentation,
} from "./living-organization-employee-presentation";
import { buildStructuredFlowBaseline } from "./living-organization-analytics";
import {
  buildFlowFieldTrialModel,
  type FlowFieldTrialModel,
} from "./living-organization-flow-trial";

export const LIVING_SCENE_RENDERER_TARGET = "three-webgpu";

export type LivingSceneEmployeeSlot = {
  employee: LivingSceneEmployee;
  workItem: LivingSceneWorkItem | null;
  presentation: LivingEmployeePresentation;
  slot: number;
};

export type LivingSceneDepartmentZone = {
  department: LivingSceneDepartment;
  zoneIndex: number;
  employeeSlots: LivingSceneEmployeeSlot[];
  workItems: LivingSceneWorkItem[];
};

export type LivingSceneRenderModel = {
  contractVersion: string;
  rendererTarget: typeof LIVING_SCENE_RENDERER_TARGET;
  sceneAuthoritative: false;
  missionRoom: LivingSceneRoom | null;
  evidenceLab: LivingSceneRoom | null;
  boardRoom: LivingSceneRoom | null;
  smartObjects: LivingSceneSmartObject[];
  handoffs: LivingSceneHandoff[];
  conversations: LivingSceneConversation[];
  missions: LivingSceneMission[];
  blockers: LivingSceneBlocker[];
  decisions: LivingSceneDecision[];
  humanActions: LivingSceneHumanActionRequest[];
  riskEscalations: LivingSceneRiskEscalation[];
  employeeSlots: LivingSceneEmployeeSlot[];
  departmentZones: LivingSceneDepartmentZone[];
  flowTrial: FlowFieldTrialModel;
};

export function buildLivingSceneRenderModel(scene: LivingOrganizationScene): LivingSceneRenderModel {
  const workById = new Map(scene.deterministic.work_items.map((item) => [item.work_item_id, item]));
  const room = (roomType: string) => scene.deterministic.rooms.find((item) => item.room_type === roomType) ?? null;
  const employeeSlots = scene.deterministic.employees.map((employee, index) => ({
    employee,
    workItem: employee.work_item_id ? workById.get(employee.work_item_id) ?? null : null,
    presentation: deriveLivingEmployeePresentation(employee),
    slot: index,
  }));

  const departmentZones = [...scene.deterministic.departments]
    .sort((left, right) => left.department_key.localeCompare(right.department_key))
    .map((department, zoneIndex) => ({
      department,
      zoneIndex,
      employeeSlots: employeeSlots.filter(({ employee }) => employee.department === department.department_key),
      workItems: scene.deterministic.work_items.filter((workItem) => workItem.department === department.department_key),
    }));

  const flowBaseline = buildStructuredFlowBaseline(scene);

  return {
    contractVersion: scene.contract_version,
    rendererTarget: LIVING_SCENE_RENDERER_TARGET,
    sceneAuthoritative: false,
    missionRoom: room("mission_room"),
    evidenceLab: room("evidence_lab"),
    boardRoom: room("board_room"),
    smartObjects: scene.deterministic.smart_objects,
    handoffs: scene.deterministic.handoffs,
    conversations: scene.deterministic.conversations,
    missions: scene.deterministic.missions,
    blockers: scene.deterministic.blockers,
    decisions: scene.deterministic.decisions,
    humanActions: scene.deterministic.human_actions,
    riskEscalations: scene.deterministic.risk_escalations,
    employeeSlots,
    departmentZones,
    flowTrial: buildFlowFieldTrialModel(flowBaseline),
  };
}
