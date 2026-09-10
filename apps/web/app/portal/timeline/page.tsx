"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ClientPortalDashboard, getClientPortalDashboard } from "../../../lib/api";
import styles from "./TimelineV2.module.css";

const TOKEN_STORAGE_KEY = "gmai-client-portal-token";
const DEVICE_STORAGE_KEY = "gmai-client-portal-device";

type JourneyStep = {
  key: string;
  title: string;
  state: "complete" | "current" | "upcoming" | "attention";
  dueAt: string | null;
  requiresHumanApproval: boolean;
};

type TimelineRecord = {
  key: string;
  kind: "Appointment" | "Submission" | "External support";
  title: string;
  detail: string;
  status: string;
  occurredAt: string | null;
};

function getDeviceFingerprint(): string {
  if (typeof window === "undefined") return "";
  try {
    let fingerprint = sessionStorage.getItem(DEVICE_STORAGE_KEY);
    if (fingerprint) return fingerprint;
    const raw = [
      navigator.userAgent,
      screen.width,
      screen.height,
      screen.colorDepth,
      navigator.language,
      Intl.DateTimeFormat().resolvedOptions().timeZone,
      Date.now(),
      Math.random(),
    ].join("|");
    fingerprint = btoa(raw).replace(/[^a-zA-Z0-9]/g, "").slice(0, 64);
    sessionStorage.setItem(DEVICE_STORAGE_KEY, fingerprint);
    return fingerprint;
  } catch {
    return "";
  }
}

function pretty(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value?: string | null) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function formatDateTime(value?: string | null) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isDeviceMismatchError(errorText: string): boolean {
  try {
    const parsed = JSON.parse(errorText) as { action?: string; detail?: { action?: string } };
    return parsed.action === "request_new_grant" || parsed.detail?.action === "request_new_grant";
  } catch {
    return errorText.includes("request_new_grant");
  }
}

function journeySteps(dashboard: ClientPortalDashboard): JourneyStep[] {
  if (dashboard.mobility_plan?.journey.length) {
    return dashboard.mobility_plan.journey.map((step) => ({
      key: step.key,
      title: step.title,
      state: step.state,
      dueAt: step.due_at,
      requiresHumanApproval: step.requires_human_approval,
    }));
  }
  return dashboard.milestones.map((step) => ({
    key: step.key,
    title: step.label,
    state: step.state,
    dueAt: null,
    requiresHumanApproval: false,
  }));
}

function timelineRecords(dashboard: ClientPortalDashboard): TimelineRecord[] {
  const records: TimelineRecord[] = [
    ...dashboard.appointments.map((appointment) => ({
      key: `appointment-${appointment.id}`,
      kind: "Appointment" as const,
      title: `${pretty(appointment.appointment_type)} · ${appointment.authority_name}`,
      detail: appointment.location || "Location not available",
      status: appointment.status,
      occurredAt: appointment.scheduled_at || null,
    })),
    ...dashboard.submissions.map((submission) => ({
      key: `submission-${submission.id}`,
      kind: "Submission" as const,
      title: `Submitted to ${submission.authority_name}`,
      detail: `${pretty(submission.submission_channel)}${submission.reference_number ? ` · Reference ${submission.reference_number}` : ""}`,
      status: submission.status,
      occurredAt: submission.submitted_at || null,
    })),
    ...dashboard.external_agency_assignments.map((assignment) => ({
      key: `agency-${assignment.id}`,
      kind: "External support" as const,
      title: assignment.agency_name,
      detail: assignment.completed_at
        ? "External support completion recorded"
        : assignment.handoff_at
          ? "External support handoff recorded"
          : "No handoff date is available",
      status: assignment.status,
      occurredAt: assignment.completed_at || assignment.handoff_at || null,
    })),
  ];

  return records.sort((left, right) => {
    if (!left.occurredAt) return right.occurredAt ? 1 : 0;
    if (!right.occurredAt) return -1;
    return new Date(right.occurredAt).getTime() - new Date(left.occurredAt).getTime();
  });
}

function MobilityTimelineContent() {
  const searchParams = useSearchParams();
  const [tokenInput, setTokenInput] = useState("");
  const [dashboard, setDashboard] = useState<ClientPortalDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function openTimeline(candidate: string) {
    const clean = candidate.trim();
    if (!clean) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getClientPortalDashboard(clean, getDeviceFingerprint());
      sessionStorage.setItem(TOKEN_STORAGE_KEY, clean);
      setDashboard(data);
      window.history.replaceState({}, "", "/portal/timeline");
    } catch (exc) {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setDashboard(null);
      const errorText = exc instanceof Error ? exc.message : String(exc);
      setError(
        isDeviceMismatchError(errorText)
          ? "This secure link is bound to a different device. Please request a new access link from your consultant."
          : "This secure link is invalid, expired, or has been revoked.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const fromUrl = searchParams.get("token") || "";
    const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY) || "";
    void openTimeline(fromUrl || stored);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    void openTimeline(tokenInput);
  }

  function closeSession() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setDashboard(null);
    setTokenInput("");
    setError(null);
  }

  if (loading) {
    return (
      <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure mobility timeline">
        <div className={styles.loading} role="status" aria-live="polite">Opening secure timeline…</div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className={`client-portal ${styles.page}`} aria-labelledby="timeline-access-title">
        <section className={styles.accessCard}>
          <div className={styles.topline}>
            <Link href="/my-mobility">← Mobility overview</Link>
            <span>Protected surface</span>
          </div>
          <span className={styles.eyebrow}>Secure timeline</span>
          <h1 id="timeline-access-title">Your timeline stays private until secure access.</h1>
          <p>
            Use the expiring client access link shared by your consultant. No milestones,
            appointments, submissions, agencies, or case status are exposed before access succeeds.
          </p>
          <form onSubmit={submit} className={styles.form}>
            <label htmlFor="timeline-token">Access token</label>
            <input
              id="timeline-token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="gmai_portal_..."
              autoComplete="off"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "timeline-access-error" : undefined}
            />
            <button type="submit" disabled={!tokenInput.trim()}>Open timeline</button>
            {error ? <div id="timeline-access-error" className={styles.error} role="alert">{error}</div> : null}
          </form>
          <div className={styles.boundary}>
            <strong>Client-safe by design.</strong>
            <span>Internal activity, staff notes, review reasoning and operational records are not shown here.</span>
          </div>
        </section>
      </main>
    );
  }

  const steps = journeySteps(dashboard);
  const records = timelineRecords(dashboard);
  const currentStep = steps.find((step) => step.state === "current" || step.state === "attention");
  const datedRecordCount = records.filter((record) => formatDateTime(record.occurredAt)).length;

  return (
    <main className={`client-portal ${styles.page}`} aria-labelledby="timeline-title">
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>My Mobility · Timeline</span>
          <h1 id="timeline-title">Your journey, in order.</h1>
          <p>{dashboard.client_name} · {dashboard.target_country || pretty(dashboard.intent)}</p>
        </div>
        <nav aria-label="Timeline workspace navigation" className={styles.actions}>
          <Link href="/my-mobility">Overview</Link>
          <Link href="/portal">My Case</Link>
          <Link href="/portal/documents">Documents</Link>
          <span aria-current="page">Timeline</span>
          <span aria-disabled="true">Messages pending</span>
          <button type="button" onClick={closeSession}>Close secure session</button>
        </nav>
      </header>

      <section className={styles.summary} aria-label="Timeline status summary">
        <div>
          <span>Current point</span>
          <strong>{currentStep ? currentStep.title : "Not established"}</strong>
        </div>
        <div>
          <span>Visible dated records</span>
          <strong>{datedRecordCount}</strong>
        </div>
        <div>
          <span>Secure access until</span>
          <strong>{formatDate(dashboard.expires_at) || "Not available"}</strong>
        </div>
      </section>

      <section className={styles.timelineLayout}>
        <section className={styles.journey} aria-labelledby="journey-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.eyebrow}>Current journey map</span>
              <h2 id="journey-title">Where your case stands.</h2>
            </div>
            <p>These are current protected milestones. They are not a prediction of timing or outcome.</p>
          </div>

          {steps.length ? (
            <ol className={styles.journeyRail}>
              {steps.map((step) => (
                <li key={step.key} className={styles.journeyStep} data-state={step.state}>
                  <span className={styles.stepMark} aria-hidden="true" />
                  <div>
                    <span className={styles.stateLabel}>{pretty(step.state)}</span>
                    <h3>{step.title}</h3>
                    <p>
                      {step.dueAt ? `Recorded date ${formatDate(step.dueAt) || "not available"}` : "No milestone date is available"}
                      {step.requiresHumanApproval ? " · Human approval required" : ""}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className={styles.empty}>
              <strong>Journey detail is not available.</strong>
              <p>No client-safe milestone record was returned for this secure workspace.</p>
            </div>
          )}
        </section>

        <section className={styles.records} aria-labelledby="records-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.eyebrow}>Dated case records</span>
              <h2 id="records-title">What has been recorded.</h2>
            </div>
            <p>Only client-visible appointments, submissions and external support records appear here.</p>
          </div>

          {records.length ? (
            <ol className={styles.recordList}>
              {records.map((record) => {
                const occurred = formatDateTime(record.occurredAt);
                return (
                  <li key={record.key} className={styles.record}>
                    <div className={styles.recordDate}>
                      {occurred && record.occurredAt ? <time dateTime={record.occurredAt}>{occurred}</time> : <span>Date not available</span>}
                    </div>
                    <div className={styles.recordCopy}>
                      <span>{record.kind}</span>
                      <h3>{record.title}</h3>
                      <p>{record.detail}</p>
                    </div>
                    <span className={styles.status}>{pretty(record.status)}</span>
                  </li>
                );
              })}
            </ol>
          ) : (
            <div className={styles.empty}>
              <strong>No dated case events are visible yet.</strong>
              <p>Future client-visible appointments, submissions or external support records will appear when they are recorded.</p>
            </div>
          )}
        </section>
      </section>

      <aside className={styles.truthBoundary}>
        <strong>Current journey ≠ complete audit history.</strong>
        <span>This timeline reports only protected client-safe records returned by the existing portal API. Missing dates, events and outcomes are never inferred.</span>
      </aside>
    </main>
  );
}

export default function MobilityTimelinePage() {
  return (
    <Suspense
      fallback={
        <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure mobility timeline">
          <div className={styles.loading} role="status" aria-live="polite">Opening secure timeline…</div>
        </main>
      }
    >
      <MobilityTimelineContent />
    </Suspense>
  );
}
