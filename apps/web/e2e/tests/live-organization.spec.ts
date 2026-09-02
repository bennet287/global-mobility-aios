import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8000";
const LATEST_PATH = "/api/v1/organization/transparency/live-organization/austria/latest";
const SCENE_PATH = "/api/v1/organization/transparency/live-organization/scene/austria/latest";
const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const CONVERSATION_ID = "pathway-evidence-coordination";
const CONVERSATION_ACTIVITY_ID = "33333333-3333-4333-8333-333333333331";
const HANDOFF_ACTIVITY_ID = "44444444-4444-4444-8444-444444444441";
const HANDOFF_CAUSATION_ACTIVITY_ID = "55555555-5555-4555-8555-555555555551";
const OWNER_PATH = `/api/v1/organization/live-organization/austria/${ROOT_ID}/owner-synthesis`;

const CORS_HEADERS = {
  "access-control-allow-credentials": "true",
  "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-origin": "http://127.0.0.1:3000",
  "content-type": "application/json",
};

type JsonResult = {
  status?: number;
  body: unknown;
};

type RecordedRequest = {
  method: string;
  path: string;
  headers: Record<string, string>;
};

type ApiScenario = {
  latest: (call: number) => JsonResult;
  scene?: (call: number) => JsonResult;
  post?: (call: number) => JsonResult;
  firstLatestDelayMs?: number;
};

async function fulfillJson(route: Route, result: JsonResult) {
  await route.fulfill({
    status: result.status ?? 200,
    headers: CORS_HEADERS,
    body: JSON.stringify(result.body),
  });
}

async function installApi(page: Page, scenario: ApiScenario) {
  const recorded: RecordedRequest[] = [];
  let latestCalls = 0;
  let sceneCalls = 0;
  let postCalls = 0;

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "OPTIONS") {
      await route.fulfill({ status: 204, headers: CORS_HEADERS, body: "" });
      return;
    }

    recorded.push({ method, path: url.pathname, headers: request.headers() });

    if (method === "GET" && url.pathname === "/health") {
      await fulfillJson(route, { body: { status: "ok" } });
      return;
    }

    if (method === "GET" && url.pathname === LATEST_PATH) {
      if (latestCalls === 0 && scenario.firstLatestDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, scenario.firstLatestDelayMs));
      }
      const result = scenario.latest(latestCalls);
      latestCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    if (method === "GET" && url.pathname === SCENE_PATH) {
      const result = scenario.scene
        ? scenario.scene(sceneCalls)
        : { body: { established: false, scene: null } };
      sceneCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    if (method === "POST" && url.pathname === OWNER_PATH && scenario.post) {
      const result = scenario.post(postCalls);
      postCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    await fulfillJson(route, {
      status: 404,
      body: { detail: `Unexpected browser test request: ${method} ${url.pathname}` },
    });
  });

  return recorded;
}

function specialist(positionKey: string, index: number) {
  return {
    position_key: positionKey,
    work_item_id: `22222222-2222-4222-8222-22222222222${index}`,
    status: "completed",
    evidence_valid: true,
    evidence_reason: null,
    action_output_id: `output-${index}`,
    execution_attempt_id: `attempt-${index}`,
    agent_run_id: `run-${index}`,
    context_hash: `context-${index}`,
    runtime_binding_hash: `runtime-${index}`,
    latency_ms: 120 + index,
    retry_count: 0,
    confidence: 0.92,
    provider_model_authority: false,
    external_action_authorized: false,
    runtime_quality: {
      contract_version: "austria-live-provider-quality.v1",
      execution_mode: "live_provider",
      provider_outcome: "success",
      configured_provider: "gemini",
      configured_model: "gemini-3.7-flash",
      response_provider: "gemini",
      response_model: "gemini-3.7-flash",
      configured_runtime_matches_binding: true,
      provider_egress_occurred: true,
      fallback_to_template: false,
      prompt_tokens: 800 + index * 10,
      completion_tokens: 200 + index * 10,
      total_tokens: 1000 + index * 20,
      estimated_cost_usd: 0.002 + index * 0.0005,
      grounding_state: "fresh_retrieval",
      evidence_ref_count: 1,
      verified_rule_ref_count: 1,
      source_snapshot_ref_count: 1,
      fresh_retrieval_provenance_present: true,
      provider_model_authority: false,
      warnings: [],
    },
  };
}

function readySnapshot() {
  return {
    generated_at: "2026-08-22T20:00:00Z",
    root_work_item_id: ROOT_ID,
    objective_key: "austria_rwr_shortage_occupation",
    owner_position_key: "mobility_operations_lead",
    root_status: "running",
    cycle_status: "specialists_complete",
    owner_synthesis_state: "pending",
    ready_for_owner_synthesis: true,
    readiness_reasons: [],
    authority_level: "bounded",
    authority_posture: "human_review_gated",
    autonomy_profile_state: null,
    provider_model_authority: false,
    external_action_authorized: false,
    specialist_outputs: [
      specialist("pathway_operations_specialist", 1),
      specialist("regulatory_intelligence_analyst", 2),
    ],
    owner_synthesis: null,
    blockers: [],
    total_latency_ms: 243,
    max_latency_ms: 122,
    total_retry_count: 0,
    activity_count: 0,
    activities: [],
    domain_evidence_refs: [],
    verified_rule_refs: [],
    source_snapshot_refs: [],
  };
}


function livingScene() {
  return {
    established: true,
    scene: {
      contract_version: "living-organization-scene.v5",
      generated_at: "2026-09-02T01:30:00Z",
      scope: "austria_mobility",
      root_work_item_id: ROOT_ID,
      objective_key: "austria_rwr_shortage_occupation",
      coverage: {
        departments: "projected_from_canonical_positions_and_work",
        missions: "workitem_objective_topology_projection",
        conversations: "organization_activity_conversation_lifecycle_v1",
        handoffs: "organization_work_assigned_activity_v1",
        blockers: "organization_blocker_canonical_records",
        human_actions: "organization_human_action_request_open_records",
        risk_escalations: "risk_escalation_open_records",
        incidents: "unavailable_no_canonical_incident_model",
        smart_objects: "m6_read_only_canonical_projections",
        runtime_costs: "unavailable_no_canonical_organization_cost_ledger",
        presence: "not_asserted_m6",
      },
      deterministic: {
        departments: [
          {
            department_key: "Global Mobility Operations",
            label: "Global Mobility Operations",
            employee_count: 3,
            work_item_count: 3,
            active_blocker_count: 0,
            canonical_basis: "OrganizationPosition.department + OrganizationalWorkItem.department",
          },
        ],
        missions: [
          {
            mission_key: `objective:${ROOT_ID}`,
            objective_key: "austria_rwr_shortage_occupation",
            root_work_item_id: ROOT_ID,
            title: "Austria mobility objective",
            state: "ready_for_owner_synthesis",
            phase_key: "J.1",
            participant_position_keys: [
              "mobility_operations_lead",
              "pathway_operations_specialist",
              "regulatory_intelligence_analyst",
            ],
            work_item_ids: [
              ROOT_ID,
              "22222222-2222-4222-8222-222222222221",
              "22222222-2222-4222-8222-222222222222",
            ],
            blocker_count: 0,
            decision_count: 0,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
          },
        ],
        canonical_projection: true,
        authoritative: false,
        employees: [
          {
            position_key: "mobility_operations_lead",
            title: "Mobility Operations Lead",
            department: "Global Mobility Operations",
            reports_to_position_key: "ceo",
            authority_level: "L2",
            organization_status: "active",
            work_item_id: ROOT_ID,
            work_status: "running",
            semantic_state: "awaiting_owner",
            presence_state: "not_asserted",
            state_reason: "Canonical specialist readiness requires the bounded owner step.",
          },
          {
            position_key: "pathway_operations_specialist",
            title: "Pathway Operations Specialist",
            department: "Global Mobility Operations",
            reports_to_position_key: "mobility_operations_lead",
            authority_level: "L1",
            organization_status: "active",
            work_item_id: "22222222-2222-4222-8222-222222222221",
            work_status: "completed",
            semantic_state: "completed",
            presence_state: "not_asserted",
            state_reason: "The canonical WorkItem is completed.",
          },
          {
            position_key: "regulatory_intelligence_analyst",
            title: "Regulatory Intelligence Analyst",
            department: "Global Mobility Operations",
            reports_to_position_key: "mobility_operations_lead",
            authority_level: "L1",
            organization_status: "active",
            work_item_id: "22222222-2222-4222-8222-222222222222",
            work_status: "completed",
            semantic_state: "completed",
            presence_state: "not_asserted",
            state_reason: "The canonical WorkItem is completed.",
          },
        ],
        work_items: [
          {
            work_item_id: ROOT_ID,
            parent_work_item_id: null,
            title: "Austria mobility objective",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1",
            status: "running",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "mobility_operations_lead",
            department: "Global Mobility Operations",
            authority_level: "L2",
            created_at: "2026-09-02T00:00:00Z",
            updated_at: "2026-09-02T01:20:00Z",
            due_at: "2026-09-02T03:00:00Z",
            completed_at: null,
            elapsed_seconds: 5400,
            overdue: false,
            specialist_evidence_valid: null,
            specialist_evidence_reason: null,
          },
          {
            work_item_id: "22222222-2222-4222-8222-222222222221",
            parent_work_item_id: ROOT_ID,
            title: "Pathway analysis",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1.pathway",
            status: "completed",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "pathway_operations_specialist",
            department: "Global Mobility Operations",
            authority_level: "L1",
            created_at: "2026-09-02T00:10:00Z",
            updated_at: "2026-09-02T01:10:00Z",
            due_at: null,
            completed_at: "2026-09-02T01:10:00Z",
            elapsed_seconds: 3600,
            overdue: false,
            specialist_evidence_valid: true,
            specialist_evidence_reason: null,
          },
          {
            work_item_id: "22222222-2222-4222-8222-222222222222",
            parent_work_item_id: ROOT_ID,
            title: "Regulatory analysis",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1.regulatory",
            status: "completed",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "regulatory_intelligence_analyst",
            department: "Global Mobility Operations",
            authority_level: "L1",
            created_at: "2026-09-02T00:15:00Z",
            updated_at: "2026-09-02T01:15:00Z",
            due_at: null,
            completed_at: "2026-09-02T01:15:00Z",
            elapsed_seconds: 3600,
            overdue: false,
            specialist_evidence_valid: true,
            specialist_evidence_reason: null,
          },
        ],
        conversations: [
          {
            conversation_id: CONVERSATION_ID,
            participant_position_keys: [
              "mobility_operations_lead",
              "pathway_operations_specialist",
            ],
            work_item_id: "22222222-2222-4222-8222-222222222221",
            status: "open",
            summary: "Coordinate pathway evidence before owner synthesis.",
            opened_activity_id: CONVERSATION_ACTIVITY_ID,
            latest_activity_id: CONVERSATION_ACTIVITY_ID,
            opened_at: "2026-09-02T01:20:00Z",
            lifecycle_at: "2026-09-02T01:20:00Z",
            authority_effect: "none",
            transcript_persisted: false,
            canonical_basis: "Immutable OrganizationActivity conversation lifecycle",
          },
        ],
        handoffs: [
          {
            activity_id: HANDOFF_ACTIVITY_ID,
            work_item_id: "22222222-2222-4222-8222-222222222221",
            previous_position_key: "mobility_operations_lead",
            assigned_position_key: "pathway_operations_specialist",
            status: "running",
            occurred_at: "2026-09-02T01:25:00Z",
            causation_activity_id: HANDOFF_CAUSATION_ACTIVITY_ID,
            canonical_basis: "organization.work.assigned.v1 OrganizationActivity",
          },
        ],
        blockers: [],
        decisions: [],
        human_actions: [],
        risk_escalations: [],
        incidents: [],
        smart_objects: [
          {
            object_key: `mission-board:${ROOT_ID}`,
            object_type: "mission_board",
            label: "Mission Board",
            state: "ready_for_owner_synthesis",
            metric_label: "WorkItems",
            metric_value: 3,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective topology",
          },
          {
            object_key: `evidence-shelf:${ROOT_ID}`,
            object_type: "evidence_shelf",
            label: "Evidence Shelf",
            state: "empty",
            metric_label: "Evidence + Rules + SourceSnapshots",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Persisted context Evidence, VerifiedRule and SourceSnapshot references",
          },
          {
            object_key: `regulatory-monitor:${ROOT_ID}`,
            object_type: "regulatory_monitor",
            label: "Regulatory Monitor",
            state: "no_snapshot_provenance",
            metric_label: "SourceSnapshot references",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Persisted K.1 context_source_snapshot_refs; does not claim SourceRetrievalRun freshness because K.1 does not persist the retrieval-run reference",
          },
          {
            object_key: `blocker-wall:${ROOT_ID}`,
            object_type: "blocker_wall",
            label: "Blocker Wall",
            state: "clear",
            metric_label: "Canonical blockers",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "OrganizationBlocker canonical records linked to scene WorkItems",
          },
          {
            object_key: `board-desk:${ROOT_ID}`,
            object_type: "board_desk",
            label: "Board Desk",
            state: "quiet",
            metric_label: "Owner decisions",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Current ExecutiveDecision records requiring Board action",
          },
          {
            object_key: `owner-inbox:${ROOT_ID}`,
            object_type: "owner_inbox",
            label: "Owner Inbox",
            state: "clear",
            metric_label: "Human actions + Board risks",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Open OrganizationHumanActionRequest records plus Board-attention RiskEscalation records",
          },
          {
            object_key: `risk-beacon:${ROOT_ID}`,
            object_type: "risk_beacon",
            label: "Risk Beacon",
            state: "clear",
            metric_label: "Open risk escalations",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Open RiskEscalation records linked to scene WorkItems",
          },
          {
            object_key: `immune-center:${ROOT_ID}`,
            object_type: "immune_center",
            label: "Immune Center",
            state: "unavailable",
            metric_label: "Scene-scoped immune state unavailable",
            metric_value: null,
            projection_only: true,
            canonical_basis: "The canonical eligibility immune circuit is aggregate-scoped and is not linked to this Austria WorkItem scene; unrelated immune state is not projected",
          },
          {
            object_key: `model-terminal:${ROOT_ID}`,
            object_type: "model_terminal",
            label: "Model Terminal",
            state: "activity_recorded",
            metric_label: "AgentRun-linked specialists",
            metric_value: 2,
            projection_only: true,
            canonical_basis: "Persisted specialist AgentRun lineage only; provider/model identity has no organizational authority and does not authorize external action",
          },
          {
            object_key: `incident-beacon:${ROOT_ID}`,
            object_type: "incident_beacon",
            label: "Incident Beacon",
            state: "unavailable",
            metric_label: "Canonical Incident model unavailable",
            metric_value: null,
            projection_only: true,
            canonical_basis: "No canonical Incident model is connected in M.6; beacon activity is not fabricated",
          },
          {
            object_key: `cost-display:${ROOT_ID}`,
            object_type: "cost_display",
            label: "Cost Display",
            state: "unavailable",
            metric_label: "Canonical organization cost unavailable",
            metric_value: null,
            projection_only: true,
            canonical_basis: "Runtime telemetry may contain estimates, but no canonical organization cost ledger exists in M.6",
          },
        ],
        rooms: [
          {
            room_key: `mission:${ROOT_ID}`,
            room_type: "mission_room",
            label: "austria_rwr_shortage_occupation",
            state: "ready_for_owner_synthesis",
            metric_label: "WorkItems",
            metric_value: 3,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective topology",
          },
          {
            room_key: `evidence:${ROOT_ID}`,
            room_type: "evidence_lab",
            label: "Evidence Lab",
            state: "empty",
            metric_label: "Evidence + Rules + SourceSnapshots",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Persisted context Evidence, VerifiedRule and SourceSnapshot references",
          },
          {
            room_key: `board:${ROOT_ID}`,
            room_type: "board_room",
            label: "Board Room",
            state: "quiet",
            metric_label: "Board attention items",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "ExecutiveDecision + OrganizationHumanActionRequest + RiskEscalation projections",
          },
        ],
        relationships: [
          {
            relationship_key: "assignment-owner",
            relationship_type: "assigned_to",
            source_type: "employee",
            source_id: "mobility_operations_lead",
            target_type: "work_item",
            target_id: ROOT_ID,
            canonical_basis: "OrganizationalWorkItem.assigned_position_key",
          },
        ],
      },
      predictive: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "reserved_for_m9_phantom_futures",
        items: [],
      },
      environmental: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "reserved_for_m9_environmental_memory",
        items: [],
      },
      truth: {
        canonical_authority: "AIOS canonical records and accepted projections",
        scene_authoritative: false,
        renderer_authoritative: false,
        prediction_authoritative: false,
        environmental_authoritative: false,
        scene_mutations_allowed: false,
      },
    },
  };
}

function analyticalScene() {
  const base = livingScene();
  const scene = base.scene;
  return {
    ...base,
    scene: {
      ...scene,
      deterministic: {
        ...scene.deterministic,
        departments: scene.deterministic.departments.map((department) => ({
          ...department,
          active_blocker_count: 1,
        })),
        missions: scene.deterministic.missions.map((mission) => ({
          ...mission,
          state: "blocked",
          blocker_count: 1,
          decision_count: 3,
        })),
        employees: scene.deterministic.employees.map((employee) =>
          employee.work_item_id === ROOT_ID
            ? {
                ...employee,
                semantic_state: "blocked",
                state_reason: "A canonical active blocker is attached to this WorkItem.",
              }
            : employee,
        ),
        work_items: scene.deterministic.work_items.map((work) => {
          if (work.work_item_id === ROOT_ID) {
            return {
              ...work,
              risk_level: "R4",
              due_at: "2026-09-02T01:00:00Z",
              overdue: true,
            };
          }
          if (work.work_item_id === "22222222-2222-4222-8222-222222222221") {
            return {
              ...work,
              specialist_evidence_valid: false,
              specialist_evidence_reason: "Professional evidence review required.",
            };
          }
          return work;
        }),
        blockers: [
          {
            blocker_id: "77777777-7777-4777-8777-777777777777",
            work_item_id: ROOT_ID,
            blocker_type: "human_input",
            title: "Missing employer declaration",
            description: "Canonical employer declaration evidence is required before the next governed step.",
            severity: "high",
            status: "open",
            accountable_position_key: "mobility_operations_lead",
            decision_id: null,
            risk_escalation_id: null,
            requires_human_action: true,
            opened_at: "2026-09-02T00:45:00Z",
            due_at: "2026-09-02T01:10:00Z",
            open_elapsed_seconds: 2700,
            overdue: true,
          },
        ],
        decisions: [
          {
            decision_id: "88888888-8888-4888-8888-888888888888",
            decision_key: "m7-owner-authority",
            title: "Board review for evidence blocker",
            question: "Should the bounded recommendation advance?",
            recommendation: "Inspect canonical evidence before any external action.",
            status: "pending_board",
            authority_level: "L4",
            decision_owner_position: "board",
            work_item_id: ROOT_ID,
            evidence_items: [{ kind: "m7-proof" }],
            record_fingerprint: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            source_object_type: "organizational_work_item",
            source_object_id: ROOT_ID,
            source_object_version: "m7.3",
            supersedes_decision_id: null,
            superseded_by_decision_id: null,
            is_current: true,
            required_owner_action: true,
            decided_at: null,
            created_at: "2026-09-02T01:00:00Z",
            superseded_by_created_at: null,
            superseded_in_projection_week: false,
          },
          {
            decision_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1",
            decision_key: "m7-historical-routing",
            title: "Historical Austria routing decision",
            question: "Should the prior bounded route remain?",
            recommendation: "Retain until a successor is recorded.",
            status: "approved",
            authority_level: "L4",
            decision_owner_position: "ceo",
            work_item_id: ROOT_ID,
            evidence_items: [],
            record_fingerprint: null,
            source_object_type: "organizational_work_item",
            source_object_id: ROOT_ID,
            source_object_version: "m7.2",
            supersedes_decision_id: null,
            superseded_by_decision_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2",
            is_current: false,
            required_owner_action: false,
            decided_at: "2026-08-30T12:00:00Z",
            created_at: "2026-08-30T11:00:00Z",
            superseded_by_created_at: "2026-09-01T09:00:00Z",
            superseded_in_projection_week: true,
          },
          {
            decision_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2",
            decision_key: "m7-historical-routing-v2",
            title: "Updated Austria routing decision",
            question: "Should the successor route replace the prior version?",
            recommendation: "Use the governed successor.",
            status: "pending_board",
            authority_level: "L4",
            decision_owner_position: "ceo",
            work_item_id: ROOT_ID,
            evidence_items: [],
            record_fingerprint: null,
            source_object_type: "organizational_work_item",
            source_object_id: ROOT_ID,
            source_object_version: "m7.3",
            supersedes_decision_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1",
            superseded_by_decision_id: null,
            is_current: true,
            required_owner_action: false,
            decided_at: null,
            created_at: "2026-09-01T09:00:00Z",
            superseded_by_created_at: null,
            superseded_in_projection_week: false,
          },
        ],
        human_actions: [
          {
            request_id: "99999999-9999-4999-8999-999999999999",
            request_type: "review",
            title: "Review employer declaration",
            instructions: "Inspect the blocker and provide a governed disposition.",
            status: "required",
            priority: "high",
            required_role: "board",
            assigned_human_id: null,
            authority_level: "L4",
            work_item_id: ROOT_ID,
            decision_id: "88888888-8888-4888-8888-888888888888",
            blocker_id: "77777777-7777-4777-8777-777777777777",
            requested_at: "2026-09-02T01:00:00Z",
            due_at: "2026-09-02T02:00:00Z",
            canonical_basis: "OrganizationHumanActionRequest canonical record",
          },
        ],
        risk_escalations: [
          {
            risk_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            risk_key: "m7-board-risk",
            category: "evidence",
            severity: "high",
            title: "Evidence gap requires Board visibility",
            description: "The canonical blocker remains unresolved.",
            status: "open",
            accountable_position_key: "mobility_operations_lead",
            escalated_to_position_key: "board",
            work_item_id: ROOT_ID,
            requires_board_attention: true,
            is_emergency: false,
            evidence_items: [{ kind: "m7-risk-proof" }],
            created_at: "2026-09-02T01:05:00Z",
            canonical_basis: "RiskEscalation canonical record",
          },
        ],
        smart_objects: scene.deterministic.smart_objects.map((item) => {
          if (item.object_type === "blocker_wall") return { ...item, state: "attention", metric_value: 1 };
          if (item.object_type === "board_desk") return { ...item, state: "attention", metric_value: 1 };
          if (item.object_type === "owner_inbox") return { ...item, state: "attention", metric_value: 2 };
          if (item.object_type === "risk_beacon") return { ...item, state: "attention", metric_value: 1 };
          return item;
        }),
        rooms: scene.deterministic.rooms.map((room) =>
          room.room_type === "board_room"
            ? { ...room, state: "attention", metric_value: 3 }
            : room,
        ),
        relationships: [
          ...scene.deterministic.relationships,
          {
            relationship_key: "blocker-root",
            relationship_type: "blocks",
            source_type: "blocker",
            source_id: "77777777-7777-4777-8777-777777777777",
            target_type: "work_item",
            target_id: ROOT_ID,
            canonical_basis: "OrganizationBlocker.work_item_id",
          },
          {
            relationship_key: "decision-root",
            relationship_type: "governs",
            source_type: "decision",
            source_id: "88888888-8888-4888-8888-888888888888",
            target_type: "work_item",
            target_id: ROOT_ID,
            canonical_basis: "ExecutiveDecision.work_item_id",
          },
        ],
      },
    },
  };
}

function completedSnapshot() {
  return {
    ...readySnapshot(),
    generated_at: "2026-08-22T20:01:00Z",
    root_status: "completed",
    cycle_status: "human_review_required",
    owner_synthesis_state: "human_review_required",
    owner_synthesis: {
      action_output_id: "owner-output-1",
      activity_id: "owner-activity-1",
      disposition: "human_review_required",
      recommendation: "Proceed to bounded human review; no external action is authorized.",
      confidence: 0.91,
      total_latency_ms: 243,
      max_latency_ms: 122,
      total_retry_count: 0,
      external_action_authorized: false,
      human_review_required: true,
      completed_at: "2026-08-22T20:01:00Z",
    },
    activity_count: 1,
    activities: [
      {
        activity_id: "owner-activity-1",
        role: "owner",
        physical_activity_class: "material",
        constitutional_activity_class: "material",
        board_inspectable: true,
        activity_type: "owner_synthesis",
        title: "Austria owner synthesis",
        summary: "Bounded owner synthesis persisted for human review.",
        actor_type: "organization_position",
        actor_id: "mobility_operations_lead",
        department: "mobility_operations",
        position_key: "mobility_operations_lead",
        authority_level: "bounded",
        source_object_type: "work_item",
        source_object_id: ROOT_ID,
        source_object_version: null,
        work_item_id: ROOT_ID,
        trace_id: null,
        causation_activity_id: null,
        occurred_at: "2026-08-22T20:01:00Z",
      },
    ],
  };
}

function blockedSnapshot() {
  return {
    ...readySnapshot(),
    cycle_status: "blocked",
    ready_for_owner_synthesis: false,
    readiness_reasons: ["Regulated evidence lineage is incomplete."],
    blockers: [
      {
        blocker_id: "blocker-1",
        work_item_id: ROOT_ID,
        blocker_type: "evidence_lineage",
        severity: "high",
        status: "open",
        title: "Professional evidence review required",
        description: "Regulated evidence lineage has not yet been professionally reviewed.",
        accountable_position_key: "mobility_operations_lead",
        requires_human_action: true,
        created_at: "2026-08-22T20:00:00Z",
      },
    ],
  };
}

function expectHeaderAuth(request: RecordedRequest | undefined) {
  expect(request, "expected browser API request").toBeTruthy();
  expect(request?.headers["x-gmai-role"]).toBe("admin");
  expect(request?.headers["x-gmai-user"]).toBe("frontend-operator");
  expect(request?.headers["content-type"]).toBe("application/json");
}


test("renders M.7.3 evidence and supersession Owner queries without mutating AIOS", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: analyticalScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const sceneSurface = page.locator(".living-scene-shell");
  const lenses = sceneSurface.getByRole("toolbar", { name: "Organization lenses" });

  await Promise.all([
    expect(sceneSurface.getByRole("heading", { name: "Living Organization Scene" })).toBeVisible(),
    expect(sceneSurface.getByText("M.7.3 · Evidence gaps + supersession-time queries")).toBeVisible(),
    expect(lenses.locator('[data-lens-key="organization"]')).toHaveAttribute("aria-pressed", "true"),
    expect(lenses.locator('[data-lens-key="flow"]')).toBeEnabled(),
    expect(lenses.locator('[data-lens-key="cost"]')).toBeDisabled(),
    expect(lenses.locator('[data-lens-key="incident"]')).toBeDisabled(),
    expect(lenses.locator('[data-lens-key="autonomy"]')).toBeDisabled(),
    expect(lenses.locator('[data-lens-key="performance"]')).toBeDisabled(),
  ]);

  await sceneSurface.getByRole("button", { name: "Show routing flow" }).click();
  const flow = sceneSurface.locator('[data-flow-authoritative="false"]');
  await Promise.all([
    expect(sceneSurface).toHaveAttribute("data-active-lens", "flow"),
    expect(flow.getByText("Directed work routing & bottleneck signals", { exact: true })).toBeVisible(),
    expect(flow.getByText("GPU fluid/field TRIAL not promoted", { exact: true })).toBeVisible(),
    expect(flow.locator("[data-flow-work]")).toHaveCount(3),
    expect(flow.getByText("Parent topology · not dependency truth", { exact: true })).toHaveCount(2),
  ]);

  await sceneSurface.getByRole("button", { name: /Show missions blocked >20m/ }).click();
  const blockedQuery = sceneSurface.locator('[data-owner-query-result="blocked_over_20_minutes"]');
  await Promise.all([
    expect(blockedQuery).toHaveAttribute("data-query-status", "available"),
    expect(blockedQuery).toContainText("1 mission"),
    expect(blockedQuery).toContainText("Austria mobility objective"),
  ]);

  await sceneSurface.getByRole("button", { name: /Show work requiring my authority/ }).click();
  const authorityQuery = sceneSurface.locator('[data-owner-query-result="owner_authority"]');
  await Promise.all([
    expect(authorityQuery).toContainText("1 WorkItem"),
    expect(authorityQuery).toContainText("Risk attention alone is not treated as Owner authority"),
  ]);

  await sceneSurface.getByRole("button", { name: /Show incomplete evidence on Austria missions/ }).click();
  const evidenceQuery = sceneSurface.locator('[data-owner-query-result="incomplete_evidence"]');
  await Promise.all([
    expect(evidenceQuery).toHaveAttribute("data-query-status", "partial"),
    expect(evidenceQuery).toContainText("1 specialist WorkItem"),
    expect(evidenceQuery).toContainText("Pathway analysis"),
    expect(evidenceQuery).toContainText("Professional evidence review required"),
  ]);

  await sceneSurface.getByRole("button", { name: /Show decisions superseded this week/ }).click();
  const supersededQuery = sceneSurface.locator('[data-owner-query-result="superseded_this_week"]');
  await Promise.all([
    expect(supersededQuery).toHaveAttribute("data-query-status", "available"),
    expect(supersededQuery).toContainText("1 decision"),
    expect(supersededQuery).toContainText("Historical Austria routing decision"),
    expect(supersededQuery).toContainText("2026-09-01T09:00:00Z"),
  ]);

  await sceneSurface.getByRole("button", { name: /Where is model cost concentrated\?/ }).click();
  const costQuery = sceneSurface.locator('[data-owner-query-result="model_cost_concentration"]');
  await Promise.all([
    expect(costQuery).toHaveAttribute("data-query-status", "unavailable"),
    expect(costQuery).toContainText("Canonical organization cost concentration is unavailable"),
    expect(sceneSurface.getByText("Mission Room", { exact: true })).toBeVisible(),
    expect(sceneSurface.getByText("Evidence Lab", { exact: true }).first()).toBeVisible(),
    expect(sceneSurface.getByText("Board Room", { exact: true }).first()).toBeVisible(),
  ]);

  const smartObjects = sceneSurface.locator('.living-scene-smart-strip[aria-label="Living Organization Smart Objects"]');
  await Promise.all([
    expect(smartObjects.locator("article")).toHaveCount(11),
    expect(smartObjects.locator("article").filter({ hasText: "Cost Display" })).toContainText("Unavailable"),
    expect(sceneSurface.getByText("CANONICAL CONVERSATIONS", { exact: true })).toBeVisible(),
    expect(sceneSurface.getByText("CANONICAL HANDOFFS", { exact: true })).toBeVisible(),
  ]);

  const conversationRecord = sceneSurface.locator(
    `[data-conversation-id="${CONVERSATION_ID}"]`,
  );
  const handoffRecord = sceneSurface.locator(
    `[data-handoff-activity-id="${HANDOFF_ACTIVITY_ID}"]`,
  );
  await Promise.all([
    expect(conversationRecord).toHaveCount(1),
    expect(conversationRecord).toContainText("Coordinate pathway evidence before owner synthesis."),
    expect(conversationRecord).toContainText("Opened Activity 33333333 · Latest Activity 33333333"),
    expect(handoffRecord).toHaveCount(1),
    expect(handoffRecord).toContainText("Mobility Operations Lead ↓ Pathway Operations Specialist"),
    expect(handoffRecord).toContainText("Governed causation 55555555"),
  ]);

  expect(recorded.some((item) => item.method === "GET" && item.path === SCENE_PATH)).toBe(true);
  expect(recorded.some((item) => item.method === "POST")).toBe(false);
});

test("M.7 FLOW field trial defaults off, stays derived, and cannot mutate AIOS", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: analyticalScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const sceneSurface = page.locator(".living-scene-shell");
  await sceneSurface.getByRole("button", { name: "Show routing flow" }).click();

  const stage = sceneSurface.locator(".living-webgpu-stage");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  const trial = stage.locator(".living-flow-trial-console");
  const canvas = stage.locator('[data-testid="living-webgpu-canvas"]');

  await Promise.all([
    expect(trial).toHaveAttribute("data-flow-trial-promotion", "benchmark_required"),
    expect(trial).toHaveAttribute("data-flow-trial-default-prominence", "false"),
    expect(trial.getByText("TRIAL · Iteration 1 · not promoted", { exact: true })).toBeVisible(),
    expect(sceneSurface.getByText("FLOW · maintained structured baseline", { exact: true })).toBeVisible(),
    expect(canvas).toHaveAttribute("data-flow-trial-enabled", "false"),
    expect(canvas).toHaveAttribute("data-flow-trial-promotion-status", "benchmark_required"),
    expect(canvas).toHaveAttribute("data-flow-trial-mutates-work", "false"),
    expect(canvas).toHaveAttribute("data-flow-trial-throughput-claimed", "false"),
    expect(canvas).toHaveAttribute("data-flow-trial-dependency-claimed", "false"),
    expect(canvas).toHaveAttribute("data-flow-trial-node-count", "3"),
    expect(canvas).toHaveAttribute("data-flow-trial-path-count", "2"),
    expect(canvas).toHaveAttribute("data-flow-trial-particle-count", "8"),
  ]);

  await trial.getByRole("button", { name: "Enable GPU field trial" }).click();
  await expect(canvas).toHaveAttribute("data-flow-trial-enabled", "true");
  await trial.getByRole("button", { name: "Structured baseline only" }).click();
  await expect(canvas).toHaveAttribute("data-flow-trial-enabled", "false");

  expect(recorded.some((item) => item.method === "POST")).toBe(false);
});

test("shows loading then truthful empty persisted state", async ({ page }) => {
  const recorded = await installApi(page, {
    firstLatestDelayMs: 400,
    latest: () => ({ body: { established: false, snapshot: null } }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByRole("status").first()).toHaveText("CONNECTING");
  await expect(page.getByRole("heading", { name: "Austria live cycle not yet established" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "No Austria cycle exists yet" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeDisabled();
  await expect(page.getByText("No persisted J/K/L Austria objective is available.", { exact: false })).toBeVisible();

  expectHeaderAuth(recorded.find((item) => item.method === "GET" && item.path === LATEST_PATH));
});

test("executes the bounded owner command and reloads persisted completion", async ({ page }) => {
  let completed = false;
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: completed ? completedSnapshot() : readySnapshot() } }),
    post: () => {
      completed = true;
      return {
        body: {
          root_work_item_id: ROOT_ID,
          action_output_id: "owner-output-1",
          activity_id: "owner-activity-1",
          disposition: "human_review_required",
          replayed: false,
        },
      };
    },
  });

  await page.goto("/cockpit/live-organization");

  const command = page.getByRole("button", { name: "Record bounded owner synthesis" });
  await expect(command).toBeEnabled();
  await expect(page.getByText("Owner synthesis is ready for a Board-authorized command.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Persisted specialist runtime signals" })).toBeVisible();
  await expect(page.getByText("gemini · gemini-3.7-flash").first()).toBeVisible();

  await command.click();

  await expect(page.getByText("The Mobility Operations Lead synthesis was persisted and moved the cycle to human review.")).toBeVisible();
  await expect(page.getByText("Proceed to bounded human review; no external action is authorized.")).toBeVisible();
  await expect(command).toBeDisabled();
  await expect(page.getByText("Human review is required.")).toBeVisible();
  await expect(page.getByText("Not authorized", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Persisted organizational activity" })).toBeVisible();
  await expect(page.getByText("Austria owner synthesis", { exact: true })).toBeVisible();
  await expect(page.getByText("No persisted causation link", { exact: false })).toBeVisible();

  const latestRequest = recorded.find((item) => item.method === "GET" && item.path === LATEST_PATH);
  const postRequest = recorded.find((item) => item.method === "POST" && item.path === OWNER_PATH);
  expectHeaderAuth(latestRequest);
  expectHeaderAuth(postRequest);
});

test("renders blocked readiness without allowing owner synthesis", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: blockedSnapshot() } }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeDisabled();
  await expect(page.getByText("The backend readiness gate has not authorized owner synthesis.")).toBeVisible();
  await expect(page.getByText("Regulated evidence lineage is incomplete.")).toBeVisible();
  await expect(page.getByText("Professional evidence review required")).toBeVisible();
  await expect(page.getByText("human action required", { exact: false })).toBeVisible();
  expect(recorded.some((item) => item.method === "POST")).toBe(false);
});

test("surfaces exact replay without implying duplicate evidence", async ({ page }) => {
  let replayed = false;
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: replayed ? completedSnapshot() : readySnapshot() } }),
    post: () => {
      replayed = true;
      return {
        body: {
          root_work_item_id: ROOT_ID,
          action_output_id: "owner-output-1",
          activity_id: "owner-activity-1",
          disposition: "human_review_required",
          replayed: true,
        },
      };
    },
  });

  await page.goto("/cockpit/live-organization");
  await page.getByRole("button", { name: "Record bounded owner synthesis" }).click();

  await expect(page.getByText("The existing bounded owner synthesis was replayed without creating duplicate evidence.")).toBeVisible();
  const postRequest = recorded.find((item) => item.method === "POST" && item.path === OWNER_PATH);
  expectHeaderAuth(postRequest);
});

test("shows backend projection failure as a visible partial state", async ({ page }) => {
  await installApi(page, {
    latest: () => ({
      status: 503,
      body: { detail: "Transparency projection unavailable" },
    }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByText("Live organization data unavailable.")).toBeVisible();
  await expect(page.getByText("Transparency projection unavailable")).toBeVisible();
  await expect(page.getByRole("status").first()).toHaveText("PARTIAL");
});


test("M.4.0 mounts the optional spatial renderer while Structured remains available", async ({ page }) => {
  await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const stage = page.locator(".living-webgpu-stage");
  await expect(stage).toBeVisible();
  await expect(stage).toHaveAttribute("data-scene-authoritative", "false");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(stage).toHaveAttribute("data-renderer-backend", /^(webgpu|webgl2)$/);

  const canvas = page.getByTestId("living-webgpu-canvas");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-scene-authoritative", "false");
  await expect(canvas).toHaveAttribute("data-renderer-authority", "none");
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");
  await expect(page.getByText("STRUCTURED · permanent product surface", { exact: true })).toBeVisible();
  await expect(page.getByText("Canonical scene reference", { exact: true })).toBeVisible();

  const box = await canvas.boundingBox();
  expect(box).toBeTruthy();
  if (!box) return;
  await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await expect(page.locator(".living-webgpu-overlay strong")).not.toHaveText("No spatial selection");
  await expect(page.locator('.living-webgpu-overlay [data-selection-authority="none"]'))
    .toContainText("Selection changes view focus only; it cannot mutate AIOS.");
});

test("M.4.0 refresh updates projection resources without remounting the GPU renderer", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const stage = page.locator(".living-webgpu-stage");
  const canvas = page.getByTestId("living-webgpu-canvas");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");

  const initialMountGeneration = Number(await canvas.getAttribute("data-renderer-mount-generation"));
  const initialModelRevision = Number(await canvas.getAttribute("data-renderer-model-revision"));
  const initialResourceCount = Number(await canvas.getAttribute("data-renderer-projection-resources"));
  expect(initialMountGeneration).toBeGreaterThanOrEqual(1);
  expect(initialModelRevision).toBeGreaterThanOrEqual(1);
  expect(initialResourceCount).toBeGreaterThan(0);

  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect.poll(
    () => recorded.filter((item) => item.method === "GET" && item.path === SCENE_PATH).length,
  ).toBeGreaterThanOrEqual(2);

  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");
  await expect(canvas).toHaveAttribute("data-renderer-mount-generation", String(initialMountGeneration));
  await expect.poll(async () => Number(await canvas.getAttribute("data-renderer-model-revision")))
    .toBeGreaterThan(initialModelRevision);
  await expect(canvas).toHaveAttribute("data-renderer-projection-resources", String(initialResourceCount));

  const box = await canvas.boundingBox();
  expect(box).toBeTruthy();
  if (!box) return;
  await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await expect(page.locator(".living-webgpu-overlay strong")).not.toHaveText("No spatial selection");
});

test("M.4.0 keeps Structured usable with WebGPU disabled and reports actual WebGL2 backend", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "gpu", {
      configurable: true,
      value: undefined,
    });
  });
  await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  await expect.poll(async () => page.evaluate(() => typeof (navigator as Navigator & { gpu?: unknown }).gpu))
    .toBe("undefined");
  const stage = page.locator(".living-webgpu-stage");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(stage).toHaveAttribute("data-renderer-backend", "webgl2");
  await expect(page.getByText("STRUCTURED · permanent product surface", { exact: true })).toBeVisible();
  await expect(page.getByText("Canonical scene reference", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeEnabled();
});


test("M.4.1 animates canonical work state without inventing presence or locomotion", async ({ page }) => {
  const animatedScene = livingScene();
  if (!animatedScene.scene) throw new Error("expected Living Organization scene fixture");

  animatedScene.scene.deterministic.employees[0].semantic_state = "working";
  animatedScene.scene.deterministic.employees[0].presence_state = "not_asserted";

  await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: animatedScene }),
  });

  await page.goto("/cockpit/live-organization");

  const stage = page.locator(".living-webgpu-stage");
  const canvas = page.getByTestId("living-webgpu-canvas");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(canvas).toHaveAttribute("data-animation-scope", "workspace-representation");
  await expect(canvas).toHaveAttribute("data-locomotion-enabled", "false");
  await expect(canvas).toHaveAttribute("data-presence-claimed", "false");
  await expect(canvas).toHaveAttribute("data-presentation-modes", /focused_work/);
  await expect(canvas).toHaveAttribute("data-animation-proof", "motion-observed", { timeout: 5_000 });
  await expect(page.getByText(/M\.4\.1 motion discipline is preserved: presence and locomotion are not asserted/)).toBeVisible();
});
