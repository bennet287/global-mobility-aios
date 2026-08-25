import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("Cockpit uses one global state vocabulary and adaptive evidence-first refinements", async () => {
  const [topbar, operationalStatus, refinements, visualPolish, layout, sidebar] = await Promise.all([
    read("components/Topbar.tsx"),
    read("components/OperationalStatus.tsx"),
    read("app/cockpit/cockpit-refinements.css"),
    read("app/cockpit/cockpit-visual-polish.css"),
    read("app/cockpit/layout.tsx"),
    read("components/Sidebar.tsx"),
  ]);

  assert.match(topbar, /<OperationalStatus status=\{loadStatus\} \/>/);
  assert.match(operationalStatus, /label: "READY"/);
  assert.match(operationalStatus, /label: "PARTIAL"/);
  assert.match(operationalStatus, /label: "DEGRADED"/);
  assert.match(operationalStatus, /loading:\s*\{[\s\S]*label: "CONNECTING"/);
  assert.match(operationalStatus, /aria-label=\{`\$\{metadata\.label\}\. \$\{metadata\.description\}`\}/);

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
