# Repository Policy

This document defines the controlled GitHub repository set allowed for Global Mobility AIOS.

## Policy Goals

- Keep the platform buildable and production-focused.
- Reduce legal and licensing risk.
- Avoid unrelated or high-risk dependencies.
- Maintain auditable provenance of imported patterns and code.

## Core Repositories (Approved)

1. global-mobility-aios
   - Main product repository and integration boundary.
2. joyozhang333-lgtm/awesome-ai-organization
   - AI organization blueprint: departments, role templates, governance, approval chains.
3. bennet287/agency-agents
   - Customized AI employee library for visa, education, recruitment, documents, sales, compliance.
4. langchain-ai/langgraph
   - Stateful workflow orchestration and human-in-loop process control.
5. crewAIInc/crewAI
   - Department-level multi-agent execution.
6. n8n-io/n8n
   - Automation and business integrations for follow-ups and operational workflows.
7. fastapi/fastapi
   - Backend API framework.
8. qdrant/qdrant
   - Vector store for semantic memory and retrieval.
9. minio/minio
   - S3-compatible object storage for document artifacts.
10. ollama/ollama
   - Local model runtime for phase-1 local-first operation.
11. langfuse/langfuse
   - LLM tracing, evaluation, observability, and auditability.
12. promptfoo/promptfoo
   - AI prompt regression, adversarial evaluation, and safety testing for controlled agents.
13. open-telemetry/opentelemetry-python and open-telemetry/opentelemetry-python-contrib
   - Vendor-neutral application/AI telemetry foundation (SDK, FastAPI instrumentation, OTLP exporters).
   - License: Apache 2.0.
   - Used as an optional, disabled-by-default Technology Radar V1.1 Wave 1 pilot.
   - AIOS Semantic Sovereignty: OpenTelemetry remains engineering trace only and never substitutes
     for OrganizationActivity, AuditLog, evidence provenance, or business authority.
14. Cisco-Talos/clamav
   - Open-source antivirus engine and malware scanner for untrusted document upload handling.
   - License: GNU GPL v2 (with linking exception for the official client libraries).
   - Used as an optional, disabled-by-default Technology Radar V1.1 Wave 1 pilot.
   - AIOS Semantic Sovereignty: a clean scan is an engineering safety signal, not evidence of
     authenticity, legal sufficiency, or evidence validity. An infected result may reject an upload.
15. DS4SD/docling
   - Open-source document normalization and structured document understanding library.
   - License: MIT.
   - Used as an optional, disabled-by-default Technology Radar V1.1 Wave 2 pilot.
   - AIOS Semantic Sovereignty: Docling output is a machine-readable normalization signal, not
     evidence of authenticity, legal sufficiency, or evidence validity; extracted values still
     require human review and authority verification.

## Adapted Repositories (Constrained Use)

1. omkarcloud/botasaurus
   - Use only for official-source collection pipelines that respect terms and law.
2. eosphoros-ai/DB-GPT
   - Optional later-stage data assistant over operational PostgreSQL with controlled scope.
3. vllm-project/semantic-router
   - Intent/model routing between domains like visa, education, recruitment, and sales.
4. career-ops
   - Adapt selected patterns into recruitment workflow modules.
5. osv-scanner/osv-scanner
   - CI dependency vulnerability scanning.

## Reference Only (No Direct Production Dependency)

- notebooklm-py
- RAG-Tutorials
- awesome-openclaw-agents
- Awesome-AI-Security
- awesome-security-GRC
- kubescape (defer to later Kubernetes phases)
- chaitanyagiri/munder-difflin, snapshot `v0.4.4`
  - Existing MIT-licensed vendored reference snapshot under `vendor/munder-difflin/v0.4.4`.
  - It is not an approved runtime/build dependency and must remain isolated from production imports,
    package manifests, execution paths, and authority semantics unless a later architecture/legal
    review explicitly promotes a bounded component.
  - Upstream comments/changelogs may mention providers or repositories excluded by AIOS policy;
    repository-policy substring scanning therefore does not rewrite or classify those vendored
    upstream bytes as Global Mobility AIOS product source.
- superradcompany/microsandbox, research pin `288ef7c89fe3048abff44521db2ef5ec330e4b1c` (Apache-2.0)
- mem0ai/mem0, research pin `19cb89aff472325c707f64b2f34ae6afdbf7faf7` (Apache-2.0)
- volcengine/OpenViking, research pin `e8cedaebd72c9bead112a337a58768368af9c5fb` (AGPL-3.0; research only)
- agno-agi/agno, research pin `2e8ca8dd926608953e907d7e8e7388e0c310d8f5` (Apache-2.0)
- CopilotKit/CopilotKit, research pin `a68fd0b2536dad5d88ec93d98f78e53c3627310d` (MIT)
- ag-ui-protocol/ag-ui, research pin `1d85ef42caef8a289b5e3839f5a63ffa622e703e` (MIT)
- mukul975/Anthropic-Cybersecurity-Skills, research pin `1b3f6b2286981381a5cc0566551ef3bb6bc38383` (Apache-2.0; community project)
- openfga/openfga, research pin `a7dfe8491dc7f9cd5905f4e9ae6c8e1d718c4bd9` (Apache-2.0)
- open-policy-agent/opa, research pin `8e733384254aa0211f0464852f2881f83d700bf1` (Apache-2.0)
- cedar-policy/cedar, research pin `468eaef41a4fd27c17a02cef48b58bce7f2034fc` (Apache-2.0)
- authzed/spicedb, research pin `1ba6b9714f0a1af73d20033c63977d963f2a9a84` (Apache-2.0)
- modelcontextprotocol/modelcontextprotocol, research pin `ca4ab3027f7c844cd3039c956438d72e8253f7f5` (license review required)
- a2aproject/A2A, research pin `f63dbb48271940ca5bd421f87e27e4d6ec002795` (Apache-2.0)
- UKGovernmentBEIS/inspect_ai, research pin `56c9cae65844c87479b10e212a93b91e1a17c351` (MIT)
- NVIDIA/garak, research pin `8ed1543b985a5722adb659584182faf6f7907d4e` (Apache-2.0; authorized defensive evaluation only)

These V1.3.5/V1.3.6 entries authorize source/documentation research at the stated pins only. They are not approved package, runtime, hosted-service, skill-installation or production dependencies. Promptfoo remains separately listed as an approved pilot source above.

## Explicitly Excluded Categories

1. Claude leak or clone repositories.
2. Unauthorized offensive security or exploit frameworks; bounded defensive evaluation tools require explicit policy listing and engagement scope.
3. Cybersecurity lab/training repositories for unrelated or ungoverned attack simulation.
4. Entertainment/unrelated repositories.
5. AGPL-heavy dependencies for core networked production services without legal review.

## Dependency Intake Rules

1. Any new external repository requires architecture and legal review.
2. Default decision for non-listed repositories is deny until approved.
3. Copying patterns is preferred over importing broad, high-risk dependency trees.
4. Every adopted dependency must document:
   - Purpose
   - License
   - Security posture
   - Upgrade and maintenance owner
5. All dependencies must pass vulnerability scanning in CI.

## Ownership

- Product owner approves business fit.
- Engineering lead approves technical fit and maintainability.
- Security/compliance owner approves legal and risk posture.
