from __future__ import annotations

import json
from pathlib import Path

from labs.r3.authority.deep_opa import _base_request


ROOT = Path("labs/r3/authority")


def test_openfga_deep_model_exercises_relationship_features() -> None:
    model = json.loads((ROOT / "openfga" / "deep_model.json").read_text(encoding="utf-8"))
    by_type = {item["type"]: item for item in model["type_definitions"]}

    assert {"agent", "position", "team", "case", "tool"} <= set(by_type)

    team_member_types = by_type["team"]["metadata"]["relations"]["member"][
        "directly_related_user_types"
    ]
    assert {"type": "position", "relation": "assignee"} in team_member_types
    assert {"type": "team", "relation": "member"} in team_member_types

    case_relations = by_type["case"]["relations"]
    assert "union" in case_relations["can_read"]
    assert "computedUserset" in case_relations["can_write"]

    tool_relations = by_type["tool"]["relations"]
    assert tool_relations["can_discover"]["computedUserset"]["relation"] == "can_call"


def test_opa_deep_policy_uses_external_canonical_data() -> None:
    policy = (ROOT / "opa" / "deep_authority.rego").read_text(encoding="utf-8")

    assert "data.aios" in policy
    assert "authority-data-v1" not in policy
    assert "canonical_actions :=" not in policy
    assert "metadata.authority_required" in policy
    assert "metadata.human_approval_required" in policy


def test_opa_deep_data_declares_high_risk_submission_requirements() -> None:
    document = json.loads((ROOT / "opa" / "deep_data.json").read_text(encoding="utf-8"))
    submission = document["aios"]["actions"]["government_application.submit"]

    assert submission["authority_required"] is True
    assert submission["human_approval_required"] is True
    assert submission["required_jurisdiction"] == "AT"


def test_deep_opa_request_does_not_carry_caller_policy_flags() -> None:
    request = _base_request("government_application.submit")

    assert "authority_required" not in request["context"]
    assert "human_approval_required" not in request["context"]
    assert "required_jurisdiction" not in request["context"]
    assert request["context"]["authority_present"] is True
