import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { buildV2OwnerSituationSummary } from "../lib/v2/owner-situation.ts";
import {
  buildV2CountTruth,
  deriveV2OwnerSourceCoverage,
  formatV2CountTruth,
} from "../lib/v2/truth-state.ts";
import { buildV2IntelligenceModel } from "../lib/v2/evidence-intelligence.ts";

function ownerData(overrides = {}) {
  return {
    loadedAt: "2026-09-07T10:00:00Z",
    partial: false,
    unavailableSources: [],
    attention: [],
    missions: [],
    recentChanges: [],
    organization: {
      established: true,
      generatedAt: "2026-09-07T10:00:00Z",
      scope: "fixture",
      contractVersion: "v5",
      sceneAuthoritative: false,
      rendererAuthoritative: false,
      mutationsAllowed: false,
      canonicalAuthority: "fixture",
      missions: [],
      zones: [],
      employeeRosterCount: 0,
      departmentCount: 0,
      missionCount: 0,
      coverage: null,
    },
    boardGeneratedAt: null,
    ...overrides,
  };
}

test("Q16 preserves legitimate zero only when required governed sources are available", () => {
  const data = ownerData();
  const coverage = deriveV2OwnerSourceCoverage(data);
  const metric = buildV2CountTruth(0, coverage, ["board", "humanActions", "blockers"]);
  assert.equal(metric.state, "known");
  assert.equal(formatV2CountTruth(metric), "0");

  const summary = buildV2OwnerSituationSummary(data);
  assert.equal(summary.attentionTotal.state, "known");
  assert.equal(formatV2CountTruth(summary.attentionTotal), "0");
  assert.equal(summary.recentChangeCount.state, "known");
  assert.equal(formatV2CountTruth(summary.recentChangeCount), "0");
});

test("Q16 never turns unavailable single-source coverage into numeric zero", () => {
  const data = ownerData({
    partial: true,
    unavailableSources: ["Activity"],
  });
  const summary = buildV2OwnerSituationSummary(data);
  assert.equal(summary.recentChangeCount.state, "unavailable");
  assert.equal(formatV2CountTruth(summary.recentChangeCount), "Unavailable");
  assert.notEqual(formatV2CountTruth(summary.recentChangeCount), "0");

  const intelligence = buildV2IntelligenceModel(data, null);
  assert.equal(intelligence.current?.recentActivityCount.state, "unavailable");
  assert.equal(formatV2CountTruth(intelligence.current.recentActivityCount), "Unavailable");
});

test("Q16 represents incomplete aggregate attention as Unknown or a proven lower bound", () => {
  const emptyPartial = ownerData({
    partial: true,
    unavailableSources: ["Board packet"],
  });
  const emptySummary = buildV2OwnerSituationSummary(emptyPartial);
  assert.equal(emptySummary.attentionTotal.state, "partial");
  assert.equal(formatV2CountTruth(emptySummary.attentionTotal), "Unknown");

  const positivePartial = ownerData({
    partial: true,
    unavailableSources: ["Board packet"],
    attention: [
      { id: "human:1", kind: "human_action", title: "Owner input", detail: "required", urgency: "high", href: "/owner-inbox", occurredAt: null, canonicalBasis: "HumanActionRequest:1" },
      { id: "blocker:1", kind: "blocker", title: "Blocked", detail: "high blocker", urgency: "high", href: "/cross-department-friction", occurredAt: null, canonicalBasis: "OrganizationBlocker:1" },
    ],
  });
  const positiveSummary = buildV2OwnerSituationSummary(positivePartial);
  assert.equal(positiveSummary.attentionTotal.state, "partial");
  assert.equal(formatV2CountTruth(positiveSummary.attentionTotal), "≥2");
  assert.deepEqual(positiveSummary.attentionTotal.affectedSources, ["Board packet"]);
});

test("Q16 distinguishes a non-established Living Organization projection from a zero projection", () => {
  const data = ownerData({
    organization: {
      ...ownerData().organization,
      established: false,
    },
  });
  const summary = buildV2OwnerSituationSummary(data);
  assert.equal(summary.missionCount.state, "not_established");
  assert.equal(summary.departmentCount.state, "not_established");
  assert.equal(formatV2CountTruth(summary.missionCount), "Not established");

  const intelligence = buildV2IntelligenceModel(data, null);
  assert.equal(intelligence.current?.missionCount.state, "not_established");
  assert.equal(intelligence.current?.departmentBlockerCount.state, "not_established");
});

test("Q16 Intelligence keeps full projection counts while adding coverage truth", () => {
  const data = ownerData({
    organization: {
      ...ownerData().organization,
      missionCount: 8,
      departmentCount: 3,
      employeeRosterCount: 4,
      zones: [{ wingKey: "operations", label: "Operations", departments: [], employeeRosterCount: 4, workItemCount: 2, activeBlockerCount: 2 }],
    },
    missions: [{ missionKey: "bounded:1", title: "Bounded", state: "running", phaseKey: null, participantCount: 1, blockerCount: 0, decisionCount: 0, rootWorkItemId: "root", canonicalBasis: "fixture" }],
  });
  const model = buildV2IntelligenceModel(data, null);
  assert.equal(model.current?.missionCount.value, 8);
  assert.equal(model.current?.missionCount.state, "known");
  assert.equal(model.current?.departmentBlockerCount.value, 2);
  assert.equal(model.current?.departmentBlockerCount.state, "known");
});

test("Q16 presentation surfaces do not retain false-zero fallback patterns", () => {
  const situationRoom = readFileSync(new URL("../components/v2/V2OwnerSituationRoom.tsx", import.meta.url), "utf8");
  const attentionList = readFileSync(new URL("../components/v2/V2AttentionList.tsx", import.meta.url), "utf8");
  const intelligence = readFileSync(new URL("../components/v2/V2IntelligenceWorkspace.tsx", import.meta.url), "utf8");

  assert.match(situationRoom, /Unknown values are not rendered as numeric zero/);
  assert.match(situationRoom, /No zero-Mission conclusion is made/);
  assert.match(situationRoom, /No zero-Activity conclusion is made/);
  assert.match(attentionList, /Attention coverage is incomplete/);
  assert.match(intelligence, /formatV2CountTruth/);
  assert.match(intelligence, /Owner-attention coverage incomplete/);
  assert.doesNotMatch(situationRoom, /summary\?\.[A-Za-z]+\s*\?\?\s*0/);
  assert.doesNotMatch(intelligence, /model\.current\.[A-Za-z]+\s*\?\?\s*0/);
});
