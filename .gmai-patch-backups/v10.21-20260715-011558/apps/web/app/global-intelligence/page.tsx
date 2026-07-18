"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  createJurisdictionCoverageBatch,
  getGlobalIntelligenceDashboard,
  getGlobalJurisdictionRegistry,
  getJurisdictionCoverageWorklist,
  getJurisdictionCoverageBaselineStatus,
  getHealthStatus,
  InitialRuleAssertion,
  InitialRulePublicationReceipt,
  GlobalIntelligenceChange,
  GlobalIntelligenceDashboard,
  GlobalJurisdictionRegistry,
  HealthStatus,
  JurisdictionCoverageBaselineStatus,
  JurisdictionCoverageEvidenceBatch,
  JurisdictionCoverageWorklist,
  listJurisdictionCoverageBatches,
  listInitialRuleAssertions,
  listOfficialSources,
  listRegulatoryAuthorities,
  OfficialSourceView,
  proposeInitialRuleAssertion,
  publishInitialRuleAssertion,
  queueJurisdictionCoverageBaselines,
  proposeJurisdictionImmigrationAssessment,
  proposeJurisdictionSourceCertification,
  RegulatoryAuthority,
  reviewInitialRuleAssertion,
  reviewJurisdictionImmigrationAssessment,
  reviewJurisdictionSourceCertification,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const TABS = ["overview", "coverage", "programmes", "processing", "occupations", "thresholds", "heatmap", "radar"] as const;
type Tab = typeof TABS[number];
type RuleRelationship = "independent" | "parent_inherited" | "shared_or_coordinated" | "not_applicable" | "unclear";

function formatDate(value: string | null | undefined) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function ChangeList({ items, empty }: { items: GlobalIntelligenceChange[]; empty: string }) {
  return <div className="global-change-list">{items.length ? items.map((item) => <article key={item.id}>
    <div><div><span>{item.country} · {titleCase(item.change_type)}</span><h3>{item.title}</h3></div><StatusBadge value={item.status} /></div>
    <p>{item.summary}</p>
    <div className="global-change-meta"><span>{titleCase(item.domain)}</span><span>{titleCase(item.materiality)}</span><span>{titleCase(item.freshness)}</span><span>{titleCase(item.coverage)}</span><span>{item.confidence === null ? "Confidence unknown" : `${Math.round(item.confidence * 100)}% confidence`}</span><span>{formatDate(item.detected_at)}</span></div>
    <small>{item.authority_name || item.source_name || "Source unavailable"}{item.reviewed_by ? ` · reviewed by ${item.reviewed_by}` : " · awaiting review"}</small>
  </article>) : <EmptyState title="No reviewed activity" detail={empty} />}</div>;
}

export default function GlobalIntelligencePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [dashboard, setDashboard] = useState<GlobalIntelligenceDashboard | null>(null);
  const [registry, setRegistry] = useState<GlobalJurisdictionRegistry | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [windowDays, setWindowDays] = useState(90);
  const [freshnessFilter, setFreshnessFilter] = useState("all");
  const [coverageFilter, setCoverageFilter] = useState("all");
  const [authorityFilter, setAuthorityFilter] = useState("all");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [materialityFilter, setMaterialityFilter] = useState("all");
  const [reviewStateFilter, setReviewStateFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registrySearch, setRegistrySearch] = useState("");
  const [registryType, setRegistryType] = useState("all");
  const [registryGap, setRegistryGap] = useState("all");
  const [selectedJurisdictionId, setSelectedJurisdictionId] = useState<string | null>(null);
  const [ruleRelationship, setRuleRelationship] = useState<RuleRelationship>("unclear");
  const [parentCode, setParentCode] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [evidenceTitle, setEvidenceTitle] = useState("");
  const [assessmentRationale, setAssessmentRationale] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [assessmentBusy, setAssessmentBusy] = useState(false);
  const [authorities, setAuthorities] = useState<RegulatoryAuthority[]>([]);
  const [officialSources, setOfficialSources] = useState<OfficialSourceView[]>([]);
  const [certificationAuthorityId, setCertificationAuthorityId] = useState("");
  const [certificationSourceId, setCertificationSourceId] = useState("");
  const [certificationDomains, setCertificationDomains] = useState("visa");
  const [certificationEvidence, setCertificationEvidence] = useState("");
  const [certificationReviewNotes, setCertificationReviewNotes] = useState("");
  const [coverageWorklist, setCoverageWorklist] = useState<JurisdictionCoverageWorklist | null>(null);
  const [coverageBatches, setCoverageBatches] = useState<JurisdictionCoverageEvidenceBatch[]>([]);
  const [coverageBaselineStatuses, setCoverageBaselineStatuses] = useState<Record<string, JurisdictionCoverageBaselineStatus>>({});
  const [coverageBaselineBusy, setCoverageBaselineBusy] = useState<string | null>(null);
  const [initialRuleAssertions, setInitialRuleAssertions] = useState<InitialRuleAssertion[]>([]);
  const [initialAssertionBatchId, setInitialAssertionBatchId] = useState("");
  const [initialAssertionCode, setInitialAssertionCode] = useState("");
  const [initialAssertionDomain, setInitialAssertionDomain] = useState("visa");
  const [initialAssertionTitle, setInitialAssertionTitle] = useState("");
  const [initialAssertionRuleKey, setInitialAssertionRuleKey] = useState("");
  const [initialAssertionStatement, setInitialAssertionStatement] = useState("");
  const [initialAssertionRationale, setInitialAssertionRationale] = useState("");
  const [initialAssertionExcerpt, setInitialAssertionExcerpt] = useState("");
  const [initialAssertionConfidence, setInitialAssertionConfidence] = useState("0.95");
  const [initialAssertionReviewNotes, setInitialAssertionReviewNotes] = useState<Record<string, string>>({});
  const [initialAssertionPublishNotes, setInitialAssertionPublishNotes] = useState<Record<string, string>>({});
  const [initialAssertionBusy, setInitialAssertionBusy] = useState<string | null>(null);
  const [initialAssertionPublicationReceipts, setInitialAssertionPublicationReceipts] = useState<Record<string, InitialRulePublicationReceipt>>({});
  const [coverageWorkGap, setCoverageWorkGap] = useState("all");
  const [coverageWorkRegion, setCoverageWorkRegion] = useState("all");
  const [coverageBatchName, setCoverageBatchName] = useState("Global coverage evidence batch");
  const [coverageBatchNotes, setCoverageBatchNotes] = useState("");
  const [coverageBatchJson, setCoverageBatchJson] = useState("[]");
  const [coverageBatchBusy, setCoverageBatchBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [healthResult, intelligence, registryResult, authorityResult, sourceResult, worklistResult, batchResult] = await Promise.all([
        getHealthStatus(), getGlobalIntelligenceDashboard(windowDays, {
          freshness: freshnessFilter,
          coverage: coverageFilter,
          authority_id: authorityFilter === "all" ? undefined : authorityFilter,
          confidence: confidenceFilter,
          materiality: materialityFilter,
          review_state: reviewStateFilter,
        }), getGlobalJurisdictionRegistry(),
        listRegulatoryAuthorities(), listOfficialSources(),
        getJurisdictionCoverageWorklist(coverageWorkGap, coverageWorkRegion, 100),
        listJurisdictionCoverageBatches(),
      ]);
      const baselineEntries = await Promise.all(
        batchResult.batches.slice(0, 8).map(async (batch) => {
          try {
            return [batch.id, await getJurisdictionCoverageBaselineStatus(batch.id)] as const;
          } catch {
            return null;
          }
        }),
      );
      const assertionEntries = await Promise.all(
        batchResult.batches.slice(0, 8).map(async (batch) => {
          try {
            return (await listInitialRuleAssertions(batch.id)).assertions;
          } catch {
            return [];
          }
        }),
      );
      setHealth(healthResult.data); setDashboard(intelligence); setRegistry(registryResult);
      setAuthorities(authorityResult.authorities); setOfficialSources(sourceResult.sources);
      setCoverageWorklist(worklistResult); setCoverageBatches(batchResult.batches);
      setCoverageBaselineStatuses(Object.fromEntries(baselineEntries.filter(Boolean) as Array<readonly [string, JurisdictionCoverageBaselineStatus]>));
      setInitialRuleAssertions(assertionEntries.flat());
      if (!initialAssertionBatchId && batchResult.batches.length) setInitialAssertionBatchId(batchResult.batches[0].id);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load global intelligence"); }
    finally { setLoading(false); }
  }, [authorityFilter, confidenceFilter, coverageFilter, coverageWorkGap, coverageWorkRegion, freshnessFilter, initialAssertionBatchId, materialityFilter, reviewStateFilter, windowDays]);

  useEffect(() => { void load(); }, [load]);
  const filteredRegistry = useMemo(() => {
    const query = registrySearch.trim().toLowerCase();
    return (registry?.entries || []).filter((entry) => {
      const matchesSearch = !query || `${entry.name} ${entry.alpha2_code} ${entry.alpha3_code}`.toLowerCase().includes(query);
      const matchesType = registryType === "all" || entry.jurisdiction_type === registryType;
      const matchesGap = registryGap === "all" || (registryGap === "ready" ? entry.coverage_ready : entry.missing.includes(registryGap));
      return matchesSearch && matchesType && matchesGap;
    });
  }, [registry, registryGap, registrySearch, registryType]);
  const selectedRegistryEntry = registry?.entries.find((entry) => entry.jurisdiction_id === selectedJurisdictionId) || null;
  const selectedAuthorities = authorities.filter((authority) => authority.jurisdiction_id === selectedJurisdictionId);
  const jurisdictionSources = officialSources.filter((source) => source.jurisdiction_id === selectedJurisdictionId);
  const selectedSources = jurisdictionSources.filter((source) =>
    (!certificationAuthorityId || source.regulatory_authority_id === certificationAuthorityId)
  );
  const initialAssertionEligibleItems = (coverageBaselineStatuses[initialAssertionBatchId]?.items || [])
    .filter((item) => item.state === "baseline_ready");
  const coverageBatchDraftCount = useMemo(() => {
    try {
      const parsed = JSON.parse(coverageBatchJson) as unknown;
      const items = Array.isArray(parsed)
        ? parsed
        : typeof parsed === "object" && parsed !== null && "items" in parsed
          ? (parsed as { items: unknown }).items
          : null;
      return Array.isArray(items) ? items.length : 0;
    } catch {
      return 0;
    }
  }, [coverageBatchJson]);

  async function proposeAssessment() {
    if (!selectedRegistryEntry) return;
    setAssessmentBusy(true); setError(null);
    try {
      await proposeJurisdictionImmigrationAssessment(selectedRegistryEntry.jurisdiction_id, {
        rule_relationship: ruleRelationship,
        parent_code: parentCode.trim() || null,
        evidence_url: evidenceUrl.trim(),
        evidence_title: evidenceTitle.trim(),
        rationale: assessmentRationale.trim(),
      });
      setEvidenceUrl(""); setEvidenceTitle(""); setAssessmentRationale(""); setParentCode("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not propose immigration-rule assessment"); }
    finally { setAssessmentBusy(false); }
  }

  async function reviewAssessment(decision: "approved" | "rejected") {
    const pending = selectedRegistryEntry?.pending_assessment;
    if (!pending) return;
    setAssessmentBusy(true); setError(null);
    try {
      await reviewJurisdictionImmigrationAssessment(pending.id, decision, reviewNotes.trim());
      setReviewNotes("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not review immigration-rule assessment"); }
    finally { setAssessmentBusy(false); }
  }

  async function proposeSourceCertification() {
    if (!selectedRegistryEntry) return;
    setAssessmentBusy(true); setError(null);
    try {
      await proposeJurisdictionSourceCertification(selectedRegistryEntry.jurisdiction_id, {
        regulatory_authority_id: certificationAuthorityId,
        official_source_id: certificationSourceId,
        coverage_domains: certificationDomains.split(",").map((domain) => domain.trim()).filter(Boolean),
        evidence_notes: certificationEvidence.trim(),
      });
      setCertificationEvidence(""); setCertificationReviewNotes("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not propose primary-source certification"); }
    finally { setAssessmentBusy(false); }
  }

  async function reviewSourceCertification(decision: "approved" | "rejected") {
    const pending = selectedRegistryEntry?.pending_source_certification;
    if (!pending) return;
    setAssessmentBusy(true); setError(null);
    try {
      await reviewJurisdictionSourceCertification(pending.id, decision, certificationReviewNotes.trim());
      setCertificationReviewNotes("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not review primary-source certification"); }
    finally { setAssessmentBusy(false); }
  }

  async function queueCoverageBaselines(batchId: string) {
    setCoverageBaselineBusy(batchId); setError(null);
    try {
      const result = await queueJurisdictionCoverageBaselines(batchId);
      setCoverageBaselineStatuses((current) => ({ ...current, [batchId]: result }));
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not queue approved source baselines"); }
    finally { setCoverageBaselineBusy(null); }
  }

  async function submitCoverageBatch() {
    setCoverageBatchBusy(true); setError(null);
    try {
      const parsed = JSON.parse(coverageBatchJson) as unknown;
      const items = Array.isArray(parsed) ? parsed : typeof parsed === "object" && parsed !== null && "items" in parsed
        ? (parsed as { items: unknown }).items
        : null;
      if (!Array.isArray(items)) throw new Error("Batch JSON must be an array or an object containing an items array.");
      await createJurisdictionCoverageBatch({
        name: coverageBatchName.trim(),
        notes: coverageBatchNotes.trim(),
        items: items as Parameters<typeof createJurisdictionCoverageBatch>[0]["items"],
      });
      setCoverageBatchNotes("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not submit coverage evidence batch"); }
    finally { setCoverageBatchBusy(false); }
  }

  async function submitInitialRuleAssertion() {
    if (!initialAssertionBatchId || !initialAssertionCode) return;
    setInitialAssertionBusy("create"); setError(null);
    try {
      await proposeInitialRuleAssertion(initialAssertionBatchId, {
        alpha2_code: initialAssertionCode,
        domain: initialAssertionDomain.trim(),
        title: initialAssertionTitle.trim(),
        rule_key: initialAssertionRuleKey.trim(),
        statement: initialAssertionStatement.trim(),
        rationale: initialAssertionRationale.trim(),
        evidence_excerpt: initialAssertionExcerpt.trim(),
        confidence: Number(initialAssertionConfidence),
      });
      setInitialAssertionTitle(""); setInitialAssertionRuleKey(""); setInitialAssertionStatement("");
      setInitialAssertionRationale(""); setInitialAssertionExcerpt("");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create initial rule assertion"); }
    finally { setInitialAssertionBusy(null); }
  }

  async function decideInitialRuleAssertion(assertionId: string, decision: "approved" | "rejected") {
    setInitialAssertionBusy(assertionId); setError(null);
    try {
      await reviewInitialRuleAssertion(assertionId, decision, (initialAssertionReviewNotes[assertionId] || "").trim());
      setInitialAssertionReviewNotes((current) => ({ ...current, [assertionId]: "" }));
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not review initial rule assertion"); }
    finally { setInitialAssertionBusy(null); }
  }

  async function publishReviewedInitialRule(assertionId: string) {
    setInitialAssertionBusy(assertionId); setError(null);
    try {
      const result = await publishInitialRuleAssertion(assertionId, (initialAssertionPublishNotes[assertionId] || "").trim());
      setInitialAssertionPublicationReceipts((current) => ({
        ...current,
        [assertionId]: result.coverage_receipt,
      }));
      setInitialAssertionPublishNotes((current) => ({ ...current, [assertionId]: "" }));
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not publish initial verified rule"); }
    finally { setInitialAssertionBusy(null); }
  }

  function selectRegistryEntry(jurisdictionId: string) {
    setSelectedJurisdictionId(jurisdictionId);
    const firstSource = officialSources.find((source) =>
      source.jurisdiction_id === jurisdictionId && source.regulatory_authority_id
    );
    const firstAuthority = authorities.find((authority) => authority.id === firstSource?.regulatory_authority_id)
      || authorities.find((authority) => authority.jurisdiction_id === jurisdictionId);
    setCertificationAuthorityId(firstAuthority?.id || "");
    setCertificationSourceId(firstSource?.id || "");
  }
  const activeFilterCount = [freshnessFilter, coverageFilter, authorityFilter, confidenceFilter, materialityFilter, reviewStateFilter]
    .filter((value) => value !== "all").length;
  function clearIntelligenceFilters() {
    setFreshnessFilter("all");
    setCoverageFilter("all");
    setAuthorityFilter("all");
    setConfidenceFilter("all");
    setMaterialityFilter("all");
    setReviewStateFilter("all");
  }
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  return <WorkspaceShell health={health}>
    <Topbar title="Global Intelligence" kicker="Reviewed mobility activity worldwide" loadStatus={loadStatus} onRefresh={load} />
    <div className="page-pad global-intelligence-page">
      {error && <InlineNotice label="Global intelligence error" detail={error} tone="bad" />}
      <section className="panel global-intelligence-hero">
        <div><span className="page-kicker">Self-updating intelligence</span><h2>Official changes become visible here only with provenance and review state.</h2><p>Monitoring views include pending changes. Opportunity signals use human-published events only.</p></div>
        <label>Activity window<select value={windowDays} onChange={(event) => setWindowDays(Number(event.target.value))}><option value={30}>30 days</option><option value={90}>90 days</option><option value={180}>180 days</option><option value={365}>365 days</option></select></label>
      </section>
      {dashboard && <section className="panel global-filter-panel" aria-label="Global intelligence filters">
        <div className="global-filter-heading">
          <div><span className="eyebrow">Evidence controls</span><h3>Filter the complete dashboard</h3><p>Every count, change list, heatmap total, and radar signal uses the same selected evidence scope.</p></div>
          <div><strong>{dashboard.filters.matched_changes}</strong><span>of {dashboard.filters.available_changes} changes</span>{activeFilterCount > 0 && <button className="button secondary" onClick={clearIntelligenceFilters}>Clear {activeFilterCount} filters</button>}</div>
        </div>
        <div className="global-filter-grid">
          <label>Freshness<select value={freshnessFilter} onChange={(event) => setFreshnessFilter(event.target.value)}><option value="all">All freshness</option>{Object.entries(dashboard.filters.options.freshness).map(([value, count]) => <option key={value} value={value}>{titleCase(value)} ({count})</option>)}</select></label>
          <label>Coverage<select value={coverageFilter} onChange={(event) => setCoverageFilter(event.target.value)}><option value="all">All coverage</option>{Object.entries(dashboard.filters.options.coverage).map(([value, count]) => <option key={value} value={value}>{titleCase(value)} ({count})</option>)}</select></label>
          <label>Authority<select value={authorityFilter} onChange={(event) => setAuthorityFilter(event.target.value)}><option value="all">All authorities</option>{dashboard.filters.options.authorities.map((authority) => <option key={authority.id} value={authority.id}>{authority.name} ({authority.count})</option>)}</select></label>
          <label>Confidence<select value={confidenceFilter} onChange={(event) => setConfidenceFilter(event.target.value)}><option value="all">All confidence</option>{Object.entries(dashboard.filters.options.confidence).map(([value, count]) => <option key={value} value={value}>{titleCase(value)} ({count})</option>)}</select></label>
          <label>Materiality<select value={materialityFilter} onChange={(event) => setMaterialityFilter(event.target.value)}><option value="all">All materiality</option>{Object.entries(dashboard.filters.options.materiality).map(([value, count]) => <option key={value} value={value}>{titleCase(value)} ({count})</option>)}</select></label>
          <label>Review state<select value={reviewStateFilter} onChange={(event) => setReviewStateFilter(event.target.value)}><option value="all">All review states</option>{Object.entries(dashboard.filters.options.review_state).map(([value, count]) => <option key={value} value={value}>{titleCase(value)} ({count})</option>)}</select></label>
        </div>
      </section>}
      {dashboard && <>
        <InlineNotice label={dashboard.scope.global_coverage_claim_ready ? "Global registry ready" : "Coverage expansion in progress"} detail={dashboard.scope.coverage_warning} tone={dashboard.scope.global_coverage_claim_ready ? "good" : "warn"} />
        <div className="metric-row global-intelligence-metrics">
          <MetricPill label="New programmes" value={dashboard.counts.new_programs || 0} />
          <MetricPill label="Countries today" value={dashboard.today.countries_updated} />
          <MetricPill label="Changes today" value={dashboard.today.changes_detected} />
          <MetricPill label="Processing updates" value={dashboard.counts.processing_time_changes || 0} />
          <MetricPill label="Occupation updates" value={dashboard.counts.occupation_list_changes || 0} />
          <MetricPill label="Verified rules" value={dashboard.scope.active_verified_rules} />
          <MetricPill label="Registry entries" value={dashboard.scope.registry_entries} />
        </div>
        <nav className="intelligence-tabs global-tabs" aria-label="Global intelligence views">{TABS.map((item) => <button className={tab === item ? "active" : ""} key={item} onClick={() => setTab(item)}>{titleCase(item)}</button>)}</nav>

        {tab === "overview" && <div className="global-overview-grid">
          <section className="panel"><SectionTitle label="Today" title={`${dashboard.today.countries_updated} countries updated`} detail={`${dashboard.today.changes_detected} detected official-source changes`} /><div className="global-country-tags">{dashboard.today.country_names.length ? dashboard.today.country_names.map((country) => <span key={country}>{country}</span>) : <p>No country changes detected today.</p>}</div></section>
          <section className="panel"><SectionTitle label="Change mix" title={`${dashboard.counts.changes || 0} events in ${dashboard.window_days} days`} detail="Includes pending, reviewed, and published events" /><div className="global-count-grid">{Object.entries(dashboard.change_type_counts).map(([key, value]) => <article key={key}><strong>{value}</strong><span>{titleCase(key)}</span></article>)}</div></section>
          <section className="panel global-overview-wide"><SectionTitle label="Recent immigration intelligence" title="Latest detected changes" detail="Review state remains visible on every event" /><ChangeList items={dashboard.immigration_changes.slice(0, 8)} empty="The monitoring pipeline has not detected changes in this window." /></section>
        </div>}
        {tab === "coverage" && <div className="global-registry-stack">
          <section className="panel">
            <SectionTitle label="Canonical registry" title={registry?.release?.version || "No active registry release"} detail="UN M49 country and area scope; immigration coverage is measured separately" />
            {registry && <>
              <div className="global-registry-metrics">
                <article><strong>{registry.summary.registry_entries}</strong><span>registry entries</span></article>
                <article><strong>{registry.summary.un_members || 0}</strong><span>UN members</span></article>
                <article><strong>{registry.summary.un_observers || 0}</strong><span>UN observers</span></article>
                <article><strong>{registry.summary.territories || 0}</strong><span>territories</span></article>
                <article><strong>{registry.summary.autonomous_jurisdictions || 0}</strong><span>autonomous</span></article>
                <article><strong>{registry.summary.coverage_ready || 0}/{registry.summary.coverage_required}</strong><span>coverage ready</span></article>
              </div>
              <InlineNotice label={registry.release_gate.global_coverage_claim_ready ? "Global coverage gate passed" : "Global coverage gate blocked"} detail={registry.release_gate.message || "Coverage gate status is unavailable."} tone={registry.release_gate.global_coverage_claim_ready ? "good" : "warn"} />
              <div className="registry-gate-grid">
                {Object.entries(registry.release_gate).filter(([key]) => key.endsWith("_complete")).map(([key, value]) => <article key={key}><StatusBadge value={value ? "ready" : "blocked"} /><span>{titleCase(key)}</span></article>)}
              </div>
            </>}
          </section>
          <section className="panel">
            <SectionTitle label="Regional posture" title="Registry and verified coverage" detail="A listed jurisdiction remains a gap until every evidence gate passes" />
            <div className="registry-region-grid">{registry?.regions.map((region) => <article key={region.region}><strong>{region.region}</strong><span>{region.entries} entries</span><b>{region.coverage_ready}/{region.coverage_required}</b><small>coverage ready</small></article>)}</div>
          </section>
          <section className="panel coverage-operations-panel">
            <SectionTitle label="Coverage operations" title="Evidence worklist and controlled batch submission" detail="Onboard authorities, official sources, and monitors in the same atomic package while preserving independent certification review" />
            <div className="coverage-operations-metrics">
              <article><strong>{coverageWorklist?.total || 0}</strong><span>filtered work items</span></article>
              <article><strong>{registry?.summary.assessments_pending_review || 0}</strong><span>assessments pending</span></article>
              <article><strong>{registry?.summary.source_certifications_pending_review || 0}</strong><span>certifications pending</span></article>
              <article><strong>{coverageBatches.length}</strong><span>recent evidence batches</span></article>
            </div>
            <div className="coverage-operations-grid">
              <div className="coverage-worklist-card">
                <div className="coverage-card-heading"><div><span>Prioritized queue</span><h3>Remaining Phase 10B evidence work</h3></div><small>First 100 matching jurisdictions</small></div>
                <div className="coverage-worklist-filters">
                  <label>Gap<select value={coverageWorkGap} onChange={(event) => setCoverageWorkGap(event.target.value)}><option value="all">All gaps</option><option value="immigration_rule_assessment">Immigration-rule assessment</option><option value="reviewed_primary_authority">Primary authority certification</option><option value="reviewed_primary_source">Primary source certification</option><option value="authority">Authority onboarding</option><option value="official_source">Official-source onboarding</option><option value="fresh_monitor">Fresh monitor</option><option value="verified_rule">Verified rule</option></select></label>
                  <label>Region<select value={coverageWorkRegion} onChange={(event) => setCoverageWorkRegion(event.target.value)}><option value="all">All regions</option>{registry?.regions.map((region) => <option key={region.region} value={region.region}>{region.region}</option>)}</select></label>
                </div>
                <div className="coverage-worklist-rows">{coverageWorklist?.items.slice(0, 12).map((item) => <button key={item.jurisdiction_id} onClick={() => selectRegistryEntry(item.jurisdiction_id)}><span><strong>{item.name}</strong><small>{item.alpha2_code} · {item.region || "Unassigned"}</small></span><span>{item.missing.slice(0, 2).map((gap) => <StatusBadge key={gap} value={gap} />)}</span></button>)}{!coverageWorklist?.items.length && <EmptyState title="No matching work items" detail="Change the gap or region filter, or refresh after the active registry is imported." />}</div>
              </div>
              <div className="coverage-batch-card">
                <div className="coverage-card-heading"><div><span>Controlled evidence package</span><h3>Onboard and submit up to 50 jurisdictions</h3></div><StatusBadge value="human_review_required" /></div>
                <label>Batch name<input value={coverageBatchName} onChange={(event) => setCoverageBatchName(event.target.value)} /></label>
                <label>Submission notes<textarea placeholder="Describe the evidence collection scope, source checks, and reviewer handoff." value={coverageBatchNotes} onChange={(event) => setCoverageBatchNotes(event.target.value)} /></label>
                <label>Evidence JSON<textarea className="coverage-batch-json" spellCheck={false} value={coverageBatchJson} onChange={(event) => setCoverageBatchJson(event.target.value)} /></label>
                <button className="button primary" disabled={coverageBatchBusy || coverageBatchName.trim().length < 3 || coverageBatchNotes.trim().length < 10} onClick={() => void submitCoverageBatch()}>{coverageBatchBusy ? "Submitting…" : "Create pending-review proposals"}</button>
                <small>Source onboarding creates or updates the authority, official source, and monitor atomically. Certification remains pending until a different authenticated reviewer approves it.</small>
              </div>
            </div>
            <div className="coverage-batch-history">
              <div className="coverage-card-heading"><div><span>Immutable submissions</span><h3>Recent evidence batches</h3></div><small>{coverageBatches.length} loaded</small></div>
              {coverageBatches.length ? <div className="coverage-batch-list">{coverageBatches.slice(0, 8).map((batch) => { const baseline = coverageBaselineStatuses[batch.id]; return <article key={batch.id}><div><strong>{batch.name}</strong><StatusBadge value={batch.status} /></div><p>{batch.notes}</p><small>{batch.item_count} jurisdictions · {batch.source_onboarding_count || 0} sources onboarded · {batch.immigration_assessment_count} assessments · {batch.source_certification_count} certifications · submitted by {batch.submitted_by}</small><div className="coverage-batch-review-counts"><span>{batch.review_counts.pending_review || 0} pending</span><span>{batch.review_counts.approved || 0} approved</span><span>{batch.review_counts.rejected || 0} rejected</span></div>{baseline && <div className="coverage-baseline-summary"><span>{baseline.baseline_ready} baselines ready</span><span>{baseline.in_progress} running</span><span>{baseline.failed} failed</span><span>{baseline.eligible_to_queue} ready to queue</span><button className="button secondary" disabled={coverageBaselineBusy === batch.id || baseline.eligible_to_queue === 0} onClick={() => void queueCoverageBaselines(batch.id)}>{coverageBaselineBusy === batch.id ? "Queueing…" : "Capture approved baselines"}</button><small>{baseline.safety.message}</small></div>}</article>; })}</div> : <EmptyState title="No evidence batches" detail="Use the controlled evidence package to create the first immutable batch." />}
            </div>
            <div className="coverage-initial-rules">
              <div className="coverage-card-heading"><div><span>Baseline rule governance</span><h3>Initial verified-rule assertions</h3></div><StatusBadge value="human_review_required" /></div>
              <InlineNotice label="Not a detected change" detail="Draft only what the immutable baseline snapshot explicitly supports. A different reviewer must approve it, and publication is a separate action." tone="warn" />
              <div className="coverage-initial-rule-grid">
                <div className="coverage-initial-rule-form">
                  <label>Evidence batch<select value={initialAssertionBatchId} onChange={(event) => { setInitialAssertionBatchId(event.target.value); setInitialAssertionCode(""); }}><option value="">Select batch</option>{coverageBatches.slice(0, 8).map((batch) => <option key={batch.id} value={batch.id}>{batch.name}</option>)}</select></label>
                  <label>Baseline jurisdiction<select value={initialAssertionCode} onChange={(event) => setInitialAssertionCode(event.target.value)}><option value="">Select baseline</option>{initialAssertionEligibleItems.map((item) => <option key={item.batch_item_id} value={item.alpha2_code}>{item.alpha2_code}</option>)}</select></label>
                  <label>Domain<input value={initialAssertionDomain} onChange={(event) => setInitialAssertionDomain(event.target.value)} /></label>
                  <label>Confidence<input type="number" min="0.9" max="1" step="0.01" value={initialAssertionConfidence} onChange={(event) => setInitialAssertionConfidence(event.target.value)} /></label>
                  <label className="coverage-initial-rule-wide">Title<input placeholder="Human-readable assertion title" value={initialAssertionTitle} onChange={(event) => setInitialAssertionTitle(event.target.value)} /></label>
                  <label>Rule key<input placeholder="residence_permit_authority" value={initialAssertionRuleKey} onChange={(event) => setInitialAssertionRuleKey(event.target.value)} /></label>
                  <label className="coverage-initial-rule-wide">Verified statement<textarea placeholder="State only the rule supported by the exact baseline snapshot" value={initialAssertionStatement} onChange={(event) => setInitialAssertionStatement(event.target.value)} /></label>
                  <label className="coverage-initial-rule-wide">Evidence excerpt<textarea placeholder="Paste the specific baseline excerpt the reviewer must verify" value={initialAssertionExcerpt} onChange={(event) => setInitialAssertionExcerpt(event.target.value)} /></label>
                  <label className="coverage-initial-rule-wide">Rationale<textarea placeholder="Explain how the excerpt supports the statement without inferring beyond the source" value={initialAssertionRationale} onChange={(event) => setInitialAssertionRationale(event.target.value)} /></label>
                  <button className="button primary coverage-initial-rule-wide" disabled={initialAssertionBusy === "create" || !initialAssertionBatchId || !initialAssertionCode || initialAssertionTitle.trim().length < 5 || initialAssertionRuleKey.trim().length < 2 || initialAssertionStatement.trim().length < 10 || initialAssertionExcerpt.trim().length < 10 || initialAssertionRationale.trim().length < 10 || Number(initialAssertionConfidence) < 0.9} onClick={() => void submitInitialRuleAssertion()}>{initialAssertionBusy === "create" ? "Submitting…" : "Submit assertion for independent review"}</button>
                </div>
                <div className="coverage-initial-rule-list">
                  {initialRuleAssertions.length ? initialRuleAssertions.map((assertion) => {
                    const coverageEntry = registry?.entries.find((entry) => entry.jurisdiction_id === assertion.jurisdiction_id);
                    const publicationReceipt = initialAssertionPublicationReceipts[assertion.id];
                    return <article key={assertion.id}>
                      <div><div><span>{assertion.alpha2_code || "—"} · {titleCase(assertion.domain)}</span><h4>{assertion.title}</h4></div><StatusBadge value={assertion.status} /></div>
                      <p>{assertion.statement}</p>
                      <blockquote>{assertion.evidence_excerpt}</blockquote>
                      <small>{Math.round(assertion.confidence * 100)}% confidence · snapshot {assertion.snapshot?.id.slice(0, 8) || "missing"} · proposed by {assertion.proposed_by}</small>
                      {assertion.status === "pending_review" && <div className="coverage-initial-rule-action"><textarea placeholder="Independent review notes" value={initialAssertionReviewNotes[assertion.id] || ""} onChange={(event) => setInitialAssertionReviewNotes((current) => ({ ...current, [assertion.id]: event.target.value }))} /><div><button className="button primary" disabled={initialAssertionBusy === assertion.id || (initialAssertionReviewNotes[assertion.id] || "").trim().length < 3} onClick={() => void decideInitialRuleAssertion(assertion.id, "approved")}>Approve</button><button className="button danger" disabled={initialAssertionBusy === assertion.id || (initialAssertionReviewNotes[assertion.id] || "").trim().length < 3} onClick={() => void decideInitialRuleAssertion(assertion.id, "rejected")}>Reject</button></div></div>}
                      {assertion.status === "approved" && <div className="coverage-initial-rule-action"><textarea placeholder="Publication notes and attestation basis" value={initialAssertionPublishNotes[assertion.id] || ""} onChange={(event) => setInitialAssertionPublishNotes((current) => ({ ...current, [assertion.id]: event.target.value }))} /><button className="button primary" disabled={initialAssertionBusy === assertion.id || (initialAssertionPublishNotes[assertion.id] || "").trim().length < 3} onClick={() => void publishReviewedInitialRule(assertion.id)}>Publish verified rule</button></div>}
                      {assertion.status === "published" && <div className="coverage-publication-receipt">
                        <div><StatusBadge value={coverageEntry?.coverage_ready ? "coverage_ready" : "coverage_gap"} /><strong>{coverageEntry?.coverage_ready ? "Jurisdiction coverage ready" : "Verified rule published"}</strong></div>
                        <small>Published rule {assertion.verified_rule?.id.slice(0, 8)} · no source change event created.</small>
                        {!coverageEntry?.coverage_ready && <small>Remaining gates: {coverageEntry?.missing.map((gap) => titleCase(gap)).join(", ") || "refresh registry coverage"}.</small>}
                        {publicationReceipt && <small>{publicationReceipt.message}</small>}
                      </div>}
                    </article>;
                  }) : <EmptyState title="No initial rule assertions" detail="An independently approved jurisdiction with an immutable baseline snapshot can be submitted for review here." />}
                </div>
              </div>
            </div>
            <InlineNotice label="Coverage claim remains blocked" detail={coverageWorklist?.safety.message || "Evidence proposals require independent human review and do not establish global coverage."} tone="warn" />
          </section>
          <section className="panel">
            <SectionTitle label="Coverage ledger" title={`${filteredRegistry.length} visible jurisdictions`} detail="Search canonical scope and isolate specific evidence gaps" />
            <div className="registry-filters">
              <input aria-label="Search jurisdictions" placeholder="Search name or code" value={registrySearch} onChange={(event) => setRegistrySearch(event.target.value)} />
              <select aria-label="Jurisdiction type" value={registryType} onChange={(event) => setRegistryType(event.target.value)}><option value="all">All types</option><option value="country">Countries</option><option value="territory">Territories</option><option value="autonomous_jurisdiction">Autonomous jurisdictions</option></select>
              <select aria-label="Coverage gap" value={registryGap} onChange={(event) => setRegistryGap(event.target.value)}><option value="all">All coverage states</option><option value="ready">Coverage ready</option><option value="reviewed_primary_authority">Primary authority not certified</option><option value="reviewed_primary_source">Primary source not certified</option><option value="fresh_monitor">Certified source not fresh</option><option value="verified_rule">Missing verified rule</option><option value="immigration_rule_assessment">Rule status unassessed</option></select>
            </div>
            {selectedRegistryEntry && <div className="registry-assessment-workspace">
              <div className="registry-assessment-heading"><div><span>Immigration-rule assessment</span><h3>{selectedRegistryEntry.name} ({selectedRegistryEntry.alpha2_code})</h3></div><button className="button secondary" onClick={() => setSelectedJurisdictionId(null)}>Close</button></div>
              {selectedRegistryEntry.approved_assessment && <article className="registry-approved-assessment"><div><StatusBadge value="approved" /><strong>{titleCase(selectedRegistryEntry.approved_assessment.rule_relationship)}</strong></div><p>{selectedRegistryEntry.approved_assessment.rationale}</p><a href={selectedRegistryEntry.approved_assessment.evidence_url} target="_blank" rel="noreferrer">{selectedRegistryEntry.approved_assessment.evidence_title}</a><small>Reviewed by {selectedRegistryEntry.approved_assessment.reviewed_by || "unknown"}</small></article>}
              {selectedRegistryEntry.pending_assessment ? <article className="registry-pending-assessment"><div><StatusBadge value="pending_review" /><strong>{titleCase(selectedRegistryEntry.pending_assessment.rule_relationship)}</strong></div><p>{selectedRegistryEntry.pending_assessment.rationale}</p><a href={selectedRegistryEntry.pending_assessment.evidence_url} target="_blank" rel="noreferrer">{selectedRegistryEntry.pending_assessment.evidence_title}</a><small>Proposed by {selectedRegistryEntry.pending_assessment.proposed_by}. A different authenticated reviewer must decide.</small><textarea placeholder="Review notes" value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} /><div><button className="button primary" disabled={assessmentBusy || reviewNotes.trim().length < 3} onClick={() => void reviewAssessment("approved")}>Approve assessment</button><button className="button danger" disabled={assessmentBusy || reviewNotes.trim().length < 3} onClick={() => void reviewAssessment("rejected")}>Reject</button></div></article> : <div className="registry-assessment-form">
                <label>Rule relationship<select value={ruleRelationship} onChange={(event) => setRuleRelationship(event.target.value as RuleRelationship)}><option value="unclear">Unclear</option><option value="independent">Independent</option><option value="parent_inherited">Inherited from parent</option><option value="shared_or_coordinated">Shared or coordinated</option><option value="not_applicable">Not applicable</option></select></label>
                {(ruleRelationship === "parent_inherited" || ruleRelationship === "shared_or_coordinated") && <label>Parent code<input maxLength={12} placeholder="e.g. GB" value={parentCode} onChange={(event) => setParentCode(event.target.value.toUpperCase())} /></label>}
                <label>Official evidence URL<input placeholder="https://government.example/..." value={evidenceUrl} onChange={(event) => setEvidenceUrl(event.target.value)} /></label>
                <label>Evidence title<input placeholder="Official immigration framework" value={evidenceTitle} onChange={(event) => setEvidenceTitle(event.target.value)} /></label>
                <label className="registry-assessment-wide">Evidence-based rationale<textarea placeholder="Explain exactly what the official evidence establishes" value={assessmentRationale} onChange={(event) => setAssessmentRationale(event.target.value)} /></label>
                <div className="registry-assessment-wide"><button className="button primary" disabled={assessmentBusy || evidenceUrl.trim().length < 8 || evidenceTitle.trim().length < 3 || assessmentRationale.trim().length < 10} onClick={() => void proposeAssessment()}>Submit for independent review</button></div>
              </div>}
              <div className="registry-certification-section">
                <div><span>Primary authority and source</span><h3>Reviewed coverage certification</h3></div>
                {selectedRegistryEntry.approved_source_certification && <article className="registry-approved-assessment"><div><StatusBadge value="approved" /><strong>Primary immigration source certified</strong></div><p>{selectedRegistryEntry.approved_source_certification.evidence_notes}</p><small>Reviewed by {selectedRegistryEntry.approved_source_certification.reviewed_by || "unknown"} · domains: {selectedRegistryEntry.approved_source_certification.coverage_domains.join(", ")}</small></article>}
                {selectedRegistryEntry.pending_source_certification ? <article className="registry-pending-assessment"><div><StatusBadge value="pending_review" /><strong>Primary source certification pending</strong></div><p>{selectedRegistryEntry.pending_source_certification.evidence_notes}</p><small>Proposed by {selectedRegistryEntry.pending_source_certification.proposed_by}. A different authenticated reviewer must decide.</small><textarea placeholder="Certification review notes" value={certificationReviewNotes} onChange={(event) => setCertificationReviewNotes(event.target.value)} /><div><button className="button primary" disabled={assessmentBusy || certificationReviewNotes.trim().length < 3} onClick={() => void reviewSourceCertification("approved")}>Approve certification</button><button className="button danger" disabled={assessmentBusy || certificationReviewNotes.trim().length < 3} onClick={() => void reviewSourceCertification("rejected")}>Reject</button></div></article> : selectedAuthorities.length && jurisdictionSources.length ? <div className="registry-assessment-form">
                  <label>Regulatory authority<select value={certificationAuthorityId} onChange={(event) => { const authorityId = event.target.value; setCertificationAuthorityId(authorityId); setCertificationSourceId(officialSources.find((source) => source.jurisdiction_id === selectedJurisdictionId && source.regulatory_authority_id === authorityId)?.id || ""); }}><option value="">Select authority</option>{selectedAuthorities.map((authority) => <option key={authority.id} value={authority.id}>{authority.name}</option>)}</select></label>
                  <label>Official source<select value={certificationSourceId} onChange={(event) => setCertificationSourceId(event.target.value)}><option value="">Select source</option>{selectedSources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>
                  <label>Coverage domains<input placeholder="visa, work, settlement" value={certificationDomains} onChange={(event) => setCertificationDomains(event.target.value)} /></label>
                  <label className="registry-assessment-wide">Certification evidence notes<textarea placeholder="Explain authority ownership, official status, scope, and why this is the primary source" value={certificationEvidence} onChange={(event) => setCertificationEvidence(event.target.value)} /></label>
                  <div className="registry-assessment-wide"><button className="button primary" disabled={assessmentBusy || !certificationAuthorityId || !certificationSourceId || certificationEvidence.trim().length < 10} onClick={() => void proposeSourceCertification()}>Submit certification for review</button></div>
                </div> : <InlineNotice label="Source onboarding required" detail="Onboard an authority, official source, and monitor in Regulatory Operations before proposing primary-source certification." tone="warn" />}
                <Link className="button secondary registry-operations-link" href="/intelligence">Open source onboarding</Link>
              </div>
            </div>}
            <div className="registry-table-wrap"><table className="registry-table"><thead><tr><th>Jurisdiction</th><th>Type</th><th>Region</th><th>Relationship</th><th>Primary authority</th><th>Primary source</th><th>Monitor</th><th>Rule</th><th>Coverage</th><th>Action</th></tr></thead><tbody>{filteredRegistry.map((entry) => <tr key={entry.id}><td><strong>{entry.name}</strong><small>{entry.alpha2_code} / {entry.alpha3_code} / {entry.m49_code}</small></td><td>{titleCase(entry.jurisdiction_type)}</td><td>{entry.region || "Unassigned"}<small>{entry.subregion}</small></td><td><StatusBadge value={entry.pending_assessment ? "pending_review" : entry.immigration_rule_status} /></td><td><StatusBadge value={entry.pending_source_certification ? "pending_review" : entry.has_reviewed_primary_authority ? "reviewed" : entry.has_authority ? "onboarded" : "missing"} /></td><td><StatusBadge value={entry.pending_source_certification ? "pending_review" : entry.has_reviewed_primary_source ? "reviewed" : entry.has_official_source ? "onboarded" : "missing"} /></td><td><StatusBadge value={entry.has_fresh_monitor ? "ready" : "missing"} /></td><td><StatusBadge value={entry.has_verified_rule ? "ready" : "missing"} /></td><td><StatusBadge value={!entry.coverage_required ? "not_required" : entry.coverage_ready ? "ready" : "gap"} /></td><td><button className="button secondary" onClick={() => selectRegistryEntry(entry.jurisdiction_id)}>{entry.pending_assessment || entry.pending_source_certification ? "Review" : "Assess"}</button></td></tr>)}</tbody></table></div>
          </section>
        </div>}
        {tab === "programmes" && <section className="panel"><SectionTitle label="New and removed visas" title="Visa Programmes Dashboard" detail="Structured programme introductions and removals from official catalogues" /><ChangeList items={dashboard.new_programs} empty="No programme introductions or removals were detected in this window." /></section>}
        {tab === "processing" && <section className="panel"><SectionTitle label="Authority timing" title="Processing-Time Dashboard" detail="Sourced guidance changes, never processing guarantees" /><ChangeList items={dashboard.processing_times} empty="No processing-time changes were detected in this window." /></section>}
        {tab === "occupations" && <section className="panel"><SectionTitle label="Workforce mobility" title="Skilled-Occupation Dashboard" detail="Shortage and eligible-occupation list changes" /><ChangeList items={dashboard.skilled_occupations} empty="No occupation-list changes were detected in this window." /></section>}
        {tab === "thresholds" && <section className="panel"><SectionTitle label="Economic requirements" title="Salary and Investment Threshold Dashboard" detail="Reviewed threshold changes with official-source provenance" /><ChangeList items={dashboard.thresholds} empty="No salary or investment threshold changes were detected in this window." /></section>}
        {tab === "heatmap" && <section className="panel"><SectionTitle label="Geographic activity" title="Country Activity Heatmap" detail="Intensity reflects sourced change volume, not destination quality" /><div className="country-activity-heatmap">{dashboard.country_heatmap.map((country) => <article className={`level-${country.activity_level}`} key={country.jurisdiction_id}><div><strong>{country.country}</strong><span>{country.code}</span></div><b>{country.activity_count}</b><p>{country.official_sources} sources · {country.active_verified_rules} rules</p><small>{titleCase(country.coverage)} coverage · {country.pending_review} pending · {country.published} published</small></article>)}</div></section>}
        {tab === "radar" && <section className="panel"><SectionTitle label="Emerging activity" title="Opportunity Radar" detail="Only human-published events contribute; signals are not predictions or recommendations" /><div className="opportunity-radar-list">{dashboard.opportunity_radar.length ? dashboard.opportunity_radar.map((signal) => <article key={signal.jurisdiction_id}><div><div><span>{signal.region || "Global"}</span><h3>{signal.country}</h3></div><div className="radar-score"><strong>{signal.activity_score}</strong><small>activity score</small></div></div><p>{signal.explanation}</p><div className="global-change-meta"><span>{signal.evidence_count} reviewed events</span><span>{titleCase(signal.signal_level)}</span><span>{titleCase(signal.classification)}</span></div></article>) : <EmptyState title="No reviewed radar signals" detail="Radar signals appear only after relevant regulatory events are human-published." />}</div></section>}
        <InlineNotice label="Intelligence safety boundary" detail={dashboard.safety.message} tone="warn" />
        <div className="planning-links"><Link className="button secondary" href="/intelligence">Open regulatory operations</Link><Link className="button secondary" href="/pathways">Open pathway catalogue</Link><Link className="button secondary" href="/planning">Open mobility planning</Link></div>
      </>}
    </div>
  </WorkspaceShell>;
}
