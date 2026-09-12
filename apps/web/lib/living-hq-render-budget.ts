import type { LivingSceneRenderModel } from "./living-organization-scene-renderer";

export type LivingHQRenderDetail = "full" | "balanced" | "compact";
export type LivingHQMotionBudget = "full" | "canonical-only" | "critical-only";

export type LivingHQRenderBudget = {
  detail: LivingHQRenderDetail;
  motion: LivingHQMotionBudget;
  employeeCount: number;
  departmentCount: number;
  rationale: string;
};

export function deriveLivingHQRenderBudget(renderModel: LivingSceneRenderModel): LivingHQRenderBudget {
  const employeeCount = renderModel.employeeSlots.length;
  const departmentCount = renderModel.departmentZones.length;
  const complexityScore = employeeCount + departmentCount * 2;

  if (complexityScore > 56 || employeeCount > 40) {
    return {
      detail: "compact",
      motion: "critical-only",
      employeeCount,
      departmentCount,
      rationale: "Large canonical scene: preserve every employee and state signal while reducing decorative detail and ambient motion.",
    };
  }

  if (complexityScore > 30 || employeeCount > 22) {
    return {
      detail: "balanced",
      motion: "canonical-only",
      employeeCount,
      departmentCount,
      rationale: "Medium canonical scene: preserve state-driven motion while reducing nonessential character detail.",
    };
  }

  return {
    detail: "full",
    motion: "full",
    employeeCount,
    departmentCount,
    rationale: "Small canonical scene: full miniature detail fits the bounded presentation budget.",
  };
}
