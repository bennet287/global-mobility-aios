# Global Mobility AIOS — Architecture Map

**Purpose:** durable navigation map for architecture sources. This file does not own active programme status, branch heads, or phase scheduling, and it must not become a second master architecture specification.

## Architecture authority

Use architecture at the narrowest relevant level:

1. Accepted canonical truth/evidence/authority/security/domain contracts and sealed decisions.
2. Verified code, schema, configuration, and tests for what is actually implemented.
3. The accepted architecture/specification that owns the task domain.
4. ADRs or dated decision records for why a consequential choice was made.
5. `docs/ROADMAP.md` for when unfinished architecture is scheduled.

The high-level product architecture is described by existing accepted documents, including:

- `docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` — combined AIOS product/organization architecture.
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` — persistent AI organization, authority, autonomy, and human-governance architecture.
- `docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md` — enterprise integration and sovereignty boundaries.
- `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — AIOS V2 product destination and redesign acceptance model.
- `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — employee/capability/skills/tools/learning architecture and capability-vs-authority separation.
- `docs/ADR/` — durable architecture decisions where a specific ADR exists.

Read only the sources relevant to the active slice. Dated phase execution/reconciliation records may contain permanent decisions, but their SHA/status snapshots are historical unless the current owning documents say otherwise.

## Implementation rule

Architecture prose describes intended contracts; the repository proves implemented reality. Before introducing a service, state store, framework, workflow, runtime, or abstraction:

- inspect the real models/services/routers/tests/configuration first;
- reuse the existing canonical owner when one exists;
- preserve truth, authority, evidence, privacy, and reconciliation boundaries;
- add a new durable architecture document only when a genuinely separate domain/authority cannot be represented in an existing owner.

The older workflow-first component sketch previously stored in this file is superseded as a repository-wide architecture description by the accepted architecture set above. Historical implementation ideas such as n8n/LangGraph usage are not implied production dependencies merely because they appeared in that sketch; verify current adoption in code and task-relevant accepted specifications.
