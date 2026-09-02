import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildStructuredFlowBaseline,
  evaluateOwnerAnalyticalQuery,
} from "../lib/living-organization-analytics.ts";

const ROOT = "11111111-1111-4111-8111-111111111111";
const CHILD = "22222222-2222-4222-8222-222222222222";

function sceneFixture() {
  return {
    contract_version: "living-organization-scene.v4",
    generated_at: "2026-09-02T01:30:00Z",
    scope: "austria_mobility",
    root_work_item_id: ROOT,
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
      canonical_projection: true,
      authoritative: false,
      departments: [],
      missions: [{
        mission_key: `objective:${ROOT}`,
        objective_key: "austria_rwr_shortage_occupation",
        root_work_item_id: ROOT,
        title: "Austria mobility objective",
        state: "blocked",
        phase_key: "J.1",
        participant_position_keys: ["mobility_operations_lead"],
        work_item_ids: [ROOT, CHILD],
        blocker_count: 1,
        decision_count: 1,
        projection_only: true,
        canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
      }],
      employees: [],
      work_items: [
        {
          work_item_id: ROOT,
          parent_work_item_id: null,
          title: "Austria mobility objective",
          objective_key: "austria_rwr_shortage_occupation",
          phase_key: "J.1",
          status: "running",
          priority: "high",
          risk_level: "R4",
          assigned_position_key: "mobility_operations_lead",
          department: "Global Mobility Operations",
          authority_level: "L4",
          created_at: "2026-09-02T00:00:00Z",
          updated_at: "2026-09-02T01:00:00Z",
          due_at: "2026-09-02T01:00:00Z",
          completed_at: null,
          elapsed_seconds: 5400,
          overdue: true,
        },
        {
          work_item_id: CHILD,
          parent_work_item_id: ROOT,
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
        },
      ],
      conversations: [],
      handoffs: [{
        activity_id: "44444444-4444-4444-8444-444444444444",
        work_item_id: CHILD,
        previous_position_key: "mobility_operations_lead",
        assigned_position_key: "pathway_operations_specialist",
        status: "running",
        occurred_at: "2026-09-02T00:30:00Z",
        causation_activity_id: null,
        canonical_basis: "organization.work.assigned.v1 OrganizationActivity",
      }],
      blockers: [{
        blocker_id: "55555555-5555-4555-8555-555555555555",
        work_item_id: ROOT,
        blocker_type: "human_input",
        title: "Missing employer declaration",
        description: "Declaration required.",
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
      }],
      decisions: [{
        decision_id: "66666666-6666-4666-8666-666666666666",
        decision_key: "board-review",
        title: "Board review",
        question: "Proceed?",
        recommendation: "Inspect evidence.",
        status: "pending_board",
        authority_level: "L4",
        decision_owner_position: "board",
        work_item_id: ROOT,
        evidence_items: [],
        record_fingerprint: null,
        source_object_type: null,
        source_object_id: null,
        source_object_version: null,
        supersedes_decision_id: null,
        superseded_by_decision_id: null,
        is_current: true,
        required_owner_action: true,
        decided_at: null,
      }],
      human_actions: [],
      risk_escalations: [],
      incidents: [],
      smart_objects: [],
      rooms: [],
      relationships: [],
    },
    predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "reserved", items: [] },
    environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "reserved", items: [] },
    truth: {
      canonical_authority: "AIOS canonical records",
      scene_authoritative: false,
      renderer_authoritative: false,
      prediction_authoritative: false,
      environmental_authoritative: false,
      scene_mutations_allowed: false,
    },
  };
}

test("M.7.2 structured FLOW preserves topology semantics and exact attention signals", () => {
  const flow = buildStructuredFlowBaseline(sceneFixture());
  assert.equal(flow.authoritative, false);
  assert.equal(flow.projectionOnly, true);
  assert.equal(flow.workItemCount, 2);
  assert.equal(flow.activeWorkItemCount, 1);
  assert.equal(flow.blockedWorkItemCount, 1);
  assert.equal(flow.ownerAttentionWorkItemCount, 1);
  assert.equal(flow.overdueWorkItemCount, 1);
  assert.equal(flow.parentEdgeCount, 1);
  assert.equal(flow.handoffCount, 1);
  assert.equal(flow.edges[0].sourceWorkItemId, ROOT);
  assert.equal(flow.edges[0].targetWorkItemId, CHILD);
  assert.match(flow.edges[0].canonicalBasis, /topology is not promoted to dependency truth/);
  const root = flow.nodes.find((node) => node.workItemId === ROOT);
  assert.equal(root?.oldestBlockerSeconds, 2700);
  assert.equal(root?.ownerAttentionCount, 1);
});

test("M.7.2 Owner analytical queries return exact matches or explicit unavailable truth", () => {
  const scene = sceneFixture();
  const blocked = evaluateOwnerAnalyticalQuery(scene, "blocked_over_20_minutes");
  assert.equal(blocked.status, "available");
  assert.equal(blocked.count, 1);
  assert.equal(blocked.items[0].id, `objective:${ROOT}`);

  const authority = evaluateOwnerAnalyticalQuery(scene, "owner_authority");
  assert.equal(authority.status, "available");
  assert.equal(authority.count, 1);
  assert.equal(authority.items[0].id, ROOT);
  assert.match(authority.limitation ?? "", /Risk attention alone is not treated as Owner authority/);

  const risk = evaluateOwnerAnalyticalQuery(scene, "r4_r5_work");
  assert.equal(risk.count, 1);
  assert.match(risk.limitation ?? "", /not silently remapped/);

  const overdue = evaluateOwnerAnalyticalQuery(scene, "overdue_work");
  assert.equal(overdue.count, 1);

  for (const key of ["incomplete_evidence", "superseded_this_week", "model_cost_concentration"]) {
    const result = evaluateOwnerAnalyticalQuery(scene, key);
    assert.equal(result.status, "unavailable");
    assert.equal(result.count, null);
    assert.equal(result.items.length, 0);
  }
});
