import type {
  OrganizationReplayEvent,
  OrganizationReplayLatest,
  OrganizationReplayState,
  OrganizationReplayStateDiff,
} from "../live-organization";

export type V2HistoryPortfolio = {
  established: boolean;
  contractVersion: string | null;
  generatedAt: string | null;
  rootWorkItemId: string | null;
  objectiveKey: string | null;
  canonicalProjection: boolean;
  authoritative: boolean;
  mutationsAllowed: boolean;
  totalEvents: number;
  returnedEvents: number;
  truncated: boolean;
  activityHistoryEstablished: boolean;
  activityHistoryBasis: string | null;
  activityHistoryCoverageStart: string | null;
  preEpochHistory: string | null;
  evidenceHistory: string | null;
  riskEscalationHistory: string | null;
  sourceSnapshotHistory: string | null;
  conversationHistory: string | null;
  events: readonly OrganizationReplayEvent[];
};

const emptyPortfolio: V2HistoryPortfolio = Object.freeze({
  established: false,
  contractVersion: null,
  generatedAt: null,
  rootWorkItemId: null,
  objectiveKey: null,
  canonicalProjection: false,
  authoritative: false,
  mutationsAllowed: false,
  totalEvents: 0,
  returnedEvents: 0,
  truncated: false,
  activityHistoryEstablished: false,
  activityHistoryBasis: null,
  activityHistoryCoverageStart: null,
  preEpochHistory: null,
  evidenceHistory: null,
  riskEscalationHistory: null,
  sourceSnapshotHistory: null,
  conversationHistory: null,
  events: Object.freeze([]),
});

export function buildV2HistoryPortfolio(latest: OrganizationReplayLatest | null | undefined): V2HistoryPortfolio {
  const replay = latest?.established ? latest.replay : null;
  if (!replay) return emptyPortfolio;
  return {
    established: true,
    contractVersion: replay.contract_version,
    generatedAt: replay.generated_at,
    rootWorkItemId: replay.root_work_item_id,
    objectiveKey: replay.objective_key,
    canonicalProjection: replay.canonical_projection,
    authoritative: replay.authoritative,
    mutationsAllowed: replay.mutations_allowed,
    totalEvents: replay.total_events,
    returnedEvents: replay.returned_events,
    truncated: replay.truncated,
    activityHistoryEstablished: replay.coverage.activity_history_established,
    activityHistoryBasis: replay.coverage.activity_history_basis,
    activityHistoryCoverageStart: replay.coverage.activity_history_coverage_start,
    preEpochHistory: replay.coverage.pre_epoch_history,
    evidenceHistory: replay.coverage.evidence_history,
    riskEscalationHistory: replay.coverage.risk_escalation_history,
    sourceSnapshotHistory: replay.coverage.source_snapshot_history,
    conversationHistory: replay.coverage.conversation_history,
    // Preserve the backend's canonical replay ordering. Q8 never re-ranks history.
    events: replay.events,
  };
}

export function selectV2HistoryEvent(events: readonly OrganizationReplayEvent[], activityId: string | null | undefined) {
  if (!activityId) return null;
  return events.find((event) => event.activity_id === activityId) ?? null;
}

export function historyEventDestination(activityId: string, compareFromActivityId?: string | null) {
  const params = new URLSearchParams({ cursor: activityId });
  if (compareFromActivityId && compareFromActivityId !== activityId) params.set("from", compareFromActivityId);
  return `/cockpit/v2/history?${params.toString()}`;
}

export function summarizeV2ReplayState(state: OrganizationReplayState | null) {
  if (!state) return null;
  return {
    workItemCount: state.work_items.length,
    blockerCount: state.blockers.length,
    decisionCount: state.decisions.length,
    humanRequestCount: state.human_requests.length,
    conversationCount: state.conversations.length,
    cursorCoverageState: state.cursor_coverage_state,
    reconstructionPosture: state.reconstruction_posture,
    unappliedTransitionCount: state.unapplied_transition_count,
    supportedDimensions: state.supported_dimensions,
    unsupportedDimensions: state.unsupported_dimensions,
    canonicalProjection: state.canonical_projection,
    authoritative: state.authoritative,
    mutationsAllowed: state.mutations_allowed,
  };
}

export type V2ReplaySemanticKind =
  | "completed"
  | "active"
  | "resolved"
  | "approved"
  | "rejected"
  | "pending"
  | "closed"
  | "neutral";

export type V2ReplaySemanticState = {
  kind: V2ReplaySemanticKind;
  label: string;
  truthScope: "historical_cursor";
};

function historicalLabel(status: string): V2ReplaySemanticState {
  return { kind: "neutral", label: `${status} at this cursor`, truthScope: "historical_cursor" };
}

export function replaySemanticState(groupLabel: string, status: string): V2ReplaySemanticState {
  const group = groupLabel.trim().toLowerCase();

  // Phase 7H deliberately recognizes only exact canonical lifecycle values.
  // Unknown aliases remain literal historical labels rather than being promoted
  // to stronger completion/resolution/decision semantics.
  if (group === "work items") {
    if (status === "completed") {
      return { kind: "completed", label: "Completed at this cursor", truthScope: "historical_cursor" };
    }
    return historicalLabel(status);
  }

  if (group === "blockers") {
    if (status === "resolved") {
      return { kind: "resolved", label: "Resolved at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "waived") {
      return { kind: "closed", label: "Waived at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "superseded") {
      return { kind: "closed", label: "Superseded at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "open" || status === "mitigated") {
      return { kind: "active", label: `${status} blocker at this cursor`, truthScope: "historical_cursor" };
    }
    return historicalLabel(status);
  }

  if (group === "decisions") {
    if (status === "approved") {
      return { kind: "approved", label: "Approved at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "rejected") {
      return { kind: "rejected", label: "Rejected at this cursor", truthScope: "historical_cursor" };
    }
    return historicalLabel(status);
  }

  if (group === "human requests") {
    if (status === "completed") {
      return { kind: "completed", label: "Completed at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "declined" || status === "cancelled" || status === "expired") {
      return { kind: "closed", label: `${status} at this cursor`, truthScope: "historical_cursor" };
    }
    if (status === "required" || status === "acknowledged" || status === "in_progress") {
      return { kind: "pending", label: `${status} at this cursor`, truthScope: "historical_cursor" };
    }
    return historicalLabel(status);
  }

  if (group === "conversations") {
    if (status === "closed") {
      return { kind: "closed", label: "Closed at this cursor", truthScope: "historical_cursor" };
    }
    if (status === "open") {
      return { kind: "active", label: "Open at this cursor", truthScope: "historical_cursor" };
    }
    return historicalLabel(status);
  }

  return historicalLabel(status);
}

export type V2ReplayStateRow = {
  id: string;
  status: string;
  coverageState: string;
  lastOccurredAt: string;
  semantic: V2ReplaySemanticState;
};

export type V2ReplayStateGroup = {
  label: string;
  rows: readonly V2ReplayStateRow[];
};

function stateRow(groupLabel: string, id: string, value: { status: string; coverage_state: string; last_occurred_at: string }): V2ReplayStateRow {
  return {
    id,
    status: value.status,
    coverageState: value.coverage_state,
    lastOccurredAt: value.last_occurred_at,
    semantic: replaySemanticState(groupLabel, value.status),
  };
}

export function replayStateGroups(state: OrganizationReplayState | null): readonly V2ReplayStateGroup[] {
  if (!state) return [];
  return [
    { label: "Work items", rows: state.work_items.map((item) => stateRow("Work items", item.work_item_id, item)) },
    { label: "Blockers", rows: state.blockers.map((item) => stateRow("Blockers", item.blocker_id, item)) },
    { label: "Decisions", rows: state.decisions.map((item) => stateRow("Decisions", item.decision_id, item)) },
    { label: "Human requests", rows: state.human_requests.map((item) => stateRow("Human requests", item.request_id, item)) },
    { label: "Conversations", rows: state.conversations.map((item) => stateRow("Conversations", item.conversation_id, item)) },
  ];
}

export type V2ReplayDiffItem = {
  entityId: string;
  changeKind: string;
  changedFields: readonly string[];
};

export type V2ReplayDiffGroup = {
  label: string;
  items: readonly V2ReplayDiffItem[];
};

function normalizeDeltas(items: readonly { entity_id: string; change_kind: string; changed_fields: string[] }[]): V2ReplayDiffItem[] {
  return items.map((item) => ({ entityId: item.entity_id, changeKind: item.change_kind, changedFields: item.changed_fields }));
}

export function replayDiffGroups(diff: OrganizationReplayStateDiff | null): readonly V2ReplayDiffGroup[] {
  if (!diff) return [];
  return [
    { label: "Work items", items: normalizeDeltas(diff.work_items) },
    { label: "Blockers", items: normalizeDeltas(diff.blockers) },
    { label: "Decisions", items: normalizeDeltas(diff.decisions) },
    { label: "Human requests", items: normalizeDeltas(diff.human_requests) },
    { label: "Conversations", items: normalizeDeltas(diff.conversations) },
  ];
}
