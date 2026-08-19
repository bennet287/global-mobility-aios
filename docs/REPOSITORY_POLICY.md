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

## Explicitly Excluded Categories

1. Claude leak or clone repositories.
2. Offensive security or exploit frameworks.
3. Cybersecurity lab/training repositories for unrelated attack simulation.
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
