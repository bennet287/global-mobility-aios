"use client";

import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  BoardPacketSnapshot,
  OrganizationPosition,
  OrganizationActivity,
  OrganizationHumanActionRequest,
  OrganizationHumanActionRequestCreateInput,
  OrganizationBlocker,
  OrganizationWorkItemDependency,
  OrganizationalWorkItem,
  ObservatoryDepartments,
  getBoardPacket,
  getOrganizationObservatoryDepartments,
  listOrganizationActivities,
  listOrganizationHumanActionRequests,
  createOrganizationHumanActionRequest,
  listOrganizationBlockers,
  listOrganizationWorkItemDependencies,
  listOrganizationWorkItems,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

type InterventionTarget = {
  kind: "blocker" | "dependency";
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

function shortDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short" }).format(date);
}

function timeLabel(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(date);
}

function daysOverdue(dueAt: string): number {
  const due = new Date(dueAt);
  if (Number.isNaN(due.getTime())) return 0;
  const now = new Date();
  return Math.max(0, Math.floor((now.getTime() - due.getTime()) / (1000 * 60 * 60 * 24)));
}

function isOverdue(dueAt?: string | null): boolean {
  if (!dueAt) return false;
  return dueAt < new Date().toISOString();
}

export default function CrossDepartmentFrictionPage() {
  const { health } = useBackendStatus();

  const [packet, setPacket] = useState<BoardPacketSnapshot | null>(null);
  const [departmentObservatory, setDepartmentObservatory] = useState<ObservatoryDepartments | null>(null);
  const [workItems, setWorkItems] = useState<OrganizationalWorkItem[]>([]);
  const [blockers, setBlockers] = useState<OrganizationBlocker[]>([]);
  const [dependencies, setDependencies] = useState<OrganizationWorkItemDependency[]>([]);
  const [humanRequests, setHumanRequests] = useState<OrganizationHumanActionRequest[]>([]);
  const [activities, setActivities] = useState<OrganizationActivity[]>([]);
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
      listOrganizationWorkItems({ page_size: 100 }),
      listOrganizationBlockers({ status: "open", page_size: 100 }),
      listOrganizationWorkItemDependencies({ status: "active", page_size: 100 }),
      listOrganizationHumanActionRequests({ page_size: 100 }),
      listOrganizationActivities({ page_size: 200 }),
    ]);

    const failures: string[] = [];
    const [packetResult, departmentsResult, workResult, blockersResult, dependenciesResult, requestsResult, activityResult] = results;

    if (packetResult.status === "fulfilled") setPacket(packetResult.value);
    else failures.push("organization control");

    if (departmentsResult.status === "fulfilled") setDepartmentObservatory(departmentsResult.value);
    else failures.push("department observatory");

    if (workResult.status === "fulfilled") setWorkItems(workResult.value.data);
    else failures.push("work items");

    if (blockersResult.status === "fulfilled") setBlockers(blockersResult.value.data);
    else failures.push("blockers");

    if (dependenciesResult.status === "fulfilled") setDependencies(dependenciesResult.value.data);
    else failures.push("dependencies");

    if (requestsResult.status === "fulfilled") setHumanRequests(requestsResult.value.data);
    else failures.push("human requests");

    if (activityResult.status === "fulfilled") setActivities(activityResult.value.data);
    else failures.push("activity stream");

    if (failures.length) setError(`Some friction signals are temporarily unavailable: ${failures.join(", ")}.`);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const allPositions = useMemo(() => packet?.positions || [], [packet]);
  const workItemById = useMemo(() => new Map(workItems.map((item) => [item.id, item])), [workItems]);
  const positionByKey = useMemo(() => new Map(allPositions.map((position) => [position.position_key, position])), [allPositions]);
  const validDepartments = useMemo(() => new Set(departmentObservatory?.departments.map((row) => row.department) || []), [departmentObservatory]);

  const crossDepartmentBlockers = useMemo(() => {
    return blockers.filter((blocker) => {
      if (!blocker.work_item_id) return false;
      const work = workItemById.get(blocker.work_item_id);
      if (!work) return false;
      return work.department !== blocker.department;
    }).sort((a, b) => (b.severity === "critical" ? 1 : 0) - (a.severity === "critical" ? 1 : 0) || (isOverdue(a.due_at) ? -1 : 0));
  }, [blockers, workItemById]);

  const crossDepartmentDependencies = useMemo(() => {
    return dependencies.filter((dep) => {
      const downstream = workItemById.get(dep.work_item_id);
      const upstream = workItemById.get(dep.depends_on_work_item_id);
      if (!downstream || !upstream) return false;
      return downstream.department !== upstream.department;
    });
  }, [dependencies, workItemById]);

  const humanRequestFor = useCallback((sourceType: string, sourceId: string) => {
    return humanRequests.find((request) => {
      if (!ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status)) return false;
      if (sourceType === "organization_blocker") return request.blocker_id === sourceId;
      if (sourceType === "organization_work_item_dependency") return request.work_item_id === sourceId;
      return false;
    });
  }, [humanRequests]);

  const latestActivityFor = useCallback((departments: string[], sourceType?: string, sourceId?: string) => {
    const departmentSet = new Set(departments);
    return activities.find((activity) => {
      if (activity.department && departmentSet.has(activity.department)) return true;
      if (sourceType && sourceId && activity.source_object_type === sourceType && activity.source_object_id === sourceId) return true;
      return false;
    });
  }, [activities]);

  const escalatedCount = useMemo(() => {
    let count = 0;
    for (const blocker of crossDepartmentBlockers) {
      if (blocker.severity === "critical" || isOverdue(blocker.due_at) || humanRequestFor("organization_blocker", blocker.id)) count += 1;
    }
    for (const dep of crossDepartmentDependencies) {
      const downstream = workItemById.get(dep.work_item_id);
      if (humanRequestFor("organization_work_item_dependency", dep.id) || (downstream && isOverdue(downstream.due_at))) count += 1;
    }
    return count;
  }, [crossDepartmentBlockers, crossDepartmentDependencies, workItemById, humanRequestFor]);

  const humanAttentionCount = useMemo(() => {
    let count = 0;
    for (const blocker of crossDepartmentBlockers) {
      if (humanRequestFor("organization_blocker", blocker.id) || blocker.requires_human_action) count += 1;
    }
    for (const dep of crossDepartmentDependencies) {
      if (humanRequestFor("organization_work_item_dependency", dep.id)) count += 1;
    }
    return count;
  }, [crossDepartmentBlockers, crossDepartmentDependencies, humanRequestFor]);

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
        request_key: `cross-department-intervention:${interventionTarget.sourceObjectType}:${interventionTarget.id}:${interventionTarget.sourceObjectVersion}`,
        request_type: interventionType,
        title: `Cross-department follow-up: ${interventionTarget.label}`.slice(0, 500),
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

  const loadStatus = health?.status !== "ok"
    ? "offline"
    : loading
      ? "loading"
      : error
        ? "partial"
        : "ready";

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Cross-department friction" kicker="Global Mobility AIOS · Owner / Board" loadStatus={loadStatus} onRefresh={() => void load()} />

      <section className="cross-department-friction">
        <header className="cross-department-friction-header">
          <div>
            <span className="premium-label">Organizational friction</span>
            <h1>Cross-department blockers & dependencies</h1>
            <p>
              Blockers and dependencies whose owning department differs from the department of the work they affect.
              Backend authorization remains authoritative.
            </p>
          </div>
          <Link className="premium-button ghost" href="/cockpit">Back to Cockpit</Link>
        </header>

        {error ? <div className="cockpit-partial-note" role="status"><strong>Partial live picture.</strong><span>{error}</span></div> : null}

        <div className="friction-summary">
          <article>
            <span>Cross-department blockers</span>
            <strong>{crossDepartmentBlockers.length}</strong>
          </article>
          <article>
            <span>Cross-department dependencies</span>
            <strong>{crossDepartmentDependencies.length}</strong>
          </article>
          <article>
            <span>Require human action</span>
            <strong>{humanAttentionCount}</strong>
          </article>
          <article>
            <span>Escalated / overdue</span>
            <strong>{escalatedCount}</strong>
          </article>
        </div>

        <div className="friction-grid">
          <section className="friction-lane friction-blockers" aria-labelledby="cross-blockers-title">
            <header>
              <span className="premium-label">Governance</span>
              <h2 id="cross-blockers-title">Cross-department blockers · {crossDepartmentBlockers.length}</h2>
            </header>
            {crossDepartmentBlockers.length ? (
              <ul className="friction-list">
                {crossDepartmentBlockers.slice(0, 8).map((blocker) => {
                  const work = blocker.work_item_id ? workItemById.get(blocker.work_item_id) : undefined;
                  const owner = blocker.accountable_position_key ? positionByKey.get(blocker.accountable_position_key) : undefined;
                  const request = humanRequestFor("organization_blocker", blocker.id);
                  const latest = latestActivityFor([blocker.department, work?.department].filter((d): d is string => Boolean(d)));
                  return (
                    <li key={blocker.id} className={isOverdue(blocker.due_at) ? "overdue" : ""}>
                      <div className="friction-row-primary">
                        <span className={`blocker-severity-${blocker.severity}`}>{titleCase(blocker.severity)}</span>
                        <strong>{blocker.title}</strong>
                      </div>
                      <div className="friction-row-meta">
                        <span>Affects: <strong>{work?.department || "Unknown"}</strong></span>
                        <span>Owned by: <strong>{blocker.department || "Unknown"}</strong></span>
                        {owner ? <span>Accountable: <strong>{owner.title}</strong></span> : null}
                        {blocker.due_at ? <span>Due {shortDate(blocker.due_at)}{isOverdue(blocker.due_at) ? ` · ${daysOverdue(blocker.due_at)}d overdue` : ""}</span> : null}
                        {request ? <span className="friction-human-attention">Human request · {titleCase(request.priority)} · {titleCase(request.status)}</span> : null}
                        {latest ? <span className="friction-activity">Changed {shortDate(latest.occurred_at)} · {latest.title}</span> : null}
                      </div>
                      <div className="friction-row-actions">
                        {work?.department && validDepartments.has(work.department) ? (
                          <Link className="premium-button ghost small" href={`/workspace/${encodeURIComponent(work.department)}`}>
                            Open {work.department}
                          </Link>
                        ) : null}
                        {blocker.department && validDepartments.has(blocker.department) ? (
                          <Link className="premium-button ghost small" href={`/workspace/${encodeURIComponent(blocker.department)}`}>
                            Open {blocker.department}
                          </Link>
                        ) : null}
                        <button
                          type="button"
                          className="governed-intervention-trigger"
                          onClick={() => beginIntervention({
                            kind: "blocker", id: blocker.id, label: blocker.title, department: blocker.department,
                            workItemId: blocker.work_item_id, blockerId: blocker.id, sourceObjectType: "organization_blocker", sourceObjectVersion: blocker.updated_at,
                          })}
                        >
                          Request follow-up
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : <div className="cockpit-empty-line">No cross-department blockers are currently visible.</div>}
          </section>

          <section className="friction-lane friction-dependencies" aria-labelledby="cross-dependencies-title">
            <header>
              <span className="premium-label">Dependencies</span>
              <h2 id="cross-dependencies-title">Cross-department dependencies · {crossDepartmentDependencies.length}</h2>
            </header>
            {crossDepartmentDependencies.length ? (
              <ul className="friction-list">
                {crossDepartmentDependencies.slice(0, 8).map((dep) => {
                  const downstream = workItemById.get(dep.work_item_id);
                  const upstream = workItemById.get(dep.depends_on_work_item_id);
                  const blocked = downstream && downstream.status !== "completed" && downstream.status !== "cancelled";
                  const request = humanRequestFor("organization_work_item_dependency", dep.id);
                  const latest = latestActivityFor([downstream?.department, upstream?.department].filter((d): d is string => Boolean(d)));
                  return (
                    <li key={dep.id} className={blocked ? "dependency-blocked" : ""}>
                      <div className="friction-row-primary">
                        <strong>{downstream?.title || dep.work_item_id.slice(0, 8)}</strong>
                        <span className="dependency-edge">depends on</span>
                        <strong>{upstream?.title || dep.depends_on_work_item_id.slice(0, 8)}</strong>
                      </div>
                      <div className="friction-row-meta">
                        <span>Downstream: <strong>{downstream?.department || "Unknown"}</strong></span>
                        <span>Upstream: <strong>{upstream?.department || "Unknown"}</strong></span>
                        <span>Type: {titleCase(dep.dependency_type)}</span>
                        {blocked ? <span className="friction-blocked-tag">Downstream blocked</span> : null}
                        {request ? <span className="friction-human-attention">Human request · {titleCase(request.priority)} · {titleCase(request.status)}</span> : null}
                        {latest ? <span className="friction-activity">Changed {shortDate(latest.occurred_at)} · {latest.title}</span> : null}
                      </div>
                      <div className="friction-row-actions">
                        {downstream?.department && validDepartments.has(downstream.department) ? (
                          <Link className="premium-button ghost small" href={`/workspace/${encodeURIComponent(downstream.department)}`}>
                            Open {downstream.department}
                          </Link>
                        ) : null}
                        {upstream?.department && validDepartments.has(upstream.department) ? (
                          <Link className="premium-button ghost small" href={`/workspace/${encodeURIComponent(upstream.department)}`}>
                            Open {upstream.department}
                          </Link>
                        ) : null}
                        <button
                          type="button"
                          className="governed-intervention-trigger"
                          onClick={() => beginIntervention({
                            kind: "dependency", id: dep.id, label: `Dependency ${dep.dependency_key}`, department: downstream?.department || null,
                            workItemId: dep.work_item_id, blockerId: null, sourceObjectType: "organization_work_item_dependency", sourceObjectVersion: dep.updated_at,
                          })}
                        >
                          Request follow-up
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : <div className="cockpit-empty-line">No cross-department dependencies are currently visible.</div>}
          </section>
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
                placeholder="Describe the cross-department follow-up required. This creates a governed request; it does not resolve, waive, approve, or reassign the underlying record."
              />
            </label>
            <div className="intervention-actions">
              <p>Backend authorization remains authoritative. The friction view does not directly change blocker or dependency status, complete work, or publish legal/regulatory outcomes.</p>
              <button type="submit" disabled={interventionSubmitting || !interventionInstructions.trim()}>
                {interventionSubmitting ? "Creating governed request…" : "Create human request"}
              </button>
            </div>
            {interventionMessage ? <div className="intervention-message" role="status">{interventionMessage}</div> : null}
          </form>
        ) : null}

        <footer className="operational-intelligence-footer">
          <span>Cross-department friction is a governed composition surface. Server authorization is authoritative.</span>
        </footer>
      </section>
    </WorkspaceShell>
  );
}

