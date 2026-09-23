# Global Mobility AIOS — Agent Entry Point

`AGENTS.md` is the repository front door only. It does not own programme status, architecture, acceptance history, or implementation truth.

## Cold-start chain

For substantial AIOS work, use this order and stop reading when the active task has enough authoritative context:

1. `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md` — how work is selected, built, verified, sealed, and reconciled.
2. `agents/PROJECT_STATE.md` — what is true now at programme level and what bounded slice is next.
3. `docs/ROADMAP.md` — what remains, why it matters, and the intended order.
4. Read only the architecture/specification/ADR material relevant to the selected slice.
5. Inspect the real code, schema, tests, current GitHub refs/PRs/workflows, and exact-head proof before acting.
6. `agents/SESSION_HANDOFF.md` — minimal recovery coordinates and the smallest task-specific resume pointer; never a substitute for live GitHub state.

Do **not** scan every historical phase record, changelog entry, acceptance artifact, or donor/reference document during cold start.

When repository mechanics are needed, use `agents/REPOSITORY_AGENT_GUIDE.md`. When durable agent-governance behavior itself is relevant, use `agents/AIOS_AGENT_CONSTITUTION.md`. When the runtime is Codex or a Codex-like shared workspace, use `agents/CODEX_RUNTIME_ADAPTER.md`. None of those files owns the current programme phase or next slice.

## Repository authority

Higher-priority platform/system instructions remain binding.

Within AIOS repository guidance, use this precedence when claims conflict:

`accepted canonical contracts / sealed decisions -> verified repository + schema + owning-system state -> accepted architecture / specification -> docs/ROADMAP.md -> agents/PROJECT_STATE.md -> agents/SESSION_HANDOFF.md -> conversation / memory`

GitHub PR, commit, branch, and workflow state is authoritative for whether a candidate is open, green, ready, merged, or currently at a particular SHA. A living document may point to the last meaningful implementation checkpoint, but it must not pretend to self-update the integration branch head.

If two sources disagree, refresh the system that owns the fact, identify the stale source, preserve accepted truth boundaries, and reconcile the existing canonical document instead of creating another status document.

## Working rule

When the user has already authorized an AIOS workflow, continue through the bounded exit predicate: inspect -> implement -> test -> independent review -> exact-head proof -> readiness -> expected-head merge where supported -> post-merge verification -> living-document reconciliation. Do not stop at an intermediate success or repeatedly ask for authorization already granted.
