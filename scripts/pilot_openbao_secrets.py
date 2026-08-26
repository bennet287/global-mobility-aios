from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.secrets_port import (  # noqa: E402
    OpenBaoSecretsPort,
    SecretMaterial,
    SecretReference,
    SecretsPortError,
)


def _build_port() -> OpenBaoSecretsPort:
    return OpenBaoSecretsPort(
        address=settings.openbao_addr,
        token=settings.openbao_token.get_secret_value(),
        mount=settings.openbao_kv_mount,
        path_prefix=settings.openbao_pilot_path_prefix,
        allowed_environment="pilot",
        namespace=settings.openbao_namespace,
        timeout_seconds=settings.openbao_timeout_seconds,
    )


def configuration_report() -> dict[str, object]:
    configured = settings.secrets_backend.strip().lower() == "openbao"
    valid = False
    reason = "SECRETS_BACKEND is not openbao"
    if configured:
        try:
            port = _build_port()
            port.close()
            valid = True
            reason = "configuration contract is valid"
        except (ValueError, SecretsPortError) as exc:
            reason = str(exc)
    return {
        "backend": settings.secrets_backend.strip().lower() or "not_configured",
        "address_configured": bool(settings.openbao_addr.strip()),
        "token_configured": bool(settings.openbao_token.get_secret_value()),
        "environment": "pilot",
        "configuration_valid": valid,
        "pilot_ready": configured and valid,
        "reason": reason,
        "secret_values_exposed": False,
        "production_adoption": False,
    }


def execute_lifecycle(*, name: str) -> dict[str, object]:
    reference = SecretReference(environment="pilot", name=name)
    first_value = secrets.token_urlsafe(24)
    rotated_value = secrets.token_urlsafe(24)
    port = _build_port()
    created = False
    try:
        first_version = port.write(
            reference,
            SecretMaterial({"sentinel": first_value}),
            expected_version=0,
        )
        created = True
        first = port.read(reference, version=first_version)
        if first.material.reveal()["sentinel"] != first_value:
            raise SecretsPortError("OpenBao initial retrieval did not match the generated sentinel")

        rotated_version = port.write(
            reference,
            SecretMaterial({"sentinel": rotated_value}),
            expected_version=first_version,
        )
        rotated = port.read(reference, version=rotated_version)
        if rotated.material.reveal()["sentinel"] != rotated_value:
            raise SecretsPortError("OpenBao rotated retrieval did not match the generated sentinel")

        port.soft_delete(reference, versions=(rotated_version,))
        port.undelete(reference, versions=(rotated_version,))
        recovered = port.read(reference, version=rotated_version)
        if recovered.material.reveal()["sentinel"] != rotated_value:
            raise SecretsPortError("OpenBao recovered retrieval did not match the generated sentinel")
        return {
            "schema_version": "gmai-openbao-pilot-receipt-v1",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "reference": f"pilot/{name}",
            "initial_version": first_version,
            "rotated_version": rotated_version,
            "retrieval_verified": True,
            "cas_rotation_verified": True,
            "soft_delete_undelete_recovery_verified": True,
            "secret_values_exposed": False,
            "production_adoption": False,
        }
    finally:
        try:
            if created:
                port.delete_metadata(reference)
        finally:
            port.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded non-production OpenBao SecretsPort pilot"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-config", action="store_true")
    mode.add_argument("--run-lifecycle", action="store_true")
    parser.add_argument("--confirm-nonproduction", action="store_true")
    parser.add_argument("--path")
    args = parser.parse_args()

    if args.check_config:
        report = configuration_report()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["pilot_ready"] else 2
    if not args.confirm_nonproduction:
        print("OpenBao pilot refused: --confirm-nonproduction is required")
        return 2
    try:
        pilot_path = args.path or f"e1-sentinel-{secrets.token_hex(6)}"
        print(json.dumps(execute_lifecycle(name=pilot_path), indent=2, sort_keys=True))
        return 0
    except (ValueError, SecretsPortError) as exc:
        print(f"OpenBao pilot failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
