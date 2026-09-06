import type {
  AustriaLiveOrganizationSnapshot,
  OrganizationEnvironmentalMemory,
} from "../live-organization";
import type {
  V2OwnerOrganizationData,
  V2RecentChange,
} from "./owner-organization";

export type V2EvidenceReferenceKind = "domain_evidence" | "verified_rule" | "source_snapshot";

export type V2EvidenceReference = {
  key: string;
  kind: V2EvidenceReferenceKind;
  label: string;
  id: string;
};

export type V2SpecialistEvidence = {
  positionKey: string;
  workItemId: string;
  status: string;
  evidenceValid: boolean;
  evidenceReason: string | null;
  groundingState: string | null;
  evidenceRefCount: number | null;
  verifiedRuleRefCount: number | null;
  sourceSnapshotRefCount: number | null;
  warnings: string[];
};

export type V2EvidenceWorkspaceModel = {
  generatedAt: string;
  rootWorkItemId: string;
  objectiveKey: string;
  references: V2EvidenceReference[];
  domainEvidenceCount: number;
  verifiedRuleCount: number;
  sourceSnapshotCount: number;
  specialists: V2SpecialistEvidence[];
  externalActionAuthorized: boolean;
};

const evidenceLabels: Record<V2EvidenceReferenceKind, string> = {
  domain_evidence: "Domain evidence",
  verified_rule: "Verified rule",
  source_snapshot: "Source snapshot",
};

export function evidenceReferenceKey(kind: V2EvidenceReferenceKind, id: string) {
  return `${kind}:${id}`;
}

function evidenceReference(kind: V2EvidenceReferenceKind, id: string): V2EvidenceReference {
  return { key: evidenceReferenceKey(kind, id), kind, label: evidenceLabels[kind], id };
}

function uniqueReferences(items: V2EvidenceReference[]) {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.key)) return false;
    seen.add(item.key);
    return true;
  });
}

export function buildV2EvidenceWorkspace(snapshot: AustriaLiveOrganizationSnapshot): V2EvidenceWorkspaceModel {
  const references = uniqueReferences([
    ...snapshot.domain_evidence_refs.map((id) => evidenceReference("domain_evidence", id)),
    ...snapshot.verified_rule_refs.map((id) => evidenceReference("verified_rule", id)),
    ...snapshot.source_snapshot_refs.map((id) => evidenceReference("source_snapshot", id)),
  ]);

  return {
    generatedAt: snapshot.generated_at,
    rootWorkItemId: snapshot.root_work_item_id,
    objectiveKey: snapshot.objective_key,
    references,
    domainEvidenceCount: snapshot.domain_evidence_refs.length,
    verifiedRuleCount: snapshot.verified_rule_refs.length,
    sourceSnapshotCount: snapshot.source_snapshot_refs.length,
    specialists: snapshot.specialist_outputs.map((specialist) => ({
      positionKey: specialist.position_key,
      workItemId: specialist.work_item_id,
      status: specialist.status,
      evidenceValid: specialist.evidence_valid,
      evidenceReason: specialist.evidence_reason,
      groundingState: specialist.runtime_quality?.grounding_state ?? null,
      evidenceRefCount: specialist.runtime_quality?.evidence_ref_count ?? null,
      verifiedRuleRefCount: specialist.runtime_quality?.verified_rule_ref_count ?? null,
      sourceSnapshotRefCount: specialist.runtime_quality?.source_snapshot_ref_count ?? null,
      warnings: [...(specialist.runtime_quality?.warnings ?? [])],
    })),
    externalActionAuthorized: snapshot.external_action_authorized,
  };
}

export function evidenceDestination(reference: Pick<V2EvidenceReference, "kind" | "id">) {
  const params = new URLSearchParams({ kind: reference.kind, ref: reference.id });
  return `/cockpit/v2/evidence?${params.toString()}`;
}

export function selectEvidenceReference(
  references: readonly V2EvidenceReference[],
  kind: string | null,
  id: string | null,
) {
  if (!kind || !id) return null;
  return references.find((item) => item.kind === kind && item.id === id) ?? null;
}

export type V2IntelligenceModel = {
  current: null | {
    loadedAt: string;
    partial: boolean;
    unavailableSources: string[];
    attentionCount: number;
    missionCount: number;
    departmentBlockerCount: number;
    recentActivityCount: number;
    recentChanges: V2RecentChange[];
  };
  memory: null | {
    generatedAt: string;
    windowEventCount: number;
    windowStart: string | null;
    windowEnd: string | null;
    kindAggregates: OrganizationEnvironmentalMemory["kind_aggregates"];
    pathFrequencies: OrganizationEnvironmentalMemory["path_frequencies"];
    heatCells: OrganizationEnvironmentalMemory["heat_cells"];
    timeline: OrganizationEnvironmentalMemory["timeline"];
    canonicalProjection: boolean;
    authoritative: boolean;
    predictive: boolean;
    mutationsAllowed: boolean;
    visualizationOnly: boolean;
    unsupportedDimensions: string[];
  };
};

export function buildV2IntelligenceModel(
  owner: V2OwnerOrganizationData | null | undefined,
  memory: OrganizationEnvironmentalMemory | null | undefined,
): V2IntelligenceModel {
  const current = owner ? {
    loadedAt: owner.loadedAt,
    partial: owner.partial,
    unavailableSources: [...owner.unavailableSources],
    attentionCount: owner.attention.length,
    missionCount: owner.organization.missionCount,
    departmentBlockerCount: owner.organization.zones.reduce((total, zone) => total + zone.activeBlockerCount, 0),
    recentActivityCount: owner.recentChanges.length,
    recentChanges: [...owner.recentChanges],
  } : null;

  const aggregateMemory = memory ? {
    generatedAt: memory.generated_at,
    windowEventCount: memory.window_event_count,
    windowStart: memory.window_start,
    windowEnd: memory.window_end,
    kindAggregates: [...memory.kind_aggregates],
    pathFrequencies: [...memory.path_frequencies],
    heatCells: [...memory.heat_cells],
    timeline: [...memory.timeline],
    canonicalProjection: memory.canonical_projection,
    authoritative: memory.authoritative,
    predictive: memory.predictive,
    mutationsAllowed: memory.mutations_allowed,
    visualizationOnly: memory.visualization_only,
    unsupportedDimensions: [...memory.unsupported_dimensions],
  } : null;

  return { current, memory: aggregateMemory };
}

export function activityDestination(activityId: string) {
  return `/cockpit/v2/intelligence?activity=${encodeURIComponent(activityId)}`;
}

export function selectRecentChange(changes: readonly V2RecentChange[], activityId: string | null) {
  if (!activityId) return null;
  return changes.find((item) => item.id === activityId) ?? null;
}
