"use client";

import { useState } from "react";
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

const COUNTRIES = ["Germany", "Canada", "Australia", "UK", "USA", "Other"];

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
    notes: "",
  });
  const [result, setResult] = useState<PublicIntakeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = <K extends keyof PublicIntakePayload>(key: K, value: PublicIntakePayload[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await createPublicIntake(form);
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
            <h1>Case started</h1>
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

            <div className="form-actions">
              <Link className="button primary" href="/">
                Go to operator workspace
              </Link>
              <button className="button secondary" onClick={() => setResult(null)}>
                Start another case
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
