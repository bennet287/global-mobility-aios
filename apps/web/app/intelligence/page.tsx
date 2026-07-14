"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  generateRegulatoryClassificationProposal,
  getHealthStatus,
  getRegulatoryKnowledgeGraph,
  getRegulatoryDashboard,
  HealthStatus,
  listJurisdictions,
  listRegulatoryClassificationProposals,
  listRegulatoryChanges,
  listSourceSnapshots,
  listVerifiedRules,
  onboardRegulatorySource,
  publishRegulatoryChange,
  RegulatoryChange,
  RegulatoryClassificationProposal,
  RegulatoryDashboard,
  RegulatoryKnowledgeGraph,
  retireVerifiedRule,
  reviewRegulatoryClassificationProposal,
  reviewRegulatoryChange,
  runSourceMonitor,
  syncRegulatoryKnowledgeGraph,
  SourceSnapshotView,
  VerifiedRule,
  Jurisdiction,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const TABS = ["overview", "coverage", "changes", "graph", "rules", "evidence", "onboarding"] as const;
type Tab = (typeof TABS)[number];

const INITIAL_ONBOARDING = {
  jurisdictionCode: "",
  jurisdictionName: "",
  jurisdictionType: "country" as "country" | "territory" | "autonomous_jurisdiction",
  region: "",
  authorityName: "",
  authorityType: "immigration_authority",
  authorityWebsiteUrl: "",
  authorityDomains: "visa",
  sourceName: "",
  sourceUrl: "",
  sourceDomain: "visa",
  sourceType: "official" as "government" | "official" | "official_portal" | "official_agency" | "gazette",
  scheduleMinutes: "1440",
  fetchMethod: "http" as "http" | "browser" | "api" | "manual",
  allowedDomains: "",
  maxRedirects: "3",
  parserProfile: "generic" as "generic" | "gazette_html_v1" | "structured_program_catalog_v1",
  parserConfig: "{}",
};

function formatDate(value: string | null | undefined) {
  if (!value) return "Never";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function diffLines(value: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed?.unified_diff) ? parsed.unified_diff : [];
  } catch {
    return [];
  }
}

function CoverageMeter({ value }: { value: number }) {
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="coverage-meter" aria-label={`${bounded}%`}>
      <span style={{ width: `${bounded}%` }} />
      <strong>{bounded.toFixed(1)}%</strong>
    </div>
  );
}

export default function IntelligencePage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [dashboard, setDashboard] = useState<RegulatoryDashboard | null>(null);
  const [changes, setChanges] = useState<RegulatoryChange[]>([]);
  const [classificationProposals, setClassificationProposals] = useState<RegulatoryClassificationProposal[]>([]);
  const [knowledgeGraph, setKnowledgeGraph] = useState<RegulatoryKnowledgeGraph | null>(null);
  const [rules, setRules] = useState<VerifiedRule[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshotView[]>([]);
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [proposalNotes, setProposalNotes] = useState("");
  const [ruleKey, setRuleKey] = useState("");
  const [ruleStatement, setRuleStatement] = useState("");
  const [supersedesRuleId, setSupersedesRuleId] = useState("");
  const [retireTarget, setRetireTarget] = useState<string | null>(null);
  const [retireReason, setRetireReason] = useState("");
  const [onboarding, setOnboarding] = useState(INITIAL_ONBOARDING);
  const [busy, setBusy] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthResult, dashboardData, changeData, proposalData, graphData, ruleData, snapshotData, jurisdictionData] = await Promise.all([
        getHealthStatus(),
        getRegulatoryDashboard(),
        listRegulatoryChanges(),
        listRegulatoryClassificationProposals({ limit: 500 }),
        getRegulatoryKnowledgeGraph({ active: true, limit: 1000 }),
        listVerifiedRules({ limit: 300 }),
        listSourceSnapshots({ limit: 100 }),
        listJurisdictions(),
      ]);
      setHealth(healthResult.data);
      setDashboard(dashboardData);
      setChanges(changeData.changes);
      setClassificationProposals(proposalData.classification_proposals);
      setKnowledgeGraph(graphData);
      setRules(ruleData.verified_rules);
      setSnapshots(snapshotData.snapshots);
      setJurisdictions(jurisdictionData.jurisdictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load regulatory intelligence");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedChange = useMemo(
    () => changes.find((change) => change.id === selectedChangeId) || null,
    [changes, selectedChangeId]
  );
  const jurisdictionNames = useMemo(
    () => new Map(jurisdictions.map((item) => [item.id, item.name])),
    [jurisdictions]
  );
  const replacementCandidates = useMemo(
    () => rules.filter(
      (rule) => rule.active &&
        rule.jurisdiction_id === selectedChange?.jurisdiction_id &&
        rule.domain === selectedChange?.domain
    ),
    [rules, selectedChange]
  );
  const selectedProposals = useMemo(
    () => classificationProposals.filter((proposal) => proposal.regulatory_change_id === selectedChangeId),
    [classificationProposals, selectedChangeId]
  );
  const hasAcceptedClassification = selectedProposals.some((proposal) => proposal.status === "accepted");
  const graphNodeMap = useMemo(
    () => new Map((knowledgeGraph?.nodes || []).map((node) => [node.id, node])),
    [knowledgeGraph]
  );

  function updateOnboarding(field: keyof typeof INITIAL_ONBOARDING, value: string) {
    setOnboarding((current) => ({ ...current, [field]: value }) as typeof INITIAL_ONBOARDING);
  }

  async function handleMonitorRun(monitorId: string) {
    setBusy(`monitor-${monitorId}`);
    setError(null);
    try {
      await runSourceMonitor(monitorId);
      setMessage("Source retrieval queued. Refresh shortly to see the resulting run.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not queue source retrieval");
    } finally {
      setBusy(null);
    }
  }

  async function handleReview(decision: "approved" | "rejected") {
    if (!selectedChange || !reviewNotes.trim()) return;
    setBusy(`review-${selectedChange.id}`);
    setError(null);
    try {
      const result = await reviewRegulatoryChange(selectedChange.id, {
        decision,
        reviewer: "frontend-reviewer",
        notes: reviewNotes.trim(),
      });
      setMessage(`Regulatory change ${decision}.`);
      setReviewNotes("");
      setChanges((current) => current.map((item) => item.id === result.change.id ? result.change : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not review regulatory change");
    } finally {
      setBusy(null);
    }
  }

  async function handleGenerateClassification(useModel: boolean) {
    if (!selectedChange) return;
    setBusy(`classify-${selectedChange.id}`);
    setError(null);
    try {
      const result = await generateRegulatoryClassificationProposal(selectedChange.id, {
        use_model: useModel,
        actor: "frontend-reviewer",
      });
      setMessage(result.classification_proposal.method === "model_assisted"
        ? "Model-assisted classification proposal created for human review."
        : "Deterministic classification proposal created; inspect the fallback reason and evidence.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate classification proposal");
    } finally {
      setBusy(null);
    }
  }

  async function handleClassificationReview(
    proposalId: string,
    decision: "accepted" | "rejected"
  ) {
    if (!proposalNotes.trim()) return;
    setBusy(`classification-review-${proposalId}`);
    setError(null);
    try {
      await reviewRegulatoryClassificationProposal(proposalId, {
        decision,
        reviewer: "frontend-reviewer",
        notes: proposalNotes.trim(),
      });
      setProposalNotes("");
      setMessage(`Classification proposal ${decision}. The regulatory change still requires separate review.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not review classification proposal");
    } finally {
      setBusy(null);
    }
  }

  async function handleGraphSync() {
    setBusy("knowledge-graph-sync");
    setError(null);
    try {
      const result = await syncRegulatoryKnowledgeGraph({ actor: "frontend-reviewer" });
      setMessage(`Knowledge graph synchronized from ${result.sync.projected_rules} human-published rules.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not synchronize the regulatory knowledge graph");
    } finally {
      setBusy(null);
    }
  }

  async function handlePublish() {
    if (!selectedChange || !ruleKey.trim() || !ruleStatement.trim()) return;
    setBusy(`publish-${selectedChange.id}`);
    setError(null);
    try {
      await publishRegulatoryChange(selectedChange.id, {
        rule_key: ruleKey.trim(),
        statement: ruleStatement.trim(),
        reviewer: "frontend-reviewer",
        confidence: 1,
        supersedes_rule_id: supersedesRuleId || undefined,
      });
      setMessage("Verified rule published with its evidence and review links.");
      setRuleKey("");
      setRuleStatement("");
      setSupersedesRuleId("");
      setSelectedChangeId(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not publish verified rule");
    } finally {
      setBusy(null);
    }
  }

  async function handleRetire(ruleId: string) {
    if (!retireReason.trim()) return;
    setBusy(`retire-${ruleId}`);
    setError(null);
    try {
      await retireVerifiedRule(ruleId, {
        reviewer: "frontend-reviewer",
        reason: retireReason.trim(),
      });
      setRetireTarget(null);
      setRetireReason("");
      setMessage("Verified rule retired and retained in history.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not retire verified rule");
    } finally {
      setBusy(null);
    }
  }

  async function handleOnboard() {
    const required = [
      onboarding.jurisdictionCode,
      onboarding.jurisdictionName,
      onboarding.authorityName,
      onboarding.sourceName,
      onboarding.sourceUrl,
    ];
    if (required.some((value) => !value.trim())) return;
    setBusy("onboarding");
    setError(null);
    try {
      let parserConfig: Record<string, unknown> = {};
      try {
        const parsedConfig = JSON.parse(onboarding.parserConfig || "{}");
        if (!parsedConfig || Array.isArray(parsedConfig) || typeof parsedConfig !== "object") {
          throw new Error("Parser configuration must be a JSON object.");
        }
        parserConfig = parsedConfig;
      } catch (err) {
        throw new Error(err instanceof Error ? err.message : "Parser configuration is not valid JSON.");
      }
      const result = await onboardRegulatorySource({
        jurisdiction_code: onboarding.jurisdictionCode.trim(),
        jurisdiction_name: onboarding.jurisdictionName.trim(),
        jurisdiction_type: onboarding.jurisdictionType,
        region: onboarding.region.trim() || undefined,
        authority_name: onboarding.authorityName.trim(),
        authority_type: onboarding.authorityType.trim(),
        authority_website_url: onboarding.authorityWebsiteUrl.trim() || undefined,
        authority_domains: onboarding.authorityDomains.split(",").map((item) => item.trim()).filter(Boolean),
        source_name: onboarding.sourceName.trim(),
        source_url: onboarding.sourceUrl.trim(),
        source_domain: onboarding.sourceDomain.trim(),
        source_type: onboarding.sourceType,
        schedule_minutes: Number(onboarding.scheduleMinutes),
        fetch_method: onboarding.fetchMethod,
        allowed_domains: onboarding.allowedDomains.split(",").map((item) => item.trim()).filter(Boolean),
        max_redirects: Number(onboarding.maxRedirects),
        parser_profile: onboarding.parserProfile,
        parser_config: parserConfig,
      });
      setMessage(`${result.official_source.name} is onboarded with an active source monitor.`);
      setOnboarding(INITIAL_ONBOARDING);
      setTab("overview");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not onboard the regulatory source");
    } finally {
      setBusy(null);
    }
  }

  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  const counts = dashboard?.counts;

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Regulatory Intelligence" kicker="Official-source operations" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad intelligence-page">
        {error && <InlineNotice label="Regulatory intelligence error" detail={error} tone="bad" />}
        {message && <InlineNotice label="Operation complete" detail={message} tone="good" />}

        <div className="tab-bar intelligence-tabs">
          {TABS.map((item) => (
            <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>
              {titleCase(item)}
              {item === "changes" && counts?.changes_pending_review ? <span>{counts.changes_pending_review}</span> : null}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <>
            <div className="metric-row intelligence-metrics">
              <MetricPill label="Jurisdictions" value={counts?.jurisdictions || 0} />
              <MetricPill label="Official sources" value={counts?.official_sources || 0} />
              <MetricPill label="Active monitors" value={counts?.monitors_active || 0} tone="good" />
              <MetricPill label="Monitor errors" value={counts?.monitors_error || 0} tone={counts?.monitors_error ? "bad" : "good"} />
              <MetricPill label="Pending changes" value={counts?.changes_pending_review || 0} tone={counts?.changes_pending_review ? "warn" : "good"} />
              <MetricPill label="Published" value={counts?.changes_published || 0} tone="good" />
            </div>

            <div className="intelligence-grid">
              <section className="panel">
                <SectionTitle label="Monitoring" title="Official-source health" detail={`${dashboard?.monitors.length || 0} configured monitors`} />
                <div className="intelligence-list">
                  {dashboard?.monitors.length ? dashboard.monitors.map((monitor) => (
                    <article className="intelligence-row" key={monitor.id}>
                      <div className="intelligence-row-main">
                        <div className="intelligence-row-title">
                          <strong>{monitor.source_name || "Unknown source"}</strong>
                          <StatusBadge value={monitor.status} />
                          {!monitor.fresh && <span className="status-badge warn">Stale</span>}
                        </div>
                        <p>{titleCase(monitor.country)} · {titleCase(monitor.domain)} · every {monitor.schedule_minutes} minutes</p>
                        <small>Last check: {formatDate(monitor.last_checked_at)} · HTTP {monitor.last_http_status || "—"}</small>
                        <small>Parser: {titleCase(monitor.parser_profile)}</small>
                        {monitor.last_error && <span className="intelligence-error">{monitor.last_error}</span>}
                      </div>
                      <button
                        className="button secondary small"
                        disabled={busy === `monitor-${monitor.id}`}
                        onClick={() => handleMonitorRun(monitor.id)}
                      >
                        {busy === `monitor-${monitor.id}` ? "Queueing…" : "Run now"}
                      </button>
                    </article>
                  )) : <EmptyState title="No source monitors" detail="Onboard an authority source and create a monitor to begin scheduled retrieval." />}
                </div>
              </section>

              <section className="panel">
                <SectionTitle label="Failures" title="Recent retrieval issues" detail="Safe failures that produced no evidence changes" />
                <div className="intelligence-list compact">
                  {dashboard?.recent_failures.length ? dashboard.recent_failures.map((run) => (
                    <article className="intelligence-failure" key={run.id}>
                      <div><StatusBadge value={run.status} /><strong>{titleCase(run.error_code)}</strong></div>
                      <p>{run.error_message}</p>
                      <small>{formatDate(run.completed_at || run.started_at)}</small>
                    </article>
                  )) : <EmptyState title="No recent failures" detail="Retrieval failures will appear here with safe operational error codes." />}
                </div>
              </section>
            </div>
          </>
        )}

        {tab === "coverage" && (
          <div className="coverage-stack">
            <section className="panel">
              <SectionTitle label="Jurisdiction coverage" title="Source and freshness posture" detail="Monitoring coverage is measured against active official sources." />
              <div className="coverage-table-wrap">
                <table className="coverage-table">
                  <thead><tr><th>Jurisdiction</th><th>Authorities</th><th>Sources</th><th>Domains</th><th>Monitored</th><th>Fresh</th><th>Pending</th><th>Active rules</th></tr></thead>
                  <tbody>
                    {dashboard?.coverage.jurisdictions.length ? dashboard.coverage.jurisdictions.map((row) => (
                      <tr key={row.id}>
                        <td><strong>{row.name}</strong><small>{row.code}{row.region ? ` · ${row.region}` : ""}</small></td>
                        <td>{row.authorities}</td>
                        <td>{row.official_sources}</td>
                        <td>{row.domains.map(titleCase).join(", ") || "—"}</td>
                        <td><CoverageMeter value={row.monitoring_coverage_percent} /></td>
                        <td><CoverageMeter value={row.freshness_percent} /></td>
                        <td>{row.pending_changes}</td>
                        <td>{row.active_rules}</td>
                      </tr>
                    )) : <tr><td colSpan={8}><EmptyState title="No jurisdiction coverage" detail="Onboard the first authority source to establish coverage." /></td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <div className="intelligence-grid coverage-grid">
              <section className="panel">
                <SectionTitle label="Authority coverage" title="Authority monitoring posture" detail={`${dashboard?.coverage.authorities.length || 0} active authorities`} />
                <div className="coverage-card-grid">
                  {dashboard?.coverage.authorities.length ? dashboard.coverage.authorities.map((row) => (
                    <article className="coverage-card" key={row.id}>
                      <div><strong>{row.name}</strong><StatusBadge value={row.monitor_errors ? "error" : "active"} /></div>
                      <small>{row.jurisdiction_code || "—"} · {row.declared_domains.map(titleCase).join(", ") || "No domains"}</small>
                      <p>{row.monitored_sources} of {row.official_sources} sources monitored · {row.fresh_monitors} fresh</p>
                      <CoverageMeter value={row.monitoring_coverage_percent} />
                    </article>
                  )) : <EmptyState title="No authorities" detail="Authority coverage appears after onboarding." />}
                </div>
              </section>

              <section className="panel">
                <SectionTitle label="Domain coverage" title="Regulatory domain posture" detail={`${dashboard?.coverage.domains.length || 0} declared domains`} />
                <div className="coverage-card-grid">
                  {dashboard?.coverage.domains.length ? dashboard.coverage.domains.map((row) => (
                    <article className="coverage-card" key={row.domain}>
                      <div><strong>{titleCase(row.domain)}</strong><span>{row.jurisdictions} jurisdictions</span></div>
                      <small>{row.authorities} authorities · {row.official_sources} official sources</small>
                      <p>{row.monitored_sources} monitored · {row.pending_changes} pending · {row.active_rules} active rules</p>
                      <CoverageMeter value={row.freshness_percent} />
                    </article>
                  )) : <EmptyState title="No domain coverage" detail="Declared authority domains appear here." />}
                </div>
              </section>
            </div>
          </div>
        )}

        {tab === "changes" && (
          <div className="intelligence-review-grid">
            <section className="panel">
              <SectionTitle label="Change queue" title="Detected regulatory changes" detail={`${changes.length} events`} />
              <div className="intelligence-list">
                {changes.length ? changes.map((change) => (
                  <button
                    className={`regulatory-change-card ${selectedChangeId === change.id ? "selected" : ""}`}
                    key={change.id}
                    onClick={() => {
                      setSelectedChangeId(change.id);
                      setRuleStatement(change.summary);
                      setRuleKey(change.change_type);
                    }}
                  >
                    <span><StatusBadge value={change.status} /><em>{titleCase(change.materiality)}</em></span>
                    <strong>{change.title}</strong>
                    <p>{jurisdictionNames.get(change.jurisdiction_id) || "Unknown jurisdiction"} · {titleCase(change.change_type)}</p>
                    <small>{formatDate(change.detected_at)}</small>
                  </button>
                )) : <EmptyState title="No regulatory changes" detail="Changed official-source snapshots will enter this queue." />}
              </div>
            </section>

            <section className="panel intelligence-review-panel">
              {selectedChange ? (
                <>
                  <SectionTitle label="Evidence review" title={selectedChange.title} detail={selectedChange.summary} />
                  <div className="review-meta-grid">
                    <div><small>Jurisdiction</small><strong>{jurisdictionNames.get(selectedChange.jurisdiction_id) || "Unknown"}</strong></div>
                    <div><small>Type</small><strong>{titleCase(selectedChange.change_type)}</strong></div>
                    <div><small>Materiality</small><strong>{titleCase(selectedChange.materiality)}</strong></div>
                    <div><small>Status</small><StatusBadge value={selectedChange.status} /></div>
                  </div>
                  <div className="diff-view">
                    <small>Snapshot difference</small>
                    <pre>{diffLines(selectedChange.diff_json).join("\n") || "No textual diff was stored."}</pre>
                  </div>

                  <div className="classification-workspace">
                    <div className="classification-workspace-header">
                      <div><small>Advisory classification ledger</small><strong>Evidence-bound proposals</strong></div>
                      {selectedChange.status === "pending_review" && (
                        <div className="form-actions">
                          <button className="button secondary small" disabled={Boolean(busy)} onClick={() => handleGenerateClassification(false)}>Deterministic proposal</button>
                          <button className="button primary small" disabled={Boolean(busy)} onClick={() => handleGenerateClassification(true)}>Model-assisted proposal</button>
                        </div>
                      )}
                    </div>
                    {selectedProposals.length ? selectedProposals.map((proposal) => (
                      <article className="classification-proposal-card" key={proposal.id}>
                        <div className="classification-proposal-heading">
                          <span><StatusBadge value={proposal.status} /><em>{titleCase(proposal.method)}</em></span>
                          <strong>{Math.round(proposal.confidence * 100)}% proposal confidence</strong>
                        </div>
                        <div className="review-meta-grid">
                          <div><small>Proposed type</small><strong>{titleCase(proposal.proposed_change_type)}</strong></div>
                          <div><small>Materiality</small><strong>{titleCase(proposal.proposed_materiality)}</strong></div>
                          <div><small>Provider</small><strong>{proposal.provider || "Deterministic rules"}</strong></div>
                          <div><small>Prompt</small><strong>{proposal.prompt_version}</strong></div>
                        </div>
                        <p>{proposal.proposed_summary}</p>
                        <small>{proposal.rationale}</small>
                        {proposal.fallback_reason && <InlineNotice label="Deterministic fallback" detail={proposal.fallback_reason} tone="warn" />}
                        <div className="classification-evidence">
                          <small>Cited snapshot evidence</small>
                          <pre>{proposal.evidence.map((item) => `${item.line_number}: ${item.text}`).join("\n") || "No valid diff evidence was cited."}</pre>
                        </div>
                        {proposal.status === "pending_review" && (
                          <div className="intelligence-form compact-form">
                            <label>Classification review notes<textarea rows={3} value={proposalNotes} onChange={(event) => setProposalNotes(event.target.value)} placeholder="Explain why the cited evidence supports or contradicts this proposal." /></label>
                            <div className="form-actions">
                              <button className="button primary small" disabled={!proposalNotes.trim() || Boolean(busy)} onClick={() => handleClassificationReview(proposal.id, "accepted")}>Accept proposal</button>
                              <button className="button secondary small" disabled={!proposalNotes.trim() || Boolean(busy)} onClick={() => handleClassificationReview(proposal.id, "rejected")}>Reject proposal</button>
                            </div>
                          </div>
                        )}
                      </article>
                    )) : <EmptyState title="No classification proposal" detail="Generate a deterministic or configured model-assisted proposal before regulatory review." />}
                  </div>

                  {selectedChange.status === "pending_review" && hasAcceptedClassification && (
                    <div className="intelligence-form">
                      <label>Reviewer notes<textarea rows={4} value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} placeholder="Describe how the official evidence was validated." /></label>
                      <div className="form-actions">
                        <button className="button primary" disabled={!reviewNotes.trim() || Boolean(busy)} onClick={() => handleReview("approved")}>Approve change</button>
                        <button className="button secondary" disabled={!reviewNotes.trim() || Boolean(busy)} onClick={() => handleReview("rejected")}>Reject</button>
                      </div>
                    </div>
                  )}
                  {selectedChange.status === "pending_review" && !hasAcceptedClassification && (
                    <InlineNotice label="Classification review required" detail="Accept an evidence-bound proposal before approving the regulatory change. Proposal acceptance does not publish a rule." tone="warn" />
                  )}

                  {selectedChange.status === "approved" && (
                    <div className="intelligence-form">
                      <label>Rule key<input value={ruleKey} onChange={(event) => setRuleKey(event.target.value)} /></label>
                      <label>Verified statement<textarea rows={4} value={ruleStatement} onChange={(event) => setRuleStatement(event.target.value)} /></label>
                      <label>Supersedes active rule<select value={supersedesRuleId} onChange={(event) => setSupersedesRuleId(event.target.value)}><option value="">No existing rule</option>{replacementCandidates.map((rule) => <option value={rule.id} key={rule.id}>{rule.rule_key} — {rule.statement.slice(0, 70)}</option>)}</select></label>
                      <button className="button primary" disabled={!ruleKey.trim() || !ruleStatement.trim() || Boolean(busy)} onClick={handlePublish}>Publish verified rule</button>
                    </div>
                  )}

                  {selectedChange.status === "published" && <InlineNotice label="Published" detail="This change is linked to an immutable verified rule." tone="good" />}
                  {selectedChange.status === "rejected" && <InlineNotice label="Rejected" detail={selectedChange.review_notes || "The reviewer rejected this change."} tone="bad" />}
                </>
              ) : <EmptyState title="Select a change" detail="Choose an event to inspect its snapshot difference and review state." />}
            </section>
          </div>
        )}

        {tab === "graph" && (
          <section className="panel intelligence-section">
            <div className="knowledge-graph-header">
              <SectionTitle label="Published-rule projection" title="Regulatory knowledge graph" detail="Every edge preserves its verified rule, reviewed change, and immutable snapshot provenance" />
              <button className="button primary" disabled={Boolean(busy)} onClick={handleGraphSync}>Synchronize published rules</button>
            </div>
            {knowledgeGraph ? (
              <>
                <div className="intelligence-metrics">
                  <MetricPill label="Graph nodes" value={knowledgeGraph.counts.nodes} />
                  <MetricPill label="Graph edges" value={knowledgeGraph.counts.edges} />
                  <MetricPill label="Published rules" value={knowledgeGraph.counts.verified_rules} />
                  <MetricPill label="Projection" value={knowledgeGraph.projection_version} />
                </div>
                <div className="graph-integrity-row">
                  <InlineNotice label="Human-published only" detail={knowledgeGraph.human_published_only ? "Graph mutation is restricted to reviewed and published verified rules." : "Graph source restriction failed."} tone={knowledgeGraph.human_published_only ? "good" : "bad"} />
                  <InlineNotice label="Provenance integrity" detail={knowledgeGraph.provenance_complete ? "Every visible edge links a rule, source snapshot, and regulatory change." : "One or more edges have incomplete provenance."} tone={knowledgeGraph.provenance_complete ? "good" : "bad"} />
                </div>
                <div className="knowledge-edge-list">
                  {knowledgeGraph.edges.length ? knowledgeGraph.edges.map((edge) => {
                    const source = graphNodeMap.get(edge.source_node_id);
                    const target = graphNodeMap.get(edge.target_node_id);
                    return (
                      <article className="knowledge-edge-card" key={edge.id}>
                        <div className="knowledge-edge-flow">
                          <span><small>{titleCase(source?.node_type || "node")}</small><strong>{source?.label || edge.source_node_id.slice(0, 8)}</strong></span>
                          <em>{titleCase(edge.relation_type)} →</em>
                          <span><small>{titleCase(target?.node_type || "node")}</small><strong>{target?.label || edge.target_node_id.slice(0, 8)}</strong></span>
                        </div>
                        <div className="knowledge-edge-provenance">
                          <span>Rule {edge.verified_rule_id.slice(0, 8)}</span>
                          <span>Change {edge.regulatory_change_id.slice(0, 8)}</span>
                          <span>Snapshot {edge.source_snapshot_id.slice(0, 8)}</span>
                        </div>
                      </article>
                    );
                  }) : <EmptyState title="No published-rule graph" detail="Publish a human-reviewed regulatory change or synchronize existing verified rules." />}
                </div>
              </>
            ) : <EmptyState title="Knowledge graph unavailable" detail="Refresh after the API and migration are ready." />}
          </section>
        )}

        {tab === "rules" && (
          <section className="panel intelligence-section">
            <SectionTitle label="Rule registry" title="Verified regulatory rules" detail={`${rules.filter((rule) => rule.active).length} active · ${rules.filter((rule) => !rule.active).length} historical`} />
            <div className="verified-rule-grid">
              {rules.length ? rules.map((rule) => (
                <article className={`verified-rule-card ${rule.active ? "" : "inactive"}`} key={rule.id}>
                  <div><StatusBadge value={rule.active ? "active" : "retired"} /><span>{titleCase(rule.country)} · {titleCase(rule.domain)}</span></div>
                  <strong>{rule.rule_key}</strong>
                  <p>{rule.statement}</p>
                  <small>Confidence {Math.round(rule.confidence * 100)}% · published {formatDate(rule.published_at)}</small>
                  {rule.supersedes_rule_id && <small>Supersedes rule {rule.supersedes_rule_id.slice(0, 8)}</small>}
                  {rule.retirement_reason && <span className="intelligence-error">{rule.retirement_reason}</span>}
                  {rule.active && (retireTarget === rule.id ? (
                    <div className="intelligence-form compact-form">
                      <label>Retirement reason<textarea rows={2} value={retireReason} onChange={(event) => setRetireReason(event.target.value)} /></label>
                      <div className="form-actions"><button className="button secondary small" onClick={() => setRetireTarget(null)}>Cancel</button><button className="button primary small" disabled={!retireReason.trim() || Boolean(busy)} onClick={() => handleRetire(rule.id)}>Confirm retirement</button></div>
                    </div>
                  ) : <button className="button secondary small" onClick={() => setRetireTarget(rule.id)}>Retire rule</button>)}
                </article>
              )) : <EmptyState title="No verified rules" detail="Approved regulatory changes can be published into this registry." />}
            </div>
          </section>
        )}

        {tab === "evidence" && (
          <section className="panel intelligence-section">
            <SectionTitle label="Evidence ledger" title="Immutable source snapshots" detail={`${snapshots.length} recent captures`} />
            <div className="snapshot-grid">
              {snapshots.length ? snapshots.map((snapshot) => (
                <article className="snapshot-card" key={snapshot.id}>
                  <div><StatusBadge value={snapshot.status} /><span>{snapshot.parser_version || snapshot.retrieval_method}</span></div>
                  <strong>{snapshot.url}</strong>
                  <p>{snapshot.content_preview || "No extracted preview."}</p>
                  <small>SHA-256 {snapshot.content_hash?.slice(0, 16) || "reference only"}… · {formatDate(snapshot.captured_at)}</small>
                </article>
              )) : <EmptyState title="No captured evidence" detail="Source-monitor baselines and changes will appear here." />}
            </div>
          </section>
        )}

        {tab === "onboarding" && (
          <div className="onboarding-grid">
            <section className="panel">
              <SectionTitle label="Controlled onboarding" title="Add an authority-backed official source" detail="The jurisdiction, authority, source, and monitor are validated and written as one audited operation." />
              <div className="intelligence-form onboarding-form">
                <div className="form-section-title"><span>1</span><div><strong>Jurisdiction</strong><small>Canonical jurisdiction identity and regional grouping</small></div></div>
                <div className="onboarding-fields three">
                  <label>Code<input value={onboarding.jurisdictionCode} maxLength={32} onChange={(event) => updateOnboarding("jurisdictionCode", event.target.value)} placeholder="NZ" /></label>
                  <label>Name<input value={onboarding.jurisdictionName} onChange={(event) => updateOnboarding("jurisdictionName", event.target.value)} placeholder="New Zealand" /></label>
                  <label>Type<select value={onboarding.jurisdictionType} onChange={(event) => updateOnboarding("jurisdictionType", event.target.value)}><option value="country">Country</option><option value="territory">Territory</option><option value="autonomous_jurisdiction">Autonomous jurisdiction</option></select></label>
                  <label>Region<input value={onboarding.region} onChange={(event) => updateOnboarding("region", event.target.value)} placeholder="Oceania" /></label>
                </div>

                <div className="form-section-title"><span>2</span><div><strong>Regulatory authority</strong><small>An existing authority with the same name is safely updated</small></div></div>
                <div className="onboarding-fields two">
                  <label>Authority name<input value={onboarding.authorityName} onChange={(event) => updateOnboarding("authorityName", event.target.value)} placeholder="Immigration New Zealand" /></label>
                  <label>Authority type<input value={onboarding.authorityType} onChange={(event) => updateOnboarding("authorityType", event.target.value)} /></label>
                  <label>Official website<input type="url" value={onboarding.authorityWebsiteUrl} onChange={(event) => updateOnboarding("authorityWebsiteUrl", event.target.value)} placeholder="https://www.immigration.govt.nz/" /></label>
                  <label>Declared domains<input value={onboarding.authorityDomains} onChange={(event) => updateOnboarding("authorityDomains", event.target.value)} placeholder="visa, work, settlement" /><small>Comma-separated; must include the source domain.</small></label>
                </div>

                <div className="form-section-title"><span>3</span><div><strong>Official source</strong><small>Only HTTPS authority-controlled URLs are accepted</small></div></div>
                <div className="onboarding-fields two">
                  <label>Source name<input value={onboarding.sourceName} onChange={(event) => updateOnboarding("sourceName", event.target.value)} placeholder="Accredited Employer Work Visa guidance" /></label>
                  <label>Source URL<input type="url" value={onboarding.sourceUrl} onChange={(event) => updateOnboarding("sourceUrl", event.target.value)} placeholder="https://www.immigration.govt.nz/..." /></label>
                  <label>Regulatory domain<input value={onboarding.sourceDomain} onChange={(event) => updateOnboarding("sourceDomain", event.target.value)} placeholder="visa" /></label>
                  <label>Source type<select value={onboarding.sourceType} onChange={(event) => updateOnboarding("sourceType", event.target.value)}><option value="official">Official</option><option value="government">Government</option><option value="official_portal">Official portal</option><option value="official_agency">Official agency</option><option value="gazette">Gazette</option></select></label>
                </div>

                <div className="form-section-title"><span>4</span><div><strong>Retrieval policy</strong><small>Schedule and egress boundary for the controlled monitor</small></div></div>
                <div className="onboarding-fields three">
                  <label>Interval in minutes<input type="number" min={15} max={525600} value={onboarding.scheduleMinutes} onChange={(event) => updateOnboarding("scheduleMinutes", event.target.value)} /></label>
                  <label>Fetch method<select value={onboarding.fetchMethod} onChange={(event) => updateOnboarding("fetchMethod", event.target.value)}><option value="http">HTTP</option><option value="browser">Browser</option><option value="api">API</option><option value="manual">Manual</option></select></label>
                  <label>Maximum redirects<input type="number" min={0} max={10} value={onboarding.maxRedirects} onChange={(event) => updateOnboarding("maxRedirects", event.target.value)} /></label>
                  <label>Allowed hostnames<input value={onboarding.allowedDomains} onChange={(event) => updateOnboarding("allowedDomains", event.target.value)} placeholder="immigration.govt.nz" /><small>Comma-separated hostnames only. Blank defaults to the source hostname.</small></label>
                  <label>Parser profile<select value={onboarding.parserProfile} onChange={(event) => updateOnboarding("parserProfile", event.target.value)}><option value="generic">Generic content</option><option value="gazette_html_v1">Gazette HTML</option><option value="structured_program_catalog_v1">Structured program catalogue</option></select></label>
                  <label className="onboarding-wide">Parser configuration<textarea rows={6} value={onboarding.parserConfig} onChange={(event) => updateOnboarding("parserConfig", event.target.value)} spellCheck={false} /><small>JSON object. Structured catalogues can define records_path, id_field, name_field, status_field, summary_field, retired_values, and missing_means_retired.</small></label>
                </div>

                <button
                  className="button primary onboarding-submit"
                  disabled={Boolean(busy) || [onboarding.jurisdictionCode, onboarding.jurisdictionName, onboarding.authorityName, onboarding.sourceName, onboarding.sourceUrl].some((value) => !value.trim())}
                  onClick={handleOnboard}
                >
                  {busy === "onboarding" ? "Validating and onboarding…" : "Onboard official source"}
                </button>
              </div>
            </section>

            <aside className="panel onboarding-policy">
              <SectionTitle label="Guardrails" title="What this workflow enforces" detail="No source becomes trusted merely because it was entered here." />
              <ul>
                <li><strong>HTTPS only</strong><span>Credentials, wildcard hosts, paths in allowlists, and non-standard ports are rejected.</span></li>
                <li><strong>Authority ownership</strong><span>An existing source cannot be silently reassigned across jurisdictions or authorities.</span></li>
                <li><strong>Controlled egress</strong><span>The source hostname must fall within the explicit retrieval allowlist.</span></li>
                <li><strong>Human validation</strong><span>Retrieved changes still require review before any verified rule can be published.</span></li>
                <li><strong>Audit history</strong><span>The authenticated operator and resulting IDs are recorded for every onboarding operation.</span></li>
              </ul>
            </aside>
          </div>
        )}
      </div>
    </WorkspaceShell>
  );
}
