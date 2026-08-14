from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CoverageBasis = Literal[
    "authoritative_current_rows",
    "first_observed_contribution",
    "not_established",
    "explicit_command_only",
    "partial_activity_coverage",
]

ReconciliationStatus = Literal[
    "matched",
    "missing_source",
    "source_state_drift",
    "source_version_drift",
    "duplicate_outcome",
    "missing_contribution_in_coverage",
    "unsupported_source",
]


class ObservatoryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContributionSourceCoverage(ObservatoryRead):
    source_type: str
    automatic_emitter: bool
    coverage_basis: CoverageBasis
    coverage_start: datetime | None = None
    coverage_established: bool
    contribution_outcome_count: int = 0
    eligible_source_rows: int = 0
    matched_source_rows: int = 0
    precoverage_source_rows: int = 0
    missing_contribution_in_coverage: int = 0
    warnings: list[str] = Field(default_factory=list)


class WorkSnapshotMetrics(ObservatoryRead):
    total: int
    active: int
    terminal: int
    overdue_active: int
    oldest_active_created_at: datetime | None = None
    by_status: dict[str, int] = Field(default_factory=dict)
    by_department: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)


class BlockerSnapshotMetrics(ObservatoryRead):
    total: int
    open: int
    mitigated: int
    due_or_overdue_open: int
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_department: dict[str, int] = Field(default_factory=dict)


class DecisionSnapshotMetrics(ObservatoryRead):
    total: int
    pending: int
    board_attention: int
    by_status: dict[str, int] = Field(default_factory=dict)


class HumanAttentionMetrics(ObservatoryRead):
    request_total: int
    pending_requests: int
    overdue_pending_requests: int
    immutable_human_actions: int
    by_request_status: dict[str, int] = Field(default_factory=dict)


class DependencySnapshotMetrics(ObservatoryRead):
    total: int
    active_edges: int
    blocked_downstream_work_items: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)


class ContributionSnapshotMetrics(ObservatoryRead):
    total_records: int
    historical_outcomes: int
    active_outcomes: int
    supersessions: int
    retractions: int
    by_department: dict[str, int] = Field(default_factory=dict)
    by_contribution_type: dict[str, int] = Field(default_factory=dict)


class ObservatorySummaryMetrics(ObservatoryRead):
    work: WorkSnapshotMetrics
    blockers: BlockerSnapshotMetrics
    decisions: DecisionSnapshotMetrics
    human_attention: HumanAttentionMetrics
    dependencies: DependencySnapshotMetrics
    contributions: ContributionSnapshotMetrics


class ObservatoryCoverage(ObservatoryRead):
    snapshot_basis: CoverageBasis = "authoritative_current_rows"
    activity_history_basis: CoverageBasis = "partial_activity_coverage"
    activity_history_established: bool = False
    contribution_sources: list[ContributionSourceCoverage] = Field(default_factory=list)


class ObservatorySummaryRead(ObservatoryRead):
    as_of: datetime
    timezone: Literal["UTC"] = "UTC"
    tenant_scope: str
    source_row_counts: dict[str, int]
    metrics: ObservatorySummaryMetrics
    coverage: ObservatoryCoverage
    warnings: list[str] = Field(default_factory=list)


class DepartmentSnapshot(ObservatoryRead):
    department: str
    work_items_total: int
    work_items_active: int
    work_items_terminal: int
    blockers_open: int
    blockers_mitigated: int
    historical_contribution_outcomes: int
    active_contributions: int
    pending_human_action_requests_linked_to_work: int


class ObservatoryDepartmentsRead(ObservatoryRead):
    as_of: datetime
    timezone: Literal["UTC"] = "UTC"
    tenant_scope: str
    source_row_counts: dict[str, int]
    coverage: ObservatoryCoverage
    departments: list[DepartmentSnapshot]
    warnings: list[str] = Field(default_factory=list)


class ContributionReconciliationItem(ObservatoryRead):
    status: ReconciliationStatus
    source_type: str
    source_id: str
    contribution_id: UUID | None = None
    contribution_key: str | None = None
    contribution_source_version: str | None = None
    current_source_version: str | None = None
    source_state: str | None = None
    current_source_state: str | None = None
    source_transition_at: datetime | None = None
    contribution_created_at: datetime | None = None
    coverage_basis: CoverageBasis
    duplicate_contribution_ids: list[UUID] = Field(default_factory=list)
    detail: str


class ContributionReconciliationRead(ObservatoryRead):
    as_of: datetime
    timezone: Literal["UTC"] = "UTC"
    tenant_scope: str
    source_row_counts: dict[str, int]
    page: int
    page_size: int
    total: int
    total_pages: int
    coverage: list[ContributionSourceCoverage]
    data: list[ContributionReconciliationItem]
    warnings: list[str] = Field(default_factory=list)
