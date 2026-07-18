"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  comparePathways,
  getHealthStatus,
  getLatestPathwayComparison,
  getLeads,
  getPathwayComparisonHistory,
  HealthStatus,
  Lead,
  PathwayComparison,
  PathwayComparisonItem,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

function money(value: number | null, currency: string) {
  if (value == null) return "Not recorded";
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

function ComparisonCard({ item, primary = false }: { item: PathwayComparisonItem; primary?: boolean }) {
  const version = item.pathway.current_version;
  return (
    <article className={`planning-comparison-card ${primary ? "primary" : ""}`}>
      <div className="planning-card-heading">
        <div>
          <span>{primary ? "Leading option" : "Alternative"}</span>
          <h3>{item.pathway.name}</h3>
          <p>{titleCase(item.pathway.country)} · {titleCase(item.pathway.domain)} · version {version?.version_number || "—"}</p>
        </div>
        <div className="planning-score"><strong>{Math.round(item.match_score * 100)}%</strong><small>profile match</small></div>
      </div>
      <p className="planning-explanation">{item.explanation}</p>
      <div className="planning-card-metrics">
        <div><small>Upfront fees</small><strong>{money(item.cost.one_time_total, item.cost.currency)}</strong></div>
        <div><small>Minimum funds</small><strong>{money(item.cost.minimum_funds, item.cost.currency)}</strong></div>
        <div><small>Risk</small><StatusBadge value={`${item.risk.level}_risk`} /></div>
        <div><small>Evidence gaps</small><strong>{item.missing_evidence.length}</strong></div>
      </div>
      <div className="planning-detail-grid">
        <div><strong>Why it matches</strong><ul>{item.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>
        <div><strong>Tradeoffs</strong><ul>{item.tradeoffs.map((tradeoff) => <li key={tradeoff}>{tradeoff}</li>)}</ul></div>
        <div><strong>Benefits</strong>{item.benefits.length ? <ul>{item.benefits.map((benefit) => <li key={benefit}>{benefit}</li>)}</ul> : <p>No reviewed benefits recorded.</p>}</div>
        <div><strong>Risks and evidence</strong><ul>{[...item.risk.declared_risks, ...item.risk.regulatory_risks, ...item.missing_evidence].map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}</ul></div>
      </div>
      <div className="planning-provenance">
        <span>Source {version?.official_source_id?.slice(0, 8) || "missing"}</span>
        <span>Snapshot {version?.source_snapshot_id?.slice(0, 8) || "missing"}</span>
        <span>{item.verified_rule_ids.length} verified rule{item.verified_rule_ids.length === 1 ? "" : "s"}</span>
      </div>
    </article>
  );
}

export default function PlanningPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [comparison, setComparison] = useState<PathwayComparison | null>(null);
  const [history, setHistory] = useState<PathwayComparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [healthResult, leadRows] = await Promise.all([getHealthStatus(), getLeads()]);
      setHealth(healthResult.data); setLeads(leadRows);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load mobility planning"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function chooseLead(selectedLeadId: string) {
    setLeadId(selectedLeadId); setComparison(null); setHistory([]); setError(null);
    if (!selectedLeadId) return;
    setLoading(true);
    const [latest, rows] = await Promise.allSettled([
      getLatestPathwayComparison(selectedLeadId),
      getPathwayComparisonHistory(selectedLeadId),
    ]);
    if (latest.status === "fulfilled") setComparison(latest.value);
    if (rows.status === "fulfilled") setHistory(rows.value);
    setLoading(false);
  }

  async function runComparison() {
    if (!leadId) return;
    setRunning(true); setError(null);
    try {
      const result = await comparePathways(leadId);
      setComparison(result);
      setHistory(result.assessment_id ? await getPathwayComparisonHistory(leadId) : []);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not generate pathway comparison"); }
    finally { setRunning(false); }
  }

  const selectedLead = leads.find((lead) => lead.id === leadId);
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  const primary = comparison?.primary;
  return (
    <WorkspaceShell health={health}>
      <Topbar title="Mobility Planning" kicker="Cost, risk, evidence, alternatives" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad planning-page">
        {error && <InlineNotice label="Planning error" detail={error} tone="bad" />}
        <section className="panel planning-selector">
          <div><span className="page-kicker">Reproducible comparison</span><strong>Compare only published, evidence-backed pathways against the current profile.</strong></div>
          <label>Lead<select value={leadId} onChange={(event) => void chooseLead(event.target.value)}><option value="">Choose a lead</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name} · {lead.target_country || "No target"}</option>)}</select></label>
          <button className="button primary" disabled={!leadId || running} onClick={() => void runComparison()}>{running ? "Comparing…" : "Generate comparison"}</button>
        </section>

        {!leadId ? <EmptyState title="No lead selected" detail="Choose a lead to compare their current profile against published mobility pathways." /> : comparison ? <>
          <div className="metric-row planning-metrics">
            <MetricPill label="Profile version" value={comparison.profile_version || "None"} />
            <MetricPill label="Alternatives" value={comparison.alternatives.length} />
            <MetricPill label="Evidence gaps" value={comparison.missing_evidence.length} tone={comparison.missing_evidence.length ? "warn" : "good"} />
            <MetricPill label="History" value={history.length} />
            <div className="metric-pill"><span>Plan status</span><strong className="profile-status-value">{titleCase(comparison.status)}</strong></div>
            <div className="metric-pill"><span>Consent</span><strong className="profile-status-value">{titleCase(comparison.consent_status)}</strong></div>
          </div>
          <InlineNotice label="Human review required" detail={comparison.summary} tone={comparison.status === "restricted" ? "bad" : primary ? "warn" : "bad"} />
          {primary ? <div className="planning-layout">
            <main className="planning-results"><ComparisonCard item={primary} primary />{comparison.alternatives.length > 0 && <section><SectionTitle label="Alternatives" title="Other plausible routes" detail="Ranked against the same immutable profile version" /><div className="planning-alternatives">{comparison.alternatives.map((item) => <ComparisonCard key={item.pathway.id} item={item} />)}</div></section>}</main>
            <aside className="planning-side">
              <section className="panel"><SectionTitle label="Evidence" title="Cross-pathway gaps" detail="Resolve these before a consultant recommendation" /><div className="planning-gap-list">{comparison.missing_evidence.length ? comparison.missing_evidence.map((gap) => <span key={gap}>{gap}</span>) : <p>No common evidence gaps were detected.</p>}</div></section>
              <section className="panel"><SectionTitle label="Audit" title="Comparison history" detail={`${history.length} immutable assessment${history.length === 1 ? "" : "s"}`} /><div className="planning-history">{history.map((item) => <article key={item.assessment_id || item.generated_at}><div><strong>{titleCase(item.status)}</strong><StatusBadge value={item.primary?.risk.level ? `${item.primary.risk.level}_risk` : item.status} /></div><p>Profile v{item.profile_version || "—"} · {item.alternatives.length} alternatives</p><small>{new Date(item.generated_at).toLocaleString()} · {item.generated_by}</small></article>)}</div></section>
              <div className="planning-links"><Link className="button secondary" href="/profiles">Update profile</Link><Link className="button secondary" href="/pathways">Manage catalogue</Link>{selectedLead && <Link className="button secondary" href={`/leads/${selectedLead.id}`}>Open lead</Link>}</div>
            </aside>
          </div> : <EmptyState title={comparison.status === "restricted" ? "Comparison restricted" : "No published pathway matches"} detail={comparison.summary} />}
        </> : <EmptyState title="No comparison yet" detail="Generate a comparison after the lead has a current profile and the catalogue contains published pathways." />}
      </div>
    </WorkspaceShell>
  );
}
