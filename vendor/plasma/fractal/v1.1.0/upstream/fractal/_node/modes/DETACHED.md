## Detached Mode

Each step is a separate session with no shared context. Rebuild from your
**radio private channel** (`fractal radio read --channel=private`), **memory**
(`$MEMORY_DIR`), and recent **saved messages**
(`fractal radio messages --saved`). Before finishing, write a concise handoff
for the next step:

```bash
fractal radio send "<context>" --node=$CURRENT_BRANCH --channel=private --subject="<subject>" --priority=<0-10>
```
