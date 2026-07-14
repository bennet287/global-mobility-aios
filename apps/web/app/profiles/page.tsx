"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  DocumentRecord,
  getCurrentMobilityProfile,
  getHealthStatus,
  getLeadDetail,
  getLeads,
  getMobilityProfileHistory,
  HealthStatus,
  Lead,
  replaceCurrentMobilityProfile,
  UniversalMobilityProfile,
  UniversalMobilityProfileInput,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

type FormState = {
  currentCountry: string;
  qualification: string;
  fieldOfStudy: string;
  institution: string;
  educationCountry: string;
  completionYear: string;
  role: string;
  employer: string;
  employmentCountry: string;
  yearsExperience: string;
  skills: string;
  language: string;
  languageLevel: string;
  testName: string;
  testScore: string;
  familyStatus: "unknown" | "single" | "partnered" | "dependants";
  familyMembers: string;
  familyConfirmed: boolean;
  budgetEur: string;
  fundingSource: string;
  goalDomain: "study" | "work" | "visa" | "settlement" | "family" | "business";
  targetCountry: string;
  desiredRoleOrProgram: string;
  targetDate: string;
  priority: "low" | "medium" | "high";
  constraints: string;
  constraintsConfirmed: boolean;
  consentStatus: "not_recorded" | "granted" | "withdrawn";
  consentPurposes: string[];
  consentExpiresAt: string;
  evidenceIds: string[];
};

const EMPTY_FORM: FormState = {
  currentCountry: "",
  qualification: "",
  fieldOfStudy: "",
  institution: "",
  educationCountry: "",
  completionYear: "",
  role: "",
  employer: "",
  employmentCountry: "",
  yearsExperience: "",
  skills: "",
  language: "",
  languageLevel: "",
  testName: "",
  testScore: "",
  familyStatus: "unknown",
  familyMembers: "",
  familyConfirmed: false,
  budgetEur: "",
  fundingSource: "",
  goalDomain: "work",
  targetCountry: "",
  desiredRoleOrProgram: "",
  targetDate: "",
  priority: "medium",
  constraints: "",
  constraintsConfirmed: false,
  consentStatus: "not_recorded",
  consentPurposes: [],
  consentExpiresAt: "",
  evidenceIds: [],
};

function formFromProfile(profile: UniversalMobilityProfile): FormState {
  const education = profile.education[0];
  const employment = profile.employment.find((item) => item.current) || profile.employment[0];
  const language = profile.languages[0];
  const goal = profile.goals[0];
  return {
    ...EMPTY_FORM,
    currentCountry: profile.current_country || "",
    qualification: education?.qualification || "",
    fieldOfStudy: education?.field_of_study || "",
    institution: education?.institution || "",
    educationCountry: education?.country || "",
    completionYear: education?.completion_year ? String(education.completion_year) : "",
    role: employment?.role || "",
    employer: employment?.employer || "",
    employmentCountry: employment?.country || "",
    yearsExperience: profile.years_experience == null ? "" : String(profile.years_experience),
    skills: profile.skills.join(", "),
    language: language?.language || "",
    languageLevel: language?.level || "",
    testName: language?.test_name || "",
    testScore: language?.test_score || "",
    familyStatus: (profile.family.status as FormState["familyStatus"]) || "unknown",
    familyMembers: (profile.family.members || []).map((item) => String(item.name || item.relationship || "")).filter(Boolean).join(", "),
    familyConfirmed: Boolean(profile.family.details_confirmed),
    budgetEur: profile.finances.budget_eur == null ? "" : String(profile.finances.budget_eur),
    fundingSource: String(profile.finances.funding_source || ""),
    goalDomain: goal?.domain || "work",
    targetCountry: goal?.target_country || "",
    desiredRoleOrProgram: goal?.desired_role_or_program || "",
    targetDate: goal?.target_date ? goal.target_date.slice(0, 10) : "",
    priority: goal?.priority || "medium",
    constraints: (profile.constraints.items || []).map((item) => String(item.value || item.type || "")).filter(Boolean).join("\n"),
    constraintsConfirmed: Boolean(profile.constraints.confirmed),
    consentStatus: (profile.consent_status as FormState["consentStatus"]) || "not_recorded",
    consentPurposes: profile.consent.purposes || [],
    consentExpiresAt: profile.consent.expires_at ? profile.consent.expires_at.slice(0, 10) : "",
    evidenceIds: profile.evidence_document_ids,
  };
}

function SectionMarker({ number, title, detail }: { number: string; title: string; detail: string }) {
  return (
    <div className="form-section-title">
      <span>{number}</span>
      <div><strong>{title}</strong><small>{detail}</small></div>
    </div>
  );
}

export default function ProfilesPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [profile, setProfile] = useState<UniversalMobilityProfile | null>(null);
  const [history, setHistory] = useState<UniversalMobilityProfile[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const loadLead = useCallback(async (selectedLeadId: string) => {
    if (!selectedLeadId) {
      setProfile(null);
      setHistory([]);
      setDocuments([]);
      setForm(EMPTY_FORM);
      return;
    }
    setLoading(true);
    setError(null);
    const [currentResult, historyResult, detailResult] = await Promise.allSettled([
      getCurrentMobilityProfile(selectedLeadId),
      getMobilityProfileHistory(selectedLeadId),
      getLeadDetail(selectedLeadId),
    ]);
    if (currentResult.status === "fulfilled") {
      setProfile(currentResult.value);
      setForm(formFromProfile(currentResult.value));
    } else {
      setProfile(null);
      const lead = leads.find((item) => item.id === selectedLeadId);
      setForm({ ...EMPTY_FORM, targetCountry: lead?.target_country || "" });
    }
    setHistory(historyResult.status === "fulfilled" ? historyResult.value : []);
    setDocuments(detailResult.status === "fulfilled" ? detailResult.value.documents : []);
    if (historyResult.status === "rejected" || detailResult.status === "rejected") {
      setError("Some lead context could not be loaded. You can still edit the profile.");
    }
    setLoading(false);
  }, [leads]);

  const loadWorkspace = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthResult, leadRows] = await Promise.all([getHealthStatus(), getLeads()]);
      setHealth(healthResult.data);
      setLeads(leadRows);
      if (leadId) await loadLead(leadId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load profiles workspace");
    } finally {
      setLoading(false);
    }
  }, [leadId, loadLead]);

  useEffect(() => {
    void loadWorkspace();
    // Initial workspace load only; lead changes are handled by the selector.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!leadId) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    const education = form.qualification ? [{
      qualification: form.qualification,
      field_of_study: form.fieldOfStudy || null,
      institution: form.institution || null,
      country: form.educationCountry || null,
      completion_year: form.completionYear ? Number(form.completionYear) : null,
    }] : [];
    const employment = form.role ? [{
      role: form.role,
      employer: form.employer || null,
      country: form.employmentCountry || null,
      years: form.yearsExperience ? Number(form.yearsExperience) : 0,
      current: true,
    }] : [];
    const payload: UniversalMobilityProfileInput = {
      current_country: form.currentCountry || null,
      education,
      employment,
      years_experience: form.yearsExperience ? Number(form.yearsExperience) : null,
      skills: form.skills.split(",").map((item) => item.trim()).filter(Boolean),
      languages: form.language ? [{ language: form.language, level: form.languageLevel || null, test_name: form.testName || null, test_score: form.testScore || null }] : [],
      family_status: form.familyStatus,
      family: form.familyMembers.split(",").map((item) => item.trim()).filter(Boolean).map((name) => ({ name })),
      family_details_confirmed: form.familyConfirmed,
      finances: {
        ...(form.budgetEur ? { budget_eur: Number(form.budgetEur) } : {}),
        ...(form.fundingSource ? { funding_source: form.fundingSource } : {}),
      },
      goals: form.targetCountry ? [{ domain: form.goalDomain, target_country: form.targetCountry, desired_role_or_program: form.desiredRoleOrProgram || null, target_date: form.targetDate ? new Date(`${form.targetDate}T00:00:00Z`).toISOString() : null, priority: form.priority }] : [],
      constraints: form.constraints.split("\n").map((item) => item.trim()).filter(Boolean).map((value) => ({ type: "operator_note", value })),
      constraints_confirmed: form.constraintsConfirmed,
      consent_status: form.consentStatus,
      consent_purposes: form.consentPurposes,
      consent_expires_at: form.consentExpiresAt ? new Date(`${form.consentExpiresAt}T00:00:00Z`).toISOString() : null,
      evidence_document_ids: form.evidenceIds,
    };
    try {
      const saved = await replaceCurrentMobilityProfile(leadId, payload);
      setProfile(saved);
      setForm(formFromProfile(saved));
      setMessage(`Version ${saved.profile_version} saved with ${saved.completeness_score}% completeness.`);
      setHistory(await getMobilityProfileHistory(leadId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile version");
    } finally {
      setSaving(false);
    }
  }

  const selectedLead = leads.find((lead) => lead.id === leadId);
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  const purposeOptions = ["eligibility", "opportunity_matching", "document_processing", "communications"];

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Mobility Profiles" kicker="Universal client facts" loadStatus={loadStatus} onRefresh={loadWorkspace} />
      <div className="page-pad profiles-page">
        {error && <InlineNotice label="Profile workspace error" detail={error} tone="bad" />}
        {message && <InlineNotice label="Profile version created" detail={message} tone="good" />}

        <section className="panel profile-selector-panel">
          <div>
            <span className="page-kicker">Client context</span>
            <strong>Select a lead to create or update an immutable mobility profile.</strong>
          </div>
          <label>
            Lead
            <select value={leadId} onChange={(event) => { setLeadId(event.target.value); void loadLead(event.target.value); }}>
              <option value="">Choose a lead</option>
              {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name} · {lead.target_country || "No target country"}</option>)}
            </select>
          </label>
        </section>

        {!leadId ? <EmptyState title="No lead selected" detail="Choose a lead to view profile readiness, evidence, consent, and version history." /> : (
          <>
            <div className="metric-row profile-metrics">
              <MetricPill label="Completeness" value={`${profile?.completeness_score || 0}%`} tone={(profile?.completeness_score || 0) >= 70 ? "good" : "warn"} />
              <MetricPill label="Version" value={profile?.profile_version || "New"} />
              <MetricPill label="Missing sections" value={profile?.missing_sections.length ?? 11} tone={profile?.missing_sections.length ? "warn" : "good"} />
              <div className="metric-pill"><span>Readiness</span><strong className="profile-status-value">{titleCase(profile?.readiness_stage || "foundation")}</strong></div>
              <div className="metric-pill"><span>Consent</span><strong className="profile-status-value">{titleCase(profile?.consent_status || "not recorded")}</strong></div>
              <MetricPill label="Evidence" value={form.evidenceIds.length} tone={form.evidenceIds.length ? "good" : "warn"} />
            </div>

            <div className="profiles-grid">
              <form className="panel mobility-profile-form intelligence-form" onSubmit={save}>
                <SectionTitle label="Profile" title={selectedLead?.full_name || "Mobility profile"} detail="Saving creates a new immutable version; prior versions remain auditable." />

                <SectionMarker number="01" title="Identity and education" detail="Residence, qualification, institution, and field" />
                <div className="profile-field-grid three">
                  <label>Current country<input value={form.currentCountry} onChange={(e) => update("currentCountry", e.target.value)} /></label>
                  <label>Qualification<input value={form.qualification} onChange={(e) => update("qualification", e.target.value)} /></label>
                  <label>Field of study<input value={form.fieldOfStudy} onChange={(e) => update("fieldOfStudy", e.target.value)} /></label>
                  <label>Institution<input value={form.institution} onChange={(e) => update("institution", e.target.value)} /></label>
                  <label>Education country<input value={form.educationCountry} onChange={(e) => update("educationCountry", e.target.value)} /></label>
                  <label>Completion year<input type="number" min="1900" max="2200" value={form.completionYear} onChange={(e) => update("completionYear", e.target.value)} /></label>
                </div>

                <SectionMarker number="02" title="Work and skills" detail="Current employment, total experience, and capabilities" />
                <div className="profile-field-grid three">
                  <label>Current role<input value={form.role} onChange={(e) => update("role", e.target.value)} /></label>
                  <label>Employer<input value={form.employer} onChange={(e) => update("employer", e.target.value)} /></label>
                  <label>Employment country<input value={form.employmentCountry} onChange={(e) => update("employmentCountry", e.target.value)} /></label>
                  <label>Years experience<input type="number" min="0" max="80" step="0.5" value={form.yearsExperience} onChange={(e) => update("yearsExperience", e.target.value)} /></label>
                  <label className="profile-wide">Skills, comma separated<input value={form.skills} onChange={(e) => update("skills", e.target.value)} /></label>
                </div>

                <SectionMarker number="03" title="Languages" detail="Ability level and recognized test evidence" />
                <div className="profile-field-grid four">
                  <label>Language<input value={form.language} onChange={(e) => update("language", e.target.value)} /></label>
                  <label>Level<input value={form.languageLevel} onChange={(e) => update("languageLevel", e.target.value)} placeholder="B2, C1, native" /></label>
                  <label>Test<input value={form.testName} onChange={(e) => update("testName", e.target.value)} placeholder="IELTS" /></label>
                  <label>Score<input value={form.testScore} onChange={(e) => update("testScore", e.target.value)} /></label>
                </div>

                <SectionMarker number="04" title="Family and finances" detail="Relocation context, dependants, and available funds" />
                <div className="profile-field-grid three">
                  <label>Family status<select value={form.familyStatus} onChange={(e) => update("familyStatus", e.target.value as FormState["familyStatus"])}><option value="unknown">Unknown</option><option value="single">Single</option><option value="partnered">Partnered</option><option value="dependants">Dependants</option></select></label>
                  <label>Family members<input value={form.familyMembers} onChange={(e) => update("familyMembers", e.target.value)} placeholder="Names, comma separated" /></label>
                  <label>Budget (EUR)<input type="number" min="0" value={form.budgetEur} onChange={(e) => update("budgetEur", e.target.value)} /></label>
                  <label>Funding source<input value={form.fundingSource} onChange={(e) => update("fundingSource", e.target.value)} /></label>
                  <label className="profile-check"><input type="checkbox" checked={form.familyConfirmed} onChange={(e) => update("familyConfirmed", e.target.checked)} /> Family details confirmed</label>
                </div>

                <SectionMarker number="05" title="Goals and constraints" detail="Desired pathway, destination, timing, and limitations" />
                <div className="profile-field-grid three">
                  <label>Goal domain<select value={form.goalDomain} onChange={(e) => update("goalDomain", e.target.value as FormState["goalDomain"])}>{["work", "study", "visa", "settlement", "family", "business"].map((value) => <option value={value} key={value}>{titleCase(value)}</option>)}</select></label>
                  <label>Target country<input value={form.targetCountry} onChange={(e) => update("targetCountry", e.target.value)} /></label>
                  <label>Role or program<input value={form.desiredRoleOrProgram} onChange={(e) => update("desiredRoleOrProgram", e.target.value)} /></label>
                  <label>Target date<input type="date" value={form.targetDate} onChange={(e) => update("targetDate", e.target.value)} /></label>
                  <label>Priority<select value={form.priority} onChange={(e) => update("priority", e.target.value as FormState["priority"])}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
                  <label className="profile-wide">Constraints, one per line<textarea rows={3} value={form.constraints} onChange={(e) => update("constraints", e.target.value)} /></label>
                  <label className="profile-check"><input type="checkbox" checked={form.constraintsConfirmed} onChange={(e) => update("constraintsConfirmed", e.target.checked)} /> Constraints reviewed and confirmed</label>
                </div>

                <SectionMarker number="06" title="Consent and evidence" detail="Purpose-limited processing and lead-owned documents" />
                <div className="profile-field-grid three">
                  <label>Consent status<select value={form.consentStatus} onChange={(e) => update("consentStatus", e.target.value as FormState["consentStatus"])}><option value="not_recorded">Not recorded</option><option value="granted">Granted</option><option value="withdrawn">Withdrawn</option></select></label>
                  <label>Consent expiry<input type="date" value={form.consentExpiresAt} onChange={(e) => update("consentExpiresAt", e.target.value)} /></label>
                  <div className="profile-purpose-list"><span>Processing purposes</span>{purposeOptions.map((purpose) => <label className="profile-check" key={purpose}><input type="checkbox" checked={form.consentPurposes.includes(purpose)} onChange={(e) => update("consentPurposes", e.target.checked ? [...form.consentPurposes, purpose] : form.consentPurposes.filter((item) => item !== purpose))} /> {titleCase(purpose)}</label>)}</div>
                  <div className="profile-evidence-list profile-wide"><span>Evidence documents</span>{documents.length ? documents.map((document) => <label className="profile-check" key={document.id}><input type="checkbox" checked={form.evidenceIds.includes(document.id)} onChange={(e) => update("evidenceIds", e.target.checked ? [...form.evidenceIds, document.id] : form.evidenceIds.filter((id) => id !== document.id))} /><strong>{document.filename}</strong><small>{titleCase(document.document_type)} · {titleCase(document.status)}</small></label>) : <small>No documents uploaded for this lead.</small>}</div>
                </div>

                {form.consentStatus === "withdrawn" && <InlineNotice label="Processing will be restricted" detail="Eligibility and opportunity matching will stop when this version becomes current." tone="warn" />}
                <button className="button primary profile-save" type="submit" disabled={saving}>{saving ? "Creating version…" : `Create ${profile ? `version ${profile.profile_version + 1}` : "first version"}`}</button>
              </form>

              <aside className="profile-side-stack">
                <section className="panel">
                  <SectionTitle label="Readiness" title="Coverage ledger" detail="Every missing section lowers decision readiness." />
                  <div className="profile-completeness"><span style={{ width: `${profile?.completeness_score || 0}%` }} /></div>
                  <div className="profile-status-row"><StatusBadge value={profile?.readiness_stage || "foundation"} /><StatusBadge value={profile?.lifecycle_status || "draft"} /></div>
                  <div className="profile-missing-list">{profile?.missing_sections.length ? profile.missing_sections.map((section) => <span key={section}>{titleCase(section)}</span>) : <p>{profile ? "All completeness sections are covered." : "Save the first version to calculate coverage."}</p>}</div>
                </section>
                <section className="panel profile-history-panel">
                  <SectionTitle label="Audit" title="Version history" detail={`${history.length} immutable version${history.length === 1 ? "" : "s"}`} />
                  <div className="profile-history-list">{history.length ? history.map((item) => <article key={item.id}><div><strong>Version {item.profile_version}</strong><StatusBadge value={item.lifecycle_status} /></div><p>{item.completeness_score}% complete · {titleCase(item.readiness_stage)}</p><small>{new Date(item.created_at).toLocaleString()} · {item.updated_by || "system"}</small></article>) : <EmptyState title="No history yet" detail="The first saved profile will begin the immutable history." />}</div>
                </section>
              </aside>
            </div>
          </>
        )}
      </div>
    </WorkspaceShell>
  );
}
