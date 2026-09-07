import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  buildV2VisibleWorkState,
  buildV2VisibleWorkStates,
  findV2VisibleWorkState,
} from "../lib/v2/visible-work-state.ts";

const employee = (semantic_state, overrides = {}) => ({
  position_key: "cto",
  title: "Chief Technology Officer",
  department: "Technology",
  reports_to_position_key: "ceo",
  authority_level: "executive",
  organization_status: "active",
  work_item_id: "work-phase7b",
  work_status: "running",
  semantic_state,
  presence_state: "not_asserted",
  state_reason: `Canonical ${semantic_state} state`,
  ...overrides,
});

test("Phase 7B reuses the sealed M.4.1 canonical employee-state mapping", () => {
  const expected = new Map([
    ["working", ["focused_work", "work_pulse", "WORK"]],
    ["blocked", ["blocked_wait", "blocked_pulse", "BLOCKED"]],
    ["awaiting_owner", ["awaiting_attention", "waiting_breathe", "OWNER"]],
    ["queued", ["queued_wait", "waiting_breathe", "QUEUED"]],
    ["completed", ["settled_idle", "settled_breathe", "DONE"]],
  ]);

  for (const [semanticState, [presentationState, motion, shortLabel]] of expected) {
    const model = buildV2VisibleWorkState(employee(semanticState));
    assert.equal(model.supported, true);
    assert.equal(model.kind, semanticState);
    assert.equal(model.presentationState, presentationState);
    assert.equal(model.motion, motion);
    assert.equal(model.shortLabel, shortLabel);
    assert.equal(model.canonicalSemanticState, semanticState);
    assert.equal(model.truth.canonicalStateSource, "LivingSceneEmployee.semantic_state");
    assert.equal(Object.isFrozen(model), true);
    assert.equal(Object.isFrozen(model.truth), true);
  }
});

test("Phase 7B semantic state remains truthful without inventing physical or adjacent semantics", () => {
  const blocked = buildV2VisibleWorkState(employee("blocked"));
  assert.equal(blocked.truth.presentationOnly, true);
  assert.equal(blocked.truth.canonicalStateWritable, false);
  assert.equal(blocked.truth.physicalPresenceClaimed, false);
  assert.equal(blocked.truth.physicalLocationClaimed, false);
  assert.equal(blocked.truth.physicalTravelClaimed, false);
  assert.equal(blocked.truth.locomotionAllowed, false);
  assert.equal(blocked.truth.conversationClaimed, false);
  assert.equal(blocked.truth.collaborationClaimed, false);
  assert.equal(blocked.truth.handoffClaimed, false);
  assert.equal(blocked.truth.blockerDetailsClaimed, false);
  assert.equal(blocked.truth.blockerResolutionClaimed, false);
  assert.equal(blocked.truth.completionEventClaimed, false);
});

test("Phase 7B does not require a work-item id to echo an already-canonical employee semantic state", () => {
  const model = buildV2VisibleWorkState(
    employee("awaiting_owner", { work_item_id: null, work_status: null }),
  );
  assert.equal(model.supported, true);
  assert.equal(model.kind, "awaiting_owner");
  assert.equal(model.truth.workItemRelationPresent, false);
  assert.equal(model.workItemId, null);
});

test("Phase 7B unknown semantic state fails to neutral/static presentation", () => {
  const model = buildV2VisibleWorkState(employee("future_unmodeled_state"));
  assert.equal(model.supported, false);
  assert.equal(model.kind, null);
  assert.equal(model.presentationState, "neutral_static");
  assert.equal(model.motion, "none");
  assert.equal(model.shortLabel, "STATIC");
});

test("Phase 7B index is deterministic and resolves by exact canonical position key", () => {
  const models = buildV2VisibleWorkStates([
    employee("queued", { position_key: "operations" }),
    employee("working", { position_key: "cto" }),
  ]);
  assert.deepEqual(models.map((model) => model.positionKey), ["cto", "operations"]);
  assert.equal(findV2VisibleWorkState(models, "operations")?.kind, "queued");
  assert.equal(findV2VisibleWorkState(models, "Operations"), null);
  assert.equal(Object.isFrozen(models), true);
});

test("Phase 7B renderer integration keeps semantic motion separate from ambience and tokenized", () => {
  const stage = readFileSync(
    new URL("../components/v2/V2LivingHqVisualStage.tsx", import.meta.url),
    "utf8",
  );
  const surface = readFileSync(
    new URL("../components/v2/V2CanonicalWorkStateSurface.tsx", import.meta.url),
    "utf8",
  );
  const css = readFileSync(
    new URL("../components/v2/V2CanonicalWorkStateSurface.module.css", import.meta.url),
    "utf8",
  );
  const tokens = readFileSync(new URL("../styles/v2/tokens.css", import.meta.url), "utf8");
  const workspace = readFileSync(
    new URL("../components/v2/V2OrganizationWorkspace.tsx", import.meta.url),
    "utf8",
  );

  assert.match(stage, /workState\?\.supported \? \(/);
  assert.match(stage, /<V2CanonicalWorkStateSurface/);
  assert.match(stage, /<V2AmbientCharacterSurface presentation=\{ambientRenderer\}>/);
  assert.match(surface, /data-blocker-details-claimed="false"/);
  assert.match(surface, /data-blocker-resolution-claimed="false"/);
  assert.match(surface, /data-completion-event-claimed="false"/);
  assert.match(surface, /data-physical-presence-claimed="false"/);
  assert.match(surface, /data-locomotion-allowed="false"/);
  assert.match(css, /var\(--aios-v2-motion-duration-semantic-work\)/);
  assert.match(css, /var\(--aios-v2-motion-duration-semantic-blocked\)/);
  assert.match(css, /var\(--aios-v2-motion-duration-semantic-wait\)/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(tokens, /--aios-v2-motion-duration-semantic-work:/);
  assert.match(workspace, /canonical employee state/);
  assert.match(workspace, /workStates=\{visibleWorkStates\}/);
});
