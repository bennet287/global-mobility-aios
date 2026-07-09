# Demo Snapshot Export v5.2

## Goal

v5.2 adds a local demo snapshot exporter so an operator can capture the current demo state before or after a walkthrough.

The exporter is read-only. It does not change leads, run agents, approve outputs, review drafts, send messages, or reset data.

## Added Files

- `scripts/export_demo_snapshot.py`
- `apps/api/tests/test_demo_snapshot.py`
- `docs/DEMO_SNAPSHOT_EXPORT_V5_2.md`

## What The Snapshot Includes

- Demo readiness status.
- Demo lead count.
- Demo controlled-agent run count.
- Demo client communication draft count.
- Demo-related audit log count.
- Per-lead summaries.
- Agent status counts.
- Public client draft status counts.
- Key audit highlight counts.
- Demo operator URLs.
- Safety rules.

## Commands

Export JSON:

```powershell
python scripts/export_demo_snapshot.py --format json
```

Export Markdown:

```powershell
python scripts/export_demo_snapshot.py --format markdown --output demo-snapshot-v5.2.md
```

Use a different local URL:

```powershell
python scripts/export_demo_snapshot.py --base-url http://localhost:9000 --format markdown
```

## Safety Rules

- Controlled agents create internal operator outputs only.
- Agent output conversion creates reviewable client communication drafts only.
- Client communication drafts require human review before manual send/export.
- No automatic email, WhatsApp, portal message, application submission, or lead conversion is performed by the local MVP.

## Verification

Expected local quality gate after this patch:

```text
51 passed, 1 warning
Local quality gate passed.
```

The remaining warning is the existing external Starlette `TestClient` warning.
