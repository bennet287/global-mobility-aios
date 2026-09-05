"use client";

import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  ClientPortalDashboard,
  getClientPortalDashboard,
} from "../lib/api";


const TOKEN_STORAGE_KEY = "gmai-client-portal-token";
const DEVICE_STORAGE_KEY = "gmai-client-portal-device";

function getDeviceFingerprint(): string {
  if (typeof window === "undefined") {
    return "";
  }
  try {
    let fingerprint = sessionStorage.getItem(DEVICE_STORAGE_KEY);
    if (fingerprint) {
      return fingerprint;
    }
    const raw = [
      navigator.userAgent,
      screen.width,
      screen.height,
      screen.colorDepth,
      navigator.language,
      Intl.DateTimeFormat().resolvedOptions().timeZone,
      new Date().getTime(),
      Math.random(),
    ].join("|");
    fingerprint = btoa(raw).replace(/[^a-zA-Z0-9]/g, "").slice(0, 64);
    sessionStorage.setItem(DEVICE_STORAGE_KEY, fingerprint);
    return fingerprint;
  } catch {
    return "";
  }
}

function getDeviceLabel(): string {
  if (typeof navigator === "undefined") {
    return "Unknown device";
  }
  const platform = navigator.platform || "Unknown";
  const vendor = navigator.vendor || "";
  return `${vendor} ${platform}`.trim() || "Browser device";
}

function isDeviceMismatchError(errorText: string): boolean {
  try {
    const parsed = JSON.parse(errorText) as { action?: string; detail?: { action?: string } };
    return parsed.action === "request_new_grant" || parsed.detail?.action === "request_new_grant";
  } catch {
    return errorText.includes("request_new_grant");
  }
}

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

function PwaInstallPrompt() {
  const [prompt, setPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault();
      setPrompt(event as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!prompt || dismissed) {
    return null;
  }

  return (
    <div className="portal-install-prompt">
      <span>Add this workspace to your home screen for quick, secure access.</span>
      <button
        type="button"
        onClick={async () => {
          await prompt.prompt();
          const choice = await prompt.userChoice;
          if (choice.outcome === "accepted") {
            setPrompt(null);
          } else {
            setDismissed(true);
          }
        }}
      >
        Install
      </button>
      <button type="button" onClick={() => setDismissed(true)}>Dismiss</button>
    </div>
  );
}

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

function formatDateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function formatMoney(
  value: number | null,
  currency: string | null,
) {
  if (value == null) return "Not established";
  if (!currency) return value.toLocaleString();
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${currency} ${value.toLocaleString()}`;
  }
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
      const fingerprint = getDeviceFingerprint();
      const data = await getClientPortalDashboard(clean, fingerprint);
      sessionStorage.setItem(TOKEN_STORAGE_KEY, clean);
      setDashboard(data);
      window.history.replaceState({}, "", "/portal");
    } catch (exc) {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setDashboard(null);
      const errorText = exc instanceof Error ? exc.message : String(exc);
      if (isDeviceMismatchError(errorText)) {
        setError(
          "This secure link is bound to a different device. Please contact your consultant for a new access link."
        );
      } else {
        setError("This secure link is invalid, expired, or has been revoked.");
      }
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
      <main className="client-portal" aria-busy="true" aria-label="Secure mobility workspace">
        <div className="portal-loading" role="status" aria-live="polite">
          <span className="portal-mark" aria-hidden="true">G</span>
          <p>Opening your secure workspace...</p>
        </div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className="client-portal portal-access-screen" aria-labelledby="portal-access-title">
        <section className="portal-access-card">
          <div className="portal-brand">
            <span className="portal-mark">G</span>
            <span><strong>GMAI</strong><small>Private mobility workspace</small></span>
          </div>
          <span className="portal-eyebrow">Secure client access</span>
          <h1 id="portal-access-title">Your mobility case,<br />quietly in one place.</h1>
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
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "portal-access-error" : undefined}
            />
            {error && <div id="portal-access-error" className="portal-access-error" role="alert">{error}</div>}
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

  const plan = dashboard.mobility_plan;
  const evidence = dashboard.evidence_summary;

  return (
    <main className="client-portal" aria-labelledby="portal-workspace-title">
      <header className="portal-topbar">
        <div className="portal-brand">
          <span className="portal-mark">G</span>
          <span><strong>GMAI</strong><small>Private mobility workspace</small></span>
        </div>
        <div className="portal-session">
          <span className="portal-secure-dot" />
          <span>
            Secure session
            <small>{getDeviceLabel()}</small>
          </span>
          <button type="button" onClick={signOut}>Close</button>
        </div>
      </header>

      <div className="portal-canvas">
        <PwaInstallPrompt />

        <nav className="portal-section-navigation" aria-label="My case navigation"><a href="#overview">Overview</a><a href="#my-case">My Case</a><a href="#documents">Documents</a><a href="#timeline">Timeline</a><a href="#messages">Messages</a></nav>
        <section id="overview" className="portal-hero">
          <div>
            <span className="portal-eyebrow">Your mobility workspace</span>
            <h1 id="portal-workspace-title">Welcome back,<br />{dashboard.client_name}.</h1>
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

        <section id="my-case" className="portal-plan-section" aria-labelledby="portal-plan-title">
          <div className="portal-section-heading portal-plan-heading">
            <div>
              <span className="portal-eyebrow">Reviewed mobility plan</span>
              <h2 id="portal-plan-title">
                {plan ? plan.pathway_name : "Your route is still under review."}
              </h2>
            </div>
            {plan ? (
              <span className="portal-plan-status">Human-activated plan</span>
            ) : null}
          </div>

          {plan ? (
            <div className="portal-plan-shell">
              <div className="portal-plan-overview">
                <article>
                  <span>Route</span>
                  <strong>{pretty(plan.domain)}</strong>
                  <small>{plan.country}{" \u00b7 "}Pathway version {plan.pathway_version_number}</small>
                </article>
                <article>
                  <span>Plan state</span>
                  <strong>{pretty(plan.plan_status)}</strong>
                  <small>Activated {formatDate(plan.activated_at)}</small>
                </article>
                <article>
                  <span>Processing evidence</span>
                  <strong>{pretty(plan.processing_evidence_status)}</strong>
                  <small>Authority timing and decisions remain external.</small>
                </article>
              </div>

              <div className="portal-plan-intelligence">
                <article className="portal-plan-card">
                  <span className="portal-eyebrow">Costs</span>
                  <div className="portal-plan-stat">
                    <span>Government application fee</span>
                    <strong>
                      {formatMoney(
                        plan.cost.government_application_fee,
                        plan.cost.currency,
                      )}
                    </strong>
                    <small>
                      {plan.cost.government_application_fee_scope
                        ? pretty(plan.cost.government_application_fee_scope)
                        : "No reviewed fee scope recorded"}
                    </small>
                  </div>
                  <div className="portal-plan-mini-grid">
                    <div>
                      <span>Minimum funds</span>
                      <strong>
                        {formatMoney(plan.cost.minimum_funds, plan.cost.currency)}
                      </strong>
                    </div>
                    <div>
                      <span>Total estimate</span>
                      <strong>{pretty(plan.cost.estimated_total_status)}</strong>
                    </div>
                  </div>
                </article>

                <article className="portal-plan-card">
                  <span className="portal-eyebrow">Risk & uncertainty</span>
                  {plan.risk ? (
                    <>
                      <div className="portal-plan-stat">
                        <span>Reviewed risk level</span>
                        <strong>{pretty(plan.risk.level)}</strong>
                        <small>Recorded categories, not an outcome prediction.</small>
                      </div>
                      <div className="portal-plan-mini-grid portal-risk-grid">
                        <div>
                          <span>Declared</span>
                          <strong>{plan.risk.declared_count}</strong>
                        </div>
                        <div>
                          <span>Evidence</span>
                          <strong>{plan.risk.evidence_count}</strong>
                        </div>
                        <div>
                          <span>Regulatory</span>
                          <strong>{plan.risk.regulatory_count}</strong>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="portal-plan-muted">
                      No client-safe reviewed risk summary is available for this plan.
                    </p>
                  )}
                </article>

                <article className="portal-plan-card portal-evidence-card">
                  <span className="portal-eyebrow">Evidence review</span>
                  {evidence ? (
                    <>
                      <div className="portal-plan-stat">
                        <span>Reviewed evidence state</span>
                        <strong>{pretty(evidence.result_status)}</strong>
                        <small>Human-reviewed {formatDate(evidence.reviewed_at)}</small>
                      </div>
                      <div className="portal-plan-mini-grid">
                        <div>
                          <span>Required</span>
                          <strong>{evidence.required_count}</strong>
                        </div>
                        <div>
                          <span>Satisfied</span>
                          <strong>{evidence.satisfied_count}</strong>
                        </div>
                        <div>
                          <span>Missing</span>
                          <strong>{evidence.missing_count}</strong>
                        </div>
                        <div>
                          <span>Inconsistencies</span>
                          <strong>{evidence.inconsistency_count}</strong>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="portal-plan-muted">
                      No pathway-aligned evidence assessment has completed human review yet.
                    </p>
                  )}
                </article>
              </div>

              <div className="portal-plan-journey">
                <div>
                  <span className="portal-eyebrow">Long-term progression</span>
                  <h3>Your governed journey.</h3>
                  <p>
                    These stages come from the human-activated plan pinned to your reviewed
                    pathway. Draft simulations and stale plan versions are kept out of this
                    workspace.
                  </p>
                </div>
                <div className="portal-plan-milestones">
                  {plan.journey.map((milestone, index) => (
                    <article
                      className={`portal-plan-milestone ${milestone.state}`}
                      key={milestone.key}
                    >
                      <span className="portal-plan-order">
                        {milestone.state === "complete"
                          ? "\u2713"
                          : String(index + 1).padStart(2, "0")}
                      </span>
                      <div>
                        <strong>{milestone.title}</strong>
                        <span>
                          {pretty(milestone.state)}
                          {milestone.due_at ? (
                            <>
                              {" \u00b7 "}
                              Planned {formatDate(milestone.due_at)}
                            </>
                          ) : null}
                        </span>
                        {milestone.requires_human_approval ? (
                          <small>Human review gate</small>
                        ) : null}
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <div className="portal-plan-boundary">
                <strong>Reviewed plan &ne; authority outcome.</strong>
                <span>
                  Your team controls professional review and any submission action. The competent
                  authority controls processing and the final decision.
                </span>
              </div>
            </div>
          ) : (
            <div className="portal-plan-empty">
              <span className="portal-plan-empty-mark" aria-hidden="true">?</span>
              <div>
                <strong>No client-safe reviewed plan is visible yet.</strong>
                <p>
                  Only a current, human-activated plan tied to your present profile and a
                  reviewed pathway can appear here. Draft simulations, stale profiles, and
                  unreviewed plan state remain private to the professional workflow.
                </p>
              </div>
            </div>
          )}
        </section>

        <section id="timeline" className="portal-progress">
          <div className="portal-section-heading">
            <div>
              <span className="portal-eyebrow">Case workflow</span>
              <h2>Immediate case progress.</h2>
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

        <section id="messages" className="portal-documents" aria-labelledby="portal-messages-title"><h2 id="portal-messages-title">Messages</h2><p>A message history is not supplied by this secure case connection. Contact your mobility team through your established contact channel.</p></section>
        <section id="documents" className="portal-documents">
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

        <section className="portal-documents">
          <div className="portal-section-heading">
            <div>
              <span className="portal-eyebrow">Agency workflow</span>
              <h2>Appointments, submissions, and checklists.</h2>
            </div>
          </div>

          {dashboard.appointments.length === 0 &&
          dashboard.submissions.length === 0 &&
          dashboard.external_agency_assignments.length === 0 &&
          dashboard.authority_checklist.length === 0 ? (
            <div className="portal-empty-documents">
              No agency workflow items are visible yet. Your consultant will update this as your case progresses.
            </div>
          ) : (
            <div className="portal-agency-workflow">
              {dashboard.appointments.length > 0 && (
                <div className="portal-workflow-group">
                  <h3>Authority appointments</h3>
                  <div className="portal-document-list">
                    {dashboard.appointments.map((appointment) => (
                      <article key={appointment.id} className="portal-document-row">
                        <span className="portal-document-icon">📅</span>
                        <div>
                          <strong>{appointment.authority_name}</strong>
                          <span>
                            {pretty(appointment.appointment_type)}
                            {appointment.location ? ` · ${appointment.location}` : ""}
                          </span>
                          <span>
                            {formatDateTime(appointment.scheduled_at)}
                            {appointment.timezone ? ` (${appointment.timezone})` : ""}
                            {appointment.reference_number ? ` · Ref: ${appointment.reference_number}` : ""}
                          </span>
                        </div>
                        <span className={`portal-document-status ${appointment.status.toLowerCase()}`}>
                          {pretty(appointment.status)}
                        </span>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {dashboard.submissions.length > 0 && (
                <div className="portal-workflow-group">
                  <h3>Agency submissions</h3>
                  <div className="portal-document-list">
                    {dashboard.submissions.map((submission) => (
                      <article key={submission.id} className="portal-document-row">
                        <span className="portal-document-icon">📤</span>
                        <div>
                          <strong>{submission.authority_name}</strong>
                          <span>
                            {pretty(submission.submission_channel)}
                            {submission.reference_number ? ` · Ref: ${submission.reference_number}` : ""}
                          </span>
                          <span>Submitted {formatDateTime(submission.submitted_at)}</span>
                        </div>
                        <span className={`portal-document-status ${submission.status.toLowerCase()}`}>
                          {pretty(submission.status)}
                        </span>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {dashboard.external_agency_assignments.length > 0 && (
                <div className="portal-workflow-group">
                  <h3>External agency assignments</h3>
                  <div className="portal-document-list">
                    {dashboard.external_agency_assignments.map((assignment) => (
                      <article key={assignment.id} className="portal-document-row">
                        <span className="portal-document-icon">🏢</span>
                        <div>
                          <strong>{assignment.agency_name}</strong>
                          <span>
                            Status: {pretty(assignment.status)}
                            {assignment.sla_status ? ` · SLA ${pretty(assignment.sla_status)}` : ""}
                            {assignment.agency_reference_number ? ` · Ref: ${assignment.agency_reference_number}` : ""}
                          </span>
                          {(assignment.handoff_at || assignment.completed_at) && (
                            <span>
                              {assignment.handoff_at ? `Handoff ${formatDate(assignment.handoff_at)}` : ""}
                              {assignment.handoff_at && assignment.completed_at ? " · " : ""}
                              {assignment.completed_at ? `Completed ${formatDate(assignment.completed_at)}` : ""}
                            </span>
                          )}
                        </div>
                        <span className={`portal-document-status ${assignment.status.toLowerCase()}`}>
                          {pretty(assignment.status)}
                        </span>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {dashboard.authority_checklist.length > 0 && (
                <div className="portal-workflow-group">
                  <h3>Authority checklist</h3>
                  <div className="portal-document-list">
                    {Object.entries(
                      dashboard.authority_checklist.reduce((groups, item) => {
                        const list = groups[item.authority_name] || [];
                        list.push(item);
                        groups[item.authority_name] = list;
                        return groups;
                      }, {} as Record<string, typeof dashboard.authority_checklist>)
                    ).map(([authority, items]) => (
                      <div key={authority} className="portal-checklist-group">
                        <h4>{authority}</h4>
                        {items.map((item) => (
                          <article key={item.id} className="portal-document-row">
                            <span className="portal-document-icon">
                              {item.status === "completed" ? "✓" : item.status === "not_applicable" ? "—" : "○"}
                            </span>
                            <div>
                              <strong>{item.item_label}</strong>
                              <span>
                                {pretty(item.category)}
                                {item.is_required ? " · Required" : " · Optional"}
                              </span>
                            </div>
                            <span className={`portal-document-status ${item.status.toLowerCase()}`}>
                              {pretty(item.status)}
                            </span>
                          </article>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}
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
