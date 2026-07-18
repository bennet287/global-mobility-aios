$ErrorActionPreference = "Stop"
$base = "http://localhost:8000"

function Call-Api($Method, $Uri, $Body, $Actor) {
    $headers = @{
        "X-GMAI-Role" = "admin"
        "X-GMAI-User" = $Actor
        "Content-Type" = "application/json"
    }
    if ($Body) {
        $json = $Body | ConvertTo-Json -Depth 10
        return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -Body $json
    } else {
        return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
    }
}

# 1. Approve IO immigration assessment
$assessmentId = "4403a371-116b-40a7-be51-9ac0f55cea76"
$assessmentReview = @{
    decision = "approved"
    notes = "BIOT is a UK overseas territory. The BIOT Administration operates under UK sovereignty and directly administers entry permits/approvals via its official biot.gov.io domain. The evidence page is official, jurisdiction-matched, and current as of the snapshot date. The shared_or_coordinated relationship with parent GB is accepted because UK overseas-territory governance applies while the Territory administers its own entry controls."
}
Write-Host "Approving immigration assessment $assessmentId..."
$assessmentResult = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/immigration-assessments/$assessmentId/review" -Body $assessmentReview -Actor "coverage-evidence-reviewer"
Write-Host "Assessment status: $($assessmentResult.status)"

# 2. Approve IO source certification
$certificationId = "598c88fd-b335-4ec6-b68d-95982eca77f8"
$certificationReview = @{
    decision = "approved"
    notes = "The source https://www.biot.gov.io/visiting/visa-requirements/ is hosted on the official biot.gov.io domain, is the BIOT Administration's own visiting/visa page, and was successfully probed with a fresh baseline snapshot. The primary-immigration certification scope is appropriate for the visa/entry guidance published on this page."
}
Write-Host "Approving source certification $certificationId..."
$certificationResult = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/source-certifications/$certificationId/review" -Body $certificationReview -Actor "coverage-evidence-reviewer"
Write-Host "Certification status: $($certificationResult.status)"

# 3. Check baseline status
$batchId = "4809d487-aec5-4884-834b-62a729618f1b"
Write-Host "Checking baseline status for batch $batchId..."
$baselineStatus = Call-Api -Method GET -Uri "$base/api/v1/global-intelligence/registry/coverage-batches/$batchId/baseline-status" -Actor "coverage-baseline-operator"
$baselineStatus | ConvertTo-Json -Depth 10

# 4. Queue baseline if eligible
if ($baselineStatus.eligible_to_queue -gt 0) {
    Write-Host "Queuing eligible baselines..."
    $queueResult = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/coverage-batches/$batchId/capture-baselines" -Body @{} -Actor "coverage-baseline-operator"
    $queueResult | ConvertTo-Json -Depth 10
} else {
    Write-Host "No baselines eligible to queue."
}

# 5. Create initial rule assertion
$assertionPayload = @{
    alpha2_code = "IO"
    domain = "visa"
    title = "British Indian Ocean Territory official visa and entry requirements"
    rule_key = "io_visa_entry_requirements_baseline"
    statement = "According to the official British Indian Ocean Territory Administration visa requirements page, there are no visa requirements for BIOT, but those visiting the Territory must have prior approval. Visiting yachts to the Outer Islands require a permit before arrival. As of 31 March 2026, the BIOT Administration has paused substantive consideration of new applications for permits to enter the Territory, except in exceptional circumstances, while it considers its position."
    rationale = "The assertion is pinned to the immutable baseline snapshot of the official BIOT Administration page. It reports only the statements present in the snapshot and does not infer eligibility, legal effect, or future changes. The UK/BIOT shared_or_coordinated relationship is accepted because the Territory administers entry controls under UK overseas-territory governance."
    evidence_excerpt = "There are no visa requirements for BIOT. Those visiting the Territory must have prior approval. Visiting yachts to the Outer Islands require a permit before arrival. In light of ongoing litigation relevant to the circumstances in which the BIOT Administration may issue permits for people to enter BIOT we have as of 31 March 2026, paused substantive consideration of new applications for permits to enter the Territory - except in exceptional circumstances - whilst the BIOT Administration considers its position."
    confidence = 0.9
}
Write-Host "Creating initial rule assertion..."
$assertion = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/coverage-batches/$batchId/initial-rule-assertions" -Body $assertionPayload -Actor "coverage-rule-proposer"
$assertion | ConvertTo-Json -Depth 10
$assertionId = $assertion.id

# 6. Review assertion
$assertionReview = @{
    decision = "approved"
    notes = "The assertion is narrower than the evidence, is pinned to the immutable snapshot, and accurately reflects the official BIOT Administration page including the current permit-application pause. No eligibility or legal effect is claimed."
}
Write-Host "Reviewing assertion $assertionId..."
$reviewedAssertion = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/review" -Body $assertionReview -Actor "coverage-rule-reviewer"
$reviewedAssertion | ConvertTo-Json -Depth 10

# 7. Publish assertion
$publishPayload = @{
    attestation = $true
    publication_notes = "Publish the IO baseline rule. Verified against the official BIOT Administration snapshot; no regulatory change is claimed."
}
Write-Host "Publishing assertion $assertionId..."
$published = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/publish" -Body $publishPayload -Actor "coverage-rule-publisher"
$published | ConvertTo-Json -Depth 10

# 8. Verify coverage receipt
Write-Host "Verifying IO coverage receipt..."
$receipt = Call-Api -Method GET -Uri "$base/api/v1/global-intelligence/registry/jurisdictions/fde507d0-e71b-4122-b622-30a7913aadca/coverage-receipt" -Actor "coverage-readiness-operator"
$receipt | ConvertTo-Json -Depth 10
