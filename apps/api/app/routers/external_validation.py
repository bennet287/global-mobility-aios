from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.db import get_session
from app.schemas import (
    ExternalValidationBoardAcceptance,
    ExternalValidationEvidenceCreate,
    ExternalValidationEvidenceRead,
    ExternalValidationFindingCreate,
    ExternalValidationFindingRead,
    ExternalValidationFindingTriage,
    ExternalValidationReviewCreate,
    ExternalValidationReviewRead,
    ExternalValidationRunCreate,
    ExternalValidationRunRead,
    ExternalValidationRunUpdate,
    ExternalValidationScenarioCreate,
    ExternalValidationScenarioRead,
)
from app.services.external_validation import (
    add_external_validation_evidence,
    board_accept_external_validation_finding,
    create_external_validation_finding,
    create_external_validation_run,
    create_external_validation_scenario,
    evaluate_external_validation_run,
    evidence_read,
    external_validation_run_read,
    get_external_validation_run,
    latest_external_validation_gate,
    list_external_validation_runs,
    list_external_validation_scenarios,
    review_read,
    scenario_read,
    seed_default_external_validation_scenario,
    submit_external_validation_review,
    triage_external_validation_finding,
    update_external_validation_run,
)


router = APIRouter(prefix="/api/v1/external-validation", tags=["external-validation-v13.10.2"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _bad_request(exc: ValueError) -> HTTPException:
    message = str(exc)
    missing = (
        "not found" in message.lower()
        or "missing" in message.lower() and "fixture" not in message.lower()
    )
    return HTTPException(status_code=404 if missing else 400, detail=message)


@router.post("/scenarios", response_model=ExternalValidationScenarioRead, status_code=201)
def api_create_external_validation_scenario(
    payload: ExternalValidationScenarioCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationScenarioRead:
    try:
        row = create_external_validation_scenario(session, payload, actor=_actor(request))
        return scenario_read(row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/scenarios/seed-defaults", response_model=ExternalValidationScenarioRead)
def api_seed_default_external_validation_scenario(
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationScenarioRead:
    try:
        row = seed_default_external_validation_scenario(session, actor=_actor(request))
        return scenario_read(row)
    except (ValueError, OSError, KeyError) as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scenarios", response_model=list[ExternalValidationScenarioRead])
def api_list_external_validation_scenarios(
    status: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[ExternalValidationScenarioRead]:
    return list_external_validation_scenarios(session, status=status, limit=limit)


@router.post("/runs", response_model=ExternalValidationRunRead, status_code=201)
def api_create_external_validation_run(
    payload: ExternalValidationRunCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationRunRead:
    try:
        row = create_external_validation_run(session, payload, actor=_actor(request))
        return external_validation_run_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.get("/runs", response_model=list[ExternalValidationRunRead])
def api_list_external_validation_runs(
    gate_status: str | None = None,
    scenario_id: UUID | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[ExternalValidationRunRead]:
    return list_external_validation_runs(
        session,
        gate_status=gate_status,
        scenario_id=scenario_id,
        limit=limit,
    )


@router.get("/runs/latest", response_model=ExternalValidationRunRead | None)
def api_latest_external_validation_run(
    session: Session = Depends(get_session),
) -> ExternalValidationRunRead | None:
    return latest_external_validation_gate(session)


@router.get("/runs/{run_id}", response_model=ExternalValidationRunRead)
def api_get_external_validation_run(
    run_id: UUID,
    session: Session = Depends(get_session),
) -> ExternalValidationRunRead:
    try:
        return get_external_validation_run(session, run_id)
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.patch("/runs/{run_id}", response_model=ExternalValidationRunRead)
def api_update_external_validation_run(
    run_id: UUID,
    payload: ExternalValidationRunUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationRunRead:
    try:
        row = update_external_validation_run(session, run_id, payload, actor=_actor(request))
        return external_validation_run_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/runs/{run_id}/reviews", response_model=ExternalValidationReviewRead, status_code=201)
def api_submit_external_validation_review(
    run_id: UUID,
    payload: ExternalValidationReviewCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationReviewRead:
    try:
        row = submit_external_validation_review(session, run_id, payload, actor=_actor(request))
        return review_read(row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/runs/{run_id}/findings", response_model=ExternalValidationFindingRead, status_code=201)
def api_create_external_validation_finding(
    run_id: UUID,
    payload: ExternalValidationFindingCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationFindingRead:
    try:
        row = create_external_validation_finding(session, run_id, payload, actor=_actor(request))
        return ExternalValidationFindingRead(**row.model_dump())
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/findings/{finding_id}/triage", response_model=ExternalValidationFindingRead)
def api_triage_external_validation_finding(
    finding_id: UUID,
    payload: ExternalValidationFindingTriage,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationFindingRead:
    try:
        row = triage_external_validation_finding(session, finding_id, payload, actor=_actor(request))
        return ExternalValidationFindingRead(**row.model_dump())
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/findings/{finding_id}/board-acceptance", response_model=ExternalValidationFindingRead)
def api_board_accept_external_validation_finding(
    finding_id: UUID,
    payload: ExternalValidationBoardAcceptance,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationFindingRead:
    try:
        row = board_accept_external_validation_finding(session, finding_id, payload, actor=_actor(request))
        return ExternalValidationFindingRead(**row.model_dump())
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/runs/{run_id}/evidence", response_model=ExternalValidationEvidenceRead, status_code=201)
def api_add_external_validation_evidence(
    run_id: UUID,
    payload: ExternalValidationEvidenceCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationEvidenceRead:
    try:
        row = add_external_validation_evidence(session, run_id, payload, actor=_actor(request))
        return evidence_read(row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.post("/runs/{run_id}/evaluate", response_model=ExternalValidationRunRead)
def api_evaluate_external_validation_run(
    run_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalValidationRunRead:
    try:
        row = evaluate_external_validation_run(session, run_id, actor=_actor(request))
        return external_validation_run_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
