import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("Austria Live Organization Cockpit surface is persisted, bounded, and explicit about proof gaps", async () => {
  const [page, api, navigation] = await Promise.all([
    read("app/cockpit/live-organization/page.tsx"),
    read("lib/live-organization.ts"),
    read("lib/workspace-navigation.ts"),
  ]);

  assert.match(navigation, /label: "Live Organization", href: "\/cockpit\/live-organization"/);
  assert.match(navigation, /pathname\.startsWith\("\/cockpit"\)/);

  assert.match(page, /getLatestAustriaLiveOrganization/);
  assert.match(page, /synthesizeAustriaOwner/);
  assert.match(page, /snapshot\.ready_for_owner_synthesis/);
  assert.match(page, /snapshot\.external_action_authorized/);
  assert.match(page, /snapshot\.provider_model_authority/);
  assert.match(page, /snapshot\.domain_evidence_refs/);
  assert.match(page, /snapshot\.verified_rule_refs/);
  assert.match(page, /The Cockpit does not simulate a live organization cycle/);
  assert.match(page, /no Evidence is fabricated by the UI/);
  assert.match(page, /regulatory truth is not implied/);
  assert.doesNotMatch(page, /Math\.random|setInterval\(/);

  assert.match(api, /createApiFetch\(CLIENT_API_CONFIG\)/);
  assert.match(api, /\/api\/v1\/organization\/transparency\/live-organization\/austria\/latest/);
  assert.match(api, /\/api\/v1\/organization\/live-organization\/austria\/\$\{encodeURIComponent\(rootWorkItemId\)\}\/owner-synthesis/);
});
