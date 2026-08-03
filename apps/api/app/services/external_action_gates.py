from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.models.domain import ApplicationRecord, AutomationDelivery, AutomationEvent


EXTERNAL_DELIVERY_CHANNELS = frozenset({"email", "messaging", "calendar", "webhook"})

ACTION_GATE_POLICIES: dict[str, dict[str, Any]] = {
    "client.external_send": {
        "authority_level": "L3",
        "executor": "reviewed_automation_delivery",
        "receipt": "automation_delivery_review",
        "requirements": [
            "human approval",
            "different reviewer",
            "dispatch audit",
        ],
    },
    "authority.submit": {
        "authority_level": "L3",
        "executor": "approved_application_submission",
        "receipt": "approved_application_state_and_audit",
        "requirements": [
            "explicit human application approval",
            "readiness guardrails",
            "submission audit",
        ],
    },
    "payment.initiate": {
        "authority_level": "L3",
        "executor": None,
        "receipt": None,
        "requirements": ["future Board-approved payment adapter"],
    },
    "contract.sign": {
        "authority_level": "L4",
        "executor": None,
        "receipt": None,
        "requirements": ["future Human Board signature adapter"],
    },
    "deployment.production": {
        "authority_level": "L3",
        "executor": None,
        "receipt": None,
        "requirements": ["future reviewed deployment adapter"],
    },
}


def action_gate_manifest() -> dict[str, dict[str, Any]]:
    return {
        action: {
            **policy,
            "executable": policy["executor"] is not None,
            "fail_closed": True,
        }
        for action, policy in ACTION_GATE_POLICIES.items()
    }


def assert_registered_executor(action: str) -> None:
    policy = ACTION_GATE_POLICIES.get(action)
    if policy is None:
        raise ValueError(f"Unknown governed action: {action}")
    if policy["executor"] is None:
        raise ValueError(f"{action} has no registered executor and remains blocked")


def assert_application_submission_authorized(application: ApplicationRecord) -> None:
    status = str(getattr(application.status, "value", application.status) or "").strip().lower()
    if status != "approved":
        raise ValueError("Authority submission requires an explicitly approved application")


def assert_agency_submission_tracking_authorized(application: ApplicationRecord) -> None:
    status = str(getattr(application.status, "value", application.status) or "").strip().lower()
    if status not in {"approved", "submitted"}:
        raise ValueError(
            "Agency submission tracking is blocked until the application is approved or submitted"
        )


def assert_delivery_dispatch_authorized(
    session: Session,
    delivery: AutomationDelivery,
) -> None:
    channel = delivery.channel.strip().lower()
    if channel not in EXTERNAL_DELIVERY_CHANNELS:
        return
    if not delivery.requires_human_approval:
        raise ValueError("External delivery cannot bypass human approval")
    if not delivery.reviewed_by or delivery.reviewed_at is None or not delivery.review_reason:
        raise ValueError("External delivery requires a complete human-review receipt")
    event = session.get(AutomationEvent, delivery.automation_event_id)
    if event is None:
        raise ValueError("Automation event not found")
    if event.created_by == delivery.reviewed_by:
        raise ValueError("External delivery requires a different reviewer")
