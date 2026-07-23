"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  CorporateAccount,
  CorporateCaseDependant,
  CorporateCaseSponsorAssignment,
  CorporateComplianceEvent,
  CorporateMobilityCase,
  CorporateRelocationTask,
  CorporateSponsorEntity,
  EntrepreneurVentureProfile,
  Lead,
  VentureEvidenceItem,
  addVentureEvidence,
  addCaseDependant,
  assignCorporateSponsor,
  createCorporateAccount,
  createCorporateSponsor,
  createComplianceEvent,
  createCorporateMobilityCase,
  createRelocationTask,
  createVentureProfile,
  getLeads,
  getVentureProfile,
  listCorporateAccounts,
  listCorporateSponsors,
  listCaseDependants,
  listCaseSponsorAssignments,
  listComplianceEvents,
  listCorporateMobilityCases,
  listRelocationTasks,
  listVentureEvidence,
  resolveComplianceEvent,
  transitionRelocationTask,
  submitVentureProfile,
  updateCorporateMobilityCase,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";


const emptyAccountForm = {
  legal_name: "",
  display_name: "",
  primary_country: "",
  registration_number: "",
  contact_name: "",
  contact_email: "",
  compliance_owner: "",
};

const emptyCaseForm = {
  employee_lead_id: "",
  case_type: "employee_relocation" as "employee_relocation" | "dependant" | "sponsor_compliance" | "entrepreneur_startup",
  origin_country: "",
  destination_country: "",
  sponsor_name: "",
  compliance_due_date: "",
  target_start_date: "",
};

const emptySponsorForm = { legal_name: "", sponsor_type: "employing_entity" as const, country: "" };
const emptyDependantForm = { dependant_lead_id: "", relationship_to_employee: "spouse" as "spouse" | "partner" | "child" | "parent" | "other", sponsorship_required: false };
const emptyEventForm = { event_type: "filing_deadline" as "filing_deadline" | "document_expiry" | "permit_renewal" | "registration" | "sponsor_report" | "payroll" | "tax" | "custom", title: "", due_at: "", evidence_required: true };
const emptyTaskForm = { title: "", category: "relocation" as "immigration" | "relocation" | "payroll" | "tax" | "housing" | "travel" | "onboarding" | "custom", owner_role: "mobility_operator", due_at: "", depends_on_task_id: "", requires_human_approval: false };
const emptyVentureForm = { founder_lead_id: "", venture_name: "", venture_stage: "idea" as "idea" | "pre_seed" | "seed" | "growth" | "established", sector: "", incorporation_country: "", founder_role: "Founder", business_model_summary: "" };
const emptyEvidenceForm = { evidence_type: "business_plan" as "business_plan" | "incorporation" | "bank_statement" | "investment_commitment" | "grant" | "revenue" | "capitalization" | "intellectual_property" | "other", title: "", declared_amount_minor: "", currency: "", document_record_id: "" };


export default function CorporateMobilityPage() {
  const { health } = useBackendStatus();
  const [accounts, setAccounts] = useState<CorporateAccount[]>([]);
  const [cases, setCases] = useState<CorporateMobilityCase[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [accountForm, setAccountForm] = useState(emptyAccountForm);
  const [caseForm, setCaseForm] = useState(emptyCaseForm);
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [sponsors, setSponsors] = useState<CorporateSponsorEntity[]>([]);
  const [assignments, setAssignments] = useState<CorporateCaseSponsorAssignment[]>([]);
  const [dependants, setDependants] = useState<CorporateCaseDependant[]>([]);
  const [events, setEvents] = useState<CorporateComplianceEvent[]>([]);
  const [tasks, setTasks] = useState<CorporateRelocationTask[]>([]);
  const [venture, setVenture] = useState<EntrepreneurVentureProfile | null>(null);
  const [ventureEvidence, setVentureEvidence] = useState<VentureEvidenceItem[]>([]);
  const [sponsorForm, setSponsorForm] = useState(emptySponsorForm);
  const [dependantForm, setDependantForm] = useState(emptyDependantForm);
  const [eventForm, setEventForm] = useState(emptyEventForm);
  const [taskForm, setTaskForm] = useState(emptyTaskForm);
  const [ventureForm, setVentureForm] = useState(emptyVentureForm);
  const [evidenceForm, setEvidenceForm] = useState(emptyEvidenceForm);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [accountRows, caseRows, leadRows] = await Promise.all([
        listCorporateAccounts(),
        listCorporateMobilityCases(),
        getLeads(),
      ]);
      setAccounts(accountRows);
      setCases(caseRows);
      setLeads(leadRows);
      setSelectedAccountId((current) => current || accountRows[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Corporate mobility workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedAccount = accounts.find((account) => account.id === selectedAccountId) || null;
  const selectedCases = cases.filter((item) => item.corporate_account_id === selectedAccountId);
  const selectedCase = selectedCases.find((item) => item.id === selectedCaseId) || selectedCases[0] || null;
  const leadNames = useMemo(() => new Map(leads.map((lead) => [lead.id, lead.full_name])), [leads]);
  const activeCases = cases.filter((item) => item.status === "active").length;
  const complianceDue = cases.filter((item) => item.compliance_due_date && !["completed", "closed"].includes(item.status)).length;

  const loadRelationships = useCallback(async () => {
    if (!selectedAccountId) {
      setSponsors([]);
      return;
    }
    const sponsorRows = await listCorporateSponsors(selectedAccountId);
    setSponsors(sponsorRows);
    if (!selectedCase) {
      setAssignments([]); setDependants([]); setEvents([]); setTasks([]); setVenture(null); setVentureEvidence([]);
      return;
    }
    const [assignmentRows, dependantRows, eventRows, taskRows] = await Promise.all([
      listCaseSponsorAssignments(selectedCase.id), listCaseDependants(selectedCase.id), listComplianceEvents(selectedCase.id), listRelocationTasks(selectedCase.id),
    ]);
    setAssignments(assignmentRows); setDependants(dependantRows); setEvents(eventRows); setTasks(taskRows);
    if (selectedCase.case_type === "entrepreneur_startup") {
      const ventureRow = await getVentureProfile(selectedCase.id).catch(() => null);
      setVenture(ventureRow);
      setVentureEvidence(ventureRow ? await listVentureEvidence(ventureRow.id) : []);
    } else {
      setVenture(null); setVentureEvidence([]);
    }
  }, [selectedAccountId, selectedCase?.id]);

  useEffect(() => { void loadRelationships().catch((err) => setError(err instanceof Error ? err.message : "Case relationships could not be loaded")); }, [loadRelationships]);

  async function submitAccount(event: FormEvent) {
    event.preventDefault();
    setWorking("account");
    setError(null);
    setMessage(null);
    try {
      const created = await createCorporateAccount(accountForm);
      setAccountForm(emptyAccountForm);
      await load();
      setSelectedAccountId(created.id);
      setMessage(`${created.display_name || created.legal_name} is ready for controlled mobility cases.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Corporate account could not be created");
    } finally {
      setWorking(null);
    }
  }

  async function submitCase(event: FormEvent) {
    event.preventDefault();
    if (!selectedAccountId) return;
    setWorking("case");
    setError(null);
    setMessage(null);
    try {
      const created = await createCorporateMobilityCase(selectedAccountId, {
        case_type: caseForm.case_type,
        destination_country: caseForm.destination_country,
        ...(caseForm.employee_lead_id ? { employee_lead_id: caseForm.employee_lead_id } : {}),
        ...(caseForm.origin_country ? { origin_country: caseForm.origin_country } : {}),
        ...(caseForm.sponsor_name ? { sponsor_name: caseForm.sponsor_name } : {}),
        ...(caseForm.compliance_due_date ? { compliance_due_date: caseForm.compliance_due_date } : {}),
        ...(caseForm.target_start_date ? { target_start_date: caseForm.target_start_date } : {}),
      });
      setCaseForm(emptyCaseForm);
      await load();
      setMessage(`${created.case_reference} was created with human review required.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Corporate mobility case could not be created");
    } finally {
      setWorking(null);
    }
  }

  async function transitionCase(item: CorporateMobilityCase, status: "active" | "on_hold" | "completed" | "closed") {
    setWorking(item.id);
    setError(null);
    setMessage(null);
    try {
      await updateCorporateMobilityCase(item.id, { status });
      await load();
      setMessage(`${item.case_reference} moved to ${titleCase(status)}. The audit and review gates remain active.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Case status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  async function submitSponsor(event: FormEvent) {
    event.preventDefault();
    if (!selectedAccountId) return;
    setWorking("sponsor"); setError(null);
    try {
      await createCorporateSponsor(selectedAccountId, sponsorForm);
      setSponsorForm(emptySponsorForm); await loadRelationships();
      setMessage("Sponsor entity added to the governed account registry.");
    } catch (err) { setError(err instanceof Error ? err.message : "Sponsor could not be created"); }
    finally { setWorking(null); }
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCase) return;
    const sponsorId = new FormData(event.currentTarget).get("sponsor_entity_id")?.toString();
    if (!sponsorId) return;
    setWorking("assignment"); setError(null);
    try {
      await assignCorporateSponsor(selectedCase.id, sponsorId); await loadRelationships();
      setMessage("Sponsor assigned with immutable audit history.");
    } catch (err) { setError(err instanceof Error ? err.message : "Sponsor could not be assigned"); }
    finally { setWorking(null); }
  }

  async function submitDependant(event: FormEvent) {
    event.preventDefault();
    if (!selectedCase || !dependantForm.dependant_lead_id) return;
    setWorking("dependant"); setError(null);
    try {
      await addCaseDependant(selectedCase.id, dependantForm); setDependantForm(emptyDependantForm);
      await loadRelationships(); setMessage("Dependant linked to the selected case.");
    } catch (err) { setError(err instanceof Error ? err.message : "Dependant could not be linked"); }
    finally { setWorking(null); }
  }

  async function submitEvent(event: FormEvent) {
    event.preventDefault();
    if (!selectedCase) return;
    setWorking("event"); setError(null);
    try {
      await createComplianceEvent(selectedCase.id, eventForm); setEventForm(emptyEventForm);
      await loadRelationships(); setMessage("Review-gated compliance event scheduled.");
    } catch (err) { setError(err instanceof Error ? err.message : "Compliance event could not be created"); }
    finally { setWorking(null); }
  }

  async function completeEvent(item: CorporateComplianceEvent) {
    setWorking(item.id); setError(null);
    try {
      await resolveComplianceEvent(item.id, "completed", "Completed by a human operator.");
      await loadRelationships(); setMessage(`${item.title} marked complete by the current operator.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Compliance event could not be completed"); }
    finally { setWorking(null); }
  }

  async function submitTask(event: FormEvent) {
    event.preventDefault();
    if (!selectedCase) return;
    setWorking("task"); setError(null);
    try {
      await createRelocationTask(selectedCase.id, {
        title: taskForm.title, category: taskForm.category, owner_role: taskForm.owner_role,
        requires_human_approval: taskForm.requires_human_approval,
        ...(taskForm.due_at ? { due_at: taskForm.due_at } : {}),
        ...(taskForm.depends_on_task_id ? { depends_on_task_id: taskForm.depends_on_task_id } : {}),
      });
      setTaskForm(emptyTaskForm); await loadRelationships();
      setMessage("Relocation task added to the governed case plan.");
    } catch (err) { setError(err instanceof Error ? err.message : "Relocation task could not be created"); }
    finally { setWorking(null); }
  }

  async function moveTask(item: CorporateRelocationTask, status: "ready" | "in_progress" | "completed") {
    setWorking(item.id); setError(null);
    try {
      const updated = await transitionRelocationTask(item.id, { status, work_notes: status === "completed" ? "Work submitted by the current operator." : undefined });
      await loadRelationships();
      setMessage(updated.status === "awaiting_approval" ? `${item.title} is awaiting an independent reviewer.` : `${item.title} moved to ${titleCase(updated.status)}.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Relocation task could not be updated"); }
    finally { setWorking(null); }
  }

  async function submitVenture(event: FormEvent) {
    event.preventDefault();
    if (!selectedCase || !ventureForm.founder_lead_id) return;
    setWorking("venture"); setError(null);
    try {
      await createVentureProfile(selectedCase.id, {
        founder_lead_id: ventureForm.founder_lead_id, venture_name: ventureForm.venture_name,
        venture_stage: ventureForm.venture_stage, sector: ventureForm.sector,
        founder_role: ventureForm.founder_role, business_model_summary: ventureForm.business_model_summary,
        target_country: selectedCase.destination_country,
        ...(ventureForm.incorporation_country ? { incorporation_country: ventureForm.incorporation_country } : {}),
      });
      setVentureForm(emptyVentureForm); await loadRelationships();
      setMessage("Founder venture dossier created with mandatory human review.");
    } catch (err) { setError(err instanceof Error ? err.message : "Venture dossier could not be created"); }
    finally { setWorking(null); }
  }

  async function submitVentureEvidenceItem(event: FormEvent) {
    event.preventDefault();
    if (!venture) return;
    setWorking("venture-evidence"); setError(null);
    try {
      await addVentureEvidence(venture.id, {
        evidence_type: evidenceForm.evidence_type, title: evidenceForm.title,
        ...(evidenceForm.declared_amount_minor ? { declared_amount_minor: Number(evidenceForm.declared_amount_minor), currency: evidenceForm.currency } : {}),
        ...(evidenceForm.document_record_id ? { document_record_id: evidenceForm.document_record_id } : {}),
      });
      setEvidenceForm(emptyEvidenceForm); await loadRelationships();
      setMessage("Venture evidence added without making a funding or eligibility claim.");
    } catch (err) { setError(err instanceof Error ? err.message : "Venture evidence could not be added"); }
    finally { setWorking(null); }
  }

  async function sendVentureForReview() {
    if (!venture) return;
    setWorking("venture-submit"); setError(null);
    try {
      await submitVentureProfile(venture.id); await loadRelationships();
      setMessage("Venture dossier sent to an independent completeness reviewer.");
    } catch (err) { setError(err instanceof Error ? err.message : "Venture dossier could not be submitted"); }
    finally { setWorking(null); }
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Corporate Mobility"
        kicker="Phase 11 · Employer-controlled relocation"
        loadStatus={loading ? "loading" : error ? "partial" : health ? "ready" : "offline"}
        onRefresh={load}
      />

      <section className="corporate-overview">
        <div>
          <span>Business mobility foundation</span>
          <h2>Relocations with accountable ownership.</h2>
          <p>Corporate accounts and employee cases remain linked to existing profiles, evidence, review gates, and immutable audit history.</p>
        </div>
        <div className="corporate-overview-metrics">
          <article><span>Accounts</span><strong>{accounts.length}</strong></article>
          <article><span>Active cases</span><strong>{activeCases}</strong></article>
          <article><span>Compliance dated</span><strong>{complianceDue}</strong></article>
        </div>
      </section>

      {error ? <InlineNotice label="Corporate mobility unavailable" detail={error} tone="bad" /> : null}
      {message ? <InlineNotice label="Workspace updated" detail={message} tone="good" /> : null}

      <section className="corporate-workspace-grid">
        <aside className="panel corporate-account-panel">
          <SectionTitle label="Employers" title="Corporate accounts" detail={`${accounts.length} governed account${accounts.length === 1 ? "" : "s"}`} />
          <div className="corporate-account-list">
            {accounts.map((account) => (
              <button
                type="button"
                className={account.id === selectedAccountId ? "active" : ""}
                key={account.id}
                onClick={() => setSelectedAccountId(account.id)}
              >
                <span><strong>{account.display_name || account.legal_name}</strong><small>{account.primary_country}</small></span>
                <StatusBadge value={account.account_status} />
              </button>
            ))}
            {!loading && !accounts.length ? <EmptyState title="No corporate accounts" detail="Create the first governed employer account." /> : null}
          </div>

          <form className="corporate-form" onSubmit={submitAccount}>
            <h3>New corporate account</h3>
            <label>Legal name<input required value={accountForm.legal_name} onChange={(event) => setAccountForm({ ...accountForm, legal_name: event.target.value })} /></label>
            <div className="corporate-form-row">
              <label>Display name<input value={accountForm.display_name} onChange={(event) => setAccountForm({ ...accountForm, display_name: event.target.value })} /></label>
              <label>Primary country<input required value={accountForm.primary_country} onChange={(event) => setAccountForm({ ...accountForm, primary_country: event.target.value })} /></label>
            </div>
            <label>Registration number<input value={accountForm.registration_number} onChange={(event) => setAccountForm({ ...accountForm, registration_number: event.target.value })} /></label>
            <div className="corporate-form-row">
              <label>Contact name<input value={accountForm.contact_name} onChange={(event) => setAccountForm({ ...accountForm, contact_name: event.target.value })} /></label>
              <label>Contact email<input type="email" value={accountForm.contact_email} onChange={(event) => setAccountForm({ ...accountForm, contact_email: event.target.value })} /></label>
            </div>
            <label>Compliance owner<input value={accountForm.compliance_owner} onChange={(event) => setAccountForm({ ...accountForm, compliance_owner: event.target.value })} /></label>
            <button className="button primary" disabled={working === "account"}>{working === "account" ? "Creating…" : "Create account"}</button>
          </form>
        </aside>

        <main className="panel corporate-case-panel">
          <div className="panel-header-row">
            <SectionTitle
              label="Relocation ledger"
              title={selectedAccount ? selectedAccount.display_name || selectedAccount.legal_name : "Select an account"}
              detail={selectedAccount ? `${selectedCases.length} mobility case${selectedCases.length === 1 ? "" : "s"} · ${selectedAccount.compliance_owner || "No compliance owner assigned"}` : "Cases are scoped to one corporate account"}
            />
            {selectedAccount ? <StatusBadge value={selectedAccount.account_status} /> : null}
          </div>

          <div className="corporate-case-list">
            {selectedCases.map((item) => (
              <article key={item.id} className={selectedCase?.id === item.id ? "selected" : ""} onClick={() => setSelectedCaseId(item.id)}>
                <div className="corporate-case-heading">
                  <div><span>{titleCase(item.case_type)}</span><strong>{item.case_reference}</strong></div>
                  <StatusBadge value={item.status} />
                </div>
                <div className="corporate-case-route">
                  <span>{item.origin_country || "Origin pending"}</span><i>→</i><strong>{item.destination_country}</strong>
                </div>
                <div className="corporate-case-meta">
                  <span>{item.employee_lead_id ? leadNames.get(item.employee_lead_id) || "Linked employee" : "Employee not linked"}</span>
                  <span>{item.compliance_due_date ? `Compliance ${new Date(item.compliance_due_date).toLocaleDateString()}` : "Compliance date pending"}</span>
                  <span>Human review required</span>
                </div>
                <div className="corporate-case-actions">
                  {item.status === "draft" ? <button className="button secondary" disabled={working === item.id} onClick={() => void transitionCase(item, "active")}>Activate</button> : null}
                  {item.status === "active" ? <button className="button secondary" disabled={working === item.id} onClick={() => void transitionCase(item, "on_hold")}>Place on hold</button> : null}
                  {item.status === "active" ? <button className="button secondary" disabled={working === item.id} onClick={() => void transitionCase(item, "completed")}>Complete</button> : null}
                  {item.status === "on_hold" ? <button className="button secondary" disabled={working === item.id} onClick={() => void transitionCase(item, "active")}>Resume</button> : null}
                  {item.status !== "closed" ? <button className="button secondary" disabled={working === item.id} onClick={() => void transitionCase(item, "closed")}>Close</button> : null}
                </div>
              </article>
            ))}
            {selectedAccount && !loading && !selectedCases.length ? <EmptyState title="No mobility cases" detail="Create the first employee, dependant, or sponsor-compliance case." /> : null}
            {!selectedAccount && !loading ? <EmptyState title="No account selected" detail="Choose or create a corporate account to begin." /> : null}
          </div>

          {selectedAccount ? (
            <form className="corporate-form corporate-case-form" onSubmit={submitCase}>
              <h3>New controlled mobility case</h3>
              <div className="corporate-form-row">
                <label>Case type<select value={caseForm.case_type} onChange={(event) => setCaseForm({ ...caseForm, case_type: event.target.value as typeof caseForm.case_type })}><option value="employee_relocation">Employee relocation</option><option value="dependant">Dependant</option><option value="sponsor_compliance">Sponsor compliance</option><option value="entrepreneur_startup">Entrepreneur / startup</option></select></label>
                <label>Employee lead<select value={caseForm.employee_lead_id} onChange={(event) => setCaseForm({ ...caseForm, employee_lead_id: event.target.value })}><option value="">Link later</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name}</option>)}</select></label>
              </div>
              <div className="corporate-form-row">
                <label>Origin country<input value={caseForm.origin_country} onChange={(event) => setCaseForm({ ...caseForm, origin_country: event.target.value })} /></label>
                <label>Destination country<input required value={caseForm.destination_country} onChange={(event) => setCaseForm({ ...caseForm, destination_country: event.target.value })} /></label>
              </div>
              <label>Sponsor name<input value={caseForm.sponsor_name} onChange={(event) => setCaseForm({ ...caseForm, sponsor_name: event.target.value })} /></label>
              <div className="corporate-form-row">
                <label>Compliance due<input type="datetime-local" value={caseForm.compliance_due_date} onChange={(event) => setCaseForm({ ...caseForm, compliance_due_date: event.target.value })} /></label>
                <label>Target start<input type="datetime-local" value={caseForm.target_start_date} onChange={(event) => setCaseForm({ ...caseForm, target_start_date: event.target.value })} /></label>
              </div>
              <InlineNotice label="Safety boundary" detail="Creating or updating a case does not determine eligibility, approve sponsorship, or submit an application. Regulated conclusions remain evidence-backed and human-reviewed." tone="warn" />
              <button className="button primary" disabled={working === "case"}>{working === "case" ? "Creating…" : "Create review-gated case"}</button>
            </form>
          ) : null}

          {selectedCase ? (
            <section className="corporate-control-plane">
              <div className="corporate-control-heading">
                <div><span>Case control plane</span><h3>{selectedCase.case_reference}</h3></div>
                <p>Sponsor, family, and deadline records are separately audited and remain human-controlled.</p>
              </div>
              <div className="corporate-control-grid">
                <article>
                  <span className="eyebrow">Sponsor entity</span>
                  <strong>{assignments.find((item) => item.status === "active") ? sponsors.find((item) => item.id === assignments.find((row) => row.status === "active")?.sponsor_entity_id)?.legal_name || "Assigned sponsor" : "Not assigned"}</strong>
                  <small>{sponsors.length} available for this account</small>
                  <form onSubmit={submitAssignment}>
                    <select name="sponsor_entity_id" aria-label="Sponsor entity" defaultValue=""><option value="" disabled>Select sponsor</option>{sponsors.filter((item) => item.status === "active").map((item) => <option value={item.id} key={item.id}>{item.legal_name}</option>)}</select>
                    <button className="button secondary" disabled={working === "assignment" || selectedCase.status === "closed"}>Assign</button>
                  </form>
                  <details><summary>Add sponsor entity</summary><form onSubmit={submitSponsor} className="corporate-mini-form"><input required placeholder="Legal name" value={sponsorForm.legal_name} onChange={(event) => setSponsorForm({ ...sponsorForm, legal_name: event.target.value })} /><div><select value={sponsorForm.sponsor_type} onChange={(event) => setSponsorForm({ ...sponsorForm, sponsor_type: event.target.value as typeof sponsorForm.sponsor_type })}><option value="employing_entity">Employing entity</option><option value="host_entity">Host entity</option><option value="authorized_agent">Authorized agent</option></select><input required placeholder="Country" value={sponsorForm.country} onChange={(event) => setSponsorForm({ ...sponsorForm, country: event.target.value })} /></div><button className="button secondary" disabled={working === "sponsor"}>Add to registry</button></form></details>
                </article>

                <article>
                  <span className="eyebrow">Dependants</span>
                  <strong>{dependants.filter((item) => item.status === "active").length} linked</strong>
                  <small>Existing lead profiles preserve consent and PII controls.</small>
                  <form className="corporate-mini-form" onSubmit={submitDependant}>
                    <select required value={dependantForm.dependant_lead_id} onChange={(event) => setDependantForm({ ...dependantForm, dependant_lead_id: event.target.value })}><option value="">Select lead</option>{leads.filter((lead) => lead.id !== selectedCase.employee_lead_id).map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name}</option>)}</select>
                    <div><select value={dependantForm.relationship_to_employee} onChange={(event) => setDependantForm({ ...dependantForm, relationship_to_employee: event.target.value as typeof dependantForm.relationship_to_employee })}><option value="spouse">Spouse</option><option value="partner">Partner</option><option value="child">Child</option><option value="parent">Parent</option><option value="other">Other</option></select><label className="corporate-check"><input type="checkbox" checked={dependantForm.sponsorship_required} onChange={(event) => setDependantForm({ ...dependantForm, sponsorship_required: event.target.checked })} />Sponsorship</label></div>
                    <button className="button secondary" disabled={working === "dependant" || selectedCase.status === "closed"}>Link dependant</button>
                  </form>
                </article>

                <article>
                  <span className="eyebrow">Compliance calendar</span>
                  <strong>{events.filter((item) => item.status === "open").length} open</strong>
                  <small>Every completion records the responsible human operator.</small>
                  <div className="corporate-event-list">{events.slice(0, 3).map((item) => <div key={item.id}><span><b>{item.title}</b><small>{new Date(item.due_at).toLocaleDateString()}</small></span><StatusBadge value={item.status} />{item.status === "open" ? <button className="button secondary" disabled={working === item.id} onClick={() => void completeEvent(item)}>Complete</button> : null}</div>)}</div>
                  <details><summary>Schedule event</summary><form onSubmit={submitEvent} className="corporate-mini-form"><input required placeholder="Event title" value={eventForm.title} onChange={(event) => setEventForm({ ...eventForm, title: event.target.value })} /><div><select value={eventForm.event_type} onChange={(event) => setEventForm({ ...eventForm, event_type: event.target.value as typeof eventForm.event_type })}><option value="filing_deadline">Filing deadline</option><option value="document_expiry">Document expiry</option><option value="permit_renewal">Permit renewal</option><option value="registration">Registration</option><option value="sponsor_report">Sponsor report</option><option value="payroll">Payroll</option><option value="tax">Tax</option><option value="custom">Custom</option></select><input required type="datetime-local" value={eventForm.due_at} onChange={(event) => setEventForm({ ...eventForm, due_at: event.target.value })} /></div><button className="button secondary" disabled={working === "event" || selectedCase.status === "closed"}>Schedule</button></form></details>
                </article>
              </div>
              <article className="corporate-task-board">
                <div className="corporate-task-header">
                  <div><span>Relocation orchestration</span><h3>Accountable task sequence</h3><p>Dependencies must finish in order. Sensitive completions wait for a different reviewer.</p></div>
                  <div><strong>{tasks.filter((item) => !["completed", "cancelled"].includes(item.status)).length}</strong><small>open tasks</small></div>
                </div>
                <div className="corporate-task-list">
                  {tasks.map((item, index) => (
                    <div key={item.id}>
                      <span className="corporate-task-index">{String(index + 1).padStart(2, "0")}</span>
                      <span className="corporate-task-copy"><b>{item.title}</b><small>{titleCase(item.category)} · {titleCase(item.owner_role)}{item.due_at ? ` · ${new Date(item.due_at).toLocaleDateString()}` : ""}</small></span>
                      {item.depends_on_task_id ? <span className="corporate-task-dependency">After {tasks.find((row) => row.id === item.depends_on_task_id)?.title || "dependency"}</span> : null}
                      <StatusBadge value={item.status} />
                      <div className="corporate-task-actions">
                        {item.status === "planned" ? <button className="button secondary" disabled={working === item.id} onClick={() => void moveTask(item, "ready")}>Ready</button> : null}
                        {item.status === "ready" ? <button className="button secondary" disabled={working === item.id} onClick={() => void moveTask(item, "in_progress")}>Start</button> : null}
                        {item.status === "in_progress" ? <button className="button secondary" disabled={working === item.id} onClick={() => void moveTask(item, "completed")}>{item.requires_human_approval ? "Submit" : "Complete"}</button> : null}
                      </div>
                    </div>
                  ))}
                  {!tasks.length ? <EmptyState title="No relocation tasks" detail="Build the controlled sequence for this case." /> : null}
                </div>
                <details className="corporate-task-create"><summary>Add relocation task</summary><form onSubmit={submitTask} className="corporate-mini-form"><div><input required placeholder="Task title" value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} /><select value={taskForm.category} onChange={(event) => setTaskForm({ ...taskForm, category: event.target.value as typeof taskForm.category })}><option value="immigration">Immigration</option><option value="relocation">Relocation</option><option value="payroll">Payroll</option><option value="tax">Tax</option><option value="housing">Housing</option><option value="travel">Travel</option><option value="onboarding">Onboarding</option><option value="custom">Custom</option></select></div><div><input required placeholder="Owner role" value={taskForm.owner_role} onChange={(event) => setTaskForm({ ...taskForm, owner_role: event.target.value })} /><input type="datetime-local" value={taskForm.due_at} onChange={(event) => setTaskForm({ ...taskForm, due_at: event.target.value })} /></div><div><select value={taskForm.depends_on_task_id} onChange={(event) => setTaskForm({ ...taskForm, depends_on_task_id: event.target.value })}><option value="">No dependency</option>{tasks.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select><label className="corporate-check"><input type="checkbox" checked={taskForm.requires_human_approval} onChange={(event) => setTaskForm({ ...taskForm, requires_human_approval: event.target.checked })} />Independent completion review</label></div><button className="button primary" disabled={working === "task" || selectedCase.status === "closed"}>Add task</button></form></details>
              </article>

              {selectedCase.case_type === "entrepreneur_startup" ? (
                <article className="venture-dossier">
                  <div className="corporate-task-header">
                    <div><span>Founder dossier</span><h3>{venture?.venture_name || "Entrepreneur venture profile"}</h3><p>Dossier review confirms completeness only. It does not determine visa eligibility or investment qualification.</p></div>
                    {venture ? <StatusBadge value={venture.status} /> : null}
                  </div>
                  {!venture ? (
                    <form className="venture-form" onSubmit={submitVenture}>
                      <div><select required value={ventureForm.founder_lead_id} onChange={(event) => setVentureForm({ ...ventureForm, founder_lead_id: event.target.value })}><option value="">Founder lead</option>{leads.map((lead) => <option value={lead.id} key={lead.id}>{lead.full_name}</option>)}</select><input required placeholder="Venture name" value={ventureForm.venture_name} onChange={(event) => setVentureForm({ ...ventureForm, venture_name: event.target.value })} /></div>
                      <div><select value={ventureForm.venture_stage} onChange={(event) => setVentureForm({ ...ventureForm, venture_stage: event.target.value as typeof ventureForm.venture_stage })}><option value="idea">Idea</option><option value="pre_seed">Pre-seed</option><option value="seed">Seed</option><option value="growth">Growth</option><option value="established">Established</option></select><input required placeholder="Sector" value={ventureForm.sector} onChange={(event) => setVentureForm({ ...ventureForm, sector: event.target.value })} /></div>
                      <div><input required placeholder="Founder role" value={ventureForm.founder_role} onChange={(event) => setVentureForm({ ...ventureForm, founder_role: event.target.value })} /><input placeholder="Incorporation country" value={ventureForm.incorporation_country} onChange={(event) => setVentureForm({ ...ventureForm, incorporation_country: event.target.value })} /></div>
                      <textarea required minLength={20} placeholder="Business model summary" value={ventureForm.business_model_summary} onChange={(event) => setVentureForm({ ...ventureForm, business_model_summary: event.target.value })} />
                      <button className="button primary" disabled={working === "venture" || selectedCase.status === "closed"}>Create review-gated dossier</button>
                    </form>
                  ) : (
                    <>
                      <div className="venture-summary"><div><span>Founder</span><strong>{leadNames.get(venture.founder_lead_id) || "Linked founder"}</strong></div><div><span>Stage</span><strong>{titleCase(venture.venture_stage)}</strong></div><div><span>Sector</span><strong>{venture.sector}</strong></div><div><span>Target</span><strong>{venture.target_country}</strong></div></div>
                      <div className="venture-evidence-list">{ventureEvidence.map((item) => <div key={item.id}><span><b>{item.title}</b><small>{titleCase(item.evidence_type)}{item.document_record_id ? " · Controlled document linked" : " · Declaration only"}</small></span>{item.declared_amount_minor !== null ? <strong>{item.currency} {item.declared_amount_minor.toLocaleString()} minor units</strong> : null}</div>)}</div>
                      {venture.status !== "review_ready" && venture.status !== "reviewed" ? <details className="corporate-task-create"><summary>Add dossier evidence</summary><form className="venture-form" onSubmit={submitVentureEvidenceItem}><div><select value={evidenceForm.evidence_type} onChange={(event) => setEvidenceForm({ ...evidenceForm, evidence_type: event.target.value as typeof evidenceForm.evidence_type })}><option value="business_plan">Business plan</option><option value="incorporation">Incorporation</option><option value="bank_statement">Bank statement</option><option value="investment_commitment">Investment commitment</option><option value="grant">Grant</option><option value="revenue">Revenue</option><option value="capitalization">Capitalization</option><option value="intellectual_property">Intellectual property</option><option value="other">Other</option></select><input required placeholder="Evidence title" value={evidenceForm.title} onChange={(event) => setEvidenceForm({ ...evidenceForm, title: event.target.value })} /></div><div><input type="number" min="0" placeholder="Amount in minor units" value={evidenceForm.declared_amount_minor} onChange={(event) => setEvidenceForm({ ...evidenceForm, declared_amount_minor: event.target.value })} /><input minLength={3} maxLength={3} placeholder="Currency" value={evidenceForm.currency} onChange={(event) => setEvidenceForm({ ...evidenceForm, currency: event.target.value })} /></div><input placeholder="Controlled document UUID" value={evidenceForm.document_record_id} onChange={(event) => setEvidenceForm({ ...evidenceForm, document_record_id: event.target.value })} /><button className="button secondary" disabled={working === "venture-evidence"}>Add evidence</button></form></details> : null}
                      {venture.status === "evidence_pending" ? <button className="button primary venture-submit" disabled={working === "venture-submit" || !ventureEvidence.some((item) => item.document_record_id)} onClick={() => void sendVentureForReview()}>Submit completeness review</button> : null}
                    </>
                  )}
                </article>
              ) : null}
            </section>
          ) : null}
        </main>
      </section>
    </WorkspaceShell>
  );
}
