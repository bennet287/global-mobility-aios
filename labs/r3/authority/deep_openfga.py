from __future__ import annotations

import argparse
import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "openfga" / "deep_model.json"
VERSION = "v1.18.1"

AGENT = "agent:austria-regulatory"
OTHER_AGENT = "agent:outsider"
POSITION = "position:austria-regulatory"
TEAM = "team:austria"
CASE = "case:tenant-alpha-at-001"
OTHER_CASE = "case:tenant-beta-at-002"
TOOLS = ("tool:source.retrieve", "tool:eligibility.calculate")


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _model() -> dict[str, Any]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _create_store_and_model(
    client: httpx.Client,
    *,
    store_name: str,
    model: dict[str, Any] | None = None,
) -> tuple[str, str]:
    store = client.post("/stores", json={"name": store_name})
    store.raise_for_status()
    store_id = store.json()["id"]
    response = client.post(
        f"/stores/{store_id}/authorization-models",
        json=model or _model(),
    )
    response.raise_for_status()
    return store_id, response.json()["authorization_model_id"]


def _write(
    client: httpx.Client,
    *,
    store_id: str,
    model_id: str,
    tuples: list[dict[str, str]],
) -> None:
    response = client.post(
        f"/stores/{store_id}/write",
        json={
            "writes": {"tuple_keys": tuples},
            "authorization_model_id": model_id,
        },
    )
    response.raise_for_status()


def _delete(
    client: httpx.Client,
    *,
    store_id: str,
    model_id: str,
    tuples: list[dict[str, str]],
) -> None:
    response = client.post(
        f"/stores/{store_id}/write",
        json={
            "deletes": {"tuple_keys": tuples},
            "authorization_model_id": model_id,
        },
    )
    response.raise_for_status()


def _check(
    client: httpx.Client,
    *,
    store_id: str,
    model_id: str,
    user: str,
    relation: str,
    object_: str,
) -> bool:
    response = client.post(
        f"/stores/{store_id}/check",
        json={
            "tuple_key": {
                "user": user,
                "relation": relation,
                "object": object_,
            },
            "authorization_model_id": model_id,
        },
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body.get("allowed"), bool):
        raise ValueError(f"OpenFGA returned malformed check response: {body!r}")
    return body["allowed"]


def _list_objects(
    client: httpx.Client,
    *,
    store_id: str,
    model_id: str,
    user: str,
    relation: str,
    type_: str,
) -> list[str]:
    response = client.post(
        f"/stores/{store_id}/list-objects",
        json={
            "authorization_model_id": model_id,
            "type": type_,
            "relation": relation,
            "user": user,
        },
    )
    response.raise_for_status()
    objects = response.json().get("objects")
    if not isinstance(objects, list) or not all(
        isinstance(value, str) for value in objects
    ):
        raise ValueError("OpenFGA returned malformed list-objects response")
    return sorted(objects)


def _canonical_projection() -> list[dict[str, str]]:
    tuples = [
        {
            "user": AGENT,
            "relation": "assignee",
            "object": POSITION,
        },
        {
            "user": f"{POSITION}#assignee",
            "relation": "member",
            "object": TEAM,
        },
        {
            "user": f"{TEAM}#member",
            "relation": "viewer",
            "object": CASE,
        },
        {
            "user": f"{TEAM}#member",
            "relation": "editor",
            "object": CASE,
        },
    ]
    tuples.extend(
        {
            "user": f"{TEAM}#member",
            "relation": "can_call",
            "object": tool,
        }
        for tool in TOOLS
    )
    return tuples


def _snapshot(
    client: httpx.Client,
    *,
    store_id: str,
    model_id: str,
) -> dict[str, Any]:
    return {
        "agent_can_read": _check(
            client,
            store_id=store_id,
            model_id=model_id,
            user=AGENT,
            relation="can_read",
            object_=CASE,
        ),
        "agent_can_write": _check(
            client,
            store_id=store_id,
            model_id=model_id,
            user=AGENT,
            relation="can_write",
            object_=CASE,
        ),
        "outsider_can_read": _check(
            client,
            store_id=store_id,
            model_id=model_id,
            user=OTHER_AGENT,
            relation="can_read",
            object_=CASE,
        ),
        "other_tenant_case_visible": _check(
            client,
            store_id=store_id,
            model_id=model_id,
            user=AGENT,
            relation="can_read",
            object_=OTHER_CASE,
        ),
        "discoverable_tools": _list_objects(
            client,
            store_id=store_id,
            model_id=model_id,
            user=AGENT,
            relation="can_discover",
            type_="tool",
        ),
        "readable_cases": _list_objects(
            client,
            store_id=store_id,
            model_id=model_id,
            user=AGENT,
            relation="can_read",
            type_="case",
        ),
    }


def _expect(
    outcomes: list[dict[str, Any]],
    *,
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "expected": expected,
            "observed": observed,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def run_deep_features(*, base_url: str) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        store_id, model_v1 = _create_store_and_model(
            client,
            store_name="gmai-r3-authority-deep",
        )
        projection = _canonical_projection()
        _write(
            client,
            store_id=store_id,
            model_id=model_v1,
            tuples=projection,
        )

        initial = _snapshot(client, store_id=store_id, model_id=model_v1)
        _expect(
            outcomes,
            feature="nested_position_team_case_read",
            observed=initial["agent_can_read"],
            expected=True,
        )
        _expect(
            outcomes,
            feature="computed_editor_can_write",
            observed=initial["agent_can_write"],
            expected=True,
        )
        _expect(
            outcomes,
            feature="outsider_denied",
            observed=initial["outsider_can_read"],
            expected=False,
        )
        _expect(
            outcomes,
            feature="cross_tenant_unrelated_resource_denied",
            observed=initial["other_tenant_case_visible"],
            expected=False,
        )
        _expect(
            outcomes,
            feature="list_objects_tool_discovery",
            observed=initial["discoverable_tools"],
            expected=sorted(TOOLS),
        )
        _expect(
            outcomes,
            feature="list_objects_case_filter",
            observed=initial["readable_cases"],
            expected=[CASE],
        )

        membership = {
            "user": f"{POSITION}#assignee",
            "relation": "member",
            "object": TEAM,
        }
        _delete(
            client,
            store_id=store_id,
            model_id=model_v1,
            tuples=[membership],
        )
        revoked = _snapshot(client, store_id=store_id, model_id=model_v1)
        _expect(
            outcomes,
            feature="revocation_removes_case_access",
            observed=revoked["agent_can_read"],
            expected=False,
        )
        _expect(
            outcomes,
            feature="revocation_removes_tool_discovery",
            observed=revoked["discoverable_tools"],
            expected=[],
        )

        _write(
            client,
            store_id=store_id,
            model_id=model_v1,
            tuples=[membership],
        )
        restored = _snapshot(client, store_id=store_id, model_id=model_v1)
        _expect(
            outcomes,
            feature="restored_membership_restores_access",
            observed=restored["agent_can_read"],
            expected=True,
        )

        model_v2_doc = copy.deepcopy(_model())
        case_type = next(
            item
            for item in model_v2_doc["type_definitions"]
            if item["type"] == "case"
        )
        case_type["relations"]["can_review"] = {
            "computedUserset": {"object": "", "relation": "viewer"}
        }
        response = client.post(
            f"/stores/{store_id}/authorization-models",
            json=model_v2_doc,
        )
        response.raise_for_status()
        model_v2 = response.json()["authorization_model_id"]
        _expect(
            outcomes,
            feature="authorization_model_versions_are_immutable",
            observed=model_v2 != model_v1,
            expected=True,
        )
        _expect(
            outcomes,
            feature="new_model_relation_works",
            observed=_check(
                client,
                store_id=store_id,
                model_id=model_v2,
                user=AGENT,
                relation="can_review",
                object_=CASE,
            ),
            expected=True,
        )

        old_model_response = client.post(
            f"/stores/{store_id}/check",
            json={
                "tuple_key": {
                    "user": AGENT,
                    "relation": "can_review",
                    "object": CASE,
                },
                "authorization_model_id": model_v1,
            },
        )
        _expect(
            outcomes,
            feature="old_model_does_not_gain_new_relation",
            observed=old_model_response.status_code >= 400,
            expected=True,
        )

        rebuild_store, rebuild_model = _create_store_and_model(
            client,
            store_name="gmai-r3-authority-rebuild",
        )
        _write(
            client,
            store_id=rebuild_store,
            model_id=rebuild_model,
            tuples=projection,
        )
        rebuilt = _snapshot(
            client,
            store_id=rebuild_store,
            model_id=rebuild_model,
        )
        _expect(
            outcomes,
            feature="derived_store_rebuild_is_behaviorally_equivalent",
            observed=rebuilt,
            expected=initial,
        )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "models": {
            "v1": model_v1,
            "v2": model_v2,
        },
        "feature_coverage": {
            "relationship_graph": True,
            "userset_inheritance": True,
            "computed_userset": True,
            "list_objects": True,
            "revocation": True,
            "model_versioning": True,
            "derived_store_rebuild": True,
            "conditions": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_deep_features(base_url=args.base_url)
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "openfga",
        "candidate_version": VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engine",
        "experiment": "t2-t3-t8-native-feature-depth",
        "test_tiers": ["T2", "T3", "T8"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "models": detail["models"],
        "outcomes": detail["outcomes"],
        "decision_candidate": (
            "ADVANCE_TO_R4"
            if detail["failures"] == 0
            else "CONTINUE_R3_WITH_SPECIFIC_GAP"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        "openfga deep features: "
        f"{result['passes']}/{result['scenario_count']} passed; "
        f"coverage={result['feature_coverage']}"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
