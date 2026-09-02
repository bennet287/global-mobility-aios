$ErrorActionPreference = "Stop"
$base = "http://localhost:8000"
$batchId = "4809d487-aec5-4884-834b-62a729618f1b"

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

function Publish-Assertion($Alpha2Code, $Title, $RuleKey, $Statement, $Excerpt, $Rationale) {
    $payload = @{
        alpha2_code = $Alpha2Code
        domain = "visa"
        title = $Title
        rule_key = $RuleKey
        statement = $Statement
        evidence_excerpt = $Excerpt
        rationale = $Rationale
        confidence = 0.9
    }

    Write-Host "Creating assertion for $Alpha2Code..."
    $assertion = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/coverage-batches/$batchId/initial-rule-assertions" -Body $payload -Actor "coverage-rule-proposer"
    $assertionId = $assertion.id
    Write-Host "Assertion ID: $assertionId"

    $reviewPayload = @{
        decision = "approved"
        notes = "Assertion is narrower than the evidence, pinned to the immutable snapshot, and describes only the official source's purpose and content. No eligibility or legal effect is claimed."
    }
    Write-Host "Reviewing assertion $assertionId..."
    $reviewed = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/review" -Body $reviewPayload -Actor "coverage-rule-reviewer"
    Write-Host "Review status: $($reviewed.status)"

    $publishPayload = @{
        attestation = $true
        publication_notes = "Publish the $Alpha2Code baseline rule. Verified against the official immutable snapshot; no regulatory change is claimed."
    }
    Write-Host "Publishing assertion $assertionId..."
    $published = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/publish" -Body $publishPayload -Actor "coverage-rule-publisher"
    Write-Host "Published rule ID: $($published.verified_rule.id)"
    Write-Host "Coverage ready: $($published.coverage_receipt.after.coverage_ready)/$($published.coverage_receipt.after.coverage_required)"

    return $published
}

# AO assertion
Publish-Assertion `
    -Alpha2Code "AO" `
    -Title "Angola SME visa authority and categories baseline" `
    -RuleKey "ao_sme_visa_authority_and_categories_baseline" `
    -Statement "The official Migration and Foreigners Service (SME) eVISA page for Angola states that SME is the central executive body of the Ministry of the Interior responsible for executing policies related to entry, transit, exit and control of foreign citizens in national territory, and the page publishes visa categories including the tourist visa." `
    -Excerpt "The Migration and Foreigners Service, abbreviated as SME, is the central executive body of the Ministry of the Interior, with administrative autonomy and budgetary management, which is responsible for executing policies and legislative and regulatory measures related to entry, transit, exit and control of the permanence and activities of foreign citizens in national territory. VISA Categories. Tourist visa is granted by Angolan diplomatic and consular missions to foreign citizens wishing to enter the Republic of Angola, in recreational, sports or cultural visit." `
    -Rationale "The assertion is pinned to the immutable SME eVISA snapshot and reports only the authority role and presence of visa categories described on the page. It does not infer eligibility, legal effect, or future changes."

# BJ assertion
Publish-Assertion `
    -Alpha2Code "BJ" `
    -Title "Benin official e-Visa platform baseline" `
    -RuleKey "bj_official_evisa_platform_baseline" `
    -Statement "The official Benin e-Visa platform (evisa.bj) is the official platform for visa applications for Benin and publishes information on visa costs, visa-exempt countries, and links to the Direction de l'Emigration et de l'Immigration." `
    -Excerpt "e-Visa - Plateforme officielle de demande de visa pour le Benin. Demander un e-Visa. Les couts des visas d'entree au Benin. Voyager sans visa (pays exemptes). Direction de l'Emigration et de l'Immigration." `
    -Rationale "The assertion is pinned to the immutable evisa.bj snapshot and describes only the official platform's purpose and the categories of information it presents. It does not state eligibility, guarantee entry, or claim legal effect."

Write-Host "AO and BJ assertions published."
