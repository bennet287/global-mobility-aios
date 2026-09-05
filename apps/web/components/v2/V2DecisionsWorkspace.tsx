"use client";
import { useCallback, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2Read } from "../../hooks/useV2Read";
import { decideBoardItem, getOrganizationDecisionRecord, listOrganizationDecisionRecords, listOrganizationRecordReferences } from "../../lib/api";
import { V2Shell } from "./V2Shell";
import { useV2SearchItems } from "./V2NavigationContext";
import { EmptyState, Provenance, ReadState, RecordFields, RelatedLink, SourceLink, StatusLabel, TruthBadge, V2PageHeader, formatV2Date, v2Styles as s } from "./V2Primitives";

function DecisionDetail({ id, onChanged }: { id: string; onChanged: () => void }) {
  const load = useCallback(async () => {
    const decision = await getOrganizationDecisionRecord(id);
    const references = await Promise.allSettled([listOrganizationRecordReferences({ decision_id: id, page_size: 100 })]);
    return { decision, references: references[0].status === "fulfilled" ? references[0].value : null };
  }, [id]);
  const read = useV2Read(load);
  useV2SearchItems(read.data ? [{ kind: "Decision", label: read.data.decision.title, description: read.data.decision.status, icon: "decisions", href: `/cockpit/v2/decisions?decision=${encodeURIComponent(id)}` }] : []);
  const [outcome, setOutcome] = useState<"approved" | "rejected" | "returned">("returned");
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reconcileRequired, setReconcileRequired] = useState(false);
  const decision = read.data?.decision;
  async function submit() {
    if (!decision || pending || !confirmed || reason.trim().length < 8 || reconcileRequired || read.loading || read.error) return;
    setPending(true); setActionError(null); setMessage(null);
    try {
      const current = await getOrganizationDecisionRecord(id);
      if (!current.is_current || current.status !== "pending_board" || current.updated_at !== decision.updated_at) {
        setActionError("This decision changed. Refresh and review the current record before acting.");
        setReconcileRequired(true); return;
      }
      const result = await decideBoardItem(id, outcome, reason.trim());
      setMessage(`Recorded status: ${result.status}.`);
      setReason(""); setConfirmed(false);
      await read.refresh(); onChanged();
    } catch (error) {
      setActionError(`${error instanceof Error ? error.message : "Decision request failed."} Refresh the record to reconcile the outcome before another submission.`);
      setReconcileRequired(true);
    } finally { setPending(false); }
  }
  return <article className={s.detail} data-guide="decision-detail">
    <ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />
    {decision ? <><TruthBadge kind={decision.status === "pending_board" ? "authority" : "canonical"} /><h2>{decision.title}</h2><StatusLabel value={decision.is_current ? decision.status : "superseded"} /><h3>The question</h3><p>{decision.question}</p><TruthBadge kind="recommendation" /><p>{decision.recommendation}</p><p>Authority: {decision.authority_level} · Decision owner: {decision.decision_owner_position}</p>
      {decision.decision_reason ? <section><h3>Recorded outcome</h3><p>{decision.decision_reason}</p><p>{decision.decided_by ?? "Actor not supplied"} · {formatV2Date(decision.decided_at)}</p></section> : null}
      <h3>Evidence & supporting records</h3>{read.data?.references === null ? <p role="status">Reference source unavailable. Evidence completeness cannot be assessed.</p> : <ul className={s.list}>{read.data?.references?.data.map((reference) => <li className={s.row} key={reference.id}><div><strong>{reference.label ?? reference.target_type}</strong><p>{reference.reference_role} · {reference.target_state ?? "State not supplied"}</p>{reference.source_url ? <SourceLink url={reference.source_url}>Source</SourceLink> : null}{reference.target_type === "verified_rule" ? <RelatedLink href={`/cockpit/v2/evidence?rule=${encodeURIComponent(reference.target_id)}`}>Inspect rule</RelatedLink> : null}<Provenance><RecordFields values={{ target_type: reference.target_type, target_id: reference.target_id, target_version: reference.target_version, reference_role: reference.reference_role, reference_id: reference.id }} /></Provenance></div></li>)}</ul>}
      <p>{read.data?.references ? `${read.data.references.data.length} of ${read.data.references.total} references returned.` : ""}</p>
      <Provenance label="Decision lineage"><RecordFields values={{ decision_id: decision.id, decision_key: decision.decision_key, work_item_id: decision.work_item_id, source_version: decision.source_version, created_at: decision.created_at, updated_at: decision.updated_at, supersedes_decision_id: decision.supersedes_decision_id, superseded_by_decision_id: decision.superseded_by_decision_id, expires_at: decision.expires_at, effect_summary: decision.effect_summary }} /></Provenance>
      {decision.superseded_by_decision_id ? <RelatedLink href={`/cockpit/v2/decisions?decision=${encodeURIComponent(decision.superseded_by_decision_id)}`}>Current decision</RelatedLink> : null}{decision.work_item_id ? <RelatedLink href={`/cockpit/v2/history?work=${encodeURIComponent(decision.work_item_id)}`}>Linked work history</RelatedLink> : null}
      {message ? <p role="status">{message}</p> : null}{actionError ? <p role="alert">{actionError}</p> : null}
      {reconcileRequired ? <div className={s.actions}><button type="button" disabled={pending || read.loading} onClick={async () => { await read.refresh(); setReconcileRequired(false); setConfirmed(false); }}>Refresh outcome before review</button></div> : null}
      {decision.is_current && decision.status === "pending_board" ? <form className={s.form} onSubmit={(event) => { event.preventDefault(); void submit(); }}><TruthBadge kind="authority" /><h3>Record a Board decision</h3><p>This changes the decision record. Your authenticated authority is checked by the backend.</p><label>Outcome<select value={outcome} disabled={pending} onChange={(event) => { setOutcome(event.target.value as typeof outcome); setConfirmed(false); }}><option value="returned">Return for revision</option><option value="approved">Approve</option><option value="rejected">Reject</option></select></label><label>Rationale<textarea required minLength={8} value={reason} disabled={pending} onChange={(event) => { setReason(event.target.value); setConfirmed(false); }} /></label><label><span><input type="checkbox" checked={confirmed} disabled={pending} onChange={(event) => setConfirmed(event.target.checked)} /> I reviewed this decision and intend to record this outcome.</span></label><button type="submit" disabled={pending || read.loading || Boolean(read.error) || !confirmed || reason.trim().length < 8 || reconcileRequired}>{pending ? "Recording…" : `Record: ${outcome}`}</button></form> : null}
    </> : null}
  </article>;
}

export function V2DecisionsWorkspace() {
  const { health } = useBackendStatus();
  const params = useSearchParams();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const selectedId = params.get("decision") ?? selected;
  const load = useCallback(() => listOrganizationDecisionRecords({ page, page_size: 25, status: status || undefined }), [page, status]);
  const read = useV2Read(load);
  return <V2Shell activeItem="Decisions" backendOnline={health?.status === "ok"}>
    <V2PageHeader eyebrow="Accountable choices" title="Decisions" description="Understand the question, examine its evidence, and act through explicit authority."><button type="button" onClick={() => void read.refresh()}>Refresh</button></V2PageHeader>
    <ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />
    <div className={s.toolbar}><label>Decision state<select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">All states</option>{["pending_board", "pending_ceo", "approved", "rejected", "returned"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label><button type="button" disabled={page === 1 || read.loading} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page}{read.data ? ` of ${Math.max(1, read.data.total_pages)} · ${read.data.total} records` : ""}</span><button type="button" disabled={!read.data || read.loading || page >= read.data.total_pages} onClick={() => setPage(page + 1)}>Next</button></div>
    <div className={s.split}><nav aria-label="Decision records"><ul className={s.list}>{read.data?.data.map((item) => <li key={item.id}><button type="button" className={s.row} aria-pressed={selectedId === item.id} onClick={() => { setSelected(item.id); window.history.replaceState(null, "", `?decision=${encodeURIComponent(item.id)}`); }}><div><strong>{item.title}</strong><small>{item.authority_level} · {item.decision_owner_position}</small></div><StatusLabel value={item.is_current ? item.status : "superseded"} /></button></li>)}</ul>{!read.loading && !read.error && !read.data?.data.length ? <EmptyState title="No decisions returned" detail="No decision in this result set matches the selected state." /> : null}</nav>{selectedId ? <DecisionDetail key={selectedId} id={selectedId} onChanged={() => void read.refresh()} /> : <EmptyState title="Choose a decision" detail="Inspect its question and recommendation before opening the evidence or recording an outcome." />}</div>
  </V2Shell>;
}
