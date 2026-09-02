"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import {
  BoardPacketSnapshot,
  OrganizationPosition,
  OrganizationActivity,
  OrganizationHumanActionRequest,
  OrganizationHumanActionRequestCreateInput,
  OrganizationBlocker,
  OrganizationWorkItemDependency,
  OrganizationalWorkItem,
  OrganizationContribution,
  ObservatoryDepartments,
  getBoardPacket,
  getOrganizationObservatoryDepartments,
  listOrganizationActivities,
  listOrganizationHumanActionRequests,
  createOrganizationHumanActionRequest,
  listOrganizationBlockers,
  listOrganizationWorkItemDependencies,
  listOrganizationWorkItems,
  listOrganizationContributions,
} from "../../../lib/api";
import { titleCase } from "../../../lib/utils";

type InterventionTarget = {
  kind: "blocker" | "work" | "dependency";
  id: string;
  label: string;
  department: string | null;
  workItemId: string | null;
  blockerId: string | null;
  sourceObjectType: string;
  sourceObjectVersion: string;
};

const ACTIVE_HUMAN_REQUEST_STATUSES = new Set(["required", "acknowledged", "in_progress"]);

function executiveRoleLabel(position: OrganizationPosition): string {
  const labels: Record<string, string> = {
    coo: "COO", cto: "CTO", ciso: "CISO", cpo: "CPO", cfo: "CFO", clo: "CLO", cmo: "CMO", cco: "CCO", chro: "CHRO",
  };
  return labels[position.position_key] || position.position_key.replaceAll("_", " ").toUpperCase();
}

function timeLabel(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(date);
}

function shortDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short" }).format(date);
}

function dateLabel(value?: string | null): string {
  if (!value) return "Not established";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not established";
  return new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function daysOverdue(dueAt: string): number {
  const due = new Date(dueAt);
  if (Number.isNaN(due.getTime())) return 0;
  const now = new Date();
  return Math.max(0, Math.floor((now.getTime() - due.getTime()) / (1000 * 60 * 60 * 24)));
}

export default function DepartmentWorkspacePage() {
  const params = useParams<{ department: string }>();
  const department = decodeURIComponent(params.department);
  const { health } = useBackendStatus();

  const [packet, setPacket] = useState<BoardPacketSnapshot | null>(null);
  const [departmentObservatory, setDepartmentObservatory] = useState<ObservatoryDepartments | null>(null);
  const [workItems, setWorkItems] = useState<OrganizationalWorkItem[]>([]);
  const [blockers, setBlockers] = useState<OrganizationBlocker[]>([]);
  const [dependencies, setDependencies] = useState<OrganizationWorkItemDependency[]>([]);
  const [humanRequests, setHumanRequests] = useState<OrganizationHumanActionRequest[]>([]);
  const [activities, setActivities] = useState<OrganizationActivity[]>([]);
  const [contributions, setContributions] = useState<OrganizationContribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [interventionTarget, setInterventionTarget] = useState<InterventionTarget | null>(null);
  const [interventionType, setInterventionType] = useState<OrganizationHumanActionRequestCreateInput["request_type"]>("review");
  const [interventionRole, setInterventionRole] = useState<"operator" | "reviewer">("operator");
  const [interventionPriority, setInterventionPriority] = useState<"low" | "normal" | "high" | "critical">("normal");
  const [interventionInstructions, setInterventionInstructions] = useState("");
  const [interventionSubmitting, setInterventionSubmitting] = useState(false);
  const [interventionMessage, setInterventionMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      getBoardPacket(),
      getOrganizationObservatoryDepartments(),
      listOrganizationWorkItems({ department, page_size: 100 }),
      listOrganizationBlockers({ status: "open", page_size: 100 }),
      listOrganizationWorkItemDependencies({ status: "active", page_size: 100 }),
      listOrganizationHumanActionRequests({ page_size: 100 }),
      listOrganizationActivities({ page_size: 50 }),
      listOrganizationContributions({ department, page_size: 100 }),
    ]);

    const failures: string[] = [];
    const [packetResult, departmentsResult, workResult, blockersResult, dependenciesResult, requestsResult, activityResult, contributionResult] = results;

    if (packetResult.status === "fulfilled") setPacket(packetResult.value);
    else failures.push("organization control");

    if (departmentsResult.status === "fulfilled") setDepartmentObservatory(departmentsResult.value);
    else failures.push("department observatory");

    if (workResult.status === "fulfilled") setWorkItems(workResult.value.data);
    else failures.push("owned work");

    if (blockersResult.status === "fulfilled") setBlockers(blockersResult.value.data);
    else failures.push("blockers");

    if (dependenciesResult.status === "fulfilled") setDependencies(dependenciesResult.value.data);
    else failures.push("dependencies");

    if (requestsResult.status === "fulfilled") setHumanRequests(requestsResult.value.data);
    else failures.push("human requests");

    if (activityResult.status === "fulfilled") setActivities(activityResult.value.data);
    else failures.push("activity stream");

    if (contributionResult.status === "fulfilled") setContributions(contributionResult.value.data);
    else failures.push("contributions");

    if (failures.length) setError(`Some workspace signals are temporarily unavailable: ${failures.join(", ")}.`);
    setLoading(false);
  }, [department]);

  useEffect(() => { void load(); }, [load]);

  const allPositions = useMemo(() => packet?.positions || [], [packet]);
  const executivePositions = useMemo(() => {
    return allPositions.filter((position) => position.reports_to_position_key === "ceo" && position.authority_level === "L3");
  }, [allPositions]);

  const validDepartment = useMemo(() => {
    return departmentObservatory?.departments.some((row) => row.department === department) ?? false;
  }, [department, departmentObservatory]);

  const departmentSnapshot = useMemo(() => {
    return departmentObservatory?.departments.find((row) => row.department === department);
  }, [department, departmentObservatory]);

  const workItemById = useMemo(() => new Map(workItems.map((item) => [item.id, item])), [workItems]);

  const departmentPositions = useMemo(() => {
    return allPositions
      .filter((position) => position.department === department)
      .sort((a, b) => a.authority_level.localeCompare(b.authority_level) || a.title.localeCompare(b.title));
  }, [allPositions, department]);

  const ownerPositions = useMemo(() => {
    const departmentRow = departmentObservatory?.departments.find((row) => row.department === department);
    if (!departmentRow) return [];
    // Derive owner from executive positions whose downstream positions include the department.
    const ownerKeys = new Set<string>();
    for (const exec of executivePositions) {
      const descendants = new Set<string>();
      const queue = [exec.position_key];
      while (queue.length) {
        const current = queue.shift()!;
        descendants.add(current);
        for (const position of allPositions) {
          if (position.reports_to_position_key === current && !descendants.has(position.position_key)) {
            queue.push(position.position_key);
          }
        }
      }
      if (departmentPositions.some((position) => descendants.has(position.position_key))) {
        ownerKeys.add(exec.position_key);
      }
    }
    return executivePositions.filter((position) => ownerKeys.has(position.position_key));
  }, [allPositions, department, departmentObservatory, departmentPositions, executivePositions]);

  const scopedBlockers = useMemo(() => {
    return blockers.filter((blocker) => {
      if (blocker.department === department) return true;
      if (blocker.work_item_id && workItemById.get(blocker.work_item_id)?.department === department) return true;
      return false;
    });
  }, [blockers, department, workItemById]);

  const scopedDependencies = useMemo(() => {
    return dependencies.filter((dep) => {
      const downstream = workItemById.get(dep.work_item_id);
      const upstream = workItemById.get(dep.depends_on_work_item_id);
      return downstream?.department === department || upstream?.department === department;
    });
  }, [dependencies, department, workItemById]);

  const scopedRequests = useMemo(() => {
    return humanRequests.filter((request) => {
      if (!ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status)) return false;
      if (request.work_item_id && workItemById.get(request.work_item_id)?.department === department) return true;
      return false;
    });
  }, [humanRequests, department, workItemById]);

  const scopedActivities = useMemo(() => {
    const positionKeys = new Set(departmentPositions.map((position) => position.position_key));
    return activities.filter((activity) => {
      if (activity.department === department) return true;
      if (activity.position_key && positionKeys.has(activity.position_key)) return true;
      return false;
    });
  }, [activities, department, departmentPositions]);

  const overdueWork = useMemo(() => {
    const now = new Date().toISOString();
    return workItems.filter((item) => item.due_at && item.due_at < now);
  }, [workItems]);

  const beginIntervention = (target: InterventionTarget) => {
    setInterventionTarget(target);
    setInterventionInstructions("");
    setInterventionRole("operator");
    setInterventionPriority("normal");
    setInterventionType("review");
    setInterventionMessage(null);
  };

  const submitIntervention = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!interventionTarget || !interventionInstructions.trim()) return;
    setInterventionSubmitting(true);
    setInterventionMessage(null);
    try {
      const created = await createOrganizationHumanActionRequest({
        request_key: `workspace-intervention:${interventionTarget.sourceObjectType}:${interventionTarget.id}:${interventionTarget.sourceObjectVersion}`,
        request_type: interventionType,
        title: `Department follow-up: ${interventionTarget.label}`.slice(0, 500),
        instructions: interventionInstructions.trim(),
        required_role: interventionRole,
        priority: interventionPriority,
        work_item_id: interventionTarget.workItemId,
        blocker_id: interventionTarget.blockerId,
        source_object_type: interventionTarget.sourceObjectType,
        source_object_id: interventionTarget.id,
        source_object_version: interventionTarget.sourceObjectVersion,
      });
      setInterventionMessage(`Governed human request created · ${titleCase(created.status)} · ${created.required_role}`);
      setInterventionInstructions("");
      await load();
    } catch (requestError) {
      setInterventionMessage(requestError instanceof Error ? requestError.message : "The governed intervention request was rejected.");
    } finally {
      setInterventionSubmitting(false);
    }
  };

  const timestamps = [
    packet?.generated_at,
    departmentObservatory?.as_of,
  ].filter(Boolean) as string[];
  const dataFreshnessAt = timestamps.length ? timestamps.sort()[timestamps.length - 1] : null;

  const loadStatus = health?.status !== "ok"
    ? "offline"
    : loading
      ? "loading"
      : error
        ? "partial"
        : "ready";

  if (!validDepartment && !loading && departmentObservatory) {
    return (
      <WorkspaceShell health={health}>
        <Topbar title="Department workspace" kicker="Global Mobility AIOS · Owner / Board" loadStatus={loadStatus} onRefresh={() => void load()} />
        <section className="department-workspace">
          <header className="department-workspace-header">
            <h1>{department}</h1>
            <p>This department is not recognized by the Organization Observatory. Deep links to departments remain presentation-only; server authorization is unchanged.</p>
            <Link className="premium-button primary" href="/cockpit">Return to Cockpit</Link>
          </header>
        </section>
      </WorkspaceShell>
    );
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Department workspace" kicker={`Global Mobility AIOS · ${department}`} loadStatus={loadStatus} onRefresh={() => void load()} />

      <section className="department-workspace">
        <header className="department-workspace-header">
          <div>
            <span className="premium-label">Bounded operational unit</span>
            <h1>{department}</h1>
            <p>
              Executive owner:
              <strong>{ownerPositions.length ? ownerPositions.map((position) => executiveRoleLabel(position)).join(" / ") : "Unresolved"}</strong>
              · Active positions: <strong>{departmentPositions.length}</strong>
              {dataFreshnessAt ? ` · Updated ${shortDate(dataFreshnessAt)} · ${timeLabel(dataFreshnessAt)}` : null}
            </p>
          </div>
          <Link className="premium-button ghost" href="/cockpit">Back to Cockpit</Link>
        </header>

        {error ? <div className="cockpit-partial-note" role="status"><strong>Partial live picture.</strong><span>{error}</span></div> : null}

        <div className="department-workspace-grid">
          <article className="department-workspace-card operating-state" aria-labelledby="operating-state-title">
            <header>
              <span className="premium-label">Operating state</span>
              <h2 id="operating-state-title">Department snapshot</h2>
            </header>
            <dl className="department-metrics">
              <div><dt>Active work</dt><dd>{departmentSnapshot?.work_items_active ?? "—"}</dd></div>
              <div><dt>Open blockers</dt><dd>{departmentSnapshot?.blockers_open ?? "—"}</dd></div>
              <div><dt>Active contributions</dt><dd>{departmentSnapshot?.active_contributions ?? "—"}</dd></div>
              <div><dt>Pending human requests</dt><dd>{departmentSnapshot?.pending_human_action_requests_linked_to_work ?? "—"}</dd></div>
            </dl>
          </article>

          <article className="department-workspace-card owned-work" aria-labelledby="owned-work-title">
            <header>
              <span className="premium-label">Owned work</span>
              <h2 id="owned-work-title">Active work · {workItems.length}</h2>
            </header>
            {workItems.length ? (
              <ul className="cockpit-lane-list">
                {workItems.slice(0, 6).map((item) => (
                  <li key={item.id} className={item.due_at && item.due_at < new Date().toISOString() ? "overdue" : ""}>
                    <strong>{item.title}</strong>
                    <small>
                      {titleCase(item.status)} · {titleCase(item.priority)}
                      {item.assigned_position_key ? ` · ${item.assigned_position_key.replaceAll("_", " ").toUpperCase()}` : null}
                      {item.due_at ? ` · Due ${shortDate(item.due_at)}${daysOverdue(item.due_at) > 0 ? ` · ${daysOverdue(item.due_at)} day${daysOverdue(item.due_at) === 1 ? "" : "s"} overdue` : ""}` : null}
                    </small>
                    <button
                      type="button"
                      className="governed-intervention-trigger"
                      onClick={() => beginIntervention({
                        kind: "work", id: item.id, label: item.title, department: item.department,
                        workItemId: item.id, blockerId: null, sourceObjectType: "organizational_work_item", sourceObjectVersion: "v1",
                      })}
                    >
                      Request follow-up
                    </button>
                  </li>
                ))}
              </ul>
            ) : <div className="cockpit-empty-line">No active work in this department.</div>}
          </article>

          <article className="department-workspace-card open-blockers" aria-labelledby="open-blockers-title">
            <header>
              <span className="premium-label">Governance</span>
              <h2 id="open-blockers-title">Open blockers · {scopedBlockers.length}</h2>
            </header>
            {scopedBlockers.length ? (
              <ul className="cockpit-lane-list">
                {scopedBlockers.slice(0, 5).map((blocker) => (
                  <li key={blocker.id}>
                    <span className={`blocker-severity-${blocker.severity}`}>{titleCase(blocker.severity)}</span>
                    <strong>{blocker.title}</strong>
                    <small>
                      {blocker.accountable_position_key ? `${blocker.accountable_position_key.replaceAll("_", " ").toUpperCase()} · ` : null}
                      {blocker.due_at ? `Due ${shortDate(blocker.due_at)}` : "No due date"}
                    </small>
                    <button
                      type="button"
                      className="governed-intervention-trigger"
                      onClick={() => beginIntervention({
                        kind: "blocker", id: blocker.id, label: blocker.title, department: blocker.department,
                        workItemId: blocker.work_item_id, blockerId: blocker.id, sourceObjectType: "organization_blocker", sourceObjectVersion: "v1",
                      })}
                    >
                      Request follow-up
                    </button>
                  </li>
                ))}
              </ul>
            ) : <div className="cockpit-empty-line">No open blockers in this department.</div>}
          </article>

          <article className="department-workspace-card active-dependencies" aria-labelledby="active-dependencies-title">
            <header>
              <span className="premium-label">Dependencies</span>
              <h2 id="active-dependencies-title">Active dependencies · {scopedDependencies.length}</h2>
            </header>
            {scopedDependencies.length ? (
              <ul className="cockpit-lane-list">
                {scopedDependencies.slice(0, 5).map((dep) => {
                  const upstream = workItemById.get(dep.depends_on_work_item_id);
                  const downstream = workItemById.get(dep.work_item_id);
                  const blocked = downstream && downstream.status !== "completed" && downstream.status !== "cancelled";
                  return (
                    <li key={dep.id} className={blocked ? "dependency-blocked" : ""}>
                      <strong>{downstream?.title || dep.work_item_id.slice(0, 8)}</strong>
                      <span className="dependency-edge">depends on</span>
                      <strong>{upstream?.title || dep.depends_on_work_item_id.slice(0, 8)}</strong>
                      <small>{titleCase(dep.dependency_type)}{blocked ? " · blocked downstream" : null}</small>
                      <button
                        type="button"
                        className="governed-intervention-trigger"
                        onClick={() => beginIntervention({
                          kind: "dependency", id: dep.id, label: `Dependency ${dep.dependency_key}`, department,
                          workItemId: dep.work_item_id, blockerId: null, sourceObjectType: "organization_work_item_dependency", sourceObjectVersion: "v1",
                        })}
                      >
                        Request follow-up
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : <div className="cockpit-empty-line">No active dependencies in this department.</div>}
          </article>

          <article className="department-workspace-card contributions" aria-labelledby="contributions-title">
            <header>
              <span className="premium-label">Evidence</span>
              <h2 id="contributions-title">Contributions · {contributions.length}</h2>
            </header>
            {contributions.length ? (
              <ul className="cockpit-lane-list">
                {contributions.slice(0, 5).map((contribution) => (
                  <li key={contribution.id}>
                    <strong>{contribution.title}</strong>
                    <small>
                      {titleCase(contribution.record_kind)} · {titleCase(contribution.contribution_type)}
                      {contribution.effective_at ? ` · ${dateLabel(contribution.effective_at)}` : null}
                    </small>
                  </li>
                ))}
              </ul>
            ) : <div className="cockpit-empty-line">No contributions in this department.</div>}
          </article>

          <article className="department-workspace-card material-activity" aria-labelledby="material-activity-title">
            <header>
              <span className="premium-label">Durable signal</span>
              <h2 id="material-activity-title">Material Activity · {scopedActivities.length}</h2>
            </header>
            {scopedActivities.length ? (
              <ul className="cockpit-lane-list activity-list">
                {scopedActivities.slice(0, 5).map((activity) => (
                  <li key={activity.id}>
                    <time dateTime={activity.occurred_at}>{shortDate(activity.occurred_at)} · {timeLabel(activity.occurred_at)}</time>
                    <strong>{activity.title}</strong>
                    <small>{activity.department || titleCase(activity.activity_class)} · {titleCase(activity.actor_type)} · {activity.actor_id}</small>
                  </li>
                ))}
              </ul>
            ) : <div className="cockpit-empty-line">No material Activity in this department.</div>}
          </article>

          <article className="department-workspace-card pending-requests" aria-labelledby="pending-requests-title">
            <header>
              <span className="premium-label">Human attention</span>
              <h2 id="pending-requests-title">Pending human requests · {scopedRequests.length}</h2>
            </header>
            {scopedRequests.length ? (
              <ul className="cockpit-lane-list">
                {scopedRequests.slice(0, 5).map((request) => (
                  <li key={request.id}>
                    <strong>{request.title}</strong>
                    <small>
                      {titleCase(request.priority)} · {request.required_role.replaceAll("_", " ")}
                      {request.due_at ? ` · Due ${shortDate(request.due_at)}` : null}
                    </small>
                  </li>
                ))}
              </ul>
            ) : <div className="cockpit-empty-line">No pending human requests in this department.</div>}
          </article>
        </div>

        {interventionTarget ? (
          <form id="governed-intervention-form" className="governed-intervention-form" onSubmit={submitIntervention}>
            <header>
              <div>
                <span className="premium-label">Governed intervention</span>
                <strong>Request human follow-up</strong>
                <small>{titleCase(interventionTarget.kind)} · {interventionTarget.label}{interventionTarget.department ? ` · ${interventionTarget.department}` : ""}</small>
              </div>
              <button type="button" className="intervention-dismiss" onClick={() => { setInterventionTarget(null); setInterventionMessage(null); }}>Dismiss</button>
            </header>
            <div className="governed-intervention-fields">
              <label>
                <span>Request type</span>
                <select value={interventionType} onChange={(event) => setInterventionType(event.target.value as typeof interventionType)}>
                  <option value="review">Review</option>
                  <option value="provide_information">Provide information</option>
                  <option value="acknowledgement">Acknowledgement</option>
                </select>
              </label>
              <label>
                <span>Required role</span>
                <select value={interventionRole} onChange={(event) => setInterventionRole(event.target.value as typeof interventionRole)}>
                  <option value="operator">Operator</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </label>
              <label>
                <span>Priority</span>
                <select value={interventionPriority} onChange={(event) => setInterventionPriority(event.target.value as typeof interventionPriority)}>
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </label>
            </div>
            <label className="intervention-instructions">
              <span>Instructions</span>
              <textarea
                value={interventionInstructions}
                onChange={(event) => setInterventionInstructions(event.target.value)}
                maxLength={4000}
                required
                placeholder="Describe the human follow-up required. This creates a governed request; it does not resolve, waive, approve, or reassign the underlying record."
              />
            </label>
            <div className="intervention-actions">
              <p>Backend authorization remains authoritative. The workspace does not directly change blocker or dependency status, complete work, or publish legal/regulatory outcomes.</p>
              <button type="submit" disabled={interventionSubmitting || !interventionInstructions.trim()}>
                {interventionSubmitting ? "Creating governed request…" : "Create human request"}
              </button>
            </div>
            {interventionMessage ? <div className="intervention-message" role="status">{interventionMessage}</div> : null}
          </form>
        ) : null}

        <footer className="operational-intelligence-footer">
          <span>Department workspace remains a governed composition surface. Server authorization is authoritative.</span>
        </footer>
      </section>
    </WorkspaceShell>
  );
}
