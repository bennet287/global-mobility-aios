import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-my-case-artifacts";

const dashboardFixture = {
  grant_id: "grant-my-case-convergence",
  client_name: "Avery Client",
  target_country: "Austria",
  intent: "work",
  case_status: "human_review",
  next_action: "Attend your authority appointment",
  application_stage: "submitted",
  updated_at: "2026-09-10T07:30:00Z",
  expires_at: "2026-09-17T07:30:00Z",
  document_counts: { verified: 0 },
  documents: [],
  milestones: [],
  appointments: [],
  submissions: [],
  external_agency_assignments: [],
  authority_checklist: [],
  mobility_plan: null,
  evidence_summary: null,
};

async function mockDashboard(page: Page) {
  await page.route("**/api/v1/public/client-portal/dashboard*", async (route) => {
    const request = route.request();
    const corsHeaders = {
      "access-control-allow-origin": "http://127.0.0.1:3000",
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": [
        "Content-Type",
        "X-GMAI-Portal-Token",
        "X-GMAI-Portal-Device",
        "X-GMAI-Role",
        "X-GMAI-User",
      ].join(", "),
    };

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders });
      return;
    }

    await route.fulfill({
      status: 200,
      headers: { ...corsHeaders, "content-type": "application/json" },
      body: JSON.stringify(dashboardFixture),
    });
  });
}

async function prepareSecureEntry(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.removeItem("gmai-client-portal-token");
    sessionStorage.removeItem("gmai-client-portal-device");
  });
  await page.goto("/portal", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /Your mobility case/i })).toBeVisible();
  await expect(page.getByLabel("Access token")).toBeVisible();
  await expect(page.getByRole("button", { name: "Open secure workspace" })).toBeDisabled();
  await expect(page.getByText("No password, public case search, or personal-data lookup is used.")).toBeVisible();
  await expect(page.getByText("Encrypted transport", { exact: true })).toBeVisible();
  await expect(page.getByText("Expiring access", { exact: true })).toBeVisible();
  await expect(page.getByText("Audited activity", { exact: true })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "My Case workspace navigation" })).toBeHidden();
}

test("Mobility My Case secure entry desktop visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await prepareSecureEntry(page);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-my-case-desktop.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Mobility My Case secure entry phone visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await prepareSecureEntry(page);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-my-case-phone.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Mobility My Case permits user zoom", async ({ page }) => {
  await prepareSecureEntry(page);
  const viewport = page.locator('meta[name="viewport"]');
  await expect(viewport).toHaveAttribute("content", /width=device-width/);
  await expect(viewport).not.toHaveAttribute("content", /user-scalable=no/i);
  await expect(viewport).not.toHaveAttribute("content", /maximum-scale=1/i);
});

test("Mobility My Case authenticated workspace converges all five destinations", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await mockDashboard(page);
  await page.goto("/portal?token=gmai_portal_convergence", { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { name: /Welcome back/i })).toBeVisible();
  const navigation = page.getByRole("navigation", { name: "My Case workspace navigation" });
  await expect(navigation).toBeVisible();
  await expect(navigation.getByRole("link", { name: "Overview" })).toHaveAttribute("href", "/my-mobility");
  await expect(navigation.getByText("My Case", { exact: true })).toHaveAttribute("aria-current", "page");
  await expect(navigation.getByRole("link", { name: "Documents" })).toHaveAttribute("href", "/portal/documents");
  await expect(navigation.getByRole("link", { name: "Timeline" })).toHaveAttribute("href", "/portal/timeline");
  await expect(navigation.getByRole("link", { name: "Messages" })).toHaveAttribute("href", "/portal/messages");
  await expect(page).toHaveURL("/portal");

  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-my-case-authenticated-convergence.png`,
    fullPage: true,
    animations: "disabled",
  });
});
