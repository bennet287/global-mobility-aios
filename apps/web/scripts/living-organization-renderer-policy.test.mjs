import assert from "node:assert/strict";
import { test } from "node:test";

import {
  acquireLivingSceneRendererCanvasLease,
  assertLivingSceneRendererModelNonAuthoritative,
  createLivingSceneSelection,
  isLivingSceneSelection,
} from "../lib/living-organization-renderer-policy.ts";

test("renderer refuses an authoritative scene model", () => {
  assert.doesNotThrow(() => assertLivingSceneRendererModelNonAuthoritative({ sceneAuthoritative: false }));
  assert.throws(
    () => assertLivingSceneRendererModelNonAuthoritative({ sceneAuthoritative: true }),
    /refuses an authoritative scene model/,
  );
  assert.throws(
    () => assertLivingSceneRendererModelNonAuthoritative({}),
    /refuses an authoritative scene model/,
  );
});

test("renderer selection exposes only viewable fields", () => {
  const selection = createLivingSceneSelection("employee", "mobility_operations_lead", "Mobility Operations Lead");
  assert.deepEqual(Object.keys(selection).sort(), ["entityKey", "entityType", "label"]);
  assert.equal(Object.isFrozen(selection), true);
  assert.equal(isLivingSceneSelection(selection), true);
  assert.equal(
    isLivingSceneSelection({ ...selection, authority_level: "L5" }),
    false,
  );
  assert.equal(
    isLivingSceneSelection({ ...selection, work_item_id: "hidden-work" }),
    false,
  );
});


test("renderer canvas lease permits mount-dispose-remount on the same canvas identity", () => {
  const canvas = {};
  const first = acquireLivingSceneRendererCanvasLease(canvas);
  assert.throws(
    () => acquireLivingSceneRendererCanvasLease(canvas),
    /duplicate live mount on the same canvas/,
  );
  first.release();
  assert.doesNotThrow(() => {
    const second = acquireLivingSceneRendererCanvasLease(canvas);
    second.release();
  });
  first.release();
});
