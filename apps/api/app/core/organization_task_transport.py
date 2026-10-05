"""Bounded transport observations; UUID correlation is not proof of scheduler origin."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from uuid import UUID

SCAN_TASK_NAME = "app.tasks.organization_tasks.scan_organization_work"
logger = logging.getLogger(__name__)


def uuid_text(value) -> str | None:
    if isinstance(value, UUID):
        return str(value)
    if type(value) is not str or len(value) != 36:
        return None
    try:
        return str(UUID(value))
    except ValueError:
        return None


@dataclass(frozen=True)
class OrganizationTaskTransport:
    task_id: str | None = None
    parent_id: str | None = None
    root_id: str | None = None

    def audit_state(self) -> dict:
        # Revalidate even internal callers; never serialize arbitrary caller objects.
        task_id = uuid_text(self.task_id)
        return {
            "task_id": task_id,
            "parent_id": uuid_text(self.parent_id) if task_id else None,
            "root_id": uuid_text(self.root_id) if task_id else None,
            "origin_independently_verified": False,
        }

    @classmethod
    def from_request(cls, request):
        if (
            getattr(request, "called_directly", True) is not False
            or getattr(request, "is_eager", True) is not False
        ):
            return cls()
        task_id = uuid_text(getattr(request, "id", None))
        return cls(
            task_id,
            uuid_text(getattr(request, "parent_id", None)) if task_id else None,
            uuid_text(getattr(request, "root_id", None)) if task_id else None,
        )


def observe_scan_publication(*, sender=None, headers=None, **ignored):
    """Only connected in scheduler-only mode; never consumes message body or secrets."""
    if sender != SCAN_TASK_NAME or type(headers) is not dict:
        return
    task_id = uuid_text(headers.get("id"))
    if task_id is None:
        return
    observation = {
        "task": SCAN_TASK_NAME,
        "task_id": task_id,
        "parent_id": uuid_text(headers.get("parent_id")),
        "root_id": uuid_text(headers.get("root_id")),
        "observation": "after_task_publish",
        "scheduler_only_configuration": True,
        "origin_independently_verified": False,
        "delivery_verified": False,
    }
    logger.info("organization_scan_publication %s", json.dumps(observation, sort_keys=True))


def log_scan_dispatch(observation: dict) -> None:
    # This observation is built only from bounded query IDs and validated UUIDs.
    logger.info("organization_scan_dispatch %s", json.dumps(observation, sort_keys=True))
