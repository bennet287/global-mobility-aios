"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  DocumentExtractionJob,
  DocumentConsistencyAssessment,
  DocumentRecord,
  DocumentSchemaDefinition,
  getHealthStatus,
  getLeadDetail,
  getLeads,
  HealthStatus,
  Lead,
  listDocumentExtractions,
  listDocumentConsistencyAssessments,
  listDocumentSchemas,
  queueDocumentExtraction,
  reviewDocumentExtraction,
  reviewDocumentConsistencyAssessment,
  seedDocumentSchemas,
  validateDocumentExtraction,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

export default function DocumentIntelligencePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [jobs, setJobs] = useState<DocumentExtractionJob[]>([]);
  const [validations, setValidations] = useState<DocumentConsistencyAssessment[]>([]);
  const [schemas, setSchemas] = useState<DocumentSchemaDefinition[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [healthResult, leadRows, schemaRows] = await Promise.all([
        getHealthStatus(), getLeads(), listDocumentSchemas(),
      ]);
      setHealth(healthResult.data); setLeads(leadRows); setSchemas(schemaRows);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load document intelligence"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function chooseLead(id: string) {
    setLeadId(id); setDocuments([]); setJobs([]); setValidations([]); setError(null); setMessage(null);
    if (!id) return;
    setLoading(true);
    try {
      const [detail, jobRows, validationRows] = await Promise.all([
        getLeadDetail(id), listDocumentExtractions({ lead_id: id }), listDocumentConsistencyAssessments(id),
      ]);
      setDocuments(detail.documents); setJobs(jobRows); setValidations(validationRows);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load lead documents"); }
    finally { setLoading(false); }
  }

  async function seedSchemas() {
    setWorking("schemas"); setError(null);
    try { setSchemas(await seedDocumentSchemas()); setMessage("Published baseline schemas are ready."); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not seed schemas"); }
    finally { setWorking(null); }
  }

  async function queue(document: DocumentRecord) {
    setWorking(document.id); setError(null); setMessage(null);
    try {
      const job = await queueDocumentExtraction(document.id);
      setJobs((rows) => [job, ...rows.filter((row) => row.id !== job.id)]);
      setMessage(`${document.filename} was queued for server-side extraction.`);
      if (!schemas.length) setSchemas(await listDocumentSchemas());
    } catch (err) { setError(err instanceof Error ? err.message : "Could not queue extraction"); }
    finally { setWorking(null); }
  }

  async function review(job: DocumentExtractionJob, decision: "approved" | "rejected") {
    const note = (notes[job.id] || "").trim();
    if (!note) { setError("A review note is required."); return; }
    setWorking(job.id); setError(null); setMessage(null);
    try {
      const updated = await reviewDocumentExtraction(job.id, decision, note);
      setJobs((rows) => rows.map((row) => row.id === updated.id ? updated : row));
      setNotes((current) => ({ ...current, [job.id]: "" }));
      setMessage(`Extraction ${decision}. Document authenticity remains a separate verification decision.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not review extraction"); }
    finally { setWorking(null); }
  }

  async function refreshJobs() {
    if (!leadId) return;
    setWorking("refresh");
    try {
      const [jobRows, validationRows] = await Promise.all([
        listDocumentExtractions({ lead_id: leadId }), listDocumentConsistencyAssessments(leadId),
      ]);
      setJobs(jobRows); setValidations(validationRows);
    }
    catch (err) { setError(err instanceof Error ? err.message : "Could not refresh jobs"); }
    finally { setWorking(null); }
  }

  async function validate(job: DocumentExtractionJob) {
    setWorking(`validate-${job.id}`); setError(null); setMessage(null);
    try {
      const assessment = await validateDocumentExtraction(job.id);
      setValidations((rows) => [assessment, ...rows.filter((row) => row.id !== assessment.id)]);
      setMessage(`Compared extraction with profile v${assessment.profile_version} and application context.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not validate extracted facts"); }
    finally { setWorking(null); }
  }

  async function reviewValidation(assessment: DocumentConsistencyAssessment, decision: "approved" | "rejected") {
    const note = (notes[assessment.id] || "").trim();
    if (!note) { setError("A consistency review note is required."); return; }
    setWorking(assessment.id); setError(null); setMessage(null);
    try {
      const updated = await reviewDocumentConsistencyAssessment(assessment.id, decision, note);
      setValidations((rows) => rows.map((row) => row.id === updated.id ? updated : row));
      setNotes((current) => ({ ...current, [assessment.id]: "" }));
      setMessage(`Consistency assessment ${decision}; source records remain unchanged.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not review consistency assessment"); }
    finally { setWorking(null); }
  }

  const reviewCount = jobs.filter((job) => job.status === "needs_review").length;
  const failedCount = jobs.filter((job) => job.status === "failed").length;
  const inconsistencyCount = validations.filter((item) => item.result_status === "inconsistencies_found").length;
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";
  return (
    <WorkspaceShell health={health}>
      <Topbar title="Document Intelligence" kicker="Server extraction and structured review" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad document-intelligence-page">
        {error && <InlineNotice label="Document intelligence error" detail={error} tone="bad" />}
        {message && <InlineNotice label="Updated" detail={message} tone="good" />}
        <section className="panel document-intelligence-selector">
          <div><span className="page-kicker">Human-controlled extraction</span><strong>Extract structured facts without treating OCR output as verified truth.</strong></div>
          <label>Lead<select value={leadId} onChange={(event) => void chooseLead(event.target.value)}><option value="">Choose a lead</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.full_name} · {lead.target_country || "No target"}</option>)}</select></label>
          <button className="button secondary" disabled={working === "schemas"} onClick={() => void seedSchemas()}>{schemas.length ? `${schemas.length} schemas ready` : "Install schemas"}</button>
        </section>

        <div className="metric-row document-intelligence-metrics">
          <MetricPill label="Stored documents" value={documents.length} />
          <MetricPill label="Extraction jobs" value={jobs.length} />
          <MetricPill label="Needs review" value={reviewCount} tone={reviewCount ? "warn" : "good"} />
          <MetricPill label="Failed" value={failedCount} tone={failedCount ? "warn" : "good"} />
          <MetricPill label="Schema versions" value={schemas.length} />
          <MetricPill label="Inconsistencies" value={inconsistencyCount} tone={inconsistencyCount ? "warn" : "good"} />
        </div>

        {!leadId ? <EmptyState title="No lead selected" detail="Choose a lead to inspect stored documents and extraction history." /> : <div className="document-intelligence-layout">
          <main className="document-intelligence-main">
            <section className="panel">
              <SectionTitle label="Source files" title="Stored lead documents" detail="Only server-readable uploads with a published schema can be queued" />
              <div className="document-source-list">{documents.length ? documents.map((document) => {
                const active = jobs.find((job) => job.document_id === document.id && ["queued", "processing"].includes(job.status));
                return <article key={document.id}><div><div><strong>{document.filename}</strong><p>{titleCase(document.document_type)} · {document.mime_type || "unknown format"}</p></div><StatusBadge value={document.status} /></div><div className="document-source-meta"><span>Storage {document.storage_provider || "missing"}</span><span>Hash {document.file_hash?.slice(0, 12) || "missing"}</span></div><button className="button secondary" disabled={Boolean(active) || working === document.id || !document.storage_provider} onClick={() => void queue(document)}>{active ? titleCase(active.status) : "Queue extraction"}</button></article>;
              }) : <EmptyState title="No documents" detail="Upload a document from the lead workspace before starting extraction." />}</div>
            </section>

            <section className="panel">
              <div className="document-jobs-heading"><SectionTitle label="Worker queue" title="Extraction and review history" detail="Refresh after the worker completes queued jobs" /><button className="button secondary" disabled={working === "refresh"} onClick={() => void refreshJobs()}>Refresh jobs</button></div>
              <div className="document-job-list">{jobs.length ? jobs.map((job) => <article key={job.id}>
                <div className="document-job-heading"><div><span>{job.schema_key} · v{job.schema_version}</span><h3>{titleCase(job.document_type)}</h3></div><StatusBadge value={job.status} /></div>
                <p>Engine {job.engine} · attempt {job.attempt_count} · requested by {job.requested_by}</p>
                {Object.keys(job.structured_data).length > 0 && <dl>{Object.entries(job.structured_data).map(([key, value]) => <div key={key}><dt>{titleCase(key)}</dt><dd>{String(value)}</dd><small>{Math.round((job.field_confidence[key] || 0) * 100)}% extraction confidence</small></div>)}</dl>}
                {job.warnings.length > 0 && <div className="document-job-warnings">{job.warnings.map((warning) => <span key={warning}>{warning}</span>)}</div>}
                {job.error_message && <InlineNotice label={job.error_code || "Extraction failed"} detail={job.error_message} tone="bad" />}
                {job.status === "needs_review" && <div className="document-review-actions"><input placeholder="Required human review note" value={notes[job.id] || ""} onChange={(event) => setNotes((current) => ({ ...current, [job.id]: event.target.value }))} /><button className="button primary" disabled={working === job.id} onClick={() => void review(job, "approved")}>Approve fields</button><button className="button secondary" disabled={working === job.id} onClick={() => void review(job, "rejected")}>Reject fields</button></div>}
                {job.status === "approved" && <button className="button secondary document-validate-button" disabled={working === `validate-${job.id}`} onClick={() => void validate(job)}>Validate against profile and application</button>}
                {job.reviewed_by && <small className="document-review-ledger">Reviewed by {job.reviewed_by} · {job.review_notes}</small>}
              </article>) : <EmptyState title="No extraction jobs" detail="Queue a supported stored document to create the first job." />}</div>
            </section>

            <section className="panel">
              <SectionTitle label="Consistency ledger" title="Profile and application validation" detail="Each assessment is pinned to an immutable profile version and application snapshot" />
              <div className="document-validation-list">{validations.length ? validations.map((assessment) => <article key={assessment.id}>
                <div className="document-job-heading"><div><span>Profile v{assessment.profile_version} · {assessment.application_id ? `application ${assessment.application_id.slice(0, 8)}` : "no application"}</span><h3>{titleCase(assessment.result_status)}</h3></div><StatusBadge value={assessment.review_status} /></div>
                <p>{assessment.summary}</p>
                <div className="document-validation-counts"><span>{assessment.match_count} matches</span><span>{assessment.mismatch_count} mismatches</span><span>{assessment.missing_count} missing</span></div>
                <div className="document-finding-list">{assessment.findings.map((finding) => <article className={finding.outcome} key={finding.finding_key}><div><strong>{titleCase(finding.finding_key)}</strong><StatusBadge value={finding.outcome} /></div><p>{finding.explanation}</p><small>{finding.source_path} · document: {String(finding.extracted_value ?? "missing")} · source: {String(finding.source_value ?? "missing")}</small></article>)}</div>
                {assessment.review_status === "pending" && <div className="document-review-actions"><input placeholder="Required consistency review note" value={notes[assessment.id] || ""} onChange={(event) => setNotes((current) => ({ ...current, [assessment.id]: event.target.value }))} /><button className="button primary" disabled={working === assessment.id} onClick={() => void reviewValidation(assessment, "approved")}>Approve assessment</button><button className="button secondary" disabled={working === assessment.id} onClick={() => void reviewValidation(assessment, "rejected")}>Reject assessment</button></div>}
                {assessment.reviewed_by && <small className="document-review-ledger">Reviewed by {assessment.reviewed_by} · {assessment.review_notes}</small>}
              </article>) : <EmptyState title="No consistency assessments" detail="Approve an extraction, then validate it against the current profile and application context." />}</div>
            </section>
          </main>
          <aside className="panel document-schema-side"><SectionTitle label="Structured schemas" title="Published baseline" detail="Exact schema versions remain attached to every job" /><div>{schemas.map((schema) => <article key={schema.id}><div><strong>{titleCase(schema.document_type)}</strong><StatusBadge value={schema.lifecycle_status} /></div><p>{schema.schema_key} · version {schema.version_number}</p><small>{Object.keys((schema.json_schema.properties as Record<string, unknown>) || {}).length} structured fields · approved by {schema.approved_by}</small></article>)}</div><InlineNotice label="Verification boundary" detail="Approving extracted fields does not verify authenticity, eligibility, or consistency with profile facts." tone="warn" /><div className="planning-links"><Link className="button secondary" href={leadId ? `/leads/${leadId}` : "/"}>Open lead</Link><Link className="button secondary" href="/profiles">Open profile</Link></div></aside>
        </div>}
      </div>
    </WorkspaceShell>
  );
}
