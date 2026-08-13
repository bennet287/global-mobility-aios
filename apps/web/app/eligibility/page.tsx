"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { evaluateEligibility, EligibilityAssessment, getLatestEligibilityAssessment } from "../../lib/api";

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "eligible" || status === "likely_eligible"
      ? "success"
      : status === "needs_documents"
      ? "warning"
      : status === "insufficient_profile"
      ? "info"
      : "error";
  return <span className={`status-badge ${tone}`}>{status.replace(/_/g, " ")}</span>;
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="score-ring">
      <div className="score-value" style={{ "--score": `${pct}%` } as React.CSSProperties}>
        {pct}%
      </div>
      <small>{label}</small>
    </div>
  );
}

function EligibilityContent() {
  const searchParams = useSearchParams();
  const leadId = searchParams.get("lead_id");
  const [assessment, setAssessment] = useState<EligibilityAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const materialRequirements = assessment?.factors.eligibility_requirements || [];

  useEffect(() => {
    if (!leadId) {
      setLoading(false);
      setError("No lead selected. Start an intake first.");
      return;
    }

    const id = leadId;
    async function load() {
      setLoading(true);
      try {
        // Try to reuse an existing assessment; otherwise trigger a new one.
        let data: EligibilityAssessment;
        try {
          data = await getLatestEligibilityAssessment(id);
        } catch {
          data = await evaluateEligibility(id);
        }
        setAssessment(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load eligibility");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [leadId]);

  if (loading) {
    return (
      <div className="eligibility-page">
        <div className="panel">
          <p>Running eligibility assessment...</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="eligibility-page">
        <div className="panel">
          <h1>Eligibility assessment</h1>
          <div className="inline-notice error">{error || "No assessment available."}</div>
          <div className="form-actions">
            <Link className="button primary" href="/intake">
              Start an intake
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="eligibility-page">
      <header className="eligibility-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Eligibility preview</small>
          </div>
        </Link>
      </header>

      <main className="eligibility-main">
        <section className="panel eligibility-panel">
          <h1>Eligibility preview</h1>
          <p className="intake-lead">
            This is an internal rule-based preview for consultant review. It is not a guarantee of
            approval.
          </p>

          <div className="eligibility-summary">
            <ScoreRing score={assessment.overall_score} label="Overall score" />
            <ScoreRing score={assessment.confidence} label="Confidence" />
            <div className="eligibility-status">
              <small>Status</small>
              <StatusBadge status={assessment.status} />
            </div>
          </div>

          {assessment.summary && <p className="eligibility-summary-text">{assessment.summary}</p>}

          <div className="eligibility-grid">
            {materialRequirements.length > 0 && <div className="eligibility-card">
              <h2>Material requirements</h2>
              <ul>
                {materialRequirements.map((requirement) => (
                  <li key={requirement.code}>
                    <strong>{requirement.label}</strong>: {requirement.detail}
                    {requirement.blocking && requirement.status === "missing" ? " Blocking prerequisite." : ""}
                  </li>
                ))}
              </ul>
            </div>}
            <div className="eligibility-card">
              <h2>Required documents</h2>
              <ul>
                {assessment.required_documents.map((doc, i) => (
                  <li key={i}>{doc}</li>
                ))}
              </ul>
            </div>

            <div className="eligibility-card">
              <h2>Plausible pathways</h2>
              <ul>
                {assessment.pathways.map((pathway, i) => (
                  <li key={i}>{pathway}</li>
                ))}
              </ul>
            </div>
          </div>

          {assessment.risks.length > 0 && (
            <div className="eligibility-card risks">
              <h2>Gaps & risks</h2>
              <ul>
                {assessment.risks.map((risk, i) => (
                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="form-actions">
            <Link className="button primary" href={`/profiles?lead_id=${leadId}`}>
              Continue to mobility profile
            </Link>
            <Link className="button secondary" href={`/planning?lead_id=${leadId}`}>
              Open mobility planning
            </Link>
            <Link className="button secondary" href={`/validation?lead_id=${leadId}`}>
              Open external validation
            </Link>
            <Link className="button secondary" href="/intake">
              Start another case
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

export default function EligibilityPage() {
  return (
    <Suspense fallback={<div className="eligibility-page"><div className="panel"><p>Loading...</p></div></div>}>
      <EligibilityContent />
    </Suspense>
  );
}
