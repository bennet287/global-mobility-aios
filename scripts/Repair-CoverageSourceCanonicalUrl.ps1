[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ [guid]::TryParse($_, [ref]([guid]::Empty)) })]
    [string]$BatchId,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z]{2}$')]
    [string]$Alpha2Code,

    [Parameter(Mandatory = $true)]
    [ValidateScript({
        $uri = [uri]$_
        $uri.Scheme -eq 'https' -and -not [string]::IsNullOrWhiteSpace($uri.Host)
    })]
    [string]$NewUrl,

    [string]$Actor = 'coverage-source-remediation-operator'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$code = $Alpha2Code.ToUpperInvariant()
$target = "coverage batch $BatchId / $code -> $NewUrl"
Write-Host 'Controlled coverage source canonical-URL remediation v10.18.2'
Write-Host "Batch:  $BatchId"
Write-Host "Code:   $code"
Write-Host "URL:    $NewUrl"
Write-Host "Actor:  $Actor"
Write-Host 'Safety: same-host HTTPS correction only; existing snapshots block mutation'

if (-not $PSCmdlet.ShouldProcess($target, 'Update the existing official source and reset its monitor for retry')) {
    return
}

$python = @'
import json
import os
from urllib.parse import urlparse
from uuid import UUID

from sqlmodel import Session, select

from app.core.db import engine
from app.models.domain import (
    JurisdictionCoverageEvidenceBatchItem,
    OfficialSource,
    SourceMonitor,
    SourceSnapshot,
    now_utc,
)
from app.services.audit_log import record_audit

batch_id = UUID(os.environ["GMAI_BATCH_ID"])
alpha2 = os.environ["GMAI_ALPHA2"].upper()
new_url = os.environ["GMAI_NEW_URL"].strip()
actor = os.environ["GMAI_ACTOR"].strip() or "coverage-source-remediation-operator"

parsed_new = urlparse(new_url)
if parsed_new.scheme.lower() != "https" or not parsed_new.hostname:
    raise SystemExit("Replacement URL must be an absolute HTTPS URL")
if parsed_new.username or parsed_new.password:
    raise SystemExit("Replacement URL cannot contain credentials")
if parsed_new.port not in (None, 443):
    raise SystemExit("Replacement URL must use the standard HTTPS port")

result = None
with Session(engine) as session:
    item = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem).where(
            JurisdictionCoverageEvidenceBatchItem.batch_id == batch_id,
            JurisdictionCoverageEvidenceBatchItem.alpha2_code == alpha2,
        )
    ).first()
    if item is None:
        raise SystemExit(f"Coverage batch item not found for {alpha2}")
    if item.official_source_id is None or item.source_monitor_id is None:
        raise SystemExit("Coverage batch item does not have an onboarded source and monitor")

    source = session.get(OfficialSource, item.official_source_id)
    monitor = session.get(SourceMonitor, item.source_monitor_id)
    if source is None or monitor is None:
        raise SystemExit("Onboarded source or monitor is missing")

    existing_snapshot = session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source.id)
        .limit(1)
    ).first()

    old_url = str(source.url)
    parsed_old = urlparse(old_url)
    old_host = (parsed_old.hostname or "").lower().rstrip(".")
    new_host = (parsed_new.hostname or "").lower().rstrip(".")
    if not old_host or new_host != old_host:
        raise SystemExit(f"Replacement host must remain {old_host or 'the existing host'}")

    try:
        allowed = [str(value).lower().rstrip(".") for value in json.loads(monitor.allowed_domains_json or "[]")]
    except json.JSONDecodeError as exc:
        raise SystemExit("Monitor domain allowlist is invalid JSON") from exc
    if not any(new_host == domain or new_host.endswith(f".{domain}") for domain in allowed):
        raise SystemExit("Replacement host is not covered by the monitor allowlist")

    url_already_corrected = old_url == new_url
    if existing_snapshot is not None and not url_already_corrected:
        raise SystemExit("Cannot change a monitored source URL after an immutable snapshot exists")

    source_id = str(source.id)
    monitor_id = str(monitor.id)
    snapshot_id = str(existing_snapshot.id) if existing_snapshot is not None else None
    changed = False

    # Once an immutable snapshot exists, an idempotent rerun may confirm the
    # canonical URL but must not mutate the source or monitor.
    if existing_snapshot is None:
        monitor_needs_reset = any(
            (
                monitor.status != "active",
                monitor.last_error is not None,
                monitor.last_http_status is not None,
            )
        )
        changed = (not url_already_corrected) or monitor_needs_reset
        if changed:
            before = {
                "source_url": old_url,
                "monitor_status": monitor.status,
                "monitor_last_error": monitor.last_error,
            }
            source.url = new_url
            source.updated_at = now_utc()
            monitor.status = "active"
            monitor.last_error = None
            monitor.last_http_status = None
            monitor.next_check_at = now_utc()
            monitor.updated_at = now_utc()
            session.add(source)
            session.add(monitor)
            record_audit(
                session,
                action="coverage_source_canonical_url_corrected",
                entity_type="official_source",
                entity_id=source.id,
                before_state=before,
                after_state={
                    "source_url": new_url,
                    "monitor_status": "active",
                    "batch_id": batch_id,
                    "alpha2_code": alpha2,
                },
                reason="Canonical HTTPS endpoint correction; transport security policy remains unchanged.",
                actor=actor,
                source="coverage_source_remediation_v10_18_2",
            )
            session.commit()

    # Copy scalar values while the ORM objects are still attached. SQLAlchemy
    # expires mapped attributes on commit by default, so no ORM attributes are
    # accessed after leaving the Session context.
    result = {
        "batch_id": str(batch_id),
        "alpha2_code": alpha2,
        "official_source_id": source_id,
        "source_monitor_id": monitor_id,
        "old_url": old_url,
        "new_url": new_url,
        "monitor_status": "active" if existing_snapshot is None else str(monitor.status),
        "changed": changed,
        "already_corrected": url_already_corrected and not changed,
        "snapshot_exists": existing_snapshot is not None,
        "snapshot_id": snapshot_id,
        "ready_for_retry": existing_snapshot is None,
    }

print(json.dumps(result, indent=2))
'@

$envArgs = @(
    '-e', "GMAI_BATCH_ID=$BatchId",
    '-e', "GMAI_ALPHA2=$code",
    '-e', "GMAI_NEW_URL=$NewUrl",
    '-e', "GMAI_ACTOR=$Actor"
)

$python | docker compose exec -T @envArgs api python -
if ($LASTEXITCODE -ne 0) {
    throw "Coverage source remediation failed with exit code $LASTEXITCODE"
}

Write-Host ''
Write-Host 'Canonical source URL updated. Retry baseline capture with:'
Write-Host ".\scripts\Capture-ApprovedCoverageBaselines.ps1 -BatchId `"$BatchId`" -Actor `"coverage-baseline-operator`""
