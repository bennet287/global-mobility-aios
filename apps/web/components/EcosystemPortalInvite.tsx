"use client";

import { useState } from "react";
import {
  EcosystemPortalGrantIssued,
  issueEcosystemPortalGrant,
} from "../lib/api";


export function EcosystemPortalInvite({
  accountId,
  accountName,
}: {
  accountId: string;
  accountName: string;
}) {
  const [audience, setAudience] = useState<"employer" | "partner">("employer");
  const [issued, setIssued] = useState<EcosystemPortalGrantIssued | null>(null);
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
      setIssued(await issueEcosystemPortalGrant(
        accountId,
        audience,
        `${accountName} ${audience} workspace`,
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create tenant access");
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
    <section className="ecosystem-invite">
      <div>
        <span className="section-kicker">External workspace</span>
        <h3>Employer & partner portal</h3>
        <p>
          Issue a 30-day link scoped only to {accountName}. It cannot access another
          corporate account or any internal operator workspace.
        </p>
      </div>
      <div className="ecosystem-invite-actions">
        {!issued ? (
          <>
            <label>
              Portal audience
              <select value={audience} onChange={(event) => setAudience(event.target.value as typeof audience)}>
                <option value="employer">Employer mobility team</option>
                <option value="partner">Authorized mobility partner</option>
              </select>
            </label>
            <button className="button primary" onClick={createAccess} disabled={loading}>
              {loading ? "Creating tenant link..." : "Create tenant portal link"}
            </button>
          </>
        ) : (
          <>
            <div className="portal-invite-link" title={portalUrl}>{portalUrl}</div>
            <button className="button primary" onClick={copyLink}>
              {copied ? "Copied" : "Copy secure link"}
            </button>
          </>
        )}
        {error ? <div className="inline-notice error">{error}</div> : null}
      </div>
    </section>
  );
}
