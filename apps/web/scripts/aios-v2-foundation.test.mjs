import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const tokens = await readFile(new URL("../styles/v2/tokens.css", import.meta.url), "utf8");
const motion = await readFile(new URL("../styles/v2/motion.css", import.meta.url), "utf8");
const foundation = await readFile(new URL("../styles/v2/foundation.css", import.meta.url), "utf8");
const shell = await readFile(new URL("../components/v2/V2Shell.tsx", import.meta.url), "utf8");
const ownerHome = await readFile(new URL("../components/v2/V2OwnerHomePrototype.tsx", import.meta.url), "utf8");
const page = await readFile(new URL("../app/cockpit/v2/page.tsx", import.meta.url), "utf8");

test("AIOS V2 tokens are namespaced and do not replace the legacy root theme", () => {
  assert.match(tokens, /\.aios-v2-root\s*\{/);
  assert.match(tokens, /--aios-v2-color-canvas:/);
  assert.match(tokens, /--aios-v2-color-accent:/);
  assert.doesNotMatch(tokens, /(^|\n):root\s*\{/);
});

test("AIOS V2 Owner navigation exposes the selected seven-domain mental model", () => {
  for (const label of ["Home", "Organization", "Missions", "Intelligence", "Evidence", "Decisions", "History"]) {
    assert.match(shell, new RegExp('label: "' + label + '"'));
  }

  for (const legacyPrimary of ["External Validation", "Agent Review Queue", "Automation Hub", "Cross-department friction"]) {
    assert.doesNotMatch(shell, new RegExp(legacyPrimary));
  }
});

test("implemented V2 domains link explicitly while future destinations stay disabled", () => {
  assert.match(shell, /href: "\/cockpit\/v2"/);
  assert.match(shell, /href: "\/cockpit\/v2\/organization"/);
  assert.match(shell, /aria-disabled="true"/);
  assert.match(shell, /href: null, enabled: false/);
});

test("V2 Owner Home uses governed sources and keeps truth caveats visible", () => {
  assert.match(ownerHome, /useV2OwnerOrganization/);
  assert.match(ownerHome, /V2AttentionList/);
  assert.match(ownerHome, /V2OrganizationBlockout/);
  assert.match(ownerHome, /Employee counts are roster counts, not presence claims/);
  assert.doesNotMatch(ownerHome, /canonical_projection\s*=|authoritative\s*=|mutations_allowed\s*=/);
});

test("V2 motion foundation includes a reduced-motion mode", () => {
  assert.match(motion, /prefers-reduced-motion: reduce/);
  assert.match(motion, /--aios-v2-motion-spatial: 1ms/);
});

test("V2 responsive foundation establishes non-desktop layout behavior", () => {
  assert.match(foundation, /@media \(max-width: 980px\)/);
  assert.match(foundation, /@media \(max-width: 760px\)/);
  assert.match(foundation, /grid-template-columns: 1fr/);
});

test("the isolated V2 owner-home route mounts the V2 prototype instead of replacing the existing cockpit", () => {
  assert.match(page, /V2OwnerHomePrototype/);
  assert.match(page, /AiosV2OwnerHomePrototypePage/);
});
