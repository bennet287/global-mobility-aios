"use client";

import { CSSProperties, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  InvestmentProgram, InvestmentSuitabilityAssessment, Lead,
  createInvestmentSuitabilityAssessment, getLeads, listInvestmentPrograms, listInvestmentSuitabilityAssessments,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const emptyForm = {
  lead_id: "", program_ids: [] as string[], available_capital: "", liquid_capital: "", net_worth: "",
  currency: "EUR", risk_tolerance: "balanced" as "conservative" | "balanced" | "growth",
  family_members: "1", timeline_months: "18", capital_preservation_required: false,
  lawful_source_of_funds_confirmed: false, disclosed_constraints: "", document_record_ids: "",
};

function values(text: string) { return text.split(/[\n,]/).map((item) => item.trim()).filter(Boolean); }
function minor(text: string) { return text ? Math.round(Number(text) * 100) : undefined; }

export default function InvestmentSuitabilityPage() {
  const { health } = useBackendStatus();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [programs, setPrograms] = useState<InvestmentProgram[]>([]);
  const [assessments, setAssessments] = useState<InvestmentSuitabilityAssessment[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [leadRows, programRows, assessmentRows] = await Promise.all([
        getLeads(), listInvestmentPrograms({ catalogue_status: "active" }), listInvestmentSuitabilityAssessments(),
      ]);
      setLeads(leadRows); setPrograms(programRows); setAssessments(assessmentRows);
      setSelectedId((current) => current || assessmentRows[0]?.id || "");
    } catch (err) { setError(err instanceof Error ? err.message : "Investor suitability workspace could not be loaded"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const selected = useMemo(() => assessments.find((item) => item.id === selectedId) || assessments[0] || null, [assessments, selectedId]);
  function toggleProgram(id: string) { setForm((current) => ({ ...current, program_ids: current.program_ids.includes(id) ? current.program_ids.filter((item) => item !== id) : [...current.program_ids, id] })); }

  async function submit(event: FormEvent) {
    event.preventDefault(); setWorking(true); setError(null); setMessage(null);
    try {
      const created = await createInvestmentSuitabilityAssessment({
        lead_id: form.lead_id, program_ids: form.program_ids,
        target_countries: form.program_ids.length ? [] : [...new Set(programs.map((item) => item.country))],
        available_capital_minor: minor(form.available_capital) || 0,
        ...(minor(form.liquid_capital) !== undefined ? { liquid_capital_minor: minor(form.liquid_capital) } : {}),
        ...(minor(form.net_worth) !== undefined ? { net_worth_minor: minor(form.net_worth) } : {}),
        currency: form.currency.toUpperCase(), risk_tolerance: form.risk_tolerance,
        family_members: Number(form.family_members), timeline_months: Number(form.timeline_months),
        capital_preservation_required: form.capital_preservation_required,
        lawful_source_of_funds_confirmed: form.lawful_source_of_funds_confirmed,
        disclosed_constraints: values(form.disclosed_constraints), document_record_ids: values(form.document_record_ids),
      });
      setAssessments((current) => [created, ...current]); setSelectedId(created.id);
      setMessage("Comparison created from independently published program versions and queued for human review.");
    } catch (err) { setError(err instanceof Error ? err.message : "Suitability comparison could not be created"); }
    finally { setWorking(false); }
  }

  return <WorkspaceShell health={health}>
    <Topbar title="Investor Suitability" kicker="Phase 11 · Client-specific mobility readiness" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />
    <section className="suitability-hero">
      <div><span className="eyebrow">Evidence before commitment</span><h2>Compare routes around the client—not the threshold.</h2><p>Evaluate capital coverage, controlled evidence, family scope, currency, and risk constraints against only independently published program versions.</p></div>
      <div className="suitability-control"><strong>{programs.length}</strong><span>Published programs available</span><small>No eligibility, return, tax, or approval prediction</small></div>
    </section>
    {error ? <InlineNotice label="Comparison stopped" detail={error} tone="bad" /> : null}
    {message ? <InlineNotice label="Comparison ready" detail={message} tone="good" /> : null}

    <div className="suitability-layout">
      <form className="panel suitability-form" onSubmit={submit}>
        <header className="advisory-panel-head"><div><span className="eyebrow">Client facts</span><h3>Build comparison</h3></div><span className="advisory-step">01</span></header>
        <label className="advisory-field"><span>Client</span><select required value={form.lead_id} onChange={(e) => setForm({ ...form, lead_id: e.target.value })}><option value="">Select client</option>{leads.map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name}</option>)}</select></label>
        <div className="suitability-money-grid">
          <label className="advisory-field"><span>Available capital</span><input required type="number" min="0" step="0.01" value={form.available_capital} onChange={(e) => setForm({ ...form, available_capital: e.target.value })} /></label>
          <label className="advisory-field"><span>Liquid capital</span><input type="number" min="0" step="0.01" value={form.liquid_capital} onChange={(e) => setForm({ ...form, liquid_capital: e.target.value })} /></label>
          <label className="advisory-field"><span>Net worth</span><input type="number" min="0" step="0.01" value={form.net_worth} onChange={(e) => setForm({ ...form, net_worth: e.target.value })} /></label>
          <label className="advisory-field"><span>Currency</span><input required minLength={3} maxLength={3} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></label>
          <label className="advisory-field"><span>Family members</span><input required type="number" min="1" value={form.family_members} onChange={(e) => setForm({ ...form, family_members: e.target.value })} /></label>
          <label className="advisory-field"><span>Timeline months</span><input required type="number" min="1" value={form.timeline_months} onChange={(e) => setForm({ ...form, timeline_months: e.target.value })} /></label>
        </div>
        <label className="advisory-field"><span>Risk posture</span><select value={form.risk_tolerance} onChange={(e) => setForm({ ...form, risk_tolerance: e.target.value as typeof form.risk_tolerance })}><option value="conservative">Conservative</option><option value="balanced">Balanced</option><option value="growth">Growth</option></select></label>
        <div className="suitability-program-picker"><span>Programs to compare</span>{programs.length ? programs.map((program) => <label className={form.program_ids.includes(program.id) ? "selected" : ""} key={program.id}><input type="checkbox" checked={form.program_ids.includes(program.id)} onChange={() => toggleProgram(program.id)} /><span><strong>{program.name}</strong><small>{titleCase(program.country)} · {titleCase(program.program_type)}</small></span><b>{program.current_version ? new Intl.NumberFormat("en", { style: "currency", currency: program.current_version.currency, maximumFractionDigits: 0 }).format(program.current_version.minimum_commitment_minor / 100) : "—"}</b></label>) : <p>No independently published programs are available yet.</p>}</div>
        <label className="advisory-field"><span>Disclosed constraints</span><textarea rows={3} value={form.disclosed_constraints} onChange={(e) => setForm({ ...form, disclosed_constraints: e.target.value })} placeholder="Prior refusals, source-of-funds complexity, banking constraints—one per line" /></label>
        <label className="advisory-field"><span>Controlled evidence document IDs</span><input value={form.document_record_ids} onChange={(e) => setForm({ ...form, document_record_ids: e.target.value })} /></label>
        <div className="advisory-checks"><label><input type="checkbox" checked={form.lawful_source_of_funds_confirmed} onChange={(e) => setForm({ ...form, lawful_source_of_funds_confirmed: e.target.checked })} /><span>Lawful source of funds can be evidenced</span></label><label><input type="checkbox" checked={form.capital_preservation_required} onChange={(e) => setForm({ ...form, capital_preservation_required: e.target.checked })} /><span>Capital preservation is mandatory</span></label></div>
        <button className="button primary" disabled={working || !programs.length}>{working ? "Comparing…" : "Compare published programs"}</button>
      </form>
      <section className="suitability-results">{selected ? <SuitabilityResult assessment={selected} /> : <div className="panel advisory-empty"><span className="eyebrow">No comparison yet</span><h3>Client-specific readiness will appear here.</h3><p>Select a client and one or more independently published programs.</p></div>}</section>
    </div>

    {assessments.length ? <section className="panel advisory-history"><header className="advisory-panel-head"><div><span className="eyebrow">Comparison ledger</span><h3>Immutable assessments</h3></div><span>{assessments.length} recorded</span></header><div className="advisory-history-list">{assessments.map((item) => <button type="button" className={selected?.id === item.id ? "active" : ""} onClick={() => setSelectedId(item.id)} key={item.id}><span><strong>{leads.find((lead) => lead.id === item.lead_id)?.full_name || "Client comparison"}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span><b>{Math.round(item.overall_readiness_score)}</b><StatusBadge value={item.status} /></button>)}</div></section> : null}
  </WorkspaceShell>;
}

function SuitabilityResult({ assessment }: { assessment: InvestmentSuitabilityAssessment }) {
  const style = { "--score": Math.max(0, Math.min(100, assessment.overall_readiness_score)) } as CSSProperties;
  return <>
    <div className="panel suitability-score"><header className="advisory-panel-head"><div><span className="eyebrow">Best current readiness</span><h3>{titleCase(assessment.readiness_band)}</h3></div><StatusBadge value={assessment.status} /></header><div><div className="feasibility-meter" style={style}><div><strong>{Math.round(assessment.overall_readiness_score)}</strong><span>/ 100</span></div></div><p>{assessment.score_semantics}</p></div></div>
    <div className="suitability-ranking">{assessment.ranked_programs.map((program, index) => <article className="panel suitability-program" key={program.program_version_id}><header><span>0{index + 1}</span><StatusBadge value={program.readiness_band} /></header><h3>{program.name}</h3><p>{titleCase(program.country)} · {titleCase(program.program_type)}</p><div className="suitability-bars">{[["Capital", program.capital_coverage_score], ["Evidence", program.evidence_score], ["Family", program.family_fit_score], ["Risk", program.risk_alignment_score]].map(([label, score]) => <div key={String(label)}><span>{label}</span><b>{Math.round(Number(score))}</b><i><em style={{ width: `${score}%` }} /></i></div>)}</div>{program.blockers.length ? <section><strong>Material blockers</strong>{program.blockers.map((item) => <p key={item}>{item}</p>)}</section> : null}<footer>Snapshot {program.source_snapshot_id.slice(0, 8)} · version pinned</footer></article>)}</div>
    <div className="panel advisory-action-plan"><header className="advisory-panel-head"><div><span className="eyebrow">Controlled next steps</span><h3>Before committing capital</h3></div><span className="advisory-step">02</span></header><ol>{assessment.next_actions.map((action) => <li key={action}>{action}</li>)}</ol></div>
  </>;
}
