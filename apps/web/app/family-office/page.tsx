"use client";

import { CSSProperties, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  FamilyOfficeAssessment,
  FamilyOfficeStructure,
  Lead,
  createFamilyOfficeAssessment,
  getLeads,
  listFamilyOfficeAssessments,
  reviewFamilyOfficeAssessment,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const emptyForm = {
  lead_id: "", family_office_name: "", primary_objectives: "", target_jurisdictions: "",
  current_tax_residencies: "", citizenships: "", family_members: "1", structures: "",
  asset_classes: "", estimated_net_worth: "", liquid_assets: "", currency: "EUR",
  source_of_wealth_status: "unconfirmed" as EvidenceStatus,
  source_of_funds_status: "unconfirmed" as EvidenceStatus,
  screening_status: "pending" as "pending" | "cleared" | "escalated",
  beneficial_ownership_documented: false, pep_or_sanctions_exposure_disclosed: false,
  tax_adviser_engaged: false, legal_adviser_engaged: false,
  succession_plan_documented: false, banking_relationships_confirmed: false,
  disclosed_constraints: "", document_record_ids: "",
};

type EvidenceStatus = "unconfirmed" | "documented" | "independently_verified";
type FormState = typeof emptyForm;

function lines(value: string) {
  return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
}

function minor(value: string) {
  return value ? Math.round(Number(value) * 100) : undefined;
}

function parseStructures(value: string): FamilyOfficeStructure[] {
  return value.split("\n").map((row) => row.trim()).filter(Boolean).map((row) => {
    const [name, structureType = "holding_company", jurisdiction = "", disclosed = "yes"] = row.split("|").map((item) => item.trim());
    return {
      name,
      structure_type: structureType as FamilyOfficeStructure["structure_type"],
      jurisdiction,
      beneficial_ownership_disclosed: ["yes", "true", "disclosed"].includes(disclosed.toLowerCase()),
    };
  });
}

export default function FamilyOfficePage() {
  const { health } = useBackendStatus();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [assessments, setAssessments] = useState<FamilyOfficeAssessment[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [form, setForm] = useState<FormState>(emptyForm);
  const [reviewNotes, setReviewNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [leadRows, assessmentRows] = await Promise.all([
        getLeads(), listFamilyOfficeAssessments(),
      ]);
      setLeads(leadRows); setAssessments(assessmentRows);
      setSelectedId((current) => current || assessmentRows[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Family-office workspace could not be loaded");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  const selected = useMemo(
    () => assessments.find((item) => item.id === selectedId) || assessments[0] || null,
    [assessments, selectedId],
  );

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setWorking("create"); setError(null); setMessage(null);
    try {
      const netWorth = minor(form.estimated_net_worth);
      const liquid = minor(form.liquid_assets);
      const created = await createFamilyOfficeAssessment({
        lead_id: form.lead_id,
        ...(form.family_office_name ? { family_office_name: form.family_office_name } : {}),
        primary_objectives: lines(form.primary_objectives),
        target_jurisdictions: lines(form.target_jurisdictions),
        current_tax_residencies: lines(form.current_tax_residencies),
        citizenships: lines(form.citizenships),
        family_members: Number(form.family_members),
        structures: parseStructures(form.structures),
        asset_classes: lines(form.asset_classes),
        ...(netWorth !== undefined ? { estimated_net_worth_minor: netWorth } : {}),
        ...(liquid !== undefined ? { liquid_assets_minor: liquid } : {}),
        ...((netWorth !== undefined || liquid !== undefined) ? { currency: form.currency.toUpperCase() } : {}),
        source_of_wealth_status: form.source_of_wealth_status,
        source_of_funds_status: form.source_of_funds_status,
        beneficial_ownership_documented: form.beneficial_ownership_documented,
        screening_status: form.screening_status,
        pep_or_sanctions_exposure_disclosed: form.pep_or_sanctions_exposure_disclosed,
        tax_adviser_engaged: form.tax_adviser_engaged,
        legal_adviser_engaged: form.legal_adviser_engaged,
        succession_plan_documented: form.succession_plan_documented,
        banking_relationships_confirmed: form.banking_relationships_confirmed,
        disclosed_constraints: lines(form.disclosed_constraints),
        document_record_ids: lines(form.document_record_ids),
      });
      setAssessments((current) => [created, ...current]);
      setSelectedId(created.id);
      setMessage("Family-office readiness map created and queued for independent human review.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Family-office assessment could not be created");
    } finally { setWorking(null); }
  }

  async function review(decision: "approved" | "revision_required") {
    if (!selected) return;
    setWorking("review"); setError(null); setMessage(null);
    try {
      await reviewFamilyOfficeAssessment(selected.id, decision, reviewNotes);
      setReviewNotes("");
      await load();
      setMessage(decision === "approved"
        ? "The readiness map was independently approved as a controlled planning record."
        : "The readiness map was returned for revision with an immutable decision record.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Family-office review could not be recorded");
    } finally { setWorking(null); }
  }

  return <WorkspaceShell health={health}>
    <Topbar title="Family Office" kicker="Phase 11 · HNWI and family-office mobility" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />

    <section className="family-office-hero">
      <div>
        <span className="eyebrow">Private-client control plane</span>
        <h2>Coordinate the family, ownership, wealth, and move.</h2>
        <p>Turn a cross-border family-office situation into five accountable workstreams with explicit evidence gaps, ownership transparency, screening posture, specialist escalation, and source-controlled mobility grounding.</p>
      </div>
      <div className="family-office-principles">
        <span>Beneficial ownership visible</span>
        <span>Wealth evidence controlled</span>
        <span>Independent human review</span>
      </div>
    </section>

    {error ? <InlineNotice label="Assessment stopped" detail={error} tone="bad" /> : null}
    {message ? <InlineNotice label="Family-office record updated" detail={message} tone="good" /> : null}

    <div className="family-office-layout">
      <form className="panel family-office-form" onSubmit={submit}>
        <header className="advisory-panel-head"><div><span className="eyebrow">Family facts</span><h3>Build the control map</h3></div><span className="advisory-step">01</span></header>
        <div className="family-office-form-grid">
          <label className="advisory-field"><span>Principal client</span><select required value={form.lead_id} onChange={(event) => update("lead_id", event.target.value)}><option value="">Select client</option>{leads.map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name}</option>)}</select></label>
          <label className="advisory-field"><span>Family-office name</span><input value={form.family_office_name} onChange={(event) => update("family_office_name", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Primary objectives</span><textarea required rows={3} value={form.primary_objectives} onChange={(event) => update("primary_objectives", event.target.value)} placeholder="Family relocation, operating-business continuity, succession—one per line" /></label>
          <label className="advisory-field"><span>Target jurisdictions</span><textarea required rows={2} value={form.target_jurisdictions} onChange={(event) => update("target_jurisdictions", event.target.value)} /></label>
          <label className="advisory-field"><span>Current tax residencies</span><textarea rows={2} value={form.current_tax_residencies} onChange={(event) => update("current_tax_residencies", event.target.value)} /></label>
          <label className="advisory-field"><span>Citizenships</span><textarea rows={2} value={form.citizenships} onChange={(event) => update("citizenships", event.target.value)} /></label>
          <label className="advisory-field"><span>Family members</span><input required type="number" min="1" value={form.family_members} onChange={(event) => update("family_members", event.target.value)} /></label>
          <label className="advisory-field wide"><span>Structures</span><textarea rows={3} value={form.structures} onChange={(event) => update("structures", event.target.value)} placeholder="Atlas Holdings | holding_company | United Kingdom | yes" /><small>One per line: name | type | jurisdiction | ownership disclosed</small></label>
          <label className="advisory-field wide"><span>Asset classes</span><textarea rows={2} value={form.asset_classes} onChange={(event) => update("asset_classes", event.target.value)} /></label>
          <label className="advisory-field"><span>Estimated net worth</span><input type="number" min="0" step="0.01" value={form.estimated_net_worth} onChange={(event) => update("estimated_net_worth", event.target.value)} /></label>
          <label className="advisory-field"><span>Liquid assets</span><input type="number" min="0" step="0.01" value={form.liquid_assets} onChange={(event) => update("liquid_assets", event.target.value)} /></label>
          <label className="advisory-field"><span>Currency</span><input minLength={3} maxLength={3} value={form.currency} onChange={(event) => update("currency", event.target.value)} /></label>
          <label className="advisory-field"><span>Source of wealth</span><EvidenceSelect value={form.source_of_wealth_status} onChange={(value) => update("source_of_wealth_status", value)} /></label>
          <label className="advisory-field"><span>Source of funds</span><EvidenceSelect value={form.source_of_funds_status} onChange={(value) => update("source_of_funds_status", value)} /></label>
          <label className="advisory-field"><span>PEP / sanctions screening</span><select value={form.screening_status} onChange={(event) => update("screening_status", event.target.value as FormState["screening_status"])}><option value="pending">Pending</option><option value="cleared">Cleared</option><option value="escalated">Escalated</option></select></label>
          <label className="advisory-field wide"><span>Material constraints</span><textarea rows={3} value={form.disclosed_constraints} onChange={(event) => update("disclosed_constraints", event.target.value)} placeholder="Prior refusals, PEP exposure, tax disputes, banking constraints—one per line" /></label>
          <label className="advisory-field wide"><span>Controlled document IDs</span><input value={form.document_record_ids} onChange={(event) => update("document_record_ids", event.target.value)} /></label>
        </div>
        <div className="family-office-checks">
          {([
            ["beneficial_ownership_documented", "Ultimate beneficial ownership documented"],
            ["tax_adviser_engaged", "Cross-border tax adviser engaged"],
            ["legal_adviser_engaged", "Qualified legal adviser engaged"],
            ["succession_plan_documented", "Succession plan documented"],
            ["banking_relationships_confirmed", "Banking relationships confirmed"],
            ["pep_or_sanctions_exposure_disclosed", "PEP or sanctions exposure disclosed"],
          ] as const).map(([key, label]) => <label key={key}><input type="checkbox" checked={form[key]} onChange={(event) => update(key, event.target.checked)} /><span>{label}</span></label>)}
        </div>
        <button className="button primary" disabled={working === "create"}>{working === "create" ? "Building control map…" : "Create readiness map"}</button>
      </form>

      <section className="family-office-results">
        {selected ? <FamilyOfficeResult assessment={selected} reviewNotes={reviewNotes} setReviewNotes={setReviewNotes} review={review} working={working} /> : <div className="panel advisory-empty"><span className="eyebrow">No assessment yet</span><h3>The family-office control map will appear here.</h3><p>Select a principal and record the family, ownership, wealth, governance, and destination facts.</p></div>}
      </section>
    </div>

    {assessments.length ? <section className="panel advisory-history"><header className="advisory-panel-head"><div><span className="eyebrow">Immutable ledger</span><h3>Family-office assessments</h3></div><span>{assessments.length} recorded</span></header><div className="advisory-history-list">{assessments.map((item) => <button type="button" className={selected?.id === item.id ? "active" : ""} onClick={() => setSelectedId(item.id)} key={item.id}><span><strong>{item.family_office_name || leads.find((lead) => lead.id === item.lead_id)?.full_name || "Private client"}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span><b>{Math.round(item.readiness_score)}</b><StatusBadge value={item.status} /></button>)}</div></section> : null}
  </WorkspaceShell>;
}

function EvidenceSelect({ value, onChange }: { value: EvidenceStatus; onChange: (value: EvidenceStatus) => void }) {
  return <select value={value} onChange={(event) => onChange(event.target.value as EvidenceStatus)}><option value="unconfirmed">Unconfirmed</option><option value="documented">Documented</option><option value="independently_verified">Independently verified</option></select>;
}

function FamilyOfficeResult({ assessment, reviewNotes, setReviewNotes, review, working }: {
  assessment: FamilyOfficeAssessment; reviewNotes: string; setReviewNotes: (value: string) => void;
  review: (decision: "approved" | "revision_required") => void; working: string | null;
}) {
  const style = { "--score": Math.max(0, Math.min(100, assessment.readiness_score)) } as CSSProperties;
  const components = [
    ["Identity", assessment.identity_score],
    ["Wealth evidence", assessment.wealth_evidence_score],
    ["Ownership", assessment.ownership_transparency_score],
    ["Governance", assessment.governance_score],
    ["Mobility", assessment.mobility_grounding_score],
  ] as const;
  return <>
    <div className="panel family-office-score">
      <header className="advisory-panel-head"><div><span className="eyebrow">Current execution readiness</span><h3>{titleCase(assessment.readiness_band)}</h3></div><StatusBadge value={assessment.status} /></header>
      <div className="family-office-score-body"><div className="feasibility-meter" style={style}><div><strong>{Math.round(assessment.readiness_score)}</strong><span>/ 100</span></div></div><div className="family-office-components">{components.map(([label, score]) => <div key={label}><span>{label}</span><strong>{Math.round(score)}</strong><i><em style={{ width: `${score}%` }} /></i></div>)}</div></div>
      <p>{assessment.score_semantics}</p>
    </div>
    <div className="family-office-workstreams">
      {assessment.workstreams.map((stream, index) => <article className="panel" key={stream.workstream_key}><header><span>0{index + 1}</span><StatusBadge value={stream.readiness_band} /></header><h3>{stream.title}</h3><strong>{Math.round(stream.readiness_score)}%</strong>{stream.blockers.length ? <ul>{stream.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul> : <p>{stream.findings[0]}</p>}<small>{stream.next_actions[0]}</small></article>)}
    </div>
    <div className="panel family-office-actions"><header className="advisory-panel-head"><div><span className="eyebrow">Controlled execution sequence</span><h3>Next accountable actions</h3></div><span className="advisory-step">02</span></header><ol>{assessment.next_actions.map((action) => <li key={action}>{action}</li>)}</ol></div>
    {assessment.status === "pending_review" ? <div className="panel family-office-review"><label className="advisory-field"><span>Independent review record</span><textarea minLength={10} rows={3} value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} placeholder="Record the workstreams, evidence, ownership, screening, specialist, and source-grounding checks performed." /></label><div><button type="button" className="button secondary" disabled={working === "review" || reviewNotes.trim().length < 10} onClick={() => review("revision_required")}>Require revision</button><button type="button" className="button primary" disabled={working === "review" || reviewNotes.trim().length < 10} onClick={() => review("approved")}>{working === "review" ? "Recording…" : "Approve control map"}</button></div><small>The assessment creator cannot approve their own output.</small></div> : null}
  </>;
}
