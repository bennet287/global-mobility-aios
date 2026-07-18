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
  activateMobilityTimeline,
  generateMobilityTimeline,
  getHealthStatus,
  getLatestPathwayComparison,
  getLeads,
  HealthStatus,
  Lead,
  listMobilityTimelines,
  MobilityTimeline,
  PathwayComparison,
  transitionMobilityMilestone,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

export default function TimelinesPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [comparison, setComparison] = useState<PathwayComparison | null>(null);
  const [timelines, setTimelines] = useState<MobilityTimeline[]>([]);
  const [timeline, setTimeline] = useState<MobilityTimeline | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [healthResult, leadRows] = await Promise.all([getHealthStatus(), getLeads()]);
      setHealth(healthResult.data); setLeads(leadRows);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load timeline workspace"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function chooseLead(id: string) {
    setLeadId(id); setTimeline(null); setTimelines([]); setComparison(null); setError(null);
    if (!id) return;
    setLoading(true);
    const [comparisonResult, timelineResult] = await Promise.allSettled([
      getLatestPathwayComparison(id), listMobilityTimelines(id),
    ]);
    if (comparisonResult.status === "fulfilled") setComparison(comparisonResult.value);
    if (timelineResult.status === "fulfilled") {
      setTimelines(timelineResult.value); setTimeline(timelineResult.value[0] || null);
    }
    setLoading(false);
  }

  async function generate() {
    if (!comparison?.assessment_id) return;
    setWorking(true); setError(null);
    try {
      const created = await generateMobilityTimeline(comparison.assessment_id);
      setTimeline(created);
      setTimelines((rows) => [created, ...rows.filter((row) => row.id !== created.id)]);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not generate timeline"); }
    finally { setWorking(false); }
  }

  async function activate() {
    if (!timeline) return;
    setWorking(true); setError(null);
    try { setTimeline(await activateMobilityTimeline(timeline.id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not activate timeline"); }
    finally { setWorking(false); }
  }

  async function transition(milestoneId: string, action: "start" | "complete" | "block" | "unblock") {
    if (!timeline) return;
    setWorking(true); setError(null);
    try {
      const updated = await transitionMobilityMilestone(timeline.id, milestoneId, action, notes[milestoneId]);
      setTimeline(updated); setNotes((current) => ({ ...current, [milestoneId]: "" }));
    } catch (err) { setError(err instanceof Error ? err.message : "Could not transition milestone"); }
    finally { setWorking(false); }
  }

  const completed = timeline?.milestones.filter((item) => item.status === "completed").length || 0;
  const blocked = timeline?.milestones.filter((item) => item.status === "blocked").length || 0;
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  return (
    <WorkspaceShell health={health}>
      <Topbar title="Mobility Timelines" kicker="Dependency-controlled case planning" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad timeline-page">
        {error && <InlineNotice label="Timeline error" detail={error} tone="bad" />}
        <section className="panel timeline-selector">
          <div><span className="page-kicker">Audited execution plan</span><strong>Turn one immutable pathway comparison into controlled case milestones.</strong></div>
          <label>Lead<select value={leadId} onChange={(event) => void chooseLead(event.target.value)}><option value="">Choose a lead</option>{leads.map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name} · {lead.target_country || "No target"}</option>)}</select></label>
          <button className="button primary" disabled={!comparison?.assessment_id || working} onClick={() => void generate()}>{working ? "Working…" : timeline ? "Refresh plan" : "Generate timeline"}</button>
        </section>

        {!leadId ? <EmptyState title="No lead selected" detail="Choose a lead with an evidence-backed pathway comparison." /> : timeline ? <>
          <div className="metric-row timeline-metrics">
            <MetricPill label="Stages complete" value={`${completed}/${timeline.milestones.length}`} tone={completed === timeline.milestones.length ? "good" : "neutral"} />
            <MetricPill label="Blocked" value={blocked} tone={blocked ? "warn" : "good"} />
            <MetricPill label="Profile version" value={timeline.profile_version || "—"} />
            <MetricPill label="Plan history" value={timelines.length} />
            <div className="metric-pill"><span>Status</span><strong className="profile-status-value">{titleCase(timeline.status)}</strong></div>
          </div>
          <InlineNotice label="Planning boundary" detail={String(timeline.schedule.warning || "Dates are planning estimates. Human approvals and authority decisions remain controlled outside this timeline.")} tone="warn" />
          <div className="timeline-layout">
            <main className="timeline-stages">
              <section className="panel timeline-heading">
                <div><SectionTitle label="Active route" title={timeline.title} detail={`Comparison ${timeline.comparison_assessment_id.slice(0, 8)} · pathway version ${timeline.primary_pathway_version_id.slice(0, 8)}`} /></div>
                {timeline.status === "draft" && <button className="button primary" disabled={working} onClick={() => void activate()}>Activate plan</button>}
              </section>
              {timeline.milestones.map((milestone) => <article className={`timeline-stage ${milestone.status}`} key={milestone.id}>
                <div className="timeline-stage-order">{milestone.stage_order}</div>
                <div className="timeline-stage-body">
                  <div className="timeline-stage-title"><div><span>{titleCase(milestone.owner_role)}</span><h3>{milestone.title}</h3></div><StatusBadge value={milestone.status} /></div>
                  <p>{milestone.description}</p>
                  <div className="timeline-stage-meta"><span>Due {milestone.due_at ? new Date(milestone.due_at).toLocaleDateString() : "unscheduled"}</span><span>{milestone.requires_human_approval ? "Human approval required" : "Operational checkpoint"}</span>{milestone.approved_by && <span>Approved by {milestone.approved_by}</span>}</div>
                  {milestone.required_evidence.length > 0 && <div className="timeline-evidence">{milestone.required_evidence.map((item) => <span key={item}>{item}</span>)}</div>}
                  {milestone.blockers.length > 0 && <InlineNotice label="Blocked" detail={milestone.blockers.join(" · ")} tone="bad" />}
                  {timeline.status === "active" && ["ready", "in_progress", "blocked"].includes(milestone.status) && <div className="timeline-actions">
                    <input aria-label={`Note for ${milestone.title}`} placeholder={milestone.requires_human_approval ? "Required approval note" : "Transition note or blocker reason"} value={notes[milestone.id] || ""} onChange={(event) => setNotes((current) => ({ ...current, [milestone.id]: event.target.value }))} />
                    {milestone.status === "ready" && <button className="button secondary" disabled={working} onClick={() => void transition(milestone.id, "start")}>Start</button>}
                    {["ready", "in_progress"].includes(milestone.status) && <button className="button primary" disabled={working} onClick={() => void transition(milestone.id, "complete")}>Complete</button>}
                    {["ready", "in_progress"].includes(milestone.status) && <button className="button secondary" disabled={working} onClick={() => void transition(milestone.id, "block")}>Block</button>}
                    {milestone.status === "blocked" && <button className="button secondary" disabled={working} onClick={() => void transition(milestone.id, "unblock")}>Unblock</button>}
                  </div>}
                </div>
              </article>)}
            </main>
            <aside className="timeline-side panel">
              <SectionTitle label="Immutable provenance" title="Plan basis" detail="Every transition stays tied to the inputs below" />
              <dl><div><dt>Profile</dt><dd>{timeline.profile_id?.slice(0, 8)} · v{timeline.profile_version}</dd></div><div><dt>Comparison</dt><dd>{timeline.comparison_assessment_id.slice(0, 8)}</dd></div><div><dt>Pathway</dt><dd>{timeline.primary_pathway_id.slice(0, 8)}</dd></div><div><dt>Generated by</dt><dd>{timeline.generated_by}</dd></div></dl>
              <div className="planning-links"><Link className="button secondary" href="/planning">Open comparison</Link><Link className="button secondary" href="/profiles">Open profile</Link><Link className="button secondary" href={`/leads/${leadId}`}>Open lead</Link></div>
            </aside>
          </div>
        </> : <EmptyState title={comparison ? "No timeline yet" : "Comparison required"} detail={comparison ? "Generate the timeline from this lead's latest comparison." : "Create an evidence-backed pathway comparison in Mobility Planning first."} />}
      </div>
    </WorkspaceShell>
  );
}
