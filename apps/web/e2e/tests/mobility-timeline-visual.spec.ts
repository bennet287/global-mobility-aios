import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-timeline-artifacts";

const dashboardFixture = {
  grant_id: "grant-timeline-visible-review",
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
  milestones: [
    { key: "received", label: "Case received", state: "complete" },
    { key: "review", label: "Consultant review", state: "current" },
  ],
  appointments: [
    {
      id: "appointment-bmeia",
      authority_name: "Residence Authority",
      appointment_type: "document_review",
      location: "Vienna",
      scheduled_at: "2026-10-02T08:30:00Z",
      timezone: "Europe/Vienna",
      status: "scheduled",
      reference_number: "APT-2048",
    },
  ],
  submissions: [
    {
      id: "submission-rwr",
      authority_name: "Residence Authority",
      submission_channel: "in_person",
      submitted_at: "2026-09-08T09:00:00Z",
      status: "received",
      reference_number: "SUB-1042",
      tracking_url: null,
    },
  ],
  external_agency_assignments: [
    {
      id: "agency-translation",
      agency_name: "Certified Translation Partner",
      status: "completed",
      agency_reference_number: "TR-17",
      handoff_at: "2026-09-04T08:00:00Z",
      completed_at: "2026-09-06T14:00:00Z",
      sla_due_at: null,
      sla_status: "met",
      sla_breached_at: null,
    },
  ],
  authority_checklist: [],
  mobility_plan: {
    timeline_id: "internal-timeline-id",
    comparison_assessment_id: "internal-comparison-id",
    profile_version: 3,
    pathway_id: "internal-pathway-id",
    pathway_version_id: "internal-pathway-version-id",
    pathway_version_number: 2,
    pathway_name: "Red-White-Red Card",
    country: "Austria",
    domain: "work",
    plan_status: "active",
    current_stage_key: "authority_review",
    activated_at: "2026-08-28T12:00:00Z",
    published_at: "2026-08-28T12:00:00Z",
    processing_evidence_status: "established",
    cost: {
      currency: "EUR",
      government_application_fee: 160,
      government_application_fee_scope: "main_applicant",
      estimated_total_status: "not_established",
      minimum_funds: null,
    },
    risk: null,
    journey: [
      { key: "case_intake", title: "Case intake", state: "complete", due_at: null, requires_human_approval: false },
      { key: "authority_review", title: "Authority review", state: "current", due_at: "2026-10-02", requires_human_approval: true },
      { key: "authority_outcome", title: "Authority outcome", state: "upcoming", due_at: null, requires_human_approval: false },
    ],
  },
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

test("Timeline remains fail-closed before secure access", async ({ page }) => {
  await clearSecureSession(page);
  await page.goto("/portal/timeline", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /timeline stays private/i })).toBeVisible();
  await expect(page.getByLabel("Access token")).toBeVisible();
  await expect(page.getByText("Authority review", { exact: true })).toHaveCount(0);
  await expect(page.getByText("SUB-1042", { exact: false })).toHaveCount(0);
});

test("Timeline reports invalid secure access without exposing records", async ({ page }) => {
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
  await page.goto("/portal/timeline?token=invalid", { waitUntil: "networkidle" });
  await expect(page.locator("#timeline-access-error")).toHaveText(/invalid, expired, or has been revoked/i);
  await expect(page.getByText("Authority review", { exact: true })).toHaveCount(0);
});

test("Timeline desktop client-safe visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await mockDashboard(page, dashboardFixture, writes);
  await page.goto("/portal/timeline?token=gmai_portal_visible_review", { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { name: "Your journey, in order." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Authority review" })).toBeVisible();
  await expect(page.getByText("Human approval required", { exact: false })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Submitted to Residence Authority" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Certified Translation Partner" })).toBeVisible();
  await expect(page.getByText(/Current journey ≠ complete audit history/)).toBeVisible();
  await expect(page.getByText("internal-timeline-id", { exact: false })).toHaveCount(0);
  await expect(page.getByText("internal-comparison-id", { exact: false })).toHaveCount(0);
  await expect(page).toHaveURL("/portal/timeline");
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);

  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-timeline-desktop.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Timeline partial record state remains explicit", async ({ page }) => {
  const partialFixture = {
    ...dashboardFixture,
    application_stage: null,
    milestones: [],
    appointments: [],
    submissions: [],
    external_agency_assignments: [],
    mobility_plan: null,
  };
  await mockDashboard(page, partialFixture);
  await page.goto("/portal/timeline?token=gmai_portal_partial", { waitUntil: "networkidle" });
  await expect(page.getByText("Not established", { exact: true })).toBeVisible();
  await expect(page.getByText("Journey detail is not available.", { exact: true })).toBeVisible();
  await expect(page.getByText("No dated case events are visible yet.", { exact: true })).toBeVisible();
});

test("Timeline phone composition remains accessible and overflow-free", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await mockDashboard(page, dashboardFixture, writes);
  await page.goto("/portal/timeline?token=gmai_portal_visible_review", { waitUntil: "networkidle" });

  await expect(page.getByRole("navigation", { name: "Timeline workspace navigation" })).toBeVisible();
  await expect(page.getByText("Timeline", { exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { level: 1, name: "Your journey, in order." })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Where your case stands." })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "What has been recorded." })).toBeVisible();

  const close = page.getByRole("button", { name: "Close secure session" });
  await close.focus();
  expect(await close.evaluate((element) => getComputedStyle(element).boxShadow)).not.toBe("none");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);

  const viewport = page.locator('meta[name="viewport"]');
  await expect(viewport).toHaveAttribute("content", /width=device-width/);
  await expect(viewport).not.toHaveAttribute("content", /user-scalable=no/i);
  await expect(viewport).not.toHaveAttribute("content", /maximum-scale=1/i);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-timeline-phone.png`,
    fullPage: true,
    animations: "disabled",
  });
});
