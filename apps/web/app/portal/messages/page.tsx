"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ClientPortalDashboard, getClientPortalDashboard } from "../../../lib/api";
import styles from "./MessagesV2.module.css";

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

function MobilityMessagesContent() {
  const searchParams = useSearchParams();
  const [tokenInput, setTokenInput] = useState("");
  const [dashboard, setDashboard] = useState<ClientPortalDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function openMessages(candidate: string) {
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
      window.history.replaceState({}, "", "/portal/messages");
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
    void openMessages(fromUrl || stored);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    void openMessages(tokenInput);
  }

  function closeSession() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setDashboard(null);
    setTokenInput("");
    setError(null);
  }

  if (loading) {
    return (
      <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure mobility messages">
        <div className={styles.loading} role="status" aria-live="polite">Opening secure messages…</div>
      </main>
    );
  }

  if (!dashboard) {
    return (
      <main className={`client-portal ${styles.page}`} aria-labelledby="messages-access-title">
        <section className={styles.accessCard}>
          <div className={styles.topline}>
            <Link href="/my-mobility">← Mobility overview</Link>
            <span>Protected surface</span>
          </div>
          <span className={styles.eyebrow}>Secure messages</span>
          <h1 id="messages-access-title">Communication stays private until secure access.</h1>
          <p>
            Use the expiring client access link shared by your consultant. No case guidance,
            communication state, internal drafts, or personal records are exposed before access succeeds.
          </p>
          <form onSubmit={submit} className={styles.form}>
            <label htmlFor="messages-token">Access token</label>
            <input
              id="messages-token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="gmai_portal_..."
              autoComplete="off"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "messages-access-error" : undefined}
            />
            <button type="submit" disabled={!tokenInput.trim()}>Open messages</button>
            {error ? <div id="messages-access-error" className={styles.error} role="alert">{error}</div> : null}
          </form>
          <div className={styles.boundary}>
            <strong>Client-safe by design.</strong>
            <span>Internal drafts, staff notes, reviewer reasoning, delivery assumptions, and operational communication are not exposed here.</span>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className={`client-portal ${styles.page}`} aria-labelledby="messages-title">
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>My Mobility · Messages</span>
          <h1 id="messages-title">Your communication space.</h1>
          <p>{dashboard.client_name} · {dashboard.target_country || pretty(dashboard.intent)}</p>
        </div>
        <nav aria-label="Messages workspace navigation" className={styles.actions}>
          <Link href="/my-mobility">Overview</Link>
          <Link href="/portal">My Case</Link>
          <Link href="/portal/documents">Documents</Link>
          <Link href="/portal/timeline">Timeline</Link>
          <span aria-current="page">Messages</span>
          <button type="button" onClick={closeSession}>Close secure session</button>
        </nav>
      </header>

      <section className={styles.summary} aria-label="Communication status summary">
        <article>
          <span>Current case guidance</span>
          <strong>{dashboard.next_action || "No client-safe guidance available"}</strong>
        </article>
        <article>
          <span>Guidance updated</span>
          <strong>{formatDateTime(dashboard.updated_at) || "Not available"}</strong>
        </article>
        <article>
          <span>Secure access until</span>
          <strong>{formatDate(dashboard.expires_at) || "Not available"}</strong>
        </article>
      </section>

      <section className={styles.communicationGrid}>
        <article className={styles.guidanceCard} aria-labelledby="messages-guidance-title">
          <span className={styles.eyebrow}>Current guidance</span>
          <h2 id="messages-guidance-title">What your case currently needs.</h2>
          <p className={styles.guidance}>{dashboard.next_action || "No client-safe next action is currently available."}</p>
          <div className={styles.note}>
            <strong>Guidance is not a delivered message.</strong>
            <span>This comes from the protected portal case summary and is shown separately from communication history.</span>
          </div>
        </article>

        <article className={styles.contactCard} aria-labelledby="messages-contact-title">
          <span className={styles.eyebrow}>Contact your mobility team</span>
          <h2 id="messages-contact-title">Use your established secure channel.</h2>
          <p>
            This surface does not invent an email address, phone number, recipient, or delivery route.
            Use the contact method already provided by your mobility consultant or organization.
          </p>
          <div className={styles.contactState}>
            <span>In-app reply</span>
            <strong>Unavailable</strong>
            <small>No accepted client-send contract exists on this surface yet.</small>
          </div>
        </article>
      </section>

      <section className={styles.history} aria-labelledby="message-history-title">
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.eyebrow}>Communication history</span>
            <h2 id="message-history-title">Delivered-message history is unavailable.</h2>
          </div>
          <p>AIOS does not currently expose a client-safe delivered-message record through the protected portal contract.</p>
        </div>
        <div className={styles.unavailableState} role="status">
          <span className={styles.unavailableMark} aria-hidden="true">—</span>
          <div>
            <strong>No delivered-message claim is made.</strong>
            <p>Internal drafts, reviewed drafts, scheduled follow-ups, and operational communication are not relabeled as sent or delivered messages.</p>
          </div>
        </div>
      </section>

      <aside className={styles.truthBoundary}>
        <strong>Draft ≠ sent · reviewed ≠ delivered.</strong>
        <span>This workspace verifies secure client access and presents current client-safe guidance only. Message history and replies remain explicitly unavailable until a governed delivered-message and client-send contract exists.</span>
      </aside>
    </main>
  );
}

export default function MobilityMessagesPage() {
  return (
    <Suspense
      fallback={
        <main className={`client-portal ${styles.page}`} aria-busy="true" aria-label="Secure mobility messages">
          <div className={styles.loading} role="status" aria-live="polite">Opening secure messages…</div>
        </main>
      }
    >
      <MobilityMessagesContent />
    </Suspense>
  );
}
