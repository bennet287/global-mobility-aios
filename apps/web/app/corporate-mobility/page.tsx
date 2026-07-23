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
  CorporateMobilityCase,
  Lead,
  createCorporateAccount,
  createCorporateMobilityCase,
  getLeads,
  listCorporateAccounts,
  listCorporateMobilityCases,
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
  case_type: "employee_relocation" as "employee_relocation" | "dependant" | "sponsor_compliance",
  origin_country: "",
  destination_country: "",
  sponsor_name: "",
  compliance_due_date: "",
  target_start_date: "",
};


export default function CorporateMobilityPage() {
  const { health } = useBackendStatus();
  const [accounts, setAccounts] = useState<CorporateAccount[]>([]);
  const [cases, setCases] = useState<CorporateMobilityCase[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [accountForm, setAccountForm] = useState(emptyAccountForm);
  const [caseForm, setCaseForm] = useState(emptyCaseForm);
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
  const leadNames = useMemo(() => new Map(leads.map((lead) => [lead.id, lead.full_name])), [leads]);
  const activeCases = cases.filter((item) => item.status === "active").length;
  const complianceDue = cases.filter((item) => item.compliance_due_date && !["completed", "closed"].includes(item.status)).length;

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
              <article key={item.id}>
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
                <label>Case type<select value={caseForm.case_type} onChange={(event) => setCaseForm({ ...caseForm, case_type: event.target.value as typeof caseForm.case_type })}><option value="employee_relocation">Employee relocation</option><option value="dependant">Dependant</option><option value="sponsor_compliance">Sponsor compliance</option></select></label>
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
        </main>
      </section>
    </WorkspaceShell>
  );
}

