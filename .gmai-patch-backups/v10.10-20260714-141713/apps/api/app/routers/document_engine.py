import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import DocumentRecord, Lead, LeadIntent

router = APIRouter()


class DocumentStatusUpdate(BaseModel):
    status: str
    filename: Optional[str] = None
    storage_key: Optional[str] = None
    notes: Optional[str] = None


class DocumentCreateRequest(BaseModel):
    document_type: str
    filename: str
    storage_key: Optional[str] = None
    status: str = "received"
    notes: Optional[str] = None


def _intent_value(lead: Lead) -> str:
    if isinstance(lead.intent, LeadIntent):
        return lead.intent.value
    return str(lead.intent)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def _document_checklist_for_lead(lead: Lead) -> list[str]:
    intent = _intent_value(lead)
    country = (lead.target_country or "").strip().lower()

    base = [
        "passport",
        "resume_cv",
        "identity_photo",
    ]

    study = [
        "highest_degree_certificate",
        "academic_transcripts",
        "language_test_certificate",
        "statement_of_purpose",
        "letters_of_recommendation",
        "admission_letter",
        "financial_proof",
        "health_insurance",
        "visa_application_form",
    ]

    visa = [
        "visa_application_form",
        "passport",
        "identity_photo",
        "financial_proof",
        "travel_or_health_insurance",
        "accommodation_proof",
        "appointment_confirmation",
        "admission_or_offer_letter",
    ]

    job = [
        "resume_cv",
        "passport",
        "highest_degree_certificate",
        "academic_transcripts",
        "work_experience_letters",
        "skill_certificates",
        "job_offer_or_employment_contract",
        "language_test_certificate",
        "police_clearance_if_required",
    ]

    document_only = [
        "passport",
        "resume_cv",
        "academic_transcripts",
        "highest_degree_certificate",
    ]

    country_specific = []

    if country == "germany":
        country_specific.extend(
            [
                "financial_proof",
                "health_insurance",
                "admission_or_offer_letter",
            ]
        )

    if country == "canada":
        country_specific.extend(
            [
                "study_permit_or_work_permit_forms",
                "proof_of_funds",
                "letter_of_acceptance_or_job_offer",
            ]
        )

    if country in {"united kingdom", "uk", "great britain"}:
        country_specific.extend(
            [
                "cas_or_sponsorship_reference_if_applicable",
                "proof_of_funds",
            ]
        )

    if country == "australia":
        country_specific.extend(
            [
                "coe_or_offer_letter_if_applicable",
                "genuine_student_or_genuine_temporary_entrant_documents",
                "proof_of_funds",
            ]
        )

    if intent == LeadIntent.study_abroad.value:
        return _dedupe(base + study + country_specific)

    if intent == LeadIntent.visa.value:
        return _dedupe(base + visa + country_specific)

    if intent == LeadIntent.overseas_job.value:
        return _dedupe(base + job + country_specific)

    if intent == LeadIntent.document.value:
        return _dedupe(base + document_only)

    return _dedupe(base + document_only)


@router.post("/api/v1/documents/checklist/generate/{lead_id}")
def generate_document_checklist(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    required_document_types = _document_checklist_for_lead(lead)
    created = []
    existing = []

    for document_type in required_document_types:
        record = session.exec(
            select(DocumentRecord)
            .where(DocumentRecord.lead_id == lead_id)
            .where(DocumentRecord.document_type == document_type)
        ).first()

        if record:
            existing.append(record)
            continue

        new_record = DocumentRecord(
            lead_id=lead_id,
            document_type=document_type,
            filename=f"PENDING_REQUIRED_{document_type}.txt",
            storage_key=None,
            status="missing",
            extracted_metadata_json=json.dumps(
                {
                    "generated_by": "document_engine_v1",
                    "requirement_type": "checklist_item",
                    "lead_intent": _intent_value(lead),
                    "target_country": lead.target_country,
                }
            ),
        )

        session.add(new_record)
        created.append(new_record)

    session.commit()

    for record in created:
        session.refresh(record)

    return jsonable_encoder(
        {
            "status": "generated",
            "lead_id": lead_id,
            "created_count": len(created),
            "existing_count": len(existing),
            "required_document_types": required_document_types,
            "created": created,
            "existing": existing,
        }
    )


@router.get("/api/v1/leads/{lead_id}/documents")
def list_lead_documents(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    documents = session.exec(
        select(DocumentRecord)
        .where(DocumentRecord.lead_id == lead_id)
        .order_by(DocumentRecord.created_at.desc())
    ).all()

    missing = [doc for doc in documents if doc.status == "missing"]
    received = [doc for doc in documents if doc.status == "received"]
    needs_review = [doc for doc in documents if doc.status == "needs_review"]
    verified = [doc for doc in documents if doc.status == "verified"]

    return jsonable_encoder(
        {
            "lead": lead,
            "documents": documents,
            "summary": {
                "total": len(documents),
                "missing": len(missing),
                "received": len(received),
                "needs_review": len(needs_review),
                "verified": len(verified),
            },
        }
    )


@router.post("/api/v1/leads/{lead_id}/documents")
def create_document_record(
    lead_id: UUID,
    payload: DocumentCreateRequest,
    session: Session = Depends(get_session),
) -> dict:
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    record = DocumentRecord(
        lead_id=lead_id,
        document_type=payload.document_type,
        filename=payload.filename,
        storage_key=payload.storage_key,
        status=payload.status,
        extracted_metadata_json=json.dumps(
            {
                "created_by": "document_engine_v1",
                "notes": payload.notes,
            }
        ),
    )

    session.add(record)
    session.commit()
    session.refresh(record)

    return jsonable_encoder(
        {
            "status": "created",
            "document": record,
        }
    )


@router.patch("/api/v1/documents/{document_id}/status")
def update_document_status(
    document_id: UUID,
    payload: DocumentStatusUpdate,
    session: Session = Depends(get_session),
) -> dict:
    document = session.get(DocumentRecord, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = payload.status

    if payload.filename:
        document.filename = payload.filename

    if payload.storage_key:
        document.storage_key = payload.storage_key

    existing_metadata = {}

    if document.extracted_metadata_json:
        try:
            existing_metadata = json.loads(document.extracted_metadata_json)
        except Exception:
            existing_metadata = {}

    existing_metadata["last_status_update"] = {
        "status": payload.status,
        "notes": payload.notes,
    }

    document.extracted_metadata_json = json.dumps(existing_metadata)

    session.add(document)
    session.commit()
    session.refresh(document)

    return jsonable_encoder(
        {
            "status": "updated",
            "document": document,
        }
    )


@router.get("/api/v1/documents/verification-queue")
def document_verification_queue(
    session: Session = Depends(get_session),
) -> dict:
    documents = session.exec(
        select(DocumentRecord)
        .where(DocumentRecord.status.in_(["received", "needs_review"]))
        .order_by(DocumentRecord.created_at.desc())
        .limit(100)
    ).all()

    return jsonable_encoder(
        {
            "count": len(documents),
            "documents": documents,
        }
    )


DOCUMENT_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Lead Documents - Global Mobility AIOS</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      padding: 30px;
    }
    a {
      color: #38bdf8;
      text-decoration: none;
    }
    h1 {
      margin-bottom: 5px;
    }
    h2 {
      margin-top: 32px;
    }
    .muted {
      color: #94a3b8;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 15px;
      margin-top: 25px;
    }
    .card {
      background: #111827;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 18px;
    }
    .label {
      color: #94a3b8;
      font-size: 13px;
    }
    .value {
      font-size: 30px;
      font-weight: bold;
      margin-top: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      background: #111827;
    }
    th, td {
      padding: 10px;
      border-bottom: 1px solid #374151;
      text-align: left;
      font-size: 13px;
      vertical-align: top;
    }
    th {
      color: #94a3b8;
    }
    .pill {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #1f2937;
      border: 1px solid #374151;
      white-space: nowrap;
    }
    button {
      padding: 8px 12px;
      border-radius: 8px;
      border: none;
      background: #38bdf8;
      color: #082f49;
      font-weight: bold;
      cursor: pointer;
      margin: 3px;
    }
    button.ok {
      background: #34d399;
      color: #052e16;
    }
    button.danger {
      background: #fb7185;
      color: #450a0a;
    }
    button.warning {
      background: #fbbf24;
      color: #451a03;
    }
    input, select, textarea {
      width: 100%;
      padding: 10px;
      margin-top: 6px;
      margin-bottom: 10px;
      border-radius: 8px;
      border: 1px solid #374151;
      background: #020617;
      color: #e5e7eb;
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      background: #111827;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 18px;
      margin-top: 18px;
    }
    .full {
      grid-column: 1 / -1;
    }
    .message {
      margin-top: 15px;
      padding: 12px;
      border-radius: 10px;
      background: #111827;
      border: 1px solid #374151;
    }
    .success {
      border-color: #34d399;
      color: #bbf7d0;
    }
    .error {
      border-color: #fb7185;
      color: #fecdd3;
    }
    pre {
      background: #020617;
      border: 1px solid #334155;
      padding: 14px;
      border-radius: 10px;
      overflow-x: auto;
      max-height: 420px;
    }
  </style>
</head>
<body>
  <a href="/admin">← Back to Admin Dashboard</a>
  |
  <a href="/admin/leads/__LEAD_ID__">Lead Detail</a>

  <h1>Lead Documents</h1>
  <div class="muted">Lead ID: <code>__LEAD_ID__</code></div>

  <button onclick="loadDocuments()">Refresh</button>
  <button class="ok" onclick="generateChecklist()">Generate Checklist</button>

  <div id="message"></div>
  <div class="cards" id="cards"></div>

  <h2>Add / Upload Document Metadata</h2>
  <div class="form-grid">
    <div>
      <label>Document Type</label>
      <input id="docType" value="passport">
    </div>
    <div>
      <label>Filename</label>
      <input id="docFilename" value="passport_scan.pdf">
    </div>
    <div>
      <label>Storage Key</label>
      <input id="docStorageKey" value="">
    </div>
    <div>
      <label>Status</label>
      <select id="docStatus">
        <option value="received">received</option>
        <option value="needs_review">needs_review</option>
        <option value="verified">verified</option>
        <option value="missing">missing</option>
        <option value="rejected">rejected</option>
      </select>
    </div>
    <div class="full">
      <label>Notes</label>
      <textarea id="docNotes">Uploaded from document console.</textarea>
    </div>
    <div class="full">
      <button class="ok" onclick="createDocument()">Create Document Record</button>
    </div>
  </div>

  <h2>Document Checklist</h2>
  <table>
    <thead>
      <tr>
        <th>Document Type</th>
        <th>Filename</th>
        <th>Status</th>
        <th>Storage Key</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="documents"></tbody>
  </table>

  <h2>Raw Document JSON</h2>
  <pre id="raw"></pre>

<script>
const leadId = "__LEAD_ID__";

function esc(v) {
  if (v === null || v === undefined) return "";
  return String(v).replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[c]));
}

function pill(v) {
  return `<span class="pill">${esc(v)}</span>`;
}

function showMessage(text, type = "success") {
  document.getElementById("message").innerHTML =
    `<div class="message ${type}">${esc(text)}</div>`;
}

async function apiPost(url, body = {}) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return text ? JSON.parse(text) : {};
}

async function apiPatch(url, body = {}) {
  const res = await fetch(url, {
    method: "PATCH",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return text ? JSON.parse(text) : {};
}

async function generateChecklist() {
  try {
    const result = await apiPost(`/api/v1/documents/checklist/generate/${leadId}`);
    showMessage(`Checklist generated. Created: ${result.created_count}. Existing: ${result.existing_count}.`);
    await loadDocuments();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function createDocument() {
  try {
    const payload = {
      document_type: document.getElementById("docType").value,
      filename: document.getElementById("docFilename").value,
      storage_key: document.getElementById("docStorageKey").value || null,
      status: document.getElementById("docStatus").value,
      notes: document.getElementById("docNotes").value
    };

    const result = await apiPost(`/api/v1/leads/${leadId}/documents`, payload);
    showMessage(`Document record created: ${result.document.id}`);
    await loadDocuments();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function updateDocumentStatus(id, status) {
  try {
    await apiPatch(`/api/v1/documents/${id}/status`, {
      status: status,
      notes: `Marked ${status} from Document Engine v1.`
    });

    showMessage(`Document marked ${status}.`);
    await loadDocuments();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function loadDocuments() {
  const res = await fetch(`/api/v1/leads/${leadId}/documents`);

  if (!res.ok) {
    document.getElementById("raw").textContent = "Documents API failed: " + res.status;
    return;
  }

  const data = await res.json();

  document.getElementById("raw").textContent = JSON.stringify(data, null, 2);

  const summary = data.summary || {};

  document.getElementById("cards").innerHTML = Object.entries(summary).map(([k, v]) => `
    <div class="card">
      <div class="label">${esc(k)}</div>
      <div class="value">${esc(v)}</div>
    </div>
  `).join("");

  document.getElementById("documents").innerHTML = (data.documents || []).map(r => `
    <tr>
      <td>${esc(r.document_type)}</td>
      <td>${esc(r.filename)}</td>
      <td>${pill(r.status)}</td>
      <td>${esc(r.storage_key)}</td>
      <td>${esc(r.created_at)}</td>
      <td>
        <button class="warning" onclick="updateDocumentStatus('${r.id}', 'needs_review')">Needs Review</button>
        <button class="ok" onclick="updateDocumentStatus('${r.id}', 'verified')">Verify</button>
        <button class="danger" onclick="updateDocumentStatus('${r.id}', 'rejected')">Reject</button>
        <button onclick="updateDocumentStatus('${r.id}', 'received')">Received</button>
      </td>
    </tr>
  `).join("");
}

loadDocuments();
</script>
</body>
</html>
"""


@router.get("/admin/leads/{lead_id}/documents", response_class=HTMLResponse)
def lead_documents_page(lead_id: UUID) -> str:
    return DOCUMENT_PAGE.replace("__LEAD_ID__", str(lead_id))


@router.get("/debug/document-engine")
def debug_document_engine() -> list[str]:
    return ["Document Engine v1 router is loaded"]
