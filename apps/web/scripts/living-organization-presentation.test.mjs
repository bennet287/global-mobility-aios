import assert from "node:assert/strict";
import { test } from "node:test";

import { deriveLivingEmployeePresentation } from "../lib/living-organization-employee-presentation.ts";

const employee = (semantic_state, presence_state = "not_asserted") => ({
  semantic_state,
  presence_state,
});

test("M.4.1 maps canonical semantic state to bounded presentation state", () => {
  const cases = [
    ["working", "focused_work", "work_pulse"],
    ["blocked", "blocked_wait", "blocked_pulse"],
    ["awaiting_owner", "awaiting_attention", "waiting_breathe"],
    ["queued", "queued_wait", "waiting_breathe"],
    ["completed", "settled_idle", "settled_breathe"],
    ["unexpected", "neutral_static", "none"],
  ];

  for (const [semantic, expectedState, expectedMotion] of cases) {
    const result = deriveLivingEmployeePresentation(employee(semantic));
    assert.equal(result.canonicalSemanticState, semantic);
    assert.equal(result.state, expectedState);
    assert.equal(result.motion, expectedMotion);
  }
});

test("M.4.1 presentation never claims presence or locomotion", () => {
  for (const semantic of ["working", "blocked", "awaiting_owner", "queued", "completed", "unknown"]) {
    const result = deriveLivingEmployeePresentation(employee(semantic));
    assert.equal(result.presentationOnly, true);
    assert.equal(result.presenceClaimed, false);
    assert.equal(result.locomotionAllowed, false);
    assert.equal(result.canonicalPresenceState, "not_asserted");
  }
});
