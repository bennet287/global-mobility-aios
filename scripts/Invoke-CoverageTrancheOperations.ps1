[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ManifestPath,

    [string]$Actor = "coverage-tranche-operator",

    [string]$ApiBaseUrl = "http://localhost:8000",

    [string]$OutputDirectory,

    [switch]$ApplyBaselineQueues,

    [ValidateRange(1, 12)]
    [int]$MaxCandidateLines = 8
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


function Invoke-AssistantPreparation {
    param(
        [Parameter(Mandatory = $true)][string]$BatchId,
        [Parameter(Mandatory = $true)][string[]]$Codes,
        [Parameter(Mandatory = $true)][bool]$DryRun,
        [Parameter(Mandatory = $true)][bool]$QueueEligibleBaselines
    )

    $payload = @{
        alpha2_codes = $Codes
        dry_run = $DryRun
        queue_eligible_baselines = $QueueEligibleBaselines
        include_candidate_assertions = $true
        max_candidate_lines = $MaxCandidateLines
    } | ConvertTo-Json -Depth 10

    $uri = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-batches/$BatchId/assistant/prepare"
    return Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $payload
}

$validator = Join-Path $PSScriptRoot "Test-CoverageTrancheManifest.ps1"
if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
    throw "Manifest validator is missing: $validator"
}
$manifest = & $validator -ManifestPath $ManifestPath

$headers = @{
    "X-GMAI-Role" = "admin"
    "X-GMAI-User" = $Actor
    "Content-Type" = "application/json"
}

$configUri = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/global-intelligence/registry/coverage-tranche-assistant/config"
$config = Invoke-RestMethod -Method Get -Uri $configUri -Headers $headers
if (-not $config.enabled) {
    throw "Coverage tranche assistant is disabled. Enable it in the Docker environment and recreate the API container."
}

foreach ($group in $manifest.groups) {
    if (@($group.alpha2_codes).Count -gt [int]$config.max_items) {
        throw "Group '$($group.label)' exceeds the API maximum of $($config.max_items) jurisdictions."
    }
}

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path (Get-Location).Path ("coverage-tranche-operations-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
}
$resolvedOutputDirectory = Resolve-PowerShellProviderPath -Path $OutputDirectory

Write-Host "Coverage tranche operations v10.22"
Write-Host "Manifest:       $($manifest.name)"
Write-Host "Groups:         $($manifest.group_count)"
Write-Host "Jurisdictions:  $($manifest.total_codes)"
Write-Host "Apply queues:   $([bool]$ApplyBaselineQueues)"
Write-Host "Safety:         no review decisions, assertions, publications, snapshot changes, or coverage claims"
Write-Host ""

$groupResults = @()
foreach ($group in $manifest.groups) {
    Write-Host "Preflight: $($group.label) [$($group.alpha2_codes -join ', ')]"
    $preflight = Invoke-AssistantPreparation `
        -BatchId $group.batch_id `
        -Codes @($group.alpha2_codes) `
        -DryRun $true `
        -QueueEligibleBaselines $false

    $applied = $null
    $queueCandidates = @($preflight.would_queue_baselines)
    if ($ApplyBaselineQueues -and $queueCandidates.Count -gt 0) {
        $target = "$($group.label) / $($queueCandidates -join ', ')"
        if ($PSCmdlet.ShouldProcess($target, "Queue explicitly selected approved baseline captures")) {
            $applied = Invoke-AssistantPreparation `
                -BatchId $group.batch_id `
                -Codes @($group.alpha2_codes) `
                -DryRun $false `
                -QueueEligibleBaselines $true
        }
    }

    $final = Invoke-AssistantPreparation `
        -BatchId $group.batch_id `
        -Codes @($group.alpha2_codes) `
        -DryRun $true `
        -QueueEligibleBaselines $false

    $groupResults += [pscustomobject]@{
        label = $group.label
        batch_id = $group.batch_id
        selected_codes = @($group.alpha2_codes)
        preflight = $preflight
        apply_result = $applied
        final = $final
    }
}

$rows = @()
$drafts = @()
foreach ($groupResult in $groupResults) {
    foreach ($item in @($groupResult.final.items)) {
        $review = $item.review_packet
        $analysis = $item.snapshot_analysis
        $assertion = $item.existing_assertion
        $receipt = $item.coverage_receipt
        $baseline = $item.baseline
        $rows += [pscustomobject]@{
            batch_label = $groupResult.label
            batch_id = $groupResult.batch_id
            alpha2_code = $item.alpha2_code
            jurisdiction_name = $item.jurisdiction_name
            stage = $item.stage
            next_action = $item.next_action
            assessment_status = if ($review -and $review.immigration_assessment) { $review.immigration_assessment.status } else { "missing" }
            certification_status = if ($review -and $review.source_certification) { $review.source_certification.status } else { "missing" }
            source_url = if ($review -and $review.official_source) { $review.official_source.url } else { "" }
            monitor_status = if ($review -and $review.monitor) { $review.monitor.status } else { "missing" }
            baseline_state = if ($baseline) { $baseline.state } else { "missing" }
            snapshot_id = if ($analysis) { $analysis.snapshot_id } else { "" }
            snapshot_quality = if ($analysis) { $analysis.quality_score } else { $null }
            snapshot_classification = if ($analysis) { $analysis.classification } else { "" }
            assertion_status = if ($assertion) { $assertion.status } else { "missing" }
            assertion_id = if ($assertion) { $assertion.id } else { "" }
            coverage_ready = if ($receipt) { [bool]$receipt.coverage_ready } else { $false }
            missing_gates = if ($receipt) { @($receipt.missing) -join ";" } else { "" }
            eligible_to_queue = if ($baseline) { [bool]$baseline.eligible_to_queue } else { $false }
        }

        if ($item.candidate_assertion) {
            $drafts += [pscustomobject]@{
                batch_label = $groupResult.label
                batch_id = $groupResult.batch_id
                batch_item_id = $item.batch_item_id
                alpha2_code = $item.alpha2_code
                jurisdiction_name = $item.jurisdiction_name
                snapshot_id = $analysis.snapshot_id
                snapshot_quality = $analysis.quality_score
                snapshot_classification = $analysis.classification
                candidate_assertion = $item.candidate_assertion
            }
        }
    }
}

$stageCounts = @{}
foreach ($grouped in @($rows | Group-Object -Property stage)) {
    $stageCounts[$grouped.Name] = $grouped.Count
}

$summary = [pscustomobject]@{
    schema_version = "1.0"
    release = "v10.22"
    manifest = [pscustomobject]@{
        name = $manifest.name
        description = $manifest.description
        source_path = $manifest.source_path
    }
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    actor = $Actor
    apply_baseline_queues_requested = [bool]$ApplyBaselineQueues
    group_count = $manifest.group_count
    jurisdiction_count = $rows.Count
    stage_counts = $stageCounts
    groups = $groupResults
    rows = $rows
    candidate_assertions = $drafts
    safety = [pscustomobject]@{
        creates_review_decisions = $false
        creates_assertions = $false
        publishes_verified_rules = $false
        mutates_snapshots = $false
        creates_regulatory_changes = $false
        creates_coverage_claim = $false
        baseline_queue_scope = "Only explicitly listed, independently approved, API-eligible batch items may be queued when apply mode is confirmed."
    }
}

Write-Host ""
Write-Host "Operational summary"
foreach ($key in @($stageCounts.Keys | Sort-Object)) {
    Write-Host ("  {0,-42} {1,3}" -f $key, $stageCounts[$key])
}
Write-Host "  candidate_assertion_drafts                 $($drafts.Count)"
Write-Host ""

$reviewRows = @($rows | Where-Object { $_.stage -in @("pending_independent_review", "assertion_pending_independent_review", "assertion_approved_awaiting_publication") })
$baselineRows = @($rows | Where-Object { $_.baseline_state -in @("retrieval_failed", "retrieval_in_progress") -or $_.eligible_to_queue })

$files = @{
    summary_json = Join-Path $resolvedOutputDirectory "tranche-operations-summary.json"
    summary_csv = Join-Path $resolvedOutputDirectory "tranche-operations-summary.csv"
    review_queue_csv = Join-Path $resolvedOutputDirectory "tranche-review-queue.csv"
    baseline_queue_csv = Join-Path $resolvedOutputDirectory "tranche-baseline-queue.csv"
    assertion_drafts_json = Join-Path $resolvedOutputDirectory "tranche-assertion-drafts.json"
}

if ($PSCmdlet.ShouldProcess($resolvedOutputDirectory, "Write tranche operation receipts")) {
    New-Item -ItemType Directory -Path $resolvedOutputDirectory -Force | Out-Null
    $summary | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $files.summary_json -Encoding UTF8
    $rows | Export-Csv -LiteralPath $files.summary_csv -NoTypeInformation -Encoding UTF8
    $reviewRows | Export-Csv -LiteralPath $files.review_queue_csv -NoTypeInformation -Encoding UTF8
    $baselineRows | Export-Csv -LiteralPath $files.baseline_queue_csv -NoTypeInformation -Encoding UTF8
    [pscustomobject]@{
        generated_at = $summary.generated_at
        draft_count = $drafts.Count
        drafts = $drafts
        safety = $summary.safety
    } | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $files.assertion_drafts_json -Encoding UTF8

    Write-Host "Saved receipts: $resolvedOutputDirectory"
}

$summary
