from __future__ import annotations

import html
import secrets
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.auth import ROLES, create_session_token, get_auth_context, normalize_role
from app.core.config import settings


router = APIRouter(tags=["auth-roles-v3.1"])


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 2rem; color: #172033; }}
      main {{ max-width: 520px; }}
      label {{ display: block; margin: 1rem 0 .35rem; font-weight: 700; }}
      input, select {{ width: 100%; padding: .65rem; border: 1px solid #c9d2e3; border-radius: 6px; }}
      button {{ margin-top: 1rem; padding: .65rem 1rem; border: 0; border-radius: 6px; background: #1f5fbf; color: white; cursor: pointer; }}
      .muted {{ color: #667085; }}
      .error {{ color: #b42318; font-weight: 700; }}
      code {{ background: #f2f4f7; padding: .1rem .3rem; border-radius: 4px; }}
      nav a {{ margin-right: .75rem; }}
    </style>
  </head>
  <body><main>{body}</main></body>
</html>
""")


@router.get("/auth/login", response_class=HTMLResponse)
def login_page(error: str = "") -> HTMLResponse:
    error_html = f"<p class='error'>{html.escape(error)}</p>" if error else ""
    roles = "".join(f"<option value='{role}'>{role}</option>" for role in sorted(ROLES))
    return _page("Global Mobility AIOS Login", f"""
      <h1>Global Mobility AIOS Login</h1>
      <p class="muted">Local v3.1 operator login. Use environment variables before sharing this beyond your machine.</p>
      {error_html}
      <form method="post" action="/auth/login">
        <label for="username">Username</label>
        <input id="username" name="username" autocomplete="username" value="{html.escape(settings.auth_admin_username)}" />
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" />
        <label for="role">Role</label>
        <select id="role" name="role">{roles}</select>
        <button type="submit">Sign in</button>
      </form>
      <p class="muted">Default local credentials are <code>admin</code> / <code>admin</code> unless changed in <code>.env</code>.</p>
    """)


@router.post("/auth/login")
async def login(request: Request):
    form = parse_qs((await request.body()).decode("utf-8"))
    username = str(form.get("username", [""])[0]).strip()
    password = str(form.get("password", [""])[0])
    role = normalize_role(form.get("role", ["admin"])[0]) or "admin"

    valid_username = secrets.compare_digest(username, settings.auth_admin_username)
    valid_password = secrets.compare_digest(password, settings.auth_admin_password)
    if not valid_username or not valid_password:
        return login_page("Invalid username or password.")

    response = RedirectResponse(url="/admin/v2", status_code=303)
    response.set_cookie(
        settings.auth_session_cookie,
        create_session_token(username=username, role=role),
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/auth/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(settings.auth_session_cookie)
    return response


@router.get("/auth/me")
def me(request: Request):
    context = get_auth_context(request)
    if context is None:
        return JSONResponse(status_code=401, content={"authenticated": False})
    return {
        "authenticated": True,
        "username": context.username,
        "role": context.role,
        "source": context.source,
        "auth_enabled": settings.auth_enabled,
    }


@router.get("/admin/auth", response_class=HTMLResponse)
def admin_auth_status(request: Request) -> HTMLResponse:
    context = get_auth_context(request)
    if context is None:
        return RedirectResponse(url="/auth/login", status_code=303)
    return _page("Auth Status", f"""
      <nav><a href="/admin/v2">Admin v2</a><a href="/admin/audit-logs">Audit Logs</a></nav>
      <h1>Auth Status</h1>
      <p><strong>User:</strong> {html.escape(context.username)}</p>
      <p><strong>Role:</strong> {html.escape(context.role)}</p>
      <p><strong>Source:</strong> {html.escape(context.source)}</p>
      <form method="post" action="/auth/logout"><button type="submit">Sign out</button></form>
    """)
