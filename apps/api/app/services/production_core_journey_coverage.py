"""Bounded, non-executing candidate-source inventory for Phase 22 core coverage.

This projection cannot satisfy a gate. It neither imports candidate code nor writes
receipts. Unsupported static forms remain explicit blockers, not inferred runtime.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time
from uuid import UUID

from sqlmodel import Session

from app.services.organization_command import OrganizationCommandContext, canonical_fingerprint, require_human
from app.services.production_deployment_acceptance import validated_deployment_networking_contract
from app.services.production_core_journey_contract import (
    CORE_COVERAGE_CONTRACT, EXPLICIT_REGISTRATION_ALIASES, FEATURE_PROBE_FAMILIES,
    FOUNDATION_BLOCKERS, FRONTEND_PROBE_FAMILIES,
)
from scripts.production_release_identity import RELEASE_CONFIGURATION_PATHS, RELEASE_IDENTITY_CONTRACT

MAX_FILE_BYTES = 1_048_576
MAX_SOURCE_BYTES = 12_582_912
MAX_ENTRIES = 10_000
MAX_METADATA_BYTES = 8192
MAX_REPORT_BYTES = 4_194_304
GIT_TIMEOUT_SECONDS = 10


class CoreCoverageError(RuntimeError):
    """Fixed-code failure; candidate source and command output are never exposed."""


def _git(root: Path, *args: str, limit: int = MAX_FILE_BYTES) -> bytes:
    deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
    try:
        process = subprocess.Popen(["git", "-C", str(root), *args], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        raise CoreCoverageError("git_unavailable") from None
    result = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CoreCoverageError("git_deadline_exceeded")
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, min(8192, limit + 1 - len(result)))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        result.extend(chunk)
                        if len(result) > limit:
                            raise CoreCoverageError("git_output_bound_exceeded")
        if process.wait(timeout=max(0.01, deadline - time.monotonic())) != 0:
            raise CoreCoverageError("git_command_failed")
        return bytes(result)
    except subprocess.TimeoutExpired:
        raise CoreCoverageError("git_deadline_exceeded") from None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()


def _identity(root: Path) -> str:
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise CoreCoverageError("candidate_checkout_dirty")
    sha = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise CoreCoverageError("candidate_commit_invalid")
    return sha


class _Sources:
    def __init__(self, root: Path, commit_sha: str):
        self.root = root
        self.files = {}
        self.manifest = {}
        self.cache = {}
        self.total = 0
        self.deadline = time.monotonic() + 120
        for entry in _git(root, "ls-tree", "-rlz", commit_sha).split(b"\0"):
            if not entry:
                continue
            try:
                metadata, raw_path = entry.split(b"\t", 1)
                mode, kind, sha, size = metadata.split()
                path = raw_path.decode("utf-8")
                self.files[path] = (mode, kind, sha.decode("ascii"), int(size))
            except (ValueError, UnicodeError):
                raise CoreCoverageError("candidate_tree_unsupported") from None
            if len(self.files) > MAX_ENTRIES:
                raise CoreCoverageError("candidate_tree_entry_bound_exceeded")

    def read(self, path: str) -> bytes:
        if time.monotonic() >= self.deadline:
            raise CoreCoverageError("inventory_deadline_exceeded")
        if path in self.cache:
            return self.cache[path]
        item = self.files.get(path)
        if item is None:
            raise CoreCoverageError("required_source_missing")
        mode, kind, sha, size = item
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            raise CoreCoverageError("source_is_not_regular_tracked_blob")
        if size > MAX_FILE_BYTES or self.total + size > MAX_SOURCE_BYTES:
            raise CoreCoverageError("candidate_source_bound_exceeded")
        content = _git(self.root, "cat-file", "blob", sha)
        if len(content) != size:
            raise CoreCoverageError("candidate_blob_size_mismatch")
        self.total += size
        self.manifest[path] = hashlib.sha256(content).hexdigest()
        self.cache[path] = content
        return content

    def tree(self, path: str) -> ast.Module:
        try:
            return ast.parse(self.read(path))
        except (SyntaxError, UnicodeError, ValueError, RecursionError):
            raise CoreCoverageError("source_ast_unsupported") from None


def _literal(node):
    try:
        return ast.literal_eval(node)
    except RecursionError:
        raise CoreCoverageError("source_literal_depth_unsupported") from None


def _assignment(tree, name):
    values = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            values.append(node.value)
    if len(values) != 1:
        raise CoreCoverageError("source_definition_ambiguous" if values else "required_source_definition_missing")
    return values[0]


def _row(kind, key, owner, **extra):
    return {"kind": kind, "key": key, "owner": owner, "evidence_status": "source_only_unprobed", **extra}


class _BoundedRows(list):
    def append(self, row):
        if len(self) >= MAX_ENTRIES:
            raise CoreCoverageError("inventory_entry_bound_exceeded")
        if len(json.dumps(row, ensure_ascii=False).encode()) > MAX_METADATA_BYTES:
            raise CoreCoverageError("inventory_metadata_bound_exceeded")
        super().append(row)


def _inventory(sources: _Sources):
    rows, blockers = _BoundedRows(), set()

    def unsupported(path, node, reason):
        key = f"{path}:{getattr(node, 'lineno', 0)}:{reason}"
        rows.append(_row("unsupported_source", key, path, syntax_fingerprint=hashlib.sha256(ast.dump(node).encode()).hexdigest()))
        blockers.add(reason)

    def mutations(tree, path, names):
        definitions = {}
        for node in ast.walk(tree):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
            for target in targets:
                base = target
                while isinstance(base, (ast.Subscript, ast.Attribute)):
                    base = base.value
                if isinstance(base, ast.Name) and base.id in names:
                    if isinstance(target, ast.Name) and node in tree.body:
                        definitions[base.id] = definitions.get(base.id, 0) + 1
                        if definitions[base.id] > 1:
                            unsupported(path, node, "registry_rebinding_unsupported")
                    if not isinstance(target, ast.Name) or isinstance(node, ast.AugAssign) or node not in tree.body:
                        unsupported(path, node, "registry_mutation_unsupported")

    registry_path = "apps/api/app/core/router_registry.py"
    registry = sources.tree(registry_path)
    mutations(registry, registry_path, {"ROUTER_SPECS"})
    for node in ast.walk(registry):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "ROUTER_SPECS":
            unsupported(registry_path, node, "dynamic_router_registry_unsupported")
    specs = _assignment(registry, "ROUTER_SPECS")
    registrations = []
    if not isinstance(specs, (ast.Tuple, ast.List)):
        unsupported(registry_path, specs, "router_registration_shape_unsupported")
    else:
        for index, node in enumerate(specs.elts):
            try:
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "RouterSpec":
                    raise ValueError()
                if len(node.args) != 1:
                    raise ValueError()
                ref = node.args[0]
                if not isinstance(ref, ast.Attribute) or ref.attr != "router" or not isinstance(ref.value, ast.Name):
                    raise ValueError()
                values = {kw.arg: _literal(kw.value) for kw in node.keywords}
                feature, prefix = values["feature"], values.get("prefix") or ""
                if not isinstance(feature, str) or not feature or not isinstance(prefix, str):
                    raise ValueError()
                registrations.append((index, ref.value.id, feature, prefix))
                rows.append(_row("registration", str(index), registry_path, module=ref.value.id, feature=feature, prefix=prefix))
            except (ValueError, TypeError, KeyError, IndexError):
                unsupported(registry_path, node, "router_registration_expression_unsupported")

    def routes(module, feature, outer_prefix, registration, ancestry=()):
        path = f"apps/api/app/routers/{module}.py"
        if module in ancestry or len(ancestry) > 8:
            raise CoreCoverageError("nested_router_cycle_or_depth_exceeded")
        tree = sources.tree(path)
        imported = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.routers."):
                for alias in node.names:
                    if alias.name == "router":
                        imported[alias.asname or alias.name] = node.module.rsplit(".", 1)[1]
        try:
            router = _assignment(tree, "router")
            if not isinstance(router, ast.Call) or not isinstance(router.func, ast.Name) or router.func.id != "APIRouter":
                raise ValueError()
            prefix_node = next((kw.value for kw in router.keywords if kw.arg == "prefix"), ast.Constant(""))
            prefix = _literal(prefix_node)
            if not isinstance(prefix, str):
                raise ValueError()
        except (ValueError, TypeError):
            unsupported(path, router, "router_prefix_unsupported")
            return
        scan(tree, path, "router", feature, outer_prefix + prefix, registration)
        decorators = {id(dec) for fn in ast.walk(tree) if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) for dec in fn.decorator_list}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "router":
                if node.func.attr == "include_router":
                    if not any(isinstance(statement, ast.Expr) and statement.value is node for statement in tree.body):
                        unsupported(path, node, "conditional_or_nested_include_unsupported")
                    try:
                        child = imported[node.args[0].id]
                        if len(node.args) != 1 or any(kw.arg not in {"prefix", "tags"} for kw in node.keywords):
                            raise ValueError()
                        child_prefix = next((_literal(kw.value) for kw in node.keywords if kw.arg == "prefix"), "")
                        if not isinstance(child_prefix, str):
                            raise ValueError()
                        routes(child, feature, outer_prefix + prefix + child_prefix, registration, ancestry + (module,))
                    except (KeyError, IndexError, AttributeError, ValueError, TypeError):
                        unsupported(path, node, "nested_router_expression_unsupported")
                elif node.func.attr.startswith("add_"):
                    unsupported(path, node, "dynamic_router_registration_unsupported")
                elif node.func.attr in {"get", "post", "put", "patch", "delete", "head", "options", "route", "api_route", "websocket"} and id(node) not in decorators:
                    unsupported(path, node, "dynamic_router_registration_unsupported")

    def scan(tree, path, receiver, feature, prefix, registration):
        receiver_aliases = {target.id for statement in ast.walk(tree) if isinstance(statement, ast.Assign)
                            and isinstance(statement.value, ast.Name) and statement.value.id == receiver
                            for target in statement.targets if isinstance(target, ast.Name)}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute) or not isinstance(decorator.func.value, ast.Name):
                    continue
                if decorator.func.value.id in receiver_aliases:
                    unsupported(path, decorator, "route_receiver_alias_unsupported")
                    continue
                if decorator.func.value.id != receiver:
                    continue
                if node not in tree.body:
                    unsupported(path, decorator, "conditional_or_nested_route_unsupported")
                try:
                    method = decorator.func.attr.upper()
                    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                        raise ValueError()
                    route_path = _literal(decorator.args[0])
                    if not isinstance(route_path, str) or (route_path and not route_path.startswith("/")):
                        raise ValueError()
                    full_path = prefix + route_path
                    if not full_path.startswith("/"):
                        raise ValueError()
                    family, dependency = FEATURE_PROBE_FAMILIES.get(feature, (None, None))
                    rows.append(_row("api_operation", f"{registration}:{method}:{full_path}", f"{path}::{node.name}",
                                     feature=feature, method=method, path=full_path, probe_family=family, dependency_owner=dependency))
                    if family is None:
                        blockers.add("api_probe_family_unmapped")
                except (ValueError, TypeError, IndexError):
                    unsupported(path, decorator, "route_decorator_expression_unsupported")

    for index, module, feature, prefix in registrations:
        routes(module, feature, prefix, index)
    main_path = "apps/api/app/main.py"
    main_tree = sources.tree(main_path)
    scan(main_tree, main_path, "app", "system", "", "main")
    main_decorators = {id(dec) for fn in ast.walk(main_tree) if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) for dec in fn.decorator_list}
    for node in ast.walk(main_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "app" and (node.func.attr in {"include_router", "add_api_route", "add_route", "mount"} or (node.func.attr in {"get", "post", "put", "patch", "delete", "head", "options", "route", "api_route", "websocket"} and id(node) not in main_decorators)):
            unsupported(main_path, node, "main_dynamic_registration_unsupported")
    for path in sorted(sources.files):
        if path.startswith("apps/web/next.config."):
            sources.read(path)
            rows.append(_row("frontend_configuration", path, path))
            blockers.add("frontend_configuration_semantics_unobserved")
        if (path.startswith("apps/web/app/") and Path(path).name.startswith("route.")) or path.startswith("apps/web/pages/"):
            sources.read(path)
            rows.append(_row("frontend_unhandled_route_source", path, path))
            blockers.add("frontend_route_source_unsupported")
        if path.startswith("apps/web/app/") and Path(path).name.startswith("page."):
            sources.read(path)
            relative = path[len("apps/web/app/"):].rsplit("/", 1)[0] if "/" in path[len("apps/web/app/"):] else ""
            route = "/" + relative
            family = FRONTEND_PROBE_FAMILIES.get(route)
            rows.append(_row("frontend_page", route, path, probe_family=family))
            if family is None:
                blockers.add("frontend_probe_family_unmapped")
            if any(mark in relative for mark in ("(", ")", "@", "[[", "...")):
                blockers.add("frontend_route_shape_unsupported")
            if Path(path).name not in {"page.tsx", "page.ts", "page.jsx", "page.js"}:
                blockers.add("frontend_page_extension_unsupported")

    agent_path = "apps/api/app/agents/registry.py"
    agent_tree = sources.tree(agent_path)
    mutations(agent_tree, agent_path, {"CONTROLLED_AGENT_REGISTRY", "AGENT_ALIASES", "AGENT_REGISTRY"})
    for node in ast.walk(agent_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in {"CONTROLLED_AGENT_REGISTRY", "AGENT_ALIASES", "AGENT_REGISTRY"} and node.func.attr not in {"items", "keys", "values", "get"}:
            unsupported(agent_path, node, "dynamic_agent_registry_unsupported")
    agents = _assignment(agent_tree, "CONTROLLED_AGENT_REGISTRY")
    if not isinstance(agents, ast.Dict):
        unsupported(agent_path, agents, "agent_registry_shape_unsupported")
    else:
        for key, value in zip(agents.keys, agents.values):
            try:
                name = _literal(key)
                if not isinstance(name, str) or not isinstance(value, ast.Dict):
                    raise ValueError()
                fields = {_literal(k): v for k, v in zip(value.keys, value.values)}
                metadata = {field: _literal(fields[field]) for field in ("version", "department")}
                if not all(isinstance(item, str) for item in metadata.values()):
                    raise ValueError()
                rows.append(_row("controlled_agent", name, agent_path, **metadata, probe_family="internal_agent_review"))
            except (ValueError, TypeError, KeyError):
                unsupported(agent_path, value, "agent_registry_expression_unsupported")
    try:
        agent_aliases = _literal(_assignment(agent_tree, "AGENT_ALIASES"))
        if not isinstance(agent_aliases, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in agent_aliases.items()):
            raise ValueError()
        names = {row["key"] for row in rows if row["kind"] == "controlled_agent"}
        for alias, target in sorted(agent_aliases.items()):
            rows.append(_row("agent_alias", alias, agent_path, canonical_agent=target))
            if target not in names:
                blockers.add("agent_alias_target_unavailable")
    except (ValueError, TypeError):
        unsupported(agent_path, agent_tree, "agent_alias_expression_unsupported")

    department_path = "apps/api/app/services/department_runtime.py"
    tree = sources.tree(department_path)
    mutations(tree, department_path, {"DEPARTMENT_RUNTIMES"})
    spec_class = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DepartmentRuntimeSpec"), None)
    default_actions = None
    if spec_class is not None:
        default_actions = next((node.value for node in spec_class.body if isinstance(node, ast.AnnAssign)
                                and isinstance(node.target, ast.Name) and node.target.id == "allowed_actions"), None)
    departments = _assignment(tree, "DEPARTMENT_RUNTIMES")
    if not isinstance(departments, ast.Dict):
        unsupported(department_path, departments, "department_registry_shape_unsupported")
    else:
        for key, value in zip(departments.keys, departments.values):
            try:
                name = _literal(key)
                if not isinstance(name, str) or not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name) or value.func.id != "DepartmentRuntimeSpec":
                    raise ValueError()
                if len(value.args) > 2:
                    raise ValueError()
                actions = next((kw.value for kw in value.keywords if kw.arg == "allowed_actions"), default_actions)
                if actions is None:
                    raise ValueError()
                if isinstance(actions, ast.Name):
                    actions = _assignment(tree, actions.id)
                if isinstance(actions, ast.Constant) and actions.value is None:
                    declared = "general_runtime"
                    action_names = None
                elif isinstance(actions, ast.Call) and isinstance(actions.func, ast.Name) and actions.func.id == "frozenset":
                    action_names = sorted(_literal(actions.args[0])) if actions.args else []
                    if not all(isinstance(action, str) for action in action_names):
                        raise ValueError()
                    declared = "bounded_actions" if action_names else "held_by_source_declaration"
                else:
                    raise ValueError()
                rows.append(_row("department_runtime", name, department_path, declared_posture=declared,
                                 declared_actions=action_names, disabled_verified=False, probe_family="scheduled_internal_work"))
            except (ValueError, TypeError):
                unsupported(department_path, value, "department_runtime_expression_unsupported")
    if time.monotonic() >= sources.deadline:
        raise CoreCoverageError("inventory_deadline_exceeded")
    rows.sort(key=lambda row: (row["kind"], row["key"], row["owner"]))
    if len(rows) > MAX_ENTRIES:
        raise CoreCoverageError("inventory_entry_bound_exceeded")
    aliases = [list(pair) for pair in sorted(EXPLICIT_REGISTRATION_ALIASES)
               if all(any(item[2] == feature for item in registrations) for feature in pair)]
    return rows, sorted(blockers), aliases


def project_core_journey_source_coverage(session: Session, context: OrganizationCommandContext, *,
                                        deployment_run_id: UUID, candidate_root: Path) -> dict:
    """Trusted Python read helper; source-only, with caller pending state unflushed."""
    require_human(context)
    with session.no_autoflush:
        return _project(session, context, deployment_run_id=deployment_run_id, candidate_root=candidate_root)


def _project(session, context, *, deployment_run_id, candidate_root):
    run, _ = validated_deployment_networking_contract(session, context, deployment_run_id=deployment_run_id)
    root = Path(candidate_root)
    before = _identity(root)
    if before != run.release_commit_sha:
        raise CoreCoverageError("candidate_release_mismatch")
    sources = _Sources(root, before)
    configuration = [{"path": path, "sha256": hashlib.sha256(sources.read(path)).hexdigest()}
                     for path in sorted(set(RELEASE_CONFIGURATION_PATHS))]
    configuration_fp = canonical_fingerprint({"contract": RELEASE_IDENTITY_CONTRACT, "files": configuration})
    if configuration_fp != run.release_configuration_fingerprint:
        raise CoreCoverageError("candidate_configuration_mismatch")
    rows, blockers, aliases = _inventory(sources)
    if _identity(root) != before:
        raise CoreCoverageError("candidate_changed_during_inventory")
    payload = {"contract": CORE_COVERAGE_CONTRACT, "release_commit_sha": before,
               "management_contract_fingerprint": canonical_fingerprint({
                   "contract": CORE_COVERAGE_CONTRACT, "feature_probe_families": FEATURE_PROBE_FAMILIES,
                   "frontend_probe_families": FRONTEND_PROBE_FAMILIES,
                   "explicit_registration_aliases": sorted(EXPLICIT_REGISTRATION_ALIASES),
                   "foundation_blockers": FOUNDATION_BLOCKERS,
               }),
               "release_configuration_fingerprint": configuration_fp, "entries": rows,
               "source_manifest": sorted(sources.manifest.items()), "explicit_registration_aliases": aliases}
    if len(json.dumps(payload, ensure_ascii=False).encode()) > MAX_REPORT_BYTES:
        raise CoreCoverageError("inventory_report_bound_exceeded")
    return {**payload, "inventory_fingerprint": canonical_fingerprint(payload),
            "deployment_run_id": str(run.id), "tenant_key": run.tenant_key,
            "core_journey_status": "blocked", "core_journey_satisfied": False,
            "receipt_written": False, "live_observation": False,
            "blockers": sorted(set(FOUNDATION_BLOCKERS) | set(blockers))}
