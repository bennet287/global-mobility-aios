# Global Mobility AIOS — Active Product & Delivery Roadmap

**Roadmap generation:** V11.1 / Technology Radar V1.1 alignment
**Date:** 2026-08-18
**Development branch:** `roadmap/global-mobility-aios-v11`
**Accepted product baseline:** Phase 13.16.9 Evidence and provenance UX consolidation — COMPLETE / PASS (sealed by this delivery checkpoint)
**Active product slice:** Phase 13.16.10 — Responsive, accessibility, polish, and integrated acceptance — UNLOCKED / NEXT
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical **active strategic and delivery roadmap** for [Global Mobility AIOS](GLOBAL_MOBILITY_AIOS_VISION_V1.md).
It is intentionally optimized for current direction, gates, sequence, and architecture rather than carrying the full
chronological implementation ledger inline.

The complete roadmap state through the sealed `f0688a8` baseline is preserved byte-for-byte at
[archive/ROADMAP_THROUGH_F0688A8_2026-08-17.md](archive/ROADMAP_THROUGH_F0688A8_2026-08-17.md). The historical changelog through
that baseline is preserved at [archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md](archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md).
Current delivery checkpoints continue in [CHANGELOG.md](CHANGELOG.md).

---

## 1. Product definition

Global Mobility AIOS is a **governed global mobility intelligence operating system** for the movement of people, talent,
families, businesses, and capital across borders. It is not merely a visa chatbot, study-abroad search product, CRM,
document uploader, or collection of disconnected agents.

The product combines:

- CRM, intake, identity, consent, and long-lived case continuity;
- universal mobility profiles and goal/constraint context;
- official-source and regulatory intelligence;
- pathway discovery, versioning, comparison, and eligibility reasoning;
- evidence, provenance, document intelligence, cost, risk, and timeline planning;
- appointments, submissions, agency and authority workflow;
- post-arrival, renewal, settlement, residence, citizenship, and global strategy progression;
- governed agents and department runtimes;
- explicit organizational authority and human-review gates;
- durable WorkItems, Decisions, Blockers, Dependencies, Human Actions, Contributions, Activity, and audit state;
- role-specific experiences for Owner/Board, Professionals/Operators, Mobility Users, and future partners/employers.

### North-star lifecycle

```text
Dream / Goal
   ↓
Profile + constraints
   ↓
Country / pathway discovery
   ↓
Eligibility + evidence + risk + cost + timeline comparison
   ↓
Study / Work / Family / Business / Investment / Remote-work move
   ↓
Documents / submissions / appointments / authority decisions / compliance
   ↓
Post-arrival / employment / business operation
   ↓
Renewal / status change / family progression
   ↓
Permanent or long-term residence
   ↓
Citizenship / global mobility strategy
```

The lifecycle is branching, not a forced funnel. Changed facts, failed assumptions, new goals, changing laws, alternate
pathways, and different user types must remain first-class.

---

## 2. Product surfaces and authority model

The canonical experience split is:

- **Global Mobility AIOS Cockpit** — Owner / Human Board control surface;
- **Board Room** — reserved Board authority-execution module inside Cockpit, not the name of the whole control surface;
- **Operations** — Professional / Operator experience;
- **My Mobility** — Mobility User experience;
- `/my-mobility` — non-sensitive orientation/access surface;
- `/portal` — secure token/device-bound personalized client workspace.

Backend authorization is authoritative. Navigation, route visibility, title, prompt wording, model capability, or UI
presence never grants business, legal, publication, certification, submission, or organizational authority.

### Experience direction

The product should feel like premium enterprise software with a distinct AI operating-system identity, not a generic SaaS
admin dashboard and not dark sci-fi. The visual baseline remains deep navy/graphite with warm ivory, selective editorial
serif plus operational sans, restrained depth/glass, high-quality icons, subtle motion, luxury-level spacing, and beautiful
information density.

---

## 3. Permanent governance and evidence invariants

These rules are product architecture, not optional UX copy:

1. **AIOS Semantic Sovereignty** — third-party infrastructure can implement capabilities; AIOS owns domain meaning.
2. **Evidence before regulated certainty** — retrieval, OCR, model output, source diffs, or signature validation are not legal truth.
3. **Explicit authority** — authority comes from deterministic contracts and gates, never model confidence or prompts.
4. **Human review remains human review** — required professional, source, certification, publication, Board, or external-action gates cannot be silently automated away.
5. **Navigation is not authorization** — frontend visibility never substitutes for backend enforcement.
6. **Durable organization semantics remain distinct** — WorkItem, Blocker, Dependency, Decision, HumanActionRequest, HumanAction, Contribution, Activity, and AuditLog are not interchangeable.
7. **Provider replacement must remain possible** — provider IDs are mappings, not semantic primary keys.
8. **Truthful unknowns** — absent or mismatched evidence must remain unknown/not-established rather than becoming inferred clearance.
9. **Preserved databases are evidence** — do not mutate preserved SQLite/PostgreSQL merely to produce a demo.
10. **Austria simulation safety remains frozen** — uncertain Austria v4 state must not be promoted into production certainty.

---

## 4. Current accepted baseline

Phase 13.16.7 is sealed at commit `f0688a872e7e6977b69d1f9ff0607b647fc71d14`.

Accepted evidence at that checkpoint includes:

- secure token/device-bound Mobility User portal experience;
- client-safe human-activated mobility plan projection;
- approved/aligned evidence-summary projection;
- truthful no-plan state;
- focused client portal/CORS regressions PASS;
- design foundation 24/24 PASS;
- Next.js 15.2.4 production build 41/41 PASS;
- complete API regression 811 passed / 5 skipped / 0 failed;
- reviewed-plan and no-plan browser/runtime acceptance PASS;
- Alembic `0076_organization_position_active_identity`;
- 118 registered model tables, 118 actual model tables, 119 physical tables including only `alembic_version` infrastructure;
- preserved `gmai.db` unchanged during the accepted browser/runtime work.

Phase 13.16.8 Professional / Operator experience is accepted by this checkpoint. Accepted evidence includes:

- the existing Operations workspace and native `/leads/[id]` case workspace refined rather than a parallel dashboard;
- Eligibility restored as a first-class Professional / Operator navigation destination;
- the professional reading order frozen as decision/context → blockers and uncertainty → governed next actions → supporting evidence/review state → technical provenance;
- a persisted `PathwayComparison` used as the current-decision anchor, with timeline and document-assessment evidence admitted to current state only when their persisted profile/pathway/version context aligns;
- historical/context-mismatched timeline and document-assessment records excluded from current blockers, evidence counts, readiness, and journey conclusions while remaining inspectable through visible context state and technical provenance;
- the latest EligibilityAssessment shown as useful persisted case context without falsely claiming full alignment to the current comparison where the contract cannot prove it;
- authority appointments, submissions, agency assignments, and checklist rows presented as case operations rather than evidence for the selected pathway unless an explicit aligned relationship is persisted;
- design-foundation **25/25 PASS**, request/auth **4/4 PASS**, Next.js 15.2.4 production build **41/41 PASS**, repository policy **PASS**, release consistency **PASS**, Docker production profile **PASS**, database migration/schema consistency **PASS**, local physical-schema parity **PASS**, and `git diff --check` **PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed**, carried forward because the context-alignment correction and final documentation work do not modify backend/API/model/schema/Alembic code;
- browser/runtime acceptance across aligned data-rich, deliberate context-mismatch, and sparse/uncertain cases **PASS**, including human visual review of all three full-page captures;
- browser fixture traffic limited to read-only `GET`/`HEAD`/`OPTIONS` semantics, with no case-open mutation;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31` unchanged through the accepted runtime work and re-verified before seal.

The Phase 13.16.8 implementation introduces no backend endpoint, model, schema, migration, authorization expansion,
client-portal projection widening, publication/certification semantic change, Technology Radar runtime dependency,
Coworker/OpenWorker runtime implementation, preserved-database mutation, or Austria legal-safety change.

Phase 13.16.9 Evidence and provenance UX consolidation is accepted by this checkpoint. Accepted evidence includes:

- one shared, presentation-only `EvidenceProvenance` grammar used across Professional Case, Pathway Catalogue, Independent Source Review, and Document Intelligence;
- a consistent distinction between official source, immutable snapshot, certification/review state, VerifiedRule, pathway evidence, case evidence, superseded/historical state, and unresolved gaps;
- explicit evidence-boundary copy preventing source references, retrieval, OCR/extraction, review state, pathway evidence, or case evidence from being silently promoted into legal truth, certification, publication, or authority outcomes;
- Professional Case provenance remaining subordinate to the persisted current-decision/context-alignment rules accepted in 13.16.8;
- Pathway Catalogue presenting official source → immutable snapshot → human-published VerifiedRule → immutable pathway version → superseded history while preserving backend publication authority;
- Independent Source Review presenting official source → immutable snapshot → deterministic review pack → independent-human certification state while keeping VerifiedRule creation and pathway publication separate;
- Document Intelligence presenting stored case evidence → derived extraction → consistency review → requirement coverage → integrity review → unresolved gaps while explicitly rejecting automated authenticity/fraud/legal-sufficiency conclusions;
- design foundation **26/26 PASS**, request/auth **4/4 PASS**, Next.js 15.2.4 production build **41/41 PASS**, repository policy **PASS**, release consistency **PASS**, Docker production profile **PASS**, database migration/schema consistency **PASS**, local physical-schema parity **PASS**, and `git diff --check` **PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed** carried forward because the exact 13.16.9 implementation/docs boundary contains no backend/API/model/schema/Alembic change;
- isolated Edge production-browser captures for all four evidence-heavy surfaces, with direct human review of the settled full-page screenshots **PASS**;
- runtime fixture request trace **61 requests / 31 GET / 30 OPTIONS / 0 mutating methods**, covering all four evidence surfaces;
- browser harness semantic-verifier failure classified as a harness false negative: two DOM snapshots were written before their final async state settled, and the Professional Case verifier additionally expected a source title where the designed summary intentionally renders a source-reference count; the later full-page screenshots and request trace were inspected directly rather than claiming an automated semantic-verifier PASS;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31` unchanged throughout static and runtime acceptance.

The Phase 13.16.9 implementation introduces no backend endpoint, model, schema, migration, authorization expansion,
publication/certification authority change, client-portal projection widening, Technology Radar runtime dependency,
Coworker/OpenWorker runtime implementation, preserved-database mutation, or Austria legal-safety change.

Technology Radar V1 was separately established as a docs-only architecture/governance checkpoint. V1 remains historical
evidence; Technology Radar V1.1 is now the active platform-evolution direction.

---

## 5. Active delivery sequence

| Slice | State | Intent / gate |
|---|---|---|
| **13.16.7** | **COMPLETE / PASS** | Governed Mobility User experience sealed at `f0688a8` |
| **13.16.8** | **COMPLETE / PASS** | Governed Professional / Operator decision workspace accepted with context-aligned evidence composition |
| **13.16.9** | **COMPLETE / PASS** | Shared evidence/provenance presentation grammar accepted across four evidence-heavy Professional surfaces |
| **13.16.10** | **UNLOCKED / NEXT** | Responsive/accessibility/polish/integrated acceptance after accepted 13.16.9 evidence/provenance consolidation |
| **13.17** | **LOCKED** | Genuine external-human acceptance after integrated role experience is ready |
| **Final Phase 13 disposition** | **LOCKED** | Deterministic release disposition after 13.16 + 13.17 evidence |
| **Phase 14** | **NOT STARTED / DEMAND-GATED** | Scale validated product; do not redesign around infrastructure prematurely |

### 5.1 Phase 13.16.8 — Professional / Operator experience

**Intent:** provide experts and internal operators with a high-information-density workspace that preserves source
provenance, uncertainty, review state, case operations, and authority workflow.

The first implementation should refine/consolidate existing surfaces rather than create a parallel dashboard. Likely
surfaces include the Operations shell, lead/case workspace, eligibility, planning, pathways, timelines, document
intelligence, source review/certification, agent review, authority appointments, submission checklists, agency workflows,
and department workspaces.

The operator mental model should prioritize:

```text
Decision / case context
        ↓
Blockers + uncertainty
        ↓
Governed next actions
        ↓
Supporting evidence + review state
        ↓
Technical provenance / audit detail
```

A critical acceptance invariant is **context alignment**: comparison, timeline, pathway/version, profile/version, and
document-assessment records may be shown together as current decision evidence only when their identifiers/provenance
align. Historical or mismatched records may remain visible but must be labeled and must not silently contribute current
blockers, evidence counts, or readiness conclusions.

13.16.8 should leave an intentional future UX seam for AIOS Coworker, but it must not introduce speculative Coworker
runtime dependencies into the active slice.

**State: COMPLETE / PASS — 2026-08-18.**

The accepted implementation refines `/`, `/leads/[id]`, Professional/Operator navigation, and premium presentation
without adding a parallel dashboard or backend contract. Current pathway evidence is composed conservatively around the
persisted pathway-comparison decision spine. Context-aligned timeline/document evidence may contribute to the current view;
historical, unassigned, or mismatched records are explicitly excluded from current blockers/evidence/readiness while
remaining inspectable. Latest eligibility remains separately labeled where full context alignment cannot be proven.

Browser/runtime acceptance covered three deliberately different states:

1. **aligned data-rich** — aligned timeline/document evidence contributes current blockers and evidence state;
2. **deliberate context mismatch** — newer mismatched records are visibly excluded while older aligned records remain current;
3. **sparse / uncertain** — no comparison means no invented current decision context, no imported historical blockers, and no inferred clearance.

All three captures passed human visual review. Browser-open fixture traffic remained read-only, the preserved database
remained unchanged, and the governance/reliance/authority boundaries remain intact.

### 5.2 Phase 13.16.9 — Evidence and provenance UX consolidation

**State: COMPLETE / PASS — 2026-08-18.**

Evidence-heavy Professional surfaces now use one shared presentation grammar while preserving each underlying domain's
existing authority and lifecycle semantics. Users/operators can distinguish official source, immutable retrieved snapshot,
certification/review state, VerifiedRule, pathway evidence, case evidence, superseded/historical state, and unresolved gaps
without a new backend evidence model.

Accepted surfaces:

1. **Professional Case** — current decision evidence chain remains context-aligned and subordinate to the persisted comparison;
2. **Pathway Catalogue** — source → snapshot → VerifiedRule → immutable pathway version → superseded history;
3. **Independent Source Review** — source → snapshot → deterministic review pack → independent-human certification boundary;
4. **Document Intelligence** — stored case evidence → derived extraction → consistency/requirement/integrity review → unresolved gaps.

The shared component is presentation-only: it does not fetch, mutate, certify, publish, authorize, or create evidence.
TechnicalDisclosure remains the deeper identifier/version/timestamp technical-provenance layer where appropriate.

Static/build/repository/schema acceptance passed, and isolated production-browser captures were reviewed across all four
surfaces. The automated semantic verifier itself is **not** recorded as PASS because two DOM files were captured before the
final async render settled and one Professional Case assertion expected a source title although the designed summary uses a
source-reference count. The later full-page screenshots, Edge/CDP logs, and 61-row read-only request trace were inspected
directly and accepted. No mutating browser fixture traffic occurred.

### 5.3 Phase 13.16.10 — responsive/accessibility/polish/integrated acceptance

**State: UNLOCKED / NEXT.**

Acceptance must cover desktop/mobile, keyboard navigation, screen-reader semantics, contrast/hierarchy, loading/error/empty
states, role separation, cross-role handoffs, and integrated Owner + Mobility User + Professional/Operator journeys.

### 5.4 Phase 13.17 — genuine external-human acceptance

This remains deliberately different from simulated/shadow correctness testing. Phase 13.17 starts only after the role
experiences are integrated and the repository/runtime evidence shows they are ready for genuine external-human use.

---

## 6. Technology Radar V1.1 — active platform-evolution architecture

The authoritative active radar is [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md). Permanent integration boundaries
live in [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md) and
[ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md). The frozen V1 snapshot is
[TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md).

V1.1 adds strategic fit tiers while preserving evidence-driven adoption classification.

### 6.1 A+ — strongest strategic fit

| Technology | AIOS role | Classification |
|---|---|---|
| Docling | document normalization / structured understanding | ADOPT / EARLY PILOT |
| Presidio | sensitive-data detection/transformation for Privacy Gateway | ADOPT / EARLY PILOT |
| Promptfoo | AI regression, adversarial, safety evaluation | ADOPT / EARLY PILOT |
| OpenTelemetry | vendor-neutral application/AI telemetry | ADOPT / EARLY PILOT |
| urlwatch | official-source change monitoring | ADOPT / EARLY PILOT |
| ClamAV | upload quarantine / malware scanning | ADOPT / EARLY PILOT |
| OpenWorker (`andrewyng/openworker`) | AIOS Coworker / finished-work execution reference | **STRATEGIC REFERENCE / CONTROLLED PILOT** |
| Temporal | durable long-running execution | STRATEGIC PILOT |
| OpenFGA | fine-grained relationship authorization | STRATEGIC PILOT |

### 6.2 A — specialist candidates

- **pgvector** — semantic retrieval candidate;
- **Pydantic AI** — typed production agent-runtime candidate;
- **Langfuse** — LLM/agent observability behind OpenTelemetry;
- **PaddleOCR** — mature OCR candidate;
- **Unlimited-OCR** — advanced OCR/VLM candidate;
- **DSPy** — offline model/program optimization;
- **Gotenberg** — general document/PDF rendering;
- **Typst** — premium professional report generation;
- **EU DSS** — EU electronic-signature validation.

### 6.3 B / conditional candidates

Qdrant, Fides, OpenLineage, OPA, OpenFeature, Haystack, and MarkItDown remain conditional/benchmark candidates. Do not remove
a candidate merely because an unrelated technology is better overall. Remove it when another candidate demonstrably owns
the same capability better and AIOS no longer benefits from maintaining both.

### 6.4 Responsibility separation

```text
OpenWorker      = Coworker / finished-work execution reference
Pydantic AI     = typed AIOS agent-runtime candidate
DSPy            = offline model/program optimization
Temporal        = execution durability
OpenTelemetry   = neutral telemetry
Promptfoo       = evaluation / regression
```

These responsibilities must not be collapsed simply because several technologies are adjacent to AI/agent execution.

---

## 7. AIOS Coworker — future product capability

**AIOS Coworker** is the AIOS-owned capability for governed finished work. OpenWorker is a strategic reference/potential
adapter, not the domain abstraction.

```text
Human asks for an outcome
        ↓
AIOS resolves case / evidence / organization context
        ↓
Governed WorkItem + authority + human-action boundaries
        ↓
AIOS Coworker execution plane
        ↓
files + tools/MCP + connectors
        ↓
finished professional deliverable
        ↓
governed real-world outcome
        ↓
provenance + permitted learning/evaluation signals
```

Candidate outcomes include employer mobility packs, missing-evidence analysis, professional case briefs, authority
correspondence review, client follow-up, case chronology, qualification evidence memos, Board briefings, regulatory-change
analysis, evidence registers, email/calendar actions, and reconciliation against new VerifiedRules.

The objective is:

> **Do the work, produce the artifact, preserve provenance, and learn from the outcome.**

Third-party coworker/runtime implementations may not redefine WorkItem, Blocker, Dependency, HumanActionRequest,
ExecutiveDecision, Contribution, Activity, authority, evidence/legal truth, certification, publication, or business outcome
semantics.

---

## 8. Internal Learning & Quality — first-class platform direction

Subject to applicable law, contractual commitments, declared processing purposes, required safeguards, and the relevant
data-use policy, Global Mobility AIOS should maximize lawful learning from the work it performs.

The platform must keep three uses distinct:

1. **Operational intelligence** — understand bottlenecks, workload, case friction, source quality, and outcomes.
2. **Evaluation & quality** — measure correctness, correction rates, retrieval/OCR quality, agent success, tool failures, and regressions.
3. **Training & optimization** — build permitted corpora for fine-tuning, specialized models, prompt/program optimization, retrieval/ranking improvement, document classifiers, workflow prediction, and agent-planning improvements.

### 8.1 Human corrections are governed learning signals

```text
AI/model/OCR/retrieval output
        ↓
professional decision / correction / confirmation
        ↓
difference + provenance
        ↓
Learning Record
        ↓
Evaluation Corpus
        ↓
Training Candidate Corpus
        ↓
Permitted Training Corpus
        ↓
shadow evaluation + regression
        ↓
controlled promotion
```

Corrections must never rewrite authoritative legal/business records merely to create training data.

### 8.2 Training and evaluation lineage

AIOS should eventually be able to establish which source categories, datasets, transformations, human corrections,
jurisdictions, effective-date cutoffs, held-out evaluation corpora, benchmark results, and promotion decisions contributed
to a model/program version.

Conceptual records include `TrainingDataset` and `ModelVersion`, with dataset purpose/provenance/permitted usages and model
training/evaluation/promotion lineage.

### 8.3 Future data-use policy boundary

A future `AIOSDataUsagePolicy` layer should represent allowed / conditional / excluded uses such as service operation,
quality assurance, analytics, agent/safety evaluation, workflow/retrieval/document improvement, prompt/program improvement,
human quality review, and internal model training. It should preserve processing purpose, applicable lawful-basis or
compatibility analysis, tenant, provenance, sensitivity class, retention class, and training lineage where relevant.

The architecture exists to make permitted learning traceable and enforceable. It does **not** imply every operational
record is automatically trainable.

### 8.4 EU compliance direction

Where GDPR applies, production learning/evaluation/training involving personal data requires the applicable processing
purpose, legal basis or compatibility analysis, transparency, minimisation, retention/security controls, and other required
safeguards. Special-category personal data requires an applicable Article 9 condition and additional safeguards.

Current EDPB/European Commission guidance supports case-specific analysis for AI model development and deployment rather
than a blanket permission or blanket prohibition. If AIOS later becomes a provider of a general-purpose AI model under the
EU AI Act, the relevant provider obligations and training-content lineage requirements must be assessed separately.

This is an engineering/compliance architecture direction, not a final legal determination for any future processing regime.

---

## 9. Platform Evolution waves

Technology Radar is a **parallel evidence-driven evolution track**. It does not reorder the Phase 13 product sequence.
Candidates may correctly end as ADOPT, HOLD, or REJECT.

### Wave 0 — architecture and governance — COMPLETE

- Technology Radar and candidate-evaluation contract;
- provider-neutral adapter rule;
- AIOS Semantic Sovereignty;
- Internal Learning & Quality Principle;
- training/evaluation lineage direction;
- AIOS Coworker / OpenWorker architecture;
- EU processing-purpose/data-use architecture.

**No runtime dependency is required by this checkpoint.**

### Wave 1 — low-blast-radius quality foundation

`Promptfoo + OpenTelemetry + ClamAV`

### Wave 2 — document + privacy intelligence

`ClamAV → Docling → OCR providers → AIOSDocumentArtifact → Presidio/Privacy Gateway → Evidence → learning signals`

Candidates: Docling, PaddleOCR, Unlimited-OCR, Presidio.

### Wave 3 — regulatory intelligence monitoring

`official source → change detection/urlwatch → RegulatoryChange candidate → AI analysis → human/source review → VerifiedRule`

Never: `website changed → law automatically changed`.

### Wave 4 — AI runtime + retrieval + quality

Pydantic AI; pgvector vs Qdrant benchmark; DSPy; Langfuse behind OpenTelemetry; Promptfoo; initial Learning & Evaluation Plane.

### Wave 5 — AIOS Coworker + organization execution

OpenWorker reference/controlled pilot; Temporal; OpenFGA; governed files/tools/connectors; durable execution; finished
deliverables; outcome learning. AIOS remains the organization.

### Wave 6 — professional output

Gotenberg; Typst; EU DSS. Target outputs include Mobility Assessments, Employer Packs, Evidence Registers, Case
Chronologies, Risk Registers, Board Briefs, Qualification Memos, professional reports, and provenance appendices.

---

## 10. Phase 14 relationship

Phase 14 remains a **scale-validated-product** programme, not permission to redesign the system around infrastructure.
Measured needs may eventually justify dedicated search, selected retrieval infrastructure, graphs, streaming, Temporal,
OpenTelemetry/SLOs, OpenFGA, or other radar winners.

AIOS Coworker is a product capability rather than merely Phase-14 infrastructure. It may begin as a bounded Platform
Evolution pilot after Phase 13 acceptance if measured product evidence supports it.

---

## 11. Acceptance and repository discipline

Every implementation slice must follow the established deterministic workflow:

1. verify exact branch/SHA and clean baseline;
2. read canonical docs relevant to the slice;
3. perform bounded discovery;
4. freeze exact file/change boundary;
5. implement incrementally inside that boundary;
6. run focused and broad acceptance appropriate to the change;
7. perform runtime/browser review for user-facing work;
8. update this active roadmap for every project patch;
9. update `CHANGELOG.md` for meaningful delivery/checkpoint closure;
10. stage exact intended files only;
11. run staged diff/whitespace checks;
12. commit truthfully and push the exact branch;
13. fetch and verify local SHA == remote SHA;
14. verify clean working tree;
15. create an immutable `.local/archives/...zip` baseline and record SHA256 when working from the canonical local repository.

Never invent PASS evidence. A missing dependency/tool is an environment limitation, not a successful check.

---

## 12. Canonical documents to read for ongoing work

At minimum:

- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [REPOSITORY_POLICY.md](REPOSITORY_POLICY.md)
- [DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md)
- [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)
- operator UX/review specifications relevant to the active slice;
- this `ROADMAP.md` and current `CHANGELOG.md`;
- archived roadmap/changelog only when detailed historical evidence is required.

---

## 13. Current decision

**Continue with Phase 13.16.10 responsive/accessibility/polish/integrated acceptance.**

Technology Radar V1.1 is now the canonical parallel Platform Evolution architecture. Its Wave 0 direction is active for
architecture/governance, while runtime pilots remain evidence-gated and must not interrupt the 13.16 product sequence.

Long-term flywheel:

> **More governed work → more outcomes → more permitted corrections → more intelligence → better evaluation/training → better AIOS → higher-quality work.**
