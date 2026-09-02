"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  BoardPacketSnapshot,
  OrganizationActivity,
  OrganizationBlocker,
  OrganizationHumanActionRequest,
  OrganizationWorkItemDependency,
  OrganizationalWorkItem,
  getBoardPacket,
  listOrganizationActivities,
  listOrganizationBlockers,
  listOrganizationHumanActionRequests,
  listOrganizationWorkItemDependencies,
  listOrganizationWorkItems,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const ACTIVE_HUMAN_REQUEST_STATUSES = new Set(["required", "acknowledged", "in_progress"]);
const TERMINAL_WORK_STATUSES = new Set(["completed", "cancelled", "failed", "superseded"]);
const BOARD_HUMAN_ROLES = new Set(["board"]);
const BOARD_POSITION_KEYS = new Set(["board"]);

type AttentionItem = {
  key: string;
  kind: "decision" | "risk" | "human request" | "work" | "blocker" | "dependency";
  title: string;
  summary: string;
  why: string;
  impact: string;
  authority: string;
  timing: string;
  href: string;
  actionLabel: string;
  rank: number;
  createdAt: string;
  activity: OrganizationActivity | null;
};

function isActiveWork(work: OrganizationalWorkItem): boolean {
  return !TERMINAL_WORK_STATUSES.has(work.status);
}

function isBoardOwnedWork(work: OrganizationalWorkItem | undefined): boolean {
  if (!work) return false;
  return work.authority_level === "L4" || BOARD_POSITION_KEYS.has(work.assigned_position_key);
}

function isOverdue(value: string | null): boolean {
  if (!value) return false;
  const date = new Date(value);
  return !Number.isNaN(date.getTime()) && date.getTime() < Date.now();
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "No due date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function sortAttention(items: AttentionItem[]): AttentionItem[] {
  return [...items].sort((a, b) => {
    if (a.rank !== b.rank) return b.rank - a.rank;
    return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
  });
}

function AttentionCard({ item }: { item: AttentionItem }) {
  return (
    <article className="owner-inbox-item">
      <div className="owner-inbox-item-main">
        <span className={`owner-inbox-kind kind-${item.kind.replace(" ", "-")}`}>{titleCase(item.kind)}</span>
        <h3>{item.title}</h3>
        <p>{item.summary}</p>
      </div>

      <dl className="owner-inbox-facts">
        <div>
          <dt>Why you are seeing this</dt>
          <dd>{item.why}</dd>
        </div>
        <div>
          <dt>Impact</dt>
          <dd>{item.impact}</dd>
        </div>
        <div>
          <dt>Authority</dt>
          <dd>{item.authority}</dd>
        </div>
        <div>
          <dt>Timing</dt>
          <dd>{item.timing}</dd>
        </div>
        {item.activity ? (
          <div>
            <dt>Latest durable signal</dt>
            <dd>{item.activity.title}</dd>
          </div>
        ) : null}
      </dl>

      <Link className="owner-inbox-route" href={item.href}>
        {item.actionLabel} <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}

function AttentionLane({
  tier,
  eyebrow,
  title,
  description,
  items,
  emptyTitle,
  emptyDetail,
}: {
  tier: "one" | "two" | "three" | "four";
  eyebrow: string;
  title: string;
  description: string;
  items: AttentionItem[];
  emptyTitle: string;
  emptyDetail: string;
}) {
  return (
    <section className={`owner-inbox-lane tier-${tier}`} aria-labelledby={`owner-inbox-${tier}`}>
      <header>
        <div className="owner-inbox-tier-index" aria-hidden="true">
          {tier === "one" ? "01" : tier === "two" ? "02" : tier === "three" ? "03" : "04"}
        </div>
        <div>
          <span className="premium-label">{eyebrow}</span>
          <h2 id={`owner-inbox-${tier}`}>{title}</h2>
          <p>{description}</p>
        </div>
        <strong className="owner-inbox-count">{items.length}</strong>
      </header>

      {items.length ? (
        <div className="owner-inbox-list">
          {items.map((item) => <AttentionCard key={item.key} item={item} />)}
        </div>
      ) : (
        <div className="owner-inbox-empty">
          <span aria-hidden="true">✓</span>
          <div>
            <strong>{emptyTitle}</strong>
            <p>{emptyDetail}</p>
          </div>
        </div>
      )}
    </section>
  );
}

export default function OwnerInboxPage() {
  const { health } = useBackendStatus();
  const [packet, setPacket] = useState<BoardPacketSnapshot | null>(null);
  const [humanRequests, setHumanRequests] = useState<OrganizationHumanActionRequest[]>([]);
  const [workItems, setWorkItems] = useState<OrganizationalWorkItem[]>([]);
  const [blockers, setBlockers] = useState<OrganizationBlocker[]>([]);
  const [dependencies, setDependencies] = useState<OrganizationWorkItemDependency[]>([]);
  const [activities, setActivities] = useState<OrganizationActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      getBoardPacket(),
      listOrganizationHumanActionRequests({ page_size: 100 }),
      listOrganizationWorkItems({ page_size: 100 }),
      listOrganizationBlockers({ status: "open", page_size: 100 }),
      listOrganizationWorkItemDependencies({ status: "active", page_size: 100 }),
      listOrganizationActivities({ page_size: 200 }),
    ]);

    const failures: string[] = [];
    const [packetResult, humanResult, workResult, blockerResult, dependencyResult, activityResult] = results;

    if (packetResult.status === "fulfilled") setPacket(packetResult.value);
    else failures.push("Board Packet");

    if (humanResult.status === "fulfilled") setHumanRequests(humanResult.value.data);
    else failures.push("human requests");

    if (workResult.status === "fulfilled") setWorkItems(workResult.value.data);
    else failures.push("work");

    if (blockerResult.status === "fulfilled") setBlockers(blockerResult.value.data);
    else failures.push("blockers");

    if (dependencyResult.status === "fulfilled") setDependencies(dependencyResult.value.data);
    else failures.push("dependencies");

    if (activityResult.status === "fulfilled") setActivities(activityResult.value.data);
    else failures.push("Activity");

    if (failures.length) {
      setError(`Some Owner Inbox signals are temporarily unavailable: ${failures.join(", ")}.`);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const model = useMemo(() => {
    const workById = new Map(workItems.map((work) => [work.id, work]));
    const blockerById = new Map(blockers.map((blocker) => [blocker.id, blocker]));
    const pendingBoardDecisions = (packet?.pending_decisions || []).filter(
      (decision) => decision.status === "pending_board",
    );
    const pendingBoardDecisionIds = new Set(pendingBoardDecisions.map((decision) => decision.id));
    const boardRisks = (packet?.open_risks || []).filter((risk) => risk.requires_board_attention);
    const orderedActivities = [...activities].sort(
      (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime(),
    );

    const activityFor = (
      sourceObjectType?: string | null,
      sourceObjectId?: string | null,
      workItemId?: string | null,
    ) => orderedActivities.find((activity) => {
      if (
        sourceObjectType &&
        sourceObjectId &&
        activity.source_object_type === sourceObjectType &&
        activity.source_object_id === sourceObjectId
      ) return true;
      return Boolean(workItemId && activity.work_item_id === workItemId);
    }) || null;

    const ownerRelevantHumanRequests = humanRequests.filter((request) => {
      if (!ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status)) return false;

      const role = request.required_role.trim().toLowerCase().replaceAll("-", "_");
      if (BOARD_HUMAN_ROLES.has(role)) return true;
      if (request.decision_id && pendingBoardDecisionIds.has(request.decision_id)) return true;

      const work = request.work_item_id ? workById.get(request.work_item_id) : undefined;
      if (isBoardOwnedWork(work)) return true;

      const blocker = request.blocker_id ? blockerById.get(request.blocker_id) : undefined;
      if (blocker?.accountable_position_key && BOARD_POSITION_KEYS.has(blocker.accountable_position_key)) return true;

      const blockerWork = blocker?.work_item_id ? workById.get(blocker.work_item_id) : undefined;
      return isBoardOwnedWork(blockerWork);
    });

    const humanRequestByDependencyId = new Map(
      ownerRelevantHumanRequests
        .filter(
          (request) =>
            request.source_object_type === "organization_work_item_dependency" &&
            request.source_object_id,
        )
        .map((request) => [request.source_object_id as string, request]),
    );

    const decisionItems: AttentionItem[] = pendingBoardDecisions.map((decision) => ({
      key: `decision:${decision.id}`,
      kind: "decision",
      title: decision.title,
      summary: decision.recommendation || decision.question,
      why: "The decision is explicitly in pending_board state.",
      impact: decision.question,
      authority: `${decision.authority_level} · ${decision.decision_owner_position.replaceAll("_", " ").toUpperCase()}`,
      timing: "Board decision required",
      href: "/board-room",
      actionLabel: "Review in Board Room",
      rank: 100,
      createdAt: decision.created_at,
      activity: activityFor("executive_decision", decision.id, null),
    }));

    const criticalItems: AttentionItem[] = [];

    for (const risk of boardRisks) {
      if (!["critical", "high"].includes(risk.severity)) continue;
      criticalItems.push({
        key: `risk:${risk.id}`,
        kind: "risk",
        title: risk.title,
        summary: risk.description,
        why: "The risk explicitly requires Board attention.",
        impact: `${titleCase(risk.category)} exception`,
        authority: `Escalated to ${risk.escalated_to_position_key.replaceAll("_", " ").toUpperCase()}`,
        timing: `${titleCase(risk.severity)} severity`,
        href: "/board-room",
        actionLabel: "Open Board Room",
        rank: risk.severity === "critical" ? 100 : 92,
        createdAt: risk.created_at,
        activity: null,
      });
    }

    for (const request of ownerRelevantHumanRequests) {
      if (request.priority !== "critical") continue;
      if (request.decision_id && pendingBoardDecisionIds.has(request.decision_id)) continue;
      const work = request.work_item_id ? workById.get(request.work_item_id) : undefined;
      criticalItems.push({
        key: `human-critical:${request.id}`,
        kind: "human request",
        title: request.title,
        summary: request.instructions,
        why: "Critical human request with explicit Owner/Board authority evidence.",
        impact: work ? `${work.department} · ${work.title}` : "Human authority required",
        authority: `Required role ${request.required_role.replaceAll("_", " ")}`,
        timing: request.due_at ? `${isOverdue(request.due_at) ? "Overdue" : "Due"} · ${formatDate(request.due_at)}` : "Critical priority",
        href: request.decision_id
          ? "/board-room"
          : request.source_object_type === "organization_work_item_dependency"
            ? "/cross-department-friction"
            : work
              ? `/workspace/${encodeURIComponent(work.department)}`
              : "/cockpit",
        actionLabel: request.decision_id ? "Open Board Room" : "Open governed context",
        rank: 96,
        createdAt: request.created_at,
        activity: activityFor(request.source_object_type, request.source_object_id, request.work_item_id),
      });
    }

    for (const work of workItems) {
      if (!isActiveWork(work) || !work.is_emergency) continue;
      criticalItems.push({
        key: `emergency-work:${work.id}`,
        kind: "work",
        title: work.title,
        summary: work.objective,
        why: "The work item is explicitly marked emergency.",
        impact: `${work.department} · ${titleCase(work.risk_level)} risk`,
        authority: `${work.authority_level} · ${work.assigned_position_key.replaceAll("_", " ").toUpperCase()}`,
        timing: work.due_at ? `${isOverdue(work.due_at) ? "Overdue" : "Due"} · ${formatDate(work.due_at)}` : "Emergency state active",
        href: `/workspace/${encodeURIComponent(work.department)}`,
        actionLabel: "Open department workspace",
        rank: isBoardOwnedWork(work) ? 94 : 88,
        createdAt: work.created_at,
        activity: activityFor("organizational_work_item", work.id, work.id),
      });
    }

    for (const blocker of blockers) {
      const work = blocker.work_item_id ? workById.get(blocker.work_item_id) : undefined;
      const boardOwned =
        (blocker.accountable_position_key && BOARD_POSITION_KEYS.has(blocker.accountable_position_key)) ||
        isBoardOwnedWork(work);
      if (blocker.severity !== "critical" || !boardOwned) continue;
      criticalItems.push({
        key: `critical-blocker:${blocker.id}`,
        kind: "blocker",
        title: blocker.title,
        summary: blocker.description,
        why: "Critical blocker is attached to Board-owned or Board-accountable work.",
        impact: work ? `${work.department} · ${work.title}` : blocker.department || "Organization-wide",
        authority: blocker.accountable_position_key
          ? blocker.accountable_position_key.replaceAll("_", " ").toUpperCase()
          : work?.authority_level || "Board-owned context",
        timing: blocker.due_at ? `${isOverdue(blocker.due_at) ? "Overdue" : "Due"} · ${formatDate(blocker.due_at)}` : "Critical blocker open",
        href: work ? `/workspace/${encodeURIComponent(work.department)}` : "/cross-department-friction",
        actionLabel: work ? "Open department workspace" : "Open friction view",
        rank: 93,
        createdAt: blocker.created_at,
        activity: activityFor("organization_blocker", blocker.id, blocker.work_item_id),
      });
    }

    const escalatedItems: AttentionItem[] = [];

    for (const request of ownerRelevantHumanRequests) {
      if (request.priority === "critical") continue;
      if (request.decision_id && pendingBoardDecisionIds.has(request.decision_id)) continue;
      const work = request.work_item_id ? workById.get(request.work_item_id) : undefined;
      const blocker = request.blocker_id ? blockerById.get(request.blocker_id) : undefined;
      const href = request.decision_id
        ? "/board-room"
        : request.source_object_type === "organization_work_item_dependency"
          ? "/cross-department-friction"
          : work
            ? `/workspace/${encodeURIComponent(work.department)}`
            : blocker?.department
              ? `/workspace/${encodeURIComponent(blocker.department)}`
              : "/cockpit";

      const priorityRank = request.priority === "high" ? 86 : request.priority === "normal" ? 76 : 70;
      escalatedItems.push({
        key: `human:${request.id}`,
        kind: "human request",
        title: request.title,
        summary: request.instructions,
        why: "Active human request has explicit Owner/Board authority evidence.",
        impact: work ? `${work.department} · ${work.title}` : blocker?.title || "Human authority required",
        authority: `Required role ${request.required_role.replaceAll("_", " ")}`,
        timing: request.due_at ? `${isOverdue(request.due_at) ? "Overdue" : "Due"} · ${formatDate(request.due_at)}` : `${titleCase(request.priority)} priority`,
        href,
        actionLabel: "Open governed context",
        rank: isOverdue(request.due_at) ? priorityRank + 6 : priorityRank,
        createdAt: request.created_at,
        activity: activityFor(request.source_object_type, request.source_object_id, request.work_item_id),
      });
    }

    for (const work of workItems) {
      if (!isActiveWork(work) || work.is_emergency || !isBoardOwnedWork(work) || !isOverdue(work.due_at)) continue;
      escalatedItems.push({
        key: `overdue-board-work:${work.id}`,
        kind: "work",
        title: work.title,
        summary: work.objective,
        why: "Board-owned work is past its explicit due date.",
        impact: `${work.department} · ${titleCase(work.risk_level)} risk`,
        authority: `${work.authority_level} · ${work.assigned_position_key.replaceAll("_", " ").toUpperCase()}`,
        timing: `Overdue · ${formatDate(work.due_at)}`,
        href: `/workspace/${encodeURIComponent(work.department)}`,
        actionLabel: "Open department workspace",
        rank: 84,
        createdAt: work.created_at,
        activity: activityFor("organizational_work_item", work.id, work.id),
      });
    }

    for (const dependency of dependencies) {
      const downstream = workById.get(dependency.work_item_id);
      const upstream = workById.get(dependency.depends_on_work_item_id);
      if (!isBoardOwnedWork(downstream) || humanRequestByDependencyId.has(dependency.id)) continue;

      const crossDepartment = Boolean(
        downstream && upstream && downstream.department !== upstream.department,
      );
      escalatedItems.push({
        key: `dependency:${dependency.id}`,
        kind: "dependency",
        title: downstream?.title || "Board-owned work dependency",
        summary: upstream
          ? `Depends on ${upstream.title}.`
          : `Depends on work ${dependency.depends_on_work_item_id.slice(0, 8)}.`,
        why: "Unresolved dependency blocks Board-owned downstream work.",
        impact: downstream ? `${downstream.department} · downstream work` : "Board-owned downstream work",
        authority: downstream
          ? `${downstream.authority_level} · ${downstream.assigned_position_key.replaceAll("_", " ").toUpperCase()}`
          : "Board-owned context",
        timing: downstream?.due_at
          ? `${isOverdue(downstream.due_at) ? "Downstream overdue" : "Downstream due"} · ${formatDate(downstream.due_at)}`
          : "Active dependency",
        href: crossDepartment
          ? "/cross-department-friction"
          : downstream
            ? `/workspace/${encodeURIComponent(downstream.department)}`
            : "/cross-department-friction",
        actionLabel: crossDepartment ? "Open friction view" : "Open department workspace",
        rank: downstream?.due_at && isOverdue(downstream.due_at) ? 82 : 74,
        createdAt: dependency.created_at,
        activity: activityFor("organization_work_item_dependency", dependency.id, dependency.work_item_id),
      });
    }

    const watchItems: AttentionItem[] = [];

    for (const risk of boardRisks) {
      if (["critical", "high"].includes(risk.severity)) continue;
      watchItems.push({
        key: `watch-risk:${risk.id}`,
        kind: "risk",
        title: risk.title,
        summary: risk.description,
        why: "The risk explicitly requires Board attention but is below High severity.",
        impact: `${titleCase(risk.category)} exception`,
        authority: `Escalated to ${risk.escalated_to_position_key.replaceAll("_", " ").toUpperCase()}`,
        timing: `${titleCase(risk.severity)} severity`,
        href: "/board-room",
        actionLabel: "Open Board Room",
        rank: risk.severity === "medium" ? 60 : 50,
        createdAt: risk.created_at,
        activity: null,
      });
    }

    for (const work of workItems) {
      if (
        !isActiveWork(work) ||
        work.is_emergency ||
        !isBoardOwnedWork(work) ||
        isOverdue(work.due_at) ||
        !["high", "critical"].includes(work.risk_level)
      ) continue;

      watchItems.push({
        key: `watch-work:${work.id}`,
        kind: "work",
        title: work.title,
        summary: work.objective,
        why: "Board-owned work carries elevated recorded risk without a current overdue or emergency state.",
        impact: work.department,
        authority: `${work.authority_level} · ${work.assigned_position_key.replaceAll("_", " ").toUpperCase()}`,
        timing: work.due_at ? `Due · ${formatDate(work.due_at)}` : "No due date",
        href: `/workspace/${encodeURIComponent(work.department)}`,
        actionLabel: "Open department workspace",
        rank: work.risk_level === "critical" ? 62 : 56,
        createdAt: work.created_at,
        activity: activityFor("organizational_work_item", work.id, work.id),
      });
    }

    return {
      decisionItems: sortAttention(decisionItems),
      criticalItems: sortAttention(criticalItems),
      escalatedItems: sortAttention(escalatedItems),
      watchItems: sortAttention(watchItems),
      delegatedHumanCount: humanRequests.filter(
        (request) =>
          ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status) &&
          !ownerRelevantHumanRequests.some((ownerRequest) => ownerRequest.id === request.id),
      ).length,
    };
  }, [activities, blockers, dependencies, humanRequests, packet, workItems]);

  const totalOwnerAttention =
    model.decisionItems.length +
    model.criticalItems.length +
    model.escalatedItems.length +
    model.watchItems.length;

  const loadStatus =
    health?.status !== "ok"
      ? "offline"
      : loading
        ? "loading"
        : error
          ? "partial"
          : "ready";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Owner Inbox"
        kicker="Global Mobility AIOS · Owner / Board"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="owner-inbox">
        <header className="owner-inbox-hero">
          <div>
            <span className="premium-label">Authority & materiality triage</span>
            <h1>Decision & escalation inbox</h1>
            <p>
              One deterministic view of records that genuinely cross an Owner or Board attention
              boundary. Priority comes from explicit authority, risk, emergency, due-date, and
              human-action state — not titles, keywords, model scoring, or chronological noise.
            </p>
          </div>
          <div className="owner-inbox-hero-actions">
            <Link className="premium-button ghost" href="/cockpit">Back to Cockpit</Link>
            <Link className="premium-button" href="/board-room">Open Board Room</Link>
          </div>
        </header>

        {error ? (
          <div className="cockpit-partial-note" role="status">
            <strong>Partial live picture.</strong>
            <span>{error}</span>
          </div>
        ) : null}

        <section className="owner-inbox-summary" aria-label="Owner attention summary">
          <article>
            <span>Owner attention</span>
            <strong>{totalOwnerAttention}</strong>
            <small>Across four authority/materiality tiers</small>
          </article>
          <article>
            <span>Decision required</span>
            <strong>{model.decisionItems.length}</strong>
            <small>Explicit pending_board records</small>
          </article>
          <article>
            <span>Critical attention</span>
            <strong>{model.criticalItems.length}</strong>
            <small>Board-risk, emergency, critical human/blocker state</small>
          </article>
          <article>
            <span>Delegated human work</span>
            <strong>{model.delegatedHumanCount}</strong>
            <small>Visible context, deliberately excluded from Owner authority</small>
          </article>
        </section>

        <div className="owner-inbox-governance-note">
          <strong>HumanActionRequest exists ≠ Owner attention.</strong>
          <span>
            Authentication role alone does not establish Board authority. Promotion requires the
            Board position, a pending Board decision, Board-owned work, or Board-accountable
            blocker context. Backend authorization remains authoritative.
          </span>
        </div>

        <div className="owner-inbox-stack">
          <AttentionLane
            tier="one"
            eyebrow="Reserved authority"
            title="Decision required"
            description="Explicit Board-reserved decisions waiting for human Owner disposition."
            items={model.decisionItems}
            emptyTitle="No Board decisions waiting."
            emptyDetail="No current decision is in pending_board state."
          />

          <AttentionLane
            tier="two"
            eyebrow="Material exception"
            title="Critical Owner attention"
            description="Critical/high Board-attention risks, emergency work, critical Owner human requests, and critical blockers attached to Board-owned/accountable work."
            items={model.criticalItems}
            emptyTitle="No critical Owner exception detected."
            emptyDetail="The loaded records contain no critical materiality signal crossing the Owner boundary."
          />

          <AttentionLane
            tier="three"
            eyebrow="Escalated authority"
            title="Human / escalation required"
            description="Owner-relevant human requests, overdue Board-owned work, and unresolved dependencies on Board-owned work."
            items={model.escalatedItems}
            emptyTitle="No Owner escalation waiting."
            emptyDetail="Delegated operational work remains outside this lane unless explicit authority or materiality promotes it."
          />

          <AttentionLane
            tier="four"
            eyebrow="Context without immediate intervention"
            title="Watch"
            description="Lower-severity Board-attention risks and elevated-risk Board-owned work that is not yet overdue or emergency."
            items={model.watchItems}
            emptyTitle="No Owner watch items."
            emptyDetail="There is no lower-urgency Board-relevant context in the loaded window."
          />
        </div>

        <footer className="owner-inbox-footer">
          <div>
            <strong>Owner Inbox routes authority; it does not execute it.</strong>
            <span>
              Board decisions and organization control stay in Board Room. Operational records stay
              in department/friction workspaces. This surface performs no blocker, dependency, work,
              Board, publication, certification, or legal-state mutation.
            </span>
          </div>
          <Link href="/board-room">Executive authority →</Link>
        </footer>
      </section>
    </WorkspaceShell>
  );
}
