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

test("Track B surface states make truth gaps reusable without manufacturing activity", async () => {
  const [surfaceState, liveOrganization, styles] = await Promise.all([
    read("components/SurfaceState.tsx"),
    read("app/cockpit/live-organization/page.tsx"),
    read("app/track-b-foundation.css"),
  ]);

  for (const kind of ["empty", "error", "blocked", "not-connected"]) {
    assert.ok(surfaceState.includes(`"${kind}"`), `missing surface-state kind ${kind}`);
  }

  assert.match(surfaceState, /data-surface-state=\{kind\}/);
  assert.match(surfaceState, /role=\{announce \? \(kind === "error" \? "alert" : "status"\) : undefined\}/);
  assert.match(surfaceState, /aria-live=\{announce \? \(kind === "error" \? "assertive" : "polite"\) : undefined\}/);
  assert.match(liveOrganization, /import \{ SurfaceState \} from "\.\.\/\.\.\/\.\.\/components\/SurfaceState"/);
  assert.match(liveOrganization, /kind="error"[\s\S]*announce/);
  assert.match(liveOrganization, /kind="empty"[\s\S]*No persisted Austria cycle/);
  assert.match(liveOrganization, /kind="not-connected"[\s\S]*Domain Evidence is not connected/);
  assert.match(liveOrganization, /kind="not-connected"[\s\S]*VerifiedRules are not connected/);
  assert.doesNotMatch(liveOrganization, /Math\.random|setInterval\(/);
  assert.match(styles, /\.ui-surface-state\.error/);
  assert.match(styles, /\.ui-surface-state\.blocked/);
  assert.match(styles, /\.ui-surface-state\.not-connected/);
});

test("UX0 removes duplicate owner navigation while preserving experience switching", async () => {
  const navigation = await read("lib/workspace-navigation.ts");

  assert.match(navigation, /shortLabel: "Cockpit"/);
  assert.match(navigation, /shortLabel: "Operations"/);
  assert.match(navigation, /label: "Cross-department friction", href: "\/cross-department-friction"/);
  assert.doesNotMatch(navigation, /label: "Open from Cockpit"/);

  const ownerBlock = navigation.slice(navigation.indexOf("owner: ["), navigation.indexOf("operator: ["));
  assert.doesNotMatch(ownerBlock, /label: "Department workspaces"/);
  assert.doesNotMatch(ownerBlock, /label: "Operations Workspace"/);
  assert.match(ownerBlock, /label: "Organization"/);
  assert.match(ownerBlock, /label: "Agent Console"/);
});
