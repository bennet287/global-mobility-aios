"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ClientPortalDashboard, getClientPortalDashboard } from "../../../lib/api";
import styles from "./DocumentsV2.module.css";

const TOKEN_STORAGE_KEY = "gmai-client-portal-token";
const DEVICE_STORAGE_KEY = "gmai-client-portal-device";

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

function isDeviceMismatchError(errorText: string): boolean {
  try {
    const parsed = JSON.parse(errorText) as { action?: string; detail?: { action?: string } };
    return parsed.action === "request_new_grant" || parsed.detail?.action === "request_new_grant";
  } catch {
    return errorText.includes("request_new_grant");
  }
}

function MobilityDocumentsContent() {
  const searchParams = useSearchParams();
  const [tokenInput, setTokenInput] = useState("");
  const [dashboard, setDashboard] = useState<ClientPortalDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function openDocuments(candidate: string) {
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
      window.history.replaceState({}, "", "/portal/documents");
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
    void openDocuments(fromUrl || stored);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    void openDocuments(tokenInput);
  }

  function closeSession() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setDashboard(null);
    setTokenInput("");
    setError(null);
  }

  if (loading) {
    return (
      <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure document room">
        <div className={styles.loading} role="status" aria-live="polite">Opening secure documents…</div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className={`client-portal ${styles.page}`} aria-labelledby="documents-access-title">
        <section className={styles.accessCard}>
          <div className={styles.topline}>
            <Link href="/my-mobility">← Mobility overview</Link>
            <span>Protected surface</span>
          </div>
          <span className={styles.eyebrow}>Secure documents</span>
          <h1 id="documents-access-title">Your document room stays private until secure access.</h1>
          <p>
            Use the expiring client access link shared by your consultant. No document names,
            statuses, requests, or evidence details are exposed before that access succeeds.
          </p>
          <form onSubmit={submit} className={styles.form}>
            <label htmlFor="documents-token">Access token</label>
            <input
              id="documents-token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="gmai_portal_..."
              autoComplete="off"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "documents-access-error" : undefined}
            />
            <button type="submit" disabled={!tokenInput.trim()}>Open document room</button>
            {error ? <div id="documents-access-error" className={styles.error} role="alert">{error}</div> : null}
          </form>
          <div className={styles.boundary}>
            <strong>Client-safe by design.</strong>
            <span>Internal storage references, reviewer internals, and professional-only evidence analysis are not shown here.</span>
          </div>
        </section>
      </main>
    );
  }

  const verifiedCount = dashboard.documents.filter((document) =>
    ["verified", "approved", "accepted"].includes(document.status.toLowerCase()),
  ).length;

  return (
    <main className={`client-portal ${styles.page}`} aria-labelledby="documents-title">
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>My Mobility · Documents</span>
          <h1 id="documents-title">Your document room.</h1>
          <p>{dashboard.client_name} · {dashboard.target_country || pretty(dashboard.intent)}</p>
        </div>
        <nav aria-label="Document workspace navigation" className={styles.actions}>
          <Link href="/my-mobility">Overview</Link>
          <Link href="/portal">My Case</Link>
          <Link href="/portal/timeline">Timeline</Link>
          <Link href="/portal/messages">Messages</Link>
          <button type="button" onClick={closeSession}>Close secure session</button>
        </nav>
      </header>

      <section className={styles.summary} aria-label="Document status summary">
        <article><span>Visible documents</span><strong>{dashboard.documents.length}</strong></article>
        <article><span>Verified or accepted</span><strong>{verifiedCount}</strong></article>
        <article><span>Secure access until</span><strong>{formatDate(dashboard.expires_at) || "Not available"}</strong></article>
      </section>

      <section className={styles.documentSection} aria-labelledby="documents-list-title">
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.eyebrow}>Client-safe evidence status</span>
            <h2 id="documents-list-title">What your team has made visible.</h2>
          </div>
          <p>Status here reflects the protected client portal record. It does not imply authority acceptance.</p>
        </div>

        {dashboard.documents.length ? (
          <div className={styles.list}>
            {dashboard.documents.map((document) => {
              const uploaded = formatDate(document.uploaded_at);
              const expiry = formatDate(document.expiry_date);
              return (
                <article key={document.id} className={styles.documentRow}>
                  <div className={styles.documentMark} aria-hidden="true">D</div>
                  <div className={styles.documentCopy}>
                    <span>{pretty(document.document_type)}</span>
                    <strong>{document.filename}</strong>
                    <small>
                      {uploaded ? `Received ${uploaded}` : "Received date not available"}
                      {expiry ? ` · Expires ${expiry}` : ""}
                    </small>
                  </div>
                  <span className={styles.status}>{pretty(document.status)}</span>
                </article>
              );
            })}
          </div>
        ) : (
          <div className={styles.empty}>
            <strong>No documents are visible yet.</strong>
            <p>Requested or reviewed client-safe documents will appear here when your team makes them available.</p>
          </div>
        )}
      </section>

      <aside className={styles.truthBoundary}>
        <strong>Document status ≠ authority outcome.</strong>
        <span>This workspace reports only the protected client-safe record returned by the existing portal API.</span>
      </aside>
    </main>
  );
}

export default function MobilityDocumentsPage() {
  return (
    <Suspense
      fallback={
        <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure document room">
          <div className={styles.loading} role="status" aria-live="polite">Opening secure documents…</div>
        </main>
      }
    >
      <MobilityDocumentsContent />
    </Suspense>
  );
}
