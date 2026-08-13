"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { TechnicalDisclosure } from "../../components/TechnicalDisclosure";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  comparePathways,
  generateCountryRanking,
  createReassessmentAcceptance,
  executeReassessmentAcceptance,
  getCountryRankingHistory,
  getHealthStatus,
  getLatestPathwayComparison,
  getLeads,
  getPathwayComparisonHistory,
  getReassessmentCandidate,
  CountryRanking,
  HealthStatus,
  Lead,
  listReassessmentAcceptances,
  PathwayComparison,
  PathwayComparisonItem,
  ReassessmentAcceptance,
  ReassessmentCandidate,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

function money(value: number | null, currency: string) {
  if (value == null) return "Not recorded";
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function ComparisonCard({ item, primary = false }: { item: PathwayComparisonItem; primary?: boolean }) {
  const version = item.pathway.current_version;
  const isDraft = item.lifecycle_status === "draft" || item.simulation_only;
  const excluded = item.recommendation_status === "excluded";
  const blockingGaps = item.evidence_gaps.filter((gap) => gap.status === "BLOCKING");
  const pendingCertifications = item.evidence_trace.filter((trace) => trace.certification_status === "pending_review");
  return (
    <article className={`planning-comparison-card ${primary ? "primary" : ""} ${isDraft ? "draft-simulation" : ""} ${excluded ? "excluded" : ""}`}>
      <div className="planning-card-heading">
        <div>
          <span>{excluded ? "Excluded route" : primary ? "Leading potential pathway" : "Other assessed route"}</span>
          <h3>{item.pathway.name}</h3>
          <p>{titleCase(item.pathway.country)} · {titleCase(item.pathway.domain)} · version {version?.version_number || "—"}</p>
          {isDraft && (
            <div className="draft-governance-badge">
              <strong>Internal simulation — not published</strong>
              <span>This draft is not a production recommendation and must not be relied on for an application.</span>
              <div><StatusBadge value={item.lifecycle_status} /><StatusBadge value="internal_simulation_only" /><StatusBadge value={item.publication_ready ? "publication_ready" : "unpublished"} /></div>
            </div>
          )}
        </div>
        <div className="planning-score"><strong>{item.compatibility_status.replaceAll("_", " ")}</strong><small>candidate status</small></div>
      </div>
      {excluded && <InlineNotice label="EXCLUDED" detail={item.exclusion_reasons.join(" ")} tone="warn" />}
      <p className="planning-explanation">{item.explanation}</p>
      {blockingGaps.length > 0 && <section className="planning-blockers" aria-label="Blocking requirements">
        <span className="hierarchy-label">Blockers</span>
        <strong>{blockingGaps[0].label}</strong>
        <p>{blockingGaps[0].detail}</p>
        {blockingGaps.length > 1 ? <small>{blockingGaps.length - 1} additional blocking requirement{blockingGaps.length === 2 ? "" : "s"} remains in supporting evidence.</small> : null}
      </section>}
      {item.next_actions.length > 0 && <section className="planning-next-actions"><span className="hierarchy-label">Next actions</span><ul>{item.next_actions.map((action) => <li key={action.code}><b>{action.title}</b><span>{action.detail}</span><small>{titleCase(action.category)}</small></li>)}</ul></section>}
      {pendingCertifications.length > 0 && <InlineNotice label="Occupation evidence review is pending" detail={`${pendingCertifications.length} material evidence certification${pendingCertifications.length === 1 ? " remains" : "s remain"} pending independent review. This pathway is not publication-ready.`} tone="warn" />}
      <div className="planning-card-metrics">
        <div><small>Government application fee</small><strong>{money(item.cost.government_application_fee, item.cost.currency)}</strong></div>
        <div><small>Estimated total cost</small><strong>{item.cost.estimated_total_status === "established" ? money(item.cost.one_time_total, item.cost.currency) : "Not established"}</strong></div>
        <div><small>Processing time</small><strong>{item.processing_evidence_status === "established" ? "Governed range recorded" : "Not established from governed evidence"}</strong></div>
        <div><small>Minimum funds</small><strong>{money(item.cost.minimum_funds, item.cost.currency)}</strong></div>
        <div><small>Risk</small><StatusBadge value={`${item.risk.level}_risk`} /></div>
        <div><small>Evidence gaps</small><strong>{item.evidence_gaps.length || item.missing_evidence.length}</strong></div>
      </div>
      {item.occupation_assessment && <section className="planning-occupation-assessment">
        <strong>Occupation assessment · {item.occupation_assessment.match_quality}</strong>
        <p>{item.occupation_assessment.occupation_input} · qualification mapping {item.occupation_assessment.qualification_mapping.toLowerCase()} · job offer {item.occupation_assessment.job_offer_status.toLowerCase()}</p>
        <p>{item.occupation_assessment.conclusion}</p>
        <details><summary>National and regional governed candidates</summary>
          <p><strong>National {item.occupation_assessment.year}:</strong> {item.occupation_assessment.national.match_quality} · {item.occupation_assessment.national.reason}</p>
          <ul>{item.occupation_assessment.national.candidates.map((candidate) => <li key={candidate.id}>{candidate.occupation_group}</li>)}</ul>
          <p><strong>Regional {item.occupation_assessment.year}:</strong> {item.occupation_assessment.regional.match_quality} · {item.occupation_assessment.regional.reason}</p>
          <ul>{item.occupation_assessment.regional.candidates.map((candidate) => <li key={candidate.id}>{candidate.occupation_group}</li>)}</ul>
        </details>
      </section>}
      {item.evidence_gaps.length > 0 && <section className="planning-gap-assessment">
        <span className="hierarchy-label">Supporting evidence</span>
        <strong>Case-specific gaps</strong>
        <div className="planning-detail-grid">{(["FACT", "EVIDENCE", "DOCUMENT", "REGULATORY", "CERTIFICATION"] as const).map((category) => {
          const gaps = item.evidence_gaps.filter((gap) => gap.category === category);
          return gaps.length ? <div key={category}><strong>{category}</strong><ul>{gaps.map((gap) => <li key={gap.code}><b>{gap.label}: {gap.status}</b> — {gap.detail}</li>)}</ul></div> : null;
        })}</div>
      </section>}
      <div className="planning-detail-grid">
        <div><strong>Compatibility evidence</strong><ul>{item.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>
        <div><strong>Tradeoffs</strong><ul>{item.tradeoffs.map((tradeoff) => <li key={tradeoff}>{tradeoff}</li>)}</ul></div>
        <div><strong>Benefits</strong>{item.benefits.length ? <ul>{item.benefits.map((benefit) => <li key={benefit}>{benefit}</li>)}</ul> : <p>No reviewed benefits recorded.</p>}</div>
        <div><strong>Risks and evidence</strong><ul>{[...item.risk.declared_risks, ...item.risk.regulatory_risks, ...item.missing_evidence].map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}</ul></div>
      </div>
      {item.evidence_trace.length > 0 && <TechnicalDisclosure label="Technical provenance" detail={`${item.evidence_trace.length} material evidence record${item.evidence_trace.length === 1 ? "" : "s"}`}>
        <div className="planning-evidence-trace-list">{item.evidence_trace.map((trace, index) => <article key={`${trace.trace_type}-${trace.evidence_role || trace.verified_rule_id}-${index}`}>
          <div><strong>{trace.requirement}</strong><StatusBadge value={trace.certification_status} /></div>
          {trace.verified_rule_statement && <p><b>Verified rule:</b> {trace.verified_rule_statement}</p>}
          {trace.evidence_role && <p><b>Pathway evidence role:</b> {trace.evidence_role}</p>}
          {trace.occupation_entry_titles.length > 0 && <p><b>Governed occupation entries:</b> {trace.occupation_entry_titles.join("; ")}</p>}
          <p><b>Official source:</b> {trace.official_source_title}{trace.authority ? ` · ${trace.authority}` : ""}</p>
          <p><b>Source identifier:</b> <code>{trace.official_source_id}</code></p>
          <p><b>Snapshot:</b> <code>{trace.source_snapshot_id}</code> · {new Date(trace.source_snapshot_captured_at).toLocaleString()}</p>
          {trace.evidence_year && <p><b>Applicable evidence year:</b> {trace.evidence_year}</p>}
          {trace.source_snapshot_content_hash && <p><b>Snapshot hash:</b> <code>{trace.source_snapshot_content_hash}</code></p>}
          {trace.certification_id && <p><b>Certification:</b> <code>{trace.certification_id}</code> · {titleCase(trace.certification_status)}</p>}
          {trace.structured_pack_sha256 && <p><b>Structured review pack:</b> <code>{trace.structured_pack_sha256}</code></p>}
          <div className="planning-trace-actions">
            <a className="button secondary" href={trace.official_source_url} target="_blank" rel="noreferrer">Inspect official evidence</a>
            {trace.review_workspace_path && <Link className="button secondary" href={trace.review_workspace_path}>Inspect review pack</Link>}
          </div>
        </article>)}</div>
        <div className="planning-provenance">
          <span>Pathway version <code>{version?.id || "missing"}</code></span>
          <span>{item.verified_rule_ids.length} verified rule{item.verified_rule_ids.length === 1 ? "" : "s"}</span>
        </div>
      </TechnicalDisclosure>}
    </article>
  );
}

export default function PlanningPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [includeDraftPathways, setIncludeDraftPathways] = useState(false);
  const [comparison, setComparison] = useState<PathwayComparison | null>(null);
  const [countryRanking, setCountryRanking] = useState<CountryRanking | null>(null);
  const [countryRankingHistory, setCountryRankingHistory] = useState<CountryRanking[]>([]);
  const [history, setHistory] = useState<PathwayComparison[]>([]);
  const [candidate, setCandidate] = useState<ReassessmentCandidate | null>(null);
  const [acceptances, setAcceptances] = useState<ReassessmentAcceptance[]>([]);
  const [acceptProfile, setAcceptProfile] = useState(false);
  const [selectedImpacts, setSelectedImpacts] = useState<string[]>([]);
  const [attestation, setAttestation] = useState("");
  const [acceptanceNotes, setAcceptanceNotes] = useState("");
  const [rankingAttestation, setRankingAttestation] = useState("");
  const [rankingNotes, setRankingNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [recording, setRecording] = useState(false);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [rankingRunning, setRankingRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [healthResult, leadRows] = await Promise.all([getHealthStatus(), getLeads()]);
      setHealth(healthResult.data); setLeads(leadRows);
      const requestedLeadId = typeof window !== "undefined"
        ? new URLSearchParams(window.location.search).get("lead_id") || ""
        : "";
      if (requestedLeadId && leadRows.some((lead) => lead.id === requestedLeadId)) {
        setLeadId(requestedLeadId);
        const [latest, rows, reassessment, acceptanceRows, rankingRows] = await Promise.allSettled([
          getLatestPathwayComparison(requestedLeadId),
          getPathwayComparisonHistory(requestedLeadId),
          getReassessmentCandidate(requestedLeadId),
          listReassessmentAcceptances(requestedLeadId),
          getCountryRankingHistory(requestedLeadId),
        ]);
        if (latest.status === "fulfilled") setComparison(latest.value);
        if (rows.status === "fulfilled") setHistory(rows.value);
        if (reassessment.status === "fulfilled") setCandidate(reassessment.value);
        if (acceptanceRows.status === "fulfilled") setAcceptances(acceptanceRows.value);
        if (rankingRows.status === "fulfilled") {
          setCountryRankingHistory(rankingRows.value);
          setCountryRanking(rankingRows.value[0] || null);
        }
      }
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load mobility planning"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function chooseLead(selectedLeadId: string) {
    setLeadId(selectedLeadId); setComparison(null); setHistory([]); setCandidate(null); setAcceptances([]); setCountryRanking(null); setCountryRankingHistory([]); setError(null);
    setAcceptProfile(false); setSelectedImpacts([]); setAttestation(""); setAcceptanceNotes(""); setRankingAttestation(""); setRankingNotes("");
    if (!selectedLeadId) return;
    setLoading(true);
    const [latest, rows, reassessment, acceptanceRows, rankingRows] = await Promise.allSettled([
      getLatestPathwayComparison(selectedLeadId),
      getPathwayComparisonHistory(selectedLeadId),
      getReassessmentCandidate(selectedLeadId),
      listReassessmentAcceptances(selectedLeadId),
      getCountryRankingHistory(selectedLeadId),
    ]);
    if (latest.status === "fulfilled") setComparison(latest.value);
    if (rows.status === "fulfilled") setHistory(rows.value);
    if (reassessment.status === "fulfilled") setCandidate(reassessment.value);
    if (acceptanceRows.status === "fulfilled") setAcceptances(acceptanceRows.value);
    if (rankingRows.status === "fulfilled") {
      setCountryRankingHistory(rankingRows.value);
      setCountryRanking(rankingRows.value[0] || null);
    }
    setLoading(false);
  }

  async function runComparison() {
    if (!leadId) return;
    setRunning(true); setError(null);
    try {
      const result = await comparePathways(leadId, { include_draft_pathways: includeDraftPathways });
      setComparison(result);
      setHistory(result.assessment_id ? await getPathwayComparisonHistory(leadId) : []);
      if (result.assessment_id) setCandidate(await getReassessmentCandidate(leadId));
    } catch (err) { setError(err instanceof Error ? err.message : "Could not generate pathway comparison"); }
    finally { setRunning(false); }
  }

  async function runCountryRanking() {
    if (!leadId) return;
    setRankingRunning(true); setError(null);
    try {
      const result = await generateCountryRanking(leadId, {
        explicit_user_acceptance: true,
        user_attestation: rankingAttestation,
        notes: rankingNotes,
        limit_countries: 20,
      });
      setCountryRanking(result);
      setCountryRankingHistory(await getCountryRankingHistory(leadId));
      setRankingAttestation(""); setRankingNotes("");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not generate reviewed country ranking"); }
    finally { setRankingRunning(false); }
  }

  async function recordAcceptance() {
    if (!leadId || !candidate) return;
    setRecording(true); setError(null);
    try {
      await createReassessmentAcceptance(leadId, {
        baseline_assessment_id: candidate.baseline_assessment_id,
        accept_profile_version: acceptProfile,
        regulatory_impact_ids: selectedImpacts,
        explicit_user_acceptance: true,
        user_attestation: attestation,
        notes: acceptanceNotes,
      });
      setAcceptances(await listReassessmentAcceptances(leadId));
      setAttestation(""); setAcceptanceNotes("");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not record reassessment acceptance"); }
    finally { setRecording(false); }
  }

  async function executeAcceptance(acceptanceId: string) {
    if (!leadId) return;
    setExecutingId(acceptanceId); setError(null);
    try {
      const result = await executeReassessmentAcceptance(acceptanceId);
      setComparison(result);
      const [rows, reassessment, acceptanceRows] = await Promise.all([
        getPathwayComparisonHistory(leadId),
        getReassessmentCandidate(leadId),
        listReassessmentAcceptances(leadId),
      ]);
      setHistory(rows); setCandidate(reassessment); setAcceptances(acceptanceRows);
      setAcceptProfile(false); setSelectedImpacts([]);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not execute accepted reassessment"); }
    finally { setExecutingId(null); }
  }

  const selectedLead = leads.find((lead) => lead.id === leadId);
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  const primary = comparison?.primary;
  const potentialAlternatives = comparison?.alternatives.filter((item) => item.recommendation_status !== "excluded") || [];
  const excludedAlternatives = comparison?.alternatives.filter((item) => item.recommendation_status === "excluded") || [];
  const internalSimulationActive = includeDraftPathways || Boolean(primary?.simulation_only || primary?.lifecycle_status === "draft");
  return (
    <WorkspaceShell health={health}>
      <Topbar title="Mobility Planning" kicker="Cost, risk, evidence, alternatives" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad planning-page">
        {error && <InlineNotice label="Planning error" detail={error} tone="bad" />}
        <section className={`panel planning-selector ${includeDraftPathways ? "simulation-context" : "production-context"}`}>
          <div><span className="page-kicker">{includeDraftPathways ? "Internal simulation context" : "Production catalogue context"}</span><strong>{includeDraftPathways ? "Assess governed draft candidates without making a production recommendation." : "Compare published, evidence-backed pathways against the current profile."}</strong></div>
          <label>Lead<select value={leadId} onChange={(event) => void chooseLead(event.target.value)}><option value="">Choose a lead</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name} · {lead.target_country || "No target"}</option>)}</select></label>
          <label className="profile-check planning-simulation-control">
            <input type="checkbox" checked={includeDraftPathways} onChange={(event) => setIncludeDraftPathways(event.target.checked)} />
            <span><strong>Include internal/draft pathways</strong><small>Simulation only; draft candidates are not published or client-facing.</small></span>
          </label>
          <button className="button primary" disabled={!leadId || running || Boolean(candidate?.requires_acceptance)} onClick={() => void runComparison()}>{running ? "Comparing…" : candidate?.requires_acceptance ? "Acceptance required" : "Generate comparison"}</button>
        </section>

        {internalSimulationActive ? <div className="simulation-banner" role="status" aria-live="polite">
          <strong>Internal simulation is active</strong>
          <span>Draft candidates may appear for internal review. They remain unpublished, are not production recommendations, and must not be relied on for an application.</span>
        </div> : null}

        {leadId && <section className="panel country-ranking-panel">
          <SectionTitle label="Global user intelligence" title="Reviewed country fit" detail="Ranks only countries represented by human-published pathways and never bypasses the global coverage gate." />
          <div className="country-ranking-controls">
            <label>User acceptance attestation<textarea value={rankingAttestation} onChange={(event) => setRankingAttestation(event.target.value)} placeholder="Record the user's explicit acceptance of this exact cross-country assessment." /></label>
            <label>Operator notes<textarea value={rankingNotes} onChange={(event) => setRankingNotes(event.target.value)} placeholder="Record consultation context and explain that this is not an eligibility guarantee." /></label>
            <button className="button primary" disabled={rankingRunning || Boolean(candidate?.requires_acceptance) || rankingAttestation.trim().length < 10 || rankingNotes.trim().length < 3} onClick={() => void runCountryRanking()}>{rankingRunning ? "Ranking…" : candidate?.requires_acceptance ? "Resolve reassessment first" : "Generate country ranking"}</button>
          </div>
          {countryRanking && <>
            <InlineNotice label={countryRanking.scope.global_coverage_claim_ready ? "Complete reviewed catalogue" : "Reviewed catalogue only"} detail={countryRanking.scope.message} tone={countryRanking.scope.global_coverage_claim_ready ? "good" : "warn"} />
            <div className="metric-row country-ranking-metrics">
              <MetricPill label="Countries ranked" value={countryRanking.countries.length} />
              <MetricPill label="Published countries" value={countryRanking.scope.published_catalogue_countries} />
              <MetricPill label="Pathway versions" value={countryRanking.scope.published_pathway_versions} />
              <MetricPill label="Ranking history" value={countryRankingHistory.length} />
            </div>
            <div className="country-ranking-grid">{countryRanking.countries.map((item) => {
              const pr = item.long_term_dependencies.find((entry) => entry.stage === "permanent_residence");
              const citizenship = item.long_term_dependencies.find((entry) => entry.stage === "citizenship");
              return <article key={`${countryRanking.assessment_id}-${item.country}`} className="country-ranking-card">
                <div className="country-ranking-heading"><span>#{item.rank}</span><div><h3>{titleCase(item.country)}</h3><p>{item.primary_pathway.pathway.name}</p></div><strong>{Math.round(item.ranking_score * 100)}%</strong></div>
                <p>{item.explanation}</p>
                <div className="country-ranking-badges"><StatusBadge value={`${item.uncertainty.level}_uncertainty`} /><StatusBadge value={item.reviewed_coverage_ready ? "coverage_ready" : "coverage_gap"} /></div>
                <dl><div><dt>Profile fit</dt><dd>{Math.round(item.profile_match_score * 100)}%</dd></div><div><dt>Published routes</dt><dd>{item.pathway_count}</dd></div><div><dt>PR dependency</dt><dd>{pr?.status === "recorded" ? pr.summary : "Not recorded"}</dd></div><div><dt>Citizenship dependency</dt><dd>{citizenship?.status === "recorded" ? citizenship.summary : "Not recorded"}</dd></div></dl>
                <details><summary>Trade-offs and uncertainty</summary><ul>{[...item.tradeoffs, ...item.uncertainty.factors].map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul></details>
              </article>;
            })}</div>
          </>}
        </section>}

        {!leadId ? <EmptyState title="No lead selected" detail="Choose a lead to compare their current profile against published mobility pathways." /> : comparison ? <>
          {(candidate?.requires_acceptance || acceptances.length > 0) && <section className="panel reassessment-panel">
            <SectionTitle label="Explicit acceptance" title="Pinned reassessment control" detail="New profile or reviewed regulatory versions never refresh this assessment automatically." />
            {candidate?.requires_acceptance && <>
              <InlineNotice label="Assessment remains unchanged" detail={candidate.summary} tone="warn" />
              <div className="reassessment-options">
                {candidate.profile_update_available && <label className="profile-check"><input type="checkbox" checked={acceptProfile} onChange={(event) => setAcceptProfile(event.target.checked)} /><span><strong>Accept profile version {candidate.current_profile_version}</strong><small>Baseline remains profile version {candidate.baseline_profile_version} until execution.</small></span></label>}
                {candidate.regulatory_changes.map((change) => <label className="profile-check" key={change.impact_id}><input type="checkbox" checked={selectedImpacts.includes(change.impact_id)} onChange={(event) => setSelectedImpacts(event.target.checked ? [...selectedImpacts, change.impact_id] : selectedImpacts.filter((id) => id !== change.impact_id))} /><span><strong>{change.pathway_name} version {change.affected_pathway_version_number} → {change.replacement_pathway_version_number}</strong><small>{titleCase(change.materiality)} · reviewed by {change.reviewed_by}</small></span></label>)}
              </div>
              <div className="reassessment-form">
                <label>User acceptance attestation<textarea value={attestation} onChange={(event) => setAttestation(event.target.value)} placeholder="Record how and when the user explicitly accepted these exact versions." /></label>
                <label>Operator notes<textarea value={acceptanceNotes} onChange={(event) => setAcceptanceNotes(event.target.value)} placeholder="Add consultation and evidence notes." /></label>
                <button className="button secondary" disabled={recording || (!acceptProfile && selectedImpacts.length === 0) || attestation.trim().length < 10 || acceptanceNotes.trim().length < 3} onClick={() => void recordAcceptance()}>{recording ? "Recording…" : "Record explicit acceptance"}</button>
              </div>
            </>}
            {acceptances.length > 0 && <div className="reassessment-ledger"><strong>Acceptance ledger</strong>{acceptances.map((item) => <article key={item.id}><div><StatusBadge value={item.status} /><span>{item.accepted_profile_version ? `Profile v${item.accepted_profile_version}` : "Pinned profile"} · {item.accepted_pathway_version_ids.length} regulatory replacement{item.accepted_pathway_version_ids.length === 1 ? "" : "s"}</span></div><p>{item.user_attestation}</p><small>{new Date(item.accepted_at).toLocaleString()} · {item.recorded_by}</small>{item.status === "accepted" && <button className="button primary" disabled={executingId === item.id} onClick={() => void executeAcceptance(item.id)}>{executingId === item.id ? "Reassessing…" : "Execute accepted reassessment"}</button>}</article>)}</div>}
          </section>}
          <div className="metric-row planning-metrics">
            <MetricPill className="planning-metric-profile" label="Profile" value={selectedLead?.full_name || comparison.profile_id || "Not pinned"} />
            <MetricPill className="planning-metric-version" label="Profile version" value={comparison.profile_version ?? "Not pinned"} />
            <MetricPill className="planning-metric-alternatives" label="Alternatives" value={comparison.alternatives.length} />
            <MetricPill className="planning-metric-gaps" label="Evidence gaps" value={primary?.evidence_gaps.length || comparison.missing_evidence.length} tone={(primary?.evidence_gaps.length || comparison.missing_evidence.length) ? "warn" : "good"} />
            <MetricPill className="planning-metric-history" label="History" value={history.length} />
            <div className="metric-pill planning-metric-status"><span>Plan status</span><strong className="profile-status-value">{titleCase(comparison.status)}</strong></div>
            <div className="metric-pill planning-metric-consent"><span>Consent</span><strong className="profile-status-value">{titleCase(comparison.consent_status)}</strong></div>
          </div>
          <InlineNotice label="Human review required" detail={comparison.summary} tone={comparison.status === "restricted" ? "bad" : primary ? "warn" : "bad"} />
          {primary ? <div className="planning-layout">
            <section className="planning-results" aria-label="Pathway comparison results">
              <ComparisonCard item={primary} primary />
              {potentialAlternatives.length > 0 && <section><SectionTitle label="Potential alternatives" title="Other routes to examine" detail="Assessed against the same immutable profile version" /><div className="planning-alternatives">{potentialAlternatives.map((item) => <ComparisonCard key={item.pathway.id} item={item} />)}</div></section>}
              {excludedAlternatives.length > 0 && <section className="excluded-routes-section"><SectionTitle label="Excluded routes" title="Assessed but not compatible" detail="Retained for audit and explanation; these are not plausible alternatives" /><div className="planning-alternatives">{excludedAlternatives.map((item) => <ComparisonCard key={item.pathway.id} item={item} />)}</div></section>}
            </section>
            <aside className="planning-side">
              <section className="panel"><SectionTitle label="Evidence" title="Cross-pathway gaps" detail="Resolve these before a consultant recommendation" /><div className="planning-gap-list">{comparison.missing_evidence.length ? comparison.missing_evidence.map((gap) => <span key={gap}>{gap}</span>) : <p>No common evidence gaps were detected.</p>}</div></section>
              <section className="panel"><SectionTitle label="Audit" title="Comparison history" detail={`${history.length} immutable assessment${history.length === 1 ? "" : "s"}`} /><div className="planning-history">{history.map((item) => <article key={item.assessment_id || item.generated_at}><div><strong>{titleCase(item.status)}</strong><StatusBadge value={item.primary?.risk.level ? `${item.primary.risk.level}_risk` : item.status} /></div><p>{item.profile_version != null ? `Profile v${item.profile_version}` : "Legacy comparison · profile input not pinned"} · {item.alternatives.length} alternatives</p><small>{new Date(item.generated_at).toLocaleString()} · {item.generated_by}</small></article>)}</div></section>
              <div className="planning-links"><Link className="button secondary" href="/profiles">Update profile</Link><Link className="button secondary" href="/pathways">Manage catalogue</Link>{selectedLead && <Link className="button secondary" href={`/leads/${selectedLead.id}`}>Open lead</Link>}</div>
            </aside>
          </div> : <EmptyState title={comparison.status === "restricted" ? "Comparison restricted" : "No published pathway matches"} detail={comparison.summary} />}
        </> : <EmptyState title="No comparison yet" detail="Generate a comparison after the lead has a current profile and the catalogue contains published pathways." />}
      </div>
    </WorkspaceShell>
  );
}
