"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  ExternalValidationFinding,
  ExternalValidationRun,
  ExternalValidationScenario,
  addExternalValidationEvidence,
  addExternalValidationFinding,
  boardAcceptExternalValidationFinding,
  createExternalValidationRun,
  evaluateExternalValidationRun,
  listExternalValidationRuns,
  listExternalValidationScenarios,
  seedExternalValidationScenario,
  submitExternalValidationReview,
  triageExternalValidationFinding,
  updateExternalValidationRun,
} from "../../lib/api";

const evidenceTypes = [
  "truth_claim",
  "verified_rule",
  "official_source",
  "source_snapshot",
  "pathway_version",
  "pathway_comparison",
  "document",
  "operator_note",
] as const;

function promptRequired(label: string, initial = ""): string | null {
  const value = window.prompt(label, initial);
  if (!value || !value.trim()) return null;
  return value.trim();
}

export default function ExternalValidationPage() {
  const { health } = useBackendStatus();
  const [scenarios, setScenarios] = useState<ExternalValidationScenario[]>([]);
  const [runs, setRuns] = useState<ExternalValidationRun[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [scenarioId, setScenarioId] = useState("");
  const [leadId, setLeadId] = useState("");
  const [comparisonId, setComparisonId] = useState("");
  const [founderInterventions, setFounderInterventions] = useState("0");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selected = useMemo(
    () => runs.find((run) => run.id === selectedId) || runs[0] || null,
    [runs, selectedId],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenarioRows, runRows] = await Promise.all([
        listExternalValidationScenarios(),
        listExternalValidationRuns(),
      ]);
      setScenarios(scenarioRows);
      setRuns(runRows);
      if (!scenarioId && scenarioRows[0]) setScenarioId(scenarioRows[0].id);
      if (!selectedId && runRows[0]) setSelectedId(runRows[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "External validation workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }, [scenarioId, selectedId]);

  useEffect(() => { void load(); }, [load]);

  async function act(action: () => Promise<unknown>, success: string) {
    setWorking(true); setError(null); setMessage(null);
    try {
      await action();
      setMessage(success);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation action failed");
    } finally {
      setWorking(false);
    }
  }

  async function seed() {
    await act(async () => { await seedExternalValidationScenario(); }, "Austria validation scenario is ready.");
  }

  async function createRun() {
    if (!scenarioId) { setError("Choose or seed a validation scenario first."); return; }
    if (!leadId.trim()) { setError("A lead UUID is required so the external run is pinned to one workflow."); return; }
    if (!comparisonId.trim()) { setError("A pathway comparison UUID is required so the external run is pinned to the result shown to testers."); return; }
    const count = Number.parseInt(founderInterventions || "0", 10);
    if (!Number.isFinite(count) || count < 0) { setError("Founder intervention count must be zero or greater."); return; }
    await act(async () => {
      const run = await createExternalValidationRun({
        scenario_id: scenarioId,
        lead_id: leadId.trim(),
        pathway_comparison_assessment_id: comparisonId.trim(),
        founder_intervention_count: count,
      });
      setSelectedId(run.id);
    }, "External validation run created. Attach the exact Truth Engine/pathway evidence shown to testers.");
  }

  async function setInterventions() {
    if (!selected) return;
    const value = promptRequired("Founder intervention count", String(selected.founder_intervention_count));
    if (value === null) return;
    const count = Number.parseInt(value, 10);
    if (!Number.isFinite(count) || count < 0) { setError("Founder intervention count must be zero or greater."); return; }
    await act(async () => { await updateExternalValidationRun(selected.id, { founder_intervention_count: count }); }, "Founder intervention count updated.");
  }

  async function addEvidence() {
    if (!selected) return;
    const type = window.prompt(`Evidence type:\n${evidenceTypes.join(" | ")}`, "truth_claim")?.trim() as typeof evidenceTypes[number] | undefined;
    if (!type || !evidenceTypes.includes(type)) { setError("Choose a supported evidence type."); return; }
    const entityId = type === "operator_note" ? null : promptRequired(`${type} entity UUID`);
    if (type !== "operator_note" && !entityId) return;
    const label = promptRequired("Short evidence label");
    if (!label) return;
    await act(async () => {
      await addExternalValidationEvidence(selected.id, {
        evidence_type: type,
        entity_id: entityId,
        label,
      });
    }, "Validation evidence pinned.");
  }

  async function addReview(type: "mobility_user" | "professional_operator") {
    if (!selected) return;
    const reviewerName = promptRequired(type === "mobility_user" ? "External mobility-user name" : "Independent professional/operator name");
    if (!reviewerName) return;
    const feedback = promptRequired("Substantive external reviewer feedback");
    if (!feedback) return;
    const usefulness = Number.parseInt(promptRequired("Usefulness rating (1–5)", "5") || "", 10);
    if (!Number.isInteger(usefulness) || usefulness < 1 || usefulness > 5) { setError("Usefulness rating must be 1–5."); return; }

    if (type === "mobility_user") {
      const understanding = Number.parseInt(promptRequired("Understanding rating (1–5)", "5") || "", 10);
      if (!Number.isInteger(understanding) || understanding < 1 || understanding > 5) { setError("Understanding rating must be 1–5."); return; }
      await act(async () => {
        await submitExternalValidationReview(selected.id, {
          reviewer_type: type,
          reviewer_name: reviewerName,
          external_human_attestation: true,
          workflow_completed: true,
          understanding_rating: understanding,
          usefulness_rating: usefulness,
          feedback,
        });
      }, "External mobility-user review recorded.");
      return;
    }

    const correct = window.confirm("Does the professional/operator confirm the jurisdiction/pathway result is correct for the supplied facts?");
    const traceability = Number.parseFloat(promptRequired("Material-rule traceability percent", "100") || "");
    const unsupported = Number.parseInt(promptRequired("Unsupported legal-certainty statement count", "0") || "", 10);
    const missingDocuments = Number.parseInt(promptRequired("Missing critical document requirement count", "0") || "", 10);
    if (![traceability, unsupported, missingDocuments].every(Number.isFinite)) { setError("Professional validation metrics must be numeric."); return; }
    await act(async () => {
      await submitExternalValidationReview(selected.id, {
        reviewer_type: type,
        reviewer_name: reviewerName,
        external_human_attestation: true,
        workflow_completed: true,
        usefulness_rating: usefulness,
        jurisdiction_pathway_correct: correct,
        material_rule_traceability_percent: traceability,
        unsupported_legal_certainty_count: unsupported,
        missing_critical_document_count: missingDocuments,
        feedback,
      });
    }, "Independent professional/operator review recorded.");
  }

  async function addFinding() {
    if (!selected) return;
    const severity = window.prompt("Finding severity: critical | high | medium | low", "medium")?.trim() as "critical" | "high" | "medium" | "low" | undefined;
    if (!severity || !["critical", "high", "medium", "low"].includes(severity)) { setError("Choose critical, high, medium, or low."); return; }
    const category = promptRequired("Finding category", "workflow");
    const title = promptRequired("Finding title");
    const description = promptRequired("Finding description");
    if (!category || !title || !description) return;
    await act(async () => {
      await addExternalValidationFinding(selected.id, { severity, category, title, description });
    }, "Validation finding recorded for triage.");
  }

  async function triageFinding(finding: ExternalValidationFinding, status: "triaged" | "resolved") {
    const notes = promptRequired(status === "resolved" ? "Resolution and retest notes" : "Triage notes");
    if (!notes) return;
    await act(async () => { await triageExternalValidationFinding(finding.id, status, notes); }, `Finding ${status}.`);
  }

  async function boardAccept(finding: ExternalValidationFinding) {
    const reason = promptRequired("Human Board risk-acceptance rationale (medium/low only)");
    if (!reason) return;
    await act(async () => { await boardAcceptExternalValidationFinding(finding.id, reason); }, "Human Board risk acceptance recorded.");
  }

  async function evaluate() {
    if (!selected) return;
    await act(async () => { await evaluateExternalValidationRun(selected.id); }, "Deterministic external-validation gate evaluated.");
  }

  return <WorkspaceShell health={health}>
    <Topbar title="External Validation" kicker="Phase 13.10.2 · Truth Engine + pathway product gate" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />

    <section className="validation-hero">
      <div>
        <span className="eyebrow">Department-expansion gate</span>
        <h2>Prove the mobility workflow with people outside the AI organization.</h2>
        <p>Finance, Communications, People, and Legal remain held until one real mobility user and one independent professional/operator complete the same evidence-backed workflow and the deterministic gate passes.</p>
      </div>
      <div className={`validation-gate-card ${selected?.gate.status || "held"}`}>
        <span>Latest selected gate</span>
        <strong>{selected?.gate.status || "held"}</strong>
        <small>{selected ? `${selected.gate.completed_reviewer_types.length}/2 external reviewer types · ${selected.evidence.length} evidence refs` : "Create the first validation run."}</small>
      </div>
    </section>

    {error ? <InlineNotice label="Validation action needs attention" detail={error} tone="bad" /> : null}
    {message ? <InlineNotice label="Validation ledger updated" detail={message} tone="good" /> : null}

    <section className="validation-create-grid">
      <div className="panel validation-create-card">
        <header><div><span className="eyebrow">Scenario</span><h3>Austria first-run fixture</h3></div></header>
        <p>The fixture supplies persona facts and acceptance criteria only. It deliberately does not encode the expected pathway or legal answer.</p>
        <button className="button" disabled={working} onClick={() => void seed()}>Seed / verify Austria scenario</button>
        <label>Scenario
          <select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
            <option value="">Choose scenario</option>
            {scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.jurisdiction_code} · {scenario.title}</option>)}
          </select>
        </label>
      </div>

      <div className="panel validation-create-card">
        <header><div><span className="eyebrow">Run</span><h3>Pin the real workflow</h3></div></header>
        <label>Lead UUID <input value={leadId} onChange={(event) => setLeadId(event.target.value)} placeholder="Existing real/test lead" /></label>
        <label>Pathway comparison UUID <input value={comparisonId} onChange={(event) => setComparisonId(event.target.value)} placeholder="Pinned comparison shown to testers" /></label>
        <label>Founder interventions <input type="number" min="0" value={founderInterventions} onChange={(event) => setFounderInterventions(event.target.value)} /></label>
        <button className="button" disabled={working || !scenarioId || !leadId.trim() || !comparisonId.trim()} onClick={() => void createRun()}>Create validation run</button>
      </div>
    </section>

    <section className="validation-workspace">
      <aside className="panel validation-run-list">
        <header><div><span className="eyebrow">Runs</span><h3>Validation ledger</h3></div><strong>{runs.length}</strong></header>
        {!runs.length ? <div className="board-empty"><strong>No external runs yet</strong><span>Seed the Austria scenario and create one.</span></div> : runs.map((run) =>
          <button key={run.id} className={selected?.id === run.id ? "active" : ""} onClick={() => setSelectedId(run.id)}>
            <span>{run.scenario.jurisdiction_code} · {run.run_key}</span>
            <strong>{run.gate.status}</strong>
            <small>{run.reviews.length}/2 reviewers · {run.findings.length} findings</small>
          </button>
        )}
      </aside>

      <div className="validation-detail">
        {!selected ? <section className="panel board-empty"><strong>Select or create a run</strong><span>The gate will stay held until external human evidence exists.</span></section> : <>
          <section className="panel validation-status-panel">
            <header><div><span className="eyebrow">Deterministic receipt</span><h3>{selected.scenario.title}</h3></div><span className={`validation-status-pill ${selected.gate.status}`}>{selected.gate.status}</span></header>
            <div className="validation-metrics">
              <div><span>Founder interventions</span><strong>{selected.founder_intervention_count}</strong></div>
              <div><span>External reviewers</span><strong>{selected.gate.completed_reviewer_types.length}/2</strong></div>
              <div><span>Evidence captured</span><strong>{selected.gate.captured_evidence_types.length}/{selected.gate.required_evidence_types.length}</strong></div>
              <div><span>Critical / high open</span><strong>{selected.gate.critical_open + selected.gate.high_open}</strong></div>
            </div>
            <div className="validation-reasons">{selected.gate.reasons.map((reason) => <p key={reason}>{reason}</p>)}</div>
            <div className="validation-actions">
              <button disabled={working} onClick={() => void addEvidence()}>Attach evidence</button>
              <button disabled={working || selected.reviews.some((r) => r.reviewer_type === "mobility_user")} onClick={() => void addReview("mobility_user")}>Record mobility-user review</button>
              <button disabled={working || selected.reviews.some((r) => r.reviewer_type === "professional_operator")} onClick={() => void addReview("professional_operator")}>Record professional review</button>
              <button disabled={working} onClick={() => void addFinding()}>Add finding</button>
              <button disabled={working} onClick={() => void setInterventions()}>Update interventions</button>
              <button className="button" disabled={working} onClick={() => void evaluate()}>Evaluate gate</button>
            </div>
          </section>

          <div className="validation-two-column">
            <section className="panel validation-evidence-panel">
              <header><div><span className="eyebrow">Provenance</span><h3>Evidence references</h3></div><strong>{selected.evidence.length}</strong></header>
              {!selected.evidence.length ? <div className="board-empty"><strong>No evidence pinned</strong><span>Attach the actual Truth Engine, source, and pathway records used.</span></div> : selected.evidence.map((item) => <article key={item.id}><span>{item.evidence_type}</span><strong>{item.label}</strong><small>{item.entity_id || "operator note"}</small></article>)}
            </section>

            <section className="panel validation-review-panel">
              <header><div><span className="eyebrow">External humans</span><h3>Reviewer receipts</h3></div><strong>{selected.reviews.length}/2</strong></header>
              {!selected.reviews.length ? <div className="board-empty"><strong>No external feedback yet</strong><span>The AI organization cannot satisfy this requirement itself.</span></div> : selected.reviews.map((review) => <article key={review.id}><span>{review.reviewer_type.replaceAll("_", " ")}</span><strong>{review.reviewer_name}</strong><p>{review.feedback}</p><small>Usefulness {review.usefulness_rating}/5 · external attestation {review.external_human_attestation ? "recorded" : "missing"}</small></article>)}
            </section>
          </div>

          <section className="panel validation-findings-panel">
            <header><div><span className="eyebrow">Defect ledger</span><h3>Findings and remediation</h3></div><strong>{selected.findings.length}</strong></header>
            {!selected.findings.length ? <div className="board-empty"><strong>No findings recorded</strong><span>Do not treat an empty ledger as evidence until both external reviews are complete.</span></div> : selected.findings.map((finding) => <article key={finding.id}>
              <div><span>{finding.severity} · {finding.category}</span><strong>{finding.title}</strong><p>{finding.description}</p></div>
              <div className="validation-finding-actions"><b>{finding.status}</b>
                {finding.status !== "resolved" && finding.status !== "accepted_risk" ? <>
                  <button disabled={working} onClick={() => void triageFinding(finding, "triaged")}>Triage</button>
                  <button disabled={working} onClick={() => void triageFinding(finding, "resolved")}>Resolve</button>
                  {(finding.severity === "medium" || finding.severity === "low") ? <button disabled={working} onClick={() => void boardAccept(finding)}>Board accept</button> : null}
                </> : null}
              </div>
            </article>)}
          </section>
        </>}
      </div>
    </section>
  </WorkspaceShell>;
}
