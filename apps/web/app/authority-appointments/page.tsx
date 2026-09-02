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
  AuthorityAppointment,
  createAuthorityAppointment,
  listApplications,
  listAuthorityAppointments,
  updateAuthorityAppointmentStatus,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const appointmentTypes: AuthorityAppointment["appointment_type"][] = [
  "biometric",
  "interview",
  "document_submission",
  "other",
];

const statusOptions: AuthorityAppointment["status"][] = [
  "scheduled",
  "completed",
  "cancelled",
  "no_show",
];

const emptyForm = {
  application_id: "",
  appointment_type: "interview" as AuthorityAppointment["appointment_type"],
  authority_name: "",
  location: "",
  scheduled_at: "",
  timezone: "UTC",
  reference_number: "",
  notes: "",
};

export default function AuthorityAppointmentsPage() {
  const { health } = useBackendStatus();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [appointments, setAppointments] = useState<AuthorityAppointment[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [statusReasons, setStatusReasons] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [applicationRows, appointmentRows] = await Promise.all([
        listApplications({ limit: 250 }),
        listAuthorityAppointments(
          selectedApplicationId ? { application_id: selectedApplicationId } : undefined
        ),
      ]);
      setApplications(applicationRows);
      setAppointments(appointmentRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authority appointments workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!loading) void load();
  }, [selectedApplicationId]);

  const filteredAppointments = useMemo(() => {
    return appointments.sort(
      (a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime()
    );
  }, [appointments]);

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

  async function submitAppointment(event: FormEvent) {
    event.preventDefault();
    if (!form.application_id || !form.scheduled_at) return;
    setWorking("appointment");
    setError(null);
    setMessage(null);
    try {
      const created = await createAuthorityAppointment({
        application_id: form.application_id,
        appointment_type: form.appointment_type,
        authority_name: form.authority_name,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        ...(form.location ? { location: form.location } : {}),
        ...(form.timezone ? { timezone: form.timezone } : {}),
        ...(form.reference_number ? { reference_number: form.reference_number } : {}),
        ...(form.notes ? { notes: form.notes } : {}),
      });
      setForm(emptyForm);
      setSelectedApplicationId(created.application_id);
      await load();
      setMessage(`Appointment with ${created.authority_name} scheduled for ${new Date(created.scheduled_at).toLocaleString()}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Appointment could not be scheduled");
    } finally {
      setWorking(null);
    }
  }

  async function changeStatus(appointment: AuthorityAppointment, status: AuthorityAppointment["status"]) {
    const reason = statusReasons[appointment.id]?.trim();
    if (!reason) {
      setError("A reason is required to update appointment status.");
      return;
    }
    setWorking(appointment.id);
    setError(null);
    setMessage(null);
    try {
      await updateAuthorityAppointmentStatus(appointment.id, status, reason);
      setStatusReasons((prev) => ({ ...prev, [appointment.id]: "" }));
      await load();
      setMessage(`${appointment.authority_name} appointment marked ${titleCase(status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Appointment status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  const loadStatus = health?.status === "ok" ? (loading ? "loading" : "ready") : "offline";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Authority Appointments"
        kicker="Government & embassy scheduling"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <div className="workspace-body">
        <div className="workspace-grid two-col">
          <section className="panel">
            <SectionTitle
              label="Schedule"
              title="Book an authority appointment"
              detail="Link the appointment to an application, record the authority, time, and reference, then track the outcome."
            />
            <form onSubmit={submitAppointment} className="form-card">
              <label className="field">
                <span className="field-label">Application</span>
                <select
                  className="input"
                  required
                  value={form.application_id}
                  onChange={(e) => setForm((f) => ({ ...f, application_id: e.target.value }))}
                >
                  <option value="">Select an application…</option>
                  {applications.map((app) => (
                    <option key={app.id} value={app.id}>
                      {applicationNames.get(app.id)}
                    </option>
                  ))}
                </select>
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Appointment type</span>
                  <select
                    className="input"
                    required
                    value={form.appointment_type}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, appointment_type: e.target.value as AuthorityAppointment["appointment_type"] }))
                    }
                  >
                    {appointmentTypes.map((type) => (
                      <option key={type} value={type}>
                        {titleCase(type)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span className="field-label">Scheduled at</span>
                  <input
                    className="input"
                    type="datetime-local"
                    required
                    value={form.scheduled_at}
                    onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))}
                  />
                </label>
              </div>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Authority / embassy</span>
                  <input
                    className="input"
                    type="text"
                    required
                    placeholder="German Consulate Mumbai"
                    value={form.authority_name}
                    onChange={(e) => setForm((f) => ({ ...f, authority_name: e.target.value }))}
                  />
                </label>

                <label className="field">
                  <span className="field-label">Location</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="Mumbai"
                    value={form.location}
                    onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                  />
                </label>
              </div>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Timezone</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="UTC"
                    value={form.timezone}
                    onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))}
                  />
                </label>

                <label className="field">
                  <span className="field-label">Reference number</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="REF-12345"
                    value={form.reference_number}
                    onChange={(e) => setForm((f) => ({ ...f, reference_number: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Notes</span>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Documents to bring, special instructions, or access details."
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </label>

              <div className="form-actions">
                <button className="button primary" type="submit" disabled={working === "appointment"}>
                  {working === "appointment" ? <span className="button-spinner" aria-hidden="true" /> : "Schedule appointment"}
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <SectionTitle
              label="Filter"
              title="Appointment registry"
              detail="Review and update outcomes for embassy, biometric, interview, and document-submission appointments."
            />

            <label className="field">
              <span className="field-label">Filter by application</span>
              <select
                className="input"
                value={selectedApplicationId}
                onChange={(e) => setSelectedApplicationId(e.target.value)}
              >
                <option value="">All applications</option>
                {applications.map((app) => (
                  <option key={app.id} value={app.id}>
                    {applicationNames.get(app.id)}
                  </option>
                ))}
              </select>
            </label>

            {error && <InlineNotice label="Error" detail={error} tone="bad" />}
            {message && <InlineNotice label="Success" detail={message} tone="good" />}

            {filteredAppointments.length === 0 ? (
              <EmptyState
                title="No authority appointments"
                detail="Schedule the first embassy, biometric, or interview appointment using the form."
              />
            ) : (
              <ul className="data-list">
                {filteredAppointments.map((item) => (
                  <li key={item.id} className="data-list-item">
                    <div className="data-list-row">
                      <div>
                        <strong className="data-list-title">{item.authority_name}</strong>
                        <span className="data-list-meta">
                          {titleCase(item.appointment_type)} · {applicationNames.get(item.application_id) || item.application_id}
                        </span>
                      </div>
                      <StatusBadge value={item.status} />
                    </div>
                    <div className="data-list-row">
                      <span className="data-list-meta">
                        {new Date(item.scheduled_at).toLocaleString(undefined, {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                        {item.timezone ? ` (${item.timezone})` : null}
                        {item.location ? ` · ${item.location}` : null}
                        {item.reference_number ? ` · Ref: ${item.reference_number}` : null}
                      </span>
                    </div>
                    {item.notes ? <p className="data-list-detail">{item.notes}</p> : null}

                    <div className="data-list-actions">
                      <label className="field slim">
                        <span className="field-label">Status reason</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="Why is the status changing?"
                          value={statusReasons[item.id] || ""}
                          onChange={(e) =>
                            setStatusReasons((prev) => ({ ...prev, [item.id]: e.target.value }))
                          }
                        />
                      </label>
                      <div className="button-group">
                        {statusOptions.map((status) => (
                          <button
                            key={status}
                            className={`button small ${item.status === status ? "secondary" : "ghost"}`}
                            type="button"
                            disabled={working === item.id}
                            onClick={() => void changeStatus(item, status)}
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
          </section>
        </div>
      </div>
    </WorkspaceShell>
  );
}
