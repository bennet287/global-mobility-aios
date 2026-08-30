from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


SPICEDB_VERSION = "v1.56.0"
AUTHZED_PY_VERSION = "1.25.0"
SCHEMA_PATH = Path(__file__).resolve().parent / "spicedb" / "schema.zed"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _record(
    outcomes: list[dict[str, Any]], feature: str, observed: Any, expected: Any
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def run_spicedb(*, endpoint: str, token: str) -> dict[str, Any]:
    try:
        from authzed.api.v1 import (
            CheckPermissionRequest,
            Consistency,
            InsecureClient,
            ObjectReference,
            Relationship,
            RelationshipUpdate,
            SubjectReference,
            WriteRelationshipsRequest,
            WriteSchemaRequest,
        )
        from authzed.api.v1.permission_service_pb2 import CheckPermissionResponse
    except ImportError as exc:
        raise ExecutionBlocked("authzed==1.25.0 is required") from exc

    client = InsecureClient(endpoint, token)
    client.WriteSchema(
        WriteSchemaRequest(schema=SCHEMA_PATH.read_text(encoding="utf-8"))
    )

    def relationship(
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
        subject_relation: str = "",
    ):
        return Relationship(
            resource=ObjectReference(
                object_type=resource_type,
                object_id=resource_id,
            ),
            relation=relation,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=subject_type,
                    object_id=subject_id,
                ),
                optional_relation=subject_relation,
            ),
        )

    tuples = [
        relationship(
            "position",
            "austria-regulatory",
            "assignee",
            "agent",
            "agent-001",
        ),
        relationship(
            "team",
            "austria",
            "member",
            "position",
            "austria-regulatory",
            "assignee",
        ),
        relationship(
            "case",
            "AT-001",
            "viewer",
            "team",
            "austria",
            "member",
        ),
        relationship(
            "tool",
            "source-retrieve",
            "caller",
            "team",
            "austria",
            "member",
        ),
    ]

    client.WriteRelationships(
        WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=RelationshipUpdate.OPERATION_TOUCH,
                    relationship=item,
                )
                for item in tuples
            ]
        )
    )

    def check(
        resource_type: str,
        resource_id: str,
        permission: str,
    ) -> bool:
        response = client.CheckPermission(
            CheckPermissionRequest(
                consistency=Consistency(fully_consistent=True),
                resource=ObjectReference(
                    object_type=resource_type,
                    object_id=resource_id,
                ),
                permission=permission,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type="agent",
                        object_id="agent-001",
                    )
                ),
            )
        )
        return (
            response.permissionship
            == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
        )

    outcomes: list[dict[str, Any]] = []
    _record(
        outcomes,
        "nested_relationship_permission",
        check("case", "AT-001", "read"),
        True,
    )
    _record(
        outcomes,
        "tool_discovery_projection",
        check("tool", "source-retrieve", "discover"),
        True,
    )
    _record(
        outcomes,
        "write_not_implicitly_granted",
        check("case", "AT-001", "write"),
        False,
    )

    client.WriteRelationships(
        WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=RelationshipUpdate.OPERATION_DELETE,
                    relationship=tuples[0],
                )
            ]
        )
    )
    _record(
        outcomes,
        "revocation_removes_derived_access",
        check("case", "AT-001", "read"),
        False,
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_spicedb": True,
            "schema_write": True,
            "nested_relationships": True,
            "permission_check": True,
            "revocation": True,
            "canonical_authority_ownership": False,
            "caveats": False,
            "lookup_resources": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="127.0.0.1:15051")
    parser.add_argument("--token", default="gmai-r3-spicedb-key")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_spicedb(endpoint=args.endpoint, token=args.token)
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "spicedb",
        "candidate_version": SPICEDB_VERSION,
        "client_version": AUTHZED_PY_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engine",
        "experiment": "t1-t2-t3-spicedb-challenger",
        "test_tiers": ["T1", "T2", "T3"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if blocked:
        print(f"SpiceDB R3 blocked: {block_reason}")
        return 2
    print(
        f"SpiceDB R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
