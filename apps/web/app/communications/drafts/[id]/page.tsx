"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CommunicationDraft,
  getCommunicationDraft,
  markDraftReviewed,
  updateCommunicationDraft,
} from "../../../../lib/api";
import { WorkspaceShell } from "../../../../components/WorkspaceShell";
import { Topbar } from "../../../../components/Topbar";
import { StatusBadge } from "../../../../components/StatusBadge";
import { SectionTitle } from "../../../../components/SectionTitle";
import { EmptyState } from "../../../../components/EmptyState";
import { InlineNotice } from "../../../../components/InlineNotice";
import { useBackendStatus } from "../../../../hooks/useBackendStatus";

export default function DraftDetailPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [draft, setDraft] = useState<CommunicationDraft | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCommunicationDraft(id);
      setDraft(data);
      setSubject(data.communication.subject);
      setBody(data.communication.body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load draft");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const handleSave = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      await updateCommunicationDraft(id, { subject, body, note });
      setResult("Draft updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      await markDraftReviewed(id, { subject, body, note });
      setResult("Draft marked as reviewed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setLoading(false);
    }
  };

  const isReviewed = draft?.communication.status === "reviewed";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={draft?.communication.title || "Communication draft"}
        kicker="Draft review"
        loadStatus={loading ? "loading" : "ready"}
        onRefresh={load}
      />
      <div className="back-link">
        <Link href="/communications">← Communications queue</Link>
      </div>

      {error && <InlineNotice label="Error" detail={error} />}
      {result && <InlineNotice label="Success" detail={result} />}

      {!draft ? (
        <section className="panel">
          <EmptyState title="Loading draft" detail="Fetching communication draft details." />
        </section>
      ) : (
        <>
          <section className="panel">
            <SectionTitle
              label="Draft"
              title={draft.communication.title}
              detail={`Template: ${draft.communication.template_key} · Status: ${draft.communication.status}`}
            />
            <div className="draft-meta-row">
              <StatusBadge value={draft.communication.status} />
              {draft.lead && (
                <Link href={`/communications/leads/${draft.lead.id}`}>
                  Lead: {draft.lead.full_name}
                </Link>
              )}
            </div>

            <div className="form-stack">
              <label>
                <span>Subject</span>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={isReviewed}
                />
              </label>
              <label>
                <span>Body</span>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={12}
                  disabled={isReviewed}
                />
              </label>
              <label>
                <span>Reviewer note</span>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note added when reviewing"
                />
              </label>
            </div>

            <div className="form-actions">
              <button className="button" onClick={handleSave} disabled={loading || isReviewed}>
                Save draft
              </button>
              <button className="button primary" onClick={handleReview} disabled={loading || isReviewed}>
                Mark reviewed
              </button>
            </div>

            <div className="send-blocker">
              <strong>Sending blocked</strong>
              <span>
                This MVP does not send email or WhatsApp messages automatically. Copy the reviewed draft and send it
                manually outside the system.
              </span>
            </div>
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}
