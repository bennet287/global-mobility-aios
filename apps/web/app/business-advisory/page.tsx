"use client";

import { CSSProperties, FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  BusinessAdvisoryAssessment,
  Lead,
  createBusinessAdvisory,
  getLeads,
  listBusinessAdvisories,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const intents = [
  "launch_startup",
  "expand_existing_business",
  "founder_relocation",
  "passive_investment",
  "family_office_relocation",
  "tax_residency_planning",
  "asset_and_family_mobility",
] as const;

const emptyForm = {
  lead_id: "",
  primary_intent: "expand_existing_business",
  situation: "",
  target_countries: "",
  capital_available: "",
  net_worth: "",
  annual_revenue: "",
  currency: "EUR",
  employees: "",
  business_age_years: "",
  founder_experience_years: "",
  timeline_months: "",
  family_relocation: false,
  lawful_source_of_funds_confirmed: false,
  risk_disclosures: "",
  document_record_ids: "",
};

type AdvisoryForm = typeof emptyForm;

function splitValues(value: string) {
  return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
}

function minorUnits(value: string) {
  if (!value.trim()) return undefined;
  return Math.round(Number(value) * 100);
}

function optionalNumber(value: string) {
  return value.trim() ? Number(value) : undefined;
}

export default function BusinessAdvisoryPage() {
  const { health } = useBackendStatus();
  const [assessments, setAssessments] = useState<BusinessAdvisoryAssessment[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [form, setForm] = useState<AdvisoryForm>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [assessmentRows, leadRows] = await Promise.all([listBusinessAdvisories(), getLeads()]);
      setAssessments(assessmentRows);
      setLeads(leadRows);
      setSelectedId((current) => current || assessmentRows[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "The advisory workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const selected = useMemo(
    () => assessments.find((assessment) => assessment.id === selectedId) || assessments[0] || null,
    [assessments, selectedId],
  );

  function update<K extends keyof AdvisoryForm>(key: K, value: AdvisoryForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setWorking(true);
    setError(null);
    setMessage(null);
    try {
      const created = await createBusinessAdvisory({
        ...(form.lead_id ? { lead_id: form.lead_id } : {}),
        primary_intent: form.primary_intent,
        situation: form.situation,
        target_countries: splitValues(form.target_countries),
        ...(minorUnits(form.capital_available) !== undefined ? { capital_available_minor: minorUnits(form.capital_available) } : {}),
        ...(minorUnits(form.net_worth) !== undefined ? { net_worth_minor: minorUnits(form.net_worth) } : {}),
        ...(minorUnits(form.annual_revenue) !== undefined ? { annual_revenue_minor: minorUnits(form.annual_revenue) } : {}),
        ...(form.capital_available || form.net_worth || form.annual_revenue ? { currency: form.currency.toUpperCase() } : {}),
        ...(optionalNumber(form.employees) !== undefined ? { employees: optionalNumber(form.employees) } : {}),
        ...(optionalNumber(form.business_age_years) !== undefined ? { business_age_years: optionalNumber(form.business_age_years) } : {}),
        ...(optionalNumber(form.founder_experience_years) !== undefined ? { founder_experience_years: optionalNumber(form.founder_experience_years) } : {}),
        ...(optionalNumber(form.timeline_months) !== undefined ? { timeline_months: optionalNumber(form.timeline_months) } : {}),
        family_relocation: form.family_relocation,
        lawful_source_of_funds_confirmed: form.lawful_source_of_funds_confirmed,
        risk_disclosures: splitValues(form.risk_disclosures),
        document_record_ids: splitValues(form.document_record_ids),
      });
      setAssessments((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setSelectedId(created.id);
      setMessage("A decision-support assessment was created and placed into independent human review.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "The assessment could not be created");
    } finally {
      setWorking(false);
    }
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Business & Wealth Advisor"
        kicker="Phase 11 · Evidence-grounded strategy"
        loadStatus={loading ? "loading" : error ? "partial" : "ready"}
        onRefresh={() => void load()}
      />

      <section className="advisory-hero">
        <div>
          <span className="eyebrow">Strategic mobility intelligence</span>
          <h2>Turn a complex situation into viable routes.</h2>
          <p>Compare commercial mobility strategies, expose blockers early, and convert uncertainty into an evidence-led action plan.</p>
        </div>
        <div className="advisory-principles" aria-label="Advisory controls">
          <span>Published pathways only</span>
          <span>Evidence-weighted scoring</span>
          <span>Independent human review</span>
        </div>
      </section>

      {error ? <InlineNotice label="Advisory unavailable" detail={error} tone="bad" /> : null}
      {message ? <InlineNotice label="Assessment ready" detail={message} tone="good" /> : null}

      <div className="advisory-layout">
        <form className="panel advisory-form" onSubmit={submit}>
          <header className="advisory-panel-head">
            <div><span className="eyebrow">Situation brief</span><h3>Describe the commercial objective</h3></div>
            <span className="advisory-step">01</span>
          </header>

          <label className="advisory-field wide">
            <span>Primary intention</span>
            <select value={form.primary_intent} onChange={(event) => update("primary_intent", event.target.value)}>
              {intents.map((intent) => <option value={intent} key={intent}>{titleCase(intent)}</option>)}
            </select>
          </label>
          <label className="advisory-field wide">
            <span>Situation and desired outcome</span>
            <textarea required minLength={30} maxLength={12000} rows={6} value={form.situation} onChange={(event) => update("situation", event.target.value)} placeholder="Explain the business, ownership, mobility objective, constraints, timing, family considerations, and what success should look like." />
          </label>
          <div className="advisory-form-grid">
            <label className="advisory-field">
              <span>Target countries</span>
              <input required value={form.target_countries} onChange={(event) => update("target_countries", event.target.value)} placeholder="Austria, UAE, Singapore" />
            </label>
            <label className="advisory-field">
              <span>Linked client (optional)</span>
              <select value={form.lead_id} onChange={(event) => update("lead_id", event.target.value)}>
                <option value="">Unlinked scenario</option>
                {leads.map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name}</option>)}
              </select>
            </label>
            <label className="advisory-field"><span>Available capital</span><input type="number" min="0" step="0.01" value={form.capital_available} onChange={(event) => update("capital_available", event.target.value)} /></label>
            <label className="advisory-field"><span>Net worth</span><input type="number" min="0" step="0.01" value={form.net_worth} onChange={(event) => update("net_worth", event.target.value)} /></label>
            <label className="advisory-field"><span>Annual revenue</span><input type="number" min="0" step="0.01" value={form.annual_revenue} onChange={(event) => update("annual_revenue", event.target.value)} /></label>
            <label className="advisory-field"><span>Currency</span><input minLength={3} maxLength={3} value={form.currency} onChange={(event) => update("currency", event.target.value)} /></label>
            <label className="advisory-field"><span>Employees</span><input type="number" min="0" value={form.employees} onChange={(event) => update("employees", event.target.value)} /></label>
            <label className="advisory-field"><span>Business age (years)</span><input type="number" min="0" step="0.5" value={form.business_age_years} onChange={(event) => update("business_age_years", event.target.value)} /></label>
            <label className="advisory-field"><span>Founder experience (years)</span><input type="number" min="0" step="0.5" value={form.founder_experience_years} onChange={(event) => update("founder_experience_years", event.target.value)} /></label>
            <label className="advisory-field"><span>Target timeline (months)</span><input type="number" min="1" value={form.timeline_months} onChange={(event) => update("timeline_months", event.target.value)} /></label>
          </div>
          <label className="advisory-field wide"><span>Material risks or prior issues</span><textarea rows={3} value={form.risk_disclosures} onChange={(event) => update("risk_disclosures", event.target.value)} placeholder="Refusals, litigation, tax issues, sanctions exposure, source-of-funds complexity — one per line." /></label>
          <label className="advisory-field wide"><span>Evidence document IDs</span><input value={form.document_record_ids} onChange={(event) => update("document_record_ids", event.target.value)} placeholder="Optional verified document UUIDs, separated by commas" /></label>
          <div className="advisory-checks">
            <label><input type="checkbox" checked={form.family_relocation} onChange={(event) => update("family_relocation", event.target.checked)} /><span>Family relocation is part of the objective</span></label>
            <label><input type="checkbox" checked={form.lawful_source_of_funds_confirmed} onChange={(event) => update("lawful_source_of_funds_confirmed", event.target.checked)} /><span>Lawful source of funds can be evidenced</span></label>
          </div>
          <button className="button primary advisory-submit" type="submit" disabled={working}>{working ? "Building strategy…" : "Build strategic assessment"}</button>
          <p className="advisory-disclaimer">Decision support only. It does not predict an authority decision or replace licensed legal, tax, or investment advice.</p>
        </form>

        <section className="advisory-result">
          {selected ? <AssessmentResult assessment={selected} /> : (
            <div className="panel advisory-empty">
              <span className="eyebrow">Strategic output</span>
              <h3>Your ranked route map will appear here.</h3>
              <p>Complete the situation brief to receive three commercially distinct options, readiness scoring, blockers, and next actions.</p>
            </div>
          )}
        </section>
      </div>

      {assessments.length ? (
        <section className="panel advisory-history">
          <header className="advisory-panel-head"><div><span className="eyebrow">Assessment ledger</span><h3>Recent strategic briefs</h3></div><span>{assessments.length} recorded</span></header>
          <div className="advisory-history-list">
            {assessments.map((assessment) => (
              <button type="button" className={assessment.id === selected?.id ? "active" : ""} onClick={() => setSelectedId(assessment.id)} key={assessment.id}>
                <span><strong>{titleCase(assessment.primary_intent)}</strong><small>{new Date(assessment.created_at).toLocaleString()}</small></span>
                <b>{Math.round(assessment.feasibility_score)}</b>
                <StatusBadge value={assessment.status} />
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </WorkspaceShell>
  );
}

function AssessmentResult({ assessment }: { assessment: BusinessAdvisoryAssessment }) {
  const meterStyle = { "--score": Math.max(0, Math.min(100, assessment.feasibility_score)) } as CSSProperties;
  const scoreRows = [
    ["Information", assessment.information_score],
    ["Evidence", assessment.evidence_score],
    ["Commercial fit", assessment.commercial_fit_score],
    ["Pathway grounding", assessment.pathway_grounding_score],
  ] as const;

  return (
    <>
      <div className="panel advisory-score-card">
        <header className="advisory-panel-head">
          <div><span className="eyebrow">Feasibility readiness</span><h3>{titleCase(assessment.feasibility_band)}</h3></div>
          <StatusBadge value={assessment.status} />
        </header>
        <div className="advisory-score-main">
          <div className="feasibility-meter" style={meterStyle}><div><strong>{Math.round(assessment.feasibility_score)}</strong><span>/ 100</span></div></div>
          <div>
            <p>{assessment.score_semantics}</p>
            <div className="advisory-score-grid">
              {scoreRows.map(([label, score]) => <div key={label}><span>{label}</span><strong>{Math.round(score)}</strong><i><em style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></i></div>)}
            </div>
          </div>
        </div>
        {assessment.escalation_required ? <InlineNotice label="Specialist escalation required" detail="Material risk or verification gaps require qualified human review before this strategy is used." tone="warn" /> : null}
      </div>

      <div className="strategy-grid">
        {assessment.strategy_options.map((strategy, index) => (
          <article className="panel strategy-card" key={strategy.strategy_key}>
            <header><span>0{index + 1}</span><StatusBadge value={strategy.verification_state} /></header>
            <div className="strategy-title"><h3>{strategy.title}</h3><strong>{Math.round(strategy.fit_score)}<small>/100 fit</small></strong></div>
            <p>{strategy.rationale[0] || "A candidate route for human evaluation."}</p>
            <div className="strategy-detail"><span>Why it fits</span><ul>{strategy.rationale.slice(1).map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div className="strategy-detail"><span>Next moves</span><ol>{strategy.next_actions.slice(0, 4).map((item) => <li key={item}>{item}</li>)}</ol></div>
            {strategy.blockers.length ? <div className="strategy-blockers"><span>Blockers</span>{strategy.blockers.map((item) => <p key={item}>{item}</p>)}</div> : null}
            <footer>{strategy.published_pathways.length ? `${strategy.published_pathways.length} published pathway${strategy.published_pathways.length === 1 ? "" : "s"} linked` : "No published pathway linked"}</footer>
          </article>
        ))}
      </div>

      <div className="panel advisory-action-plan">
        <header className="advisory-panel-head"><div><span className="eyebrow">Execution sequence</span><h3>What to do next</h3></div><span className="advisory-step">02</span></header>
        <ol>{assessment.next_actions.map((action) => <li key={action}>{action}</li>)}</ol>
        {assessment.blockers.length ? <div><strong>Current blockers</strong>{assessment.blockers.map((blocker) => <p key={blocker}>{blocker}</p>)}</div> : null}
      </div>
    </>
  );
}
