"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import {
  type ExecutiveDecision,
  type OrganizationRecordPage,
  getOrganizationDecisionRecord,
  listOrganizationDecisionRecords,
} from "../../../lib/api";
import { titleCase } from "../../../lib/utils";

const PAGE_SIZE = 50;

type DecisionExplorerState =
  | { kind: "list" }
  | { kind: "detail"; decision: ExecutiveDecision };

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

export default function DecisionExplorerPage() {
  const { health, error: healthError } = useBackendStatus();
  const [page, setPage] = useState(1);
  const [records, setRecords] = useState<OrganizationRecordPage<ExecutiveDecision> | null>(null);
  const [loading, setLoading] = useState(true);
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
    try {
      const decision = await getOrganizationDecisionRecord(id);
      setState({ kind: "detail", decision });
    } catch {
      // Fall back to the row already loaded; detail is a richer read but not required.
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
    : loading
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
              {listRows.map(({ decision, authority, outcome, workItemId, decidedAt, decisionState }) => (
                <tr
                  key={decision.id}
                  className={decision.is_current ? "decision-current" : "decision-superseded"}
                  onClick={() => selectDecision(decision.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      selectDecision(decision.id);
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
                      {decisionState}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {records && records.total_pages > 1 ? (
            <div className="decision-pagination">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span>
                Page {page} of {records.total_pages}
              </span>
              <button
                type="button"
                disabled={page >= records.total_pages}
                onClick={() => setPage((p) => Math.min(records.total_pages, p + 1))}
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
    const decision = state.decision;
    return (
      <section className="cockpit-surface decision-detail" aria-labelledby="decision-detail-title">
        <header className="cockpit-surface-header">
          <div>
            <span className="premium-label">Decision detail</span>
            <h3 id="decision-detail-title">{decision.title}</h3>
          </div>
          <button
            type="button"
            className="premium-button ghost"
            onClick={() => setState({ kind: "list" })}
          >
            Back to list
          </button>
        </header>

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
            <header><span>Work item</span><strong>{shortId(decision.work_item_id)}</strong></header>
            {decision.work_item_id ? (
              <p>
                <Link href={`/cockpit/work-items/${decision.work_item_id}`}>View associated work</Link>
              </p>
            ) : (
              <p>No work item is linked to this decision.</p>
            )}
          </article>
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
                <strong>
                  <button
                    type="button"
                    className="decision-lineage-link"
                    onClick={() => selectDecision(decision.supersedes_decision_id as string)}
                  >
                    {shortId(decision.supersedes_decision_id)}
                  </button>
                </strong>
              </div>
            ) : (
              <div><span>Supersedes</span><strong>—</strong></div>
            )}
            {decision.superseded_by_decision_id ? (
              <div>
                <span>Superseded by</span>
                <strong>
                  <button
                    type="button"
                    className="decision-lineage-link"
                    onClick={() => selectDecision(decision.superseded_by_decision_id as string)}
                  >
                    {shortId(decision.superseded_by_decision_id)}
                  </button>
                </strong>
              </div>
            ) : (
              <div><span>Superseded by</span><strong>—</strong></div>
            )}
          </div>
        </div>

        <div className="decision-provenance">
          <h4>Evidence / provenance</h4>
          <div className="attention-rows">
            <div>
              <span>Source fingerprint</span>
              <strong className="decision-fingerprint">{decision.source_version || "—"}</strong>
            </div>
          </div>
          <p className="cockpit-empty-line">
            The source fingerprint is exposed exactly as recorded by the backend. The Cockpit does not recompute it.
          </p>
        </div>
      </section>
    );
  };

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Decision Explorer"
        kicker="Global Mobility AIOS Cockpit · M.1 Board Transparency"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command" aria-labelledby="decision-explorer-state-title">
        <div className="cockpit-command-copy">
          <h2 id="decision-explorer-state-title">Executive decision transparency</h2>
          <p>
            This Cockpit surface shows what was decided, by what authority, for which work, when, and from what evidence.
            It is read-only and does not create, approve, reject, or supersede canonical decisions.
          </p>
        </div>
      </section>

      {state.kind === "list" ? renderList() : renderDetail()}
    </WorkspaceShell>
  );
}
