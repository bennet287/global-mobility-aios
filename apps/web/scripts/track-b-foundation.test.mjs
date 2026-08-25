import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("Track B operational status owns the shared workspace-state contract", async () => {
  const [status, topbar] = await Promise.all([
    read("components/OperationalStatus.tsx"),
    read("components/Topbar.tsx"),
  ]);

  for (const state of ["idle", "loading", "ready", "partial", "offline"]) {
    assert.ok(status.includes(`${state}: {`), `missing operational status state ${state}`);
  }

  for (const label of ["CONNECTING", "READY", "PARTIAL", "DEGRADED"]) {
    assert.ok(status.includes(`label: "${label}"`), `missing operational status label ${label}`);
  }

  assert.match(status, /role="status"/);
  assert.match(status, /aria-live="polite"/);
  assert.match(status, /aria-label=\{`\$\{metadata\.label\}\. \$\{metadata\.description\}`\}/);
  assert.match(status, /data-operational-state=\{status\}/);
  assert.match(topbar, /OperationalStatus/);
  assert.match(topbar, /loadStatus: OperationalStatusKind/);
  assert.doesNotMatch(topbar, /WORKSPACE_STATE_LABELS|WORKSPACE_STATE_DESCRIPTIONS/);
});

test("Track B state styling remains compact on mobile and motion-safe", async () => {
  const [layout, styles] = await Promise.all([
    read("app/layout.tsx"),
    read("app/track-b-foundation.css"),
  ]);

  assert.match(layout, /import "\.\/track-b-foundation\.css"/);
  for (const state of ["loading", "ready", "partial", "offline"]) {
    assert.ok(styles.includes(`.ui-operational-status.${state}`), `missing style for ${state}`);
  }
  assert.match(styles, /@media \(max-width: 620px\)/);
  assert.match(styles, /\.ui-operational-status-label[\s\S]*display: none/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(styles, /animation: none/);
});
