[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ManifestPath,

    [ValidateRange(1, 100)]
    [int]$MaxGroups = 20,

    [ValidateRange(1, 50)]
    [int]$MaxCodesPerGroup = 25
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

$resolvedPath = Resolve-PowerShellProviderPath -Path $ManifestPath
if (-not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
    throw "Coverage tranche operations manifest was not found: $resolvedPath"
}

try {
    $manifest = Get-Content -LiteralPath $resolvedPath -Raw | ConvertFrom-Json
}
catch {
    throw "Coverage tranche operations manifest is not valid JSON: $($_.Exception.Message)"
}

if ($null -eq $manifest) {
    throw "Coverage tranche operations manifest is empty."
}

$schemaVersion = [string]$manifest.schema_version
if ($schemaVersion -ne "1.0") {
    throw "Unsupported schema_version '$schemaVersion'. Expected '1.0'."
}

$name = [string]$manifest.name
if ([string]::IsNullOrWhiteSpace($name)) {
    throw "Manifest name is required."
}

$groups = @($manifest.groups)
if ($groups.Count -eq 0) {
    throw "Manifest groups must contain at least one coverage evidence batch."
}
if ($groups.Count -gt $MaxGroups) {
    throw "Manifest contains $($groups.Count) groups; the configured maximum is $MaxGroups."
}

$normalizedGroups = @()
$totalCodes = 0
$groupNumber = 0

foreach ($group in $groups) {
    $groupNumber++
    $batchIdText = [string]$group.batch_id
    $parsedBatchId = [guid]::Empty
    if (-not [guid]::TryParse($batchIdText, [ref]$parsedBatchId)) {
        throw "Group $groupNumber has an invalid batch_id: '$batchIdText'."
    }

    $label = [string]$group.label
    if ([string]::IsNullOrWhiteSpace($label)) {
        $label = "Coverage batch $groupNumber"
    }

    $codes = @(
        @($group.alpha2_codes) |
            ForEach-Object { ([string]$_).Trim().ToUpperInvariant() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Select-Object -Unique
    )

    if ($codes.Count -eq 0) {
        throw "Group '$label' must contain at least one alpha2 code."
    }
    if ($codes.Count -gt $MaxCodesPerGroup) {
        throw "Group '$label' contains $($codes.Count) codes; the maximum is $MaxCodesPerGroup."
    }

    $invalidCodes = @($codes | Where-Object { $_ -notmatch '^[A-Z]{2}$' })
    if ($invalidCodes.Count -gt 0) {
        throw "Group '$label' contains invalid alpha2 codes: $($invalidCodes -join ', ')."
    }

    $totalCodes += $codes.Count
    $normalizedGroups += [pscustomobject]@{
        label = $label
        batch_id = $parsedBatchId.ToString()
        alpha2_codes = $codes
    }
}

[pscustomobject]@{
    schema_version = "1.0"
    name = $name.Trim()
    description = [string]$manifest.description
    source_path = $resolvedPath
    group_count = $normalizedGroups.Count
    total_codes = $totalCodes
    groups = $normalizedGroups
    safety = [pscustomobject]@{
        creates_evidence_batches = $false
        creates_review_decisions = $false
        creates_assertions = $false
        publishes_verified_rules = $false
        creates_coverage_claim = $false
        message = "The manifest identifies existing coverage evidence batches and jurisdictions only."
    }
}
