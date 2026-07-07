
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
      margin-top: 25px;
      background: #111827;
    }
    th, td {
      padding: 10px;
      border-bottom: 1px solid #374151;
      text-align: left;
      font-size: 13px;
    }
    th { color: #94a3b8; }
    .pill {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #1f2937;
      border: 1px solid #374151;
    }
    button {
      padding: 10px 14px;
      border-radius: 8px;
      border: none;
      background: #38bdf8;
      color: #082f49;
      font-weight: bold;
      cursor: pointer;
      margin-top: 20px;
    }
    pre {
      background: #020617;
      border: 1px solid #334155;
      padding: 14px;
      border-radius: 10px;
      overflow-x: auto;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <h1>Global Mobility AIOS Admin</h1>
  <div class="muted">MVP-1 dashboard for leads, truth checks, reviews, workflows, and agent activity.</div>

  <button onclick="loadDashboard()">Refresh</button>

  <div class="cards" id="cards"></div>

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
      </tr>
    </thead>
    <tbody id="reviews"></tbody>
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
      <td>${esc(r.full_name)}</td>
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
    </tr>
  `).join("");

  document.getElementById("reviews").innerHTML = (data.recent.pending_reviews || []).map(r => `
    <tr>
      <td>${esc(r.reason)}</td>
      <td>${pill(r.priority)}</td>
      <td>${pill(r.status)}</td>
      <td>${esc(r.created_at)}</td>
    </tr>
  `).join("");
}

loadDashboard();
</script>
</body>
</html>
"""
