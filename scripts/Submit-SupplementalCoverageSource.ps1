[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PackPath = (Join-Path $PSScriptRoot "..\knowledge\global_coverage\tranches\v10_21_2_canada_supplemental_visa.json"),
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$Actor = "coverage-supplemental-source-proposer",
    [ValidateSet("admin", "reviewer")]
    [string]$Role = "admin"
)

$ErrorActionPreference = "Stop"
$resolvedPack = (Resolve-Path -LiteralPath $PackPath).Path
$pack = Get-Content -LiteralPath $resolvedPack -Raw -Encoding UTF8 | ConvertFrom-Json

if ($pack.review_status -ne "pending_independent_review") {
    throw "Supplemental source pack must remain pending_independent_review."
}
if ($pack.coverage_claim_ready -ne $false) {
    throw "Supplemental source pack must not claim coverage readiness."
}
if ($pack.safety.auto_approves_evidence -ne $false) {
    throw "Supplemental source pack must not auto-approve evidence."
}
if ($pack.safety.supersedes_primary_certification -ne $false) {
    throw "Supplemental source pack must preserve the existing primary certification."
}
if (-not $pack.batch -or @($pack.batch.items).Count -ne 1) {
    throw "Supplemental source pack must contain exactly one batch item."
}

$item = $pack.batch.items[0]
$scope = [string]$item.source_onboarding.certification_scope
if ($scope -notmatch '^supplemental_[a-z0-9_]+$') {
    throw "Certification scope must be supplemental_<domain>."
}
if ([string]$item.source_onboarding.source_url -notmatch '^https://') {
    throw "Supplemental official source must use HTTPS."
}

Write-Host "Supplemental coverage source pack v10.21.2"
Write-Host "Pack:          $($pack.title)"
Write-Host "Jurisdiction:  $($item.alpha2_code)"
Write-Host "Source:        $($item.source_onboarding.source_url)"
Write-Host "Scope:         $scope"
Write-Host "Review state:  $($pack.review_status)"
Write-Host "Safety:        preserves primary certification; pending review only"

$endpoint = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-batches"
if (-not $PSCmdlet.ShouldProcess($endpoint, "Submit supplemental official source as a pending-review batch")) {
    return
}

$headers = @{
    "X-GMAI-Role" = $Role
    "X-GMAI-User" = $Actor
}
$body = $pack.batch | ConvertTo-Json -Depth 30 -Compress
$result = Invoke-RestMethod -Method Post -Uri $endpoint -Headers $headers -ContentType "application/json" -Body $body

Write-Host "Submission completed."
Write-Host "Created:       $($result.created)"
Write-Host "Batch ID:      $($result.id)"
Write-Host "Status:        $($result.status)"
Write-Host "Pending review:$($result.review_counts.pending_review)"
Write-Host "The approved primary certification was not superseded. A different reviewer must decide the supplemental certification."
$result
