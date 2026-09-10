import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  filterNavigationCommands,
  navigationCommands,
  ownerNavigation,
} from "../lib/v2/navigation.ts";
import {
  operatorContextualDestinations,
  operatorNavigation,
} from "../lib/v2/operator-navigation.ts";
import { mobilityNavigation } from "../lib/v2/mobility-navigation.ts";

const shellUrl = new URL("../components/v2/V2Shell.tsx", import.meta.url);
const operatorShellUrl = new URL("../components/v2/V2OperatorShell.tsx", import.meta.url);
const operatorPageUrl = new URL("../app/operator/v2/page.tsx", import.meta.url);
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

test("Operator navigation locks the six-domain professional mental model", async () => {
  assert.equal(operatorNavigation.length, 6);
  assert.deepEqual(operatorNavigation.map((item) => item.label), [
    "Work",
    "Profiles",
    "Pathways",
    "Evidence",
    "Communication",
    "Tools",
  ]);

  for (const item of operatorNavigation) {
    if (item.enabled) {
      assert.ok(item.href, `${item.label} must provide an href when enabled`);
      await assertRouteExists(item.href);
    } else {
      assert.equal(item.href, null, `${item.label} must fail closed until its conceptual home is implemented`);
    }
  }
});

test("Mobility navigation locks the five-domain case-first model and fails closed for unmigrated client surfaces", async () => {
  assert.equal(mobilityNavigation.length, 5);
  assert.deepEqual(mobilityNavigation.map((item) => item.label), [
    "Overview",
    "My Case",
    "Documents",
    "Timeline",
    "Messages",
  ]);

  for (const item of mobilityNavigation) {
    if (item.enabled) {
      assert.ok(item.href, `${item.label} must provide an href when enabled`);
      await assertRouteExists(item.href);
    } else {
      assert.equal(item.href, null, `${item.label} must fail closed until a client-safe destination is accepted`);
    }
  }

  assert.equal(mobilityNavigation.find((item) => item.label === "Overview")?.href, "/my-mobility");
  assert.equal(mobilityNavigation.find((item) => item.label === "My Case")?.href, "/portal");
  assert.equal(mobilityNavigation.find((item) => item.label === "Documents")?.href, "/portal/documents");
  assert.equal(mobilityNavigation.find((item) => item.label === "Timeline")?.href, "/portal/timeline");
  assert.equal(mobilityNavigation.find((item) => item.label === "Messages")?.href, "/portal/messages");
});

test("Operator specialist routes stay contextual and map to one primary conceptual home", async () => {
  const homes = new Set(operatorNavigation.map((item) => item.label));
  const hrefs = operatorContextualDestinations.map((item) => item.href);
  assert.equal(new Set(hrefs).size, hrefs.length);

  for (const item of operatorContextualDestinations) {
    assert.ok(homes.has(item.conceptualHome), `${item.label} must map to a valid Operator conceptual home`);
    await assertRouteExists(item.href);
  }
});

test("visible Operator V2 shell is isolated, six-domain, and navigation-only", async () => {
  await assertRouteExists("/operator/v2");
  const shell = await readFile(operatorShellUrl, "utf8");
  const page = await readFile(operatorPageUrl, "utf8");

  assert.match(shell, /operatorNavigation\.map/);
  assert.match(shell, /Professional \/ Operator navigation/);
  assert.match(shell, /V2ThemeControl/);
  assert.match(page, /<V2OperatorShell activeItem="Work">/);
  assert.match(page, /Work, Profiles, Pathways, Evidence, Communication and Tools/);
  assert.match(page, /Migration pending/);
  assert.match(page, /authority boundaries, review gates and mutation semantics remain unchanged/);
  assert.doesNotMatch(`${shell}\n${page}`, /fetch\(|axios|method:\s*["'](?:POST|PUT|PATCH|DELETE)|onSubmit=/i);
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
  assert.deepEqual(filterNavigationCommands("decisions").map((item) => item.label), ["Decisions", "Decision Explorer"]);
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
  assert.match(icon, /work:/);
  assert.match(icon, /profiles:/);
  assert.match(icon, /pathways:/);
  assert.match(icon, /communication:/);
  assert.match(icon, /tools:/);
  assert.match(icon, /viewBox="0 0 24 24"/);
  assert.match(icon, /stroke="currentColor"/);
});
