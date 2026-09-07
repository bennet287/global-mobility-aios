import type {
  LivingSceneDecision,
  LivingSceneEmployee,
  LivingSceneHumanActionRequest,
  LivingSceneRiskEscalation,
} from "../live-organization";

export const V2_CANONICAL_HUMAN_ACTION_COVERAGE =
  "organization_human_action_request_open_records" as const;
export const V2_CANONICAL_RISK_ESCALATION_COVERAGE =
  "risk_escalation_open_records" as const;

export type V2VisibleEscalationParticipant = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
};

export type V2VisibleDecisionAttention = {
  readonly kind: "decision_attention";
  readonly decisionId: string;
  readonly title: string;
  readonly status: string;
  readonly authorityLevel: string;
  readonly decisionOwnerPosition: string;
  readonly workItemId: string | null;
  readonly recommendation: string;
  readonly canonicalBasis: "ExecutiveDecision.required_owner_action";
};

export type V2VisibleHumanActionAttention = {
  readonly kind: "human_action";
  readonly requestId: string;
  readonly title: string;
  readonly instructions: string;
  readonly status: string;
  readonly priority: string;
  readonly requiredRole: string;
  readonly authorityLevel: string | null;
  readonly workItemId: string | null;
  readonly decisionId: string | null;
  readonly blockerId: string | null;
  readonly requestedAt: string;
  readonly dueAt: string | null;
  readonly canonicalBasis: string;
};

export type V2VisibleRiskEscalation = {
  readonly kind: "risk_escalation";
  readonly riskId: string;
  readonly riskKey: string;
  readonly title: string;
  readonly description: string;
  readonly category: string;
  readonly severity: string;
  readonly status: string;
  readonly accountablePositionKey: string;
  readonly escalatedToPositionKey: string;
  readonly accountableParticipant: V2VisibleEscalationParticipant | null;
  readonly escalatedToParticipant: V2VisibleEscalationParticipant | null;
  readonly workItemId: string | null;
  readonly requiresBoardAttention: boolean;
  readonly isEmergency: boolean;
  readonly createdAt: string;
  readonly canonicalBasis: string;
};

export type V2VisibleOwnerBoardEscalationCollection = {
  readonly humanActionCoverageSupported: boolean;
  readonly riskEscalationCoverageSupported: boolean;
  readonly humanActionCoverageState: string;
  readonly riskEscalationCoverageState: string;
  readonly decisionAttention: readonly V2VisibleDecisionAttention[];
  readonly humanActions: readonly V2VisibleHumanActionAttention[];
  readonly riskEscalations: readonly V2VisibleRiskEscalation[];
  readonly boardAttentionCount: number | null;
  readonly limitation: string | null;
  readonly truth: {
    readonly attentionEvidenceClaimed: true;
    readonly boardMeetingClaimed: false;
    readonly approvalClaimed: false;
    readonly physicalPresenceClaimed: false;
    readonly physicalLocationClaimed: false;
    readonly locomotionClaimed: false;
    readonly canonicalMutationAllowed: false;
  };
};

function normalized(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim() : "";
}

function rosterIndex(
  employees: readonly LivingSceneEmployee[],
): ReadonlyMap<string, V2VisibleEscalationParticipant> {
  const index = new Map<string, V2VisibleEscalationParticipant>();
  const duplicates = new Set<string>();
  for (const employee of employees) {
    const positionKey = normalized(employee.position_key);
    if (!positionKey || duplicates.has(positionKey)) continue;
    if (index.has(positionKey)) {
      index.delete(positionKey);
      duplicates.add(positionKey);
      continue;
    }
    index.set(positionKey, {
      positionKey,
      title: normalized(employee.title) || positionKey,
      department: normalized(employee.department) || "Unknown department",
    });
  }
  return index;
}

function validDecision(decision: LivingSceneDecision): boolean {
  return Boolean(
    decision.required_owner_action === true &&
      decision.is_current === true &&
      normalized(decision.decision_id) &&
      normalized(decision.title) &&
      normalized(decision.status) &&
      normalized(decision.authority_level) &&
      normalized(decision.decision_owner_position),
  );
}

function validHumanAction(request: LivingSceneHumanActionRequest): boolean {
  return Boolean(
    normalized(request.request_id) &&
      normalized(request.title) &&
      normalized(request.instructions) &&
      normalized(request.status) &&
      normalized(request.priority) &&
      normalized(request.required_role) &&
      normalized(request.requested_at) &&
      normalized(request.canonical_basis),
  );
}

function validRisk(risk: LivingSceneRiskEscalation): boolean {
  return Boolean(
    normalized(risk.risk_id) &&
      normalized(risk.risk_key) &&
      normalized(risk.title) &&
      normalized(risk.description) &&
      normalized(risk.category) &&
      normalized(risk.severity) &&
      normalized(risk.status) &&
      normalized(risk.accountable_position_key) &&
      normalized(risk.escalated_to_position_key) &&
      normalized(risk.created_at) &&
      normalized(risk.canonical_basis),
  );
}

export function buildV2VisibleOwnerBoardEscalations({
  decisions,
  humanActions,
  riskEscalations,
  employees,
  humanActionCoverageState,
  riskEscalationCoverageState,
}: {
  readonly decisions: readonly LivingSceneDecision[];
  readonly humanActions: readonly LivingSceneHumanActionRequest[];
  readonly riskEscalations: readonly LivingSceneRiskEscalation[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly humanActionCoverageState: string | null | undefined;
  readonly riskEscalationCoverageState: string | null | undefined;
}): V2VisibleOwnerBoardEscalationCollection {
  const humanCoverage = normalized(humanActionCoverageState) || "unavailable";
  const riskCoverage = normalized(riskEscalationCoverageState) || "unavailable";
  const humanActionCoverageSupported = humanCoverage === V2_CANONICAL_HUMAN_ACTION_COVERAGE;
  const riskEscalationCoverageSupported = riskCoverage === V2_CANONICAL_RISK_ESCALATION_COVERAGE;
  const employeesByPosition = rosterIndex(employees);

  const decisionAttention: V2VisibleDecisionAttention[] = decisions
    .filter(validDecision)
    .map((decision) => ({
      kind: "decision_attention" as const,
      decisionId: normalized(decision.decision_id),
      title: normalized(decision.title),
      status: normalized(decision.status),
      authorityLevel: normalized(decision.authority_level),
      decisionOwnerPosition: normalized(decision.decision_owner_position),
      workItemId: normalized(decision.work_item_id) || null,
      recommendation: normalized(decision.recommendation),
      canonicalBasis: "ExecutiveDecision.required_owner_action" as const,
    }));

  const visibleHumanActions: V2VisibleHumanActionAttention[] = humanActionCoverageSupported
    ? humanActions.filter(validHumanAction).map((request) => ({
        kind: "human_action" as const,
        requestId: normalized(request.request_id),
        title: normalized(request.title),
        instructions: normalized(request.instructions),
        status: normalized(request.status),
        priority: normalized(request.priority),
        requiredRole: normalized(request.required_role),
        authorityLevel: normalized(request.authority_level) || null,
        workItemId: normalized(request.work_item_id) || null,
        decisionId: normalized(request.decision_id) || null,
        blockerId: normalized(request.blocker_id) || null,
        requestedAt: normalized(request.requested_at),
        dueAt: normalized(request.due_at) || null,
        canonicalBasis: normalized(request.canonical_basis),
      }))
    : [];

  const visibleRisks: V2VisibleRiskEscalation[] = riskEscalationCoverageSupported
    ? riskEscalations.filter(validRisk).map((risk) => {
        const accountablePositionKey = normalized(risk.accountable_position_key);
        const escalatedToPositionKey = normalized(risk.escalated_to_position_key);
        return {
          kind: "risk_escalation" as const,
          riskId: normalized(risk.risk_id),
          riskKey: normalized(risk.risk_key),
          title: normalized(risk.title),
          description: normalized(risk.description),
          category: normalized(risk.category),
          severity: normalized(risk.severity),
          status: normalized(risk.status),
          accountablePositionKey,
          escalatedToPositionKey,
          accountableParticipant: employeesByPosition.get(accountablePositionKey) ?? null,
          escalatedToParticipant: employeesByPosition.get(escalatedToPositionKey) ?? null,
          workItemId: normalized(risk.work_item_id) || null,
          requiresBoardAttention: risk.requires_board_attention === true,
          isEmergency: risk.is_emergency === true,
          createdAt: normalized(risk.created_at),
          canonicalBasis: normalized(risk.canonical_basis),
        };
      })
    : [];

  decisionAttention.sort((left, right) => left.decisionId.localeCompare(right.decisionId));
  visibleHumanActions.sort((left, right) => right.requestedAt.localeCompare(left.requestedAt));
  visibleRisks.sort((left, right) => right.createdAt.localeCompare(left.createdAt));

  const limitationParts: string[] = [];
  if (!humanActionCoverageSupported) {
    limitationParts.push(
      "Human-action attention is unavailable for this coverage state; AIOS will not infer a required human role.",
    );
  }
  if (!riskEscalationCoverageSupported) {
    limitationParts.push(
      "Risk-escalation attention is unavailable for this coverage state; AIOS will not infer Board attention from severity or room placement.",
    );
  }

  return {
    humanActionCoverageSupported,
    riskEscalationCoverageSupported,
    humanActionCoverageState: humanCoverage,
    riskEscalationCoverageState: riskCoverage,
    decisionAttention,
    humanActions: visibleHumanActions,
    riskEscalations: visibleRisks,
    boardAttentionCount:
      humanActionCoverageSupported && riskEscalationCoverageSupported
        ? decisionAttention.length + visibleHumanActions.length + visibleRisks.filter((risk) => risk.requiresBoardAttention).length
        : null,
    limitation: limitationParts.length ? limitationParts.join(" ") : null,
    truth: {
      attentionEvidenceClaimed: true,
      boardMeetingClaimed: false,
      approvalClaimed: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      locomotionClaimed: false,
      canonicalMutationAllowed: false,
    },
  };
}

export function visibleOwnerBoardEscalationsForPosition(
  collection: V2VisibleOwnerBoardEscalationCollection,
  positionKey: string,
): readonly V2VisibleRiskEscalation[] {
  const key = normalized(positionKey);
  if (!key || !collection.riskEscalationCoverageSupported) return [];
  return collection.riskEscalations.filter(
    (risk) => risk.accountablePositionKey === key || risk.escalatedToPositionKey === key,
  );
}
