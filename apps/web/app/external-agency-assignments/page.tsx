"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  ApplicationRecord,
  ExternalAgency,
  ExternalAgencyAssignment,
  createExternalAgency,
  createExternalAgencyAssignment,
  listApplications,
  listExternalAgencies,
  listExternalAgencyAssignments,
  updateExternalAgencyAssignmentStatus,
  updateExternalAgencyStatus,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const agencyStatuses: ExternalAgency["status"][] = ["active", "suspended", "retired"];

const assignmentStatusWorkflow: ExternalAgencyAssignment["status"][] = [
  "assigned",
  "in_progress",
  "handed_off",
  "completed",
  "cancelled",
];

const terminalAssignmentStatuses: ExternalAgencyAssignment["status"][] = ["completed", "cancelled"];

const allowedAssignmentTransitions: Record<string, ExternalAgencyAssignment["status"][] | undefined> = {
  assigned: ["in_progress", "cancelled"],
  in_progress: ["handed_off", "cancelled"],
  handed_off: ["completed", "cancelled"],
};

const emptyAgencyForm = {
  name: "",
  country: "",
  city: "",
  contact_email: "",
  contact_phone: "",
  website: "",
  sla_due_hours: "72",
  notes: "",
};

const emptyAssignmentForm = {
  application_id: "",
  external_agency_id: "",
  agency_reference_number: "",
  notes: "",
};

export default function ExternalAgencyAssignmentsPage() {
  const { health } = useBackendStatus();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [agencies, setAgencies] = useState<ExternalAgency[]>([]);
  const [assignments, setAssignments] = useState<ExternalAgencyAssignment[]>([]);
  const [agencyForm, setAgencyForm] = useState(emptyAgencyForm);
  const [assignmentForm, setAssignmentForm] = useState(emptyAssignmentForm);
  const [agencyStatusReasons, setAgencyStatusReasons] = useState<Record<string, string>>({});
  const [assignmentStatusReasons, setAssignmentStatusReasons] = useState<Record<string, string>>({});
  const [assignmentRefInputs, setAssignmentRefInputs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [applicationRows, agencyRows, assignmentRows] = await Promise.all([
        listApplications({ limit: 250 }),
        listExternalAgencies(),
        listExternalAgencyAssignments(),
      ]);
      setApplications(applicationRows);
      setAgencies(agencyRows);
      setAssignments(assignmentRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "External agency workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const applicationNames = useMemo(
    () =>
      new Map(
        applications.map((app) => [
          app.id,
          `${app.domain.toUpperCase()} — ${app.target_country || "Unknown"} (${app.id.slice(0, 8)})`,
        ])
      ),
    [applications]
  );

  const agencyNames = useMemo(() => new Map(agencies.map((agency) => [agency.id, agency.name])), [agencies]);

  const activeAgencies = useMemo(() => agencies.filter((a) => a.status === "active"), [agencies]);

  async function submitAgency(event: FormEvent) {
    event.preventDefault();
    if (!agencyForm.name) return;
    setWorking("agency");
    setError(null);
    setMessage(null);
    try {
      const created = await createExternalAgency({
        name: agencyForm.name,
        ...(agencyForm.country ? { country: agencyForm.country } : {}),
        ...(agencyForm.city ? { city: agencyForm.city } : {}),
        ...(agencyForm.contact_email ? { contact_email: agencyForm.contact_email } : {}),
        ...(agencyForm.contact_phone ? { contact_phone: agencyForm.contact_phone } : {}),
        ...(agencyForm.website ? { website: agencyForm.website } : {}),
        sla_due_hours: Number(agencyForm.sla_due_hours) || 72,
        ...(agencyForm.notes ? { notes: agencyForm.notes } : {}),
      });
      setAgencyForm(emptyAgencyForm);
      await load();
      setMessage(`${created.name} added to the external agency registry.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "External agency could not be created");
    } finally {
      setWorking(null);
    }
  }

  async function changeAgencyStatus(agency: ExternalAgency, status: ExternalAgency["status"]) {
    const reason = agencyStatusReasons[agency.id]?.trim();
    if (!reason) {
      setError("A reason is required to change agency status.");
      return;
    }
    setWorking(agency.id);
    setError(null);
    setMessage(null);
    try {
      await updateExternalAgencyStatus(agency.id, status, reason);
      setAgencyStatusReasons((prev) => ({ ...prev, [agency.id]: "" }));
      await load();
      setMessage(`${agency.name} is now ${titleCase(status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agency status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  async function submitAssignment(event: FormEvent) {
    event.preventDefault();
    if (!assignmentForm.application_id || !assignmentForm.external_agency_id) return;
    setWorking("assignment");
    setError(null);
    setMessage(null);
    try {
      const created = await createExternalAgencyAssignment({
        application_id: assignmentForm.application_id,
        external_agency_id: assignmentForm.external_agency_id,
        ...(assignmentForm.agency_reference_number
          ? { agency_reference_number: assignmentForm.agency_reference_number }
          : {}),
        ...(assignmentForm.notes ? { notes: assignmentForm.notes } : {}),
      });
      setAssignmentForm(emptyAssignmentForm);
      await load();
      const agency = agencyNames.get(created.external_agency_id) || created.external_agency_id;
      setMessage(`Application assigned to ${agency}. SLA status: ${titleCase(created.sla_status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assignment could not be created");
    } finally {
      setWorking(null);
    }
  }

  async function changeAssignmentStatus(assignment: ExternalAgencyAssignment, status: ExternalAgencyAssignment["status"]) {
    const reason = assignmentStatusReasons[assignment.id]?.trim();
    if (!reason) {
      setError("A reason is required to update assignment status.");
      return;
    }
    setWorking(assignment.id);
    setError(null);
    setMessage(null);
    try {
      await updateExternalAgencyAssignmentStatus(
        assignment.id,
        status,
        reason,
        assignmentRefInputs[assignment.id]?.trim() || undefined
      );
      setAssignmentStatusReasons((prev) => ({ ...prev, [assignment.id]: "" }));
      setAssignmentRefInputs((prev) => ({ ...prev, [assignment.id]: "" }));
      await load();
      setMessage(`Assignment moved to ${titleCase(status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assignment status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  const loadStatus = health?.status === "ok" ? (loading ? "loading" : "ready") : "offline";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="External Agency Assignments"
        kicker="Agency registry and handoff tracking"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <div className="workspace-body">
        <div className="workspace-grid two-col">
          <section className="panel">
            <SectionTitle
              label="Registry"
              title="External agencies"
              detail="Maintain the directory of visa facilitators, relocation providers, and mobility agencies. Only active agencies can receive assignments."
            />
            <form onSubmit={submitAgency} className="form-card">
              <label className="field">
                <span className="field-label">Agency name</span>
                <input
                  className="input"
                  type="text"
                  required
                  placeholder="Mumbai Visa Services Pvt Ltd"
                  value={agencyForm.name}
                  onChange={(e) => setAgencyForm((f) => ({ ...f, name: e.target.value }))}
                />
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Country</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="India"
                    value={agencyForm.country}
                    onChange={(e) => setAgencyForm((f) => ({ ...f, country: e.target.value }))}
                  />
                </label>

                <label className="field">
                  <span className="field-label">City</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="Mumbai"
                    value={agencyForm.city}
                    onChange={(e) => setAgencyForm((f) => ({ ...f, city: e.target.value }))}
                  />
                </label>
              </div>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Email</span>
                  <input
                    className="input"
                    type="email"
                    placeholder="ops@example.com"
                    value={agencyForm.contact_email}
                    onChange={(e) => setAgencyForm((f) => ({ ...f, contact_email: e.target.value }))}
                  />
                </label>

                <label className="field">
                  <span className="field-label">Phone</span>
                  <input
                    className="input"
                    type="tel"
                    placeholder="+91-22-1234-5678"
                    value={agencyForm.contact_phone}
                    onChange={(e) => setAgencyForm((f) => ({ ...f, contact_phone: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Website</span>
                <input
                  className="input"
                  type="url"
                  placeholder="https://..."
                  value={agencyForm.website}
                  onChange={(e) => setAgencyForm((f) => ({ ...f, website: e.target.value }))}
                />
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">SLA due hours</span>
                  <input
                    className="input"
                    type="number"
                    min={1}
                    max={8760}
                    required
                    value={agencyForm.sla_due_hours}
                    onChange={(e) => setAgencyForm((f) => ({ ...f, sla_due_hours: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Notes</span>
                <textarea
                  className="input"
                  rows={2}
                  placeholder="Contract terms, coverage, or special instructions."
                  value={agencyForm.notes}
                  onChange={(e) => setAgencyForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </label>

              <div className="form-actions">
                <button className="button primary" type="submit" disabled={working === "agency"}>
                  {working === "agency" ? <span className="button-spinner" aria-hidden="true" /> : "Add agency"}
                </button>
              </div>
            </form>

            <div className="panel-section">
              <h3>Agency directory</h3>
              {agencies.length === 0 ? (
                <EmptyState title="No agencies" detail="Add the first external agency using the form above." />
              ) : (
                <ul className="data-list compact">
                  {agencies.map((agency) => (
                    <li key={agency.id} className="data-list-item">
                      <div className="data-list-row">
                        <div>
                          <strong className="data-list-title">{agency.name}</strong>
                          <span className="data-list-meta">
                            {[agency.city, agency.country].filter(Boolean).join(", ")}
                            {agency.sla_due_hours ? ` · SLA ${agency.sla_due_hours}h` : null}
                          </span>
                        </div>
                        <StatusBadge value={agency.status} />
                      </div>
                      <div className="data-list-actions">
                        <label className="field slim">
                          <span className="field-label">Status reason</span>
                          <input
                            className="input"
                            type="text"
                            placeholder="Why is the status changing?"
                            value={agencyStatusReasons[agency.id] || ""}
                            onChange={(e) =>
                              setAgencyStatusReasons((prev) => ({ ...prev, [agency.id]: e.target.value }))
                            }
                          />
                        </label>
                        <div className="button-group">
                          {agencyStatuses.map((status) => (
                            <button
                              key={status}
                              className={`button small ${agency.status === status ? "secondary" : "ghost"}`}
                              type="button"
                              disabled={working === agency.id}
                              onClick={() => void changeAgencyStatus(agency, status)}
                            >
                              {titleCase(status)}
                            </button>
                          ))}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="panel">
            <SectionTitle
              label="Handoffs"
              title="Assign applications to agencies"
              detail="Hand off applications to external agencies and track the forward-only lifecycle. SLA status is computed from the agency's due-hours setting."
            />
            <form onSubmit={submitAssignment} className="form-card">
              <label className="field">
                <span className="field-label">Application</span>
                <select
                  className="input"
                  required
                  value={assignmentForm.application_id}
                  onChange={(e) => setAssignmentForm((f) => ({ ...f, application_id: e.target.value }))}
                >
                  <option value="">Select an application…</option>
                  {applications.map((app) => (
                    <option key={app.id} value={app.id}>
                      {applicationNames.get(app.id)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span className="field-label">Active agency</span>
                <select
                  className="input"
                  required
                  value={assignmentForm.external_agency_id}
                  onChange={(e) => setAssignmentForm((f) => ({ ...f, external_agency_id: e.target.value }))}
                >
                  <option value="">Select an agency…</option>
                  {activeAgencies.map((agency) => (
                    <option key={agency.id} value={agency.id}>
                      {agency.name} ({agency.sla_due_hours}h SLA)
                    </option>
                  ))}
                </select>
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Agency reference number</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="MVS-REF-001"
                    value={assignmentForm.agency_reference_number}
                    onChange={(e) => setAssignmentForm((f) => ({ ...f, agency_reference_number: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Notes</span>
                <textarea
                  className="input"
                  rows={2}
                  placeholder="Scope of work, special instructions, or handoff notes."
                  value={assignmentForm.notes}
                  onChange={(e) => setAssignmentForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </label>

              <div className="form-actions">
                <button className="button primary" type="submit" disabled={working === "assignment"}>
                  {working === "assignment" ? <span className="button-spinner" aria-hidden="true" /> : "Create assignment"}
                </button>
              </div>
            </form>

            <div className="panel-section">
              <h3>Assignments</h3>
              {assignments.length === 0 ? (
                <EmptyState title="No assignments" detail="Create the first handoff once an agency and an application are available." />
              ) : (
                <ul className="data-list">
                  {assignments.map((item) => {
                    const nextStatuses = allowedAssignmentTransitions[item.status] || [];
                    return (
                      <li key={item.id} className="data-list-item">
                        <div className="data-list-row">
                          <div>
                            <strong className="data-list-title">
                              {agencyNames.get(item.external_agency_id) || item.external_agency_id}
                            </strong>
                            <span className="data-list-meta">
                              {applicationNames.get(item.application_id) || item.application_id}
                            </span>
                          </div>
                          <div className="status-stack">
                            <StatusBadge value={item.status} />
                            <StatusBadge value={item.sla_status} />
                          </div>
                        </div>
                        <div className="data-list-row">
                          <span className="data-list-meta">
                            {item.agency_reference_number ? `Ref: ${item.agency_reference_number} · ` : null}
                            SLA due{" "}
                            {item.sla_due_at
                              ? new Date(item.sla_due_at).toLocaleString(undefined, {
                                  dateStyle: "medium",
                                  timeStyle: "short",
                                })
                              : "—"}
                            {item.handoff_at ? ` · Handoff ${new Date(item.handoff_at).toLocaleDateString()}` : null}
                            {item.completed_at ? ` · Completed ${new Date(item.completed_at).toLocaleDateString()}` : null}
                          </span>
                        </div>
                        {item.notes ? <p className="data-list-detail">{item.notes}</p> : null}

                        {nextStatuses.length > 0 ? (
                          <div className="data-list-actions stacked">
                            <label className="field slim">
                              <span className="field-label">Status reason</span>
                              <input
                                className="input"
                                type="text"
                                placeholder="Why is the status changing?"
                                value={assignmentStatusReasons[item.id] || ""}
                                onChange={(e) =>
                                  setAssignmentStatusReasons((prev) => ({ ...prev, [item.id]: e.target.value }))
                                }
                              />
                            </label>
                            <label className="field slim">
                              <span className="field-label">Reference number (optional)</span>
                              <input
                                className="input"
                                type="text"
                                placeholder="Update agency reference"
                                value={assignmentRefInputs[item.id] || ""}
                                onChange={(e) =>
                                  setAssignmentRefInputs((prev) => ({ ...prev, [item.id]: e.target.value }))
                                }
                              />
                            </label>
                            <div className="button-group">
                              {nextStatuses.map((status) => (
                                <button
                                  key={status}
                                  className="button small ghost"
                                  type="button"
                                  disabled={working === item.id}
                                  onClick={() => void changeAssignmentStatus(item, status)}
                                >
                                  Move to {titleCase(status)}
                                </button>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <InlineNotice
                            label="Terminal"
                            detail={`${titleCase(item.status)} is a terminal state. No further status changes are permitted.`}
                            tone="neutral"
                          />
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </section>
        </div>
      </div>
    </WorkspaceShell>
  );
}
