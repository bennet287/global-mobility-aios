# Investment Program Onboarding Readiness v11.7

Phase 11.7 makes the empty investment-program catalogue operationally legible. It does not seed sample records or treat a draft as verified.

Each jurisdiction advances through these gates:

1. Active official source in the investment, wealth, business, or entrepreneur domain.
2. Content-addressed snapshot from that exact source.
3. Mobility pathway draft grounded in the snapshot.
4. Independent publication of the pathway.
5. Investment-program draft tied to the published pathway version and snapshot.
6. Independent publication of the program.

The readiness API is available at:

`GET /api/v1/investment-mobility/onboarding/readiness`

It returns jurisdiction counts, current state, blockers, and the next controlled action. The Investment Programs workspace presents the same pipeline.

Country matching alone is not sufficient source grounding. Sources from visa or unrelated regulatory domains are rejected for investment programs.

This delivery completes the readiness and diagnosis workflow. Actual jurisdiction onboarding remains incomplete until real official-source evidence is captured and separate authenticated reviewers publish the pathway and program versions.
