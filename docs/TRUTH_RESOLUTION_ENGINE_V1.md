# Truth Resolution Engine v1

Truth Resolution Engine v1 provides a controlled way to move blocked leads forward after the Truth Engine rejects or flags a claim.

## Purpose

The system must not simply ignore rejected visa, job, or immigration claims. Instead, a human reviewer must:

1. Attach or verify official source evidence.
2. Resolve or supersede the unsafe claim.
3. Create a corrected source-backed claim where appropriate.
4. Close pending human reviews.
5. Let downstream Sales and Application guardrails recalculate.

## Core routes

```text
GET  /api/v1/truth/resolution-queue
GET  /api/v1/leads/{lead_id}/truth-resolution
POST /api/v1/truth/claims/{claim_id}/resolve
POST /api/v1/truth/claims/{claim_id}/supersede
POST /api/v1/truth/leads/{lead_id}/corrected-claim
POST /api/v1/truth/leads/{lead_id}/close-reviews
GET  /admin/truth-resolution
GET  /debug/truth-resolution
```

## Design rule

Rejected and review-required truth states are upstream blockers. Sales and Application workflows should only progress when Truth Resolution reports no blocking rejected claims, no truth claims requiring human review, and no pending human reviews.

## Evidence policy

By default, resolving a rejected claim requires at least one official source reference attached to the claim. This protects the platform from silently clearing misinformation without evidence.

## Safe state model

Truth resolution changes old unsafe claims into non-blocking `resolved` or `superseded` states where the current data model supports those fields. It also clears `requires_human_review` where supported.

Downstream systems continue to compute their own stages. This module does not directly force sales/application progression.
