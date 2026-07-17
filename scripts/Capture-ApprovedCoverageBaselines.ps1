[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [Guid]$BatchId,
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$Actor = "coverage-baseline-operator",
    [ValidateSet("admin", "reviewer")]
    [string]$Role = "admin"
)

$ErrorActionPreference = "Stop"
$base = $ApiBaseUrl.TrimEnd('/')
$statusEndpoint = "$base/api/v1/global-intelligence/registry/coverage-batches/$BatchId/baseline-status"
$captureEndpoint = "$base/api/v1/global-intelligence/registry/coverage-batches/$BatchId/capture-baselines"
$headers = @{
    "X-GMAI-Role" = $Role
    "X-GMAI-User" = $Actor
}

$status = Invoke-RestMethod -Method Get -Uri $statusEndpoint -Headers $headers
Write-Host "Controlled coverage baseline capture"
Write-Host "Batch:          $($status.batch_name)"
Write-Host "Batch ID:       $BatchId"
Write-Host "Items:          $($status.item_count)"
Write-Host "Pending review: $($status.pending_review)"
Write-Host "Ready to queue: $($status.eligible_to_queue)"
Write-Host "Baselines ready:$($status.baseline_ready)"
Write-Host "In progress:    $($status.in_progress)"
Write-Host "Failed:         $($status.failed)"
Write-Host "Safety:         captures evidence only; no rule publication or coverage claim"

if ($status.eligible_to_queue -eq 0) {
    Write-Host "Nothing is eligible to queue. Complete independent reviews or inspect existing runs."
    $status
    return
}

if (-not $PSCmdlet.ShouldProcess($captureEndpoint, "Queue approved source monitors for baseline capture")) {
    return
}

$result = Invoke-RestMethod -Method Post -Uri $captureEndpoint -Headers $headers -ContentType "application/json"
Write-Host "Queue request completed."
Write-Host "Queued:         $($result.queued)"
Write-Host "Baselines ready:$($result.baseline_ready)"
Write-Host "In progress:    $($result.in_progress)"
Write-Host "Failed:         $($result.failed)"
Write-Host "No verified rule was published. Review snapshots and regulatory changes separately."
$result
