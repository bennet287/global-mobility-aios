from __future__ import annotations

from scripts.print_demo_runbook import build_demo_runbook


def test_demo_runbook_lists_core_operator_entrypoints() -> None:
    runbook = build_demo_runbook("http://localhost:9000")
    urls = {item["label"]: item["url"] for item in runbook["urls"]}

    assert urls["Health"] == "http://localhost:9000/health"
    assert urls["Admin v2"] == "http://localhost:9000/admin/v2"
    assert urls["Agent Console"] == "http://localhost:9000/admin/controlled-agents"
    assert urls["Agent Review Queue"] == "http://localhost:9000/admin/agent-output-reviews"
    assert urls["Client Communications"] == "http://localhost:9000/admin/client-communications"
    assert urls["Communication Drafts"] == "http://localhost:9000/admin/client-communications/drafts"
    assert urls["Audit Logs"] == "http://localhost:9000/admin/audit-logs"


def test_demo_runbook_flow_covers_agent_to_client_draft_path() -> None:
    runbook = build_demo_runbook()
    flow = " ".join(runbook["flow"])

    assert "Demo 3" in flow
    assert "client_drafting_agent" in flow
    assert "client communication draft" in flow
    assert "Audit Logs" in flow
    assert "export_demo_snapshot.py" in flow


def test_demo_runbook_keeps_safety_rules_explicit() -> None:
    runbook = build_demo_runbook()
    safety = " ".join(runbook["safety_rules"]).lower()

    assert "human review" in safety
    assert "no automatic email" in safety
    assert "whatsapp" in safety
    assert "application submission" in safety
