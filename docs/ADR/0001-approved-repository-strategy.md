# ADR 0001: Approved Repository Strategy

- Status: Accepted
- Date: 2026-07-06
- Owners: Product, Engineering, Security

## Context

Global Mobility AIOS must remain buildable, legally safe, and production-focused.
Uncontrolled dependency intake from unrelated repositories creates legal, operational,
and security risk.

## Decision

Adopt a controlled repository strategy with three groups:

1. Approved core repositories for direct product build.
2. Adapted repositories with constrained scope.
3. Reference-only repositories with no direct production dependency.

All non-allowlisted repositories are denied by default until architecture and legal review.

Machine enforcement is required in CI via:

- scripts/check_repo_policy.py
- .github/workflows/repo-policy-check.yml

## Consequences

Positive:

- Tighter legal and licensing control.
- Clear contributor boundaries.
- Lower supply-chain and maintenance risk.
- Auditable dependency decisions.

Trade-offs:

- Slower onboarding for new dependencies due to review gate.
- Requires ongoing maintenance of allowlist documents.

## References

- docs/REPOSITORY_POLICY.md
- docs/SECURITY_AND_COMPLIANCE.md
- docs/ARCHITECTURE.md
