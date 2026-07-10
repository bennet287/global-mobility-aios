import { TruthClaim } from "../lib/api";
import { StatusBadge } from "./StatusBadge";

export function TruthClaimCard({ claim }: { claim: TruthClaim }) {
  const confidence = Math.round((claim.confidence || 0) * 100);
  return (
    <article className="claim-card">
      <div className="claim-topline">
        <StatusBadge value={claim.verdict} />
        <span>
          {claim.country || "Global"} · {claim.domain}
        </span>
      </div>
      <strong>{claim.claim}</strong>
      <p>{claim.explanation || claim.recommended_next_step || "No explanation recorded."}</p>
      <div className="confidence-row">
        <span>Confidence</span>
        <div className="confidence-track">
          <i style={{ width: `${Math.min(100, Math.max(0, confidence))}%` }} />
        </div>
        <strong>{confidence}%</strong>
      </div>
    </article>
  );
}
