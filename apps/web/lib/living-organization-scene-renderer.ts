import type {
  LivingOrganizationScene,
  LivingSceneEmployee,
  LivingSceneRoom,
  LivingSceneWorkItem,
} from "./live-organization";

export const LIVING_SCENE_RENDERER_TARGET = "three-webgpu";

export type LivingSceneEmployeeSlot = {
  employee: LivingSceneEmployee;
  workItem: LivingSceneWorkItem | null;
  slot: number;
};

export type LivingSceneRenderModel = {
  contractVersion: string;
  rendererTarget: typeof LIVING_SCENE_RENDERER_TARGET;
  sceneAuthoritative: false;
  missionRoom: LivingSceneRoom | null;
  evidenceLab: LivingSceneRoom | null;
  boardRoom: LivingSceneRoom | null;
  employeeSlots: LivingSceneEmployeeSlot[];
};

export function buildLivingSceneRenderModel(scene: LivingOrganizationScene): LivingSceneRenderModel {
  const workById = new Map(scene.deterministic.work_items.map((item) => [item.work_item_id, item]));
  const room = (roomType: string) => scene.deterministic.rooms.find((item) => item.room_type === roomType) ?? null;

  return {
    contractVersion: scene.contract_version,
    rendererTarget: LIVING_SCENE_RENDERER_TARGET,
    sceneAuthoritative: false,
    missionRoom: room("mission_room"),
    evidenceLab: room("evidence_lab"),
    boardRoom: room("board_room"),
    employeeSlots: scene.deterministic.employees.map((employee, index) => ({
      employee,
      workItem: employee.work_item_id ? workById.get(employee.work_item_id) ?? null : null,
      slot: index,
    })),
  };
}
