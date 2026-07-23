# Relocation Task Orchestration v11.2

## Scope

v11.2 adds a governed work sequence to each corporate mobility case. Tasks record a category,
accountable owner role, optional due date, optional predecessor, and whether completion needs
independent human approval.

## Lifecycle and review

- Tasks transition through `planned`, `ready`, `in_progress`, and `completed`; operators may
  explicitly block or cancel non-terminal work with required notes.
- A downstream task cannot become ready until its same-case predecessor is completed.
- Sensitive completion moves to `awaiting_approval`. The submitting operator cannot decide
  their own submission.
- Approval completes the task; rejection returns it to work. Every decision is an append-only
  record and every mutation also writes an actor-attributed audit event.
- Completed and cancelled tasks are immutable. Closed cases reject task creation, transition,
  and review.

## Safety boundary

Relocation tasks coordinate accountable human work. They do not infer eligibility, approve a
sponsor or application, submit a government filing, publish regulatory content, or bypass the
Truth Engine and existing evidence-review controls.

Alembic revision `0035_relocation_tasks` adds the task and immutable decision tables. The
Corporate Mobility workspace renders the dependency-aware task ledger within the selected-case
control plane.
