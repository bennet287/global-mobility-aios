from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable, TypeVar
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select

from app.core.db import get_session
from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActorType,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationContribution,
    OrganizationDependencyStatus,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationHumanActionRequestStatus,
    OrganizationRecordReference,
    OrganizationWorkItemDependency,
    OrganizationalWorkItem,
)
from app.schemas_organization_records import (
    ActivityCreate,
    ActivityRead,
    BlockerCreate,
    BlockerRead,
    BlockerSupersedeCreate,
    ContributionCorrectionCreate,
    ContributionCreate,
    ContributionRead,
    DecisionCreate,
    DecisionOutcome,
    DecisionRead,
    DecisionSupersede,
    DependencyCreate,
    DependencyRead,
    DependencySatisfyCommand,
    HumanActionComplete,
    HumanActionCompletionRead,
    HumanActionCreate,
    HumanActionRead,
    HumanActionRequestAssign,
    HumanActionRequestCreate,
    HumanActionRequestRead,
    OrganizationPage,
    ReasonCommand,
    ReferenceCreate,
    ReferenceRead,
    WorkAssignCommand,
    WorkItemCreate,
    WorkItemRead,
)
from app.services.organization_activity import append_activity
from app.services.organization_command import (
    AuthorityDenied,
    ContributionSourceRejected,
    DependencyConflict,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    NotFound,
    OrganizationCommandContext,
    OrganizationCommandError,
    TenantMismatch,
)
from app.services.organization_contribution import (
    append_contribution_correction,
    create_contribution,
    validate_authoritative_outcome,
)
from app.services.organization_decision import (
    create_executive_decision,
    record_executive_decision_outcome,
    supersede_executive_decision,
)
from app.services.organization_human_action import (
    acknowledge_human_action_request,
    append_human_action,
    assign_human_action_request,
    cancel_human_action_request,
    complete_human_action_request,
    create_human_action_request,
    decline_human_action_request,
    expire_human_action_request,
    start_human_action_request,
)
from app.services.organization_reference import create_record_reference
from app.services.organization_work import (
    assign_work_item,
    await_human_for_work_item,
    block_work_item,
    cancel_work_item,
    complete_work_item,
    create_dependency,
    create_work_item,
    mitigate_blocker,
    open_blocker,
    resolve_blocker,
    satisfy_dependency,
    start_work_item,
    supersede_dependency,
    waive_blocker,
    waive_dependency,
)


router = APIRouter(
    prefix="/api/v1/organization",
    tags=["organization-records-v13.16.1c"],
    responses={
        401: {"description": "Authentication required."},
        403: {"description": "Organization action is not permitted."},
        404: {"description": "Organization resource not found."},
        409: {"description": "Organization command conflicts with current state."},
        422: {"description": "Request or organization reference is invalid."},
    },
)

DEFAULT_TENANT = "default"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# The current application auth contract authenticates human users and has no tenant,
# agent-identity, or position claims. Keep its local tenant explicit and map its
# existing roles conservatively; future identity claims must replace this mapping,
# never request-body fields.
_ROLE_CONTEXT: dict[str, tuple[str, str, str]] = {
    "admin": ("executive", "board", "L4"),
    "operator": ("operations", "organization_operator", "L2"),
    "reviewer": ("compliance", "reviewer", "L1"),
    "sales": ("sales", "sales_operator", "L1"),
    "read_only": ("organization", "reader", "L0"),
}


def organization_command_context(request: Request) -> OrganizationCommandContext:
    auth = getattr(request.state, "auth", None)
    username = str(getattr(auth, "username", "")).strip()
    role = str(getattr(auth, "role", "")).strip()
    if not username or role not in _ROLE_CONTEXT:
        raise HTTPException(status_code=401, detail="Authentication required.")
    department, position_key, authority_level = _ROLE_CONTEXT[role]
    return OrganizationCommandContext(
        tenant_key=DEFAULT_TENANT,
        actor_id=username,
        actor_type=OrganizationActorType.human,
        authenticated_user_id=username,
        role=role,
        department=department,
        position_key=position_key,
        authority_level=authority_level,
        request_id=str(uuid4()),
    )


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Organization resource not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(exc, IdempotencyConflict):
        return HTTPException(status_code=409, detail="Idempotency key conflicts with an existing command.")
    if isinstance(exc, InvalidTransition):
        return HTTPException(status_code=409, detail="Organization resource cannot perform that transition.")
    if isinstance(exc, DependencyConflict):
        return HTTPException(status_code=409, detail="Organization dependency command conflicts with current state.")
    if isinstance(exc, ContributionSourceRejected):
        return HTTPException(status_code=422, detail="Contribution source is not authorized.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Organization reference is invalid.")
    return HTTPException(status_code=400, detail="Organization command was rejected.")


ResultT = TypeVar("ResultT")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


ModelT = TypeVar("ModelT", bound=SQLModel)


def _tenant_detail(session: Session, model: type[ModelT], record_id: UUID, tenant_key: str) -> ModelT:
    row = session.exec(
        select(model).where(model.id == record_id, model.tenant_key == tenant_key)  # type: ignore[attr-defined]
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Organization resource not found.")
    return row


def _page_result(rows: list[Any], *, page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "data": rows,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


@router.get("/activities", response_model=OrganizationPage[ActivityRead])
def list_activities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    work_item_id: UUID | None = None,
    activity_class: OrganizationActivityClass | None = None,
    activity_type: str | None = None,
    correlation_key: str | None = None,
    actor_id: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationActivity.tenant_key == context.tenant_key]
    for value, column in (
        (work_item_id, OrganizationActivity.work_item_id),
        (activity_class, OrganizationActivity.activity_class),
        (activity_type, OrganizationActivity.activity_type),
        (correlation_key, OrganizationActivity.correlation_key),
        (actor_id, OrganizationActivity.actor_id),
    ):
        if value is not None:
            conditions.append(column == value)
    if occurred_from is not None:
        conditions.append(OrganizationActivity.occurred_at >= occurred_from)
    if occurred_to is not None:
        conditions.append(OrganizationActivity.occurred_at <= occurred_to)
    total = session.exec(select(func.count()).select_from(OrganizationActivity).where(*conditions)).one()
    rows = list(
        session.exec(
            select(OrganizationActivity)
            .where(*conditions)
            .order_by(OrganizationActivity.occurred_at.desc(), OrganizationActivity.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/activities/{activity_id}", response_model=ActivityRead)
def get_activity(
    activity_id: UUID,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationActivity:
    return _tenant_detail(session, OrganizationActivity, activity_id, context.tenant_key)


@router.post("/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity_endpoint(
    payload: ActivityCreate,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationActivity:
    return _command(lambda: append_activity(session, context, **payload.model_dump()))


@router.get("/contributions", response_model=OrganizationPage[ContributionRead])
def list_contributions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    work_item_id: UUID | None = None,
    department: str | None = None,
    contribution_type: str | None = None,
    source_type: str | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationContribution.tenant_key == context.tenant_key]
    for value, column in (
        (work_item_id, OrganizationContribution.work_item_id),
        (department, OrganizationContribution.department),
        (contribution_type, OrganizationContribution.contribution_type),
        (source_type, OrganizationContribution.source_object_type),
    ):
        if value is not None:
            conditions.append(column == value)
    total = session.exec(select(func.count()).select_from(OrganizationContribution).where(*conditions)).one()
    rows = list(
        session.exec(
            select(OrganizationContribution)
            .where(*conditions)
            .order_by(OrganizationContribution.effective_at.desc(), OrganizationContribution.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/contributions/{contribution_id}", response_model=ContributionRead)
def get_contribution(
    contribution_id: UUID,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationContribution:
    return _tenant_detail(session, OrganizationContribution, contribution_id, context.tenant_key)


@router.post("/contributions", response_model=ContributionRead, status_code=status.HTTP_201_CREATED)
def create_contribution_endpoint(
    payload: ContributionCreate,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationContribution:
    def invoke() -> OrganizationContribution:
        descriptor = validate_authoritative_outcome(
            session,
            context,
            source_type=payload.source_type,
            source_id=payload.source_id,
            source_version=payload.source_version,
            outcome_type=payload.outcome_type,
            verification_basis=payload.verification_basis,
        )
        command = payload.model_dump(
            exclude={"source_type", "source_id", "source_version", "outcome_type", "verification_basis"}
        )
        return create_contribution(
            session,
            context,
            descriptor=descriptor,
            authority_level=context.authority_level or "L0",
            **command,
        )

    return _command(invoke)


@router.post(
    "/contributions/{contribution_id}/corrections",
    response_model=ContributionRead,
    status_code=status.HTTP_201_CREATED,
)
def correct_contribution_endpoint(
    contribution_id: UUID,
    payload: ContributionCorrectionCreate,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationContribution:
    def invoke() -> OrganizationContribution:
        descriptor = validate_authoritative_outcome(
            session,
            context,
            source_type=payload.source_type,
            source_id=payload.source_id,
            source_version=payload.source_version,
            outcome_type=payload.outcome_type,
            verification_basis=payload.verification_basis,
        )
        return append_contribution_correction(
            session,
            context,
            original_contribution_id=contribution_id,
            descriptor=descriptor,
            **payload.model_dump(
                exclude={"source_type", "source_id", "source_version", "outcome_type", "verification_basis"}
            ),
        )

    return _command(invoke)


# `/work-items` remains the legacy v13 governance surface. The reviewed durable
# records use this collision-free subresource until a separately governed legacy
# migration can consolidate both contracts.
@router.get("/work-items/records", response_model=OrganizationPage[WorkItemRead])
def list_work_item_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(default=None, alias="status"),
    department: str | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationalWorkItem.tenant_key == context.tenant_key]
    if status_filter is not None:
        conditions.append(OrganizationalWorkItem.status == status_filter)
    if department is not None:
        conditions.append(OrganizationalWorkItem.department == department)
    total = session.exec(select(func.count()).select_from(OrganizationalWorkItem).where(*conditions)).one()
    rows = list(
        session.exec(
            select(OrganizationalWorkItem)
            .where(*conditions)
            .order_by(OrganizationalWorkItem.created_at.desc(), OrganizationalWorkItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.post("/work-items/records", response_model=WorkItemRead, status_code=status.HTTP_201_CREATED)
def create_work_item_record(
    payload: WorkItemCreate,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationalWorkItem:
    return _command(
        lambda: create_work_item(
            session,
            context,
            authority_level=context.authority_level or "L0",
            context_payload=payload.context,
            **payload.model_dump(exclude={"context"}),
        )
    )


@router.get("/work-items/records/{work_item_id}", response_model=WorkItemRead)
def get_work_item_record(
    work_item_id: UUID,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> OrganizationalWorkItem:
    return _tenant_detail(session, OrganizationalWorkItem, work_item_id, context.tenant_key)


def _work_transition(
    operation: Callable[..., OrganizationalWorkItem],
    session: Session,
    context: OrganizationCommandContext,
    work_item_id: UUID,
    reason: str,
) -> OrganizationalWorkItem:
    return _command(lambda: operation(session, context, work_item_id=work_item_id, reason=reason))


@router.post("/work-items/records/{work_item_id}/start", response_model=WorkItemRead)
def start_work_item_record(work_item_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _work_transition(start_work_item, session, context, work_item_id, payload.reason)


@router.post("/work-items/records/{work_item_id}/block", response_model=WorkItemRead)
def block_work_item_record(work_item_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _work_transition(block_work_item, session, context, work_item_id, payload.reason)


@router.post("/work-items/records/{work_item_id}/await-human", response_model=WorkItemRead)
def await_human_work_item_record(work_item_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _work_transition(await_human_for_work_item, session, context, work_item_id, payload.reason)


@router.post("/work-items/records/{work_item_id}/complete", response_model=WorkItemRead)
def complete_work_item_record(work_item_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _work_transition(complete_work_item, session, context, work_item_id, payload.reason)


@router.post("/work-items/records/{work_item_id}/cancel", response_model=WorkItemRead)
def cancel_work_item_record(work_item_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _work_transition(cancel_work_item, session, context, work_item_id, payload.reason)


@router.post("/work-items/records/{work_item_id}/assign", response_model=WorkItemRead)
def assign_work_item_record(work_item_id: UUID, payload: WorkAssignCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    return _command(lambda: assign_work_item(session, context, work_item_id=work_item_id, assigned_position_key=payload.assigned_position_key, reason=payload.reason))


@router.get("/work-item-dependencies", response_model=OrganizationPage[DependencyRead])
def list_dependencies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    work_item_id: UUID | None = None,
    status_filter: OrganizationDependencyStatus | None = Query(default=None, alias="status"),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationWorkItemDependency.tenant_key == context.tenant_key]
    if work_item_id is not None:
        conditions.append(OrganizationWorkItemDependency.work_item_id == work_item_id)
    if status_filter is not None:
        conditions.append(OrganizationWorkItemDependency.status == status_filter)
    total = session.exec(select(func.count()).select_from(OrganizationWorkItemDependency).where(*conditions)).one()
    rows = list(session.exec(select(OrganizationWorkItemDependency).where(*conditions).order_by(OrganizationWorkItemDependency.created_at.desc(), OrganizationWorkItemDependency.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/work-item-dependencies/{dependency_id}", response_model=DependencyRead)
def get_dependency(dependency_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationWorkItemDependency:
    return _tenant_detail(session, OrganizationWorkItemDependency, dependency_id, context.tenant_key)


@router.post("/work-item-dependencies", response_model=DependencyRead, status_code=status.HTTP_201_CREATED)
def create_dependency_endpoint(payload: DependencyCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationWorkItemDependency:
    return _command(lambda: create_dependency(session, context, **payload.model_dump()))


@router.post("/work-item-dependencies/{dependency_id}/satisfy", response_model=DependencyRead)
def satisfy_dependency_endpoint(dependency_id: UUID, payload: DependencySatisfyCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationWorkItemDependency:
    return _command(lambda: satisfy_dependency(session, context, dependency_id=dependency_id, contribution_id=payload.contribution_id, reason=payload.reason))


@router.post("/work-item-dependencies/{dependency_id}/waive", response_model=DependencyRead)
def waive_dependency_endpoint(dependency_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationWorkItemDependency:
    return _command(lambda: waive_dependency(session, context, dependency_id=dependency_id, reason=payload.reason))


@router.post("/work-item-dependencies/{dependency_id}/supersede", response_model=DependencyRead)
def supersede_dependency_endpoint(dependency_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationWorkItemDependency:
    return _command(lambda: supersede_dependency(session, context, dependency_id=dependency_id, reason=payload.reason))


@router.get("/blockers", response_model=OrganizationPage[BlockerRead])
def list_blockers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    work_item_id: UUID | None = None,
    status_filter: OrganizationBlockerStatus | None = Query(default=None, alias="status"),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationBlocker.tenant_key == context.tenant_key]
    if work_item_id is not None:
        conditions.append(OrganizationBlocker.work_item_id == work_item_id)
    if status_filter is not None:
        conditions.append(OrganizationBlocker.status == status_filter)
    total = session.exec(select(func.count()).select_from(OrganizationBlocker).where(*conditions)).one()
    rows = list(session.exec(select(OrganizationBlocker).where(*conditions).order_by(OrganizationBlocker.created_at.desc(), OrganizationBlocker.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/blockers/{blocker_id}", response_model=BlockerRead)
def get_blocker(blocker_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _tenant_detail(session, OrganizationBlocker, blocker_id, context.tenant_key)


@router.post("/blockers", response_model=BlockerRead, status_code=status.HTTP_201_CREATED)
def create_blocker_endpoint(payload: BlockerCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _command(lambda: open_blocker(session, context, department=context.department, accountable_position_key=context.position_key, authority_level=context.authority_level, **payload.model_dump()))


def _blocker_transition(operation: Callable[..., OrganizationBlocker], session: Session, context: OrganizationCommandContext, blocker_id: UUID, reason: str) -> OrganizationBlocker:
    return _command(lambda: operation(session, context, blocker_id=blocker_id, reason=reason))


@router.post("/blockers/{blocker_id}/mitigate", response_model=BlockerRead)
def mitigate_blocker_endpoint(blocker_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _blocker_transition(mitigate_blocker, session, context, blocker_id, payload.reason)


@router.post("/blockers/{blocker_id}/resolve", response_model=BlockerRead)
def resolve_blocker_endpoint(blocker_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _blocker_transition(resolve_blocker, session, context, blocker_id, payload.reason)


@router.post("/blockers/{blocker_id}/waive", response_model=BlockerRead)
def waive_blocker_endpoint(blocker_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _blocker_transition(waive_blocker, session, context, blocker_id, payload.reason)


@router.post("/blockers/{blocker_id}/supersede", response_model=BlockerRead, status_code=status.HTTP_201_CREATED)
def supersede_blocker_endpoint(blocker_id: UUID, payload: BlockerSupersedeCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationBlocker:
    return _command(
        lambda: open_blocker(
            session,
            context,
            supersedes_blocker_id=blocker_id,
            department=context.department,
            accountable_position_key=context.position_key,
            authority_level=context.authority_level,
            **payload.model_dump(),
        )
    )


@router.get("/human-action-requests", response_model=OrganizationPage[HumanActionRequestRead])
def list_human_action_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: OrganizationHumanActionRequestStatus | None = Query(default=None, alias="status"),
    assigned_human_id: str | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationHumanActionRequest.tenant_key == context.tenant_key]
    if status_filter is not None:
        conditions.append(OrganizationHumanActionRequest.status == status_filter)
    if assigned_human_id is not None:
        conditions.append(OrganizationHumanActionRequest.assigned_human_id == assigned_human_id)
    total = session.exec(select(func.count()).select_from(OrganizationHumanActionRequest).where(*conditions)).one()
    rows = list(session.exec(select(OrganizationHumanActionRequest).where(*conditions).order_by(OrganizationHumanActionRequest.created_at.desc(), OrganizationHumanActionRequest.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/human-action-requests/{request_id}", response_model=HumanActionRequestRead)
def get_human_action_request(request_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _tenant_detail(session, OrganizationHumanActionRequest, request_id, context.tenant_key)


@router.post("/human-action-requests", response_model=HumanActionRequestRead, status_code=status.HTTP_201_CREATED)
def create_human_action_request_endpoint(payload: HumanActionRequestCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: create_human_action_request(session, context, authority_level=context.authority_level, **payload.model_dump()))


@router.post("/human-action-requests/{request_id}/assign", response_model=HumanActionRequestRead)
def assign_human_action_request_endpoint(request_id: UUID, payload: HumanActionRequestAssign, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: assign_human_action_request(session, context, request_id=request_id, assigned_human_id=payload.assigned_human_id, reason=payload.reason))


@router.post("/human-action-requests/{request_id}/acknowledge", response_model=HumanActionRequestRead)
def acknowledge_human_action_request_endpoint(request_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: acknowledge_human_action_request(session, context, request_id=request_id))


@router.post("/human-action-requests/{request_id}/start", response_model=HumanActionRequestRead)
def start_human_action_request_endpoint(request_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: start_human_action_request(session, context, request_id=request_id))


@router.post("/human-action-requests/{request_id}/complete", response_model=HumanActionCompletionRead)
def complete_human_action_request_endpoint(request_id: UUID, payload: HumanActionComplete, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> dict[str, Any]:
    request_row, action = _command(lambda: complete_human_action_request(session, context, request_id=request_id, **payload.model_dump()))
    return {"request": request_row, "action": action}


@router.post("/human-action-requests/{request_id}/decline", response_model=HumanActionRequestRead)
def decline_human_action_request_endpoint(request_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: decline_human_action_request(session, context, request_id=request_id, outcome=payload.reason))


@router.post("/human-action-requests/{request_id}/cancel", response_model=HumanActionRequestRead)
def cancel_human_action_request_endpoint(request_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: cancel_human_action_request(session, context, request_id=request_id, outcome=payload.reason))


@router.post("/human-action-requests/{request_id}/expire", response_model=HumanActionRequestRead)
def expire_human_action_request_endpoint(request_id: UUID, payload: ReasonCommand, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanActionRequest:
    return _command(lambda: expire_human_action_request(session, context, request_id=request_id, outcome=payload.reason))


@router.get("/human-actions", response_model=OrganizationPage[HumanActionRead])
def list_human_actions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    human_action_request_id: UUID | None = None,
    human_actor_id: str | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationHumanAction.tenant_key == context.tenant_key]
    if human_action_request_id is not None:
        conditions.append(OrganizationHumanAction.human_action_request_id == human_action_request_id)
    if human_actor_id is not None:
        conditions.append(OrganizationHumanAction.human_actor_id == human_actor_id)
    total = session.exec(select(func.count()).select_from(OrganizationHumanAction).where(*conditions)).one()
    rows = list(session.exec(select(OrganizationHumanAction).where(*conditions).order_by(OrganizationHumanAction.occurred_at.desc(), OrganizationHumanAction.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/human-actions/{action_id}", response_model=HumanActionRead)
def get_human_action(action_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanAction:
    return _tenant_detail(session, OrganizationHumanAction, action_id, context.tenant_key)


@router.post("/human-actions", response_model=HumanActionRead, status_code=status.HTTP_201_CREATED)
def create_human_action_endpoint(payload: HumanActionCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationHumanAction:
    return _command(lambda: append_human_action(session, context, **payload.model_dump()))


@router.get("/decisions/records", response_model=OrganizationPage[DecisionRead])
def list_decision_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(default=None, alias="status"),
    work_item_id: UUID | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [ExecutiveDecision.tenant_key == context.tenant_key]
    if status_filter is not None:
        conditions.append(ExecutiveDecision.status == status_filter)
    if work_item_id is not None:
        conditions.append(ExecutiveDecision.work_item_id == work_item_id)
    total = session.exec(select(func.count()).select_from(ExecutiveDecision).where(*conditions)).one()
    rows = list(session.exec(select(ExecutiveDecision).where(*conditions).order_by(ExecutiveDecision.created_at.desc(), ExecutiveDecision.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.post("/decisions/records", response_model=DecisionRead, status_code=status.HTTP_201_CREATED)
def create_decision_record(payload: DecisionCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> ExecutiveDecision:
    authority_level = "L4" if payload.decision_type.value == "board_reserved" else (context.authority_level or "L0")
    owner = "board" if authority_level == "L4" else "ceo"
    return _command(lambda: create_executive_decision(session, context, authority_level=authority_level, requested_by_position=context.position_key or "unknown", decision_owner_position=owner, **payload.model_dump()))


@router.get("/decisions/records/{decision_id}", response_model=DecisionRead)
def get_decision_record(decision_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> ExecutiveDecision:
    return _tenant_detail(session, ExecutiveDecision, decision_id, context.tenant_key)


@router.post("/decisions/records/{decision_id}/outcome", response_model=DecisionRead)
def record_decision_outcome_endpoint(decision_id: UUID, payload: DecisionOutcome, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> ExecutiveDecision:
    return _command(lambda: record_executive_decision_outcome(session, context, decision_id=decision_id, outcome=payload.outcome, reason=payload.reason, effect_summary=payload.effect_summary))


@router.post("/decisions/records/{decision_id}/supersede", response_model=DecisionRead, status_code=status.HTTP_201_CREATED)
def supersede_decision_endpoint(decision_id: UUID, payload: DecisionSupersede, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> ExecutiveDecision:
    return _command(lambda: supersede_executive_decision(session, context, original_decision_id=decision_id, **payload.model_dump()))


@router.get("/record-references", response_model=OrganizationPage[ReferenceRead])
def list_record_references(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    target_type: str | None = None,
    target_id: str | None = None,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions: list[Any] = [OrganizationRecordReference.tenant_key == context.tenant_key]
    if target_type is not None:
        conditions.append(OrganizationRecordReference.target_type == target_type)
    if target_id is not None:
        conditions.append(OrganizationRecordReference.target_id == target_id)
    total = session.exec(select(func.count()).select_from(OrganizationRecordReference).where(*conditions)).one()
    rows = list(session.exec(select(OrganizationRecordReference).where(*conditions).order_by(OrganizationRecordReference.created_at.desc(), OrganizationRecordReference.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return _page_result(rows, page=page, page_size=page_size, total=total)


@router.get("/record-references/{reference_id}", response_model=ReferenceRead)
def get_record_reference(reference_id: UUID, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationRecordReference:
    return _tenant_detail(session, OrganizationRecordReference, reference_id, context.tenant_key)


@router.post("/record-references", response_model=ReferenceRead, status_code=status.HTTP_201_CREATED)
def create_record_reference_endpoint(payload: ReferenceCreate, context: OrganizationCommandContext = Depends(organization_command_context), session: Session = Depends(get_session)) -> OrganizationRecordReference:
    return _command(lambda: create_record_reference(session, context, **payload.model_dump()))
