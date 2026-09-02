import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("Cockpit uses one global state vocabulary and adaptive evidence-first refinements", async () => {
  const [topbar, refinements, visualPolish, layout, sidebar] = await Promise.all([
    read("components/Topbar.tsx"),
    read("app/cockpit/cockpit-refinements.css"),
    read("app/cockpit/cockpit-visual-polish.css"),
    read("app/cockpit/layout.tsx"),
    read("components/Sidebar.tsx"),
  ]);

  assert.match(topbar, /ready: "READY"/);
  assert.match(topbar, /partial: "PARTIAL"/);
  assert.match(topbar, /offline: "DEGRADED"/);
  assert.match(topbar, /loading: "CONNECTING"/);
  assert.match(topbar, /aria-label=\{`\$\{stateLabel\}\. \$\{stateDescription\}`\}/);

  assert.match(layout, /cockpit-refinements\.css/);
  assert.match(layout, /cockpit-visual-polish\.css/);
  assert.match(refinements, /Organization foundation exists; no active operational positions are currently instantiated\./);
  assert.match(refinements, /No professionally reviewed jurisdiction signal yet\./);
  assert.match(refinements, /\.owner-attention:has\(\.owner-attention-state\.needs-attention\)/);
  assert.match(refinements, /\.live-organization:has\(\.activity-empty-state\)/);
  assert.match(refinements, /\.cockpit-control-dock > a/);
  assert.doesNotMatch(refinements, /content:\s*"[1-9][0-9]*"/);

  assert.match(visualPolish, /\.pulse-executive-card > div > strong[\s\S]*font-size:\s*11px/);
  assert.match(visualPolish, /\.pulse-domain-card strong[\s\S]*font-size:\s*10\.5px/);
  assert.match(visualPolish, /section\[aria-labelledby="live-cycle-empty-title"\]/);
  assert.doesNotMatch(visualPolish, /content:\s*"[1-9][0-9]*"/);

  assert.match(sidebar, /role="tooltip"/);
  assert.match(sidebar, /onMouseEnter=\{\(event\) => showRailTooltip/);
  assert.match(sidebar, /onFocus=\{\(event\) => showRailTooltip/);
});


test("Decision Explorer M.2 follows canonical work, reference, activity and supersession reads only", async () => {
  const decisionExplorer = await read("app/cockpit/decisions/page.tsx");
  const api = await read("lib/api.ts");

  assert.match(decisionExplorer, /M\.2 Decision → Work → Evidence/);
  assert.match(decisionExplorer, /getOrganizationWorkItem/);
  assert.match(decisionExplorer, /listOrganizationRecordReferences/);
  assert.match(decisionExplorer, /listOrganizationActivities/);
  assert.match(decisionExplorer, /objective_key/);
  assert.match(decisionExplorer, /phase_key/);
  assert.match(decisionExplorer, /superseded_by_decision_id/);
  assert.match(decisionExplorer, /Missing relationships remain unknown rather than being inferred/);
  assert.match(decisionExplorer, /does not create work, evidence, activities, decisions, or supersession/);
  assert.doesNotMatch(decisionExplorer, /createOrganizationWork/);
  assert.doesNotMatch(decisionExplorer, /decideBoardItem/);

  assert.match(api, /work_item_id\?: string/);
  assert.match(api, /decision_id\?: string/);
  assert.match(api, /reference_role\?: string/);
  assert.match(api, /\/api\/v1\/organization\/record-references/);
});
