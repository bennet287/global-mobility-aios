from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

ROLES = frozenset({"admin", "operator", "reviewer", "sales", "read_only"})
READ_ROLES = ROLES
DEFAULT_MUTATION_ROLES = frozenset({"admin", "operator"})
READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

PUBLIC_EXACT_PATHS = frozenset({"/", "/health", "/favicon.ico", "/openapi.json"})
PUBLIC_PREFIXES = (
    "/auth",
    "/docs",
    "/redoc",
    "/debug",
    "/api/v1/public",
    "/api/public/v1",
    "/api/partner/v1",
)


def path_starts(path: str, prefixes: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes)


def is_public_path(path: str) -> bool:
    return path in PUBLIC_EXACT_PATHS or path_starts(path, PUBLIC_PREFIXES)


@dataclass(frozen=True)
class PathRoleRule:
    """Ordered declarative authorization rule.

    Rules are intentionally simple and deterministic. More-specific rules must
    appear before broader rules so route policy can be audited as data instead
    of growing another hand-written if/elif cascade.
    """

    roles: frozenset[str]
    prefixes: tuple[str, ...] = ()
    methods: frozenset[str] | None = None
    suffixes: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()
    contains_any: tuple[str, ...] = ()

    def matches(self, method: str, path: str) -> bool:
        if self.methods is not None and method not in self.methods:
            return False
        if self.prefixes and not path_starts(path, self.prefixes):
            return False
        if self.suffixes and not any(path.endswith(suffix) for suffix in self.suffixes):
            return False
        if self.contains and not all(marker in path for marker in self.contains):
            return False
        if self.contains_any and not any(marker in path for marker in self.contains_any):
            return False
        return True


AUTH_RULES: tuple[PathRoleRule, ...] = (
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/pathways",),
        methods=frozenset({"POST"}),
        contains_any=("/match/", "/compare/"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/eligibility/evaluate",),
        methods=frozenset({"POST"}),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/document-intelligence",),
        suffixes=("/review",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/document-intelligence",),
    ),
    PathRoleRule(
        roles=READ_ROLES,
        prefixes=("/api/v1/document-access",),
        suffixes=("/content",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/document-access",),
    ),
    PathRoleRule(roles=READ_ROLES, methods=READ_METHODS),
    PathRoleRule(
        roles=frozenset({"admin"}),
        prefixes=("/api/v1/external-validation",),
        contains=("/board-acceptance",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/external-validation",),
        contains_any=("/reviews", "/findings"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator"}),
        prefixes=("/api/v1/external-validation",),
    ),
    PathRoleRule(roles=frozenset({"admin"}), contains_any=("reset", "delete")),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/truth", "/admin/truth-resolution"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/regulatory-intelligence",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/global-intelligence/registry",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/document-verification", "/admin/document-verification"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "sales"}),
        prefixes=("/api/v1/sales", "/admin/sales"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/operations/reviews",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/applications", "/admin/applications"),
        contains_any=("/approve", "/submit"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/applications", "/admin/applications"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator"}),
        prefixes=("/api/v1/application-draft-control", "/admin/application-draft-control"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/authority-decision", "/admin/authority-decision"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/post-approval-onboarding", "/admin/post-approval-onboarding"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator", "reviewer"}),
        prefixes=("/api/v1/client-communications", "/admin/client-communications"),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "reviewer"}),
        prefixes=("/api/v1/automation",),
        contains=("/decision",),
    ),
    PathRoleRule(
        roles=frozenset({"admin", "operator"}),
        prefixes=("/api/v1/automation",),
    ),
)


def required_roles(method: str, path: str) -> set[str]:
    normalized_method = method.upper()
    for rule in AUTH_RULES:
        if rule.matches(normalized_method, path):
            return set(rule.roles)
    return set(DEFAULT_MUTATION_ROLES)
