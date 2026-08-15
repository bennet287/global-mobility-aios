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


test("role-based shells expose Cockpit, Operations, and My Mobility without replacing backend authorization", async () => {
  const [sidebar, navigation, cockpit, myMobility] = await Promise.all([read("components/Sidebar.tsx"),read("lib/workspace-navigation.ts"),read("app/cockpit/page.tsx"),read("app/my-mobility/page.tsx")]);
  for (const label of ["Cockpit", "Professional / Operator", "Mobility User", "My Mobility"]) assert.ok(navigation.includes(label), `missing role-shell label ${label}`);
  assert.match(navigation, /href: "\/cockpit"/);
  assert.match(navigation, /href: "\/my-mobility"/);
  assert.doesNotMatch(sidebar, /Navigation context only\. Server authorization remains authoritative\./);
  assert.match(cockpit, /Server authorization remains authoritative/);
  assert.match(sidebar, /WORKSPACE_EXPERIENCE_STORAGE_KEY/);
  assert.match(cockpit, /Global Mobility AIOS · Owner \/ Board/);
  assert.match(cockpit, /One governed view of human authority, organizational execution/);
  assert.doesNotMatch(cockpit, /13\.16\.2|13\.16\.3|Cockpit ≠ Board Room/);
  assert.match(cockpit, /href="\/board-room"/);
  assert.match(myMobility, /href="\/portal"/);
  assert.match(myMobility, /Current stage/);
  assert.match(myMobility, /Evidence requests/);
  assert.doesNotMatch(myMobility, /long-term navigation model|user-facing shell/);
  assert.doesNotMatch(myMobility, /href="\/agents\//);
  assert.doesNotMatch(myMobility, /href="\/board-room"/);
});

test("workspace rail uses the premium compact control-rail pattern", async () => {
  const [sidebar, styles] = await Promise.all([read("components/Sidebar.tsx"), read("app/globals.css")]);
  assert.match(sidebar, /rail-brand-copy/);
  assert.match(sidebar, /Global Mobility AIOS/);
  assert.match(sidebar, /rail-experience-icon/);
  assert.match(sidebar, /ExperienceIcon/);
  assert.doesNotMatch(sidebar, /experienceGlyph/);
  assert.match(sidebar, /className="rail-group-label"/);
  assert.match(sidebar, /className="rail-icon"/);
  assert.doesNotMatch(sidebar, /rail-authority-note/);
  assert.match(styles, /grid-template-columns: 88px minmax\(0, 1fr\)/);
  assert.match(styles, /Keep the control rail calm and spatially stable/);
  assert.match(styles, /\.workspace-rail:hover,[\s\S]*width: 88px/);
  assert.match(sidebar, /data-label=\{`\$\{item\.shortLabel\} · \$\{item\.label\}`\}/);
  assert.match(styles, /\.rail-brand-mark[\s\S]*width: 40px;[\s\S]*height: 40px;/);
  assert.match(styles, /\.rail-navigation[\s\S]*overflow-y: auto/);
  assert.match(sidebar, /showRailTooltip/);
  assert.match(sidebar, /className="rail-hover-label"/);
  assert.match(sidebar, /onMouseEnter=\{\(event\) => showRailTooltip/);
  assert.match(sidebar, /onFocus=\{\(event\) => showRailTooltip/);
  assert.match(styles, /\.rail-hover-label \{[\s\S]*position: fixed;[\s\S]*pointer-events: none/);
  assert.match(styles, /The rail remains spatially stable; labels float outside it instead of expanding over the Cockpit/);
});


test("premium role-shell direction stays product-facing and data-grounded", async () => {
  const [cockpit, myMobility, home, api, styles] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("app/my-mobility/page.tsx"),
    read("app/page.tsx"),
    read("lib/api.ts"),
    read("app/globals.css"),
  ]);
  assert.match(cockpit, /Operating within delegated authority/);
  assert.match(cockpit, /Organization pulse/);
  assert.match(cockpit, /Governed runtime fabric/);
  assert.match(cockpit, /pulse-layer-connector/);
  assert.match(cockpit, /Requires your authority/);
  assert.match(cockpit, /owner-authority-orbit/);
  assert.match(cockpit, /Global mobility pulse/);
  assert.match(cockpit, /global-coverage-map/);
  assert.match(cockpit, /JURISDICTION_CENTROIDS/);
  assert.match(cockpit, /world-region-labels/);
  assert.doesNotMatch(cockpit, /className="world-land"/);
  assert.match(cockpit, /cockpit-control-dock/);
  assert.match(cockpit, /Durable Activity stream/);
  assert.match(cockpit, /Durable Activity is ready/);
  assert.match(cockpit, /getOrganizationObservatorySummary/);
  assert.match(cockpit, /listOrganizationActivities/);
  assert.match(cockpit, /getGlobalIntelligenceDashboard/);
  assert.doesNotMatch(cockpit, /97%|hard-coded|delivered in 13|establishes the shell/);
  assert.match(api, /\/api\/v1\/organization\/observatory\/summary/);
  assert.match(api, /\/api\/v1\/organization\/activities/);
  assert.match(myMobility, /Know where your case stands/);
  assert.match(myMobility, /Protected case access/);
  assert.doesNotMatch(myMobility, /Secure workspace<\/small>/);
  assert.match(home, /Case summary temporarily unavailable/);
  assert.match(styles, /--font-editorial/);
  assert.match(styles, /\.cockpit-command-copy h2[\s\S]*font-family: var\(--font-editorial\)/);
  assert.match(styles, /@keyframes cockpit-live-pulse/);
  assert.match(styles, /@keyframes pulse-flow/);
  assert.match(styles, /\.global-coverage-map/);
  assert.match(styles, /\.world-region-labels text/);
  assert.match(styles, /\.cockpit-control-links\.cockpit-control-dock/);
  assert.match(cockpit, /EXECUTIVE_ROLE_LABELS/);
  assert.match(cockpit, /cto: "CTO"/);
  assert.match(cockpit, /ciso: "CISO"/);
  assert.match(cockpit, /position\.reports_to_position_key === "ceo" && position\.authority_level === "L3"/);
  assert.match(cockpit, /pulse-executive-layer/);
  assert.match(cockpit, /pulse-executive-grid/);
  assert.match(cockpit, /pulse-operational-layer/);
  assert.match(cockpit, /pulse-domain-grid/);
  assert.match(cockpit, /executivePortfolios/);
  assert.match(cockpit, /operationalDomains/);
  assert.doesNotMatch(cockpit, /PULSE_ROW_X|pulseTopDepartments|pulseBottomDepartments|data-slot=/);
  assert.match(styles, /\.pulse-executive-grid/);
  assert.match(styles, /\.pulse-domain-grid/);
  assert.match(styles, /\.organization-pulse-map\.enterprise-authority-map/);
  assert.match(cockpit, /activity-coverage-viz/);
  assert.match(cockpit, /Earlier history/);
  assert.match(cockpit, /Coverage boundary/);
  assert.match(styles, /\.activity-coverage-boundary/);
  assert.match(styles, /\.activity-now-point/);
  assert.match(styles, /\.authority-ring/);
  assert.match(styles, /prefers-reduced-motion: reduce/);
});

test("Cockpit dark mode preserves visible information-surface hierarchy", async () => {
  const styles = await read("app/globals.css");
  assert.match(styles, /dark-mode hierarchy correction: preserve premium depth without hiding information surfaces/);
  assert.match(styles, /\[data-theme="dark"\] \.cockpit-surface \{[\s\S]*rgba\(31, 36, 48/);
  assert.match(styles, /\[data-theme="dark"\] \.pulse-executive-layer \{/);
  assert.match(styles, /\[data-theme="dark"\] \.pulse-executive-card \{/);
  assert.match(styles, /\[data-theme="dark"\] \.owner-attention-state \{/);
  assert.match(styles, /\[data-theme="dark"\] \.live-organization \.activity-empty-state \{/);
  assert.match(styles, /Keep the page canvas darker than its information surfaces so panel boundaries remain obvious/);
  assert.match(styles, /Important executive titles must remain readable/);
});
