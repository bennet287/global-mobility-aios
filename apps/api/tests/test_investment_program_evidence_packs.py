from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


PACK_ROOT = Path(__file__).resolve().parents[3] / "knowledge" / "investment_mobility" / "tranches"


def _packs() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(PACK_ROOT.glob("*.json"))]


def test_investment_program_evidence_packs_are_fail_closed_and_content_addressed():
    packs = _packs()
    assert packs
    for pack in packs:
        assert pack["review_status"] == "pending_independent_review"
        assert pack["requires_separate_reviewer"] is True
        assert pack["creates_eligibility_claim"] is False
        assert pack["creates_approval_prediction"] is False
        source = pack["source_onboarding"]
        parsed = urlparse(source["source_url"])
        assert parsed.scheme == "https"
        assert any(
            parsed.hostname == domain or parsed.hostname.endswith(f".{domain}")
            for domain in source["allowed_domains"]
        )
        assert source["source_domain"] in {"investment", "business", "wealth", "entrepreneur"}
        snapshot = pack["snapshot_receipt"]
        assert snapshot["http_status"] == 200
        assert re.fullmatch(r"[0-9a-f]{64}", snapshot["content_sha256"])
        serialized = json.dumps(pack).lower()
        assert "guaranteed approval" not in serialized
        assert "100% approval" not in serialized


def test_austria_pack_preserves_threshold_semantics_and_pending_state():
    pack = next(item for item in _packs() if item["jurisdiction"]["code"] == "AT")
    draft = pack["pathway_draft"]
    assert draft["minimum_commitment_minor"] == 10_000_000
    assert draft["currency"] == "EUR"
    assert draft["catalogue_status"] == "draft"
    capital_rule = next(
        item for item in pack["proposed_rules"]
        if item["rule_key"] == "at-self-employed-key-worker-capital-indicator"
    )
    assert "one stated indicator" in capital_rule["statement"]
    assert "not automatic eligibility" in " ".join(draft["material_risks"]).lower()
