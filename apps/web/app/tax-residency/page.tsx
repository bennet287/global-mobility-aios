"use client";

import { CSSProperties, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  Lead,
  OfficialSourceView,
  SourceSnapshotView,
  TaxResidencyAssessment,
  TaxTreatyEvidence,
  createTaxResidencyAssessment,
  createTaxTreatyEvidence,
  decideTaxTreatyEvidence,
  getLeads,
  listOfficialSources,
  listSourceSnapshots,
  listTaxResidencyAssessments,
  listTaxTreatyEvidence,
  reviewTaxResidencyAssessment,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const currentYear = new Date().getFullYear();

const emptyAssessment = {
  lead_id: "", tax_year: String(currentYear), current_residencies: "",
  target_residencies: "", citizenships: "", presence_periods: "",
  available_homes: "", spouse_or_dependant_jurisdictions: "",
  employment_jurisdictions: "", director_or_control_jurisdictions: "",
  business_structure_jurisdictions: "", income_categories: "",
  planned_departure_date: "", planned_arrival_date: "", objectives: "",
  disclosed_constraints: "", document_record_ids: "",
  tax_adviser_engaged: false, home_jurisdiction_adviser_engaged: false,
  destination_adviser_engaged: false,
};

const emptyEvidence = {
  evidence_key: "", jurisdiction_a: "", jurisdiction_b: "",
  topic: "residency_tie_breaker", title: "", statement: "",
  official_source_id: "", source_snapshot_id: "", effective_from: "", effective_to: "",
};

type AssessmentForm = typeof emptyAssessment;
type EvidenceForm = typeof emptyEvidence;

function lines(value: string) {
  return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
}

function parsePresence(value: string) {
  return value.split("\n").map((row) => row.trim()).filter(Boolean).map((row) => {
    const [jurisdiction, days = "0"] = row.split("|").map((item) => item.trim());
    return { jurisdiction, days: Number(days) };
  });
}

function parseHomes(value: string) {
  return value.split("\n").map((row) => row.trim()).filter(Boolean).map((row) => {
    const [jurisdiction, homeType = "other", continuous = "no"] = row.split("|").map((item) => item.trim());
    return {
      jurisdiction,
      home_type: homeType as "owned" | "leased" | "family_home" | "employer_provided" | "other",
      continuously_available: ["yes", "true", "continuous"].includes(continuous.toLowerCase()),
    };
  });
}

export default function TaxResidencyPage() {
  const { health } = useBackendStatus();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [sources, setSources] = useState<OfficialSourceView[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshotView[]>([]);
  const [evidence, setEvidence] = useState<TaxTreatyEvidence[]>([]);
  const [assessments, setAssessments] = useState<TaxResidencyAssessment[]>([]);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState("");
  const [assessmentForm, setAssessmentForm] = useState<AssessmentForm>(emptyAssessment);
  const [evidenceForm, setEvidenceForm] = useState<EvidenceForm>(emptyEvidence);
  const [reviewReason, setReviewReason] = useState("");
  const [evidenceReviewReason, setEvidenceReviewReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [leadRows, sourceRows, snapshotRows, evidenceRows, assessmentRows] = await Promise.all([
        getLeads(),
        listOfficialSources({ domain: "tax" }),
        listSourceSnapshots({ limit: 500 }),
        listTaxTreatyEvidence(),
        listTaxResidencyAssessments(),
      ]);
      setLeads(leadRows);
      setSources(sourceRows.sources.filter((source) => source.active));
      setSnapshots(snapshotRows.snapshots);
      setEvidence(evidenceRows);
      setAssessments(assessmentRows);
      setSelectedAssessmentId((current) => current || assessmentRows[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tax and treaty workspace could not be loaded");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const selectedAssessment = useMemo(
    () => assessments.find((item) => item.id === selectedAssessmentId) || assessments[0] || null,
    [assessments, selectedAssessmentId],
  );
  const sourceSnapshots = snapshots.filter(
    (snapshot) => snapshot.official_source_id === evidenceForm.official_source_id && snapshot.content_hash,
  );
  const pendingEvidence = evidence.filter((item) => item.status === "pending_review");
  const publishedEvidence = evidence.filter((item) => item.status === "published");

  function updateAssessment<K extends keyof AssessmentForm>(key: K, value: AssessmentForm[K]) {
    setAssessmentForm((current) => ({ ...current, [key]: value }));
  }

  function updateEvidence<K extends keyof EvidenceForm>(key: K, value: EvidenceForm[K]) {
    setEvidenceForm((current) => ({
      ...current,
      [key]: value,
      ...(key === "official_source_id" ? { source_snapshot_id: "" } : {}),
    }));
  }

  async function submitAssessment(event: FormEvent) {
    event.preventDefault(); setWorking("assessment"); setError(null); setMessage(null);
    try {
      const created = await createTaxResidencyAssessment({
        lead_id: assessmentForm.lead_id,
        tax_year: Number(assessmentForm.tax_year),
        current_residencies: lines(assessmentForm.current_residencies),
        target_residencies: lines(assessmentForm.target_residencies),
        citizenships: lines(assessmentForm.citizenships),
        presence_periods: parsePresence(assessmentForm.presence_periods),
        available_homes: parseHomes(assessmentForm.available_homes),
        spouse_or_dependant_jurisdictions: lines(assessmentForm.spouse_or_dependant_jurisdictions),
        employment_jurisdictions: lines(assessmentForm.employment_jurisdictions),
        director_or_control_jurisdictions: lines(assessmentForm.director_or_control_jurisdictions),
        business_structure_jurisdictions: lines(assessmentForm.business_structure_jurisdictions),
        income_categories: lines(assessmentForm.income_categories),
        ...(assessmentForm.planned_departure_date ? { planned_departure_date: assessmentForm.planned_departure_date } : {}),
        ...(assessmentForm.planned_arrival_date ? { planned_arrival_date: assessmentForm.planned_arrival_date } : {}),
        objectives: lines(assessmentForm.objectives),
        disclosed_constraints: lines(assessmentForm.disclosed_constraints),
        tax_adviser_engaged: assessmentForm.tax_adviser_engaged,
        home_jurisdiction_adviser_engaged: assessmentForm.home_jurisdiction_adviser_engaged,
        destination_adviser_engaged: assessmentForm.destination_adviser_engaged,
        document_record_ids: lines(assessmentForm.document_record_ids),
        treaty_evidence_ids: selectedEvidenceIds,
      });
      setAssessments((current) => [created, ...current]);
      setSelectedAssessmentId(created.id);
      setMessage("A controlled tax-residency issue map was created for independent specialist review.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tax-residency assessment could not be created");
    } finally { setWorking(null); }
  }

  async function submitEvidence(event: FormEvent) {
    event.preventDefault(); setWorking("evidence"); setError(null); setMessage(null);
    try {
      const created = await createTaxTreatyEvidence({
        ...evidenceForm,
        ...(evidenceForm.effective_from ? { effective_from: `${evidenceForm.effective_from}T00:00:00Z` } : {}),
        ...(evidenceForm.effective_to ? { effective_to: `${evidenceForm.effective_to}T23:59:59Z` } : {}),
      });
      setEvidence((current) => [created, ...current]);
      setEvidenceForm(emptyEvidence);
      setMessage("Treaty evidence was proposed. It remains unavailable to assessments until independent publication.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Treaty evidence proposal could not be created");
    } finally { setWorking(null); }
  }

  async function decideEvidence(item: TaxTreatyEvidence, decision: "approved" | "rejected") {
    setWorking(`evidence-${item.id}`); setError(null); setMessage(null);
    try {
      await decideTaxTreatyEvidence(item.id, decision, evidenceReviewReason);
      setEvidenceReviewReason(""); await load();
      setMessage(decision === "approved"
        ? "Treaty evidence is independently published and available for matching assessments."
        : "Treaty evidence was rejected and remains excluded from all assessments.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Treaty evidence decision could not be recorded");
    } finally { setWorking(null); }
  }

  async function reviewAssessment(decision: "specialist_reviewed" | "revision_required") {
    if (!selectedAssessment) return;
    setWorking("assessment-review"); setError(null); setMessage(null);
    try {
      await reviewTaxResidencyAssessment(selectedAssessment.id, decision, reviewReason);
      setReviewReason(""); await load();
      setMessage("The independent specialist decision was recorded in the immutable review ledger.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Specialist review could not be recorded");
    } finally { setWorking(null); }
  }

  return <WorkspaceShell health={health}>
    <Topbar title="Tax & Treaty" kicker="Phase 11 · residence facts and treaty coordination" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />

    <section className="tax-hero">
      <div>
        <span className="eyebrow">Cross-border tax control plane</span>
        <h2>Build the fact pattern before the conclusion.</h2>
        <p>Coordinate presence, homes, family ties, work, ownership, income, dated official evidence, and licensed advisers without turning an operational readiness score into tax advice.</p>
      </div>
      <div className="tax-hero-ledger">
        <div><strong>{publishedEvidence.length}</strong><span>Published treaty records</span></div>
        <div><strong>{pendingEvidence.length}</strong><span>Awaiting evidence review</span></div>
        <div><strong>{assessments.length}</strong><span>Client issue maps</span></div>
      </div>
    </section>

    {error ? <InlineNotice label="Control stopped" detail={error} tone="bad" /> : null}
    {message ? <InlineNotice label="Ledger updated" detail={message} tone="good" /> : null}

    <div className="tax-layout">
      <form className="panel tax-form" onSubmit={submitAssessment}>
        <header className="advisory-panel-head"><div><span className="eyebrow">Client facts</span><h3>Residence coordination brief</h3></div><span className="advisory-step">01</span></header>
        <div className="tax-form-grid">
          <label className="advisory-field"><span>Client</span><select required value={assessmentForm.lead_id} onChange={(event) => updateAssessment("lead_id", event.target.value)}><option value="">Select client</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name}</option>)}</select></label>
          <label className="advisory-field"><span>Tax year</span><input required type="number" min="2000" max="2200" value={assessmentForm.tax_year} onChange={(event) => updateAssessment("tax_year", event.target.value)} /></label>
          <label className="advisory-field"><span>Current claimed / filed residencies</span><input value={assessmentForm.current_residencies} onChange={(event) => updateAssessment("current_residencies", event.target.value)} placeholder="Austria" /></label>
          <label className="advisory-field"><span>Target residencies</span><input required value={assessmentForm.target_residencies} onChange={(event) => updateAssessment("target_residencies", event.target.value)} placeholder="Germany" /></label>
          <label className="advisory-field"><span>Citizenships</span><input value={assessmentForm.citizenships} onChange={(event) => updateAssessment("citizenships", event.target.value)} /></label>
          <label className="advisory-field"><span>Family jurisdictions</span><input value={assessmentForm.spouse_or_dependant_jurisdictions} onChange={(event) => updateAssessment("spouse_or_dependant_jurisdictions", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Presence ledger</span><textarea required rows={3} value={assessmentForm.presence_periods} onChange={(event) => updateAssessment("presence_periods", event.target.value)} placeholder={"Austria | 170\nGermany | 196"} /><small>One line per jurisdiction: jurisdiction | days</small></label>
          <label className="advisory-field wide"><span>Available homes</span><textarea rows={3} value={assessmentForm.available_homes} onChange={(event) => updateAssessment("available_homes", event.target.value)} placeholder={"Austria | owned | yes\nGermany | leased | yes"} /><small>Jurisdiction | owned, leased, family_home, employer_provided or other | continuously available</small></label>
          <label className="advisory-field"><span>Employment jurisdictions</span><input value={assessmentForm.employment_jurisdictions} onChange={(event) => updateAssessment("employment_jurisdictions", event.target.value)} /></label>
          <label className="advisory-field"><span>Director / control jurisdictions</span><input value={assessmentForm.director_or_control_jurisdictions} onChange={(event) => updateAssessment("director_or_control_jurisdictions", event.target.value)} /></label>
          <label className="advisory-field"><span>Business structure jurisdictions</span><input value={assessmentForm.business_structure_jurisdictions} onChange={(event) => updateAssessment("business_structure_jurisdictions", event.target.value)} /></label>
          <label className="advisory-field"><span>Income categories</span><input value={assessmentForm.income_categories} onChange={(event) => updateAssessment("income_categories", event.target.value)} /></label>
          <label className="advisory-field"><span>Planned departure</span><input type="date" value={assessmentForm.planned_departure_date} onChange={(event) => updateAssessment("planned_departure_date", event.target.value)} /></label>
          <label className="advisory-field"><span>Planned arrival</span><input type="date" value={assessmentForm.planned_arrival_date} onChange={(event) => updateAssessment("planned_arrival_date", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Objectives</span><textarea required rows={2} value={assessmentForm.objectives} onChange={(event) => updateAssessment("objectives", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Material constraints and disclosures</span><textarea rows={2} value={assessmentForm.disclosed_constraints} onChange={(event) => updateAssessment("disclosed_constraints", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Controlled document IDs</span><input value={assessmentForm.document_record_ids} onChange={(event) => updateAssessment("document_record_ids", event.target.value)} placeholder="Comma-separated document UUIDs" /></label>
        </div>
        <div className="tax-advisers">
          {([
            ["tax_adviser_engaged", "Coordinating cross-border tax adviser"],
            ["home_jurisdiction_adviser_engaged", "Home-jurisdiction adviser"],
            ["destination_adviser_engaged", "Destination-jurisdiction adviser"],
          ] as const).map(([key, label]) => <label key={key}><input type="checkbox" checked={assessmentForm[key]} onChange={(event) => updateAssessment(key, event.target.checked)} /><span>{label}</span></label>)}
        </div>
        <fieldset className="tax-evidence-picker">
          <legend>Published treaty evidence</legend>
          {publishedEvidence.length ? publishedEvidence.map((item) => <label key={item.id}><input type="checkbox" checked={selectedEvidenceIds.includes(item.id)} onChange={(event) => setSelectedEvidenceIds((current) => event.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))} /><span><strong>{item.jurisdiction_a} ↔ {item.jurisdiction_b}</strong><small>{item.title}</small></span></label>) : <p>No independently published treaty evidence is available. The assessment can still expose the gap, but treaty grounding will be zero.</p>}
        </fieldset>
        <button className="button primary" disabled={working === "assessment"}>{working === "assessment" ? "Building issue map…" : "Create tax-residency issue map"}</button>
      </form>

      <section className="tax-results">
        {selectedAssessment ? <AssessmentResult assessment={selectedAssessment} reason={reviewReason} setReason={setReviewReason} review={reviewAssessment} working={working} /> : <div className="tax-empty-result">
          <div className="panel advisory-empty"><span className="eyebrow">No issue map yet</span><h3>Residence and treaty coordination will appear here.</h3><p>Record the dated client facts, controlled documents, published treaty evidence, and assigned specialists.</p></div>
          <div className="panel tax-empty-guide">
            <header><span className="eyebrow">Controlled sequence</span><strong>What happens next</strong></header>
            <ol>
              <li><span>01</span><div><strong>Reconcile the facts</strong><small>Presence, homes, family, work, ownership, income, and dates.</small></div></li>
              <li><span>02</span><div><strong>Pin the evidence</strong><small>Client documents and independently published treaty snapshots.</small></div></li>
              <li><span>03</span><div><strong>Expose the issues</strong><small>Domestic residence, treaty, entity, payroll, and filing questions.</small></div></li>
              <li><span>04</span><div><strong>Assign specialist conclusions</strong><small>The map coordinates licensed review; it does not invent the conclusion.</small></div></li>
            </ol>
          </div>
        </div>}
      </section>
    </div>

    <section className="tax-evidence-desk">
      <form className="panel tax-evidence-form" onSubmit={submitEvidence}>
        <header className="advisory-panel-head"><div><span className="eyebrow">Source-controlled registry</span><h3>Propose treaty evidence</h3></div><span className="advisory-step">02</span></header>
        <div className="tax-form-grid">
          <label className="advisory-field wide"><span>Evidence key</span><input required pattern="[a-z0-9][a-z0-9_-]+" minLength={3} value={evidenceForm.evidence_key} onChange={(event) => updateEvidence("evidence_key", event.target.value)} placeholder="at-de-residency-tie-breaker-2026" /></label>
          <label className="advisory-field"><span>Jurisdiction A</span><input required value={evidenceForm.jurisdiction_a} onChange={(event) => updateEvidence("jurisdiction_a", event.target.value)} /></label>
          <label className="advisory-field"><span>Jurisdiction B</span><input required value={evidenceForm.jurisdiction_b} onChange={(event) => updateEvidence("jurisdiction_b", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Topic</span><select value={evidenceForm.topic} onChange={(event) => updateEvidence("topic", event.target.value)}>{["residency_definition", "residency_tie_breaker", "permanent_establishment", "employment_income", "business_profits", "dividends_interest_royalties", "capital_gains", "pensions", "elimination_of_double_taxation", "mutual_agreement", "other"].map((topic) => <option value={topic} key={topic}>{titleCase(topic)}</option>)}</select></label>
          <label className="advisory-field wide"><span>Evidence title</span><input required minLength={5} value={evidenceForm.title} onChange={(event) => updateEvidence("title", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Narrow factual statement</span><textarea required minLength={20} rows={4} value={evidenceForm.statement} onChange={(event) => updateEvidence("statement", event.target.value)} /><small>Record what the official text says. Do not write a client conclusion or outcome promise.</small></label>
          <label className="advisory-field wide"><span>Active tax-domain official source</span><select required value={evidenceForm.official_source_id} onChange={(event) => updateEvidence("official_source_id", event.target.value)}><option value="">Select source</option>{sources.map((source) => <option value={source.id} key={source.id}>{source.country} · {source.name}</option>)}</select></label>
          <label className="advisory-field wide"><span>Content-addressed snapshot</span><select required value={evidenceForm.source_snapshot_id} onChange={(event) => updateEvidence("source_snapshot_id", event.target.value)}><option value="">Select snapshot</option>{sourceSnapshots.map((snapshot) => <option value={snapshot.id} key={snapshot.id}>{snapshot.content_hash?.slice(0, 18)} · {new Date(snapshot.captured_at).toLocaleDateString()}</option>)}</select></label>
          <label className="advisory-field"><span>Effective from</span><input type="date" value={evidenceForm.effective_from} onChange={(event) => updateEvidence("effective_from", event.target.value)} /></label>
          <label className="advisory-field"><span>Effective to</span><input type="date" value={evidenceForm.effective_to} onChange={(event) => updateEvidence("effective_to", event.target.value)} /></label>
        </div>
        <button className="button primary" disabled={working === "evidence" || !sources.length}>{working === "evidence" ? "Pinning evidence…" : "Create pending proposal"}</button>
      </form>

      <div className="panel tax-review-queue">
        <header className="advisory-panel-head"><div><span className="eyebrow">Independent publication</span><h3>Treaty evidence queue</h3></div><span>{pendingEvidence.length} pending</span></header>
        {pendingEvidence.length ? <>
          <label className="advisory-field"><span>Review reason</span><textarea minLength={10} rows={3} value={evidenceReviewReason} onChange={(event) => setEvidenceReviewReason(event.target.value)} placeholder="Record the official-text, scope, snapshot, protocol, and effective-period checks." /></label>
          <div className="tax-review-list">{pendingEvidence.map((item) => <article key={item.id}><div><span>{item.jurisdiction_a} ↔ {item.jurisdiction_b}</span><StatusBadge value={item.status} /></div><h4>{item.title}</h4><p>{item.statement}</p><small>{item.source_content_hash} · proposed by {item.proposed_by}</small><footer><button type="button" className="button secondary" disabled={evidenceReviewReason.trim().length < 10 || working === `evidence-${item.id}`} onClick={() => void decideEvidence(item, "rejected")}>Reject</button><button type="button" className="button primary" disabled={evidenceReviewReason.trim().length < 10 || working === `evidence-${item.id}`} onClick={() => void decideEvidence(item, "approved")}>Publish</button></footer></article>)}</div>
        </> : <div className="tax-empty">No treaty evidence is awaiting independent review.</div>}
      </div>
    </section>

    {assessments.length ? <section className="panel advisory-history"><header className="advisory-panel-head"><div><span className="eyebrow">Immutable client ledger</span><h3>Tax-residency issue maps</h3></div><span>{assessments.length} recorded</span></header><div className="advisory-history-list">{assessments.map((item) => <button type="button" className={selectedAssessment?.id === item.id ? "active" : ""} onClick={() => setSelectedAssessmentId(item.id)} key={item.id}><span><strong>{leads.find((lead) => lead.id === item.lead_id)?.full_name || "Client"} · {item.tax_year}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span><b>{Math.round(item.readiness_score)}</b><StatusBadge value={item.status} /></button>)}</div></section> : null}
  </WorkspaceShell>;
}

function AssessmentResult({ assessment, reason, setReason, review, working }: {
  assessment: TaxResidencyAssessment; reason: string; setReason: (value: string) => void;
  review: (decision: "specialist_reviewed" | "revision_required") => void; working: string | null;
}) {
  const style = { "--score": Math.max(0, Math.min(100, assessment.readiness_score)) } as CSSProperties;
  const components = [
    ["Fact pattern", assessment.fact_completeness_score],
    ["Client evidence", assessment.controlled_evidence_score],
    ["Treaty grounding", assessment.treaty_grounding_score],
    ["Specialists", assessment.specialist_coordination_score],
  ] as const;
  return <>
    <div className="panel tax-score">
      <header className="advisory-panel-head"><div><span className="eyebrow">Specialist readiness</span><h3>{titleCase(assessment.readiness_band)}</h3></div><StatusBadge value={assessment.status} /></header>
      <div className="family-office-score-body"><div className="feasibility-meter" style={style}><div><strong>{Math.round(assessment.readiness_score)}</strong><span>/ 100</span></div></div><div className="family-office-components">{components.map(([label, score]) => <div key={label}><span>{label}</span><strong>{Math.round(score)}</strong><i><em style={{ width: `${score}%` }} /></i></div>)}</div></div>
      <p>{assessment.score_semantics}</p>
    </div>
    <div className="panel tax-issues">
      <header className="advisory-panel-head"><div><span className="eyebrow">Issue matrix</span><h3>Questions requiring conclusions</h3></div><span>{assessment.issue_matrix.length} issues</span></header>
      <div>{assessment.issue_matrix.map((issue) => <article key={issue.issue_key}><header><strong>{issue.title}</strong><StatusBadge value={issue.severity} /></header><p>{issue.rationale}</p><small>{issue.jurisdictions.join(" · ")} · {titleCase(issue.evidence_state)}</small></article>)}</div>
    </div>
    <div className="family-office-workstreams">{assessment.workstreams.map((stream, index) => <article className="panel" key={stream.workstream_key}><header><span>0{index + 1}</span><StatusBadge value={stream.readiness_band} /></header><h3>{stream.title}</h3><strong>{Math.round(stream.readiness_score)}%</strong>{stream.blockers.length ? <ul>{stream.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul> : <p>No recorded blocker in this workstream.</p>}<small>{stream.next_actions[0]}</small></article>)}</div>
    <div className="panel family-office-actions"><header className="advisory-panel-head"><div><span className="eyebrow">Controlled sequence</span><h3>Next accountable actions</h3></div><span className="advisory-step">03</span></header><ol>{assessment.next_actions.map((action) => <li key={action}>{action}</li>)}</ol></div>
    {assessment.status === "specialist_review_required" ? <div className="panel family-office-review"><label className="advisory-field"><span>Independent specialist review</span><textarea minLength={10} rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Record the domestic-law, treaty, effective-period, entity, income, payroll, filing, and evidence checks performed." /></label><div><button type="button" className="button secondary" disabled={working === "assessment-review" || reason.trim().length < 10} onClick={() => review("revision_required")}>Require revision</button><button type="button" className="button primary" disabled={working === "assessment-review" || reason.trim().length < 10} onClick={() => review("specialist_reviewed")}>Record specialist review</button></div><small>The issue-map creator cannot perform this review.</small></div> : null}
  </>;
}
