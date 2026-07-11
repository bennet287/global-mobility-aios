"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CommunicationDraft,
  generateDraftPack,
  getLeadCommunications,
  LeadCommunications,
  markAllDraftsReviewed,
} from "../../../../lib/api";
import { WorkspaceShell } from "../../../../components/WorkspaceShell";
import { Topbar } from "../../../../components/Topbar";
import { StatusBadge } from "../../../../components/StatusBadge";
import { SectionTitle } from "../../../../components/SectionTitle";
import { EmptyState } from "../../../../components/EmptyState";
import { InlineNotice } from "../../../../components/InlineNotice";
import { useBackendStatus } from "../../../../hooks/useBackendStatus";
import { titleCase } from "../../../../lib/utils";

export default function LeadCommunicationsPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [data, setData] = useState<LeadCommunications | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const payload = await getLeadCommunications(id);
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load communications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const handleGeneratePack = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await generateDraftPack(id);
      setResult(`Created ${res.created_count} draft(s). Skipped ${res.skipped_existing_count} existing.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate draft pack");
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAllReviewed = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await markAllDraftsReviewed(id);
      setResult(`Marked ${res.reviewed_count} draft(s) as reviewed.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark drafts reviewed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={data?.lead.full_name || "Lead communications"}
        kicker="Client communication workspace"
        loadStatus={loading ? "loading" : "ready"}
        onRefresh={load}
      />
      <div className="back-link">
        <Link href="/communications">← Communications queue</Link>
      </div>

      {error && <InlineNotice label="Error" detail={error} />}
      {result && <InlineNotice label="Success" detail={result} />}

      {!data ? (
        <section className="panel">
          <EmptyState title="Loading" detail="Fetching lead communication workspace." />
        </section>
      ) : (
        <>
          <section className="panel">
            <SectionTitle
              label="Summary"
              title="Communication readiness"
              detail={data.summary.next_action}
            />
            <div className="agent-review-counts">
              <div className="metric-pill">
                <span>Drafts</span>
                <strong>{data.summary.draft_count}</strong>
              </div>
              <div className="metric-pill warn">
                <span>Stage</span>
                <strong>{titleCase(data.summary.stage)}</strong>
              </div>
            </div>
            <div className="form-actions">
              <button className="button" onClick={handleGeneratePack} disabled={loading}>
                Generate draft pack
              </button>
              <button className="button secondary" onClick={handleMarkAllReviewed} disabled={loading}>
                Mark all reviewed
              </button>
            </div>
          </section>

          <section className="panel">
            <SectionTitle label="Drafts" title="Lead communication drafts" detail={`${data.drafts.length} drafts`} />
            {data.drafts.length === 0 ? (
              <EmptyState title="No drafts" detail="Generate a draft pack to create client communication drafts." />
            ) : (
              <div className="compact-list">
                {data.drafts.map((item) => (
                  <DraftRow item={item} key={item.draft.id} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}

function DraftRow({ item }: { item: CommunicationDraft }) {
  return (
    <div className="compact-row communication-draft-row">
      <div>
        <strong>{item.communication.title}</strong>
        <span>{item.communication.subject}</span>
      </div>
      <div className="draft-row-actions">
        <StatusBadge value={item.communication.status} />
        <Link className="button secondary" href={`/communications/drafts/${item.draft.id}`}>
          Review
        </Link>
      </div>
    </div>
  );
}
