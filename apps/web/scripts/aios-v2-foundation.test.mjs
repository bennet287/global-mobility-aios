import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const tokens = await readFile(new URL("../styles/v2/tokens.css", import.meta.url), "utf8");
const motion = await readFile(new URL("../styles/v2/motion.css", import.meta.url), "utf8");
const foundation = await readFile(new URL("../styles/v2/foundation.css", import.meta.url), "utf8");
const premiumShell = await readFile(new URL("../styles/v2/premium-shell.css", import.meta.url), "utf8");
const premiumOwnerHome = await readFile(new URL("../styles/v2/premium-owner-home.css", import.meta.url), "utf8");
const premiumHq = await readFile(new URL("../styles/v2/premium-hq.css", import.meta.url), "utf8");
const premiumCharacters = await readFile(new URL("../styles/v2/premium-characters.css", import.meta.url), "utf8");
const shell = await readFile(new URL("../components/v2/V2Shell.tsx", import.meta.url), "utf8");
const characterMiniature = await readFile(new URL("../components/v2/V2CharacterMiniature.tsx", import.meta.url), "utf8");
const navigation = await readFile(new URL("../lib/v2/navigation.ts", import.meta.url), "utf8");
const ownerHome = await readFile(new URL("../components/v2/V2OwnerHomePrototype.tsx", import.meta.url), "utf8");
const situationRoom = await readFile(new URL("../components/v2/V2OwnerSituationRoom.tsx", import.meta.url), "utf8");
const page = await readFile(new URL("../app/cockpit/v2/page.tsx", import.meta.url), "utf8");
const layout = await readFile(new URL("../app/cockpit/v2/layout.tsx", import.meta.url), "utf8");

test("AIOS V2 tokens are namespaced and do not replace the legacy root theme", () => {
  assert.match(tokens, /\.aios-v2-root\s*\{/);
  assert.match(tokens, /--aios-v2-color-canvas:/);
  assert.match(tokens, /--aios-v2-color-accent:/);
  assert.doesNotMatch(tokens, /(^|\n):root\s*\{/);
});

test("AIOS V2 Owner navigation exposes the selected seven-domain mental model", () => {
  for (const label of ["Home", "Organization", "Missions", "Intelligence", "Evidence", "Decisions", "History"]) {
    assert.match(navigation, new RegExp('label: "' + label + '"'));
  }

  for (const legacyPrimary of ["External Validation", "Agent Review Queue", "Automation Hub", "Cross-department friction"]) {
    assert.doesNotMatch(navigation, new RegExp(legacyPrimary));
  }

  assert.match(shell, /ownerNavigation\.map/);
});

test("implemented V2 domains link explicitly while the shell retains fail-closed rendering support", () => {
  for (const href of [
    "/cockpit/v2",
    "/cockpit/v2/organization",
    "/cockpit/v2/missions",
    "/cockpit/v2/intelligence",
    "/cockpit/v2/evidence",
    "/cockpit/v2/decisions",
    "/cockpit/v2/history",
  ]) {
    assert.match(navigation, new RegExp(`href: "${href.replaceAll("/", "\\/")}", enabled: true`));
  }
  assert.doesNotMatch(navigation, /href: null, enabled: false/);
  assert.match(shell, /aria-disabled="true"/);
});

test("V2 Owner Home uses governed sources and keeps truth caveats visible", () => {
  assert.match(ownerHome, /useV2OwnerOrganization/);
  assert.match(ownerHome, /V2OwnerSituationRoom/);
  assert.match(ownerHome, /useV2SearchItems/);
  assert.match(situationRoom, /V2AttentionList/);
  assert.match(situationRoom, /V2OrganizationBlockout/);
  assert.match(situationRoom, /roster counts rather than presence claims/);
  assert.doesNotMatch(`${ownerHome}\n${situationRoom}`, /canonical_projection\s*=|authoritative\s*=|mutations_allowed\s*=/);
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

test("major redesign premium shell stays scoped, responsive and reduced-motion safe", () => {
  assert.match(layout, /premium-shell\.css/);
  assert.match(premiumShell, /\.aios-v2-root\s*\{/);
  assert.match(premiumShell, /\.aios-v2-rail\s*\{/);
  assert.match(premiumShell, /\.aios-v2-topline\s*\{/);
  assert.match(premiumShell, /\.aios-v2-nav-item\.active/);
  assert.match(premiumShell, /@media \(max-width: 980px\)/);
  assert.match(premiumShell, /@media \(max-width: 760px\)/);
  assert.match(premiumShell, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(premiumShell, /(^|\n):root\s*\{/);
  assert.doesNotMatch(premiumShell, /presenceClaimed|locomotionAllowed|canonical_projection|mutations_allowed/);
});

test("major redesign Owner Home composition is isolated and truth-neutral", () => {
  assert.match(layout, /premium-owner-home\.css/);
  assert.match(premiumOwnerHome, /:has\(#aios-v2-owner-home-title\)/);
  assert.match(premiumOwnerHome, /@media \(max-width: 760px\)/);
  assert.match(premiumOwnerHome, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(premiumOwnerHome, /(^|\n):root\s*\{/);
  assert.doesNotMatch(premiumOwnerHome, /presenceClaimed|locomotionAllowed|canonical_projection|mutations_allowed|authority\s*=/);
});

test("major redesign Living HQ remains presentation-only, responsive and reduced-motion safe", () => {
  assert.match(layout, /premium-hq\.css/);
  assert.match(premiumHq, /\.aios-v2-root \.aios-v2-hq-blockout/);
  assert.match(premiumHq, /\.zone-executive/);
  assert.match(premiumHq, /\.zone-regulatory/);
  assert.match(premiumHq, /\.zone-atrium/);
  assert.match(premiumHq, /\.zone-technology/);
  assert.match(premiumHq, /\.zone-operations/);
  assert.match(premiumHq, /@media \(max-width: 760px\)/);
  assert.match(premiumHq, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(premiumHq, /(^|\n):root\s*\{/);
  assert.doesNotMatch(premiumHq, /presenceClaimed|locomotionAllowed|canonical_projection|mutations_allowed|physicalLocationClaimed/);
});

test("premium character presentation uses governed presentation keys and preserves truth boundaries", () => {
  assert.match(layout, /premium-characters\.css/);
  assert.match(characterMiniature, /resolveV2CharacterPresentation/);
  assert.match(characterMiniature, /resolveCharacterArtPrototype\(\{ presentationKey: model\.presentationKey \}\)/);
  assert.match(characterMiniature, /V2CharacterArtPrototype/);
  assert.match(characterMiniature, /presentationKey=\{model\.presentationKey\}/);
  assert.match(characterMiniature, /data-presentation-only="true"/);
  assert.match(characterMiniature, /data-presence-claimed="false"/);
  assert.match(characterMiniature, /data-canonical-state-writable="false"/);
  assert.match(characterMiniature, /data-semantic-animation-active="false"/);
  assert.doesNotMatch(characterMiniature, /resolveCharacterArtPrototype\(\{[^}]*title|resolveCharacterArtPrototype\(\{[^}]*department/);
  assert.match(premiumCharacters, /\.aios-v2-root \.aios-v2-character-stage-art/);
  assert.match(premiumCharacters, /data-art-archetype="ceo"/);
  assert.match(premiumCharacters, /data-art-archetype="cto"/);
  assert.match(premiumCharacters, /data-art-archetype="regulatory-compliance"/);
  assert.match(premiumCharacters, /data-art-archetype="operations"/);
  assert.match(premiumCharacters, /data-art-archetype="neutral-professional"/);
  assert.match(premiumCharacters, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(premiumCharacters, /(^|\n):root\s*\{|canonical_projection|mutations_allowed|physicalPresenceClaimed|physicalLocationClaimed/);
});

test("the isolated V2 owner-home route mounts the V2 prototype instead of replacing the existing cockpit", () => {
  assert.match(page, /V2OwnerHomePrototype/);
  assert.match(page, /AiosV2OwnerHomePrototypePage/);
});
