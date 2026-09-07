import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  V2_CANONICAL_CONVERSATION_COVERAGE,
  buildV2VisibleConversations,
} from "../lib/v2/visible-conversation.ts";
import {
  V2_CANONICAL_MISSION_COVERAGE,
  buildV2VisibleMissionCollaborations,
  visibleMissionCollaborationsForMission,
  visibleMissionCollaborationsForPosition,
} from "../lib/v2/visible-mission-collaboration.ts";

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
    title: "Coordinate governed mobility evidence",
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

function mission(overrides = {}) {
  return {
    mission_key: "objective:root-1",
    objective_key: "objective-1",
    root_work_item_id: "root-1",
    title: "Austria mobility readiness",
    state: "running",
    phase_key: null,
    participant_position_keys: ["cto", "regulatory_lead", "ceo"],
    work_item_ids: ["root-1", "work-1", "work-2"],
    blocker_count: 0,
    decision_count: 0,
    projection_only: true,
    canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
    ...overrides,
  };
}

function conversation(overrides = {}) {
  return {
    conversation_id: "conversation-1",
    participant_position_keys: ["cto", "regulatory_lead"],
    work_item_id: "work-1",
    status: "open",
    summary: "CTO and regulatory lead coordinated the governed evidence boundary.",
    opened_activity_id: "activity-open",
    latest_activity_id: "activity-open",
    opened_at: "2026-09-07T15:00:00Z",
    lifecycle_at: "2026-09-07T15:00:00Z",
    authority_effect: "none",
    transcript_persisted: false,
    canonical_basis: V2_CANONICAL_CONVERSATION_COVERAGE,
    ...overrides,
  };
}

const employees = [
  employee("cto", "work-1"),
  employee("regulatory_lead", "work-2"),
  employee("ceo", "root-1"),
];
const workItems = [
  workItem({ work_item_id: "root-1", assigned_position_key: "ceo" }),
  workItem(),
  workItem({ work_item_id: "work-2", assigned_position_key: "regulatory_lead" }),
];

function conversationProjection(overrides = {}) {
  return buildV2VisibleConversations({
    conversations: [conversation()],
    employees,
    workItems,
    coverageState: V2_CANONICAL_CONVERSATION_COVERAGE,
    ...overrides,
  });
}

test("Phase 7E accepts only the exact Mission topology coverage", () => {
  assert.equal(V2_CANONICAL_MISSION_COVERAGE, "workitem_objective_topology_projection");
  for (const missionCoverageState of ["unavailable", "partial", "canonical", ""]) {
    const result = buildV2VisibleMissionCollaborations({
      missions: [mission()],
      conversations: conversationProjection(),
      missionCoverageState,
    });
    assert.equal(result.supported, false);
    assert.deepEqual(result.items, []);
  }
});

test("Phase 7E derives governed coordination from exact conversation participants inside one Mission", () => {
  const result = buildV2VisibleMissionCollaborations({
    missions: [mission()],
    conversations: conversationProjection(),
    missionCoverageState: V2_CANONICAL_MISSION_COVERAGE,
  });

  assert.equal(result.supported, true);
  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].missionKey, "objective:root-1");
  assert.equal(result.items[0].workItemId, "work-1");
  assert.deepEqual(result.items[0].participantPositionKeys, ["cto", "regulatory_lead"]);
  assert.equal(result.items[0].participantPositionKeys.includes("ceo"), false);
  assert.equal(result.items[0].truth.missionProjectionOnly, true);
  assert.equal(result.items[0].truth.governedCoordinationClaimed, true);
  assert.equal(result.items[0].truth.activeCollaborationClaimed, false);
  assert.equal(result.items[0].truth.liveSpeechClaimed, false);
  assert.equal(result.items[0].truth.physicalPresenceClaimed, false);
  assert.equal(result.items[0].truth.completionClaimed, false);
});

test("Phase 7E does not promote topology-only Mission membership into collaboration", () => {
  const result = buildV2VisibleMissionCollaborations({
    missions: [mission()],
    conversations: conversationProjection(),
    missionCoverageState: V2_CANONICAL_MISSION_COVERAGE,
  });

  assert.equal(visibleMissionCollaborationsForPosition(result, "cto").length, 1);
  assert.equal(visibleMissionCollaborationsForPosition(result, "regulatory_lead").length, 1);
  assert.equal(visibleMissionCollaborationsForPosition(result, "ceo").length, 0);
  assert.equal(visibleMissionCollaborationsForMission(result, "objective:root-1").length, 1);
});

test("Phase 7E fails closed when one WorkItem maps to multiple Missions", () => {
  const result = buildV2VisibleMissionCollaborations({
    missions: [
      mission(),
      mission({
        mission_key: "objective:root-2",
        objective_key: "objective-2",
        root_work_item_id: "root-2",
        title: "Ambiguous second Mission",
      }),
    ],
    conversations: conversationProjection(),
    missionCoverageState: V2_CANONICAL_MISSION_COVERAGE,
  });

  assert.equal(result.supported, true);
  assert.deepEqual(result.items, []);
});

test("Phase 7E fails closed when exact conversation participants are inconsistent with Mission topology", () => {
  const result = buildV2VisibleMissionCollaborations({
    missions: [mission({ participant_position_keys: ["cto", "ceo"] })],
    conversations: conversationProjection(),
    missionCoverageState: V2_CANONICAL_MISSION_COVERAGE,
  });
  assert.deepEqual(result.items, []);
});

test("Phase 7E remains unavailable when governed conversation coverage is unavailable", () => {
  const result = buildV2VisibleMissionCollaborations({
    missions: [mission()],
    conversations: {
      supported: false,
      coverageState: "unavailable",
      items: [],
      limitation: "fixture unavailable",
    },
    missionCoverageState: V2_CANONICAL_MISSION_COVERAGE,
  });
  assert.equal(result.supported, false);
  assert.deepEqual(result.items, []);
});

test("Phase 7E visible surfaces preserve anti-overclaim language and shared projection", () => {
  const signal = readFileSync(
    new URL("../components/v2/V2CanonicalMissionCollaborationSignal.tsx", import.meta.url),
    "utf8",
  );
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

  assert.match(signal, /data-active-collaboration-claimed="false"/);
  assert.match(signal, /not live teamwork · not co-location/);
  assert.match(inspector, /Mission membership alone claims collaboration: no/);
  assert.match(missionRoom, /Topology membership only/);
  assert.match(missionRoom, /will not infer collaboration from Mission membership or shared topology/);
  assert.match(inspectorModel, /buildV2VisibleMissionCollaborations/);
  assert.match(inspectorModel, /visibleMissionCollaborationsForPosition/);
});
