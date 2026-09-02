import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildFlowFieldTrialModel,
  evaluateFlowTrialBenchmark,
  FLOW_FIELD_PRESENTATION_FORMULA,
} from "../lib/living-organization-flow-trial.ts";

function baselineFixture() {
  return {
    authoritative: false,
    projectionOnly: true,
    workItemCount: 3,
    activeWorkItemCount: 2,
    blockedWorkItemCount: 1,
    ownerAttentionWorkItemCount: 1,
    overdueWorkItemCount: 1,
    parentEdgeCount: 2,
    handoffCount: 1,
    nodes: [
      {
        workItemId: "root",
        title: "Austria mission",
        status: "running",
        priority: "high",
        riskLevel: "R4",
        assignedPositionKey: "mobility_operations_lead",
        department: "mobility",
        elapsedSeconds: 3600,
        overdue: true,
        blockerCount: 1,
        oldestBlockerSeconds: 1800,
        handoffCount: 0,
        riskEscalationCount: 1,
        ownerAttentionCount: 1,
        attentionSignalCount: 3,
        specialistEvidenceValid: null,
        specialistEvidenceReason: null,
        canonicalBasis: "root basis",
      },
      {
        workItemId: "child-a",
        title: "Pathway",
        status: "running",
        priority: "normal",
        riskLevel: "routine",
        assignedPositionKey: "pathway_specialist",
        department: "mobility",
        elapsedSeconds: 1200,
        overdue: false,
        blockerCount: 0,
        oldestBlockerSeconds: null,
        handoffCount: 1,
        riskEscalationCount: 0,
        ownerAttentionCount: 0,
        attentionSignalCount: 0,
        specialistEvidenceValid: true,
        specialistEvidenceReason: null,
        canonicalBasis: "child a basis",
      },
      {
        workItemId: "child-b",
        title: "Regulatory",
        status: "completed",
        priority: "normal",
        riskLevel: "routine",
        assignedPositionKey: "regulatory_analyst",
        department: "regulatory",
        elapsedSeconds: 800,
        overdue: false,
        blockerCount: 0,
        oldestBlockerSeconds: null,
        handoffCount: 0,
        riskEscalationCount: 0,
        ownerAttentionCount: 0,
        attentionSignalCount: 0,
        specialistEvidenceValid: true,
        specialistEvidenceReason: null,
        canonicalBasis: "child b basis",
      },
    ],
    edges: [
      {
        edgeKey: "parent:root:child-a",
        edgeType: "parent_topology",
        sourceWorkItemId: "root",
        targetWorkItemId: "child-a",
        canonicalBasis: "parent topology only",
      },
      {
        edgeKey: "parent:root:child-b",
        edgeType: "parent_topology",
        sourceWorkItemId: "root",
        targetWorkItemId: "child-b",
        canonicalBasis: "parent topology only",
      },
    ],
    handoffs: [],
    canonicalBasis: "structured flow baseline",
  };
}

test("M.7 FLOW field trial is deterministic and cannot manufacture dependency or throughput truth", () => {
  const first = buildFlowFieldTrialModel(baselineFixture());
  const second = buildFlowFieldTrialModel(baselineFixture());
  assert.deepEqual(first, second);
  assert.equal(first.authoritative, false);
  assert.equal(first.projectionOnly, true);
  assert.equal(first.promotionStatus, "benchmark_required");
  assert.equal(first.defaultProminence, false);
  assert.equal(first.fieldStateCanMutateWork, false);
  assert.equal(first.throughputClaimed, false);
  assert.equal(first.dependencyClaimed, false);
  assert.equal(first.formula, FLOW_FIELD_PRESENTATION_FORMULA);
  assert.equal(first.paths.length, 2);
  assert.ok(first.paths.every((path) => path.relationshipSemantics === "parent_topology"));
  assert.match(first.paths[0].canonicalBasis, /topology only/);
  assert.equal(first.nodes.find((node) => node.workItemId === "root")?.stalledCue, true);
});

test("M.7 FLOW field trial never auto-promotes without human and performance evidence", () => {
  const pending = evaluateFlowTrialBenchmark({
    participantCount: 0,
    truthLeakageCount: 0,
    baselineCorrectRate: null,
    trialCorrectRate: null,
    baselineMedianCorrectMs: null,
    trialMedianCorrectMs: null,
    baselineErrorRate: null,
    trialErrorRate: null,
    ordinaryFps: null,
    sustainedMinFps: null,
    p95FeedbackMs: null,
    mainThreadComputeImprovementPct: null,
    capabilitySustainedAbove30Fps: false,
  });
  assert.equal(pending.status, "benchmark_required");

  const ready = evaluateFlowTrialBenchmark({
    participantCount: 4,
    truthLeakageCount: 0,
    baselineCorrectRate: 1,
    trialCorrectRate: 1,
    baselineMedianCorrectMs: 10000,
    trialMedianCorrectMs: 7500,
    baselineErrorRate: 0.2,
    trialErrorRate: 0.1,
    ordinaryFps: 58,
    sustainedMinFps: 38,
    p95FeedbackMs: 82,
    mainThreadComputeImprovementPct: 34,
    capabilitySustainedAbove30Fps: false,
  });
  assert.equal(ready.status, "promotion_ready");
  assert.equal(ready.correctnessGate, true);
  assert.equal(ready.comprehensionGate, true);
  assert.equal(ready.renderingGate, true);
  assert.equal(ready.computeValueGate, true);

  const hardFail = evaluateFlowTrialBenchmark({
    participantCount: 4,
    truthLeakageCount: 1,
    baselineCorrectRate: 1,
    trialCorrectRate: 1,
    baselineMedianCorrectMs: 10000,
    trialMedianCorrectMs: 7000,
    baselineErrorRate: 0.2,
    trialErrorRate: 0.1,
    ordinaryFps: 60,
    sustainedMinFps: 45,
    p95FeedbackMs: 70,
    mainThreadComputeImprovementPct: 40,
    capabilitySustainedAbove30Fps: false,
  });
  assert.equal(hardFail.status, "hard_fail");
});
