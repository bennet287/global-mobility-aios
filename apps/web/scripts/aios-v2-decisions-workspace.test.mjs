import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  buildV2DecisionPortfolio,
  decisionDestination,
  filterV2Decisions,
  selectV2Decision,
} from "../lib/v2/decisions-workspace.ts";
import { navigationCommands, ownerNavigation } from "../lib/v2/navigation.ts";

const decision = (id, overrides = {}) => ({
  decision_id: id,
  decision_key: `key:${id}`,
  title: id === "decision:current" ? "Austria filing authority" : "Earlier filing authority",
  question: "Which recorded route should proceed?",
  recommendation: id === "decision:current" ? "Proceed to owner review" : "Earlier recommendation",
  status: id === "decision:current" ? "awaiting_owner" : "superseded",
  authority_level: id === "decision:current" ? "L3" : "L2",
  decision_owner_position: "ceo",
  work_item_id: "work:root",
  evidence_items: [{ ref: "evidence:a" }],
  record_fingerprint: `fp:${id}`,
  source_object_type: "WorkItem",
  source_object_id: "work:root",
  source_object_version: "1",
  supersedes_decision_id: id === "decision:current" ? "decision:old" : null,
  superseded_by_decision_id: id === "decision:old" ? "decision:current" : null,
  is_current: id === "decision:current",
  required_owner_action: id === "decision:current",
  decided_at: id === "decision:current" ? null : "2026-09-05T01:00:00Z",
  created_at: id === "decision:current" ? "2026-09-06T01:00:00Z" : "2026-09-05T01:00:00Z",
  superseded_by_created_at: id === "decision:old" ? "2026-09-06T01:00:00Z" : null,
  superseded_in_projection_week: id === "decision:old",
  ...overrides,
});

const latest = (decisions = [decision("decision:old"), decision("decision:current")]) => ({
  established: true,
  scene: {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-06T01:02:00Z",
    scope: "fixture",
    root_work_item_id: "work:root",
    objective_key: "fixture",
    coverage: {},
    deterministic: { decisions },
    predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
    environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
    truth: { canonical_authority: "Fixture canonical source", scene_authoritative: false, renderer_authoritative: false, prediction_authoritative: false, environmental_authoritative: false, scene_mutations_allowed: false },
  },
});

test("Q7 derives only literal Decision portfolio counts and supplied flags", () => {
  const portfolio = buildV2DecisionPortfolio(latest());
  assert.equal(portfolio.returnedDecisionCount, 2);
  assert.equal(portfolio.currentDecisionCount, 1);
  assert.equal(portfolio.ownerActionCount, 1);
  assert.equal(portfolio.supersessionLinkedCount, 2);
  assert.equal(portfolio.decisions[0].decisionId, "decision:current");
  assert.equal(portfolio.decisions[0].requiredOwnerAction, true);
  assert.equal(portfolio.decisions[0].evidenceItemCount, 1);
});

test("Q7 keeps unestablished distinct from an established empty Decision collection", () => {
  assert.equal(buildV2DecisionPortfolio({ established: false, scene: null }).established, false);
  const empty = buildV2DecisionPortfolio(latest([]));
  assert.equal(empty.established, true);
  assert.equal(empty.returnedDecisionCount, 0);
});

test("Q7 filtering and selection preserve exact statuses and opaque Decision IDs", () => {
  const records = buildV2DecisionPortfolio(latest()).decisions;
  assert.deepEqual(filterV2Decisions(records, "filing L3", "awaiting_owner", true).map((item) => item.decisionId), ["decision:current"]);
  assert.deepEqual(filterV2Decisions(records, "", "superseded", true), []);
  assert.equal(selectV2Decision(records, "decision:old")?.isCurrent, false);
  const opaque = "decision:AT /?ref=%23#alpha";
  assert.equal(new URL(decisionDestination(opaque), "http://test").searchParams.get("decision"), opaque);
});

test("Q7 Decisions remains enabled as Q8 adds the final History domain", () => {
  const decisions = ownerNavigation.find((item) => item.label === "Decisions");
  assert.equal(decisions?.enabled, true);
  assert.equal(decisions?.href, "/cockpit/v2/decisions");
  assert.equal(navigationCommands.filter((item) => item.href === "/cockpit/v2/decisions").length, 1);
  const history = ownerNavigation.find((item) => item.label === "History");
  assert.equal(history?.enabled, true);
  assert.equal(history?.href, "/cockpit/v2/history");
});

test("Q7 reads the existing Living Organization transparency scene and adds no mutation path", () => {
  const hook = readFileSync(new URL("../hooks/useV2DecisionsScene.ts", import.meta.url), "utf8");
  const component = readFileSync(new URL("../components/v2/V2DecisionsWorkspace.tsx", import.meta.url), "utf8");
  assert.match(hook, /getLatestAustriaLivingScene/);
  assert.match(component, /useV2SearchItems/);
  assert.match(component, /V2TruthBadge kind="recommendation"/);
  assert.match(component, /requiredOwnerAction/);
  assert.match(component, /supersedesDecisionId/);
  assert.doesNotMatch(component, /\b(POST|PUT|PATCH|DELETE)\b/);
  assert.doesNotMatch(component, /fetch\(/);
  assert.doesNotMatch(component, />\s*(Approve|Reject|Execute|Complete Decision)\s*</i);
  assert.match(component, /No approval, legal validity, completion, urgency or execution authority is inferred/);
});

test("Q7 source contract remains wired into the design-foundation gate", () => {
  const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8");
  assert.match(packageJson, /scripts\/aios-v2-decisions-workspace\.test\.mjs/);
});
