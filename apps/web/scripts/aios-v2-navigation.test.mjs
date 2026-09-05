import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  filterNavigationCommands,
  navigationCommands,
  ownerNavigation,
} from "../lib/v2/navigation.ts";

const shellUrl = new URL("../components/v2/V2Shell.tsx", import.meta.url);
const iconUrl = new URL("../components/v2/V2Icon.tsx", import.meta.url);

async function assertRouteExists(href) {
  await access(new URL(`../app${href}/page.tsx`, import.meta.url));
}

test("Owner navigation keeps the seven-domain mental model without linking unfinished V2 workspaces", async () => {
  assert.equal(ownerNavigation.length, 7);
  assert.deepEqual(ownerNavigation.map((item) => item.label), [
    "Home",
    "Organization",
    "Missions",
    "Intelligence",
    "Evidence",
    "Decisions",
    "History",
  ]);

  for (const item of ownerNavigation) {
    if (item.enabled) {
      assert.ok(item.href, `${item.label} must provide an href when enabled`);
      await assertRouteExists(item.href);
    } else {
      assert.equal(item.href, null, `${item.label} must fail closed until its route is accepted`);
    }
  }
});

test("navigation commands contain only implemented destinations and never imply workflow authority", async () => {
  assert.equal(new Set(navigationCommands.map((item) => item.href)).size, navigationCommands.length);
  for (const command of navigationCommands) {
    assert.ok(command.href.startsWith("/cockpit"));
    await assertRouteExists(command.href);
    assert.equal(/approve|reject|submit|write|mutate/i.test(`${command.label} ${command.description}`), false);
  }
});

test("workspace search matches normalized words across label and description", () => {
  assert.deepEqual(filterNavigationCommands("   "), navigationCommands);
  assert.deepEqual(filterNavigationCommands("  ORGANIZATION   living ").map((item) => item.label), ["Organization"]);
  assert.deepEqual(filterNavigationCommands("decisions").map((item) => item.label), ["Decision Explorer"]);
  assert.deepEqual(filterNavigationCommands("no-such-workspace"), []);
  assert.deepEqual(filterNavigationCommands("approve"), []);
});

test("V2 shell uses the shared SVG icon system instead of single-letter navigation glyphs", async () => {
  const shell = await readFile(shellUrl, "utf8");
  const icon = await readFile(iconUrl, "utf8");
  assert.match(shell, /import \{ V2Icon \}/);
  assert.match(shell, /<V2Icon name=\{item\.icon\}/);
  assert.match(shell, /<V2Icon name="search"/);
  assert.doesNotMatch(shell, /glyph:\s*"[HOMIEDT]"/);
  assert.match(icon, /viewBox="0 0 24 24"/);
  assert.match(icon, /stroke="currentColor"/);
});
