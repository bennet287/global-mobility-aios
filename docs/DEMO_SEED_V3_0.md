# Demo Seed v3.0

## Goal

v3.0 creates a clean, intentional demo state for presenting the local MVP.

The seed contains exactly four `demo_v3_0` leads:

```text
1. Blocked Visa Claim
2. Documents Pending
3. Ready For Application
4. Completed Journey
```

## Safety

By default, the script deletes and recreates only rows connected to:

```text
Lead.source = demo_v3_0
```

It does not delete non-demo local data unless you explicitly pass:

```powershell
--reset-all --yes
```

## Run

From the repository root:

```powershell
python scripts/seed_demo_data.py
```

For a completely clean local demo database:

```powershell
python scripts/seed_demo_data.py --reset-all --yes
```

## Demo Scenarios

### Demo 1 - Blocked Visa Claim

Unsafe claim:

```text
Germany student visa is guaranteed without financial proof.
```

Expected behavior:

```text
Truth rejected
Human review required
Sales/application progression blocked
```

### Demo 2 - Documents Pending

Truth is clear, but documents are incomplete.

Expected behavior:

```text
Missing documents visible
Application not ready
Follow-up available
```

### Demo 3 - Ready For Application

Truth is clear and all documents are verified.

Expected behavior:

```text
Controlled application draft allowed
Human approval still required before submission
```

### Demo 4 - Completed Journey

Application is approved by authority.

Expected behavior:

```text
Lead converted
Onboarding tasks completed
Client communication drafts reviewed
Audit log populated
```

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py
python scripts/check_repo_policy.py --root .
$env:PYTHONPATH = "apps/api"
python -m pytest apps/api/tests -q
```

## Files changed

```text
scripts/seed_demo_data.py
apps/api/tests/test_demo_seed.py
docs/DEMO_SEED_V3_0.md
```
