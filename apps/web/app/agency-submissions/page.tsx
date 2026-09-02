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
  AgencySubmission,
  ApplicationRecord,
  createAgencySubmission,
  listAgencySubmissions,
  listApplications,
  updateAgencySubmissionStatus,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const submissionChannels: AgencySubmission["submission_channel"][] = [
  "online",
  "in_person",
  "courier",
  "agency",
];

const statusWorkflow: AgencySubmission["status"][] = [
  "submitted",
  "acknowledged",
  "under_review",
  "decision_received",
  "returned",
];

const terminalStatuses: AgencySubmission["status"][] = ["decision_received", "returned"];

const emptyForm = {
  application_id: "",
  submission_channel: "online" as AgencySubmission["submission_channel"],
  authority_name: "",
  submitted_at: "",
  reference_number: "",
  tracking_url: "",
  notes: "",
};

export default function AgencySubmissionsPage() {
  const { health } = useBackendStatus();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [submissions, setSubmissions] = useState<AgencySubmission[]>([]);
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
      const [applicationRows, submissionRows] = await Promise.all([
        listApplications({ limit: 250 }),
        listAgencySubmissions(
          selectedApplicationId ? { application_id: selectedApplicationId } : undefined
        ),
      ]);
      setApplications(applicationRows);
      setSubmissions(submissionRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agency submissions workspace could not be loaded");
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

  const filteredSubmissions = useMemo(() => {
    return [...submissions].sort(
      (a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
    );
  }, [submissions]);

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

  function availableNextStatuses(current: AgencySubmission["status"]): AgencySubmission["status"][] {
    if (terminalStatuses.includes(current)) return [];
    const index = statusWorkflow.indexOf(current);
    if (index === -1) return [];
    return statusWorkflow.slice(index + 1);
  }

  async function submitSubmission(event: FormEvent) {
    event.preventDefault();
    if (!form.application_id || !form.submitted_at || !form.authority_name) return;
    setWorking("submission");
    setError(null);
    setMessage(null);
    try {
      const created = await createAgencySubmission({
        application_id: form.application_id,
        authority_name: form.authority_name,
        submission_channel: form.submission_channel,
        submitted_at: new Date(form.submitted_at).toISOString(),
        ...(form.reference_number ? { reference_number: form.reference_number } : {}),
        ...(form.tracking_url ? { tracking_url: form.tracking_url } : {}),
        ...(form.notes ? { notes: form.notes } : {}),
      });
      setForm(emptyForm);
      setSelectedApplicationId(created.application_id);
      await load();
      setMessage(`Submission to ${created.authority_name} recorded as ${titleCase(created.submission_channel)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission could not be recorded");
    } finally {
      setWorking(null);
    }
  }

  async function changeStatus(submission: AgencySubmission, status: AgencySubmission["status"]) {
    const reason = statusReasons[submission.id]?.trim();
    if (!reason) {
      setError("A reason is required to update submission status.");
      return;
    }
    setWorking(submission.id);
    setError(null);
    setMessage(null);
    try {
      await updateAgencySubmissionStatus(submission.id, status, reason);
      setStatusReasons((prev) => ({ ...prev, [submission.id]: "" }));
      await load();
      setMessage(`${submission.authority_name} submission moved to ${titleCase(status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  const loadStatus = health?.status === "ok" ? (loading ? "loading" : "ready") : "offline";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Agency Submissions"
        kicker="Government and mobility agency tracking"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <div className="workspace-body">
        <div className="workspace-grid two-col">
          <section className="panel">
            <SectionTitle
              label="Record"
              title="Log a submission to an authority"
              detail="Record when and how the application was submitted. Track reference numbers and progress without changing the application lifecycle state."
            />
            <form onSubmit={submitSubmission} className="form-card">
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
                  <span className="field-label">Submission channel</span>
                  <select
                    className="input"
                    required
                    value={form.submission_channel}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, submission_channel: e.target.value as AgencySubmission["submission_channel"] }))
                    }
                  >
                    {submissionChannels.map((channel) => (
                      <option key={channel} value={channel}>
                        {titleCase(channel)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span className="field-label">Submitted at</span>
                  <input
                    className="input"
                    type="datetime-local"
                    required
                    value={form.submitted_at}
                    onChange={(e) => setForm((f) => ({ ...f, submitted_at: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Authority / agency</span>
                <input
                  className="input"
                  type="text"
                  required
                  placeholder="German Consulate Mumbai"
                  value={form.authority_name}
                  onChange={(e) => setForm((f) => ({ ...f, authority_name: e.target.value }))}
                />
              </label>

              <div className="form-row">
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

                <label className="field">
                  <span className="field-label">Tracking URL</span>
                  <input
                    className="input"
                    type="url"
                    placeholder="https://..."
                    value={form.tracking_url}
                    onChange={(e) => setForm((f) => ({ ...f, tracking_url: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Notes</span>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Courier details, submission centre, or operator notes."
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </label>

              <div className="form-actions">
                <button className="button primary" type="submit" disabled={working === "submission"}>
                  {working === "submission" ? <span className="button-spinner" aria-hidden="true" /> : "Record submission"}
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <SectionTitle
              label="Registry"
              title="Submission progress"
              detail="Track submission status from logged to acknowledged, under review, decision received, or returned."
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

            {filteredSubmissions.length === 0 ? (
              <EmptyState
                title="No agency submissions"
                detail="Record the first submission event using the form."
              />
            ) : (
              <ul className="data-list">
                {filteredSubmissions.map((item) => {
                  const nextStatuses = availableNextStatuses(item.status);
                  return (
                    <li key={item.id} className="data-list-item">
                      <div className="data-list-row">
                        <div>
                          <strong className="data-list-title">{item.authority_name}</strong>
                          <span className="data-list-meta">
                            {titleCase(item.submission_channel)} · {applicationNames.get(item.application_id) || item.application_id}
                          </span>
                        </div>
                        <StatusBadge value={item.status} />
                      </div>
                      <div className="data-list-row">
                        <span className="data-list-meta">
                          Submitted{" "}
                          {new Date(item.submitted_at).toLocaleString(undefined, {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                          {item.reference_number ? ` · Ref: ${item.reference_number}` : null}
                        </span>
                      </div>
                      {item.tracking_url ? (
                        <a
                          className="data-list-detail link"
                          href={item.tracking_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Tracking link
                        </a>
                      ) : null}
                      {item.notes ? <p className="data-list-detail">{item.notes}</p> : null}

                      {nextStatuses.length > 0 ? (
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
                            {nextStatuses.map((status) => (
                              <button
                                key={status}
                                className="button small ghost"
                                type="button"
                                disabled={working === item.id}
                                onClick={() => void changeStatus(item, status)}
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
          </section>
        </div>
      </div>
    </WorkspaceShell>
  );
}
