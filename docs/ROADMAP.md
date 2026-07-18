# Global Mobility AIOS Delivery Roadmap

The canonical product scope is defined in
[`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md). This
roadmap turns that complete vision into incremental delivery phases. A later phase
does not remove any capability from the canonical blueprint.

## Delivery Status — v10.22.21 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.21 adds a pending-review Africa coverage evidence tranche 2A for Eswatini (`SZ`), Lesotho (`LS`), Liberia (`LR`), Zambia (`ZM`), and Uganda (`UG`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 with usable content for all five selected endpoints. Algeria (`DZ`) and The Gambia (`GM`) were excluded after transport failures, and Nigeria (`NG`) was excluded after HTTP 403; retrieval controls were not weakened.
- Coverage readiness remains 65/243. No assessment or certification in this tranche has been approved, no baseline capture has been queued, no assertion or rule has been published, and the global coverage claim remains false. The content-addressed evidence pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.20 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.20 adds a pending-review Asia/Americas coverage evidence tranche 1B for the Republic of Korea (`KR`), Malaysia (`MY`), Chile (`CL`), Peru (`PE`), and Qatar (`QA`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 with usable content for all five selected endpoints. Thailand (`TH`), Vietnam (`VN`), and Mexico (`MX`) were excluded after controlled probes returned HTTP 403, a transport failure, and challenge-only content respectively; retrieval controls were not weakened.
- Coverage readiness remains 65/243. No assessment or certification has been approved, no baseline capture has been queued, no assertion or rule has been published, and the global coverage claim remains false. The content-addressed evidence pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.19 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.19 adds the Asia/Americas coverage evidence tranche 1A for Japan (`JP`), Indonesia (`ID`), Philippines (`PH`), Argentina (`AR`) and Brazil (`BR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 60/243 to 65/243; the global coverage claim remains false.
- Japan's official source is the Ministry of Justice English portal at `moj.go.jp/EN/`. Indonesia's official source is the Directorate General of Immigration portal at `imigrasi.go.id/`. The Philippines' official source is the Bureau of Immigration portal at `immigration.gov.ph/`. Argentina's official source is the National Migration Directorate page on the government portal at `argentina.gob.ar/interior/migraciones`. Brazil's official source is the Ministry of Justice and Public Security portal at `gov.br/mj/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, residence, justice, citizenship or foreigner-related content. The v10.22.19 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.18 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.18 adds the Europe coverage evidence tranche 1E for Romania (`RO`), Bulgaria (`BG`), Luxembourg (`LU`), North Macedonia (`MK`) and Serbia (`RS`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 55/243 to 60/243; the global coverage claim remains false.
- Romania's official source is the Ministry of Internal Affairs at `mai.gov.ro/`. Bulgaria's official source is the Ministry of the Interior at `mvr.bg/`. Luxembourg's official source is the government administrative portal at `guichet.lu/`, which redirects to `guichet.public.lu/` for service content. North Macedonia's official source is the Ministry of Internal Affairs at `mvr.gov.mk/`. Serbia's official source is the Ministry of Internal Affairs at `mup.gov.rs/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, residence, border-control or foreigner-related content. Luxembourg and North Macedonia required source-monitor allowlist remediation for canonical redirects (`www.guichet.lu` -> `guichet.public.lu` and `www.mvr.gov.mk` -> `mvr.gov.mk`); TLS verification was not bypassed. The v10.22.18 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.17 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.17 adds the Europe coverage evidence tranche 1D for Spain (`ES`), Portugal (`PT`), Italy (`IT`), Slovenia (`SI`) and Croatia (`HR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 50/243 to 55/243; the global coverage claim remains false.
- Spain's official source is the Ministry of Foreign Affairs, European Union and Cooperation portal at `exteriores.gob.es/`. Portugal's official source is the official government services portal at `eportugal.gov.pt/`, which redirects to `www.gov.pt/` and provides access to services including "Estrangeiros em Portugal" (Foreigners in Portugal). Italy's official source is the Ministry of the Interior at `interno.gov.it/`. Slovenia's official source is the Slovenian Government English portal at `gov.si/en/`. Croatia's official source is the Ministry of the Interior at `mup.gov.hr/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable foreigner, immigration, residence, work or migration content. Portugal's initial monitor fetch was blocked because the canonical `eportugal.gov.pt/` endpoint redirects to `www.gov.pt/`; the source monitor allowlist was remediated to include both domains without bypassing TLS verification. The v10.22.17 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.16 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.16 adds the Europe coverage evidence tranche 1C for Estonia (`EE`), Latvia (`LV`), Poland (`PL`), Czech Republic (`CZ`) and Greece (`GR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 45/243 to 50/243; the global coverage claim remains false.
- Estonia's official source is the Police and Border Guard Board at `politsei.ee/en/`. Latvia's official source is the Office of Citizenship and Migration Affairs at `pmlp.gov.lv/en/`. Poland's official source is the Office for Foreigners at `gov.pl/web/udsc/`. Czech Republic's official source is the Ministry of the Interior at `mv.gov.cz/mvcren/`. Greece's official source is the Ministry of Migration and Asylum at `migration.gov.gr/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable migration, citizenship, asylum or residence content. The v10.22.16 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.15 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.15 adds the Europe coverage evidence tranche 1B for Denmark (`DK`), Netherlands (`NL`), Belgium (`BE`), France (`FR`) and Ireland (`IE`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 40/243 to 45/243; the global coverage claim remains false.
- Denmark's official source is the Danish Immigration Service portal at `nyidanmark.dk/en-GB/`. Netherlands's official source is the Immigration and Naturalisation Service (IND) at `ind.nl/en/`. Belgium's official source is the FPS Foreign Affairs at `diplomatie.belgium.be/en/`. France's official source is the Ministry for Europe and Foreign Affairs (France Diplomatie) at `diplomatie.gouv.fr/en/`. Ireland's official source is Immigration Service Delivery at `irishimmigration.ie/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, visa, residence or travel content. The v10.22.15 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.14 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.14 adds the Europe coverage evidence tranche 1A for Iceland (`IS`), Norway (`NO`), Switzerland (`CH`), Sweden (`SE`) and Finland (`FI`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 35/243 to 40/243; the global coverage claim remains false.
- Iceland's official source is the Directorate of Immigration page on the Icelandic government portal at `island.is/s/utlendingastofnun`. Norway's official source is the Norwegian Directorate of Immigration English portal at `udi.no/en/`. Switzerland's official source is the State Secretariat for Migration English portal at `sem.admin.ch/sem/en/home.html`. Sweden's official source is the Swedish Migration Agency English portal at `migrationsverket.se/en.html`. Finland's official source is the Finnish Immigration Service English portal at `migri.fi/en`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration and residence content. The v10.22.14 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.13 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.13 adds the Asia/MENA coverage evidence tranche 1A for Oman (`OM`), Bahrain (`BH`), Georgia (`GE`), Singapore (`SG`) and the United Arab Emirates (`AE`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 30/243 to 35/243; the global coverage claim remains false.
- Oman's official source is the Royal Oman Police eVisa portal at `evisa.rop.gov.om/`. Bahrain's official source is the Bahrain Electronic Visa Service at `evisa.gov.bh/`. Georgia's official source is the Ministry of Foreign Affairs e-VISA PORTAL at `evisa.gov.ge/GeoVisa/`. Singapore's official source is the Immigration and Checkpoints Authority portal at `ica.gov.sg/`. The UAE's official source is the Federal Authority for Identity, Citizenship, Customs and Port Security (ICP) English portal at `icp.gov.ae/en/`, which provides federal-level identity and residency content.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable English-language immigration, visa or residency content. The UAE ICP root path (`https://icp.gov.ae/`) was also reachable, but the English path (`/en/`) provides clearer federal service content, so it was selected as the monitored source.
- The v10.22.13 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.12 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.12 adds the Africa coverage evidence tranche 1H for South Africa (`ZA`) and Seychelles (`SC`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 28/243 to 30/243; the global coverage claim remains false. South Africa's official source is the Department of Home Affairs portal at `dha.gov.za`. Seychelles's official source is the Electronic Border System at `seychelles.govtas.com/en`, which identifies itself as the official government website. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration/entry content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), Democratic Republic of the Congo (`CD`), Nigeria (`NG`), South Sudan (`SS`), Tanzania (`TZ`), Togo (`TG`), Uganda (`UG`), and Zambia (`ZM`) remain blocked or deferred. The v10.22.12 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.11 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.11 adds the Africa coverage evidence tranche 1G for Mauritius (`MU`) and Zimbabwe (`ZW`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 26/243 to 28/243; the global coverage claim remains false. Mauritius's official source is the Passport and Immigration Office portal at `passport.govmu.org/passport`, which describes passport and immigration services under the Director General of Immigration. Zimbabwe's official source is the Zimbabwe eVisa portal at `evisa.gov.zw`, operated by the Zimbabwe Immigration Department. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), Democratic Republic of the Congo (`CD`), and Zambia (`ZM`) remain blocked or deferred from earlier tranches. The v10.22.11 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.10 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.10 adds the Africa coverage evidence tranche 1F for Madagascar (`MG`), Malawi (`MW`), and Mozambique (`MZ`). All three jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 23/243 to 26/243; the global coverage claim remains false. Madagascar's official source is the eService of Tourism, Immigration and Emigration at `evisamada-mg.com/en/home`, which states it is the only official online visa application site of the Republic of Madagascar. Malawi's official source is the Malawi e-Visa System at `evisa.gov.mw`, operated by the Department of Immigration and Citizenship Services. Mozambique's official source is the eVisa and eTA portal at `evisa.gov.mz`, operated by the National Immigration Service. All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration/visa content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), and Democratic Republic of the Congo (`CD`) remain blocked or deferred from earlier tranches. The v10.22.10 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.9 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.9 adds the Africa coverage evidence tranche 1E for Kenya (`KE`) and Rwanda (`RW`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 21/243 to 23/243; the global coverage claim remains false. Kenya's official source is the Electronic Travel Authorization (eTA) portal at `evisa.go.ke`, operated by the Directorate of Immigration Services. Rwanda's official source is the Immigration and Emigration portal at `migration.gov.rw`, operated by the Rwanda Directorate General of Immigration and Emigration. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration content. The Democratic Republic of the Congo (`CD`) was deferred because the official `evisa.gouv.cd` page is a dynamic Inertia.js application with minimal generic-parser text extraction. Gabon (`GA`), Gambia (`GM`), and Guinea-Bissau (`GW`) remain blocked or deferred from earlier tranches. The v10.22.9 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.8 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.8 adds the Africa coverage evidence tranche 1D for Ghana (`GH`) and Guinea (`GN`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 19/243 to 21/243; the global coverage claim remains false. Ghana's official source is the Ghana Immigration Service e-Visa portal at `evisa.immigration.gov.gh`, which returned structured `GovernmentService` JSON-LD identifying the Ghana Immigration Service as the provider. Guinea's official source is the Police aux Frontieres (PAF) e-Visa page at `paf.gov.gn/visa`. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable content. Gambia (`GM`) and Guinea-Bissau (`GW`) were deferred from this tranche because a confirmed reachable official source was not yet identified; Gabon (`GA`) remains blocked by TLS certificate validation from the previous tranche. The v10.22.8 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.7 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.7 adds the Africa coverage evidence tranche 1C for Djibouti (`DJ`), Egypt (`EG`), and Ethiopia (`ET`). All three jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 16/243 to 19/243; the global coverage claim remains false. Egypt required canonical-source remediation from `https://www.visa2egypt.gov.eg/` to `https://www.visa2egypt.gov.eg/eVisa/Home` because the root path only returned a meta-redirect with no usable text; the remediation was applied through the controlled source-remediation path and audited. Gabon (`GA`) was removed from the planned tranche because the official `evisa.dgdi.ga` endpoint fails TLS certificate-chain validation inside the API container; TLS verification was not bypassed. The v10.22.7 evidence pack, operations receipt, and SHA-256 receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.6 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.6 adds the Africa coverage evidence tranche 1B for Chad and Cote d'Ivoire. Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 14/243 to 16/243; the global coverage claim remains false. Algeria remains excluded because of a TLS certificate-chain validation failure; Comoros and Congo (Brazzaville) were deferred from the original plan because a confirmed official source was not yet identified. The v10.22.6 evidence pack, operations manifest, and SHA-256 receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.5 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.5 completes the Africa tranche 1A evidence review and initial-rule publication cycle for the British Indian Ocean Territory, Angola, Benin, Burkina Faso, Burundi, Cabo Verde, Cameroon, and Central African Republic. All nine tranche 1A jurisdictions now have independently approved assessments and source certifications, immutable baselines, and active verified rules. Coverage readiness moved from 6/243 to 14/243; the global coverage claim remains false.
- v10.22.1 corrects PowerShell-relative manifest and receipt path resolution in the tranche operations scripts. Paths now resolve from the active PowerShell provider location instead of a stale host-process working directory; no API, database, evidence, review, assertion, publication, snapshot, or coverage state is changed.
- v10.22 adds safe multi-batch tranche operations: read-only expansion planning, offline manifest validation, mandatory dry-run preflight, consolidated review/baseline/assertion/readiness receipts, and optional confirmation-gated queueing for explicitly selected approved baselines. It creates no review decision, assertion, publication, snapshot mutation, regulatory change, or coverage claim.
- v10.21.2 adds review-gated supplemental official sources for domains where the approved primary portal is unsuitable for monitoring. Supplemental approvals require the existing approved primary authority/source and relationship, never supersede the primary certification, and can supply fresh evidence for a snapshot-pinned assertion.
- v10.21.1 fixes the tranche-assistant draft handoff: copying a constrained draft now confirms success, scrolls to the existing initial-rule assertion form, and focuses the title field without submitting or persisting any record.
- v10.21 adds a feature-flagged coverage tranche assistant that prepares review packets, rejects navigation-heavy snapshots, extracts exact candidate evidence lines, and can selectively queue approved baseline captures. It creates no approvals, assertions, publications, snapshot mutations, regulatory changes, or coverage claims.
- v10.20 adds audited before/after jurisdiction coverage-readiness receipts, read-only reconciliation, dashboard count verification, and safer empty-by-default evidence JSON.
- v10.19 adds controlled initial verified-rule assertions from independently approved immutable baseline snapshots. Assertions are content-addressed, require a different reviewer, publish only through a separate explicit action, and project to the knowledge graph without fabricating a regulatory-change event.
- v10.18.2 fixes the canonical-source remediation helper's post-commit reporting path and makes reruns idempotent. An earlier run that committed the URL change but failed while printing detached ORM attributes can now be safely confirmed without a duplicate audit event.
- v10.18.1 corrects the Austria starter-tranche monitor to a canonical HTTPS endpoint after the upstream short URL redirected to HTTP. The retrieval security policy remains fail-closed; existing deployments use an audited same-host source-remediation script before retrying baseline capture.
- v10.18 adds controlled, idempotent baseline capture for independently approved evidence-batch sources. It pre-creates durable retrieval runs, queues the exact monitored source through Celery, records immutable snapshots, and never publishes a verified rule or coverage claim.
- v10.17 adds the first current official-evidence tranche for Austria, Germany, Canada, Australia, and New Zealand, plus offline validation and a PowerShell submission workflow. The linked assessment/certification records still require independent decisions before baseline capture is eligible.
- v10.16 extends coverage evidence batches with atomic authority, official-source, and monitor onboarding plus automatically linked pending primary-source certification proposals.
- v10.15.1 fixed PostgreSQL-safe compilation of the `0030` coverage-batch index names and added an offline PostgreSQL migration regression gate.

- Phase 7 regulatory-intelligence foundation is complete.
- Phase 8 universal profile, pathway catalogue, comparisons, and single-pathway timelines are complete.
- Phase 9 document intelligence is complete: extraction, profile/application validation,
  expiry reminders, missing-document and inconsistency detection, human-reviewed integrity
  indicators, and signed expiring document access with production storage controls.
- Phase 10A self-updating intelligence, controlled classification, relational knowledge
  graph, and pathway-impact linking are complete.
- Phase 10C dashboard filtering is complete across freshness, coverage, authority,
  confidence, materiality, and review state.
- Phase 10D is complete: explicit reassessment acceptance preserves pinned assessments,
  while immutable country-ranking assessments compare only human-published pathways,
  explain costs, trade-offs, long-term residence dependencies, and uncertainty, and preserve
  the Phase 10B global-coverage claim boundary.
- Phase 10E is complete: immutable, human-confirmed multi-year and multi-country scenarios
  model reviewed study, graduate-rights, work, settlement, permanent-residence, and
  citizenship-review transitions. Reviewed rule changes create a new scenario version and
  never rewrite the original plan.
- Phase 10B now has a prioritized evidence worklist and atomic, idempotent evidence batches
  for up to 50 jurisdictions. The same package can onboard authorities, official sources, and
  monitors, then create pending certification proposals while preserving the separate-reviewer
  requirement. Approved batch items can now queue controlled baseline retrieval and immutable
  source snapshots, while pending or rejected evidence remains ineligible. Reviewed baseline
  assertions can now publish the first verified rule without misclassifying a baseline as a
  detected change. A feature-flagged tranche assistant now prepares review packets, evaluates
  baseline content quality, extracts exact candidate evidence, and selectively queues approved
  baselines without creating legal decisions or persistent assertion drafts. Review-gated
  supplemental sources preserve approved primary certifications while narrower domain sources
  can provide monitored evidence. Multi-batch tranche operations now consolidate stage, blocker,
  review, baseline, draft, and readiness receipts without bypassing human decisions. The initial
  Austria, Germany, Canada, Australia, and New Zealand tranche has completed all gates, proving
  the workflow end to end while global coverage remains incomplete.
- The remaining Phase 10 delivery work is factual Phase 10B evidence collection and human
  approval across every required jurisdiction.
- Global coverage claims remain blocked until the authority, source, freshness,
  verified-rule, and jurisdiction-assessment gates are complete.

### Recommended execution order

1. Use v10.22 read-only expansion planning to select the next 10–25 evidence gaps without inferring authorities or relationships.
2. Research and independently verify each jurisdiction's relationship, authority, source, and evidence scope.
3. Submit reviewed source packages through the v10.16 atomic evidence-batch path; use v10.21.2 supplemental sources only where an approved primary portal is unsuitable for monitoring.
4. Use the v10.22 operations manifest to run mandatory dry-run preparation across existing batches and produce consolidated review, baseline, assertion, and readiness queues.
5. Complete assessment and certification decisions with separate reviewer identities.
6. Queue only explicitly selected approved baselines; inspect failures without weakening retrieval controls.
7. Draft, independently review, and explicitly publish snapshot-pinned initial rules through the existing v10.19 workflow.
8. Confirm readiness with v10.20 receipts and review later detected changes through the existing classification and publication gates.
9. Maintain fresh monitors and expand coverage without claiming global completeness until every required jurisdiction passes all Phase 10B gates.

### Remaining-work ledger

- **Phase 9:** complete.
- **Phase 10B:** software workflow complete; jurisdiction evidence onboarding and independent
  review remain operationally incomplete.
- **Phase 10C:** complete.
- **Phase 10D:** complete.
- **Phase 10E:** complete.
- **Phases 11–13:** not started; all listed capability groups remain future work.

## Current Baseline: MVP Phases 1-5

- Local/Docker FastAPI and Next.js platform
- CRM, public intake, client return, lead detail, and operator workbench
- Official-source Truth Engine and human review queues
- Documents, MinIO-ready storage, browser OCR, and verification actions
- Eligibility assessment and coaching
- Opportunity catalogue and deterministic matching
- Controlled agents and asynchronous batch execution
- Draft communications and trigger-based automatic communication records
- Audit, RBAC, demo/release checks, and Alembic foundation

## Phase 6: Foundation Alignment

- Make this roadmap and the product blueprint canonical
- Repair controlled-agent contract tests
- Complete migrations for every current SQLModel table
- Align public routes, browser sessions, local header authentication, and CORS
- Refresh architecture and operational documentation
- Keep frontend build, API tests, schema checks, and repository policy green

## Phase 7: Regulatory Intelligence Foundation

- [x] Add jurisdiction, immigration authority, and source schedule models
- [x] Support country, territory, and autonomous-jurisdiction identifiers
- [x] Ingest official-source content into immutable snapshots with hashes and timestamps
- [x] Compare snapshots and produce structured regulatory change sets
- [x] Queue every material change for human validation
- [x] Publish approved verified rules with evidence links and effective dates
- [x] Execute scheduled retrieval through controlled background workers
- [x] Add safe generic HTML, text, JSON, XML, and PDF parser routing
- [x] Add a Next.js regulatory operations workspace for health, review, publication, rules, and evidence
- [x] Add rule supersession and explicit retirement controls with audit history
- [x] Expose source-monitor freshness, due-state, errors, and retrieval failures
- [x] Add transactional jurisdiction, authority, source, and monitor onboarding with domain allowlists
- [x] Add coverage and freshness rollups by jurisdiction, authority, and regulatory domain
- [x] Add configurable authority-specific gazette and structured API parser profiles
- [x] Detect new, changed, and retired programs from structured authority catalogues

## Phase 8: Universal Mobility Profile and Pathways

- [x] Expand the profile across education, work, skills, languages, family,
  finances, goals, constraints, consent, and evidence
  - [x] Add immutable versions, supersession, completeness, and readiness stages
  - [x] Validate lead-owned document evidence and record purpose-limited consent
  - [x] Restrict eligibility and opportunity processing after consent withdrawal
  - [x] Persist profile-version provenance on eligibility conclusions
  - [x] Add the operator profile workspace and version history
- [x] Build a versioned pathway catalogue for study, work, visa, scholarship,
  settlement, family, and digital-nomad routes
  - [x] Add immutable draft, published, superseded, and retired versions
  - [x] Require official sources, immutable snapshots, verified rules, and human review for publication
  - [x] Add deterministic profile matching with consent enforcement and missing-evidence results
  - [x] Add the pathway governance workspace and version ledger
- [x] Connect eligibility conclusions to verified rules and source references
  - [x] Persist pathway, version, source, snapshot, and verified-rule provenance in assessment factors
- [x] Add cost, risk, alternative-pathway, and missing-evidence explanations
  - [x] Persist comparisons against exact profile and pathway versions
  - [x] Separate payable fees, recurring costs, and minimum-funds thresholds
  - [x] Explain declared, evidence-derived, and regulatory-freshness risks
  - [x] Rank alternatives with tradeoffs, benefits, gaps, and source provenance
  - [x] Add the Mobility Planning workspace and immutable comparison history
- [x] Build the multi-stage mobility timeline engine
  - [x] Generate deterministic profile-to-settlement stages from an immutable pathway comparison
  - [x] Enforce sequential dependencies, profile consent, and exact profile/pathway-version provenance
  - [x] Require audited human approval notes for eligibility, route, application, submission, and decision gates
  - [x] Keep application approval, authority decisions, and regulatory claims in their existing controlled systems
  - [x] Add the Mobility Timelines operator workspace with evidence, blockers, ownership, and due dates

## Phase 9: Document Intelligence

- [x] Server-side OCR/extraction jobs and structured document schemas
  - [x] Add Celery extraction jobs tied to immutable upload hashes and exact schema versions
  - [x] Extract text server-side from text files, PDF text layers, and Tesseract-supported images
  - [x] Publish baseline schemas for passports, CVs, degrees, transcripts, employment letters, and bank statements
  - [x] Require human approval or rejection without automatically verifying authenticity or mutating profile facts
  - [x] Add restricted document-intelligence APIs and an operator review workspace
- [x] Validation against profile and application facts
  - [x] Compare only human-approved extractions with exact immutable profile versions
  - [x] Snapshot lead identity and application facts inside every assessment
  - [x] Separate matches, mismatches, missing values, and semantically non-comparable facts
  - [x] Require human assessment review without overwriting documents, profiles, or applications
  - [x] Add consistency findings and immutable assessment history to the Document Intelligence workspace
- [x] Expiry monitoring and reminders
  - [x] Add deterministic 90, 30, 7-day, and expired urgency bands
  - [x] Create immutable, deduplicated reminder tasks from recorded document expiry metadata
  - [x] Supersede stale tasks when urgency increases or an expiry date changes
  - [x] Schedule controlled scans and expose lead-scoped manual scanning
  - [x] Require human review notes without sending uncontrolled external messages
  - [x] Add expiry metrics, task review, and audit history to Document Intelligence
- [x] Missing-document and inconsistency detection
  - [x] Resolve exact human-published pathway versions, eligibility assessments, or application-domain requirement snapshots
  - [x] Create immutable, content-addressed coverage assessments without creating or modifying source records
  - [x] Distinguish satisfied, missing, optional, expired, rejected, unverified, mismatch, and duplicate-conflict outcomes
  - [x] Reuse approved document-consistency findings as broader cross-document risk signals
  - [x] Add deduplicated scheduled and lead-scoped scans with mandatory human review and audit history
  - [x] Add requirement metrics, findings, provenance, and review actions to Document Intelligence
- [x] Human-reviewed fraud-risk indicators
  - [x] Create immutable, content-addressed integrity assessments with exact source provenance
  - [x] Detect exact-file reuse, approved identity/material mismatches, duplicate conflicts, rejected evidence, and hash-integrity failures
  - [x] Detect approved identifier reuse across leads while storing only hashes and masked values
  - [x] Require controlled human triage without declaring fraud or taking adverse action
  - [x] Add scheduled and lead-scoped scans, audit history, metrics, and review controls
- [x] Signed, expiring document access and production object-storage controls
  - [x] Issue short-lived, audited access grants instead of durable or direct object URLs
  - [x] Enforce authenticated role, lead ownership, document scope, and purpose on every grant
  - [x] Support local storage and MinIO without exposing storage credentials or unrestricted object keys
  - [x] Record grant creation, access, expiry, revocation, denial, and actor provenance
  - [x] Add explicit revocation and fail-closed handling for expired, altered, missing, or unauthorized objects
  - [x] Add production bucket privacy, TLS, encryption, retention/lifecycle, backup, and recovery guidance
  - [x] Add restricted operator controls and regression coverage without changing document verification state

## Phase 10: Global Self-Updating Mobility Intelligence — Highest Priority

### 10A. Self-Updating Visa Intelligence Engine

- [x] Continuously schedule controlled retrieval from allowlisted government, authority, and gazette sources
- [x] Detect immutable source changes through content hashes and snapshot comparison
- [x] Extract generic HTML, text, JSON, XML, PDF, gazette, and structured programme catalogues
- [x] Classify new programmes, removals, rule changes, salary thresholds, age limits,
  occupation lists, quotas, processing times, and policy changes
- [x] Route every material change through human validation before verified-rule publication
- [x] Refresh relational intelligence and dashboards from reviewed changes and verified rules
- [x] Add controlled model-assisted classification proposals with confidence, evidence, and deterministic fallback
- [x] Add a provenance-preserving regulatory knowledge graph updated only from human-published rules
- [x] Link graph updates to affected pathway versions without silently changing client assessments

Target pipeline:

```text
Government website / official API / gazette
  -> controlled crawler
  -> immutable snapshot and extraction
  -> structured classification proposal
  -> deterministic comparison
  -> human validation when material
  -> verified rule and knowledge-graph update
  -> global dashboard refresh
```

Delivered classification governance: every detected change receives a persisted
deterministic proposal tied to exact snapshots and diff evidence. Operators can
request configured model assistance; invalid, unavailable, or disabled model
execution falls back deterministically with a visible reason. A human must
accept one proposal before the separate regulatory-change review and verified-
rule publication gates can proceed. See
`docs/CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md`.

Delivered graph governance: human-published verified rules now transactionally
project typed jurisdiction, domain, authority, source, snapshot, change, and
rule nodes with per-edge rule/change/snapshot provenance. Supersession and
retirement preserve history, while controlled synchronization ignores
unpublished rules. See `docs/REGULATORY_KNOWLEDGE_GRAPH_V10_5.md`.

Delivered pathway-impact governance: rule publication, supersession, and
retirement now create idempotent, review-gated links to exact currently
published pathway versions using jurisdiction, domain, source, and direct-rule
evidence. Existing pathway criteria, comparisons, timelines, and client
conclusions remain immutable; resolving an impact requires an explicitly
published newer pathway version. See
`docs/PATHWAY_REGULATORY_IMPACT_LINKS_V10_6.md`.

### 10B. Global Country and Immigration-Jurisdiction Coverage

- [x] Support country, territory, and autonomous-immigration-jurisdiction types
- [x] Support parent jurisdictions, authorities, official sources, domains, and independent schedules
- [x] Seed and version a canonical registry covering every UN member/observer state and ISO 3166-1 entry
- [x] Register autonomous jurisdictions and territories without inferring their immigration-rule relationship
- [x] Add evidence-backed proposal, separate-reviewer approval, rejection, and supersession for immigration-rule relationships
- [x] Add a prioritized region/gap worklist for the remaining jurisdiction evidence programme
- [x] Add atomic, idempotent evidence batches that create pending proposals only
- [x] Add atomic batch onboarding for authorities, official sources, and source monitors
- [x] Automatically link onboarded sources to pending primary-source certification proposals
- [x] Preserve independent review and immutable batch provenance at scale
- [x] Capture immutable baselines only after both jurisdiction and primary-source reviews pass
- [x] Create independently reviewed initial verified-rule assertions without fabricating source-change events
- [x] Reconcile verified-rule publication into audited jurisdiction coverage-readiness receipts and live dashboard counts
- [x] Add feature-flagged tranche preparation that rejects weak snapshots and never auto-approves or publishes legal evidence
- [x] Add multi-batch tranche operations planning, manifest validation, and consolidated dry-run receipts without automatic legal decisions
- [ ] Complete reviewed independent, inherited, shared, or not-applicable assessments for every required jurisdiction
- [x] Add separate-reviewer certification for each jurisdiction's primary immigration authority and official source
- [ ] Establish at least one reviewed primary immigration authority and official source per jurisdiction
- [x] Track country-level source, authority, freshness, verified-rule, and immigration-rule-assessment gaps
- [x] Prevent “global coverage” claims unless registry and source-coverage release gates pass

Delivered registry foundation: immutable dataset-hashed releases from the fixed
UN M49 source with ISO 3166-1 scope reconciliation, 249 active entries, a
reproducible import command, coverage-gap API, release gate, and operator ledger.
Territories remain `unassessed` for independent immigration rules until reviewed;
their presence in the registry is not treated as verified immigration coverage.

Initial named coverage includes Austria, Germany, Canada, UAE, Singapore, Japan,
New Zealand, South Korea, Brazil, South Africa, Qatar, Oman, Saudi Arabia, and
all remaining registry jurisdictions—not only this example list.

Delivered v10.15 coverage operations: a prioritized release-derived worklist and
immutable SHA-256-keyed evidence batches for up to 50 jurisdictions. Batches are
atomic, create only pending assessment/certification proposals, and never bypass
the separate-reviewer or global-coverage release gates. See
`docs/GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md`.

Delivered v10.16 source onboarding: the same atomic evidence package can create or update
a registry-bound regulatory authority, HTTPS official source, allowlisted source monitor,
and pending primary-source certification. Any invalid row rolls back the entire package;
source ownership conflicts and unsafe URLs still fail closed. Certification remains subject
to an independent reviewer and does not establish coverage by itself. See
`docs/GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md`.

Delivered v10.19 initial-rule governance: an approved batch item with an immutable baseline
snapshot can create a content-addressed assertion tied to the exact jurisdiction, source,
snapshot hash, domain, statement, excerpt, rationale, and confidence. The proposer cannot
review or publish it; independent approval and a separate explicit publication action create
a verified rule. Knowledge-graph provenance records the initial assertion rather than a
fictional regulatory change, and the Opportunity Radar remains change-event-only. See
`docs/INITIAL_RULE_ASSERTIONS_V10_19.md`.

Delivered v10.20 readiness reconciliation: assertion-backed rule publication now returns and
audits the exact jurisdiction evidence-gate state before and after publication. Read-only
receipts expose remaining gaps and registry-wide counts; repeated publication is idempotent.
The Coverage workspace displays whether publication completed jurisdiction readiness, while
detected-change and Opportunity Radar counts remain event-only. Placeholder evidence JSON is
no longer preloaded. See `docs/COVERAGE_READINESS_RECEIPTS_V10_20.md`.

Delivered v10.21 tranche preparation: a disabled-by-default assistant assembles review packets,
scores immutable baseline content, rejects navigation-heavy pages, extracts exact candidate
evidence lines, and offers constrained assertion suggestions for human editing. It never creates
or approves review records, persists assertions, publishes rules, changes snapshots, or makes
coverage claims. Apply mode can only queue explicitly selected approved baseline captures. See
`docs/COVERAGE_TRANCHE_ASSISTANT_V10_21.md`.

Delivered v10.21.2 supplemental-source governance: an independently approved primary source and
authority can be preserved while a narrower `supplemental_<domain>` source enters its own
pending-review, baseline, assertion, and publication sequence. Supplemental approvals never
supersede the primary certification, and coverage freshness may use either approved source while
primary authority/source gates remain primary-only. See
`docs/SUPPLEMENTAL_OFFICIAL_SOURCES_V10_21_2.md`.

Delivered v10.22 tranche operations: read-only expansion planning converts the prioritized
coverage worklist into blank human-research plans. Offline manifest validation and a mandatory
dry-run preflight can prepare multiple existing evidence batches, then emit consolidated JSON
and CSV receipts for blockers, review queues, baseline states, candidate drafts, and readiness.
Optional apply mode can only queue explicitly selected API-eligible baselines and cannot review,
submit assertions, publish rules, mutate snapshots, create regulatory changes, or make coverage
claims. See `docs/COVERAGE_TRANCHE_OPERATIONS_V10_22.md`.

Delivered v10.17 official evidence starter: a validated, content-addressed pack prepares
Austria, Germany, Canada, Australia, and New Zealand for review using current official
authority and immigration portal evidence. Submission creates five pending immigration-rule
assessments and five pending primary-source certifications; it creates no approvals, source
snapshots, verified rules, or coverage claim. Combined rows link each assessment to the exact
newly onboarded official source. See
`docs/GLOBAL_COVERAGE_OFFICIAL_EVIDENCE_STARTER_V10_17.md`.

Delivered v10.18 controlled baseline capture: independently approved batch items can create
durable queued retrieval runs and dispatch the exact allowlisted monitors through the existing
controlled Celery worker. Existing snapshots and queued/running work are not duplicated; failed
runs remain visible for deliberate retry. The workflow captures evidence only and cannot publish
a verified rule or satisfy the global-coverage gate by itself. See
`docs/CONTROLLED_COVERAGE_BASELINE_CAPTURE_V10_18.md`.

### 10C. Live Global Intelligence Dashboard

- [x] New Visa Programmes dashboard with introductions, removals, provenance, and visible review state
- [x] Immigration Changes dashboard with countries and changes updated today
- [x] Processing-Time dashboard with windowed change history and visible review state
- [x] Skilled-Occupation dashboard with shortage/eligible-list changes
- [x] Salary and Investment Threshold dashboard
- [x] Global country activity heatmap across onboarded jurisdictions
- [x] Evidence-based Opportunity Radar calculated only from human-published events
- [x] Freshness, coverage, authority, confidence, materiality, and review-state filters
  - [x] Apply one evidence scope consistently to counts, change feeds, heatmaps, and Opportunity Radar
  - [x] Expose verified-rule or classification-proposal confidence provenance without inventing confidence
  - [x] Preserve pending-review visibility while keeping the Opportunity Radar human-published-only
- [x] Explicitly label activity signals as evidence summaries—not predictions or visa recommendations

Delivered foundation: `GET /api/v1/global-intelligence/dashboard` and the
`/global-intelligence` operator workspace. The dashboard deliberately displays
an onboarded-coverage warning until the Phase 10B global registry release gate passes.

### 10D. Global User Intelligence Engine

- [x] Maintain one immutable universal profile across education, experience,
  skills, languages, family, finances, goals, constraints, consent, and evidence
- [x] Rank published pathways with risks, costs, evidence gaps, alternatives, and provenance
- [x] Generate dependency-controlled operational case timelines
- [x] Rank best-fit countries across the complete reviewed global catalogue
  - [x] Persist immutable, content-addressed country-ranking assessments against an exact profile and published pathway-version set
  - [x] Require explicit user acceptance and human review before generating a new country-ranking assessment
  - [x] Preserve the Phase 10B release gate by labelling incomplete scope as reviewed-published-catalogue-only
- [x] Explain country-level tradeoffs, long-term goals, PR/citizenship dependencies, and uncertainty
  - [x] Derive ranking scores deterministically from profile fit, confidence, and reviewed pathway risk
  - [x] Surface costs, processing ranges, evidence gaps, coverage posture, and route alternatives by country
  - [x] Read permanent-residence and citizenship dependencies only from human-published pathway metadata and never infer missing rules
  - [x] Add uncertainty scoring and explicit non-recommendation/non-guarantee labels
- [x] Reassess only when the user explicitly accepts a new profile or reviewed regulatory version

### 10E. Multi-Year Global Mobility Timeline

- [x] Generate operational profile-to-settlement milestones for one selected pathway
- [x] Model versioned transitions across study, graduate rights, work permits,
  skilled migration, settlement, permanent residence, and citizenship eligibility
- [x] Support dated multi-country scenarios such as Austria study (2026), graduate
  permit (2028), RWR Card (2029), RWR Plus (2031), permanent residence (2034),
  and citizenship-eligibility review (2035)
- [x] Recalculate downstream stages when verified rules change while preserving the original scenario
- [x] Never present future eligibility dates as guarantees; require reviewed rules and human confirmation


Delivered country-ranking governance: explicit user acceptance creates an immutable
assessment tied to the exact profile version, published pathway versions, and registry
release posture. Countries are grouped and ranked only from human-published pathway
evidence. Permanent-residence and citizenship dependencies are surfaced only when they
exist in reviewed pathway metadata; missing data becomes visible uncertainty, never an
inference. Until Phase 10B passes, every response is labelled
`reviewed_published_catalogue_only` and cannot claim complete global ranking coverage. See
`docs/REVIEWED_GLOBAL_COUNTRY_RANKING_V10_13.md`.

Delivered multi-year scenario governance: explicit user acceptance and human review create
an immutable scenario version from exact published pathway versions, verified rules, source
snapshots, operator-confirmed durations, and dated dependencies. Reviewed pathway-impact
replacements can create a new scenario version; the prior scenario and all of its dates and
evidence remain unchanged. Every stage states that future eligibility is not guaranteed and
must be re-verified before action. See `docs/MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md`.

Historical and predictive analytics remain gated until sufficient verified history exists.

## Phase 11: Business and Wealth Mobility — Not Started

- [ ] Corporate accounts, employees, dependants, sponsors, relocations, and compliance
- [ ] Entrepreneur and startup mobility
- [ ] Residency/citizenship by investment
- [ ] HNWI and family-office mobility
- [ ] Tax residency and treaty intelligence with specialist-review controls

## Phase 12: Channels, Ecosystem, and Automation — Not Started

- [ ] Dedicated client portal and mobile application
- [ ] Employer and partner portal with tenant isolation
- [ ] Versioned public/partner APIs
- [ ] Email, messaging, calendar, CRM, and case-event automation
- [ ] Government and mobility-agency workflows

## Phase 13: Global Scale Platform — Not Started

- [ ] Progressive coverage of all recognized countries and independent jurisdictions
- [ ] OpenSearch/Elasticsearch when validated search requirements exceed PostgreSQL
- [ ] Neo4j when validated graph traversal requires a dedicated graph store
- [ ] Durable event streaming and Temporal-class workflows when scale requires them
- [ ] OpenTelemetry, Prometheus, Grafana, Loki, tracing, SLOs, backups, and DR exercises
- [ ] Kubernetes and AWS/Azure/GCP/on-premise deployment profiles when operationally justified

## Delivery Rules

Every phase must include:

- Source provenance and Truth Engine integration for regulated claims
- Controlled agent permissions and human-review defaults
- Audit events for sensitive actions and state transitions
- Database migration and rollback paths
- Backend tests and frontend type/build validation
- Security, privacy, consent, retention, and operational notes
- Documentation updates and coverage-ledger status changes
## v10.22.5 — Africa tranche 1A completion

- Completes independent assessment and source-certification review for the British Indian Ocean Territory (`IO`), Angola (`AO`), Benin (`BJ`), Burkina Faso (`BF`), Burundi (`BI`), Cabo Verde (`CV`), Cameroon (`CM`), and Central African Republic (`CF`).
- Publishes narrow, snapshot-pinned initial verified rules for all eight jurisdictions through the separate proposer/reviewer/publisher identities.
- Moves coverage readiness from 6/243 to 14/243 and verified-rule count from 6 to 14.
- Keeps the global coverage claim false because 229 required jurisdictions remain incomplete.
- Algeria (`DZ`) remains blocked by official-endpoint TLS validation; TLS verification was not bypassed.
- Adds v10.22.4 regression tests in `apps/api/tests/test_coverage_v10_22_4_reconciliation.py` covering source-only supplemental assessment reuse, local pending/rejected assessment precedence, mandatory source certification, and snapshot provenance.
- Replaces deprecated `session.query()` usage in `apps/api/tests/test_eligibility.py` with `session.exec()`.
- Adds `.gitattributes` for LF/CRLF normalization to reduce line-ending noise on Windows.
- Makes `apps/api/tests/conftest.py` robust to shallow Docker container directory structures.
- Updates `docs/ROADMAP.md` and records the operational receipts in the local `coverage-operations-receipts/` folder.
- No database migration, automatic evidence approval, snapshot mutation, regulatory-change claim, or global coverage claim.

## v10.22.4 — Supplemental baseline assessment reconciliation

- Baseline eligibility may reuse the latest independently approved jurisdiction assessment when a source-only supplemental batch intentionally omits a duplicate assessment.
- Supplemental reconciliation preserves explicit supplemental certification scope and also recognizes source-only batches through the intentional absence of a batch-local assessment.
- A batch-local pending or rejected assessment continues to take precedence and is never bypassed.
- The supplemental source certification remains batch-item-specific and must be independently approved.
- Initial-rule assertion proposals use the same controlled reconciliation for source-only supplemental items while continuing to require the item's own approved source certification and immutable baseline snapshot.
- No database migration, automatic evidence approval, rule publication, snapshot mutation, or coverage claim.
