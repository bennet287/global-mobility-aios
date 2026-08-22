import { CLIENT_API_CONFIG } from "./client-api-config.ts";
import { createApiFetch } from "./request-client.mjs";

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

export type AustriaOwnerSynthesisCommand = {
  root_work_item_id: string;
  action_output_id: string;
  activity_id: string;
  disposition: string;
  replayed: boolean;
};

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
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function getLatestAustriaLiveOrganization(): Promise<AustriaLiveOrganizationLatest> {
  return liveRequest<AustriaLiveOrganizationLatest>(
    "/api/v1/organization/transparency/live-organization/austria/latest",
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
