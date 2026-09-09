# Global Mobility AIOS — Agent Entry Point

This repository uses a layered agent-governance contract. Read the following sources before substantial implementation work and treat repository state plus accepted proof as authoritative.

## Required startup order

1. Read `agents/AIOS_AGENT_CONSTITUTION.md` for durable autonomy, verification, PR/CI, visual-acceptance, truth-boundary, and merge rules.
2. Read `agents/PROJECT_STATE.md` for the current project map.
3. Read `agents/SESSION_HANDOFF.md` for the latest branch/worktree state, recent decisions, and recovery commands.
4. Read `agents/REPOSITORY_AGENT_GUIDE.md` for repository layout, stack, setup, test/proof commands, security, vendor boundaries, and documentation conventions.
5. When running in Codex or a Codex-like shared-workspace runtime, also read `agents/CODEX_RUNTIME_ADAPTER.md`.
6. Verify active milestone and acceptance claims against `docs/ROADMAP.md`, `docs/CHANGELOG.md`, relevant acceptance records, current git refs, current PR metadata, and current workflow state before acting.

## Precedence

Higher-priority platform/system instructions remain binding.

Within repository guidance, current observed repository/project state outranks stale prose. The constitution defines durable agent behavior; the repository guide defines project-specific mechanics; project-state/handoff files describe current execution context; roadmap and acceptance records define milestone truth.

If two repository documents disagree, do not silently choose the more convenient claim. Refresh the underlying repository/PR/workflow state, identify which document is stale, preserve accepted truth boundaries, and reconcile documentation when the active task authorizes it.

## Working rule

When the user asks to proceed with an already-authorized AIOS workflow, continue through implementation, required validation, current-head CI, applicable visual inspection, normalization/readiness, merge, and post-merge verification as required by the slice acceptance contract. Do not stop at an intermediate success or repeatedly ask for authorization already granted.
