import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  V2_CANONICAL_BLOCKER_COVERAGE,
  buildV2VisibleBlockers,
  selectV2CanonicalBlockersForPosition,
  summarizeV2VisibleBlockers,
  visibleBlockersForPosition,
} from "../lib/v2/visible-blocker.ts";

function employee(position_key, work_item_id) {
  return {
    position_key,
    title: position_key.toUpperCase(),
    department: "Technology",
    reports_to_position_key: null,
    authority_level: "operational",
    organization_status: "active",
    work_item_id,
    work_status: "blocked",
    semantic_state: "blocked",
    presence_state: "not_asserted",
    state_reason: "canonical fixture",
  };
}

function blocker(overrides = {}) {
  return {
    blocker_id: "blocker-1",
    work_item_id: "work-1",
    blocker_type: "dependency",
    title: "Regulatory API evidence missing",
    description: "External evidence is required before governed work can proceed.",
    severity: "high",
    status: "open",
    accountable_position_key: "cto",
    decision_id: null,
    risk_escalation_id: null,
    requires_human_action: false,
    opened_at: "2026-09-07T15:00:00Z",
    due_at: null,
    open_elapsed_seconds: 900,
    overdue: false,
    ...overrides,
  };
}

test("Phase 7C accepts only the real canonical blocker coverage adapter", () => {
  assert.equal(V2_CANONICAL_BLOCKER_COVERAGE, "organization_blocker_canonical_records");

  const employees = [employee("cto", "work-1")];
  for (const coverageState of ["unavailable", "partial", "covered", ""]) {
    const result = buildV2VisibleBlockers({
      blockers: [blocker()],
      employees,
      coverageState,
    });
    assert.equal(result.supported, false);
    assert.deepEqual(result.items, []);
  }
});

test("Phase 7C preserves explicit accountable-position blocker truth", () => {
  const result = buildV2VisibleBlockers({
    blockers: [blocker()],
    employees: [employee("cto", "work-1"), employee("ceo", "work-1")],
    coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
  });

  assert.equal(result.supported, true);
  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].positionKey, "cto");
  assert.equal(result.items[0].relation, "accountable_position");
  assert.equal(result.items[0].title, "Regulatory API evidence missing");
  assert.equal(result.items[0].severity, "high");
  assert.equal(result.items[0].truth.accountablePositionClaimed, true);
  assert.equal(result.items[0].truth.causalBlockClaimed, false);
  assert.equal(result.items[0].truth.resolutionClaimed, false);
  assert.equal(result.items[0].truth.physicalPresenceClaimed, false);
  assert.equal(result.items[0].truth.canonicalMutationAllowed, false);
});

test("Phase 7C fails closed when WorkItem-only blocker ownership is ambiguous", () => {
  const employees = [
    employee("cto", "work-1"),
    employee("regulatory_lead", "work-1"),
  ];
  const blockers = [blocker({ accountable_position_key: null })];
  const result = buildV2VisibleBlockers({
    blockers,
    employees,
    coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
  });

  assert.equal(result.supported, true);
  assert.deepEqual(result.items, []);

  for (const positionKey of ["cto", "regulatory_lead"]) {
    const selection = selectV2CanonicalBlockersForPosition({
      blockers,
      employees,
      coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
      positionKey,
    });
    assert.equal(selection.supported, true);
    assert.deepEqual(selection.blockers, []);
    assert.deepEqual(selection.blockerIds, []);
  }
});

test("Phase 7C canonical blocker selector preserves a unique WorkItem-only relation", () => {
  const employees = [employee("cto", "work-1")];
  const blockers = [blocker({ accountable_position_key: null })];
  const selection = selectV2CanonicalBlockersForPosition({
    blockers,
    employees,
    coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
    positionKey: "cto",
  });

  assert.equal(selection.supported, true);
  assert.deepEqual(selection.blockerIds, ["blocker-1"]);
  assert.equal(selection.blockers[0]?.title, "Regulatory API evidence missing");
});

test("Phase 7C permits a unique WorkItem relation without upgrading it to accountability", () => {
  const result = buildV2VisibleBlockers({
    blockers: [blocker({ accountable_position_key: null })],
    employees: [employee("cto", "work-1")],
    coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
  });

  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].relation, "unique_work_item");
  assert.equal(result.items[0].truth.accountablePositionClaimed, false);
});

test("Phase 7C summarizes multiple blockers by count instead of cherry-picking severity", () => {
  const result = buildV2VisibleBlockers({
    blockers: [
      blocker({ blocker_id: "blocker-high", severity: "high" }),
      blocker({ blocker_id: "blocker-critical", severity: "critical", title: "Second canonical blocker" }),
    ],
    employees: [employee("cto", "work-1")],
    coverageState: V2_CANONICAL_BLOCKER_COVERAGE,
  });

  assert.equal(visibleBlockersForPosition(result, "cto").length, 2);
  const summary = summarizeV2VisibleBlockers(result, "cto");
  assert.equal(summary?.count, 2);
  assert.equal(summary?.single, null);
  assert.equal(summary?.label, "2 blockers");
});

test("Phase 7C marker is non-animated and truth attributes remain explicit", () => {
  const component = readFileSync(
    new URL("../components/v2/V2CanonicalBlockerMarker.tsx", import.meta.url),
    "utf8",
  );
  const css = readFileSync(
    new URL("../components/v2/V2CanonicalBlockerMarker.module.css", import.meta.url),
    "utf8",
  );
  const stage = readFileSync(
    new URL("../components/v2/V2LivingHqVisualStage.tsx", import.meta.url),
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

  assert.match(component, /data-blocker-resolution-claimed="false"/);
  assert.match(component, /data-causal-block-claimed="false"/);
  assert.match(component, /data-physical-presence-claimed="false"/);
  assert.doesNotMatch(css, /animation\s*:/i);
  assert.match(stage, /workState\.kind === "blocked"/);
  assert.match(stage, /V2CanonicalBlockerMarker/);
  assert.match(inspector, /Blocker details unavailable/);
  assert.match(inspector, /Blocker resolution claimed: no/);
  assert.match(missionRoom, /will not present an empty blocker list as canonical zero/);
  assert.match(inspectorModel, /selectV2CanonicalBlockersForPosition/);
  assert.doesNotMatch(
    inspectorModel,
    /blocker\.accountable_position_key === positionKey\s*\|\|/,
  );
});
