from __future__ import annotations

import inspect

from labs.r3.sandbox.microsandbox_lab import run_microsandbox


def test_microsandbox_runner_is_async_real_candidate() -> None:
    assert inspect.iscoroutinefunction(run_microsandbox)


def test_sandbox_lab_does_not_contain_product_authority_mutation() -> None:
    source = inspect.getsource(run_microsandbox)
    assert "AuthorityGrant" not in source
    assert "VerifiedRule" not in source
