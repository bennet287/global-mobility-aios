from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    AgentRun,
    FollowUp,
    HumanReview,
    Lead,
    Profile,
    TruthClaim,
    WorkflowRun,
)

router = APIRouter()


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


@router.get("/api/v1/dashboard/summary")
def dashboard_summary(session: Session = Depends(get_session)) -> dict:
    pending_reviews = session.exec(
        select(HumanReview)
        .where(HumanReview.status == "pending")
        .order_by(HumanReview.created_at.desc())
        .limit(10)
    ).all()

    pending_follow_ups = session.exec(
        select(FollowUp)
        .where(FollowUp.status == "pending")
        .order_by(FollowUp.created_at.desc())
        .limit(10)
    ).all()

    data = {
        "counts": {
            "leads": _count(session, Lead),
            "profiles": _count(session, Profile),
            "truth_claims": _count(session, TruthClaim),
            "human_reviews": _count(session, HumanReview),
            "pending_human_reviews": len(pending_reviews),
            "follow_ups": _count(session, FollowUp),
            "pending_follow_ups": len(pending_follow_ups),
            "workflow_runs": _count(session, WorkflowRun),
            "agent_runs": _count(session, AgentRun),
        },
        "recent": {
            "leads": session.exec(
                select(Lead).order_by(Lead.created_at.desc()).limit(10)
            ).all(),
            "profiles": session.exec(
                select(Profile).order_by(Profile.created_at.desc()).limit(10)
            ).all(),
            "truth_claims": session.exec(
                select(TruthClaim).order_by(TruthClaim.created_at.desc()).limit(10)
            ).all(),
            "pending_reviews": pending_reviews,
            "pending_follow_ups": pending_follow_ups,
            "workflow_runs": session.exec(
                select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(10)
            ).all(),
            "agent_runs": session.exec(
                select(AgentRun).order_by(AgentRun.created_at.desc()).limit(10)
            ).all(),
        },
    }

    return jsonable_encoder(data)


@router.get("/debug/routes")
def debug_routes() -> list[str]:
    return ["Dashboard router is loaded"]


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard() -> str:
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Global Mobility AIOS Admin</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      padding: 30px;
    }
    h1 { margin-bottom: 5px; }
    h2 { margin-top: 32px; }
    .muted { color: #94a3b8; }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
    th { color: #94a3b8; }
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
    button.danger {
      background: #fb7185;
      color: #450a0a;
    }
    button.ok {
      background: #34d399;
      color: #052e16;
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
    textarea {
      min-height: 70px;
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
    pre {
      background: #020617;
      border: 1px solid #334155;
      padding: 14px;
      border-radius: 10px;
      overflow-x: auto;
      margin-top: 20px;
      max-height: 420px;
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
  </style>
</head>
<body>
  <h1>Global Mobility AIOS Admin</h1>
  <div class="muted">Admin Dashboard v1.1 — operational actions for MVP-1.</div>

  <button onclick="loadDashboard()">Refresh Dashboard</button>
  <div id="message"></div>

  <div class="cards" id="cards"></div>

  <h2>Create New Lead</h2>
  <div class="form-grid">
    <div>
      <label>Full Name</label>
      <input id="leadName" value="New Test Lead">
    </div>
    <div>
      <label>Email</label>
      <input id="leadEmail" value="newlead@example.com">
    </div>
    <div>
      <label>Intent</label>
      <select id="leadIntent">
        <option value="visa">Visa</option>
        <option value="study_abroad">Study Abroad</option>
        <option value="overseas_job">Overseas Job</option>
        <option value="document">Document</option>
        <option value="unknown">Unknown</option>
      </select>
    </div>
    <div>
      <label>Target Country</label>
      <input id="leadCountry" value="Germany">
    </div>
    <div class="full">
      <label>Claim / Requirement</label>
      <textarea id="leadClaim">Germany student visa is guaranteed without financial proof</textarea>
    </div>
    <div class="full">
      <button class="ok" onclick="createLead()">Create Lead + Run Workflow</button>
    </div>
  </div>

  <h2>Recent Leads</h2>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Intent</th>
        <th>Country</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="leads"></tbody>
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
      </tr>
    </thead>
    <tbody id="claims"></tbody>
  </table>

  <h2>Pending Reviews</h2>
  <table>
    <thead>
      <tr>
        <th>Reason</th>
        <th>Priority</th>
        <th>Status</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="reviews"></tbody>
  </table>

  <h2>Pending Follow-ups</h2>
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

  <h2>Workflow Runs</h2>
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

  <h2>Agent Runs</h2>
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

  <h2>Raw Dashboard JSON</h2>
  <pre id="raw"></pre>

<script>
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

function shortJson(v) {
  if (!v) return "";
  try {
    const parsed = typeof v === "string" ? JSON.parse(v) : v;
    return `<pre>${esc(JSON.stringify(parsed, null, 2))}</pre>`;
  } catch {
    return `<pre>${esc(v)}</pre>`;
  }
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

async function createLead() {
  try {
    const payload = {
      full_name: document.getElementById("leadName").value,
      email: document.getElementById("leadEmail").value,
      intent: document.getElementById("leadIntent").value,
      target_country: document.getElementById("leadCountry").value,
      claim: document.getElementById("leadClaim").value,
      source: "admin_dashboard"
    };

    const result = await apiPost("/api/v1/workflows/lead-intake", payload);
    showMessage("Lead created and workflow executed: " + result.workflow_run_id);
    await loadDashboard();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function approveReview(id) {
  try {
    await apiPost(`/api/v1/operations/reviews/${id}/approve`, {
      reviewer_notes: "Approved from Admin Dashboard v1.1"
    });
    showMessage("Review approved.");
    await loadDashboard();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function rejectReview(id) {
  try {
    await apiPost(`/api/v1/operations/reviews/${id}/reject`, {
      reviewer_notes: "Rejected from Admin Dashboard v1.1"
    });
    showMessage("Review rejected.");
    await loadDashboard();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function resolveReview(id) {
  try {
    await apiPost(`/api/v1/operations/reviews/${id}/resolve`, {
      reviewer_notes: "Resolved from Admin Dashboard v1.1"
    });
    showMessage("Review resolved.");
    await loadDashboard();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function completeFollowUp(id) {
  try {
    await apiPost(`/api/v1/operations/follow-ups/${id}/complete`);
    showMessage("Follow-up completed.");
    await loadDashboard();
  } catch (err) {
    showMessage(err.message || String(err), "error");
  }
}

async function loadDashboard() {
  const res = await fetch("/api/v1/dashboard/summary");

  if (!res.ok) {
    document.getElementById("raw").textContent = "Dashboard API failed: " + res.status;
    return;
  }

  const data = await res.json();
  document.getElementById("raw").textContent = JSON.stringify(data, null, 2);

  const counts = data.counts || {};
  document.getElementById("cards").innerHTML = Object.entries(counts).map(([k, v]) => `
    <div class="card">
      <div class="label">${esc(k)}</div>
      <div class="value">${esc(v)}</div>
    </div>
  `).join("");

  document.getElementById("leads").innerHTML = (data.recent.leads || []).map(r => `
    <tr>
      <td><a href="/admin/leads/${r.id}">${esc(r.full_name)}</a></td>
      <td>${esc(r.email)}</td>
      <td>${pill(r.intent)}</td>
      <td>${esc(r.target_country)}</td>
      <td>${pill(r.status)}</td>
    </tr>
  `).join("");

  document.getElementById("claims").innerHTML = (data.recent.truth_claims || []).map(r => `
    <tr>
      <td>${esc(r.claim)}</td>
      <td>${esc(r.domain)}</td>
      <td>${esc(r.country)}</td>
      <td>${pill(r.verdict)}</td>
      <td>${esc(r.confidence)}</td>
      <td>${esc(r.explanation)}</td>
    </tr>
  `).join("");

  document.getElementById("reviews").innerHTML = (data.recent.pending_reviews || []).map(r => `
    <tr>
      <td>${esc(r.reason)}</td>
      <td>${pill(r.priority)}</td>
      <td>${pill(r.status)}</td>
      <td>${esc(r.created_at)}</td>
      <td>
        <button class="ok" onclick="approveReview('${r.id}')">Approve</button>
        <button class="danger" onclick="rejectReview('${r.id}')">Reject</button>
        <button class="warning" onclick="resolveReview('${r.id}')">Resolve</button>
      </td>
    </tr>
  `).join("");

  document.getElementById("followups").innerHTML = (data.recent.pending_follow_ups || []).map(r => `
    <tr>
      <td>${esc(r.message)}</td>
      <td>${esc(r.channel)}</td>
      <td>${pill(r.status)}</td>
      <td>${esc(r.due_at)}</td>
      <td>
        <button class="ok" onclick="completeFollowUp('${r.id}')">Complete</button>
      </td>
    </tr>
  `).join("");

  document.getElementById("workflows").innerHTML = (data.recent.workflow_runs || []).map(r => `
    <tr>
      <td>${esc(r.workflow_name)}</td>
      <td>${pill(r.detected_intent)}</td>
      <td>${esc(r.route)}</td>
      <td>${pill(r.status)}</td>
      <td>${shortJson(r.output_json)}</td>
    </tr>
  `).join("");

  document.getElementById("agents").innerHTML = (data.recent.agent_runs || []).map(r => `
    <tr>
      <td>${esc(r.agent_name)}</td>
      <td>${esc(r.task)}</td>
      <td>${pill(r.status)}</td>
      <td>${shortJson(r.output_json)}</td>
    </tr>
  `).join("");
}

loadDashboard();
</script>
</body>
</html>
"""
