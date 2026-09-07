import type {
  LivingSceneConversation,
  LivingSceneEmployee,
  LivingSceneWorkItem,
} from "../live-organization";

export const V2_CANONICAL_CONVERSATION_COVERAGE =
  "organization_activity_conversation_lifecycle_v1" as const;

export type V2VisibleConversationParticipant = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
};

export type V2VisibleConversationItem = {
  readonly conversationId: string;
  readonly workItemId: string;
  readonly participantPositionKeys: readonly string[];
  readonly participants: readonly V2VisibleConversationParticipant[];
  readonly status: string;
  readonly summary: string;
  readonly openedAt: string;
  readonly lifecycleAt: string;
  readonly authorityEffect: "none";
  readonly transcriptPersisted: false;
  readonly truth: {
    readonly canonicalSource: "LivingSceneConversation";
    readonly conversationLifecycleClaimed: true;
    readonly speechClaimed: false;
    readonly transcriptClaimed: false;
    readonly physicalPresenceClaimed: false;
    readonly physicalLocationClaimed: false;
    readonly authorityOutcomeClaimed: false;
    readonly canonicalMutationAllowed: false;
  };
};

export type V2VisibleConversationCollection = {
  readonly supported: boolean;
  readonly coverageState: string;
  readonly items: readonly V2VisibleConversationItem[];
  readonly limitation: string | null;
};

export type V2VisibleConversationSummary = {
  readonly positionKey: string;
  readonly count: number;
  readonly openCount: number;
  readonly latest: V2VisibleConversationItem;
  readonly label: string;
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

function uniqueWorkItemById(
  workItems: readonly LivingSceneWorkItem[],
  workItemId: string,
): LivingSceneWorkItem | null {
  const matches = workItems.filter(
    (workItem) => normalized(workItem.work_item_id) === workItemId,
  );
  return matches.length === 1 ? matches[0] : null;
}

function conversationItem(
  conversation: LivingSceneConversation,
  employees: readonly LivingSceneEmployee[],
  workItems: readonly LivingSceneWorkItem[],
): V2VisibleConversationItem | null {
  const conversationId = normalized(conversation.conversation_id);
  const workItemId = normalized(conversation.work_item_id);
  const status = normalized(conversation.status);
  const summary = normalized(conversation.summary);
  const participantPositionKeys = conversation.participant_position_keys.map(normalized);

  if (
    !conversationId ||
    !workItemId ||
    !status ||
    !summary ||
    participantPositionKeys.length < 2 ||
    participantPositionKeys.some((positionKey) => !positionKey) ||
    new Set(participantPositionKeys).size !== participantPositionKeys.length ||
    conversation.authority_effect !== "none" ||
    conversation.transcript_persisted !== false
  ) {
    return null;
  }

  const workItem = uniqueWorkItemById(workItems, workItemId);
  if (
    !workItem ||
    !participantPositionKeys.includes(normalized(workItem.assigned_position_key))
  ) {
    return null;
  }

  const participants: V2VisibleConversationParticipant[] = [];
  for (const positionKey of participantPositionKeys) {
    const employee = uniqueEmployeeByPosition(employees, positionKey);
    if (!employee) return null;
    participants.push({
      positionKey,
      title: normalized(employee.title) || positionKey,
      department: normalized(employee.department),
    });
  }

  return {
    conversationId,
    workItemId,
    participantPositionKeys,
    participants,
    status,
    summary,
    openedAt: normalized(conversation.opened_at),
    lifecycleAt: normalized(conversation.lifecycle_at),
    authorityEffect: "none",
    transcriptPersisted: false,
    truth: {
      canonicalSource: "LivingSceneConversation",
      conversationLifecycleClaimed: true,
      speechClaimed: false,
      transcriptClaimed: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      authorityOutcomeClaimed: false,
      canonicalMutationAllowed: false,
    },
  };
}

export function buildV2VisibleConversations({
  conversations,
  employees,
  workItems,
  coverageState,
}: {
  readonly conversations: readonly LivingSceneConversation[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly workItems: readonly LivingSceneWorkItem[];
  readonly coverageState: string | null | undefined;
}): V2VisibleConversationCollection {
  const coverage = normalized(coverageState) || "unavailable";
  if (coverage !== V2_CANONICAL_CONVERSATION_COVERAGE) {
    return {
      supported: false,
      coverageState: coverage,
      items: [],
      limitation:
        "Governed conversation lifecycle is unavailable for this scene coverage state. AIOS will not infer dialogue, participation, transcript or authority from other activity.",
    };
  }

  const items = conversations
    .map((conversation) => conversationItem(conversation, employees, workItems))
    .filter((item): item is V2VisibleConversationItem => item !== null)
    .sort((left, right) => {
      const lifecycleOrder = right.lifecycleAt.localeCompare(left.lifecycleAt);
      return lifecycleOrder !== 0
        ? lifecycleOrder
        : left.conversationId.localeCompare(right.conversationId, undefined, {
            numeric: true,
            sensitivity: "base",
          });
    });

  return {
    supported: true,
    coverageState: coverage,
    items,
    limitation: null,
  };
}

export function visibleConversationsForPosition(
  collection: V2VisibleConversationCollection,
  positionKey: string,
): readonly V2VisibleConversationItem[] {
  if (!collection.supported) return [];
  const key = normalized(positionKey);
  if (!key) return [];
  return collection.items.filter((item) => item.participantPositionKeys.includes(key));
}

export function visibleConversationsForWorkItem(
  collection: V2VisibleConversationCollection,
  workItemId: string,
): readonly V2VisibleConversationItem[] {
  if (!collection.supported) return [];
  const id = normalized(workItemId);
  if (!id) return [];
  return collection.items.filter((item) => item.workItemId === id);
}

export function summarizeV2VisibleConversations(
  collection: V2VisibleConversationCollection,
  positionKey: string,
): V2VisibleConversationSummary | null {
  const items = visibleConversationsForPosition(collection, positionKey);
  if (!items.length) return null;
  const openCount = items.filter((item) => item.status === "open").length;
  return {
    positionKey,
    count: items.length,
    openCount,
    latest: items[0],
    label:
      openCount > 0
        ? `${openCount} governed conversation${openCount === 1 ? "" : "s"} open`
        : `${items.length} governed conversation${items.length === 1 ? "" : "s"}`,
  };
}
