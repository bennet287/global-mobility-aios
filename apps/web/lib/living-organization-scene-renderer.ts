import type {
  LivingOrganizationScene,
  LivingSceneDepartment,
  LivingSceneEmployee,
  LivingSceneRoom,
  LivingSceneSmartObject,
  LivingSceneWorkItem,
} from "./live-organization";
import {
  deriveLivingEmployeePresentation,
  type LivingEmployeePresentation,
} from "./living-organization-employee-presentation";

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
  employeeSlots: LivingSceneEmployeeSlot[];
  departmentZones: LivingSceneDepartmentZone[];
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

  return {
    contractVersion: scene.contract_version,
    rendererTarget: LIVING_SCENE_RENDERER_TARGET,
    sceneAuthoritative: false,
    missionRoom: room("mission_room"),
    evidenceLab: room("evidence_lab"),
    boardRoom: room("board_room"),
    smartObjects: scene.deterministic.smart_objects,
    employeeSlots,
    departmentZones,
  };
}
