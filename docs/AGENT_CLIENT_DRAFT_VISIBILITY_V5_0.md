# Agent Client Draft Visibility v5.0

## Status

Implemented as a conversion safety fix after local manual testing.

## Problem

Approved `client_drafting_agent` outputs converted successfully and wrote a `FollowUp`, but the converted draft did not appear in the Client Communication Review pages.

The conversion message used:

```text
[agent_output_conversion:v4.2]
```

The client communication module only recognizes reviewable communication drafts when the follow-up message contains:

```text
[client_communication_draft:v2.6]
```

So the conversion was persisted but invisible to the draft review queue.

## Change

`apps/api/app/routers/controlled_agents.py` now writes converted client-drafting outputs with the same draft marker and metadata format used by the Client Communication Review module:

```text
[client_communication_draft:v2.6] template=agent_client_update title=Agent drafted client update subject=... body=... note=...
```

Converted drafts are still stored with enum-safe status:

```text
FollowUp.status = pending
public communication.status = draft
```

The channel is now:

```text
email_draft
```

No automatic email, WhatsApp, portal message, or send action is introduced.

## Regression Coverage

Updated:

```text
apps/api/tests/test_controlled_agents.py
```

The conversion test now verifies that:

- converted client drafting outputs contain the client communication draft marker
- converted drafts use `email_draft`
- converted drafts appear in `/api/v1/client-communications/drafts`
- public communication status is `draft`
- template key is `agent_client_update`

## Verification

Run:

```powershell
python scripts/check_local_quality.py
```

Expected:

```text
Local quality gate passed.
45 passed
```

Manual local test:

1. Generate `Draft Client Update` for Demo 3.
2. Approve the `client_drafting_agent` output.
3. Convert the approved output.
4. Open `/admin/client-communications/drafts`.

Expected:

```text
Demo 3 - Ready For Application appears as a draft.
No automatic sending occurs.
```
