"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import {
  type ExecutiveDecision,
  type OrganizationActivity,
  type OrganizationRecordPage,
  type OrganizationRecordReference,
  type OrganizationalWorkItem,
  getOrganizationDecisionRecord,
  getOrganizationWorkItem,
  listOrganizationActivities,
  listOrganizationDecisionRecords,
  listOrganizationRecordReferences,
} from "../../../lib/api";
import { titleCase } from "../../../lib/utils";

const PAGE_SIZE = 50;

type DecisionDetailContext = {
  decision: ExecutiveDecision;
  workItem: OrganizationalWorkItem | null;
  references: OrganizationRecordReference[];
  activities: OrganizationActivity[];
  relatedReadsPartial: boolean;
};

type DecisionExplorerState =
  | { kind: "list" }
  | { kind: "detail"; context: DecisionDetailContext };

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function shortId(value: string | null): string {
  return value ? value.slice(0, 8) : "—";
}

function decisionState(decision: ExecutiveDecision): string {
  if (!decision.is_current) return "SUPERSEDED";
  if (decision.status === "approved") return "APPROVED";
  if (decision.status === "rejected") return "REJECTED";
  if (decision.status === "pending_board") return "PENDING BOARD";
  if (decision.status === "pending_ceo") return "PENDING CEO";
  return titleCase(decision.status);
}

function authorityLabel(decision: ExecutiveDecision): string {
  if (decision.authority_level === "L4" || decision.decision_owner_position === "board") return "BOARD";
  if (decision.decision_owner_position === "ceo") return "CEO";
  return decision.decision_owner_position.replaceAll("_", " ").toUpperCase();
}

function mergeReferences(
  decisionReferences: OrganizationRecordReference[],
  workReferences: OrganizationRecordReference[],
): OrganizationRecordReference[] {
  const merged = new Map<string, OrganizationRecordReference>();
  for (const reference of [...decisionReferences, ...workReferences]) {
    merged.set(reference.id, reference);
  }
  return [...merged.values()].sort((left, right) => (
    new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
  ));
}

function referenceScope(reference: OrganizationRecordReference, decision: ExecutiveDecision): string {
  if (reference.decision_id === decision.id) return "Decision";
  if (reference.work_item_id === decision.work_item_id) return "Work item";
  return "Related record";
}

export default function DecisionExplorerPage() {
  const { health, error: healthError } = useBackendStatus();
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState<OrganizationRecordPage<ExecutiveDecision> | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<DecisionExplorerState>({ kind: "list" });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOrganizationDecisionRecords({ page, page_size: PAGE_SIZE });
      setRecords(data);
    } catch (loadError) {
      setRecords(null);
      setError(loadError instanceof Error ? loadError.message : "Could not load decisions.");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectDecision = useCallback(async (id: string) => {
    setDetailLoading(true);
    setError(null);
    try {
      const decision = await getOrganizationDecisionRecord(id);

      const workPromise = decision.work_item_id
        ? getOrganizationWorkItem(decision.work_item_id).catch(() => null)
        : Promise.resolve(null);
      const decisionReferencesPromise = listOrganizationRecordReferences({
        decision_id: decision.id,
        page_size: 100,
      }).catch(() => null);
      const workReferencesPromise = decision.work_item_id
        ? listOrganizationRecordReferences({
            work_item_id: decision.work_item_id,
            page_size: 100,
          }).catch(() => null)
        : Promise.resolve(null);
      const activityPromise = decision.work_item_id
        ? listOrganizationActivities({
            work_item_id: decision.work_item_id,
            page_size: 50,
          }).catch(() => null)
        : Promise.resolve(null);

      const [workItem, decisionReferences, workReferences, activityPage] = await Promise.all([
        workPromise,
        decisionReferencesPromise,
        workReferencesPromise,
        activityPromise,
      ]);

      setState({
        kind: "detail",
        context: {
          decision,
          workItem,
          references: mergeReferences(
            decisionReferences?.data ?? [],
            workReferences?.data ?? [],
          ),
          activities: activityPage?.data ?? [],
          relatedReadsPartial:
            Boolean(decision.work_item_id && !workItem)
            || decisionReferences === null
            || Boolean(decision.work_item_id && workReferences === null)
            || Boolean(decision.work_item_id && activityPage === null),
        },
      });
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load decision detail.");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const listRows = useMemo(() => {
    if (!records) return [];
    return records.data.map((decision) => ({
      decision,
      decisionState: decisionState(decision),
      authority: authorityLabel(decision),
      outcome: titleCase(decision.status),
      workItemId: decision.work_item_id,
      decidedAt: decision.decided_at ? formatDate(decision.decided_at) : "—",
    }));
  }, [records]);

  const loadStatus = health?.status !== "ok"
    ? "offline"
    : loading || detailLoading
      ? "loading"
      : error || healthError
        ? "partial"
        : "ready";

  const renderList = () => (
    <section className="cockpit-surface" aria-labelledby="decisions-list-title">
      <header className="cockpit-surface-header">
        <div>
          <span className="premium-label">Board transparency</span>
          <h3 id="decisions-list-title">Executive decisions</h3>
        </div>
        <span className="live-activity-total">{records?.total ?? "—"}</span>
      </header>
      {error ? (
        <div className="cockpit-partial-note" role="status">
          <strong>Decision explorer unavailable.</strong>
          <span>{error}</span>
        </div>
      ) : null}
      {!loading && !error && (!records || records.data.length === 0) ? (
        <div className="cockpit-empty-line">No executive decisions are recorded yet.</div>
      ) : null}
      {records && records.data.length > 0 ? (
        <div className="decision-table-wrap">
          <table className="decision-table">
            <thead>
              <tr>
                <th>Decision</th>
                <th>Authority</th>
                <th>Outcome</th>
                <th>Work item</th>
                <th>Decision time</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {listRows.map(({ decision, authority, outcome, workItemId, decidedAt, decisionState: rowState }) => (
                <tr
                  key={decision.id}
                  className={decision.is_current ? "decision-current" : "decision-superseded"}
                  onClick={() => void selectDecision(decision.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      void selectDecision(decision.id);
                    }
                  }}
                >
                  <td>
                    <strong>{decision.title}</strong>
                    <small>{decision.decision_key}</small>
                  </td>
                  <td>{authority}</td>
                  <td>{outcome}</td>
                  <td>{shortId(workItemId)}</td>
                  <td>{decidedAt}</td>
                  <td>
                    <span className={`decision-state ${decision.is_current ? "current" : "superseded"}`}>
                      {rowState}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {records.total_pages > 1 ? (
            <div className="decision-pagination">
              <button type="button" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
                Previous
              </button>
              <span>Page {page} of {records.total_pages}</span>
              <button
                type="button"
                disabled={page >= records.total_pages}
                onClick={() => setPage((value) => Math.min(records.total_pages, value + 1))}
              >
                Next
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
      <div className="cockpit-empty-line">
        This view reads canonical ExecutiveDecision records only. It does not create, approve, reject, or supersede decisions.
      </div>
    </section>
  );

  const renderDetail = () => {
    if (state.kind !== "detail") return null;
    const { decision, workItem, references, activities, relatedReadsPartial } = state.context;

    return (
      <section className="cockpit-surface decision-detail" aria-labelledby="decision-detail-title">
        <header className="cockpit-surface-header">
          <div>
            <span className="premium-label">Decision reconstruction · M.2</span>
            <h3 id="decision-detail-title">{decision.title}</h3>
          </div>
          <button type="button" className="premium-button ghost" onClick={() => setState({ kind: "list" })}>
            Back to list
          </button>
        </header>

        {relatedReadsPartial ? (
          <div className="cockpit-partial-note" role="status">
            <strong>Some linked context is unavailable.</strong>
            <span>The decision remains canonical; unavailable WorkItem, reference, or activity reads are not inferred.</span>
          </div>
        ) : null}

        <div className="decision-detail-grid">
          <article className="cockpit-lane">
            <header><span>Outcome</span><strong>{titleCase(decision.status)}</strong></header>
            <p>The canonical outcome recorded for this decision.</p>
          </article>
          <article className="cockpit-lane">
            <header><span>Authority</span><strong>{authorityLabel(decision)}</strong></header>
            <p>{decision.authority_level === "L4" ? "Board-level (L4) authority." : `Decision owner: ${decision.decision_owner_position}`}</p>
          </article>
          <article className="cockpit-lane">
            <header><span>Decision ID</span><strong>{decision.id}</strong></header>
            <p>Canonical identifier from ExecutiveDecision.</p>
          </article>
          <article className="cockpit-lane">
            <header><span>Linked work</span><strong>{workItem?.title ?? shortId(decision.work_item_id)}</strong></header>
            <p>{workItem ? `${titleCase(workItem.status)} · ${workItem.department}` : decision.work_item_id ? "Work item details unavailable." : "No work item is linked."}</p>
          </article>
        </div>

        <div className="decision-related-section">
          <h4>Work / mission context</h4>
          {workItem ? (
            <>
              <div className="decision-related-grid">
                <div><span>Status</span><strong>{titleCase(workItem.status)}</strong></div>
                <div><span>Department</span><strong>{workItem.department}</strong></div>
                <div><span>Assigned position</span><strong>{workItem.assigned_position_key.replaceAll("_", " ")}</strong></div>
                <div><span>Priority</span><strong>{titleCase(workItem.priority)}</strong></div>
                <div><span>Risk</span><strong>{titleCase(workItem.risk_level)}</strong></div>
                <div><span>Authority</span><strong>{workItem.authority_level}</strong></div>
                <div><span>Objective / mission key</span><strong>{workItem.objective_key || "Not recorded"}</strong></div>
                <div><span>Phase</span><strong>{workItem.phase_key || "Not recorded"}</strong></div>
                <div><span>Parent work</span><strong>{shortId(workItem.parent_work_item_id)}</strong></div>
                <div><span>Due</span><strong>{formatDate(workItem.due_at)}</strong></div>
              </div>
              <div className="decision-context-block">
                <strong>Work objective</strong>
                <p>{workItem.objective}</p>
              </div>
              <p className="cockpit-empty-line">
                Mission context is shown only from canonical WorkItem objective_key, phase_key, and parent linkage. No separate Mission record is inferred.
              </p>
            </>
          ) : (
            <div className="cockpit-empty-line">
              {decision.work_item_id ? "The decision carries a WorkItem ID, but its details are unavailable." : "This decision has no canonical WorkItem linkage."}
            </div>
          )}
        </div>

        <div className="decision-context">
          <h4>Decision context</h4>
          <div className="decision-context-block">
            <strong>Question</strong>
            <p>{decision.question}</p>
          </div>
          <div className="decision-context-block">
            <strong>Recommendation</strong>
            <p>{decision.recommendation}</p>
          </div>
          {decision.effect_summary ? (
            <div className="decision-context-block">
              <strong>Effect summary</strong>
              <p>{decision.effect_summary}</p>
            </div>
          ) : null}
        </div>

        <div className="decision-lineage">
          <h4>Governance lineage</h4>
          <div className="attention-rows">
            <div><span>Created</span><strong>{formatDate(decision.created_at)}</strong></div>
            <div><span>Decided</span><strong>{formatDate(decision.decided_at)}</strong></div>
            <div><span>Requested by</span><strong>{decision.requested_by_position.replaceAll("_", " ")}</strong></div>
            <div><span>Decided by</span><strong>{decision.decided_by || "—"}</strong></div>
            {decision.supersedes_decision_id ? (
              <div>
                <span>Supersedes</span>
                <strong><button type="button" className="decision-lineage-link" onClick={() => void selectDecision(decision.supersedes_decision_id as string)}>{shortId(decision.supersedes_decision_id)}</button></strong>
              </div>
            ) : <div><span>Supersedes</span><strong>—</strong></div>}
            {decision.superseded_by_decision_id ? (
              <div>
                <span>Superseded by</span>
                <strong><button type="button" className="decision-lineage-link" onClick={() => void selectDecision(decision.superseded_by_decision_id as string)}>{shortId(decision.superseded_by_decision_id)}</button></strong>
              </div>
            ) : <div><span>Superseded by</span><strong>—</strong></div>}
          </div>
        </div>

        <div className="decision-provenance">
          <h4>Evidence / provenance</h4>
          <div className="attention-rows">
            <div><span>Decision source fingerprint</span><strong className="decision-fingerprint">{decision.source_version || "—"}</strong></div>
            <div><span>Linked references</span><strong>{references.length}</strong></div>
          </div>
          <p className="cockpit-empty-line">
            The decision fingerprint and reference target versions are displayed exactly as provided by the backend. The Cockpit does not recompute them.
          </p>
          {references.length > 0 ? (
            <div className="decision-reference-list">
              {references.map((reference) => (
                <article key={reference.id} className="decision-reference-card">
                  <header>
                    <div>
                      <span>{referenceScope(reference, decision)} · {titleCase(reference.reference_role)}</span>
                      <strong>{reference.label || titleCase(reference.target_type)}</strong>
                    </div>
                    <small>{formatDate(reference.created_at)}</small>
                  </header>
                  <div className="decision-reference-meta">
                    <span>Target</span><strong>{reference.target_type} · {shortId(reference.target_id)}</strong>
                    <span>Version</span><strong className="decision-fingerprint">{reference.target_version || "—"}</strong>
                    <span>State</span><strong>{reference.target_state || "—"}</strong>
                  </div>
                  {reference.source_url ? (
                    <a href={reference.source_url} target="_blank" rel="noreferrer">Open recorded source</a>
                  ) : <p>No source URL is recorded for this reference.</p>}
                </article>
              ))}
            </div>
          ) : <div className="cockpit-empty-line">No decision- or WorkItem-owned record references are currently linked.</div>}
        </div>

        <div className="decision-related-section">
          <h4>Recent durable work activity</h4>
          {activities.length > 0 ? (
            <div className="decision-activity-list">
              {activities.map((activity) => (
                <article key={activity.id} className="decision-activity-card">
                  <header>
                    <div>
                      <span>{titleCase(activity.activity_class)} · {titleCase(activity.activity_type)}</span>
                      <strong>{activity.title}</strong>
                    </div>
                    <time dateTime={activity.occurred_at}>{formatDate(activity.occurred_at)}</time>
                  </header>
                  <p>{activity.summary}</p>
                  <div className="decision-reference-meta">
                    <span>Actor</span><strong>{activity.actor_id}</strong>
                    <span>Source</span><strong>{activity.source_object_type} · {shortId(activity.source_object_id)}</strong>
                    <span>Source version</span><strong className="decision-fingerprint">{activity.source_object_version || "—"}</strong>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="cockpit-empty-line">
              {decision.work_item_id ? "No durable activity is currently recorded for the linked WorkItem." : "No WorkItem is linked, so no WorkItem activity is inferred."}
            </div>
          )}
        </div>

        <div className="cockpit-empty-line">
          M.2 is read-only: it follows canonical links and provenance but does not create work, evidence, activities, decisions, or supersession.
        </div>
      </section>
    );
  };

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Decision Explorer"
        kicker="Global Mobility AIOS Cockpit · M.2 Decision → Work → Evidence"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command" aria-labelledby="decision-explorer-state-title">
        <div className="cockpit-command-copy">
          <h2 id="decision-explorer-state-title">Executive decision reconstruction</h2>
          <p>
            Inspect what was decided, by what authority, which canonical work it belongs to, its recorded evidence/provenance,
            recent durable activity, and its supersession lineage. Missing relationships remain unknown rather than being inferred.
          </p>
        </div>
      </section>

      {state.kind === "list" ? renderList() : renderDetail()}
    </WorkspaceShell>
  );
}
