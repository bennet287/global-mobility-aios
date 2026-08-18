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

test("13.16.3A Cockpit interaction stays data-grounded and authority-correct", async () => {
  const [cockpit, api, styles] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("lib/api.ts"),
    read("app/globals.css"),
  ]);

  assert.match(cockpit, /organizationFocus/);
  assert.match(cockpit, /organizationFocusView/);
  assert.match(cockpit, /aria-pressed=\{organizationFocus\.kind === "ceo"\}/);
  assert.match(cockpit, /kind: "executive"/);
  assert.match(cockpit, /kind: "domain"/);
  assert.match(cockpit, /Interactive organization focus/);
  assert.match(cockpit, /Active contributions/);
  assert.match(cockpit, /No recent durable signal in the loaded window/);
  assert.match(cockpit, /risk\.requires_board_attention/);
  assert.match(cockpit, /const ownerAttention = boardAttention \+ boardRiskAttention/);
  assert.match(cockpit, /Reserved authority queue/);
  assert.match(cockpit, /These records are not counted as Owner authority unless they are escalated/);
  assert.match(api, /\/api\/v1\/organization\/observatory\/departments/);
  assert.match(api, /\/api\/v1\/organization\/human-action-requests/);
  assert.match(styles, /Phase 13\.16\.3A — interactive Owner Control Center focus and authority queue/);
  assert.match(styles, /\.pulse-focus-panel/);
  assert.match(styles, /\.owner-authority-queue/);
  assert.match(styles, /\.pulse-executive-card\.selected/);
});


test("13.16.3A interaction polish keeps scope counts consistent and the Cockpit content-led", async () => {
  const [cockpit, styles] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("app/globals.css"),
  ]);

  assert.match(cockpit, /const downstreamPositions = organizationFocus\.kind === "domain"/);
  assert.match(cockpit, /downstream position/);
  assert.match(cockpit, /operational position/);
  assert.match(cockpit, /organizationFocusView\.scopeSummary/);
  assert.match(cockpit, /<small>Execution<\/small>/);
  assert.match(cockpit, /<small>Governance<\/small>/);
  assert.match(cockpit, /<small>Evidence<\/small>/);
  assert.match(cockpit, /<small>Human attention<\/small>/);
  assert.match(styles, /Phase 13\.16\.3A interaction polish: consistent span-of-control language and content-led Cockpit height/);
  assert.match(styles, /\.cockpit-primary-grid \{[\s\S]*align-items: start/);
  assert.match(styles, /\.owner-attention \{[\s\S]*align-self: start/);
  assert.match(styles, /\.organization-pulse-map\.enterprise-authority-map \{[\s\S]*min-height: 0/);
});


test("13.16.3B Owner operational intelligence remains data-grounded", async () => {
  const [cockpit, api, styles] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("lib/api.ts"),
    read("app/globals.css"),
  ]);

  assert.match(cockpit, /listOrganizationBlockers/);
  assert.match(cockpit, /listOrganizationWorkItemDependencies/);
  assert.match(cockpit, /listOrganizationWorkItems/);
  assert.match(cockpit, /OrganizationBlocker/);
  assert.match(cockpit, /OrganizationWorkItemDependency/);
  assert.match(cockpit, /Operational intelligence/);
  assert.match(cockpit, /cockpit-operational-intelligence/);
  assert.match(cockpit, /owner-blockers-lane/);
  assert.match(cockpit, /owner-dependencies-lane/);
  assert.match(cockpit, /owner-overdue-lane/);
  assert.match(cockpit, /owner-human-requests-lane/);
  assert.match(cockpit, /Open blockers/);
  assert.match(cockpit, /Active dependencies/);
  assert.match(cockpit, /Overdue active work/);
  assert.match(cockpit, /Pending human requests/);
  assert.match(cockpit, /No open blockers in the current view/);
  assert.match(cockpit, /No active dependencies in the current view/);
  assert.match(cockpit, /No overdue active work in the current view/);
  assert.match(cockpit, /No pending human requests in the current view/);
  assert.match(cockpit, /Evidence health/);
  assert.match(cockpit, /Updated [\s\S]*{shortDate/);
  assert.match(cockpit, /#overdue-work-title/);
  assert.match(cockpit, /#pending-human-requests-title/);
  assert.doesNotMatch(cockpit, /mitigate.*blocker|resolve.*blocker|waive.*dependency/);
  assert.doesNotMatch(cockpit, /97%|hard-coded|synthetic activity|fake blocker/);

  assert.match(api, /\/api\/v1\/organization\/blockers/);
  assert.match(api, /\/api\/v1\/organization\/work-item-dependencies/);
  assert.match(api, /\/api\/v1\/organization\/work-items\/records/);

  assert.match(styles, /Phase 13\.16\.3B/);
  assert.match(styles, /\.cockpit-operational-intelligence/);
  assert.match(styles, /\.operational-intelligence-grid/);
  assert.match(styles, /\.owner-blockers-lane/);
  assert.match(styles, /\.owner-dependencies-lane/);
  assert.match(styles, /\.owner-overdue-lane/);
  assert.match(styles, /\.owner-human-requests-lane/);
  assert.match(styles, /\.blocker-severity-critical/);
  assert.match(styles, /\.blocker-severity-high/);
  assert.match(styles, /\.blocker-severity-medium/);
  assert.match(styles, /\.blocker-severity-low/);
  assert.match(styles, /\.dependency-blocked/);
});

test("13.16.3C department drill-down and intervention stay governed", async () => {
  const [cockpit, api, styles] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("lib/api.ts"),
    read("app/globals.css"),
  ]);

  assert.match(cockpit, /Department drill-down/);
  assert.match(cockpit, /cockpit-department-drilldown/);
  assert.match(cockpit, /department-drilldown-grid/);
  assert.match(cockpit, /Governed intervention/);
  assert.match(cockpit, /Request human follow-up/);
  assert.match(cockpit, /createOrganizationHumanActionRequest/);
  assert.match(cockpit, /Backend authorization remains authoritative/);
  assert.match(cockpit, /does not directly change blocker or dependency status, complete work, or publish legal\/regulatory outcomes/);
  assert.doesNotMatch(cockpit, /mitigateOrganizationBlocker|resolveOrganizationBlocker|waiveOrganizationBlocker|waiveOrganizationWorkItemDependency|completeOrganizationWorkItem/);

  assert.match(api, /OrganizationHumanActionRequestCreateInput/);
  assert.match(api, /createOrganizationHumanActionRequest/);
  assert.match(api, /method: "POST"/);
  assert.match(api, /\/api\/v1\/organization\/human-action-requests/);

  assert.match(styles, /Phase 13\.16\.3C/);
  assert.match(styles, /\.cockpit-department-drilldown/);
  assert.match(styles, /\.governed-intervention-form/);
  assert.match(styles, /\.governed-intervention-trigger/);
});


test("13.16.4 Department workspaces route, navigation, and governed composition", async () => {
  const [cockpit, workspace, nav, styles, api] = await Promise.all([
    read("app/cockpit/page.tsx"),
    read("app/workspace/[department]/page.tsx"),
    read("lib/workspace-navigation.ts"),
    read("app/globals.css"),
    read("lib/api.ts"),
  ]);

  assert.ok(
    cockpit.includes('href={`/workspace/${encodeURIComponent(departmentDrilldown.domain.department)}`}'),
    "Cockpit drill-down must deep-link to the bounded department workspace",
  );
  assert.match(nav, /Department workspaces/);
  assert.match(nav, /pathname\.startsWith\("\/workspace\/"\)/);

  assert.match(workspace, /className="department-workspace"/);
  assert.match(workspace, /className="department-workspace-header"/);
  assert.match(workspace, /className="department-workspace-grid"/);
  assert.match(workspace, /className="department-workspace-card/);
  assert.match(workspace, /className="department-metrics"/);

  assert.match(workspace, /listOrganizationContributions\({ department, page_size: 100 }\)/);
  assert.match(workspace, /getOrganizationObservatoryDepartments\(\)/);
  assert.match(workspace, /Owned work/);
  assert.match(workspace, /Open blockers/);
  assert.match(workspace, /Active dependencies/);
  assert.match(workspace, /Pending human requests/);
  assert.match(workspace, /Contributions/);
  assert.match(workspace, /Material Activity/);
  assert.match(workspace, /Governed intervention/);
  assert.match(workspace, /Backend authorization remains authoritative/);
  assert.doesNotMatch(
    workspace,
    /resolveOrganizationBlocker|waiveOrganizationBlocker|completeOrganizationWorkItem|reassignOrganizationWorkItem|publishOrganizationContribution|certifyOrganization/,
  );

  assert.match(api, /export type OrganizationContribution/);
  assert.match(api, /listOrganizationContributions/);
  assert.match(api, /getOrganizationContribution/);

  assert.match(styles, /Phase 13\.16\.4/);
  assert.match(styles, /\.department-workspace/);
  assert.match(styles, /\.department-workspace-header/);
  assert.match(styles, /\.department-workspace-grid/);
  assert.match(styles, /\.department-workspace-card/);
  assert.match(styles, /\.department-metrics/);
});


test("13.16.5 Cross-department friction surface stays governed and read-only", async () => {
  const [friction, cockpit, nav, styles] = await Promise.all([
    read("app/cross-department-friction/page.tsx"),
    read("app/cockpit/page.tsx"),
    read("lib/workspace-navigation.ts"),
    read("app/globals.css"),
  ]);

  assert.match(nav, /Cross-department friction/);
  assert.match(nav, /href: "\/cross-department-friction"/);
  assert.match(nav, /pathname === "\/cross-department-friction"/);
  assert.match(cockpit, /href="\/cross-department-friction"/);
  assert.match(cockpit, /Cross-department view/);

  assert.match(friction, /className="cross-department-friction"/);
  assert.match(friction, /className="friction-summary"/);
  assert.match(friction, /className="friction-grid"/);
  assert.match(friction, /className="friction-lane friction-blockers"/);
  assert.match(friction, /className="friction-lane friction-dependencies"/);
  assert.match(friction, /listOrganizationBlockers\({ status: "open", page_size: 100 }\)/);
  assert.match(friction, /listOrganizationWorkItemDependencies\({ status: "active", page_size: 100 }\)/);
  assert.match(friction, /listOrganizationWorkItems\({ page_size: 100 }\)/);
  assert.match(friction, /listOrganizationHumanActionRequests\({ page_size: 100 }\)/);
  assert.match(friction, /listOrganizationActivities\({ page_size: 200 }\)/);
  assert.match(friction, /Affects:/);
  assert.match(friction, /Owned by:/);
  assert.match(friction, /Downstream:/);
  assert.match(friction, /Upstream:/);
  assert.match(friction, /Human request/);
  assert.match(friction, /Governed intervention/);
  assert.match(
    friction,
    /request\.source_object_type === sourceType && request\.source_object_id === sourceId/,
  );
  assert.doesNotMatch(
    friction,
    /organization_work_item_dependency"\) return request\.work_item_id === sourceId/,
  );
  assert.match(
    await read("lib/api.ts"),
    /export type OrganizationHumanActionRequest = \{[\s\S]*source_object_type: string \| null;[\s\S]*source_object_id: string \| null;[\s\S]*source_object_version: string \| null;/,
  );
  assert.match(friction, /friction view does not directly change blocker or dependency status/);
  assert.doesNotMatch(
    friction,
    /resolveOrganizationBlocker|waiveOrganizationBlocker|mitigateOrganizationBlocker|waiveOrganizationWorkItemDependency|completeOrganizationWorkItem|reassignOrganizationWorkItem/,
  );

  assert.match(styles, /Phase 13\.16\.5/);
  assert.match(styles, /\.cross-department-friction/);
  assert.match(styles, /\.friction-summary/);
  assert.match(styles, /\.friction-grid/);
  assert.match(styles, /\.friction-lane/);
  assert.match(styles, /\.friction-list/);
});
test("13.16.6 Owner Inbox prioritizes authority and materiality without duplicating mutations", async () => {
  const [inbox, cockpit, nav, styles] = await Promise.all([
    read("app/owner-inbox/page.tsx"),
    read("app/cockpit/page.tsx"),
    read("lib/workspace-navigation.ts"),
    read("app/globals.css"),
  ]);

  assert.match(nav, /Owner Inbox/);
  assert.match(nav, /href: "\/owner-inbox"/);
  assert.match(nav, /pathname === "\/owner-inbox"/);
  assert.match(cockpit, /href="\/owner-inbox"/);
  assert.match(cockpit, /Open Owner Inbox/);

  for (const binding of [
    "getBoardPacket()",
    "listOrganizationHumanActionRequests({ page_size: 100 })",
    "listOrganizationWorkItems({ page_size: 100 })",
    'listOrganizationBlockers({ status: "open", page_size: 100 })',
    'listOrganizationWorkItemDependencies({ status: "active", page_size: 100 })',
    "listOrganizationActivities({ page_size: 200 })",
  ]) {
    assert.ok(inbox.includes(binding), `missing Owner Inbox read binding ${binding}`);
  }

  assert.match(inbox, /pending_board/);
  assert.match(inbox, /requires_board_attention/);
  assert.match(inbox, /const BOARD_HUMAN_ROLES = new Set\(\["board"\]\);/);
  assert.doesNotMatch(inbox, /BOARD_HUMAN_ROLES = new Set\(\["admin"/);
  assert.match(inbox, /Authentication role alone does not establish Board authority/);
  assert.match(inbox, /isBoardOwnedWork/);
  assert.match(inbox, /HumanActionRequest exists ≠ Owner attention/);
  assert.match(inbox, /Priority comes from explicit authority, risk, emergency, due-date, and/);
  assert.match(inbox, /Decision required/);
  assert.match(inbox, /Critical Owner attention/);
  assert.match(inbox, /Human \/ escalation required/);
  assert.match(inbox, /title="Watch"/);
  assert.match(inbox, /Owner Inbox routes authority; it does not execute it/);
  assert.match(inbox, /href="\/board-room"/);
  assert.match(inbox, /\/cross-department-friction/);
  assert.match(inbox, /`\/workspace\/\$\{encodeURIComponent\(/);

  assert.doesNotMatch(
    inbox,
    /decideBoardItem|updateOrganizationControl|resolveOrganizationBlocker|waiveOrganizationBlocker|mitigateOrganizationBlocker|waiveOrganizationWorkItemDependency|completeOrganizationWorkItem|reassignOrganizationWorkItem|publishOrganizationContribution|certifyOrganization/,
  );
  assert.doesNotMatch(inbox, /\.includes\(["']urgent["']\)|title\.includes|recommendation\.includes/);

  assert.match(styles, /Phase 13\.16\.6 Owner decision and escalation inbox/);
  assert.match(styles, /\.owner-inbox \{/);
  assert.match(styles, /\.owner-inbox-lane/);
  assert.match(styles, /\.owner-inbox-item/);
  assert.match(styles, /\.owner-inbox-governance-note/);
  assert.match(styles, /Phase 13\.16\.6 Owner Inbox hero action contrast/);
  assert.match(styles, /\.owner-inbox-hero \.premium-button\.ghost/);
  assert.match(styles, /color: var\(--ink\);/);
});
test("13.16.7 secure Mobility User plan stays reviewed, pinned, and client-safe", async () => {
  const [portal, api, styles] = await Promise.all([
    read("components/ClientPortalPage.tsx"),
    read("lib/api.ts"),
    read("app/globals.css"),
  ]);

  assert.match(api, /export type ClientPortalMobilityPlan = \{/);
  assert.match(api, /mobility_plan: ClientPortalMobilityPlan \| null/);
  assert.match(api, /evidence_summary: ClientPortalEvidenceSummary \| null/);
  assert.match(api, /processing_evidence_status: "established" \| "not_established"/);

  assert.match(portal, /Reviewed mobility plan/);
  assert.match(portal, /Human-activated plan/);
  assert.match(portal, /Long-term progression/);
  assert.match(portal, /Reviewed plan &ne; authority outcome/);
  assert.match(portal, /Draft simulations and stale plan versions are kept out/);
  assert.match(portal, /No client-safe reviewed plan is visible yet/);
  assert.match(portal, /No pathway-aligned evidence assessment has completed human review yet/);

  assert.doesNotMatch(
    portal,
    /verified_rule_ids|source_snapshot_ids|review_notes|approved_by|owner_role|findings_json|document_snapshot_json/,
  );
  assert.doesNotMatch(
    portal,
    /generatePathwayComparison|generateMobilityTimeline|activateMobilityTimeline|transitionMobilityMilestone|evaluateEligibility/,
  );
  assert.doesNotMatch(
    api,
    /ClientPortalFollowUp|ClientPortalCommunication/,
  );

  assert.match(styles, /Phase 13\.16\.7 secure Mobility User experience/);
  assert.match(styles, /\.portal-plan-section/);
  assert.match(styles, /\.portal-plan-shell/);
  assert.match(styles, /\.portal-plan-journey/);
  assert.match(styles, /\.portal-plan-boundary/);
  assert.match(styles, /\.portal-plan-empty/);
  assert.ok(portal.includes('{" \\u00b7 "}'));
  assert.doesNotMatch(portal, /\? Planned/);
  assert.match(portal, /portal-risk-grid/);
  assert.match(
    styles,
    /\.portal-risk-grid > div:last-child:nth-child\(odd\)/,
  );
});

test("13.16.8 Professional / Operator experience composes governed case reads without creating a parallel dashboard", async () => {
  const [operations, casePage, navigation, styles, api, portal] = await Promise.all([
    read("app/page.tsx"),
    read("app/leads/[id]/page.tsx"),
    read("lib/workspace-navigation.ts"),
    read("app/globals.css"),
    read("lib/api.ts"),
    read("components/ClientPortalPage.tsx"),
  ]);

  assert.match(navigation, /label: "Professional \/ Operator"/);
  assert.match(navigation, /label: "Eligibility", href: "\/eligibility"/);
  assert.match(navigation, /label: "Operations Workspace", href: "\/"/);
  assert.match(navigation, /label: "Board Room", href: "\/board-room"/);

  assert.match(operations, /Professional attention desk/);
  assert.match(operations, /What requires professional attention now\?/);
  assert.match(operations, /className="operator-workflow-map"/);
  assert.match(operations, /Professional decision workflow/);
  assert.match(operations, /href: `\/leads\/\$\{item\.lead\.id\}\?tab=truth`/);
  assert.match(operations, /href: `\/leads\/\$\{item\.lead\.id\}\?tab=applications`/);
  assert.doesNotMatch(operations, /href: `\$\{apiBase\}\/api\/v1\/leads\/\$\{item\.lead\.id\}\/truth-resolution`/);

  for (const readBinding of [
    "getLatestEligibilityAssessment(id)",
    "getLatestPathwayComparison(id)",
    "listMobilityTimelines(id)",
    "listDocumentRequirementAssessments({ lead_id: id })",
    "listAuthorityAppointments({ application_id: application.id })",
    "listAgencySubmissions({ application_id: application.id })",
    "listExternalAgencyAssignments({ application_id: application.id })",
    "listApplicationAuthorityChecklistItems({ application_id: application.id })",
  ]) {
    assert.ok(casePage.includes(readBinding), `missing Professional / Operator read binding ${readBinding}`);
  }
  assert.match(casePage, /Promise\.allSettled/);
  assert.match(casePage, /Refreshing professional case reads/);
  assert.match(casePage, /Treat unavailable signals as unknown, not absent/);
  assert.match(casePage, /Human review required by persisted comparison/);
  assert.match(casePage, /professionalContext\.comparison\?\.human_review_required/);
  assert.match(casePage, /type DecisionContextSpine = \{/);
  assert.match(casePage, /buildDecisionContextSpine\(professionalContext\.comparison\)/);
  assert.match(casePage, /timelineMatchesDecisionContext\(timeline, decisionContextSpine\)/);
  assert.match(casePage, /requirementAssessmentMatchesDecisionContext\(assessment, decisionContextSpine\)/);
  assert.match(casePage, /timeline\.comparison_assessment_id === spine\.assessmentId/);
  assert.match(casePage, /timeline\.profile_id === spine\.profileId/);
  assert.match(casePage, /timeline\.profile_version === spine\.profileVersion/);
  assert.match(casePage, /timeline\.primary_pathway_id === spine\.pathwayId/);
  assert.match(casePage, /timeline\.primary_pathway_version_id === spine\.pathwayVersionId/);
  assert.match(casePage, /assessment\.profile_id === spine\.profileId/);
  assert.match(casePage, /assessment\.profile_version === spine\.profileVersion/);
  assert.match(casePage, /assessment\.pathway_id === spine\.pathwayId/);
  assert.match(casePage, /assessment\.pathway_version_id === spine\.pathwayVersionId/);
  assert.match(casePage, /excludedTimelines/);
  assert.match(casePage, /excludedRequirementAssessments/);
  assert.match(casePage, /Context alignment/);
  assert.match(casePage, /Context mismatch/);
  assert.match(casePage, /historical\/context-mismatch/);
  assert.match(casePage, /alignment to current comparison is not established/);
  assert.match(casePage, /Latest eligibility is shown separately and is not treated as context-aligned/);
  assert.match(casePage, /present_unverified/);
  assert.match(casePage, /Persisted operator records only/);
  assert.match(casePage, /No aligned persisted blocker signal/);
  assert.match(casePage, /No persisted next action/);
  assert.match(casePage, /TechnicalDisclosure/);
  assert.match(casePage, /These are case operations, not evidence for the current pathway/);

  assert.doesNotMatch(casePage, /const activeTimeline = timelinesByRecency/);
  assert.doesNotMatch(casePage, /const latestRequirementAssessment = \[\.\.\.professionalContext\.requirementAssessments\]/);
  assert.doesNotMatch(casePage, /for \(const requirement of professionalContext\.eligibility\?\.factors\.eligibility_requirements/);

  const contextIndex = casePage.indexOf("Decision / case context");
  const blockersIndex = casePage.indexOf("Blockers & uncertainty");
  const actionsIndex = casePage.indexOf("Next governed actions");
  const evidenceIndex = casePage.indexOf("Supporting evidence & review state");
  const alignmentIndex = casePage.indexOf("contextAlignmentLabel");
  const provenanceIndex = casePage.indexOf("<TechnicalDisclosure", evidenceIndex);
  assert.ok(alignmentIndex >= 0 && alignmentIndex < provenanceIndex, "material context alignment must be visible before technical provenance");
  assert.ok(contextIndex >= 0 && contextIndex < blockersIndex, "decision context must precede blockers");
  assert.ok(blockersIndex < actionsIndex, "blockers must precede next governed actions");
  assert.ok(actionsIndex < evidenceIndex, "next governed actions must precede supporting evidence");
  assert.ok(evidenceIndex < provenanceIndex, "supporting evidence must precede technical provenance");

  assert.doesNotMatch(
    casePage,
    /evaluateEligibility\(|comparePathways\(|generateMobilityTimeline\(|activateMobilityTimeline\(|transitionMobilityMilestone\(|generateDocumentRequirementAssessment\(|reviewDocumentRequirementAssessment\(|createAuthorityAppointment\(|createAgencySubmission\(|applyAuthorityChecklistTemplate\(/,
  );

  for (const readContract of [
    "getLatestEligibilityAssessment",
    "getLatestPathwayComparison",
    "listMobilityTimelines",
    "listDocumentRequirementAssessments",
    "listAuthorityAppointments",
    "listAgencySubmissions",
    "listExternalAgencyAssignments",
    "listApplicationAuthorityChecklistItems",
  ]) {
    assert.ok(api.includes(`export async function ${readContract}`), `missing existing API read contract ${readContract}`);
  }

  assert.match(styles, /Phase 13\.16\.8 Professional \/ Operator experience/);
  assert.match(styles, /\.operator-workflow-map/);
  assert.match(styles, /\.operator-case-workbench/);
  assert.match(styles, /\.operator-reliance-boundary/);
  assert.match(styles, /\.operator-evidence-grid/);
  assert.match(styles, /@media \(max-width: 640px\)[\s\S]*\.operator-workflow-map/);

  assert.doesNotMatch(portal, /operator-case-workbench|Technical provenance.*Eligibility assessment/);
});

test("13.16.9 evidence and provenance UX uses one presentation taxonomy without changing evidence authority", async () => {
  const [component, casePage, pathways, sourceReview, documents, styles] = await Promise.all([
    read("components/EvidenceProvenance.tsx"),
    read("app/leads/[id]/page.tsx"),
    read("app/pathways/page.tsx"),
    read("app/source-certification-review/page.tsx"),
    read("app/document-intelligence/page.tsx"),
    read("app/globals.css"),
  ]);

  assert.match(component, /role="list"/);
  assert.match(component, /role="listitem"/);
  assert.match(component, /Evidence boundary/);
  assert.match(component, /aria-current=/);
  assert.doesNotMatch(component, /lib\/api|fetch\(|onClick=|<button/);

  assert.match(casePage, /Current decision evidence chain/);
  assert.match(casePage, /source URL alone does not establish certification, a VerifiedRule, or pathway applicability/);
  assert.match(casePage, /Historical or mismatched assessments are excluded/);

  assert.match(pathways, /Source-to-pathway evidence chain/);
  assert.match(pathways, /selectedSnapshot\.content_hash/);
  assert.match(pathways, /selectedRules\.map\(\(rule\) => rule\.rule_key\)/);
  assert.match(pathways, /Publishing a pathway remains a separate human-reviewed backend action/);

  assert.match(sourceReview, /Source certification provenance/);
  assert.match(sourceReview, /Approving source certification does not itself publish a VerifiedRule/);
  assert.match(sourceReview, /Certification review changes only the governed certification state/);

  assert.match(documents, /Case evidence provenance/);
  assert.match(documents, /OCR\/extraction output is derived data/);
  assert.match(documents, /never turns a case document into an official source, a VerifiedRule, legal truth, or an authority decision/);

  const combined = [casePage, pathways, sourceReview, documents].join("\n");
  for (const stage of [
    "Official source",
    "Immutable snapshot",
    "Certification / review",
    "VerifiedRule",
    "Pathway evidence",
    "Case evidence",
    "Superseded / historical",
    "Unresolved gaps",
  ]) {
    assert.ok(combined.includes(stage), `missing evidence/provenance stage ${stage}`);
  }

  assert.match(styles, /Phase 13\.16\.9 evidence and provenance UX consolidation/);
  assert.match(styles, /\.evidence-provenance-grid/);
  assert.match(styles, /\.evidence-provenance-boundary/);
});

test("13.16.10 integrated accessibility keeps mobile focus, secure portal states, and responsive role handoffs governed", async () => {
  const [shell, portal, myMobility, styles] = await Promise.all([
    read("components/WorkspaceShell.tsx"),
    read("components/ClientPortalPage.tsx"),
    read("app/my-mobility/page.tsx"),
    read("app/globals.css"),
  ]);

  assert.match(shell, /menuButtonRef/);
  assert.match(shell, /mobileNavWasOpenRef/);
  assert.match(shell, /document\.body\.style\.overflow = "hidden"/);
  assert.match(shell, /containMobileNavigationFocus/);
  assert.match(shell, /event\.key === "Escape"/);
  assert.match(shell, /event\.key !== "Tab"/);
  assert.match(shell, /menuButtonRef\.current\?\.focus\(\)/);
  assert.match(shell, /type="button"/);

  assert.match(portal, /aria-busy="true"/);
  assert.match(portal, /role="status" aria-live="polite"/);
  assert.match(portal, /aria-labelledby="portal-access-title"/);
  assert.match(portal, /aria-invalid=\{Boolean\(error\)\}/);
  assert.match(portal, /aria-describedby=\{error \? "portal-access-error" : undefined\}/);
  assert.match(portal, /id="portal-access-error"[\s\S]*role="alert"/);
  assert.match(portal, /aria-labelledby="portal-workspace-title"/);
  assert.match(portal, /id="portal-workspace-title"/);

  assert.match(myMobility, /href="\/portal"/);
  assert.match(myMobility, /Personal case details are shown only after secure portal access is established/);

  assert.match(styles, /Phase 13\.16\.10 integrated accessibility and responsive acceptance/);
  assert.match(styles, /:focus-visible[\s\S]*outline: 2px solid var\(--green\)/);
  assert.match(styles, /\.mobile-menu-button,[\s\S]*min-height: 44px/);
  assert.match(styles, /\.portal-token-form input\[aria-invalid="true"\]/);
  assert.match(styles, /@media \(max-width: 720px\)[\s\S]*\.workspace,[\s\S]*overflow-x: clip/);
});

test("13.16.10 mobile visual composition keeps Cockpit and Operations narrative panels sequential", async () => {
  const styles = await read("app/globals.css");
  assert.match(styles, /Phase 13\.16\.10 mobile visual acceptance correction/);
  assert.match(styles, /@media \(max-width: 900px\)[\s\S]*\.cockpit-command \{[\s\S]*grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*\.command-strip \{[\s\S]*display: grid;[\s\S]*min-height: 0/);
  assert.match(styles, /\.system-canvas \{[\s\S]*position: relative;[\s\S]*order: 2;[\s\S]*transform: none/);
  assert.match(styles, /\.premium-grid,[\s\S]*\.governance-grid \{[\s\S]*grid-template-columns: minmax\(0, 1fr\)/);
});
