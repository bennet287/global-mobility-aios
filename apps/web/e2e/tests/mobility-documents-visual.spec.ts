import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-documents-artifacts";

const dashboardFixture = {
  grant_id: "grant-visible-review",
  client_name: "Avery Client",
  target_country: "Austria",
  intent: "work",
  case_status: "in_review",
  next_action: "Wait for document review",
  application_stage: "not_submitted",
  updated_at: "2026-09-10T07:30:00Z",
  expires_at: "2026-09-17T07:30:00Z",
  document_counts: { uploaded: 1, verified: 1 },
  documents: [
    {
      id: "doc-passport",
      document_type: "passport",
      filename: "passport.pdf",
      status: "verified",
      uploaded_at: "2026-09-08T09:00:00Z",
      expiry_date: "2031-05-18",
    },
    {
      id: "doc-degree",
      document_type: "degree_certificate",
      filename: "degree-certificate.pdf",
      status: "uploaded",
      uploaded_at: "2026-09-09T11:15:00Z",
      expiry_date: null,
    },
  ],
};

async function mockDashboard(page: Page) {
  await page.route("**/api/v1/public/client-portal/dashboard*", async (route) => {
    const request = route.request();
    const corsHeaders = {
      "access-control-allow-origin": "http://127.0.0.1:3000",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": "X-GMAI-Portal-Token, X-GMAI-Portal-Device, Content-Type",
    };

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders });
      return;
    }

    await route.fulfill({
      status: 200,
      headers: {
        ...corsHeaders,
        "content-type": "application/json",
      },
      body: JSON.stringify(dashboardFixture),
    });
  });
}

test("Documents remains fail-closed before secure access", async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.removeItem("gmai-client-portal-token");
    sessionStorage.removeItem("gmai-client-portal-device");
  });
  await page.goto("/portal/documents", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /document room stays private/i })).toBeVisible();
  await expect(page.getByLabel("Access token")).toBeVisible();
  await expect(page.getByText("passport.pdf", { exact: true })).toHaveCount(0);
});

test("Documents desktop client-safe visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await mockDashboard(page);
  await page.goto("/portal/documents?token=gmai_portal_visible_review", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Your document room." })).toBeVisible();
  await expect(page.getByText("passport.pdf", { exact: true })).toBeVisible();
  await expect(page.getByText("Degree Certificate", { exact: true })).toBeVisible();
  await expect(page.getByText(/Document status ≠ authority outcome/)).toBeVisible();
  await page.screenshot({ path: `${ARTIFACT_DIR}/mobility-documents-desktop.png`, fullPage: true, animations: "disabled" });
});

test("Documents phone client-safe visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboard(page);
  await page.goto("/portal/documents?token=gmai_portal_visible_review", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Your document room." })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: `${ARTIFACT_DIR}/mobility-documents-phone.png`, fullPage: true, animations: "disabled" });
});
