[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [string]$BatchId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string[]]$Alpha2Code,

    [string]$Actor = "coverage-tranche-operator",

    [string]$ApiBaseUrl = "http://localhost:8000",

    [switch]$ApplyBaselineQueues,

    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

$headers = @{
    "X-GMAI-Role" = "admin"
    "X-GMAI-User" = $Actor
    "Content-Type" = "application/json"
}

$configUri = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-tranche-assistant/config"
$config = Invoke-RestMethod -Method Get -Uri $configUri -Headers $headers

Write-Host "Coverage tranche assistant v10.21"
Write-Host "Enabled:        $($config.enabled)"
Write-Host "Batch:          $BatchId"
Write-Host "Jurisdictions:  $($Alpha2Code -join ', ')"
Write-Host "Max items:      $($config.max_items)"
Write-Host "Safety:         $($config.safety.message)"

if (-not $config.enabled) {
    throw "Coverage tranche assistant is disabled. Set COVERAGE_TRANCHE_ASSISTANT_ENABLED=true in .env and rebuild the API container."
}

$codes = @($Alpha2Code | ForEach-Object { $_.Trim().ToUpperInvariant() } | Where-Object { $_ } | Select-Object -Unique)
if ($codes.Count -eq 0) {
    throw "At least one jurisdiction code is required."
}
if ($codes.Count -gt [int]$config.max_items) {
    throw "The assistant allows at most $($config.max_items) jurisdictions per request."
}
if ($codes | Where-Object { $_ -notmatch '^[A-Z]{2}$' }) {
    throw "Every jurisdiction code must be a two-letter alpha-2 code."
}

$apply = $false
if ($ApplyBaselineQueues) {
    $target = "coverage batch $BatchId / $($codes -join ', ')"
    $apply = $PSCmdlet.ShouldProcess($target, "Queue only explicitly selected approved baseline captures")
}

$payload = @{
    alpha2_codes = $codes
    dry_run = -not $apply
    queue_eligible_baselines = [bool]$ApplyBaselineQueues
    include_candidate_assertions = $true
    max_candidate_lines = 8
} | ConvertTo-Json -Depth 10

$prepareUri = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-batches/$BatchId/assistant/prepare"
$result = Invoke-RestMethod -Method Post -Uri $prepareUri -Headers $headers -Body $payload

Write-Host ""
Write-Host "Preparation completed."
Write-Host "Dry run:        $($result.dry_run)"
Write-Host "Selected:       $($result.selected_count)"
Write-Host "Would queue:    $($result.would_queue_baselines.Count)"
Write-Host "Queued:         $($result.queued_baselines)"
Write-Host ""

foreach ($item in $result.items) {
    Write-Host "$($item.alpha2_code) - $($item.jurisdiction_name)"
    Write-Host "  Stage:        $($item.stage)"
    Write-Host "  Next action:  $($item.next_action)"
    if ($item.snapshot_analysis) {
        Write-Host "  Snapshot:     $($item.snapshot_analysis.snapshot_id)"
        Write-Host "  Quality:      $($item.snapshot_analysis.quality_score)/100 ($($item.snapshot_analysis.classification))"
    }
    if ($item.candidate_assertion) {
        Write-Host "  Draft title:  $($item.candidate_assertion.title)"
        Write-Host "  Draft only:   True - no assertion was created"
    }
    Write-Host ""
}

if ($OutputPath) {
    $resolved = [System.IO.Path]::GetFullPath($OutputPath)
    $directory = Split-Path -Parent $resolved
    if ($directory -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resolved -Encoding UTF8
    Write-Host "Saved preparation receipt: $resolved"
}

$result
