"use client";

import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  ClientPortalDashboard,
  getClientPortalDashboard,
} from "../lib/api";


const TOKEN_STORAGE_KEY = "gmai-client-portal-token";

function pretty(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function ClientPortalPage() {
  const searchParams = useSearchParams();
  const [tokenInput, setTokenInput] = useState("");
  const [dashboard, setDashboard] = useState<ClientPortalDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function openPortal(candidate: string) {
    const clean = candidate.trim();
    if (!clean) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getClientPortalDashboard(clean);
      sessionStorage.setItem(TOKEN_STORAGE_KEY, clean);
      setDashboard(data);
      window.history.replaceState({}, "", "/portal");
    } catch {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setDashboard(null);
      setError("This secure link is invalid, expired, or has been revoked.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const fromUrl = searchParams.get("token") || "";
    const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY) || "";
    void openPortal(fromUrl || stored);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    void openPortal(tokenInput);
  }

  function signOut() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setTokenInput("");
    setDashboard(null);
    setError(null);
  }

  if (loading) {
    return (
      <main className="client-portal">
        <div className="portal-loading">
          <span className="portal-mark">G</span>
          <p>Opening your secure workspace...</p>
        </div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className="client-portal portal-access-screen">
        <section className="portal-access-card">
          <div className="portal-brand">
            <span className="portal-mark">G</span>
            <span><strong>GMAI</strong><small>Private mobility workspace</small></span>
          </div>
          <span className="portal-eyebrow">Secure client access</span>
          <h1>Your mobility case,<br />quietly in one place.</h1>
          <p>
            Open the expiring access link shared by your consultant. No password,
            public case search, or personal-data lookup is used.
          </p>
          <form onSubmit={submit} className="portal-token-form">
            <label htmlFor="portal-token">Access token</label>
            <input
              id="portal-token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="gmai_portal_..."
              autoComplete="off"
            />
            {error && <div className="portal-access-error">{error}</div>}
            <button type="submit" disabled={!tokenInput.trim()}>
              Open secure workspace
            </button>
          </form>
          <div className="portal-trust-row">
            <span>Encrypted transport</span>
            <span>Expiring access</span>
            <span>Audited activity</span>
          </div>
        </section>
      </main>
    );
  }

  const verifiedDocuments = Object.entries(dashboard.document_counts)
    .filter(([key]) => ["verified", "approved", "accepted"].includes(key))
    .reduce((total, [, count]) => total + count, 0);

  return (
    <main className="client-portal">
      <header className="portal-topbar">
        <div className="portal-brand">
          <span className="portal-mark">G</span>
          <span><strong>GMAI</strong><small>Private mobility workspace</small></span>
        </div>
        <div className="portal-session">
          <span className="portal-secure-dot" />
          Secure session
          <button onClick={signOut}>Close</button>
        </div>
      </header>

      <div className="portal-canvas">
        <section className="portal-hero">
          <div>
            <span className="portal-eyebrow">Your mobility workspace</span>
            <h1>Welcome back,<br />{dashboard.client_name}.</h1>
            <p>
              {pretty(dashboard.intent)}
              {dashboard.target_country ? ` · ${dashboard.target_country}` : ""}
            </p>
          </div>
          <div className="portal-next-action">
            <span>What happens next</span>
            <strong>{dashboard.next_action}</strong>
            <small>Updated {formatDate(dashboard.updated_at)}</small>
          </div>
        </section>

        <section className="portal-progress">
          <div className="portal-section-heading">
            <div>
              <span className="portal-eyebrow">Case journey</span>
              <h2>Progress without the noise.</h2>
            </div>
            <span className="portal-status-pill">{pretty(dashboard.case_status)}</span>
          </div>
          <div className="portal-milestones">
            {dashboard.milestones.map((milestone, index) => (
              <div key={milestone.key} className={`portal-milestone ${milestone.state}`}>
                <div className="portal-milestone-index">
                  {milestone.state === "complete" ? "✓" : String(index + 1).padStart(2, "0")}
                </div>
                <div>
                  <strong>{milestone.label}</strong>
                  <span>{pretty(milestone.state)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="portal-summary-grid">
          <article className="portal-summary-card feature">
            <span className="portal-eyebrow">Application</span>
            <strong>{dashboard.application_stage ? pretty(dashboard.application_stage) : "Not started"}</strong>
            <p>Your team controls submission and authority-facing actions.</p>
          </article>
          <article className="portal-summary-card">
            <span className="portal-eyebrow">Documents</span>
            <strong>{dashboard.documents.length}</strong>
            <p>{verifiedDocuments} verified or accepted</p>
          </article>
          <article className="portal-summary-card">
            <span className="portal-eyebrow">Access</span>
            <strong>{formatDate(dashboard.expires_at)}</strong>
            <p>This private link expires automatically.</p>
          </article>
        </section>

        <section className="portal-documents">
          <div className="portal-section-heading">
            <div>
              <span className="portal-eyebrow">Document room</span>
              <h2>Visible, calm, controlled.</h2>
            </div>
          </div>
          {dashboard.documents.length ? (
            <div className="portal-document-list">
              {dashboard.documents.map((document) => (
                <article key={document.id} className="portal-document-row">
                  <span className="portal-document-icon">□</span>
                  <div>
                    <strong>{pretty(document.document_type)}</strong>
                    <span>{document.filename}</span>
                  </div>
                  <span className={`portal-document-status ${document.status.toLowerCase()}`}>
                    {pretty(document.status)}
                  </span>
                </article>
              ))}
            </div>
          ) : (
            <div className="portal-empty-documents">
              Your document room is ready. Requested files will appear here.
            </div>
          )}
        </section>

        <footer className="portal-footer">
          <div className="portal-brand">
            <span className="portal-mark">G</span>
            <span><strong>GMAI</strong><small>Human-controlled mobility intelligence</small></span>
          </div>
          <p>This portal shows client-safe workflow status. It does not promise an authority outcome.</p>
        </footer>
      </div>
    </main>
  );
}
