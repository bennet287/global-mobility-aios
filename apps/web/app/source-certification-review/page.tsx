"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  getHealthStatus,
  getSourceCertificationReviewQueue,
  getSourceCertificationReviewWorkspace,
  HealthStatus,
  reviewJurisdictionSourceCertification,
  SourceCertificationReviewQueue,
  SourceCertificationReviewWorkspace,
} from "../../lib/api";

function formatDate(value: string | null | undefined) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function objectText(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export default function SourceCertificationReviewPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [queue, setQueue] = useState<SourceCertificationReviewQueue | null>(null);
  const [workspace, setWorkspace] = useState<SourceCertificationReviewWorkspace | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [snapshotId, setSnapshotId] = useState<string | null>(null);
  const [decision, setDecision] = useState<"approved" | "rejected">("approved");
  const [notes, setNotes] = useState("");
  const [hashConfirmation, setHashConfirmation] = useState("");
  const [attested, setAttested] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    const [healthResult, queueResult] = await Promise.all([
      getHealthStatus(),
      getSourceCertificationReviewQueue(),
    ]);
    setHealth(healthResult.data);
    setQueue(queueResult);
    setSelectedId((current) => current || queueResult.items[0]?.certification.id || null);
  }, []);

  const loadWorkspace = useCallback(async (certificationId: string, pinnedSnapshotId?: string | null) => {
    const result = await getSourceCertificationReviewWorkspace(certificationId, pinnedSnapshotId);
    setWorkspace(result);
    if (!pinnedSnapshotId && result.review_pack?.source_snapshot?.id) {
      setSnapshotId(String(result.review_pack.source_snapshot.id));
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadQueue();
      if (selectedId) await loadWorkspace(selectedId, snapshotId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load the review workspace.");
    } finally {
      setLoading(false);
    }
  }, [loadQueue, loadWorkspace, selectedId, snapshotId]);

  useEffect(() => {
    setLoading(true);
    loadQueue()
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load review queue."))
      .finally(() => setLoading(false));
  }, [loadQueue]);

  useEffect(() => {
    if (!selectedId) {
      setWorkspace(null);
      return;
    }
    setError(null);
    setNotice(null);
    setHashConfirmation("");
    setAttested(false);
    setNotes("");
    loadWorkspace(selectedId, snapshotId)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load review evidence."));
  }, [loadWorkspace, selectedId, snapshotId]);

  const exactHash = workspace?.review_pack?.evidence_pack_sha256 || "";
  const hashMatches = exactHash.length === 64 && hashConfirmation.trim().toLowerCase() === exactHash.toLowerCase();
  const canSubmit = Boolean(
    workspace?.can_submit_review &&
    hashMatches &&
    attested &&
    notes.trim().length >= 3 &&
    workspace.review_pack,
  );

  const queueItem = useMemo(
    () => queue?.items.find((item) => item.certification.id === selectedId) || null,
    [queue, selectedId],
  );

  function selectCertification(id: string) {
    const item = queue?.items.find((candidate) => candidate.certification.id === id);
    setSelectedId(id);
    setSnapshotId(item?.selected_source_snapshot_id || null);
  }

  function downloadPack() {
    if (!workspace?.review_pack) return;
    const blob = new Blob([JSON.stringify(workspace.review_pack, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `source-certification-review-pack-${workspace.review_pack.certification_id}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function copyHash() {
    if (!exactHash) return;
    await navigator.clipboard.writeText(exactHash);
    setNotice("Exact evidence-pack SHA-256 copied. Paste it into the confirmation field after completing the review.");
  }

  async function submitReview() {
    if (!workspace?.review_pack || !canSubmit) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      await reviewJurisdictionSourceCertification(
        workspace.certification.id,
        decision,
        notes.trim(),
        {
          evidence_pack_sha256: workspace.review_pack.evidence_pack_sha256,
          source_snapshot_id: String(workspace.review_pack.source_snapshot.id),
          independent_human_attestation: true,
        },
      );
      setNotice(`Certification ${decision}. Pathway publication remains a separate controlled action.`);
      const updated = await getSourceCertificationReviewWorkspace(
        workspace.certification.id,
        String(workspace.review_pack.source_snapshot.id),
      );
      setWorkspace(updated);
      const updatedQueue = await getSourceCertificationReviewQueue();
      setQueue(updatedQueue);
      setHashConfirmation("");
      setAttested(false);
      setNotes("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review submission failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Independent Source Review"
        kicker="Evidence governance"
        loadStatus={loading ? "loading" : error ? "partial" : "ready"}
        onRefresh={refresh}
      />

      <section className="source-review-hero">
        <div>
          <span className="page-kicker">Human-controlled certification</span>
          <h2>Review immutable source evidence before certification.</h2>
          <p>
            This workspace binds one pending certification to an exact source snapshot and deterministic
            structured projection. Pack generation is read-only; approval or rejection requires a genuinely
            separate human reviewer, exact pack-hash confirmation, notes, and explicit attestation.
          </p>
        </div>
        <div className="source-review-gate">
          <span>Pending structured reviews</span>
          <strong>{queue?.total ?? "—"}</strong>
          <small>{queue?.safety_message || "Loading governed review queue…"}</small>
        </div>
      </section>

      {error ? <InlineNotice label="Review workspace error" detail={error} tone="bad" /> : null}
      {notice ? <InlineNotice label="Review workspace update" detail={notice} tone="good" /> : null}

      <section className="source-review-layout">
        <aside className="panel source-review-queue">
          <header>
            <div>
              <span className="page-kicker">Review queue</span>
              <h3>Structured certifications</h3>
            </div>
          </header>
          {queue?.items.length ? queue.items.map((item) => (
            <button
              type="button"
              className={item.certification.id === selectedId ? "active" : ""}
              key={item.certification.id}
              onClick={() => selectCertification(item.certification.id)}
            >
              <span>{item.jurisdiction.code} · v{item.certification.certification_version}</span>
              <strong>{item.official_source.name}</strong>
              <small>{item.certification.certification_scope}</small>
              <div>
                <StatusBadge value={item.certification.status} />
                <StatusBadge value={item.review_pack_state} />
              </div>
            </button>
          )) : <EmptyState title="No pending structured reviews" detail="No structured source certification currently requires review." />}
        </aside>

        <div className="source-review-main">
          {!selectedId || !workspace ? (
            <section className="panel"><EmptyState title="Select a certification" detail="Choose a pending structured source certification to inspect its immutable evidence." /></section>
          ) : (
            <>
              <section className="panel source-review-summary">
                <header>
                  <div>
                    <span className="page-kicker">Certification</span>
                    <h3>{queueItem?.official_source.name || workspace.certification.official_source_id}</h3>
                  </div>
                  <StatusBadge value={workspace.certification.status} />
                </header>
                <div className="source-review-metrics">
                  <div><span>Reviewer</span><strong>{workspace.reviewer_identity} · {workspace.reviewer_role}</strong></div>
                  <div><span>Proposer</span><strong>{workspace.certification.proposed_by}</strong></div>
                  <div><span>Pack state</span><strong>{workspace.review_pack_state}</strong></div>
                  <div><span>Can submit</span><strong>{workspace.can_submit_review ? "Yes" : "No"}</strong></div>
                </div>
                {workspace.reviewer_identity_conflict ? (
                  <InlineNotice label="Reviewer identity blocked" detail="The authenticated reviewer identity matches the proposer. This review cannot be submitted." tone="bad" />
                ) : null}
                {workspace.available_projections.length > 1 ? (
                  <label className="source-review-field">
                    <span>Exact structured projection</span>
                    <select value={snapshotId || ""} onChange={(event) => setSnapshotId(event.target.value || null)}>
                      <option value="">Select an immutable source snapshot</option>
                      {workspace.available_projections.map((item) => (
                        <option key={item.source_snapshot_id} value={item.source_snapshot_id}>
                          {item.year} · {item.scope} · {item.entry_count} entries · {item.source_snapshot_id}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
                <div className="source-review-requirements">
                  {workspace.submission_requirements.map((requirement) => <p key={requirement}>{requirement}</p>)}
                </div>
              </section>

              {workspace.review_pack ? (
                <>
                  <section className="panel source-review-pack">
                    <header>
                      <div>
                        <span className="page-kicker">Deterministic review pack</span>
                        <h3>{objectText(workspace.review_pack.structured_projection.year)} · {objectText(workspace.review_pack.structured_projection.scope)}</h3>
                      </div>
                      <button className="button secondary" type="button" onClick={downloadPack}>Download exact JSON pack</button>
                    </header>
                    <div className="source-review-hash">
                      <span>Evidence-pack SHA-256</span>
                      <code>{workspace.review_pack.evidence_pack_sha256}</code>
                      <button className="button secondary" type="button" onClick={copyHash}>Copy hash</button>
                    </div>
                    <div className="source-review-metrics">
                      <div><span>Entries</span><strong>{objectText(workspace.review_pack.structured_projection.entry_count)}</strong></div>
                      <div><span>Year</span><strong>{objectText(workspace.review_pack.structured_projection.year)}</strong></div>
                      <div><span>Scope</span><strong>{objectText(workspace.review_pack.structured_projection.scope)}</strong></div>
                      <div><span>Pack version</span><strong>{workspace.review_pack.pack_version}</strong></div>
                    </div>
                    <div className="source-review-checklist">
                      {workspace.review_pack.review_checklist.map((item, index) => (
                        <label key={item}><input type="checkbox" /> <span>{index + 1}. {item}</span></label>
                      ))}
                    </div>
                  </section>

                  <section className="source-review-compare">
                    <article className="panel">
                      <header><div><span className="page-kicker">Immutable source</span><h3>Source text</h3></div></header>
                      <pre>{workspace.review_pack.source_content_text}</pre>
                    </article>
                    <article className="panel">
                      <header><div><span className="page-kicker">Derived projection</span><h3>Structured entries</h3></div></header>
                      <div className="source-review-entries">
                        {workspace.review_pack.structured_entries.map((entry) => (
                          <div key={`${entry.source_ordinal}-${entry.entry_sha256}`}>
                            <span>#{entry.source_ordinal}</span>
                            <strong>{entry.occupation_group}</strong>
                            {entry.occupation_aliases.length ? <small>Aliases: {entry.occupation_aliases.join(" · ")}</small> : null}
                            {entry.province_names.length ? <small>Provinces: {entry.province_names.join(" · ")}</small> : null}
                            <code>{entry.entry_sha256}</code>
                          </div>
                        ))}
                      </div>
                    </article>
                  </section>

                  <section className="panel source-review-submit">
                    <header>
                      <div><span className="page-kicker">Explicit human decision</span><h3>Submit certification review</h3></div>
                      <StatusBadge value={decision} />
                    </header>
                    <InlineNotice
                      label="Independent-human review required"
                      detail="Do not use this form unless you are a genuinely separate human reviewer who personally reviewed this exact pack. A certification decision does not publish the pathway."
                      tone="warn"
                    />
                    <div className="source-review-form-grid">
                      <label className="source-review-field">
                        <span>Decision</span>
                        <select value={decision} onChange={(event) => setDecision(event.target.value as "approved" | "rejected")}>
                          <option value="approved">Approve certification</option>
                          <option value="rejected">Reject certification</option>
                        </select>
                      </label>
                      <label className="source-review-field">
                        <span>Confirm exact evidence-pack SHA-256</span>
                        <input
                          value={hashConfirmation}
                          onChange={(event) => setHashConfirmation(event.target.value)}
                          placeholder="Paste the 64-character pack hash after review"
                          spellCheck={false}
                        />
                        <small className={hashConfirmation && !hashMatches ? "danger-text" : ""}>
                          {hashMatches ? "Exact hash confirmed." : "Must exactly match the deterministic pack hash."}
                        </small>
                      </label>
                    </div>
                    <label className="source-review-field">
                      <span>Reviewer notes</span>
                      <textarea
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        rows={5}
                        placeholder="Record what you checked, any mismatch found, and the basis for the decision."
                      />
                    </label>
                    <label className="source-review-attestation">
                      <input type="checkbox" checked={attested} onChange={(event) => setAttested(event.target.checked)} />
                      <span>I attest that I am a genuinely separate human reviewer and personally reviewed the exact immutable source evidence and structured projection shown in this pack.</span>
                    </label>
                    <button className="button primary" type="button" disabled={!canSubmit || submitting} onClick={submitReview}>
                      {submitting ? "Submitting governed review…" : `Submit ${decision} review`}
                    </button>
                  </section>
                </>
              ) : (
                <section className="panel">
                  <EmptyState
                    title="Exact source snapshot required"
                    detail="This source has multiple structured projections. Pin one immutable source snapshot before a review pack can be generated or submitted."
                  />
                </section>
              )}

              <section className="panel source-review-history">
                <header><div><span className="page-kicker">Audit closure</span><h3>Review history</h3></div></header>
                {workspace.review_history.length ? workspace.review_history.map((item) => (
                  <article key={item.id}>
                    <div><StatusBadge value={item.decision || "reviewed"} /><strong>{item.actor}</strong><span>{formatDate(item.created_at)}</span></div>
                    <p>{item.notes || "No review notes recorded."}</p>
                    <small>Attestation: {item.independent_human_attestation ? "recorded" : "not recorded"}</small>
                    {item.evidence_pack_sha256 ? <code>{item.evidence_pack_sha256}</code> : null}
                  </article>
                )) : <EmptyState title="No review decision recorded" detail="The evidence pack is prepared, but no independent-human certification decision has been submitted." />}
              </section>
            </>
          )}
        </div>
      </section>
    </WorkspaceShell>
  );
}
