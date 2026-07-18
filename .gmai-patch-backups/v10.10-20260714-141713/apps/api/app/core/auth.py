from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Iterable, Optional, Set

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.core.config import settings


ROLES = {"admin", "operator", "reviewer", "sales", "read_only"}
READ_ROLES = frozenset(ROLES)
DEFAULT_MUTATION_ROLES = {"admin", "operator"}


@dataclass(frozen=True)
class AuthContext:
    username: str
    role: str
    source: str


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _signature(payload: str) -> str:
    secret = settings.jwt_secret.encode("utf-8")
    return hmac.new(secret, payload.encode("ascii"), hashlib.sha256).hexdigest()


def create_session_token(username: str, role: str) -> str:
    role = normalize_role(role) or "read_only"
    payload = _b64encode(json.dumps(
        {"username": username, "role": role},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8"))
    return f"{payload}.{_signature(payload)}"


def parse_session_token(token: str) -> Optional[AuthContext]:
    try:
        payload, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _signature(payload)):
        return None
    try:
        data = json.loads(_b64decode(payload).decode("utf-8"))
    except Exception:
        return None
    username = str(data.get("username") or "").strip()
    role = normalize_role(data.get("role"))
    if not username or not role:
        return None
    return AuthContext(username=username, role=role, source="cookie")


def normalize_role(value: object) -> Optional[str]:
    role = str(value or "").strip().lower().replace("-", "_")
    return role if role in ROLES else None


def get_auth_context(request: Request) -> Optional[AuthContext]:
    if settings.auth_allow_header_role:
        role = normalize_role(request.headers.get("x-gmai-role"))
        if role:
            username = str(request.headers.get("x-gmai-user") or "local-operator").strip()
            return AuthContext(username=username, role=role, source="header")

    token = request.cookies.get(settings.auth_session_cookie)
    if token:
        return parse_session_token(token)
    return None


def _path_starts(path: str, prefixes: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes)


def is_public_path(path: str) -> bool:
    if path in {"/", "/health", "/favicon.ico", "/openapi.json"}:
        return True
    return _path_starts(
        path,
        ("/auth", "/docs", "/redoc", "/debug", "/api/v1/public"),
    )


def required_roles(method: str, path: str) -> Set[str]:
    method = method.upper()

    if _path_starts(path, ("/api/v1/document-intelligence",)):
        if path.endswith("/review"):
            return {"admin", "reviewer"}
        return {"admin", "operator", "reviewer"}

    if method in {"GET", "HEAD", "OPTIONS"}:
        if path.startswith("/admin") or path.startswith("/api/v1"):
            return set(READ_ROLES)
        return set(READ_ROLES)

    if "reset" in path or "delete" in path:
        return {"admin"}

    if _path_starts(path, ("/api/v1/truth", "/admin/truth-resolution")):
        return {"admin", "reviewer"}

    if _path_starts(path, ("/api/v1/regulatory-intelligence",)):
        return {"admin", "reviewer"}

    if _path_starts(path, ("/api/v1/global-intelligence/registry",)):
        return {"admin", "reviewer"}

    if _path_starts(path, ("/api/v1/document-verification", "/admin/document-verification")):
        return {"admin", "operator", "reviewer"}

    if _path_starts(path, ("/api/v1/sales", "/admin/sales")):
        return {"admin", "operator", "sales"}

    if _path_starts(path, ("/api/v1/operations/reviews",)):
        return {"admin", "reviewer"}

    if _path_starts(path, ("/api/v1/applications", "/admin/applications")):
        if any(marker in path for marker in ("/approve", "/submit")):
            return {"admin", "reviewer"}
        return {"admin", "operator", "reviewer"}

    if _path_starts(path, ("/api/v1/application-draft-control", "/admin/application-draft-control")):
        return {"admin", "operator"}

    if _path_starts(path, ("/api/v1/authority-decision", "/admin/authority-decision")):
        return {"admin", "reviewer"}

    if _path_starts(path, ("/api/v1/post-approval-onboarding", "/admin/post-approval-onboarding")):
        return {"admin", "operator", "reviewer"}

    if _path_starts(path, ("/api/v1/client-communications", "/admin/client-communications")):
        return {"admin", "operator", "reviewer"}

    return set(DEFAULT_MUTATION_ROLES)


def unauthorized_response(path: str) -> Response:
    if path.startswith("/admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Authentication required.",
            "login_url": "/auth/login",
        },
    )


def forbidden_response(role: str, allowed_roles: Set[str]) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "detail": "Role is not allowed for this action.",
            "role": role,
            "allowed_roles": sorted(allowed_roles),
        },
    )


async def auth_middleware(request: Request, call_next):
    # Allow browser CORS preflight requests. Real requests still require auth.
    if request.method.upper() == "OPTIONS":
        return await call_next(request)

    if not settings.auth_enabled or is_public_path(request.url.path):
        return await call_next(request)

    context = get_auth_context(request)
    if context is None:
        return unauthorized_response(request.url.path)

    allowed_roles = required_roles(request.method, request.url.path)
    if context.role not in allowed_roles:
        return forbidden_response(context.role, allowed_roles)

    request.state.auth = context
    return await call_next(request)

