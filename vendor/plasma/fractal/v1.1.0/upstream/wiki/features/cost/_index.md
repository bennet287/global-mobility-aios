---
name: features/cost
desc: |
  Cost accounting and budgets: how spend is measured and attributed, how
  token usage is priced, the run/iteration/step cost cap tiers with their
  reserve window, and the time budget tiers with the pause credit-back.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T11:36:38Z
---

# features/cost

[[features/_index|..]]

[[features/cost/budgets|budgets]]: The cost budget cap tiers and their
enforcement: the per-run subtree-shared run cap, the per-iteration and per-step
caps, the reserve window that steers wind-down before the ceiling, and how
remaining headroom is read.

[[features/cost/measurement|measurement]]: How spend is measured and attributed:
cost figures flow from agent streams into per-step ledger rows in the central
database, roll up through iterations and runs, and include descendant nodes
through the per-run subtree chain. Unknowable cost is recorded as null and
disclosed, never conflated with a genuine zero.

[[features/cost/pricing|pricing]]: How token usage becomes dollars: the cached
LiteLLM price table, its refresh and staleness semantics, and the unpriced-model
contract.

[[features/cost/time_budgets|time_budgets]]: Time budgets: the run, iteration,
and step timeout tiers, how remaining time is derived from configured limits and
row start instants, and the pause credit-back that keeps frozen time from
charging against run and iteration deadlines.

***

Covers how fractal measures and bounds spend, in dollars and in wall-clock time.
The dollar side runs from raw agent streams to enforced ceilings:
[[features/cost/measurement|measurement]] describes how every step's spend lands
in the central ledger and rolls up through iterations, runs, and the subtree;
[[features/cost/pricing|pricing]] describes how token counts become dollars and
what happens when a model has no price; [[features/cost/budgets|budgets]]
describes the cap tiers that stop the loop and the reserve window that turns the
last slice of budget into wind-down. The wall-clock side,
[[features/cost/time_budgets|time_budgets]], mirrors the same run/iteration/step
tiering for timeouts and explains how pauses stop the clock. Both are read live
through `fractal node cost` and `fractal node time`.
