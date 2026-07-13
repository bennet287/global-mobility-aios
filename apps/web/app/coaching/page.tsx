"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CoachReview,
  generateTrainingCases,
  getHealthStatus,
  HealthStatus,
  listAllCoachReviews,
  listTrainingCases,
  runTrainingCase,
  submitCoachFeedback,
  TrainingCase,
} from "../../lib/api";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { SectionTitle } from "../../components/SectionTitle";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";

const TABS = ["reviews", "training"] as const;
type Tab = (typeof TABS)[number];

function safeJson(value: string | null) {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function safeJsonObject(value: string | null) {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

export default function CoachingPage() {
  const [tab, setTab] = useState<Tab>("reviews");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [reviews, setReviews] = useState<CoachReview[]>([]);
  const [cases, setCases] = useState<TrainingCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [runningCaseId, setRunningCaseId] = useState<string | null>(null);
  const [feedbackReviewId, setFeedbackReviewId] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, reviewList, caseList] = await Promise.all([
        getHealthStatus(),
        listAllCoachReviews(),
        listTrainingCases({ limit: 50 }),
      ]);
      setHealth(healthData.data);
      setReviews(reviewList);
      setCases(caseList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load coaching data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await generateTrainingCases({ count: 5 });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate cases");
    } finally {
      setGenerating(false);
    }
  };

  const handleRunCase = async (caseId: string) => {
    setRunningCaseId(caseId);
    setError(null);
    try {
      await runTrainingCase(caseId);
      await load();
      setTab("reviews");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run training case");
    } finally {
      setRunningCaseId(null);
    }
  };

  const handleSubmitFeedback = async (reviewId: string, decision: "approved" | "overridden") => {
    setError(null);
    try {
      await submitCoachFeedback(reviewId, {
        operator_feedback: feedbackText,
        override_decision: decision,
      });
      setFeedbackReviewId(null);
      setFeedbackText("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit feedback");
    }
  };

  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Agent Coaching" kicker="Quality & training" loadStatus={loadStatus} onRefresh={load} />

      <div className="page-pad">
        {error && <InlineNotice label="Error" detail={error} tone="bad" />}

        <div className="tab-bar">
          {TABS.map((t) => (
            <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
              {t === "reviews" ? "Coach Reviews" : "Training Cases"}
            </button>
          ))}
        </div>

        {tab === "reviews" && (
          <section className="coaching-section">
            <SectionTitle label="Reviews" title="Recent coach audits" detail={`${reviews.length} total`} />
            {reviews.length === 0 ? (
              <EmptyState title="No reviews" detail="No coach reviews yet. Run a training case to create one." />
            ) : (
              <div className="coaching-list">
                {reviews.map((review) => (
                  <article className="panel coaching-card" key={review.id}>
                    <div className="coaching-card-header">
                      <div>
                        <strong>{review.target_agent_name}</strong>
                        <span className="coach-meta">{review.coach_agent_name}</span>
                      </div>
                      <span className={`status-badge ${review.conclusion_valid ? "success" : "warning"}`}>
                        {review.conclusion_valid ? "Valid" : "Needs review"}
                      </span>
                    </div>
                    <p className="coaching-summary">{review.corrected_summary}</p>
                    <div className="coaching-details">
                      {safeJson(review.missing_facts_json).length > 0 && (
                        <div>
                          <small>Missing facts</small>
                          <ul>
                            {safeJson(review.missing_facts_json).map((fact, i) => (
                              <li key={i}>{fact}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {safeJson(review.source_issues_json).length > 0 && (
                        <div>
                          <small>Source issues</small>
                          <ul>
                            {safeJson(review.source_issues_json).map((issue, i) => (
                              <li key={i}>{issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    <div className="coaching-card-footer">
                      <span className="coach-meta">Confidence: {review.confidence}</span>
                      <span className="coach-meta">Status: {review.status}</span>
                      {feedbackReviewId === review.id ? (
                        <div className="feedback-form">
                          <textarea
                            placeholder="Add operator feedback..."
                            value={feedbackText}
                            onChange={(e) => setFeedbackText(e.target.value)}
                            rows={2}
                          />
                          <div className="feedback-actions">
                            <button
                              className="button primary small"
                              onClick={() => handleSubmitFeedback(review.id, "approved")}
                            >
                              Approve
                            </button>
                            <button
                              className="button secondary small"
                              onClick={() => handleSubmitFeedback(review.id, "overridden")}
                            >
                              Override
                            </button>
                            <button className="button ghost small" onClick={() => setFeedbackReviewId(null)}>
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button className="button secondary small" onClick={() => setFeedbackReviewId(review.id)}>
                          Review
                        </button>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === "training" && (
          <section className="coaching-section">
            <div className="section-header-row">
              <SectionTitle label="Training" title="Synthetic cases" detail={`${cases.length} cases`} />
              <button className="button primary" onClick={handleGenerate} disabled={generating}>
                {generating ? "Generating..." : "Generate 5 cases"}
              </button>
            </div>
            {cases.length === 0 ? (
              <EmptyState title="No cases" detail="No training cases yet. Generate some to start drills." />
            ) : (
              <div className="coaching-list">
                {cases.map((c) => {
                  const scenario = safeJsonObject(c.scenario_json);
                  const expected = safeJsonObject(c.expected_outcome_json);
                  return (
                    <article className="panel coaching-card" key={c.id}>
                      <div className="coaching-card-header">
                        <div>
                          <strong>{c.title}</strong>
                          <span className="coach-meta">{c.country} · {c.profession} · run {c.times_run} times</span>
                        </div>
                        <button
                          className="button secondary small"
                          onClick={() => handleRunCase(c.id)}
                          disabled={runningCaseId === c.id}
                        >
                          {runningCaseId === c.id ? "Running..." : "Run drill"}
                        </button>
                      </div>
                      {scenario && (
                        <div className="coaching-details">
                          <div>
                            <small>Scenario</small>
                            <pre>{JSON.stringify(scenario, null, 2)}</pre>
                          </div>
                          {expected && (
                            <div>
                              <small>Expected outcome</small>
                              <pre>{JSON.stringify(expected, null, 2)}</pre>
                            </div>
                          )}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}
      </div>
    </WorkspaceShell>
  );
}
