from dataclasses import replace
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from sqlmodel import select

from app.main import app
from app.models.domain import Lead
from app.models.production_deployment_acceptance import ProductionDeploymentAcceptanceCheckReceipt
from app.services.organization_command import InvalidHumanActor, NotFound
from app.services.production_deployment_acceptance import prepare_deployment_acceptance_run
from app.services import production_core_journey_coverage as coverage
from scripts.production_release_identity import RELEASE_CONFIGURATION_PATHS, compute_release_configuration_fingerprint
from tests.test_production_deployment_acceptance import (
    _context, _work_and_decision, ENVIRONMENT_FP, NETWORKING_CONTRACT,
)


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


def _commit(root):
    _git(root, "add", ".")
    _git(root, "-c", "user.name=Pytest", "-c", "user.email=pytest@example.invalid", "commit", "-m", "synthetic candidate")
    return _git(root, "rev-parse", "HEAD")


def _write(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / "candidate"
    root.mkdir()
    _git(root, "init")
    for path in RELEASE_CONFIGURATION_PATHS:
        _write(root, path, f"synthetic configuration: {path}\n")
    _write(root, "apps/api/app/core/router_registry.py", '''ROUTER_SPECS = (
    RouterSpec(crm.router, prefix="/api/v1", feature="crm"),
)
''')
    _write(root, "apps/api/app/routers/crm.py", '''router = APIRouter()
@router.post("/leads")
def create_lead(): pass
@router.get("/leads")
def list_leads(): pass
''')
    _write(root, "apps/api/app/main.py", '''@app.get("/health")
def health(): pass
register_routers(app)
''')
    _write(root, "apps/api/app/agents/registry.py", '''CONTROLLED_AGENT_REGISTRY = {
    "sales_summary_agent": {"version": "v4.0", "department": "sales", "role_card": "not emitted"},
}
AGENT_ALIASES = {"sales_followup_agent": "sales_summary_agent"}
raise RuntimeError("candidate code must never execute")
''')
    _write(root, "apps/api/app/services/department_runtime.py", '''class DepartmentRuntimeSpec:
    allowed_actions: frozenset[str] | None = frozenset()
_INTERNAL_ANALYSIS = frozenset({"internal.analysis"})
DEPARTMENT_RUNTIMES = {
    "executive": DepartmentRuntimeSpec("executive", "ceo"),
    "operations": DepartmentRuntimeSpec("operations", "coo", allowed_actions=None),
    "technology": DepartmentRuntimeSpec("technology", "cto", allowed_actions=_INTERNAL_ANALYSIS),
}
''')
    _write(root, "apps/web/app/page.tsx", "export default function Page() { return null; }")
    _commit(root)
    return root


def _run(session, root, *, configuration_fingerprint=None):
    sha = _git(root, "rev-parse", "HEAD")
    context = _context()
    work, decision = _work_and_decision(session, source_version=sha)
    run = prepare_deployment_acceptance_run(
        session, context, deployment_run_key=f"coverage-{uuid4()}", environment_key="synthetic-canary",
        target_environment_fingerprint=ENVIRONMENT_FP, release_commit_sha=sha,
        release_configuration_fingerprint=configuration_fingerprint or compute_release_configuration_fingerprint(root),
        rollback_release_commit_sha="b" * 40, rollback_configuration_fingerprint="d" * 64,
        networking_contract=NETWORKING_CONTRACT, work_item_id=work.id,
        admission_decision_id=decision.id, reason="Prepare synthetic source inventory only.",
    )
    return context, run


def _project(session, root, context, run):
    return coverage.project_core_journey_source_coverage(session, context, deployment_run_id=run.id, candidate_root=root)


def test_bound_projection_is_deterministic_read_only_and_never_satisfied(candidate, db_session):
    context, run = _run(db_session, candidate)
    pending = Lead(full_name="Unflushed caller state")
    db_session.add(pending)
    first = _project(db_session, candidate, context, run)
    assert first == _project(db_session, candidate, context, run)
    assert pending in db_session.new
    assert first["core_journey_status"] == "blocked"
    assert first["core_journey_satisfied"] is False
    assert first["live_observation"] is False
    assert first["receipt_written"] is False
    assert "not emitted" not in str(first)
    assert "candidate code must never execute" not in str(first)
    assert all(row["evidence_status"] == "source_only_unprobed" for row in first["entries"])
    held = next(row for row in first["entries"] if row["kind"] == "department_runtime" and row["key"] == "executive")
    assert held["declared_posture"] == "held_by_source_declaration"
    assert held["disabled_verified"] is False
    with db_session.no_autoflush:
        assert db_session.exec(select(ProductionDeploymentAcceptanceCheckReceipt)).all() == []


def test_canonical_tenant_actor_and_integrity_checks_precede_source_reads(candidate, db_session, monkeypatch):
    context, run = _run(db_session, candidate)
    monkeypatch.setattr(coverage, "_identity", lambda root: pytest.fail("source read before authorization/integrity"))
    from app.models.domain import OrganizationActorType
    with pytest.raises(InvalidHumanActor):
        _project(db_session, candidate, replace(context, actor_type=OrganizationActorType.agent), run)
    with pytest.raises(NotFound):
        _project(db_session, candidate, replace(context, tenant_key="other"), run)
    run.record_fingerprint = "0" * 64
    db_session.add(run)
    db_session.commit()
    from app.services.production_deployment_acceptance import DeploymentAcceptanceIntegrityError
    with pytest.raises(DeploymentAcceptanceIntegrityError):
        _project(db_session, candidate, context, run)


def test_new_paths_pages_actions_and_aliases_remain_explicit_unprobed(candidate, db_session):
    _write(candidate, "apps/api/app/routers/crm.py", '''router = APIRouter()
@router.post("/brand-new-action")
def new_action(): pass
@router.get(path=dynamic_path)
def unsupported_route(): pass
''')
    _write(candidate, "apps/web/app/api/new/route.ts", "export async function GET() {}")
    _write(candidate, "apps/web/pages/legacy.tsx", "export default function Page() {}")
    _write(candidate, "apps/web/next.config.js", "module.exports = {pageExtensions: ['mdx']}")
    _write(candidate, "apps/web/app/@parallel/(group)/[[...slug]]/page.mdx", "synthetic page")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    report = _project(db_session, candidate, context, run)
    assert any(row.get("path") == "/api/v1/brand-new-action" for row in report["entries"])
    assert any(row["kind"] == "unsupported_source" for row in report["entries"])
    assert any(row["key"] == "/@parallel/(group)/[[...slug]]" for row in report["entries"])
    assert any(row["kind"] == "agent_alias" and row["canonical_agent"] == "sales_summary_agent" for row in report["entries"])
    assert "route_decorator_expression_unsupported" in report["blockers"]
    assert "frontend_route_shape_unsupported" in report["blockers"]
    assert "frontend_page_extension_unsupported" in report["blockers"]
    assert "frontend_route_source_unsupported" in report["blockers"]
    assert "frontend_configuration_semantics_unobserved" in report["blockers"]
    assert len([row for row in report["entries"] if row["kind"] == "frontend_unhandled_route_source"]) == 2


def test_exact_commit_pin_dirty_drift_and_resource_bounds(candidate, db_session, monkeypatch):
    context, run = _run(db_session, candidate)
    calls = []
    original = coverage._git

    def observe(root, *args, **kwargs):
        calls.append(args)
        return original(root, *args, **kwargs)

    monkeypatch.setattr(coverage, "_git", observe)
    _project(db_session, candidate, context, run)
    assert ("ls-tree", "-rlz", run.release_commit_sha) in calls
    assert not any(args[:2] == ("ls-tree", "HEAD") for args in calls)
    _write(candidate, "untracked.txt", "synthetic dirty input")
    with pytest.raises(coverage.CoreCoverageError, match="candidate_checkout_dirty"):
        _project(db_session, candidate, context, run)
    (candidate / "untracked.txt").unlink()
    monkeypatch.setattr(coverage, "MAX_SOURCE_BYTES", 1)
    with pytest.raises(coverage.CoreCoverageError, match="source_bound_exceeded"):
        _project(db_session, candidate, context, run)


def test_real_candidate_parser_matches_actual_router_registration_without_startup():
    root = Path(__file__).resolve().parents[3]
    sha = _git(root, "rev-parse", "HEAD")
    rows, blockers, aliases = coverage._inventory(coverage._Sources(root, sha))
    parsed = [(row["method"], row["path"]) for row in rows if row["kind"] == "api_operation"]
    actual = [(method, route.path) for route in app.routes if isinstance(route, APIRoute) for method in route.methods]
    assert sorted(parsed) == sorted(actual)
    assert len([row for row in rows if row["kind"] == "frontend_page"]) == 61
    assert ["dashboard-api", "dashboard-compat"] in aliases
    assert "route_decorator_expression_unsupported" not in blockers


def test_release_configuration_and_postread_drift_are_rejected(candidate, db_session, monkeypatch):
    context, run = _run(db_session, candidate)
    _write(candidate, "new-file", "changed commit")
    _commit(candidate)
    with pytest.raises(coverage.CoreCoverageError, match="candidate_release_mismatch"):
        _project(db_session, candidate, context, run)
    _git(candidate, "reset", "--hard", run.release_commit_sha)
    wrong_context, wrong_run = _run(db_session, candidate, configuration_fingerprint="0" * 64)
    with pytest.raises(coverage.CoreCoverageError, match="candidate_configuration_mismatch"):
        _project(db_session, candidate, wrong_context, wrong_run)
    observations = iter([run.release_commit_sha, "a" * 40])
    monkeypatch.setattr(coverage, "_identity", lambda root: next(observations))
    with pytest.raises(coverage.CoreCoverageError, match="candidate_changed_during_inventory"):
        _project(db_session, candidate, context, run)


def test_subprocess_and_inventory_bounds_have_fixed_errors(candidate, monkeypatch):
    with pytest.raises(coverage.CoreCoverageError, match="git_output_bound_exceeded"):
        coverage._git(candidate, "rev-parse", "HEAD", limit=1)
    monkeypatch.setattr(coverage, "GIT_TIMEOUT_SECONDS", 0)
    with pytest.raises(coverage.CoreCoverageError, match="git_deadline_exceeded"):
        coverage._git(candidate, "rev-parse", "HEAD")
    monkeypatch.setattr(coverage, "GIT_TIMEOUT_SECONDS", 10)
    source = coverage._Sources(candidate, _git(candidate, "rev-parse", "HEAD"))
    monkeypatch.setattr(coverage, "MAX_ENTRIES", 1)
    with pytest.raises(coverage.CoreCoverageError, match="inventory_entry_bound_exceeded"):
        coverage._inventory(source)
    monkeypatch.setattr(coverage, "MAX_ENTRIES", 10000)
    monkeypatch.setattr(coverage, "MAX_METADATA_BYTES", 1)
    with pytest.raises(coverage.CoreCoverageError, match="inventory_metadata_bound_exceeded"):
        coverage._inventory(source)


def test_owner_default_and_unknown_main_registration_are_not_assumed(candidate, db_session):
    path = candidate / "apps/api/app/services/department_runtime.py"
    path.write_text(path.read_text().replace("allowed_actions: frozenset[str] | None = frozenset()", "allowed_actions: frozenset[str] | None = None"))
    main = candidate / "apps/api/app/main.py"
    main.write_text(main.read_text() + "app.add_api_route('/new', unknown_handler)\nroute_alias = app\n@route_alias.get('/aliased')\ndef aliased(): pass\n")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    report = _project(db_session, candidate, context, run)
    executive = next(row for row in report["entries"] if row["kind"] == "department_runtime" and row["key"] == "executive")
    assert executive["declared_posture"] == "general_runtime"
    assert executive["disabled_verified"] is False
    assert "main_dynamic_registration_unsupported" in report["blockers"]
    assert "route_receiver_alias_unsupported" in report["blockers"]


@pytest.mark.parametrize("path,extra,blocker", [
    ("apps/api/app/core/router_registry.py", "ROUTER_SPECS += (new_spec,)\n", "registry_mutation_unsupported"),
    ("apps/api/app/agents/registry.py", "CONTROLLED_AGENT_REGISTRY['new'] = dynamic_agent\n", "registry_mutation_unsupported"),
    ("apps/api/app/services/department_runtime.py", "DEPARTMENT_RUNTIMES['new'] = dynamic_runtime\n", "registry_mutation_unsupported"),
])
def test_registry_mutations_cannot_disappear(candidate, db_session, path, extra, blocker):
    target = candidate / path
    target.write_text(target.read_text() + extra)
    _commit(candidate)
    context, run = _run(db_session, candidate)
    report = _project(db_session, candidate, context, run)
    assert blocker in report["blockers"]
    assert any(row["kind"] == "unsupported_source" and row["owner"] == path for row in report["entries"])


def test_positional_prefix_and_rebound_registry_cannot_be_silently_parsed(candidate, db_session):
    path = candidate / "apps/api/app/core/router_registry.py"
    path.write_text("ROUTER_SPECS = (RouterSpec(crm.router, '/alternate', feature='crm'),)\n")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    assert "router_registration_expression_unsupported" in _project(db_session, candidate, context, run)["blockers"]
    path.write_text(path.read_text() + "ROUTER_SPECS = ()\n")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    with pytest.raises(coverage.CoreCoverageError, match="source_definition_ambiguous"):
        _project(db_session, candidate, context, run)


def test_conditional_nested_router_and_unknown_feature_remain_blocked(candidate, db_session):
    _write(candidate, "apps/api/app/core/router_registry.py", "ROUTER_SPECS = (RouterSpec(crm.router, prefix='/api/v1', feature='brand-new-feature'),)\n")
    _write(candidate, "apps/api/app/routers/crm.py", "from app.routers.child import router as child_router\nrouter = APIRouter()\nif enabled:\n    router.include_router(child_router)\n    @router.get('/conditional')\n    def conditional(): pass\n")
    _write(candidate, "apps/api/app/routers/child.py", "router = APIRouter()\n@router.get('/child')\ndef child(): pass\n")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    report = _project(db_session, candidate, context, run)
    assert "conditional_or_nested_include_unsupported" in report["blockers"]
    assert "conditional_or_nested_route_unsupported" in report["blockers"]
    assert "api_probe_family_unmapped" in report["blockers"]
    paths = {row.get("path") for row in report["entries"]}
    assert {'/api/v1/child', '/api/v1/conditional'} <= paths


def test_positional_department_actions_and_dynamic_main_decorator_block(candidate, db_session):
    _write(candidate, "apps/api/app/services/department_runtime.py", "class DepartmentRuntimeSpec:\n    allowed_actions: frozenset[str] | None = frozenset()\nDEPARTMENT_RUNTIMES = {'executive': DepartmentRuntimeSpec('executive', 'ceo', None)}\n")
    main = candidate / "apps/api/app/main.py"
    main.write_text(main.read_text() + "app.get('/dynamic')(handler)\n")
    _commit(candidate)
    context, run = _run(db_session, candidate)
    report = _project(db_session, candidate, context, run)
    assert "department_runtime_expression_unsupported" in report["blockers"]
    assert not any(row["kind"] == "department_runtime" and row["key"] == "executive" for row in report["entries"])
    assert "main_dynamic_registration_unsupported" in report["blockers"]
