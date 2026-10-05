"""Source-owned probe families, never evidence of implemented or passing probes."""

CORE_COVERAGE_CONTRACT = "phase22.core_journey.source_coverage.v1"
FEATURE_PROBE_FAMILIES = {
    "crm": ("synthetic_lead_persistence", "postgresql"),
    "controlled-agents": ("synthetic_agent_queue_review", "postgresql_redis_worker"),
    "organization-governance": ("scheduled_internal_work", "postgresql_redis_worker_beat"),
    "auth": ("governed_action_denial", "signed_session"),
}
FRONTEND_PROBE_FAMILIES = {
    "/": "synthetic_lead_form",
    "/agents/console": "compiled_batch_submission",
    "/agents/review": "durable_review_readback",
    "/agents/review/[id]": "durable_review_detail",
}
# This compatibility pair is explicitly documented in router_registry.py.
# No other same-named endpoint is automatically treated as equivalent.
EXPLICIT_REGISTRATION_ALIASES = frozenset({("dashboard-api", "dashboard-compat")})
FOUNDATION_BLOCKERS = (
    "source_inventory_is_not_deployed_runtime_evidence",
    "actual_capability_probes_unavailable",
    "scheduler_dispatch_provenance_unavailable",
    "restart_durability_evidence_unavailable",
    "compiled_frontend_manifest_observation_unavailable",
    "deployed_runtime_profile_inventory_unavailable",
)
