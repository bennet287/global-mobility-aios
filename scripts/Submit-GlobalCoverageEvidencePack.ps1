[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PackPath = (Join-Path $PSScriptRoot "..\knowledge\global_coverage\tranches\v10_17_official_evidence_starter.json"),
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$Actor = "coverage-evidence-proposer",
    [ValidateSet("admin", "reviewer")]
    [string]$Role = "admin"
)

$ErrorActionPreference = "Stop"
$resolvedPack = (Resolve-Path -LiteralPath $PackPath).Path
$pack = Get-Content -LiteralPath $resolvedPack -Raw -Encoding UTF8 | ConvertFrom-Json

if ($pack.review_status -ne "pending_independent_review") {
    throw "Evidence pack must remain pending_independent_review."
}
if ($pack.coverage_claim_ready -ne $false) {
    throw "Evidence pack must not claim global coverage readiness."
}
if (-not $pack.batch -or -not $pack.batch.items) {
    throw "Evidence pack does not contain a batch payload."
}

$codes = @($pack.batch.items | ForEach-Object { $_.alpha2_code })
Write-Host "Global coverage evidence pack"
Write-Host "Pack:          $($pack.pack_version)"
Write-Host "Verified at:   $($pack.verified_at)"
Write-Host "Jurisdictions: $($codes -join ', ')"
Write-Host "Review state:  $($pack.review_status)"
Write-Host "Safety:        pending proposals only; separate reviewer required"

$endpoint = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-batches"
if (-not $PSCmdlet.ShouldProcess($endpoint, "Submit evidence pack as pending-review proposals")) {
    return
}

$headers = @{
    "X-GMAI-Role" = $Role
    "X-GMAI-User" = $Actor
}
$body = $pack.batch | ConvertTo-Json -Depth 30 -Compress
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$result = Invoke-RestMethod -Method Post -Uri $endpoint -Headers $headers -ContentType "application/json; charset=utf-8" -Body $bodyBytes

Write-Host "Submission completed."
Write-Host "Created:       $($result.created)"
Write-Host "Batch ID:      $($result.id)"
Write-Host "Status:        $($result.status)"
Write-Host "Pending review:$($result.review_counts.pending_review)"
Write-Host "No proposal has been approved. Use a different reviewer account for decisions."
$result
