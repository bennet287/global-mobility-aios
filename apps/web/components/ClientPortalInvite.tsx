"use client";

import { useState } from "react";
import { ClientPortalGrantIssued, issueClientPortalGrant } from "../lib/api";


export function ClientPortalInvite({ leadId }: { leadId: string }) {
  const [issued, setIssued] = useState<ClientPortalGrantIssued | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const portalUrl = issued && typeof window !== "undefined"
    ? `${window.location.origin}${issued.portal_path}`
    : "";

  async function createAccess() {
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      setIssued(await issueClientPortalGrant(leadId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create portal access");
    } finally {
      setLoading(false);
    }
  }

  async function copyLink() {
    if (!portalUrl) return;
    await navigator.clipboard.writeText(portalUrl);
    setCopied(true);
  }

  return (
    <section className="portal-invite-panel">
      <div>
        <span className="section-kicker">Client channel</span>
        <h2>Secure client portal</h2>
        <p>
          Create a lead-scoped link that expires in 30 days. The raw token is shown once
          and every access is audited.
        </p>
      </div>
      <div className="portal-invite-actions">
        {!issued ? (
          <button className="button primary" onClick={createAccess} disabled={loading}>
            {loading ? "Creating secure link..." : "Create portal link"}
          </button>
        ) : (
          <>
            <div className="portal-invite-link" title={portalUrl}>{portalUrl}</div>
            <button className="button primary" onClick={copyLink}>
              {copied ? "Copied" : "Copy client link"}
            </button>
          </>
        )}
        {error && <div className="inline-notice error">{error}</div>}
      </div>
    </section>
  );
}
