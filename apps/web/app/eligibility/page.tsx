"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { InlineNotice } from "../../components/InlineNotice";
import { Skeleton } from "../../components/Skeleton";
import { StatusBadge } from "../../components/StatusBadge";
import { TechnicalDisclosure } from "../../components/TechnicalDisclosure";
import { evaluateEligibility, EligibilityAssessment, getLatestEligibilityAssessment } from "../../lib/api";

function AssessmentSignal({ score, label }: { score: number; label: string }) {
  const percentage = Math.round(score * 100);
  return (
    <div className="assessment-signal">
      <span>{label}</span>
      <strong>{percentage}%</strong>
      <small>Internal assessment signal</small>
    </div>
  );
}

type PresentedRisk = {
  plainLanguage: string;
  rawValue: string;
  certificationPending: boolean;
};

const riskLanguageByLabel: Record<string, string> = {
  "Binding Austrian job offer": "Binding Austrian job offer is missing and blocks progress.",
  "Employer declaration": "Employer declaration has not been provided.",
  "Salary/remuneration evidence": "Salary or remuneration evidence has not been provided.",
  "Employment province": "Employment province is not known yet.",
  "Occupation-list applicability": "Occupation-list applicability still needs review.",
  "Occupation qualification mapping": "Qualification mapping still needs review.",
  "Qualification recognition/equivalence": "Qualification recognition or equivalence has not been established yet.",
  "Qualification evidence": "Qualification evidence has not been provided.",
  "Work-experience evidence": "Work-experience evidence has not been provided.",
  "Language certificate": "A language certificate has not been provided.",
  "Travel document": "A travel document has not been provided.",
  "Health insurance evidence": "Health insurance evidence has not been provided.",
  "National occupation-source certification": "National occupation evidence is awaiting independent certification.",
  "Regional occupation-source certification": "Regional occupation evidence is awaiting independent certification.",
};

function presentEligibilityRisk(rawValue: string): PresentedRisk {
  const match = rawValue.match(/^Pathway evidence gap:\s+([A-Z_]+) GAP\s+—\s+(.+):\s+([A-Z_]+)$/);
  if (!match) return { plainLanguage: rawValue, rawValue, certificationPending: false };

  const [, category, label, status] = match;
  const fallbackByStatus: Record<string, string> = {
    BLOCKING: `${label} is missing and blocks progress.`,
    NOT_PROVIDED: `${label} has not been provided.`,
    UNKNOWN: `${label} is not known yet.`,
    UNRESOLVED: `${label} still needs review.`,
    PENDING_REVIEW: `${label} is awaiting independent review.`,
  };

  return {
    plainLanguage: riskLanguageByLabel[label] || fallbackByStatus[status] || `${label} requires review.`,
    rawValue,
    certificationPending: category === "CERTIFICATION" && status === "PENDING_REVIEW",
  };
}

function EligibilityContent() {
  const searchParams = useSearchParams();
  const leadId = searchParams.get("lead_id");
  const [assessment, setAssessment] = useState<EligibilityAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

    void load();
  }, [leadId]);

  if (loading) {
    return (
      <div className="eligibility-page">
        <div className="panel eligibility-loading" role="status" aria-live="polite">
          <Skeleton className="skeleton-title" />
          <Skeleton className="skeleton-paragraph" />
          <p>Running eligibility assessment…</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="eligibility-page">
        <main className="eligibility-main">
          <section className="panel eligibility-panel">
            <h1>Eligibility assessment</h1>
            <InlineNotice label="Eligibility assessment unavailable" detail={error || "No assessment is available."} tone="bad" />
            <div className="form-actions">
              <Link className="button primary" href="/intake">Start an intake</Link>
            </div>
          </section>
        </main>
      </div>
    );
  }

  const materialRequirements = assessment.factors.eligibility_requirements || [];
  const blockingRequirements = materialRequirements.filter(
    (requirement) => requirement.blocking && requirement.status === "missing",
  );
  const supportingRequirements = materialRequirements.filter(
    (requirement) => !requirement.blocking || requirement.status !== "missing",
  );
  const presentedRisks = assessment.risks.map(presentEligibilityRisk);

  return (
    <div className="eligibility-page">
      <a className="skip-link" href="#eligibility-content">Skip to assessment</a>
      <header className="eligibility-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Eligibility preview</small>
          </div>
        </Link>
      </header>

      <main id="eligibility-content" className="eligibility-main" tabIndex={-1}>
        <section className="panel eligibility-panel">
          <div className="decision-context">
            <span className="hierarchy-label">Decision context</span>
            <h1>Eligibility preview</h1>
            <p className="intake-lead">
              This internal rule-based assessment supports consultant review. It is not an eligibility
              decision and does not predict immigration approval.
            </p>
            <StatusBadge value={assessment.status} />
          </div>

          <div className="assessment-signals" aria-label="Internal assessment signals">
            <AssessmentSignal score={assessment.overall_score} label="Assessment coverage" />
            <AssessmentSignal score={assessment.confidence} label="Data confidence" />
            <p>These percentages summarize internal assessment inputs. They are not the probability of visa or permit approval.</p>
          </div>

          {assessment.summary ? <p className="eligibility-summary-text">{assessment.summary}</p> : null}

          <section className="decision-section decision-blockers" aria-labelledby="eligibility-blockers">
            <span className="hierarchy-label">Blockers</span>
            <h2 id="eligibility-blockers">What prevents this pathway from proceeding</h2>
            {blockingRequirements.length ? (
              <div className="blocker-list">
                <ul>
                  {blockingRequirements.map((requirement) => (
                    <li key={requirement.code}>
                      <strong>{requirement.label}</strong>
                      <span>{requirement.detail}</span>
                      <b>Required and currently missing</b>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <InlineNotice
                label="No explicit blocking requirement was returned"
                detail="A consultant must still review the assessment, evidence gaps, and pathway conditions."
                tone="warn"
              />
            )}
          </section>

          <section className="decision-section next-action-section" aria-labelledby="eligibility-actions">
            <span className="hierarchy-label">Next actions</span>
            <h2 id="eligibility-actions">Move the case forward</h2>
            <p>
              {blockingRequirements.length
                ? `Resolve ${blockingRequirements[0].label.toLowerCase()} first, then update the profile and run a fresh assessment.`
                : "Review the profile and supporting evidence before relying on this preview."}
            </p>
            <div className="form-actions">
              <Link className="button primary" href={`/profiles?lead_id=${leadId}`}>Update profile and evidence</Link>
              <Link className="button secondary" href={`/planning?lead_id=${leadId}`}>Review pathway plan</Link>
              <Link className="button secondary" href={`/validation?lead_id=${leadId}`}>Open validation record</Link>
            </div>
          </section>

          <section className="decision-section" aria-labelledby="eligibility-evidence">
            <span className="hierarchy-label">Supporting evidence</span>
            <h2 id="eligibility-evidence">Requirements, documents, and assessed pathways</h2>
            {presentedRisks.length ? (
              <div className="eligibility-card eligibility-additional-gaps">
                <h3>Additional gaps and review needs</h3>
                <ul>
                  {presentedRisks.map((risk, index) => (
                    <li className={risk.certificationPending ? "certification-warning" : undefined} key={index}>
                      {risk.certificationPending ? <strong>Independent certification pending</strong> : null}
                      <span>{risk.plainLanguage}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="eligibility-grid supporting-evidence-grid">
              {supportingRequirements.length ? (
                <div className="eligibility-card">
                  <h3>Other material requirements</h3>
                  <ul>{supportingRequirements.map((requirement) => <li key={requirement.code}><strong>{requirement.label}</strong>: {requirement.detail}</li>)}</ul>
                </div>
              ) : null}
              <div className="eligibility-card">
                <h3>Required documents</h3>
                <ul>{assessment.required_documents.map((document, index) => <li key={index}>{document}</li>)}</ul>
              </div>
              <div className="eligibility-card">
                <h3>Assessed pathways</h3>
                <ul>{assessment.pathways.map((pathway, index) => <li key={index}>{pathway}</li>)}</ul>
              </div>
            </div>
          </section>

          <TechnicalDisclosure detail="Assessment identifiers and version metadata">
            <dl className="technical-metadata-list">
              <div><dt>Assessment ID</dt><dd><code>{assessment.id}</code></dd></div>
              <div><dt>Lead ID</dt><dd><code>{assessment.lead_id}</code></dd></div>
              <div><dt>Preview version</dt><dd><code>{assessment.factors.eligibility_preview_version || "not recorded"}</code></dd></div>
              <div><dt>Updated</dt><dd>{new Date(assessment.updated_at).toLocaleString()}</dd></div>
            </dl>
            {presentedRisks.length ? (
              <div className="technical-risk-values">
                <h3>Raw assessment states</h3>
                <ul>{presentedRisks.map((risk, index) => <li key={index}><code>{risk.rawValue}</code></li>)}</ul>
              </div>
            ) : null}
          </TechnicalDisclosure>

          <Link className="text-link eligibility-link" href="/intake">Start a different intake</Link>
        </section>
      </main>
    </div>
  );
}

export default function EligibilityPage() {
  return (
    <Suspense fallback={<div className="eligibility-page"><div className="panel eligibility-loading" role="status"><Skeleton className="skeleton-title" /><p>Loading assessment…</p></div></div>}>
      <EligibilityContent />
    </Suspense>
  );
}
