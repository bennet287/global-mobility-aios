from __future__ import annotations

from labs.r3.authority.opa_bundle_lab import POLICY, SIGNING_SECRET


def test_signed_bundle_fixture_has_no_canonical_side_effect_code() -> None:
    assert "AuthorityGrant" not in POLICY
    assert "VerifiedRule" not in POLICY
    assert SIGNING_SECRET.startswith("gmai-r3-")
