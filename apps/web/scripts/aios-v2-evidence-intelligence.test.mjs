import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  activityDestination,
  buildV2EvidenceWorkspace,
  buildV2IntelligenceModel,
  evidenceDestination,
  selectEvidenceReference,
  selectRecentChange,
} from "../lib/v2/evidence-intelligence.ts";
import { navigationCommands, ownerNavigation } from "../lib/v2/navigation.ts";

const snapshot = () => ({
  generated_at: "2026-09-06T02:00:00Z",
  root_work_item_id: "work:root",
  objective_key: "fixture",
  owner_position_key: "ceo",
  root_status: "running",
  cycle_status: "running",
  owner_synthesis_state: "pending",
  ready_for_owner_synthesis: false,
  readiness_reasons: [],
  authority_level: "L3",
  authority_posture: "recorded",
  autonomy_profile_state: null,
  provider_model_authority: false,
  external_action_authorized: false,
  specialist_outputs: [
    { position_key: "regulatory", work_item_id: "work:reg", status: "completed", evidence_valid: true, evidence_reason: "fixture", action_output_id: null, execution_attempt_id: null, agent_run_id: null, context_hash: null, runtime_binding_hash: null, latency_ms: 10, retry_count: 0, confidence: null, provider_model_authority: false, external_action_authorized: false, runtime_quality: { contract_version: "v1", execution_mode: "fixture", provider_outcome: "ok", configured_provider: null, configured_model: null, response_provider: null, response_model: null, configured_runtime_matches_binding: null, provider_egress_occurred: null, fallback_to_template: false, prompt_tokens: null, completion_tokens: null, total_tokens: null, estimated_cost_usd: null, grounding_state: "grounded", evidence_ref_count: 2, verified_rule_ref_count: 1, source_snapshot_ref_count: 1, fresh_retrieval_provenance_present: true, provider_model_authority: false, warnings: [] } },
  ],
  owner_synthesis: null,
  blockers: [], total_latency_ms: 10, max_latency_ms: 10, total_retry_count: 0, activity_count: 0, activities: [],
  domain_evidence_refs: ["evidence:a", "evidence:b"],
  verified_rule_refs: ["rule:a"],
  source_snapshot_refs: ["snapshot:a"],
});

const ownerData = () => ({
  loadedAt: "2026-09-06T02:01:00Z",
  partial: true,
  unavailableSources: ["Board packet"],
  attention: [{ id: "event:1", kind: "blocker", title: "Blocked filing", detail: "high blocker", urgency: "high", href: "/cross-department-friction", occurredAt: null, canonicalBasis: "Blocker:1" }],
  missions: [],
  recentChanges: [{ id: "activity:1", title: "Assignment recorded", summary: "Recorded assignment change", occurredAt: "2026-09-06T02:00:00Z", activityClass: "work_assignment", department: "Operations", positionKey: "ops" }],
  organization: { established: true, generatedAt: "2026-09-06T02:00:00Z", scope: "fixture", contractVersion: "v5", sceneAuthoritative: false, rendererAuthoritative: false, mutationsAllowed: false, canonicalAuthority: "fixture", missions: [], zones: [{ wingKey: "operations", label: "Operations", departments: [], employeeRosterCount: 0, workItemCount: 0, activeBlockerCount: 2 }], employeeRosterCount: 0, departmentCount: 1, missionCount: 3, coverage: null },
  boardGeneratedAt: null,
});

const memory = () => ({
  contract_version: "memory.v1", generated_at: "2026-09-06T02:02:00Z", scope: "fixture", root_work_item_id: "work:root", objective_key: "fixture", source_contract_version: "replay.v1",
  canonical_projection: true, authoritative: false, predictive: false, mutations_allowed: false, visualization_only: true,
  window_event_count: 9, window_start: "2026-09-05T00:00:00Z", window_end: "2026-09-06T00:00:00Z",
  coverage: { activity_history_basis: "fixture", activity_history_established: true, activity_history_coverage_start: "2026-09-05T00:00:00Z", pre_epoch_history: "partial", bounded_replay_window: "fixture", replay_truncated: false, path_history: "covered" },
  kind_aggregates: [{ event_kind: "handoff", event_count: 4 }],
  path_frequencies: [{ previous_position_key: "regulatory", assigned_position_key: "ops", handoff_count: 2, work_item_count: 2, first_occurred_at: "2026-09-05T00:00:00Z", last_occurred_at: "2026-09-06T00:00:00Z", coverage_state: "covered" }],
  heat_cells: [{ department: "Operations", event_kind: "handoff", event_count: 2, covered_event_count: 2 }],
  timeline: [{ bucket_start: "2026-09-06T00:00:00Z", event_count: 9, handoff_count: 2, blocker_count: 1, decision_count: 1, conversation_count: 0, coverage_state: "covered" }],
  unsupported_dimensions: ["presence"],
});

test("Q6 Evidence preserves exact reference identities and supplied specialist validity", () => {
  const model = buildV2EvidenceWorkspace(snapshot());
  assert.equal(model.domainEvidenceCount, 2);
  assert.equal(model.verifiedRuleCount, 1);
  assert.equal(model.sourceSnapshotCount, 1);
  assert.deepEqual(model.references.map((item) => item.id), ["evidence:a", "evidence:b", "rule:a", "snapshot:a"]);
  assert.equal(model.specialists[0].evidenceValid, true);
  assert.equal(model.specialists[0].groundingState, "grounded");
  assert.equal(model.externalActionAuthorized, false);
});

test("Q6 Evidence selection and destinations preserve opaque identities", () => {
  const model = buildV2EvidenceWorkspace(snapshot());
  assert.equal(selectEvidenceReference(model.references, "verified_rule", "rule:a")?.id, "rule:a");
  assert.equal(selectEvidenceReference(model.references, "verified_rule", "missing"), null);
  const opaque = { kind: "source_snapshot", id: "snapshot:AT /?x=#y" };
  const url = new URL(evidenceDestination(opaque), "http://test");
  assert.equal(url.searchParams.get("kind"), opaque.kind);
  assert.equal(url.searchParams.get("ref"), opaque.id);
});

test("Q6 Intelligence keeps current governed reads separate from non-authoritative aggregate memory", () => {
  const model = buildV2IntelligenceModel(ownerData(), memory());
  assert.equal(model.current?.attentionCount, 1);
  assert.equal(model.current?.missionCount, 3);
  assert.equal(model.current?.departmentBlockerCount, 2);
  assert.equal(model.current?.recentActivityCount, 1);
  assert.equal(model.memory?.windowEventCount, 9);
  assert.equal(model.memory?.predictive, false);
  assert.equal(model.memory?.authoritative, false);
  assert.equal(model.memory?.visualizationOnly, true);
  assert.equal(model.memory?.pathFrequencies[0].handoff_count, 2);
});

test("Q6 Activity selection is exact and search destinations do not create a fetch path", () => {
  const changes = ownerData().recentChanges;
  assert.equal(selectRecentChange(changes, "activity:1")?.title, "Assignment recorded");
  assert.equal(selectRecentChange(changes, "missing"), null);
  assert.equal(new URL(activityDestination("activity:/?#1"), "http://test").searchParams.get("activity"), "activity:/?#1");
});

test("Q6 keeps Intelligence and Evidence enabled as Decisions is introduced while History remains fail-closed", () => {
  for (const [label, href] of [["Intelligence", "/cockpit/v2/intelligence"], ["Evidence", "/cockpit/v2/evidence"]]) {
    const item = ownerNavigation.find((candidate) => candidate.label === label);
    assert.equal(item?.enabled, true);
    assert.equal(item?.href, href);
    assert.equal(navigationCommands.filter((command) => command.href === href).length, 1);
  }
  const history = ownerNavigation.find((candidate) => candidate.label === "History");
  assert.equal(history?.enabled, false);
  assert.equal(history?.href, null);
});

test("Q6 uses existing read-only endpoints and keeps search registration loaded-record only", () => {
  const evidenceHook = readFileSync(new URL("../hooks/useV2EvidenceSnapshot.ts", import.meta.url), "utf8");
  const memoryHook = readFileSync(new URL("../hooks/useV2EnvironmentalMemory.ts", import.meta.url), "utf8");
  const evidenceComponent = readFileSync(new URL("../components/v2/V2EvidenceWorkspace.tsx", import.meta.url), "utf8");
  const intelligenceComponent = readFileSync(new URL("../components/v2/V2IntelligenceWorkspace.tsx", import.meta.url), "utf8");
  assert.match(evidenceHook, /getLatestAustriaLiveOrganization/);
  assert.match(memoryHook, /getLatestAustriaOrganizationEnvironmentalMemory/);
  assert.match(intelligenceComponent, /useV2OwnerOrganization/);
  assert.match(evidenceComponent + intelligenceComponent, /useV2SearchItems/);
  assert.doesNotMatch(evidenceComponent + intelligenceComponent, /\b(POST|PUT|PATCH|DELETE)\b/);
  assert.doesNotMatch(evidenceComponent + intelligenceComponent, /fetch\(/);
  assert.match(intelligenceComponent, /not physical movement/i);
  assert.match(evidenceComponent, /No source text, approval, freshness or legal conclusion is inferred/);
});

test("Q6 source contract is wired into the design-foundation gate", () => {
  const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8");
  assert.match(packageJson, /scripts\/aios-v2-evidence-intelligence\.test\.mjs/);
});
