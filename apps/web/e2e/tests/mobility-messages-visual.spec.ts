import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-messages-artifacts";

const dashboardFixture = {
  grant_id: "grant-messages-visible-review",
  client_name: "Avery Client",
  target_country: "Austria",
  intent: "work",
  case_status: "human_review",
  next_action: "Attend your authority appointment",
  application_stage: "submitted",
  updated_at: "2026-09-10T07:30:00Z",
  expires_at: "2026-09-17T07:30:00Z",
  document_counts: { verified: 2 },
  documents: [],
  milestones: [],
  appointments: [],
  submissions: [],
  external_agency_assignments: [],
  authority_checklist: [],
  mobility_plan: null,
  evidence_summary: null,
};

async function mockDashboard(page: Page, fixture = dashboardFixture, writes: string[] = []) {
  await page.route("**/api/v1/public/client-portal/dashboard*", async (route) => {
    const request = route.request();
    if (request.method() !== "GET" && request.method() !== "OPTIONS") writes.push(request.method());
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
      body: JSON.stringify(fixture),
    });
  });
}

async function clearSecureSession(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.removeItem("gmai-client-portal-token");
    sessionStorage.removeItem("gmai-client-portal-device");
  });
}

test("Messages remains fail-closed before secure access", async ({ page }) => {
  await clearSecureSession(page);
  await page.goto("/portal/messages", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /Communication stays private/i })).toBeVisible();
  await expect(page.getByLabel("Access token")).toBeVisible();
  await expect(page.getByText("Attend your authority appointment", { exact: true })).toHaveCount(0);
  await expect(page.getByText(/Delivered-message history is unavailable/i)).toHaveCount(0);
});

test("Messages reports invalid secure access without exposing guidance", async ({ page }) => {
  await clearSecureSession(page);
  await page.route("**/api/v1/public/client-portal/dashboard*", async (route) => {
    await route.fulfill({
      status: 404,
      headers: {
        "access-control-allow-origin": "http://127.0.0.1:3000",
        "content-type": "application/json",
      },
      body: JSON.stringify({ detail: "Client portal access is invalid or unavailable" }),
    });
  });
  await page.goto("/portal/messages?token=invalid", { waitUntil: "networkidle" });
  await expect(page.locator("#messages-access-error")).toHaveText(/invalid, expired, or has been revoked/i);
  await expect(page.getByText("Attend your authority appointment", { exact: true })).toHaveCount(0);
});

test("Messages desktop client-safe visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await mockDashboard(page, dashboardFixture, writes);
  await page.goto("/portal/messages?token=gmai_portal_visible_review", { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { level: 1, name: "Your communication space." })).toBeVisible();
  await expect(page.getByText("Attend your authority appointment", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Delivered-message history is unavailable." })).toBeVisible();
  await expect(page.getByText("No delivered-message claim is made.", { exact: true })).toBeVisible();
  await expect(page.getByText(/Draft ≠ sent · reviewed ≠ delivered/)).toBeVisible();
  await expect(page.getByText("Sent", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Delivered", { exact: true })).toHaveCount(0);
  await expect(page).toHaveURL("/portal/messages");
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);

  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-messages-desktop.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Messages explicitly distinguishes missing send/history contracts", async ({ page }) => {
  await mockDashboard(page);
  await page.goto("/portal/messages?token=gmai_portal_boundary", { waitUntil: "networkidle" });
  await expect(page.getByText("In-app reply", { exact: true })).toBeVisible();
  await expect(page.getByText("No accepted client-send contract exists on this surface yet.", { exact: true })).toBeVisible();
  await expect(page.getByText(/does not currently expose a client-safe delivered-message record/i)).toBeVisible();
  await expect(page.getByRole("textbox")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /send|reply/i })).toHaveCount(0);
});

test("Messages phone composition remains accessible and overflow-free", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await mockDashboard(page, dashboardFixture, writes);
  await page.goto("/portal/messages?token=gmai_portal_visible_review", { waitUntil: "networkidle" });

  const navigation = page.getByRole("navigation", { name: "Messages workspace navigation" });
  await expect(navigation).toBeVisible();
  await expect(navigation.getByText("Messages", { exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { level: 2, name: "What your case currently needs." })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Use your established secure channel." })).toBeVisible();

  const close = page.getByRole("button", { name: "Close secure session" });
  await close.focus();
  expect(await close.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe("none");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);

  const viewport = page.locator('meta[name="viewport"]');
  await expect(viewport).toHaveAttribute("content", /width=device-width/);
  await expect(viewport).not.toHaveAttribute("content", /user-scalable=no/i);
  await expect(viewport).not.toHaveAttribute("content", /maximum-scale=1/i);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-messages-phone.png`,
    fullPage: true,
    animations: "disabled",
  });
});