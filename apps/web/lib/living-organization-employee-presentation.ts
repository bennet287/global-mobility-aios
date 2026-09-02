import type { LivingSceneEmployee } from "./live-organization";

export type LivingEmployeePresentationState =
  | "focused_work"
  | "blocked_wait"
  | "awaiting_attention"
  | "queued_wait"
  | "settled_idle"
  | "neutral_static";

export type LivingEmployeeMotionMode =
  | "work_pulse"
  | "blocked_pulse"
  | "waiting_breathe"
  | "settled_breathe"
  | "none";

export type LivingEmployeePresentation = {
  state: LivingEmployeePresentationState;
  motion: LivingEmployeeMotionMode;
  presentationOnly: true;
  locomotionAllowed: false;
  presenceClaimed: false;
  canonicalSemanticState: string;
  canonicalPresenceState: string;
  rationale: string;
};

export function deriveLivingEmployeePresentation(
  employee: Pick<LivingSceneEmployee, "semantic_state" | "presence_state">,
): LivingEmployeePresentation {
  const base = {
    presentationOnly: true as const,
    locomotionAllowed: false as const,
    presenceClaimed: false as const,
    canonicalSemanticState: employee.semantic_state,
    canonicalPresenceState: employee.presence_state,
  };

  switch (employee.semantic_state) {
    case "working":
      return {
        ...base,
        state: "focused_work",
        motion: "work_pulse",
        rationale: "Canonical running work may use stationary focused-work motion without asserting presence.",
      };
    case "blocked":
      return {
        ...base,
        state: "blocked_wait",
        motion: "blocked_pulse",
        rationale: "A canonical blocker may use stationary attention motion without inventing a location or blocker.",
      };
    case "awaiting_owner":
      return {
        ...base,
        state: "awaiting_attention",
        motion: "waiting_breathe",
        rationale: "Canonical owner readiness may use restrained waiting motion while remaining Owner-gated.",
      };
    case "queued":
      return {
        ...base,
        state: "queued_wait",
        motion: "waiting_breathe",
        rationale: "Queued canonical work may use stationary waiting motion without claiming active execution.",
      };
    case "completed":
      return {
        ...base,
        state: "settled_idle",
        motion: "settled_breathe",
        rationale: "Completed canonical work may use calm settled motion without implying new work or availability.",
      };
    default:
      return {
        ...base,
        state: "neutral_static",
        motion: "none",
        rationale: "Unknown or unsupported semantic state remains neutral and static.",
      };
  }
}
