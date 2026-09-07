import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  V2_CANONICAL_HUMAN_ACTION_COVERAGE,
  V2_CANONICAL_RISK_ESCALATION_COVERAGE,
  buildV2VisibleOwnerBoardEscalations,
  visibleOwnerBoardEscalationsForPosition,
} from "../lib/v2/visible-owner-board-escalation.ts";

function employee(position_key, title = position_key.toUpperCase()) {
  return {
    position_key,
    title,
    department: "Executive",
    reports_to_position_key: null,
    authority_level: "executive",
    organization_status: "active",
    work_item_id: null,
    work_status: null,
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "canonical fixture",
  };
}

function decision(overrides = {}) {
  return {
    decision_id: "decision-1",
    decision_key: "decision-key-1",
    title: "Approve governed route",
    question: "Proceed?",
    recommendation: "Review evidence before deciding.",
    status: "pending_board",
    authority_level: "board",
    decision_owner_position: "board",
    work_item_id: "work-1",
    evidence_items: [],
    record_fingerprint: "fingerprint",
    source_object_type: "work_item",
    source_object_id: "work-1",
    source_object_version: "1",
    supersedes_decision_id: null,
    superseded_by_decision_id: null,
    is_current: true,
    required_owner_action: true,
    decided_at: null,
    created_at: "2026-09-07T20:00:00Z",
    superseded_by_created_at: null,
    superseded_in_projection_week: false,
    ...overrides,
  };
}

function humanAction(overrides = {}) {
  return {
    request_id: "request-1",
    request_type: "review",
    title: "Owner review required",
    instructions: "Review the canonical evidence bundle.",
    status: "required",
    priority: "high",
    required_role: "owner",
    assigned_human_id: null,
    authority_level: "owner",
    work_item_id: "work-1",
    decision_id: "decision-1",
    blocker_id: null,
    requested_at: "2026-09-07T20:05:00Z",
    due_at: null,
    canonical_basis: "OrganizationHumanActionRequest canonical record",
    ...overrides,
  };
}

function risk(overrides = {}) {
  return {
    risk_id: "risk-1",
    risk_key: "risk-key-1",
    category: "governance",
    severity: "high",
    title: "Board attention required",
    description: "Canonical risk requires explicit Board attention.",
    status: "open",
    accountable_position_key: "ceo",
    escalated_to_position_key: "board",
    work_item_id: "work-1",
    requires_board_attention: true,
    is_emergency: false,
    evidence_items: [],
    created_at: "2026-09-07T20:10:00Z",
    canonical_basis: "RiskEscalation canonical record linked to scene WorkItem",
    ...overrides,
  };
}

const employees = [employee("ceo", "Chief Executive Officer")];

function projection(overrides = {}) {
  return buildV2VisibleOwnerBoardEscalations({
    decisions: [decision()],
    humanActions: [humanAction()],
    riskEscalations: [risk()],
    employees,
    humanActionCoverageState: V2_CANONICAL_HUMAN_ACTION_COVERAGE,
    riskEscalationCoverageState: V2_CANONICAL_RISK_ESCALATION_COVERAGE,
    ...overrides,
  });
}

test("Phase 7F accepts only exact human-action and risk-escalation coverage", () => {
  assert.equal(
    V2_CANONICAL_HUMAN_ACTION_COVERAGE,
    "organization_human_action_request_open_records",
  );
  assert.equal(V2_CANONICAL_RISK_ESCALATION_COVERAGE, "risk_escalation_open_records");

  const humanGap = projection({ humanActionCoverageState: "unavailable" });
  assert.equal(humanGap.humanActionCoverageSupported, false);
  assert.deepEqual(humanGap.humanActions, []);
  assert.equal(humanGap.boardAttentionCount, null);

  const riskGap = projection({ riskEscalationCoverageState: "partial" });
  assert.equal(riskGap.riskEscalationCoverageSupported, false);
  assert.deepEqual(riskGap.riskEscalations, []);
  assert.equal(riskGap.boardAttentionCount, null);
});

test("Phase 7F preserves three distinct canonical attention classes", () => {
  const result = projection();
  assert.equal(result.decisionAttention.length, 1);
  assert.equal(result.humanActions.length, 1);
  assert.equal(result.riskEscalations.length, 1);
  assert.equal(result.boardAttentionCount, 3);
  assert.equal(result.decisionAttention[0].canonicalBasis, "ExecutiveDecision.required_owner_action");
  assert.equal(result.humanActions[0].requiredRole, "owner");
  assert.equal(result.riskEscalations[0].requiresBoardAttention, true);
  assert.equal(result.riskEscalations[0].accountablePositionKey, "ceo");
  assert.equal(result.riskEscalations[0].escalatedToPositionKey, "board");
});

test("Phase 7F does not infer Board attention from risk severity", () => {
  const result = projection({
    decisions: [],
    humanActions: [],
    riskEscalations: [risk({ severity: "critical", requires_board_attention: false })],
  });
  assert.equal(result.boardAttentionCount, 0);
  assert.equal(result.riskEscalations[0].severity, "critical");
  assert.equal(result.riskEscalations[0].requiresBoardAttention, false);
});

test("Phase 7F binds risk routing only to unique exact roster position keys", () => {
  const result = projection();
  assert.equal(result.riskEscalations[0].accountableParticipant?.title, "Chief Executive Officer");
  assert.equal(result.riskEscalations[0].escalatedToParticipant, null);
  assert.equal(visibleOwnerBoardEscalationsForPosition(result, "ceo").length, 1);
  assert.equal(visibleOwnerBoardEscalationsForPosition(result, "board").length, 1);

  const ambiguous = projection({
    employees: [employee("ceo", "CEO A"), employee("ceo", "CEO B")],
  });
  assert.equal(ambiguous.riskEscalations[0].accountableParticipant, null);
});

test("Phase 7F ignores decisions that do not carry exact required_owner_action evidence", () => {
  const result = projection({
    decisions: [
      decision({ required_owner_action: false }),
      decision({ decision_id: "decision-2", is_current: false }),
    ],
    humanActions: [],
    riskEscalations: [],
  });
  assert.deepEqual(result.decisionAttention, []);
  assert.equal(result.boardAttentionCount, 0);
});

test("Phase 7F anti-overclaim contract forbids meeting, approval, presence and locomotion claims", () => {
  const result = projection();
  assert.equal(result.truth.attentionEvidenceClaimed, true);
  assert.equal(result.truth.boardMeetingClaimed, false);
  assert.equal(result.truth.approvalClaimed, false);
  assert.equal(result.truth.physicalPresenceClaimed, false);
  assert.equal(result.truth.physicalLocationClaimed, false);
  assert.equal(result.truth.locomotionClaimed, false);
  assert.equal(result.truth.canonicalMutationAllowed, false);

  const signal = readFileSync(
    new URL("../components/v2/V2CanonicalOwnerBoardEscalationSignal.tsx", import.meta.url),
    "utf8",
  );
  assert.match(signal, /data-board-meeting-claimed="false"/);
  assert.match(signal, /data-approval-claimed="false"/);
  assert.match(signal, /no Board meeting · no approval inferred · no physical presence or room attendance/);
});
