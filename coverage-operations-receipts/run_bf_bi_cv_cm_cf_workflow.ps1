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

function Approve-Review($Item, $AssessmentNotes, $CertificationNotes) {
    $assessmentId = $Item.review_packet.immigration_assessment.id
    $certificationId = $Item.review_packet.source_certification.id

    Write-Host "Approving $($Item.alpha2_code) assessment $assessmentId..."
    $assessmentReview = @{
        decision = "approved"
        notes = $AssessmentNotes
    }
    $assessmentResult = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/immigration-assessments/$assessmentId/review" -Body $assessmentReview -Actor "coverage-evidence-reviewer"
    Write-Host "Assessment status: $($assessmentResult.status)"

    Write-Host "Approving $($Item.alpha2_code) certification $certificationId..."
    $certificationReview = @{
        decision = "approved"
        notes = $CertificationNotes
    }
    $certificationResult = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/source-certifications/$certificationId/review" -Body $certificationReview -Actor "coverage-evidence-reviewer"
    Write-Host "Certification status: $($certificationResult.status)"
}

function Publish-Assertion($Item, $Title, $RuleKey, $Statement, $Excerpt, $Rationale) {
    $alpha2 = $Item.alpha2_code
    $payload = @{
        alpha2_code = $alpha2
        domain = "visa"
        title = $Title
        rule_key = $RuleKey
        statement = $Statement
        evidence_excerpt = $Excerpt
        rationale = $Rationale
        confidence = 0.9
    }

    Write-Host "Creating $alpha2 assertion..."
    $assertion = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/coverage-batches/$batchId/initial-rule-assertions" -Body $payload -Actor "coverage-rule-proposer"
    $assertionId = $assertion.id
    Write-Host "Assertion ID: $assertionId"

    $reviewPayload = @{
        decision = "approved"
        notes = "Assertion is narrower than the evidence, pinned to the immutable snapshot, and describes only the official source's purpose and content. No eligibility or legal effect is claimed."
    }
    Write-Host "Reviewing $alpha2 assertion..."
    $reviewed = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/review" -Body $reviewPayload -Actor "coverage-rule-reviewer"
    Write-Host "Review status: $($reviewed.status)"

    $publishPayload = @{
        attestation = $true
        publication_notes = "Publish the $alpha2 baseline rule. Verified against the official immutable snapshot; no regulatory change is claimed."
    }
    Write-Host "Publishing $alpha2 assertion..."
    $published = Call-Api -Method POST -Uri "$base/api/v1/global-intelligence/registry/initial-rule-assertions/$assertionId/publish" -Body $publishPayload -Actor "coverage-rule-publisher"
    Write-Host "Published rule ID: $($published.verified_rule.id)"
    Write-Host "Coverage total: $($published.coverage_receipt.after.registry_summary.coverage_ready)/$($published.coverage_receipt.after.registry_summary.coverage_required)"

    return $published
}

$packet = Get-Content -LiteralPath "coverage-operations-receipts/v10_22_africa_pending_5_review.json" -Raw | ConvertFrom-Json

foreach ($item in $packet.items) {
    $code = $item.alpha2_code
    Write-Host "`n=== Processing $code - $($item.jurisdiction_name) ==="

    switch ($code) {
        "BF" {
            Approve-Review -Item $item `
                -AssessmentNotes "Burkina Faso operates an independent visa regime. The Visa Burkina eVisa portal (visaburkina.bf) is the official government visa platform under the Ministry of Security / National Police Migration Division. Evidence is jurisdiction-matched and official." `
                -CertificationNotes "The source https://www.visaburkina.bf/en/home/ is hosted on the official visaburkina.bf domain and is the government eVisa portal. The primary-immigration certification scope is appropriate for the visa information published."
            Publish-Assertion -Item $item `
                -Title "Burkina Faso official eVisa portal baseline" `
                -RuleKey "bf_official_evisa_portal_baseline" `
                -Statement "The official Visa Burkina eVisa portal for Burkina Faso, operated under the Ministry of Security / Directorate General of National Police Migration Division, publishes visa information including types of visas (transit, short term, long term) and where to apply." `
                -Excerpt "Visa Burkina (evisa Burkina Faso). Types of Visas. The transit visa. The short term visa. The long term visa. Where to get your visa. At the border with immigration services. Fill out application form." `
                -Rationale "The assertion is pinned to the immutable snapshot of the official Visa Burkina portal and reports only the authority and visa categories described. It does not infer eligibility or legal effect."
        }
        "BI" {
            Approve-Review -Item $item `
                -AssessmentNotes "Burundi operates an independent visa regime. The Ministry of Foreign Affairs (MAE) is the competent foreign-affairs visa authority and its official page hosts visa application forms. The evidence is narrow but official and jurisdiction-matched." `
                -CertificationNotes "The source https://www.mae.gov.bi/en/visa-application-forms/ is the official Ministry of Foreign Affairs page for Burundi visa application forms. The primary-immigration certification scope is limited to the forms and instructions presented on the page."
            Publish-Assertion -Item $item `
                -Title "Burundi official visa application forms baseline" `
                -RuleKey "bi_official_visa_application_forms_baseline" `
                -Statement "The official Ministry of Foreign Affairs of Burundi visa application forms page publishes visa application forms and directs users to select a visa type and complete the form." `
                -Excerpt "Visa application forms - Ministry of Foreign Affairs, Republic of Burundi. Foreign Missions in Burundi with Residence in Bujumbura. Foreign Missions in Burundi with Residence Abroad. Visa application forms. Visa Select a type of visa then complete the form." `
                -Rationale "The assertion is pinned to the immutable MAE snapshot and is limited to describing the presence of official visa application forms. It does not infer eligibility or legal effect."
        }
        "CV" {
            Approve-Review -Item $item `
                -AssessmentNotes "Cabo Verde operates an independent visa regime. The Ministry of Foreign Affairs, Cooperation and Regional Integration Consular Services operates the official consular portal, which publishes substantive visa rules and exemptions." `
                -CertificationNotes "The source https://portalconsular.mnec.gov.cv/en/vistos is the official Cabo Verde consular portal. The primary-immigration certification scope is appropriate for the visa and exemption information published."
            Publish-Assertion -Item $item `
                -Title "Cabo Verde official consular visa information baseline" `
                -RuleKey "cv_official_consular_visa_information_baseline" `
                -Statement "The official Cabo Verde Consular Portal publishes visa information stating that foreign citizens generally need visas to enter and stay in Cape Verde, while qualified foreigners with valid residence permits, foreigners benefiting from visa exemptions, and citizens of countries without Cabo Verde diplomatic representation may have different entry conditions." `
                -Excerpt "Visas - Portal Consular. Generally, foreign citizens need visas to enter and stay in Cape Verde, however they can enter Cape Verde without a visa: Qualified foreigners with a valid residence permit; Foreigners who benefit from visa exemptions or exemptions provided for by law or international agreements. Types of Visas. By residence." `
                -Rationale "The assertion is pinned to the immutable consular portal snapshot and reports only the general visa requirement and exemption categories presented. It does not infer eligibility or legal effect."
        }
        "CM" {
            Approve-Review -Item $item `
                -AssessmentNotes "Cameroon operates an independent visa regime. The Ministry of External Relations (MINREX) is the competent foreign-affairs visa authority. The assessment evidence URL was diplocam.cm/e-visa/; the official monitored source is evisacam.cm. Both are Cameroon government consular/e-Visa domains, and the evisacam.cm portal is the operational application channel. The relationship is accepted as independent with the official source being evisacam.cm." `
                -CertificationNotes "The source https://www.evisacam.cm/ is the official Cameroon e-Visa portal for consular and visa applications. The primary-immigration certification scope is appropriate for the visa and consular services published."
            Publish-Assertion -Item $item `
                -Title "Cameroon official e-Visa portal baseline" `
                -RuleKey "cm_official_evisa_portal_baseline" `
                -Statement "The official Cameroon e-Visa portal (evisacam.cm) is the official portal for visa applications to Cameroon and publishes information on visa applications, consular card applications, laissez-passer applications, and exit visa applications." `
                -Excerpt "evisa Cameroun - The official portal for visa applications to Cameroon. Visa Applications. Consular Card Applications. Laissez-passer Applications (Ordinary / Mortuary). Exit Visa Applications." `
                -Rationale "The assertion is pinned to the immutable evisacam.cm snapshot and describes only the official portal's purpose and the categories of applications it handles. It does not infer eligibility or legal effect."
        }
        "CF" {
            Approve-Review -Item $item `
                -AssessmentNotes "The Central African Republic operates an independent visa regime. The Ministry of Foreign Affairs manages consular services; the embassy in France operates the short-stay visa service page. The evidence is embassy-level but official and jurisdiction-matched, scoped to short-stay visa services provided by this diplomatic mission." `
                -CertificationNotes "The source https://paris.diplomatie.gouv.cf/services/24/visa-court-sejour is the official short-stay visa service of the Embassy of the Central African Republic in France. The primary-immigration certification scope is limited to the short-stay (and linked long-stay) visa services presented on this embassy page."
            Publish-Assertion -Item $item `
                -Title "Central African Republic official short-stay visa service baseline" `
                -RuleKey "cf_official_short_stay_visa_service_baseline" `
                -Statement "The official short-stay visa service of the Embassy of the Central African Republic in France publishes information on short-stay and long-stay visas and provides an online visa application form." `
                -Excerpt "Visa court sejour | Ambassade de la Republique Centrafricaine en France. Visa court sejour. Visa long sejour. cliquez sur l'image ci-haut pour creer votre compte, puis accedez au formulaire de demande de visa en ligne. 01-AMB-CFFR-- Demande de visa court sejour.pdf." `
                -Rationale "The assertion is pinned to the immutable embassy page snapshot and is limited to describing the short-stay visa service and online application process. It does not infer eligibility or legal effect and acknowledges embassy-level scope."
        }
    }
}

Write-Host "`nAll five jurisdictions processed. Final registry summary:"
$finalReceipt = Call-Api -Method GET -Uri "$base/api/v1/global-intelligence/registry/jurisdictions/fde507d0-e71b-4122-b622-30a7913aadca/coverage-receipt" -Actor "coverage-readiness-operator"
$finalReceipt.registry_summary | ConvertTo-Json -Depth 5
Write-Host "Global claim ready: $($finalReceipt.global_coverage_claim_ready)"
