## Reserve Mode

You have exceeded a cost cap, or you are very close to one. Wind down this
iteration as cheaply as possible instead of starting new work. These
instructions override the current step:

1. **Finish in-progress work minimally** -- bring whatever is open to a safe,
   committed state; do not begin anything new.
2. **Update memory** with what was accomplished and what remains.
3. **Settle your children** -- for each settled child, either merge its finished
   work now (`fractal node merge <branch>`, one child at a time) or hand it off
   by naming the branch and its merge-readiness in memory and in the parent
   report, so stranded descendants are never silently orphaned when this run
   ends.
4. **Report to parent** via radio:
   ```bash
   fractal radio send "<summary>" --parent --subject="<subject>" --priority=<0-10>
   ```

The loop decides at this iteration's boundary whether the run ends or continues
-- do not defer wind-down work past this iteration: it may never run. Do **not**
run `fractal node finish` yourself, with one exception: if your charter's
requirements are already fully verified, finish deliberately with a short
goal-met reason (`fractal node finish --reason="<what was verified>"`) -- the
run then books `completed` even if spend crosses the cap during the drain, with
the overshoot recorded on the run row. The loop's own abort phrases
(`cost budget ... (spent $...)`, `subtree cost budget ... (spent $...)`) are
reserved -- a reason bearing one classifies the finish as a budget abort -- so
write your reason in your own words. Budget semantics live in the `fractal`
skill's Cost section.
