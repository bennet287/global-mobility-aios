import type {
  StructuredFlowBaseline,
  StructuredFlowNode,
} from "./living-organization-analytics";

export const FLOW_FIELD_TRIAL_VERSION = "gpu-flow-field-trial.v1";

export const FLOW_FIELD_PRESENTATION_FORMULA =
  "congestion = blocker*4 + risk*3 + owner_attention*3 + overdue*2 + min(handoff,3)";

export const FLOW_FIELD_TRIAL_GATES = Object.freeze({
  medianTimeImprovementPct: 20,
  errorRateImprovementPct: 25,
  ordinaryFps: 55,
  sustainedFpsFloor: 30,
  p95FeedbackMs: 100,
  mainThreadComputeImprovementPct: 30,
});

export type FlowFieldTrialNode = {
  workItemId: string;
  label: string;
  department: string;
  x: number;
  z: number;
  congestionScore: number;
  fieldStrength: number;
  blockerCount: number;
  riskEscalationCount: number;
  ownerAttentionCount: number;
  handoffCount: number;
  overdue: boolean;
  stalledCue: boolean;
  canonicalBasis: string;
};

export type FlowFieldTrialPath = {
  pathKey: string;
  sourceWorkItemId: string;
  targetWorkItemId: string;
  sourceX: number;
  sourceZ: number;
  targetX: number;
  targetZ: number;
  fieldStrength: number;
  stalledCue: boolean;
  relationshipSemantics: "parent_topology";
  canonicalBasis: string;
};

export type FlowFieldTrialModel = {
  trialVersion: typeof FLOW_FIELD_TRIAL_VERSION;
  authoritative: false;
  projectionOnly: true;
  promotionStatus: "benchmark_required";
  defaultProminence: false;
  fieldStateCanMutateWork: false;
  throughputClaimed: false;
  dependencyClaimed: false;
  formula: typeof FLOW_FIELD_PRESENTATION_FORMULA;
  nodes: FlowFieldTrialNode[];
  paths: FlowFieldTrialPath[];
  dominantDerivedPathKey: string | null;
  canonicalBasis: string;
};

export type FlowTrialBenchmarkEvidence = {
  participantCount: number;
  truthLeakageCount: number;
  baselineCorrectRate: number | null;
  trialCorrectRate: number | null;
  baselineMedianCorrectMs: number | null;
  trialMedianCorrectMs: number | null;
  baselineErrorRate: number | null;
  trialErrorRate: number | null;
  ordinaryFps: number | null;
  sustainedMinFps: number | null;
  p95FeedbackMs: number | null;
  mainThreadComputeImprovementPct: number | null;
  capabilitySustainedAbove30Fps: boolean;
};

export type FlowTrialBenchmarkEvaluation = {
  status: "benchmark_required" | "hard_fail" | "defer" | "promotion_ready";
  truthGate: boolean | null;
  correctnessGate: boolean | null;
  comprehensionGate: boolean | null;
  renderingGate: boolean | null;
  computeValueGate: boolean | null;
  medianTimeImprovementPct: number | null;
  errorRateImprovementPct: number | null;
  reason: string;
};

function finiteOrNull(value: number | null): number | null {
  return value !== null && Number.isFinite(value) ? value : null;
}

function percentImprovement(baseline: number | null, trial: number | null): number | null {
  const left = finiteOrNull(baseline);
  const right = finiteOrNull(trial);
  if (left === null || right === null || left <= 0) return null;
  return ((left - right) / left) * 100;
}

function congestionScore(node: StructuredFlowNode): number {
  return (
    node.blockerCount * 4
    + node.riskEscalationCount * 3
    + node.ownerAttentionCount * 3
    + (node.overdue ? 2 : 0)
    + Math.min(node.handoffCount, 3)
  );
}

function nodeLayout(nodes: StructuredFlowNode[]): Map<string, { x: number; z: number }> {
  const departments = [...new Set(nodes.map((node) => node.department))].sort();
  const result = new Map<string, { x: number; z: number }>();
  const departmentSpacing = 5.2;
  const departmentStart = -((Math.max(1, departments.length) - 1) * departmentSpacing) / 2;

  departments.forEach((department, departmentIndex) => {
    const departmentNodes = nodes
      .filter((node) => node.department === department)
      .sort((left, right) => left.workItemId.localeCompare(right.workItemId));

    departmentNodes.forEach((node, nodeIndex) => {
      const column = nodeIndex % 3;
      const row = Math.floor(nodeIndex / 3);
      result.set(node.workItemId, {
        x: departmentStart + departmentIndex * departmentSpacing + (column - 1) * 1.15,
        z: 3.4 + row * 1.15,
      });
    });
  });

  return result;
}

export function buildFlowFieldTrialModel(
  baseline: StructuredFlowBaseline,
): FlowFieldTrialModel {
  const layout = nodeLayout(baseline.nodes);
  const maxScore = Math.max(1, ...baseline.nodes.map(congestionScore));

  const nodes = baseline.nodes.map((node): FlowFieldTrialNode => {
    const point = layout.get(node.workItemId) ?? { x: 0, z: 3.4 };
    const score = congestionScore(node);
    return {
      workItemId: node.workItemId,
      label: node.title,
      department: node.department,
      x: point.x,
      z: point.z,
      congestionScore: score,
      fieldStrength: Math.max(0.12, score / maxScore),
      blockerCount: node.blockerCount,
      riskEscalationCount: node.riskEscalationCount,
      ownerAttentionCount: node.ownerAttentionCount,
      handoffCount: node.handoffCount,
      overdue: node.overdue,
      stalledCue: node.blockerCount > 0 || node.overdue,
      canonicalBasis: node.canonicalBasis,
    };
  });

  const nodeById = new Map(nodes.map((node) => [node.workItemId, node]));
  const paths = baseline.edges.flatMap((edge): FlowFieldTrialPath[] => {
    const source = nodeById.get(edge.sourceWorkItemId);
    const target = nodeById.get(edge.targetWorkItemId);
    if (!source || !target) return [];
    return [{
      pathKey: edge.edgeKey,
      sourceWorkItemId: edge.sourceWorkItemId,
      targetWorkItemId: edge.targetWorkItemId,
      sourceX: source.x,
      sourceZ: source.z,
      targetX: target.x,
      targetZ: target.z,
      fieldStrength: Math.max(0.12, (source.fieldStrength + target.fieldStrength) / 2),
      stalledCue: source.stalledCue || target.stalledCue,
      relationshipSemantics: "parent_topology",
      canonicalBasis: edge.canonicalBasis,
    }];
  });

  const dominantDerivedPathKey = [...paths]
    .sort((left, right) => (
      right.fieldStrength - left.fieldStrength
      || left.pathKey.localeCompare(right.pathKey)
    ))[0]?.pathKey ?? null;

  return {
    trialVersion: FLOW_FIELD_TRIAL_VERSION,
    authoritative: false,
    projectionOnly: true,
    promotionStatus: "benchmark_required",
    defaultProminence: false,
    fieldStateCanMutateWork: false,
    throughputClaimed: false,
    dependencyClaimed: false,
    formula: FLOW_FIELD_PRESENTATION_FORMULA,
    nodes,
    paths,
    dominantDerivedPathKey,
    canonicalBasis:
      "Derived from the maintained Structured FLOW baseline; parent topology remains topology, not dependency/throughput truth.",
  };
}

export function evaluateFlowTrialBenchmark(
  evidence: FlowTrialBenchmarkEvidence,
): FlowTrialBenchmarkEvaluation {
  if (evidence.truthLeakageCount > 0) {
    return {
      status: "hard_fail",
      truthGate: false,
      correctnessGate: null,
      comprehensionGate: null,
      renderingGate: null,
      computeValueGate: null,
      medianTimeImprovementPct: null,
      errorRateImprovementPct: null,
      reason: "Truth/authority leakage is a hard failure regardless of visual or performance results.",
    };
  }

  const medianTimeImprovementPct = percentImprovement(
    evidence.baselineMedianCorrectMs,
    evidence.trialMedianCorrectMs,
  );
  const errorRateImprovementPct = percentImprovement(
    evidence.baselineErrorRate,
    evidence.trialErrorRate,
  );

  const hasHumanEvidence = (
    evidence.participantCount > 0
    && evidence.baselineCorrectRate !== null
    && evidence.trialCorrectRate !== null
    && (
      medianTimeImprovementPct !== null
      || errorRateImprovementPct !== null
    )
  );
  const hasRenderingEvidence = (
    evidence.ordinaryFps !== null
    && evidence.sustainedMinFps !== null
    && evidence.p95FeedbackMs !== null
  );
  const hasComputeEvidence = (
    evidence.mainThreadComputeImprovementPct !== null
    || evidence.capabilitySustainedAbove30Fps
  );

  if (!hasHumanEvidence || !hasRenderingEvidence || !hasComputeEvidence) {
    return {
      status: "benchmark_required",
      truthGate: true,
      correctnessGate: null,
      comprehensionGate: null,
      renderingGate: null,
      computeValueGate: null,
      medianTimeImprovementPct,
      errorRateImprovementPct,
      reason: "Promotion is blocked until human comprehension plus rendering and compute-value evidence is recorded.",
    };
  }

  const correctnessGate = (evidence.trialCorrectRate ?? 0) >= (evidence.baselineCorrectRate ?? 0);
  const comprehensionGate = (
    (medianTimeImprovementPct ?? Number.NEGATIVE_INFINITY) >= FLOW_FIELD_TRIAL_GATES.medianTimeImprovementPct
    || (errorRateImprovementPct ?? Number.NEGATIVE_INFINITY) >= FLOW_FIELD_TRIAL_GATES.errorRateImprovementPct
  );
  const renderingGate = (
    (evidence.ordinaryFps ?? 0) >= FLOW_FIELD_TRIAL_GATES.ordinaryFps
    && (evidence.sustainedMinFps ?? 0) >= FLOW_FIELD_TRIAL_GATES.sustainedFpsFloor
    && (evidence.p95FeedbackMs ?? Number.POSITIVE_INFINITY) <= FLOW_FIELD_TRIAL_GATES.p95FeedbackMs
  );
  const computeValueGate = (
    (evidence.mainThreadComputeImprovementPct ?? Number.NEGATIVE_INFINITY)
      >= FLOW_FIELD_TRIAL_GATES.mainThreadComputeImprovementPct
    || evidence.capabilitySustainedAbove30Fps
  );

  const promotionReady = correctnessGate && comprehensionGate && renderingGate && computeValueGate;
  return {
    status: promotionReady ? "promotion_ready" : "defer",
    truthGate: true,
    correctnessGate,
    comprehensionGate,
    renderingGate,
    computeValueGate,
    medianTimeImprovementPct,
    errorRateImprovementPct,
    reason: promotionReady
      ? "All recorded promotion gates pass; promotion may be considered by the roadmap acceptance process."
      : "At least one recorded promotion gate failed; keep the fluid/field representation non-default and redesign or defer.",
  };
}
