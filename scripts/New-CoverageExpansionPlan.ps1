[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
    [ValidateRange(1, 25)]
    [int]$Count = 10,

    [string]$Gap = "all",

    [string]$Region = "all",

    [string]$Actor = "coverage-planning-operator",

    [string]$ApiBaseUrl = "http://localhost:8000",

    [string]$OutputPath = ".\coverage-expansion-plan.json",

    [string]$CsvOutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-PowerShellProviderPath {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Path
    )

    return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
}


$headers = @{
    "X-GMAI-Role" = "admin"
    "X-GMAI-User" = $Actor
}

$base = $ApiBaseUrl.TrimEnd('/')
$gapValue = [System.Uri]::EscapeDataString($Gap)
$regionValue = [System.Uri]::EscapeDataString($Region)
$uri = "$base/api/v1/global-intelligence/registry/coverage-worklist?gap=$gapValue&region=$regionValue&limit=$Count"

Write-Host "Coverage expansion planner v10.22"
Write-Host "Count:          $Count"
Write-Host "Gap filter:     $Gap"
Write-Host "Region filter:  $Region"
Write-Host "Safety:         planning output only; no evidence, review, baseline, assertion, publication, or coverage mutation"

$worklist = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
$items = @($worklist.items)

$jurisdictions = @()
foreach ($item in $items) {
    $jurisdictions += [pscustomobject]@{
        alpha2_code = [string]$item.alpha2_code
        name = [string]$item.name
        region = [string]$item.region
        jurisdiction_type = [string]$item.jurisdiction_type
        immigration_rule_status = [string]$item.immigration_rule_status
        missing_gates = @($item.missing)
        pending_assessment = $item.pending_assessment
        pending_source_certification = $item.pending_source_certification
        operator_status = "needs_evidence_research"
        evidence = [pscustomobject]@{
            relationship = ""
            relationship_evidence_url = ""
            relationship_evidence_title = ""
            relationship_rationale = ""
            authority_name = ""
            authority_website_url = ""
            official_source_name = ""
            official_source_url = ""
            source_domain = "visa"
            coverage_domains = @("visa")
            evidence_notes = ""
        }
    }
}

$plan = [pscustomobject]@{
    schema_version = "1.0"
    name = "Coverage expansion plan - $(Get-Date -Format 'yyyy-MM-dd')"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    generated_by = $Actor
    registry_release = $worklist.release
    filters = $worklist.filters
    selected_count = $jurisdictions.Count
    jurisdictions = $jurisdictions
    safety = [pscustomobject]@{
        creates_evidence_batches = $false
        infers_immigration_relationships = $false
        certifies_sources = $false
        queues_monitors = $false
        publishes_rules = $false
        creates_coverage_claim = $false
        message = "Every blank evidence field requires human research and review before submission."
    }
}

$resolvedOutput = Resolve-PowerShellProviderPath -Path $OutputPath
if ($PSCmdlet.ShouldProcess($resolvedOutput, "Write coverage expansion planning JSON")) {
    $directory = Split-Path -Parent $resolvedOutput
    if ($directory -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $plan | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resolvedOutput -Encoding UTF8
    Write-Host "Saved planning JSON: $resolvedOutput"
}

if (-not [string]::IsNullOrWhiteSpace($CsvOutputPath)) {
    $resolvedCsv = Resolve-PowerShellProviderPath -Path $CsvOutputPath
    $csvRows = @(
        $jurisdictions | ForEach-Object {
            [pscustomobject]@{
                alpha2_code = $_.alpha2_code
                name = $_.name
                region = $_.region
                jurisdiction_type = $_.jurisdiction_type
                immigration_rule_status = $_.immigration_rule_status
                missing_gates = ($_.missing_gates -join ';')
                operator_status = $_.operator_status
            }
        }
    )
    if ($PSCmdlet.ShouldProcess($resolvedCsv, "Write coverage expansion planning CSV")) {
        $directory = Split-Path -Parent $resolvedCsv
        if ($directory -and -not (Test-Path -LiteralPath $directory)) {
            New-Item -ItemType Directory -Path $directory -Force | Out-Null
        }
        $csvRows | Export-Csv -LiteralPath $resolvedCsv -NoTypeInformation -Encoding UTF8
        Write-Host "Saved planning CSV:  $resolvedCsv"
    }
}

Write-Host "Selected:       $($jurisdictions.Count)"
$plan
