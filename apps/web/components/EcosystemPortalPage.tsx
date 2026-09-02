"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  EcosystemPortalDashboard,
  getEcosystemPortalDashboard,
} from "../lib/api";


const TOKEN_STORAGE_KEY = "gmai-ecosystem-portal-token";

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

export function EcosystemPortalPage() {
  const searchParams = useSearchParams();
  const [tokenInput, setTokenInput] = useState("");
  const [dashboard, setDashboard] = useState<EcosystemPortalDashboard | null>(null);
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
      const data = await getEcosystemPortalDashboard(clean);
      sessionStorage.setItem(TOKEN_STORAGE_KEY, clean);
      setDashboard(data);
      window.history.replaceState({}, "", "/partner-portal");
    } catch {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setDashboard(null);
      setError("This tenant link is invalid, expired, or has been revoked.");
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

  const totalCases = dashboard?.cases.length || 0;
  const activeCases = useMemo(
    () => dashboard?.cases.filter((item) => item.status === "active").length || 0,
    [dashboard],
  );
  const openCompliance = useMemo(
    () => dashboard?.cases.reduce((total, item) => total + item.open_compliance_items, 0) || 0,
    [dashboard],
  );

  if (loading) {
    return (
      <main className="ecosystem-portal">
        <div className="ecosystem-loading"><span>G</span><p>Opening tenant workspace...</p></div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className="ecosystem-portal ecosystem-access">
        <section className="ecosystem-access-card">
          <div className="ecosystem-brand"><span>G</span><strong>GMAI</strong></div>
          <p className="ecosystem-kicker">Employer & partner access</p>
          <h1>One account.<br />One controlled view.</h1>
          <p className="ecosystem-access-copy">
            Use the expiring tenant link shared by your mobility team. It can view
            only the corporate account assigned to it.
          </p>
          <form onSubmit={submit}>
            <label htmlFor="ecosystem-token">Tenant access token</label>
            <input
              id="ecosystem-token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="gmai_ecosystem_..."
              autoComplete="off"
            />
            {error ? <div className="portal-access-error">{error}</div> : null}
            <button disabled={!tokenInput.trim()}>Open tenant workspace</button>
          </form>
          <div className="ecosystem-trust">
            <span>Account scoped</span><span>Revocable</span><span>Audited</span>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="ecosystem-portal">
      <header className="ecosystem-topbar">
        <div className="ecosystem-brand"><span>G</span><strong>GMAI</strong></div>
        <div>
          <span className="ecosystem-session-dot" /> Tenant-secure session
          <button onClick={signOut}>Close</button>
        </div>
      </header>

      <div className="ecosystem-canvas">
        <section className="ecosystem-hero">
          <div>
            <p className="ecosystem-kicker">{pretty(dashboard.audience_type)} workspace</p>
            <h1>{dashboard.account_name}</h1>
            <p>{dashboard.primary_country} · Account status {pretty(dashboard.account_status)}</p>
          </div>
          <aside>
            <span>Tenant boundary</span>
            <strong>Only this account is visible.</strong>
            <p>No operator tools, internal notes, or other employer records are available.</p>
          </aside>
        </section>

        <section className="ecosystem-metrics">
          <article><span>Total cases</span><strong>{totalCases}</strong><small>Scoped to this account</small></article>
          <article><span>Active</span><strong>{activeCases}</strong><small>Controlled mobility cases</small></article>
          <article><span>Compliance</span><strong>{openCompliance}</strong><small>Open dated items</small></article>
          <article><span>Access expires</span><strong>{formatDate(dashboard.expires_at)}</strong><small>Renew through your mobility team</small></article>
        </section>

        <section className="ecosystem-case-section">
          <div className="ecosystem-section-heading">
            <div><p className="ecosystem-kicker">Mobility portfolio</p><h2>Cases that need a clear next move.</h2></div>
            <span>{totalCases} visible</span>
          </div>
          {dashboard.cases.length ? (
            <div className="ecosystem-case-grid">
              {dashboard.cases.map((item) => (
                <article key={item.case_reference}>
                  <div className="ecosystem-case-top">
                    <span>{pretty(item.case_type)}</span>
                    <b className={`ecosystem-status ${item.status}`}>{pretty(item.status)}</b>
                  </div>
                  <h3>{item.employee_name || item.case_reference}</h3>
                  <p className="ecosystem-reference">{item.case_reference}</p>
                  <div className="ecosystem-route">
                    <span>{item.origin_country || "Origin pending"}</span>
                    <i>→</i>
                    <strong>{item.destination_country}</strong>
                  </div>
                  <div className="ecosystem-case-counts">
                    <span><b>{item.open_tasks}</b> open tasks</span>
                    <span><b>{item.open_compliance_items}</b> compliance items</span>
                  </div>
                  <div className="ecosystem-next">
                    <span>Next controlled action</span>
                    <p>{item.next_action}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="ecosystem-empty">No mobility cases are currently assigned to this account.</div>
          )}
        </section>

        <section className="ecosystem-compliance-section">
          <div className="ecosystem-section-heading">
            <div><p className="ecosystem-kicker">Compliance calendar</p><h2>Upcoming obligations.</h2></div>
          </div>
          {dashboard.upcoming_compliance.length ? (
            <div className="ecosystem-compliance-list">
              {dashboard.upcoming_compliance.map((item) => (
                <article key={`${item.case_reference}-${item.title}-${item.due_at}`}>
                  <time dateTime={item.due_at}>{formatDate(item.due_at)}</time>
                  <div><strong>{item.title}</strong><span>{item.case_reference} · {pretty(item.event_type)}</span></div>
                  <b>{item.evidence_required ? "Evidence required" : "Tracked"}</b>
                </article>
              ))}
            </div>
          ) : (
            <div className="ecosystem-empty">No open compliance deadlines are visible.</div>
          )}
        </section>

        <footer className="ecosystem-footer">
          <div className="ecosystem-brand"><span>G</span><strong>GMAI</strong></div>
          <p>Tenant-scoped operational visibility. Authority outcomes remain independently determined.</p>
        </footer>
      </div>
    </main>
  );
}
