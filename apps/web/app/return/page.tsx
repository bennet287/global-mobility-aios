"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  lookupClientCases,
  getClientReturnDashboard,
  ClientLookupResult,
  ClientReturnDashboard,
} from "../../lib/api";

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "converted"
      ? "success"
      : status === "human_review"
      ? "warning"
      : status === "needs_documents"
      ? "info"
      : "default";
  return <span className={`status-badge ${tone}`}>{status.replace(/_/g, " ")}</span>;
}

function Dashboard({ data }: { data: ClientReturnDashboard }) {
  return (
    <div className="return-dashboard">
      <div className="return-dashboard-header">
        <div>
          <h1>{data.full_name}</h1>
          <p className="intake-lead">
            {data.intent.replace(/_/g, " ")} &middot; {data.target_country || "No target country"}
          </p>
        </div>
        <StatusBadge status={data.status} />
      </div>

      {data.eligibility && (
        <div className="eligibility-summary">
          <div className="score-ring">
            <div
              className="score-value"
              style={{ "--score": `${Math.round(data.eligibility.overall_score * 100)}%` } as React.CSSProperties}
            >
              {Math.round(data.eligibility.overall_score * 100)}%
            </div>
            <small>Eligibility score</small>
          </div>
          <div className="eligibility-status">
            <small>Eligibility status</small>
            <StatusBadge status={data.eligibility.status} />
          </div>
        </div>
      )}

      <div className="return-card next-action">
        <h2>Next step</h2>
        <p>{data.next_action}</p>
      </div>

      <div className="return-grid">
        <div className="return-card">
          <h2>Checklist</h2>
          <ul>
            {data.checklist.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="return-card">
          <h2>Required documents</h2>
          {data.eligibility && data.eligibility.required_documents.length > 0 ? (
            <ul>
              {data.eligibility.required_documents.map((doc, i) => (
                <li key={i}>{doc}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">No documents required yet.</p>
          )}
        </div>
      </div>

      <div className="return-card">
        <h2>Uploaded documents</h2>
        {data.documents.length > 0 ? (
          <ul className="document-list">
            {data.documents.map((doc) => (
              <li key={doc.id}>
                <span className="doc-type">{doc.document_type}</span>
                <span className="doc-name">{doc.filename}</span>
                <StatusBadge status={doc.status} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No documents uploaded yet.</p>
        )}
      </div>

      {data.follow_ups.length > 0 && (
        <div className="return-card">
          <h2>Messages & follow-ups</h2>
          <ul className="followup-list">
            {data.follow_ups.map((f) => (
              <li key={f.id}>
                <span className="followup-channel">{f.channel}</span>
                <span className="followup-message">{f.message}</span>
                <StatusBadge status={f.status} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.eligibility && data.eligibility.pathways.length > 0 && (
        <div className="return-card">
          <h2>Plausible pathways</h2>
          <ul>
            {data.eligibility.pathways.map((pathway, i) => (
              <li key={i}>{pathway}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="form-actions">
        <Link className="button secondary" href="/">
          Operator workspace
        </Link>
        <Link className="button secondary" href="/intake">
          Start a new case
        </Link>
      </div>
    </div>
  );
}

function ReturnContent() {
  const searchParams = useSearchParams();
  const [form, setForm] = useState({ email: "", phone: "", session_token: "" });
  const [results, setResults] = useState<ClientLookupResult[] | null>(null);
  const [dashboard, setDashboard] = useState<ClientReturnDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      setForm((prev) => ({ ...prev, session_token: token }));
      handleLookup({ session_token: token });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  async function handleLookup(payload: { email?: string; phone?: string; session_token?: string }) {
    setLoading(true);
    setError(null);
    setResults(null);
    setDashboard(null);
    try {
      const cases = await lookupClientCases(payload);
      setResults(cases);
      if (cases.length === 1) {
        const data = await getClientReturnDashboard(cases[0].lead_id);
        setDashboard(data);
      } else if (cases.length === 0) {
        setError("No cases found. Check the details you entered or start a new intake.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setLoading(false);
    }
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    handleLookup({
      email: form.email || undefined,
      phone: form.phone || undefined,
      session_token: form.session_token || undefined,
    });
  }

  if (dashboard) {
    return <Dashboard data={dashboard} />;
  }

  return (
    <div className="return-page">
      <header className="return-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Client return portal</small>
          </div>
        </Link>
      </header>

      <main className="return-main">
        <section className="panel return-panel">
          <h1>Return to your case</h1>
          <p className="intake-lead">
            Enter the email, phone number, or session token you used when you started your case.
          </p>

          <form onSubmit={submit} className="return-form">
            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
              />
            </label>
            <label>
              Phone
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+1 234 567 890"
              />
            </label>
            <label className="full-field">
              Session token
              <input
                value={form.session_token}
                onChange={(e) => setForm({ ...form, session_token: e.target.value })}
                placeholder="Paste your session token"
              />
            </label>
            {error && <div className="inline-notice error">{error}</div>}
            <div className="form-actions full-field">
              <button className="button primary" type="submit" disabled={loading}>
                {loading ? "Looking up..." : "Find my case"}
              </button>
            </div>
          </form>

          {results && results.length > 1 && (
            <div className="return-results">
              <h2>Multiple cases found</h2>
              <ul>
                {results.map((c) => (
                  <li key={c.lead_id}>
                    <button
                      className="button ghost"
                      onClick={async () => {
                        setLoading(true);
                        try {
                          const data = await getClientReturnDashboard(c.lead_id);
                          setDashboard(data);
                        } catch (err) {
                          setError(err instanceof Error ? err.message : "Could not load dashboard");
                        } finally {
                          setLoading(false);
                        }
                      }}
                    >
                      {c.full_name} &middot; {c.target_country || "No country"} &middot;{" "}
                      {c.status.replace(/_/g, " ")}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default function ReturnPage() {
  return (
    <Suspense fallback={<div className="return-page"><div className="panel"><p>Loading...</p></div></div>}>
      <ReturnContent />
    </Suspense>
  );
}
