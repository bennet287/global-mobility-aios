import type {
  LivingOrganizationSceneLatest,
  LivingSceneDecision,
} from "../live-organization";

export type V2DecisionRecord = {
  decisionId: string;
  decisionKey: string;
  title: string;
  question: string;
  recommendation: string;
  status: string;
  authorityLevel: string;
  decisionOwnerPosition: string;
  workItemId: string | null;
  evidenceItemCount: number;
  recordFingerprint: string | null;
  sourceObjectType: string | null;
  sourceObjectId: string | null;
  sourceObjectVersion: string | null;
  supersedesDecisionId: string | null;
  supersededByDecisionId: string | null;
  isCurrent: boolean;
  requiredOwnerAction: boolean;
  decidedAt: string | null;
  createdAt: string;
  supersededByCreatedAt: string | null;
  supersededInProjectionWeek: boolean;
};

export type V2DecisionPortfolio = {
  established: boolean;
  generatedAt: string | null;
  contractVersion: string | null;
  canonicalAuthority: string | null;
  sceneAuthoritative: boolean;
  mutationsAllowed: boolean;
  decisions: V2DecisionRecord[];
  returnedDecisionCount: number;
  currentDecisionCount: number;
  ownerActionCount: number;
  supersessionLinkedCount: number;
};

function decisionRecord(decision: LivingSceneDecision): V2DecisionRecord {
  return {
    decisionId: decision.decision_id,
    decisionKey: decision.decision_key,
    title: decision.title,
    question: decision.question,
    recommendation: decision.recommendation,
    status: decision.status,
    authorityLevel: decision.authority_level,
    decisionOwnerPosition: decision.decision_owner_position,
    workItemId: decision.work_item_id,
    evidenceItemCount: Array.isArray(decision.evidence_items) ? decision.evidence_items.length : 0,
    recordFingerprint: decision.record_fingerprint,
    sourceObjectType: decision.source_object_type,
    sourceObjectId: decision.source_object_id,
    sourceObjectVersion: decision.source_object_version,
    supersedesDecisionId: decision.supersedes_decision_id,
    supersededByDecisionId: decision.superseded_by_decision_id,
    isCurrent: decision.is_current,
    requiredOwnerAction: decision.required_owner_action,
    decidedAt: decision.decided_at,
    createdAt: decision.created_at,
    supersededByCreatedAt: decision.superseded_by_created_at,
    supersededInProjectionWeek: decision.superseded_in_projection_week,
  };
}

function decisionSort(a: V2DecisionRecord, b: V2DecisionRecord): number {
  const ownerAction = Number(b.requiredOwnerAction) - Number(a.requiredOwnerAction);
  if (ownerAction) return ownerAction;
  const current = Number(b.isCurrent) - Number(a.isCurrent);
  if (current) return current;
  return b.createdAt.localeCompare(a.createdAt) || a.title.localeCompare(b.title);
}

export function buildV2DecisionPortfolio(latest: LivingOrganizationSceneLatest | null): V2DecisionPortfolio {
  const scene = latest?.established ? latest.scene : null;
  if (!scene) {
    return {
      established: false,
      generatedAt: null,
      contractVersion: null,
      canonicalAuthority: null,
      sceneAuthoritative: false,
      mutationsAllowed: false,
      decisions: [],
      returnedDecisionCount: 0,
      currentDecisionCount: 0,
      ownerActionCount: 0,
      supersessionLinkedCount: 0,
    };
  }

  const decisions = scene.deterministic.decisions.map(decisionRecord).sort(decisionSort);
  return {
    established: true,
    generatedAt: scene.generated_at,
    contractVersion: scene.contract_version,
    canonicalAuthority: scene.truth.canonical_authority,
    sceneAuthoritative: scene.truth.scene_authoritative,
    mutationsAllowed: scene.truth.scene_mutations_allowed,
    decisions,
    returnedDecisionCount: decisions.length,
    currentDecisionCount: decisions.filter((item) => item.isCurrent).length,
    ownerActionCount: decisions.filter((item) => item.requiredOwnerAction).length,
    supersessionLinkedCount: decisions.filter((item) => item.supersedesDecisionId || item.supersededByDecisionId).length,
  };
}

export function filterV2Decisions(
  decisions: readonly V2DecisionRecord[],
  query: string,
  status: string,
  ownerActionOnly: boolean,
): V2DecisionRecord[] {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return decisions.filter((decision) => {
    if (status && decision.status !== status) return false;
    if (ownerActionOnly && !decision.requiredOwnerAction) return false;
    if (!words.length) return true;
    const text = `${decision.title} ${decision.question} ${decision.status} ${decision.authorityLevel} ${decision.decisionOwnerPosition}`.toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

export function selectV2Decision(decisions: readonly V2DecisionRecord[], decisionId: string | null) {
  if (!decisionId) return null;
  return decisions.find((item) => item.decisionId === decisionId) ?? null;
}

export function decisionDestination(decisionId: string) {
  const params = new URLSearchParams({ decision: decisionId });
  return `/cockpit/v2/decisions?${params.toString()}`;
}
