"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { createPublicIntake, PublicIntakePayload, PublicIntakeResponse } from "../../lib/api";
import { DocumentOcrUploader } from "../../components/DocumentOcrUploader";

const GOALS = [
  "Work abroad",
  "Study abroad",
  "Get a visa",
  "Permanent residency",
  "Not sure yet",
];

const COUNTRIES = ["Austria", "Germany", "Canada", "Australia", "UK", "USA", "Other"];

const JOB_OFFER_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "none", label: "I do not have a job offer" },
  { value: "pending", label: "I have a pending offer" },
  { value: "signed", label: "I have a signed offer" },
];

const QUALIFICATION_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "not_started", label: "Not started" },
  { value: "in_progress", label: "In progress" },
  { value: "recognized", label: "Recognized" },
  { value: "unknown", label: "I am unsure" },
];

const LANGUAGE_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "A1", label: "A1 - Beginner" },
  { value: "A2", label: "A2 - Elementary" },
  { value: "B1", label: "B1 - Intermediate" },
  { value: "B2", label: "B2 - Upper intermediate" },
  { value: "C1", label: "C1 - Advanced" },
  { value: "C2", label: "C2 - Proficient" },
  { value: "unknown", label: "I do not know" },
];

export default function IntakePage() {
  const [form, setForm] = useState<PublicIntakePayload>({
    full_name: "",
    email: "",
    phone: "",
    goal: "Work abroad",
    nationality: "",
    profession: "",
    years_experience: undefined,
    target_country: "Germany",
    current_country: "",
    job_offer_status: "",
    qualification_recognition: "",
    language_level: "",
    notes: "",
  });
  const [result, setResult] = useState<PublicIntakeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submissionKey = useRef("");

  const isAustria = form.target_country === "Austria";

  const update = <K extends keyof PublicIntakePayload>(key: K, value: PublicIntakePayload[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!submissionKey.current) {
        submissionKey.current = crypto.randomUUID();
      }
      const response = await createPublicIntake({ ...form, submission_key: submissionKey.current });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="intake-page">
      <header className="intake-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Start your case</small>
          </div>
        </Link>
      </header>

      <main className="intake-main">
        {!result ? (
          <section className="panel intake-panel">
            <h1>Tell us your goal</h1>
            <p className="intake-lead">
              Share a few details and our agents will prepare a personalized pathway for a consultant to review.
            </p>

            <form onSubmit={submit} className="intake-form public-intake">
              <label className="full-field">
                Full name
                <input
                  required
                  value={form.full_name}
                  onChange={(e) => update("full_name", e.target.value)}
                  placeholder="Your name"
                />
              </label>

              <label>
                Email
                <input
                  type="email"
                  value={form.email || ""}
                  onChange={(e) => update("email", e.target.value)}
                  placeholder="you@example.com"
                />
              </label>

              <label>
                Phone
                <input
                  value={form.phone || ""}
                  onChange={(e) => update("phone", e.target.value)}
                  placeholder="+1 234 567 890"
                />
              </label>

              <label className="full-field">
                What is your main goal?
                <select value={form.goal} onChange={(e) => update("goal", e.target.value)}>
                  {GOALS.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Nationality
                <input
                  required
                  value={form.nationality}
                  onChange={(e) => update("nationality", e.target.value)}
                  placeholder="e.g., India"
                />
              </label>

              <label>
                Current country
                <input
                  value={form.current_country || ""}
                  onChange={(e) => update("current_country", e.target.value)}
                  placeholder="e.g., India"
                />
              </label>

              <label>
                Profession
                <input
                  required
                  value={form.profession}
                  onChange={(e) => update("profession", e.target.value)}
                  placeholder="e.g., Registered Nurse"
                />
              </label>

              <label>
                Years of experience
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={form.years_experience ?? ""}
                  onChange={(e) => update("years_experience", e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="3"
                />
              </label>

              <label>
                Target country
                <select value={form.target_country} onChange={(e) => update("target_country", e.target.value)}>
                  {COUNTRIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>

              {isAustria && (
                <>
                  <label className="full-field">
                    Austria job-offer status
                    <select value={form.job_offer_status || ""} onChange={(e) => update("job_offer_status", e.target.value)}>
                      {JOB_OFFER_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </label>

                  <label className="full-field">
                    Qualification recognition status for Austria
                    <select value={form.qualification_recognition || ""} onChange={(e) => update("qualification_recognition", e.target.value)}>
                      {QUALIFICATION_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </label>

                  <label className="full-field">
                    German language level
                    <select value={form.language_level || ""} onChange={(e) => update("language_level", e.target.value)}>
                      {LANGUAGE_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </label>
                </>
              )}

              <label className="full-field">
                Anything else we should know?
                <textarea
                  value={form.notes || ""}
                  onChange={(e) => update("notes", e.target.value)}
                  placeholder="Budget, language skills, family situation, deadlines..."
                  rows={4}
                />
              </label>

              {error && <div className="inline-notice error">{error}</div>}

              <div className="form-actions full-field">
                <button className="button primary" type="submit" disabled={loading}>
                  {loading ? "Starting your case..." : "Start my case"}
                </button>
              </div>
            </form>
          </section>
        ) : (
          <section className="panel intake-panel success">
            <div className="success-icon">✓</div>
            <h1>Your case has been created.</h1>
            <p><strong>{form.target_country} · {form.goal}</strong></p>
            <p>Case reference: <strong>{result.case_reference}</strong></p>
            <p>{result.message}</p>

            <div className="checklist">
              <h2>Your personalized checklist</h2>
              <ul>
                {result.checklist.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>

            {result.lead_id && (
              <div className="ocr-section">
                <h2>Upload a document to auto-fill details</h2>
                <p className="intake-lead">
                  Optional: upload an image of your passport, CV, or certificate and we&apos;ll extract text for the consultant.
                </p>
                <DocumentOcrUploader leadId={result.lead_id} />
              </div>
            )}

            {result.lead_id && (
              <div className="eligibility-link">
                <Link className="button primary" href={`/eligibility?lead_id=${result.lead_id}`}>
                  Continue your case
                </Link>
                <Link className="button secondary" href={`/profiles?lead_id=${result.lead_id}`}>Open mobility profile</Link>
                <Link className="button secondary" href={`/planning?lead_id=${result.lead_id}`}>Open mobility planning</Link>
                <Link className="button secondary" href={`/validation?lead_id=${result.lead_id}`}>Open external validation</Link>
              </div>
            )}

            <p className="intake-lead">
              Save this return link to check your case status later:{" "}
              <Link href={`/return?token=${result.session_token}`}>
                Return to my case
              </Link>
            </p>

            <div className="form-actions">
              <Link className="button secondary" href="/">
                Go to operator workspace
              </Link>
              <button className="button secondary" onClick={() => { submissionKey.current = ""; setResult(null); }}>
                Start another case
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
