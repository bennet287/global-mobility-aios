# Authentication and Roles v3.1

This milestone adds a local authentication and role guardrail layer for the operator dashboard and workflow APIs.

## Scope

- Signed-cookie browser login at `/auth/login`.
- Local header auth for tests and trusted scripts through `X-GMAI-Role` and `X-GMAI-User`.
- Middleware-level role checks for admin pages and mutating workflow API routes.
- Auth status page at `/admin/auth`.
- Regression tests for unauthenticated access, read-only blocking, reviewer access, sales blocking, and login cookies.

## Roles

| Role | Intended use |
|---|---|
| `admin` | Full local operator control. |
| `operator` | Day-to-day workflow operations. |
| `reviewer` | Truth, document, application, authority, onboarding, and communication review actions. |
| `sales` | Sales workflow actions only. |
| `read_only` | View dashboards and API reads without mutating records. |

## Default Local Login

The local defaults are:

```text
username: admin
password: admin
```

Change these in `.env` before sharing the app beyond your local machine:

```text
AUTH_ADMIN_USERNAME=admin
AUTH_ADMIN_PASSWORD=change-this
JWT_SECRET=change-this-to-a-long-random-secret
```

## Local Script/Test Headers

Trusted local scripts and pytest use:

```text
X-GMAI-Role: admin
X-GMAI-User: local-operator
```

Allowed roles are:

```text
admin
operator
reviewer
sales
read_only
```

Header auth can be disabled with:

```text
AUTH_ALLOW_HEADER_ROLE=false
```

## Permission Summary

| Action | Admin | Operator | Reviewer | Sales | Read-only |
|---|---:|---:|---:|---:|---:|
| View admin/API reads | Yes | Yes | Yes | Yes | Yes |
| Resolve truth claims | Yes | No | Yes | No | No |
| Verify documents | Yes | Yes | Yes | No | No |
| Sales workflow actions | Yes | Yes | No | Yes | No |
| Approve/submit applications | Yes | No | Yes | No | No |
| Record authority decisions | Yes | No | Yes | No | No |
| Complete onboarding tasks | Yes | Yes | Yes | No | No |
| Review client drafts | Yes | Yes | Yes | No | No |
| Delete/reset actions | Yes | No | No | No | No |

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py
python scripts/check_repo_policy.py --root .
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected result after this milestone:

```text
All tests pass.
Repository policy check passed.
```

## Notes

This is intentionally not Keycloak/Auth0 production auth. It is a local MVP guardrail that prevents accidental dashboard/API mutation by unauthenticated or read-only users while preserving the current local development workflow.
