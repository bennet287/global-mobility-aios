from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.models.runtime_economics import ProviderCallAllocation
from app.services.runtime_economics import (
    PROVIDER_BREAKER_FAILURE_THRESHOLD,
    RuntimeEconomicsError,
    authorize_provider_calls,
    reset_provider_circuit,
    summarize_cost_evidence,
)


router = APIRouter(prefix="/api/v1/runtime-economics", tags=["runtime-economics"])


class ProviderCallCapacityRequest(BaseModel):
    authorized_calls: int = Field(ge=0, le=1_000_000)
    paused: bool = False
    reason: str = Field(min_length=1, max_length=1000)


class ProviderCircuitResetRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


def _admin_actor(request: Request) -> str:
    auth = getattr(request.state, "auth", None)
    if str(getattr(auth, "role", "read_only")) != "admin":
        raise HTTPException(status_code=403, detail="Provider call allocation requires the admin role")
    return str(getattr(auth, "username", "api-operator"))


def _view(allocation: ProviderCallAllocation) -> dict:
    return {
        "provider": allocation.provider,
        "authorized_calls": allocation.authorized_calls,
        "used_calls": allocation.used_calls,
        "remaining_calls": allocation.authorized_calls - allocation.used_calls,
        "paused": allocation.paused,
        "breaker_open": allocation.breaker_open,
        "breaker_failures": allocation.breaker_failures,
        "breaker_opened_at": allocation.breaker_opened_at,
        "breaker_failure_threshold": PROVIDER_BREAKER_FAILURE_THRESHOLD,
        "breaker_scope": "admin_enrolled_provider_only",
        "authorized_by": allocation.authorized_by,
        "reason": allocation.reason,
        "updated_at": allocation.updated_at,
        "cost_basis": "call_count_not_money",
    }


@router.get("/cost-evidence")
def get_runtime_cost_evidence(
    request: Request, session: Session = Depends(get_session),
) -> dict:
    _admin_actor(request)
    return summarize_cost_evidence(session)


@router.put("/providers/{provider}/capacity")
def set_provider_call_capacity(
    provider: str, payload: ProviderCallCapacityRequest, request: Request,
    session: Session = Depends(get_session),
) -> dict:
    actor = _admin_actor(request)
    if not payload.reason.strip():
        raise HTTPException(status_code=422, detail="Reason is required")
    try:
        allocation = authorize_provider_calls(
            session, provider=provider, authorized_calls=payload.authorized_calls,
            paused=payload.paused, actor=actor, reason=payload.reason.strip(),
        )
    except RuntimeEconomicsError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _view(allocation)


@router.get("/providers/{provider}/capacity")
def get_provider_call_capacity(
    provider: str, request: Request, session: Session = Depends(get_session),
) -> dict:
    _admin_actor(request)
    allocation = session.get(ProviderCallAllocation, provider)
    if allocation is None:
        raise HTTPException(status_code=404, detail="Provider call capacity has not been authorized")
    return _view(allocation)


@router.post("/providers/{provider}/circuit/reset")
def reset_provider_circuit_endpoint(
    provider: str, payload: ProviderCircuitResetRequest, request: Request,
    session: Session = Depends(get_session),
) -> dict:
    actor = _admin_actor(request)
    if not payload.reason.strip():
        raise HTTPException(status_code=422, detail="Reason is required")
    try:
        allocation = reset_provider_circuit(
            session, provider=provider, actor=actor, reason=payload.reason.strip(),
        )
    except RuntimeEconomicsError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _view(allocation)
