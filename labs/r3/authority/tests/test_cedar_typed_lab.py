from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cedar_typed_assets_exist() -> None:
    assert (ROOT / "cedar" / "schema.cedarschema").is_file()
    assert (ROOT / "cedar" / "typed_policy.cedar").is_file()
    assert (ROOT / "cedar" / "typed_entities.json").is_file()


def test_cedar_policy_contains_explicit_forbid() -> None:
    text = (ROOT / "cedar" / "typed_policy.cedar").read_text(encoding="utf-8")
    assert "forbid" in text
    assert "humanApproved" in text
    assert "authorityPresent" in text
