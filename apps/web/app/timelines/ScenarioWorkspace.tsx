"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import {
  createMobilityScenario,
  getMobilityScenarioRecalculationCandidate,
  listMobilityScenarios,
  listPathways,
  MobilityPathway,
  MobilityScenario,
  MobilityScenarioRecalculationCandidate,
  MobilityScenarioStageType,
  recalculateMobilityScenario,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

type StageDraft = {
  stage_type: MobilityScenarioStageType;
  pathway_version_id: string;
  duration_months: number;
  gap_months_before: number;
};

const stageTypes: MobilityScenarioStageType[] = [
  "study",
  "graduate_rights",
  "work_permit",
  "skilled_migration",
  "settlement",
  "permanent_residence",
  "citizenship_review",
];

const defaultStages: StageDraft[] = [
  { stage_type: "study", pathway_version_id: "", duration_months: 24, gap_months_before: 0 },
  { stage_type: "work_permit", pathway_version_id: "", duration_months: 36, gap_months_before: 0 },
];

export function ScenarioWorkspace({ leadId }: { leadId: string }) {
  const [pathways, setPathways] = useState<MobilityPathway[]>([]);
  const [scenarios, setScenarios] = useState<MobilityScenario[]>([]);
  const [scenario, setScenario] = useState<MobilityScenario | null>(null);
  const [candidate, setCandidate] = useState<MobilityScenarioRecalculationCandidate | null>(null);
  const [title, setTitle] = useState("Reviewed multi-year mobility scenario");
  const [startDate, setStartDate] = useState("2026-09-01");
  const [stages, setStages] = useState<StageDraft[]>(defaultStages);
  const [attestation, setAttestation] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [recalcAttestation, setRecalcAttestation] = useState("");
  const [recalcNotes, setRecalcNotes] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!leadId) {
      setScenarios([]); setScenario(null); setCandidate(null);
      return;
    }
    setError(null);
    const [pathwayResult, scenarioResult] = await Promise.allSettled([
      listPathways({ catalogue_status: "active" }),
      listMobilityScenarios(leadId),
    ]);
    if (pathwayResult.status === "fulfilled") setPathways(pathwayResult.value.filter((row) => row.current_version?.lifecycle_status === "published"));
    if (scenarioResult.status === "fulfilled") {
      setScenarios(scenarioResult.value);
      setScenario(scenarioResult.value[0] || null);
    }
  }, [leadId]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!scenario) { setCandidate(null); return; }
    void getMobilityScenarioRecalculationCandidate(scenario.id)
      .then(setCandidate)
      .catch(() => setCandidate(null));
  }, [scenario]);

  const versions = useMemo(() => pathways.flatMap((pathway) => pathway.current_version ? [{ pathway, version: pathway.current_version }] : []), [pathways]);

  function updateStage(index: number, patch: Partial<StageDraft>) {
    setStages((rows) => rows.map((row, rowIndex) => rowIndex === index ? { ...row, ...patch } : row));
  }

  async function createScenario() {
    if (!leadId) return;
    setWorking(true); setError(null);
    try {
      const created = await createMobilityScenario({
        lead_id: leadId,
        title,
        start_date: new Date(`${startDate}T00:00:00Z`).toISOString(),
        stages,
        explicit_user_acceptance: true,
        user_attestation: attestation,
        review_notes: reviewNotes,
      });
      setScenario(created);
      setScenarios((rows) => [created, ...rows.filter((row) => row.id !== created.id)]);
      setAttestation(""); setReviewNotes("");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create mobility scenario"); }
    finally { setWorking(false); }
  }

  async function recalculate() {
    if (!scenario || !candidate?.available) return;
    setWorking(true); setError(null);
    try {
      const created = await recalculateMobilityScenario(scenario.id, {
        regulatory_impact_ids: candidate.impacts.map((row) => row.impact_id),
        explicit_user_acceptance: true,
        user_attestation: recalcAttestation,
        review_notes: recalcNotes,
      });
      setScenario(created);
      setScenarios((rows) => [created, ...rows.filter((row) => row.id !== created.id)]);
      setRecalcAttestation(""); setRecalcNotes("");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not recalculate scenario"); }
    finally { setWorking(false); }
  }

  if (!leadId) return <EmptyState title="No lead selected" detail="Choose a lead to build a human-confirmed multi-year scenario." />;

  return <section className="scenario-workspace">
    {error && <InlineNotice label="Scenario error" detail={error} tone="bad" />}
    <section className="panel scenario-builder">
      <SectionTitle label="Phase 10E scenario builder" title="Versioned multi-year and multi-country plan" detail="Every stage requires a human-published pathway version. Dates are planning estimates, never guarantees." />
      <div className="scenario-form-grid">
        <label>Scenario title<input value={title} onChange={(event) => setTitle(event.target.value)} /></label>
        <label>Planning start<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
      </div>
      <div className="scenario-stage-editor">
        {stages.map((stage, index) => <article key={`${index}-${stage.stage_type}`}>
          <strong>{index + 1}</strong>
          <label>Transition<select value={stage.stage_type} onChange={(event) => updateStage(index, { stage_type: event.target.value as MobilityScenarioStageType })}>{stageTypes.map((value) => <option value={value} key={value}>{titleCase(value)}</option>)}</select></label>
          <label>Reviewed pathway<select value={stage.pathway_version_id} onChange={(event) => updateStage(index, { pathway_version_id: event.target.value })}><option value="">Choose published pathway</option>{versions.map(({ pathway, version }) => <option value={version.id} key={version.id}>{pathway.country} · {pathway.name} · v{version.version_number}</option>)}</select></label>
          <label>Duration months<input type="number" min={1} max={240} value={stage.duration_months} onChange={(event) => updateStage(index, { duration_months: Number(event.target.value) })} /></label>
          <label>Gap before<input type="number" min={0} max={120} value={stage.gap_months_before} onChange={(event) => updateStage(index, { gap_months_before: Number(event.target.value) })} /></label>
          <button className="button secondary" disabled={stages.length <= 2} onClick={() => setStages((rows) => rows.filter((_, rowIndex) => rowIndex !== index))}>Remove</button>
        </article>)}
      </div>
      <button className="button secondary" onClick={() => setStages((rows) => [...rows, { stage_type: "settlement", pathway_version_id: "", duration_months: 24, gap_months_before: 0 }])}>Add stage</button>
      <div className="scenario-attestation-grid">
        <label>User attestation<textarea value={attestation} onChange={(event) => setAttestation(event.target.value)} placeholder="Confirm that the client accepts this reviewed planning scenario and its uncertainty." /></label>
        <label>Human review notes<textarea value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} placeholder="Record how stages, evidence, durations, and non-guarantee boundaries were reviewed." /></label>
        <button className="button primary" disabled={working || stages.some((row) => !row.pathway_version_id) || attestation.trim().length < 10 || reviewNotes.trim().length < 3} onClick={() => void createScenario()}>{working ? "Working…" : "Create immutable scenario"}</button>
      </div>
    </section>

    {scenario ? <>
      <div className="metric-row scenario-metrics">
        <MetricPill label="Scenario version" value={`v${scenario.scenario_version}`} />
        <MetricPill label="Countries" value={scenario.countries.length} />
        <MetricPill label="Stages" value={scenario.stages.length} />
        <MetricPill label="History" value={scenarios.length} />
      </div>
      <InlineNotice label="Non-guarantee boundary" detail={scenario.warning} tone="warn" />
      <div className="scenario-layout">
        <section className="scenario-stage-list" aria-label="Scenario stages">
          <section className="panel scenario-heading">
            <SectionTitle label="Human-confirmed scenario" title={scenario.title} detail={`Profile v${scenario.profile_version || "—"} · reviewed by ${scenario.reviewed_by}`} />
            <StatusBadge value={scenario.status} />
          </section>
          {scenario.stages.map((stage) => <article className="scenario-stage-card" key={stage.id}>
            <div className="scenario-stage-index">{stage.stage_order}</div>
            <div>
              <div className="scenario-stage-title"><div><span>{stage.country} · {titleCase(stage.stage_type)}</span><h3>{stage.title}</h3></div><strong>{stage.duration_months} mo</strong></div>
              <p>{new Date(stage.planned_start).toLocaleDateString()} → {new Date(stage.planned_end).toLocaleDateString()}</p>
              <div className="scenario-stage-badges"><span>{titleCase(stage.domain)}</span><span>Pathway {stage.pathway_version_id.slice(0, 8)}</span><span>{stage.verified_rule_ids.length} reviewed rule(s)</span><span>Human confirmation required</span></div>
            </div>
          </article>)}
        </section>
        <aside className="panel scenario-history">
          <SectionTitle label="Immutable versions" title="Scenario history" detail="Recalculation creates a new version and never rewrites earlier dates or evidence." />
          {scenarios.map((row) => <button className={row.id === scenario.id ? "active" : ""} onClick={() => setScenario(row)} key={row.id}><strong>v{row.scenario_version} · {row.title}</strong><span>{new Date(row.created_at).toLocaleString()} · {row.countries.join(" → ")}</span></button>)}
        </aside>
      </div>
      {candidate?.available && <section className="panel scenario-recalculation">
        <SectionTitle label="Reviewed rule changes" title="Create a new scenario version" detail={candidate.message} />
        <div className="scenario-impact-list">{candidate.impacts.map((impact) => <article key={impact.impact_id}><strong>{titleCase(impact.impact_type)}</strong><span>Stages {impact.affected_stage_orders.join(", ")} · {titleCase(impact.materiality)}</span><p>{impact.review_notes || "Reviewed replacement pathway version available."}</p></article>)}</div>
        <div className="scenario-attestation-grid">
          <label>User attestation<textarea value={recalcAttestation} onChange={(event) => setRecalcAttestation(event.target.value)} /></label>
          <label>Human review notes<textarea value={recalcNotes} onChange={(event) => setRecalcNotes(event.target.value)} /></label>
          <button className="button primary" disabled={working || recalcAttestation.trim().length < 10 || recalcNotes.trim().length < 3} onClick={() => void recalculate()}>Create version {scenario.scenario_version + 1}</button>
        </div>
      </section>}
    </> : <EmptyState title="No scenario yet" detail={pathways.length ? "Build a reviewed sequence from published pathways." : "Publish reviewed pathway versions before creating a scenario."} />}
  </section>;
}
