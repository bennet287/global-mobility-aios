import { CLIENT_API_CONFIG } from "./client-api-config.ts";
import { createApiFetch } from "./request-client.mjs";

export type AustriaLiveRuntimeQuality = {
  contract_version: string;
  execution_mode: string;
  provider_outcome: string;
  configured_provider: string | null;
  configured_model: string | null;
  response_provider: string | null;
  response_model: string | null;
  configured_runtime_matches_binding: boolean | null;
  provider_egress_occurred: boolean | null;
  fallback_to_template: boolean;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  estimated_cost_usd: number | null;
  grounding_state: string;
  evidence_ref_count: number;
  verified_rule_ref_count: number;
  source_snapshot_ref_count: number;
  fresh_retrieval_provenance_present: boolean;
  provider_model_authority: boolean;
  warnings: string[];
};

export type AustriaLiveSpecialist = {
  position_key: string;
  work_item_id: string;
  status: string;
  evidence_valid: boolean;
  evidence_reason: string | null;
  action_output_id: string | null;
  execution_attempt_id: string | null;
  agent_run_id: string | null;
  context_hash: string | null;
  runtime_binding_hash: string | null;
  latency_ms: number | null;
  retry_count: number | null;
  confidence: number | null;
  provider_model_authority: boolean;
  external_action_authorized: boolean;
  runtime_quality: AustriaLiveRuntimeQuality | null;
};

export type AustriaLiveBlocker = {
  blocker_id: string;
  work_item_id: string | null;
  blocker_type: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  accountable_position_key: string | null;
  requires_human_action: boolean;
  created_at: string;
};

export type AustriaOwnerSynthesis = {
  action_output_id: string;
  activity_id: string;
  disposition: string;
  recommendation: string;
  confidence: number;
  total_latency_ms: number;
  max_latency_ms: number;
  total_retry_count: number;
  external_action_authorized: boolean;
  human_review_required: boolean;
  completed_at: string | null;
};

export type AustriaLiveActivity = {
  activity_id: string;
  role: string;
  physical_activity_class: string;
  constitutional_activity_class: string | null;
  board_inspectable: boolean;
  activity_type: string;
  title: string;
  summary: string;
  actor_type: string;
  actor_id: string;
  department: string | null;
  position_key: string | null;
  authority_level: string | null;
  source_object_type: string;
  source_object_id: string;
  source_object_version: string | null;
  work_item_id: string | null;
  trace_id: string | null;
  causation_activity_id: string | null;
  occurred_at: string;
};

export type AustriaLiveOrganizationSnapshot = {
  generated_at: string;
  root_work_item_id: string;
  objective_key: string;
  owner_position_key: string;
  root_status: string;
  cycle_status: string;
  owner_synthesis_state: string;
  ready_for_owner_synthesis: boolean;
  readiness_reasons: string[];
  authority_level: string;
  authority_posture: string;
  autonomy_profile_state: string | null;
  provider_model_authority: boolean;
  external_action_authorized: boolean;
  specialist_outputs: AustriaLiveSpecialist[];
  owner_synthesis: AustriaOwnerSynthesis | null;
  blockers: AustriaLiveBlocker[];
  total_latency_ms: number;
  max_latency_ms: number;
  total_retry_count: number;
  activity_count: number;
  activities: AustriaLiveActivity[];
  domain_evidence_refs: string[];
  verified_rule_refs: string[];
};

export type AustriaLiveOrganizationLatest = {
  established: boolean;
  snapshot: AustriaLiveOrganizationSnapshot | null;
};



export type LivingSceneEmployee = {
  position_key: string;
  title: string;
  department: string;
  reports_to_position_key: string | null;
  authority_level: string;
  organization_status: string;
  work_item_id: string | null;
  work_status: string | null;
  semantic_state: string;
  presence_state: string;
  state_reason: string;
};

export type LivingSceneDepartment = {
  department_key: string;
  label: string;
  employee_count: number;
  work_item_count: number;
  active_blocker_count: number;
  canonical_basis: string;
};

export type LivingSceneMission = {
  mission_key: string;
  objective_key: string;
  root_work_item_id: string;
  title: string;
  state: string;
  phase_key: string | null;
  participant_position_keys: string[];
  work_item_ids: string[];
  blocker_count: number;
  decision_count: number;
  projection_only: boolean;
  canonical_basis: string;
};

export type LivingSceneConversation = {
  conversation_id: string;
  participant_position_keys: string[];
  work_item_id: string;
  status: string;
  summary: string;
  opened_activity_id: string;
  latest_activity_id: string;
  opened_at: string;
  lifecycle_at: string;
  authority_effect: string;
  transcript_persisted: boolean;
  canonical_basis: string;
};

export type LivingSceneHandoff = {
  activity_id: string;
  work_item_id: string;
  previous_position_key: string;
  assigned_position_key: string;
  status: string;
  occurred_at: string;
  causation_activity_id: string | null;
  canonical_basis: string;
};

export type LivingSceneIncident = {
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  work_item_id: string | null;
};

export type LivingSceneSmartObject = {
  object_key: string;
  object_type: string;
  label: string;
  state: string;
  metric_label: string;
  metric_value: number;
  projection_only: boolean;
  canonical_basis: string;
};

export type LivingSceneCoverage = {
  departments: string;
  missions: string;
  conversations: string;
  handoffs: string;
  incidents: string;
  smart_objects: string;
  presence: string;
};

export type LivingSceneWorkItem = {
  work_item_id: string;
  parent_work_item_id: string | null;
  title: string;
  objective_key: string | null;
  phase_key: string | null;
  status: string;
  priority: string;
  risk_level: string;
  assigned_position_key: string;
  department: string;
  authority_level: string;
};

export type LivingSceneBlocker = {
  blocker_id: string;
  work_item_id: string | null;
  title: string;
  severity: string;
  status: string;
  requires_human_action: boolean;
};

export type LivingSceneDecision = {
  decision_id: string;
  decision_key: string;
  title: string;
  status: string;
  authority_level: string;
  decision_owner_position: string;
  work_item_id: string | null;
  supersedes_decision_id: string | null;
  superseded_by_decision_id: string | null;
  is_current: boolean;
  decided_at: string | null;
};

export type LivingSceneRoom = {
  room_key: string;
  room_type: "mission_room" | "evidence_lab" | "board_room" | string;
  label: string;
  state: string;
  metric_label: string;
  metric_value: number;
  projection_only: boolean;
  canonical_basis: string;
};

export type LivingSceneRelationship = {
  relationship_key: string;
  relationship_type: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  canonical_basis: string;
};

export type LivingSceneDeterministicPlane = {
  canonical_projection: boolean;
  authoritative: boolean;
  departments: LivingSceneDepartment[];
  missions: LivingSceneMission[];
  employees: LivingSceneEmployee[];
  work_items: LivingSceneWorkItem[];
  conversations: LivingSceneConversation[];
  handoffs: LivingSceneHandoff[];
  blockers: LivingSceneBlocker[];
  decisions: LivingSceneDecision[];
  incidents: LivingSceneIncident[];
  smart_objects: LivingSceneSmartObject[];
  rooms: LivingSceneRoom[];
  relationships: LivingSceneRelationship[];
};

export type LivingSceneNonCanonicalPlane = {
  enabled: boolean;
  canonical_projection: boolean;
  authoritative: boolean;
  status: string;
  items: Record<string, unknown>[];
};

export type LivingSceneTruthPosture = {
  canonical_authority: string;
  scene_authoritative: boolean;
  renderer_authoritative: boolean;
  prediction_authoritative: boolean;
  environmental_authoritative: boolean;
  scene_mutations_allowed: boolean;
};

export type LivingOrganizationScene = {
  contract_version: string;
  generated_at: string;
  scope: string;
  root_work_item_id: string;
  objective_key: string;
  coverage: LivingSceneCoverage;
  deterministic: LivingSceneDeterministicPlane;
  predictive: LivingSceneNonCanonicalPlane;
  environmental: LivingSceneNonCanonicalPlane;
  truth: LivingSceneTruthPosture;
};

export type LivingOrganizationSceneLatest = {
  established: boolean;
  scene: LivingOrganizationScene | null;
};

export type AustriaOwnerSynthesisCommand = {
  root_work_item_id: string;
  action_output_id: string;
  activity_id: string;
  disposition: string;
  replayed: boolean;
};

export class LiveOrganizationRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "LiveOrganizationRequestError";
    this.status = status;
  }
}

const apiFetch = createApiFetch(CLIENT_API_CONFIG);

async function liveRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string" && body.detail.trim()) detail = body.detail;
    } catch {
      // Preserve the status-based fallback when a proxy or server returns non-JSON.
    }
    throw new LiveOrganizationRequestError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export async function getLatestAustriaLiveOrganization(): Promise<AustriaLiveOrganizationLatest> {
  return liveRequest<AustriaLiveOrganizationLatest>(
    "/api/v1/organization/transparency/live-organization/austria/latest",
  );
}



export async function getLatestAustriaLivingScene(): Promise<LivingOrganizationSceneLatest> {
  return liveRequest<LivingOrganizationSceneLatest>(
    "/api/v1/organization/transparency/live-organization/scene/austria/latest",
  );
}

export async function synthesizeAustriaOwner(
  rootWorkItemId: string,
): Promise<AustriaOwnerSynthesisCommand> {
  return liveRequest<AustriaOwnerSynthesisCommand>(
    `/api/v1/organization/live-organization/austria/${encodeURIComponent(rootWorkItemId)}/owner-synthesis`,
    { method: "POST" },
  );
}
