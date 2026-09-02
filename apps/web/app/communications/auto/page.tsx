"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getAutoCommunicationTemplates,
  createAutoCommunication,
  listAutoCommunications,
  AutoCommunication,
  AutoCommunicationTemplate,
} from "../../../lib/api";

const TRIGGERS = [
  { key: "intake_submitted", label: "Intake submitted" },
  { key: "document_uploaded", label: "Document uploaded" },
  { key: "eligibility_ready", label: "Eligibility ready" },
  { key: "missing_documents", label: "Missing documents" },
];

export default function AutoCommunicationsPage() {
  const [leadId, setLeadId] = useState("");
  const [trigger, setTrigger] = useState("intake_submitted");
  const [templates, setTemplates] = useState<Record<string, AutoCommunicationTemplate>>({});
  const [communications, setCommunications] = useState<AutoCommunication[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAutoCommunicationTemplates()
      .then((data) => setTemplates(data.templates))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load templates"));
  }, []);

  async function loadCommunications() {
    if (!leadId.trim()) return;
    try {
      const data = await listAutoCommunications(leadId.trim());
      setCommunications(data.communications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load communications");
    }
  }

  async function generate() {
    if (!leadId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createAutoCommunication(leadId.trim(), trigger);
      await loadCommunications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auto-communications-page">
      <header className="page-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Automated client communications</small>
          </div>
        </Link>
      </header>

      <main className="page-main">
        <section className="panel">
          <h1>Automated communications</h1>
          <p className="intake-lead">
            Generate review-gated follow-up messages triggered by intake, document uploads, and
            eligibility updates.
          </p>

          <div className="matcher-bar">
            <label>
              Lead ID
              <input
                value={leadId}
                onChange={(e) => setLeadId(e.target.value)}
                placeholder="Paste lead UUID"
              />
            </label>
            <label>
              Trigger
              <select value={trigger} onChange={(e) => setTrigger(e.target.value)}>
                {TRIGGERS.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="button primary"
              onClick={generate}
              disabled={loading || !leadId.trim()}
            >
              {loading ? "Generating..." : "Generate draft"}
            </button>
            <button
              className="button secondary"
              onClick={loadCommunications}
              disabled={!leadId.trim()}
            >
              Load history
            </button>
          </div>

          {error && <div className="inline-notice error">{error}</div>}

          {Object.keys(templates).length > 0 && (
            <div className="templates-list">
              <h2>Templates</h2>
              <ul>
                {Object.entries(templates).map(([key, tmpl]) => (
                  <li key={key}>
                    <strong>{key}</strong>
                    <span className="template-subject">{tmpl.subject}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {communications.length > 0 && (
            <div className="communications-list">
              <h2>Scheduled / sent messages</h2>
              {communications.map((comm, i) => (
                <div key={i} className="communication-card">
                  <div className="communication-header">
                    <strong>{comm.trigger}</strong>
                    <StatusBadge status={comm.status} />
                  </div>
                  <p className="communication-subject">{comm.subject}</p>
                  <pre className="communication-body">{comm.body}</pre>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const tone = status === "pending" ? "warning" : status === "completed" ? "success" : "default";
  return <span className={`status-badge ${tone}`}>{status}</span>;
}
