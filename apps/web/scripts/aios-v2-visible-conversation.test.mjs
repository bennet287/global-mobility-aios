import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  V2_CANONICAL_CONVERSATION_COVERAGE,
  buildV2VisibleConversations,
  summarizeV2VisibleConversations,
  visibleConversationsForPosition,
  visibleConversationsForWorkItem,
} from "../lib/v2/visible-conversation.ts";

function employee(position_key, work_item_id = null) {
  return {
    position_key,
    title: position_key.toUpperCase(),
    department: "Technology",
    reports_to_position_key: null,
    authority_level: "operational",
    organization_status: "active",
    work_item_id,
    work_status: "running",
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "canonical fixture",
  };
}

function workItem(overrides = {}) {
  return {
    work_item_id: "work-1",
    parent_work_item_id: null,
    title: "Verify governed mobility evidence",
    objective_key: "objective-1",
    phase_key: null,
    status: "running",
    priority: "normal",
    risk_level: "low",
    assigned_position_key: "cto",
    department: "Technology",
    authority_level: "operational",
    created_at: "2026-09-07T14:00:00Z",
    updated_at: "2026-09-07T15:00:00Z",
    due_at: null,
    completed_at: null,
    elapsed_seconds: 3600,
    overdue: false,
    specialist_evidence_valid: null,
    specialist_evidence_reason: null,
    ...overrides,
  };
}

function conversation(overrides = {}) {
  return {
    conversation_id: "conversation-1",
    participant_position_keys: ["cto", "regulatory_lead"],
    work_item_id: "work-1",
    status: "open",
    summary: "CTO and regulatory lead reviewed the governed evidence boundary.",
    opened_activity_id: "activity-open",
    latest_activity_id: "activity-open",
    opened_at: "2026-09-07T15:00:00Z",
    lifecycle_at: "2026-09-07T15:00:00Z",
    authority_effect: "none",
    transcript_persisted: false,
    canonical_basis: "organization_activity_conversation_lifecycle_v1",
    ...overrides,
  };
}

const employees = [
  employee("cto", "work-1"),
  employee("regulatory_lead", "work-2"),
];
const workItems = [workItem(), workItem({ work_item_id: "work-2", assigned_position_key: "regulatory_lead" })];

test("Phase 7D accepts only the canonical conversation lifecycle coverage adapter", () => {
  assert.equal(
    V2_CANONICAL_CONVERSATION_COVERAGE,
    "organization_activity_conversation_lifecycle_v1",
  );
  for (const coverageState of ["unavailable", "partial", "covered", ""]) {
    const result = buildV2VisibleConversations({
      conversations: [conversation()],
      employees,
      workItems,
      coverageState,
    });
    assert.equal(result.supported, false);
    assert.deepEqual(result.items, []);
  }
});

test("Phase 7D preserves exact participant and WorkItem conversation truth", () => {
  const result = buildV2VisibleConversations({
    conversations: [conversation()],
    employees,
    workItems,
    coverageState: V2_CANONICAL_CONVERSATION_COVERAGE,
  });

  assert.equal(result.supported, true);
  assert.equal(result.items.length, 1);
  assert.deepEqual(result.items[0].participantPositionKeys, ["cto", "regulatory_lead"]);
  assert.equal(result.items[0].workItemId, "work-1");
  assert.equal(result.items[0].authorityEffect, "none");
  assert.equal(result.items[0].transcriptPersisted, false);
  assert.equal(result.items[0].truth.speechClaimed, false);
  assert.equal(result.items[0].truth.physicalPresenceClaimed, false);
  assert.equal(result.items[0].truth.authorityOutcomeClaimed, false);
  assert.equal(result.items[0].truth.canonicalMutationAllowed, false);
});

test("Phase 7D fails closed on unknown participant, missing WorkItem, or assigned-position mismatch", () => {
  const fixtures = [
    conversation({ participant_position_keys: ["cto", "unknown_position"] }),
    conversation({ work_item_id: "missing-work" }),
    conversation({ participant_position_keys: ["regulatory_lead", "ceo"] }),
  ];

  for (const candidate of fixtures) {
    const result = buildV2VisibleConversations({
      conversations: [candidate],
      employees: [...employees, employee("ceo", null)],
      workItems,
      coverageState: V2_CANONICAL_CONVERSATION_COVERAGE,
    });
    assert.deepEqual(result.items, []);
  }
});

test("Phase 7D rejects records that overclaim authority or transcript persistence", () => {
  for (const candidate of [
    conversation({ authority_effect: "decision" }),
    conversation({ transcript_persisted: true }),
  ]) {
    const result = buildV2VisibleConversations({
      conversations: [candidate],
      employees,
      workItems,
      coverageState: V2_CANONICAL_CONVERSATION_COVERAGE,
    });
    assert.deepEqual(result.items, []);
  }
});

test("Phase 7D selectors retain exact position and WorkItem relations", () => {
  const result = buildV2VisibleConversations({
    conversations: [conversation()],
    employees,
    workItems,
    coverageState: V2_CANONICAL_CONVERSATION_COVERAGE,
  });

  assert.equal(visibleConversationsForPosition(result, "cto").length, 1);
  assert.equal(visibleConversationsForPosition(result, "ceo").length, 0);
  assert.equal(visibleConversationsForWorkItem(result, "work-1").length, 1);
  assert.equal(visibleConversationsForWorkItem(result, "work-2").length, 0);
  assert.equal(summarizeV2VisibleConversations(result, "cto")?.label, "1 governed conversation open");
});

test("Phase 7D visible surfaces preserve anti-overclaim language", () => {
  const inspector = readFileSync(
    new URL("../components/v2/V2EmployeeInspector.tsx", import.meta.url),
    "utf8",
  );
  const missionRoom = readFileSync(
    new URL("../components/v2/V2MissionRoomPanel.tsx", import.meta.url),
    "utf8",
  );
  const inspectorModel = readFileSync(
    new URL("../lib/v2/mission-room-inspector.ts", import.meta.url),
    "utf8",
  );

  assert.match(inspector, /data-live-speech-claimed="false"/);
  assert.match(inspector, /data-transcript-claimed="false"/);
  assert.match(inspector, /Authority effect: none · transcript not persisted/);
  assert.match(missionRoom, /will not infer dialogue or participation from unrelated activity/);
  assert.match(missionRoom, /Conversation coverage:/);
  assert.match(inspectorModel, /buildV2VisibleConversations/);
});
