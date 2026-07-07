from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    AgentRun,
    FollowUp,
    HumanReview,
    Lead,
    Profile,
    SourceReference,
    TruthClaim,
    WorkflowRun,
)

router = APIRouter()


@router.get("/api/v1/leads/{lead_id}/detail")
def lead_detail_api(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profiles = session.exec(
        select(Profile).where(Profile.lead_id == lead_id)
    ).all()

    truth_claims = session.exec(
        select(TruthClaim)
        .where(TruthClaim.lead_id == lead_id)
        .order_by(TruthClaim.created_at.desc())
    ).all()

    truth_claim_ids = [claim.id for claim in truth_claims]

    source_references = []

    if truth_claim_ids:
        source_references = session.exec(
            select(SourceReference)
            .where(SourceReference.truth_claim_id.in_(truth_claim_ids))
            .order_by(SourceReference.retrieved_at.desc())
        ).all()

    reviews = session.exec(
        select(HumanReview)
        .where(HumanReview.lead_id == lead_id)
        .order_by(HumanReview.created_at.desc())
    ).all()

    follow_ups = session.exec(
        select(FollowUp)
        .where(FollowUp.lead_id == lead_id)
        .order_by(FollowUp.created_at.desc())
    ).all()

    workflow_runs = session.exec(
        select(WorkflowRun)
        .where(WorkflowRun.lead_id == lead_id)
        .order_by(WorkflowRun.started_at.desc())
    ).all()

    agent_runs = session.exec(
        select(AgentRun)
        .where(AgentRun.lead_id == lead_id)
        .order_by(AgentRun.created_at.desc())
    ).all()

    return jsonable_encoder(
        {
            "lead": lead,
            "profiles": profiles,
            "truth_claims": truth_claims,
            "source_references": source_references,
            "reviews": reviews,
            "follow_ups": follow_ups,
            "workflow_runs": workflow_runs,
            "agent_runs": agent_runs,
        }
    )


@router.get("/admin/leads/{lead_id}", response_class=HTMLResponse)
def lead_detail_page(lead_id: UUID) -> str:
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Lead Detail - Global Mobility AIOS</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      padding: 30px;
    }}
    a {{
      color: #38bdf8;
      text-decoration: none;
    }}
    h1 {{
      margin-bottom: 5px;
    }}
    h2 {{
      margin-top: 32px;
    }}
    .muted {{
      color: #94a3b8;
    }}
    .panel {{
      background: #111827;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 18px;
      margin-top: 18px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }}
    .label {{
      color: #94a3b8;
      font-size: 13px;
      margin-bottom: 5px;
    }}
    .value {{
      font-size: 16px;
      font-weight: bold;
      word-break: break-word;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      background: #111827;
    }}
    th, td {{
      padding: 10px;
      border-bottom: 1px solid #374151;
      text-align: left;
      font-size: 13px;
      vertical-align: top;
    }}
    th {{
      color: #94a3b8;
    }}
    .pill {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #1f2937;
      border: 1px solid #374151;
      white-space: nowrap;
    }}
    button {{
      padding: 8px 12px;
      border-radius: 8px;
      border: none;
      background: #38bdf8;
      color: #082f49;
      font-weight: bold;
      cursor: pointer;
      margin: 3px;
    }}
    button.ok {{
      background: #34d399;
      color: #052e16;
    }}
    button.danger {{
      background: #fb7185;
      color: #450a0a;
    }}
    button.warning {{
      background: #fbbf24;
      color: #451a03;
    }}
    pre {{
      background: #020617;
      border: 1px solid #334155;
      padding: 14px;
      border-radius: 10px;
      overflow-x: auto;
      max-height: 360px;
    }}
    .message {{
      margin-top: 15px;
      padding: 12px;
      border-radius: 10px;
      background: #111827;
      border: 1px solid #374151;
    }}
    .success {{
      border-color: #34d399;
      color: #bbf7d0;
    }}
    .error {{
      border-color: #fb7185;
      color: #fecdd3;
    }}
  </style>
</head>
<body>
  <a href="/admin">← Back to Admin Dashboard</a>

  <h1>Lead Detail</h1>
  <div class="muted">Lead ID: <code>{lead_id}</code></div>

  <button onclick="loadLead()">Refresh Lead Detail</button>
  <a href="/admin/leads/{lead_id}/documents"><button>Documents</button></a>
  <div id="message"></div>

  <div id="leadSummary"></div>

  <h2>Profiles</h2>
  <table>
    <thead>
      <tr>
        <th>Type</th>
        <th>Qualification</th>
        <th>Field</th>
        <th>Current Country</th>
        <th>Target Country</th>
        <th>Desired Role</th>
        <th>Budget EUR</th>
      </tr>
    </thead>
    <tbody id="profiles"></tbody>
  </table>

  <h2>Truth Claims</h2>
  <table>
    <thead>
      <tr>
        <th>Claim</th>
        <th>Domain</th>
        <th>Country</th>
        <th>Verdict</th>
        <th>Confidence</th>
        <th>Explanation</th>
        <th>Evidence Actions</th>
      </tr>
    </thead>
    <tbody id="truthClaims"></tbody>
  </table>

  <h2>Source Evidence</h2>
  <table>
    <thead>
      <tr>
        <th>Truth Claim</th>
        <th>Source Type</th>
        <th>Country</th>
        <th>Title</th>
        <th>URL</th>
        <th>Retrieved</th>
      </tr>
    </thead>
    <tbody id="sources"></tbody>
  </table>

  <h2>Review History</h2>
  <table>
    <thead>
      <tr>
        <th>Reason</th>
        <th>Priority</th>
        <th>Status</th>
        <th>Reviewer Notes</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="reviews"></tbody>
  </table>

  <h2>Follow-up History</h2>
  <table>
    <thead>
      <tr>
        <th>Message</th>
        <th>Channel</th>
        <th>Status</th>
        <th>Due</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="followups"></tbody>
  </table>

  <h2>Workflow History</h2>
  <table>
    <thead>
      <tr>
        <th>Workflow</th>
        <th>Intent</th>
        <th>Route</th>
        <th>Status</th>
        <th>Output</th>
      </tr>
    </thead>
    <tbody id="workflows"></tbody>
  </table>

  <h2>Agent History</h2>
  <table>
    <thead>
      <tr>
        <th>Agent</th>
        <th>Task</th>
        <th>Status</th>
        <th>Output</th>
      </tr>
    </thead>
    <tbody id="agents"></tbody>
  </table>

  <h2>Raw Lead Detail JSON</h2>
  <pre id="raw"></pre>

<script>
const leadId = "{lead_id}";

function esc(v) {{
  if (v === null || v === undefined) return "";
  return String(v).replace(/[&<>"']/g, c => ({{
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }}[c]));
}}

function pill(v) {{
  return `<span class="pill">${{esc(v)}}</span>`;
}}

function shortId(v) {{
  if (!v) return "";
  return String(v).slice(0, 8);
}}

function shortJson(v) {{
  if (!v) return "";
  try {{
    const parsed = typeof v === "string" ? JSON.parse(v) : v;
    return `<pre>${{esc(JSON.stringify(parsed, null, 2))}}</pre>`;
  }} catch {{
    return `<pre>${{esc(v)}}</pre>`;
  }}
}}

function showMessage(text, type = "success") {{
  document.getElementById("message").innerHTML =
    `<div class="message ${{type}}">${{esc(text)}}</div>`;
}}

async function apiPost(url, body = {{}}) {{
  const res = await fetch(url, {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify(body)
  }});

  const text = await res.text();

  if (!res.ok) {{
    throw new Error(text || `Request failed: ${{res.status}}`);
  }}

  return text ? JSON.parse(text) : {{}};
}}

async function approveReview(id) {{
  try {{
    await apiPost(`/api/v1/operations/reviews/${{id}}/approve`, {{
      reviewer_notes: "Approved from Lead Detail view."
    }});
    showMessage("Review approved.");
    await loadLead();
  }} catch (err) {{
    showMessage(err.message || String(err), "error");
  }}
}}

async function rejectReview(id) {{
  try {{
    await apiPost(`/api/v1/operations/reviews/${{id}}/reject`, {{
      reviewer_notes: "Rejected from Lead Detail view."
    }});
    showMessage("Review rejected.");
    await loadLead();
  }} catch (err) {{
    showMessage(err.message || String(err), "error");
  }}
}}

async function resolveReview(id) {{
  try {{
    await apiPost(`/api/v1/operations/reviews/${{id}}/resolve`, {{
      reviewer_notes: "Resolved from Lead Detail view."
    }});
    showMessage("Review resolved.");
    await loadLead();
  }} catch (err) {{
    showMessage(err.message || String(err), "error");
  }}
}}

async function completeFollowUp(id) {{
  try {{
    await apiPost(`/api/v1/operations/follow-ups/${{id}}/complete`);
    showMessage("Follow-up completed.");
    await loadLead();
  }} catch (err) {{
    showMessage(err.message || String(err), "error");
  }}
}}

async function attachSources(claimId) {{
  try {{
    const result = await apiPost(`/api/v1/operations/truth-claims/${{claimId}}/attach-sources`);
    showMessage(`Official sources attached: ${{result.attached_count}}. Existing skipped: ${{result.skipped_existing_count || 0}}.`);
    await loadLead();
  }} catch (err) {{
    showMessage(err.message || String(err), "error");
  }}
}}

async function loadLead() {{
  const res = await fetch(`/api/v1/leads/${{leadId}}/detail`);

  if (!res.ok) {{
    document.getElementById("raw").textContent = "Lead detail API failed: " + res.status;
    return;
  }}

  const data = await res.json();
  document.getElementById("raw").textContent = JSON.stringify(data, null, 2);

  const lead = data.lead || {{}};

  document.getElementById("leadSummary").innerHTML = `
    <div class="panel grid">
      <div>
        <div class="label">Full Name</div>
        <div class="value">${{esc(lead.full_name)}}</div>
      </div>
      <div>
        <div class="label">Email</div>
        <div class="value">${{esc(lead.email)}}</div>
      </div>
      <div>
        <div class="label">Phone</div>
        <div class="value">${{esc(lead.phone)}}</div>
      </div>
      <div>
        <div class="label">Intent</div>
        <div class="value">${{pill(lead.intent)}}</div>
      </div>
      <div>
        <div class="label">Target Country</div>
        <div class="value">${{esc(lead.target_country)}}</div>
      </div>
      <div>
        <div class="label">Status</div>
        <div class="value">${{pill(lead.status)}}</div>
      </div>
      <div>
        <div class="label">Source</div>
        <div class="value">${{esc(lead.source)}}</div>
      </div>
      <div>
        <div class="label">Created</div>
        <div class="value">${{esc(lead.created_at)}}</div>
      </div>
    </div>
  `;

  document.getElementById("profiles").innerHTML = (data.profiles || []).map(r => `
    <tr>
      <td>${{esc(r.profile_type)}}</td>
      <td>${{esc(r.highest_qualification)}}</td>
      <td>${{esc(r.field_of_study)}}</td>
      <td>${{esc(r.current_country)}}</td>
      <td>${{esc(r.target_country)}}</td>
      <td>${{esc(r.desired_role)}}</td>
      <td>${{esc(r.budget_eur)}}</td>
    </tr>
  `).join("");

  document.getElementById("truthClaims").innerHTML = (data.truth_claims || []).map(r => `
    <tr>
      <td>${{esc(r.claim)}}</td>
      <td>${{esc(r.domain)}}</td>
      <td>${{esc(r.country)}}</td>
      <td>${{pill(r.verdict)}}</td>
      <td>${{esc(r.confidence)}}</td>
      <td>${{esc(r.explanation)}}</td>
      <td>
        <button class="ok" onclick="attachSources('${{r.id}}')">Attach Official Sources</button>
      </td>
    </tr>
  `).join("");

  document.getElementById("sources").innerHTML = (data.source_references || []).length
    ? data.source_references.map(r => `
      <tr>
        <td>${{esc(shortId(r.truth_claim_id))}}</td>
        <td>${{pill(r.source_type)}}</td>
        <td>${{esc(r.country)}}</td>
        <td>${{esc(r.title)}}</td>
        <td><a href="${{esc(r.source_url)}}" target="_blank">${{esc(r.source_url)}}</a></td>
        <td>${{esc(r.retrieved_at)}}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="6" class="muted">No official source references attached to this lead yet.</td></tr>`;

  document.getElementById("reviews").innerHTML = (data.reviews || []).map(r => `
    <tr>
      <td>${{esc(r.reason)}}</td>
      <td>${{pill(r.priority)}}</td>
      <td>${{pill(r.status)}}</td>
      <td>${{esc(r.reviewer_notes)}}</td>
      <td>
        <button class="ok" onclick="approveReview('${{r.id}}')">Approve</button>
        <button class="danger" onclick="rejectReview('${{r.id}}')">Reject</button>
        <button class="warning" onclick="resolveReview('${{r.id}}')">Resolve</button>
      </td>
    </tr>
  `).join("");

  document.getElementById("followups").innerHTML = (data.follow_ups || []).map(r => `
    <tr>
      <td>${{esc(r.message)}}</td>
      <td>${{esc(r.channel)}}</td>
      <td>${{pill(r.status)}}</td>
      <td>${{esc(r.due_at)}}</td>
      <td>
        <button class="ok" onclick="completeFollowUp('${{r.id}}')">Complete</button>
      </td>
    </tr>
  `).join("");

  document.getElementById("workflows").innerHTML = (data.workflow_runs || []).map(r => `
    <tr>
      <td>${{esc(r.workflow_name)}}</td>
      <td>${{pill(r.detected_intent)}}</td>
      <td>${{esc(r.route)}}</td>
      <td>${{pill(r.status)}}</td>
      <td>${{shortJson(r.output_json)}}</td>
    </tr>
  `).join("");

  document.getElementById("agents").innerHTML = (data.agent_runs || []).map(r => `
    <tr>
      <td>${{esc(r.agent_name)}}</td>
      <td>${{esc(r.task)}}</td>
      <td>${{pill(r.status)}}</td>
      <td>${{shortJson(r.output_json)}}</td>
    </tr>
  `).join("");
}}

loadLead();
</script>

<section style="background:white;border:1px solid #ddd;border-radius:12px;padding:16px;margin:16px 0;">
  <h2>Document Summary</h2>
  <p><a href="/admin/leads/{lead_id}/documents">Open Document Workspace</a></p>
  <iframe src="/admin/leads/{lead_id}/documents/summary-card" style="width:100%;height:520px;border:0;border-radius:12px;background:white;"></iframe>
</section>

</body>
</html>
"""


@router.get("/debug/detail-views")
def debug_detail_views() -> list[str]:
    return ["Lead detail router is loaded"]
