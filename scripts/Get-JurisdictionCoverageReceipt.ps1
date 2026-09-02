[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z]{2}$')]
    [string]$Alpha2Code,

    [string]$ApiBaseUrl = 'http://localhost:8000',

    [string]$Actor = 'coverage-readiness-operator'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$code = $Alpha2Code.Trim().ToUpperInvariant()
$base = $ApiBaseUrl.TrimEnd('/')
$headers = @{
    'X-GMAI-Role' = 'admin'
    'X-GMAI-User' = $Actor
}

try {
    $registry = Invoke-RestMethod `
        -Method Get `
        -Uri "$base/api/v1/global-intelligence/registry" `
        -Headers $headers

    $entry = @($registry.entries) |
        Where-Object { $_.alpha2_code -eq $code } |
        Select-Object -First 1

    if (-not $entry) {
        throw "Jurisdiction $code was not found in the active registry release."
    }

    $receipt = Invoke-RestMethod `
        -Method Get `
        -Uri "$base/api/v1/global-intelligence/registry/jurisdictions/$($entry.jurisdiction_id)/coverage-receipt" `
        -Headers $headers

    Write-Host 'Reviewed jurisdiction coverage receipt'
    Write-Host ("Jurisdiction:     {0} ({1})" -f $receipt.name, $receipt.alpha2_code)
    Write-Host ("Registry release: {0}" -f $receipt.registry_release_version)
    Write-Host ("Status:           {0}" -f $receipt.status)
    Write-Host ("Coverage ready:   {0}" -f $receipt.coverage_ready)
    Write-Host ("Missing gates:    {0}" -f ($(if (@($receipt.missing).Count) { @($receipt.missing) -join ', ' } else { 'none' })))
    Write-Host ("Ready total:      {0}/{1}" -f $receipt.registry_summary.coverage_ready, $receipt.registry_summary.coverage_required)
    Write-Host ("Verified rules:   {0}" -f $receipt.registry_summary.with_verified_rule)
    Write-Host ("Global claim:     {0}" -f $receipt.global_coverage_claim_ready)
    Write-Host ''

    $receipt
}
catch {
    throw "Could not retrieve the jurisdiction coverage receipt: $($_.Exception.Message)"
}
