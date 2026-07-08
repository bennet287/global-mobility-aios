from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.domain import AuditLog


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _json_safe(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def to_audit_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        data = obj
    elif hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = {key: value for key, value in vars(obj).items() if not key.startswith("_")}
    return {key: _json_safe(value) for key, value in data.items()}


def _json_dump(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(to_audit_dict(value) if not isinstance(value, list) else value, default=str, sort_keys=True)


def record_audit(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[Any] = None,
    before_state: Optional[Any] = None,
    after_state: Optional[Any] = None,
    reason: Optional[str] = None,
    actor: str = "system",
    source: str = "api",
    commit: bool = False,
) -> AuditLog:
    log = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(_json_safe(entity_id)) if entity_id is not None else None,
        before_state_json=_json_dump(before_state),
        after_state_json=_json_dump(after_state),
        reason=reason,
        source=source,
    )
    session.add(log)
    if commit:
        session.commit()
        session.refresh(log)
    return log
