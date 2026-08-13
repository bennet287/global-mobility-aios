import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("shared typography and semantic tokens are present", async () => {
  const [layout, styles] = await Promise.all([read("app/layout.tsx"), read("app/globals.css")]);
  assert.match(layout, /Geist, Geist_Mono/);
  assert.match(layout, /--font-geist-sans/);
  for (const token of [
    "--type-page-title",
    "--type-section-title",
    "--type-card-title",
    "--type-body",
    "--type-label",
    "--type-caption",
    "--type-status",
    "--type-technical",
    "--content-readable",
    "--content-operator",
    "--state-warning-bg",
    "--state-danger-bg",
  ]) {
    assert.ok(styles.includes(token), `missing design token ${token}`);
  }
  assert.match(styles, /prefers-reduced-motion: reduce/);
});

test("workspace shell exposes keyboard and landmark foundations", async () => {
  const shell = await read("components/WorkspaceShell.tsx");
  assert.match(shell, /className="skip-link"/);
  assert.match(shell, /id="main-content"/);
  assert.match(shell, /aria-expanded=\{open\}/);
  assert.match(shell, /aria-controls="workspace-navigation"/);
  assert.match(shell, /event\.key === "Escape"/);

  for (const route of [
    "app/automation/page.tsx",
    "app/corporate-mobility/page.tsx",
    "app/document-intelligence/page.tsx",
    "app/planning/page.tsx",
    "app/timelines/page.tsx",
    "app/timelines/ScenarioWorkspace.tsx",
  ]) {
    assert.doesNotMatch(await read(route), /<main\b/, `${route} must not nest a main landmark inside WorkspaceShell`);
  }
});

test("technical provenance uses a native accessible disclosure", async () => {
  const disclosure = await read("components/TechnicalDisclosure.tsx");
  assert.match(disclosure, /<details/);
  assert.match(disclosure, /<summary/);
  assert.match(disclosure, /aria-controls=\{contentId\}/);
});

test("Round 6 presentation findings are represented without decision changes", async () => {
  const [eligibility, planning] = await Promise.all([
    read("app/eligibility/page.tsx"),
    read("app/planning/page.tsx"),
  ]);
  assert.doesNotMatch(eligibility, /label="Overall score"/);
  assert.match(eligibility, /not the probability of visa or permit approval/);
  assert.match(eligibility, /What prevents this pathway from proceeding/);
  assert.match(planning, /Internal simulation is active/);
  assert.match(planning, /Excluded routes/);
  assert.match(planning, /not plausible alternatives/);
  assert.match(planning, /TechnicalDisclosure/);
});

test("Eligibility orders action before additional gaps and translates raw states", async () => {
  const eligibility = await read("app/eligibility/page.tsx");
  const blockerIndex = eligibility.indexOf("What prevents this pathway from proceeding");
  const actionIndex = eligibility.indexOf("Move the case forward");
  const supportingGapIndex = eligibility.indexOf("Additional gaps and review needs");
  assert.ok(blockerIndex >= 0 && blockerIndex < actionIndex, "primary blocker must precede next actions");
  assert.ok(actionIndex < supportingGapIndex, "next actions must precede the supporting gap inventory");
  assert.match(eligibility, /Employer declaration has not been provided/);
  assert.match(eligibility, /National occupation evidence is awaiting independent certification/);
  assert.match(eligibility, /Raw assessment states/);
});

test("Board Room preserves conventional executive acronyms", async () => {
  const boardRoom = await read("app/board-room/page.tsx");
  for (const acronym of ["cco", "cfo", "clo", "cmo", "coo", "chro", "cpo", "ciso", "cto"]) {
    assert.ok(boardRoom.includes(`"${acronym}"`), `missing executive acronym ${acronym.toUpperCase()}`);
  }
  assert.match(boardRoom, /normalized\.toUpperCase\(\)/);
  assert.match(boardRoom, /executivePositionLabel\(position\.position_key\)/);
});

test("Agent lead rows expose stable structural columns", async () => {
  const [consolePage, styles] = await Promise.all([
    read("app/agents/console/page.tsx"),
    read("app/globals.css"),
  ]);
  for (const className of ["agent-lead-select", "agent-lead-avatar", "agent-lead-content", "agent-lead-status"]) {
    assert.ok(consolePage.includes(className), `missing lead-row structural class ${className}`);
  }
  assert.match(styles, /grid-template-columns: 1\.25rem 2\.5rem minmax\(0, 1fr\) auto/);
  assert.match(styles, /\.agent-lead-name[\s\S]*overflow-wrap: anywhere/);
});

test("Validation simulation checkbox remains associated with its label and helper", async () => {
  const [validation, styles] = await Promise.all([
    read("app/validation/page.tsx"),
    read("app/globals.css"),
  ]);
  assert.match(validation, /<label className="profile-check validation-simulation-control">/);
  assert.match(validation, /type="checkbox"[\s\S]*aria-describedby="validation-simulation-help"/);
  assert.match(validation, /id="validation-simulation-help"/);
  assert.match(styles, /\.validation-create-card input:not\(\[type="checkbox"\]\)/);
  assert.match(styles, /\.validation-simulation-control input\[type="checkbox"\]/);
});

test("Planning mobile summary and simulation control expose stable layout hooks", async () => {
  const [planning, metricPill, styles] = await Promise.all([
    read("app/planning/page.tsx"),
    read("components/MetricPill.tsx"),
    read("app/globals.css"),
  ]);
  for (const className of [
    "planning-simulation-control",
    "planning-metric-profile",
    "planning-metric-version",
    "planning-metric-alternatives",
    "planning-metric-gaps",
    "planning-metric-history",
    "planning-metric-status",
    "planning-metric-consent",
  ]) {
    assert.ok(planning.includes(className), `missing Planning layout hook ${className}`);
  }
  assert.match(metricPill, /className\?: string/);
  assert.match(styles, /\.planning-metric-profile,[\s\S]*\.planning-metric-consent[\s\S]*grid-column: 1 \/ -1/);
  assert.match(styles, /\.planning-simulation-control[\s\S]*grid-template-columns: 2\.5rem minmax\(0, 1fr\)/);
  assert.match(styles, /\.planning-metric-profile strong[\s\S]*word-break: normal/);
});

test("Planning derives the optional latest country ranking from ordered history", async () => {
  const planning = await read("app/planning/page.tsx");
  assert.doesNotMatch(planning, /getLatestCountryRanking/);
  assert.match(planning, /getCountryRankingHistory\(requestedLeadId\)/);
  assert.match(planning, /getCountryRankingHistory\(selectedLeadId\)/);
  assert.match(planning, /setCountryRanking\(rankingRows\.value\[0\] \|\| null\)/);
});

test("Mobile shell keeps the closed rail and run history outside content", async () => {
  const styles = await read("app/globals.css");
  assert.match(styles, /\.workspace-rail[\s\S]*visibility: hidden;[\s\S]*pointer-events: none/);
  assert.match(styles, /\.app-frame\.mobile-nav-open \.workspace-rail[\s\S]*visibility: visible/);
  assert.match(styles, /\.mobile-header[\s\S]*position: relative/);
  assert.match(styles, /\.agent-console-runs \{ min-width: 0; overflow: hidden; \}/);
  assert.match(styles, /\.agent-runs-row > span \{ min-width: 0; overflow-wrap: anywhere; \}/);
});

test("App Router icon has no conflicting public asset", async () => {
  const icon = await read("app/icon.svg");
  assert.match(icon, /<svg[^>]+viewBox="0 0 32 32"/);
  await assert.rejects(read("public/icon.svg"), (error) => error?.code === "ENOENT");
});
