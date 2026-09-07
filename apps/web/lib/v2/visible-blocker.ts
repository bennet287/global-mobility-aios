import type {
  LivingSceneBlocker,
  LivingSceneEmployee,
} from "../live-organization";

export const V2_CANONICAL_BLOCKER_COVERAGE =
  "organization_blocker_canonical_records" as const;

export type V2VisibleBlockerRelation =
  | "accountable_position"
  | "unique_work_item";

export type V2VisibleBlockerItem = {
  readonly blockerId: string;
  readonly workItemId: string | null;
  readonly positionKey: string;
  readonly relation: V2VisibleBlockerRelation;
  readonly title: string;
  readonly description: string;
  readonly blockerType: string;
  readonly severity: string;
  readonly status: string;
  readonly requiresHumanAction: boolean;
  readonly openedAt: string;
  readonly dueAt: string | null;
  readonly overdue: boolean;
  readonly decisionId: string | null;
  readonly riskEscalationId: string | null;
  readonly truth: {
    readonly canonicalSource: "LivingSceneBlocker";
    readonly accountablePositionClaimed: boolean;
    readonly causalBlockClaimed: false;
    readonly resolutionClaimed: false;
    readonly physicalPresenceClaimed: false;
    readonly physicalLocationClaimed: false;
    readonly canonicalMutationAllowed: false;
  };
};

export type V2VisibleBlockerCollection = {
  readonly supported: boolean;
  readonly coverageState: string;
  readonly items: readonly V2VisibleBlockerItem[];
  readonly limitation: string | null;
};

export type V2VisibleBlockerSummary = {
  readonly positionKey: string;
  readonly count: number;
  readonly single: V2VisibleBlockerItem | null;
  readonly label: string;
};

export type V2CanonicalBlockerSelection = {
  readonly supported: boolean;
  readonly coverageState: string;
  readonly blockers: readonly LivingSceneBlocker[];
  readonly blockerIds: readonly string[];
};

function normalized(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim() : "";
}

function uniqueEmployeeByPosition(
  employees: readonly LivingSceneEmployee[],
  positionKey: string,
): LivingSceneEmployee | null {
  const matches = employees.filter(
    (employee) => normalized(employee.position_key) === positionKey,
  );
  return matches.length === 1 ? matches[0] : null;
}

function uniqueEmployeeByWorkItem(
  employees: readonly LivingSceneEmployee[],
  workItemId: string,
): LivingSceneEmployee | null {
  const matches = employees.filter(
    (employee) => normalized(employee.work_item_id) === workItemId,
  );
  return matches.length === 1 ? matches[0] : null;
}

function blockerItem(
  blocker: LivingSceneBlocker,
  employee: LivingSceneEmployee,
  relation: V2VisibleBlockerRelation,
): V2VisibleBlockerItem | null {
  const blockerId = normalized(blocker.blocker_id);
  const title = normalized(blocker.title);
  const severity = normalized(blocker.severity);
  const status = normalized(blocker.status);
  const blockerType = normalized(blocker.blocker_type);
  const positionKey = normalized(employee.position_key);

  if (!blockerId || !title || !severity || !status || !blockerType || !positionKey) {
    return null;
  }

  return {
    blockerId,
    workItemId: normalized(blocker.work_item_id) || null,
    positionKey,
    relation,
    title,
    description: normalized(blocker.description),
    blockerType,
    severity,
    status,
    requiresHumanAction: Boolean(blocker.requires_human_action),
    openedAt: normalized(blocker.opened_at),
    dueAt: normalized(blocker.due_at) || null,
    overdue: Boolean(blocker.overdue),
    decisionId: normalized(blocker.decision_id) || null,
    riskEscalationId: normalized(blocker.risk_escalation_id) || null,
    truth: {
      canonicalSource: "LivingSceneBlocker",
      accountablePositionClaimed: relation === "accountable_position",
      causalBlockClaimed: false,
      resolutionClaimed: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      canonicalMutationAllowed: false,
    },
  };
}

export function buildV2VisibleBlockers({
  blockers,
  employees,
  coverageState,
}: {
  readonly blockers: readonly LivingSceneBlocker[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly coverageState: string | null | undefined;
}): V2VisibleBlockerCollection {
  const coverage = normalized(coverageState) || "unavailable";
  if (coverage !== V2_CANONICAL_BLOCKER_COVERAGE) {
    return {
      supported: false,
      coverageState: coverage,
      items: [],
      limitation:
        "Canonical blocker detail is unavailable for this scene coverage state. AIOS will not infer blocker title, type, severity or accountability from employee work state.",
    };
  }

  const items: V2VisibleBlockerItem[] = [];

  for (const blocker of blockers) {
    const accountablePositionKey = normalized(blocker.accountable_position_key);
    if (accountablePositionKey) {
      const employee = uniqueEmployeeByPosition(employees, accountablePositionKey);
      if (!employee) continue;
      const item = blockerItem(blocker, employee, "accountable_position");
      if (item) items.push(item);
      continue;
    }

    const workItemId = normalized(blocker.work_item_id);
    if (!workItemId) continue;
    const employee = uniqueEmployeeByWorkItem(employees, workItemId);
    if (!employee) continue;
    const item = blockerItem(blocker, employee, "unique_work_item");
    if (item) items.push(item);
  }

  items.sort((left, right) =>
    `${left.positionKey}:${left.blockerId}`.localeCompare(
      `${right.positionKey}:${right.blockerId}`,
    ),
  );

  return {
    supported: true,
    coverageState: coverage,
    items,
    limitation: null,
  };
}

export function visibleBlockersForPosition(
  collection: V2VisibleBlockerCollection,
  positionKey: string,
): readonly V2VisibleBlockerItem[] {
  if (!collection.supported) return [];
  return collection.items.filter((item) => item.positionKey === positionKey);
}

export function selectV2CanonicalBlockersForPosition({
  blockers,
  employees,
  coverageState,
  positionKey,
}: {
  readonly blockers: readonly LivingSceneBlocker[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly coverageState: string | null | undefined;
  readonly positionKey: string;
}): V2CanonicalBlockerSelection {
  const collection = buildV2VisibleBlockers({
    blockers,
    employees,
    coverageState,
  });
  const items = visibleBlockersForPosition(collection, positionKey);
  const selected = items
    .map((item) =>
      blockers.find(
        (blocker) => normalized(blocker.blocker_id) === item.blockerId,
      ),
    )
    .filter((blocker): blocker is LivingSceneBlocker => blocker !== undefined);

  return {
    supported: collection.supported,
    coverageState: collection.coverageState,
    blockers: selected,
    blockerIds: selected.map((blocker) => blocker.blocker_id),
  };
}

export function summarizeV2VisibleBlockers(
  collection: V2VisibleBlockerCollection,
  positionKey: string,
): V2VisibleBlockerSummary | null {
  const items = visibleBlockersForPosition(collection, positionKey);
  if (!items.length) return null;

  if (items.length === 1) {
    const single = items[0];
    return {
      positionKey,
      count: 1,
      single,
      label: `${single.severity.toUpperCase()} blocker`,
    };
  }

  return {
    positionKey,
    count: items.length,
    single: null,
    label: `${items.length} blockers`,
  };
}
