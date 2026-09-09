import { expect, test } from "@playwright/test";

const fixtureLeadId = "operator-v2-profile-fixture";

const operatorRoutes = [
  { href: "/", label: "Work" },
  { href: `/profiles?lead_id=${fixtureLeadId}`, label: "Profiles" },
  { href: "/operator/v2/pathways", label: "Pathways" },
  { href: "/document-intelligence", label: "Evidence" },
  { href: "/communications", label: "Communication" },
  { href: "/operator/v2/tools", label: "Tools" },
] as const;

const lead = {
  id: fixtureLeadId,
  full_name: "Alex Morgan",
  email: "alex@example.test",
  phone: null,
  source: "operator-v2-proof",
  intent: "work",
  target_country: "Austria",
  status: "qualified",
  notes: null,
};

const profileFixture = {
  id: "profile-v3",
  lead_id: fixtureLeadId,
  profile_version: 3,
  lifecycle_status: "active",
  supersedes_profile_id: "profile-v2",
  current_country: "Austria",
  education: [{ qualification: "Master of Business Administration", field_of_study: "Supply Chain Management", institution: "AIOS Professional Institute", country: "Austria", completion_year: 2026 }],
  employment: [{ role: "Operations Analyst", employer: "Northstar Mobility", country: "Austria", years: 3.5, current: true }],
  years_experience: 3.5,
  skills: ["Operations", "Supply chain", "Project delivery"],
  languages: [{ language: "German", level: "B2", test_name: "Goethe-Zertifikat", test_score: "B2" }],
  family: { status: "single", members: [], details_confirmed: true },
  finances: { budget_eur: 18000, funding_source: "Personal savings" },
  goals: [{ domain: "work", target_country: "Austria", desired_role_or_program: "Supply Chain Specialist", target_date: "2027-06-01T00:00:00Z", priority: "high" }],
  constraints: { items: [{ type: "operator_note", value: "Prefer Vienna or Lower Austria" }], confirmed: true },
  consent: { status: "granted", purposes: ["eligibility", "document_processing", "communications"], expires_at: "2027-06-30T00:00:00Z", recorded_at: "2026-08-10T10:00:00Z" },
  evidence_document_ids: ["doc-passport", "doc-degree", "doc-language"],
  completeness_score: 92,
  readiness_stage: "decision_ready",
  consent_status: "granted",
  missing_sections: ["employment_reference"],
  activated_at: "2026-08-11T09:00:00Z",
  updated_by: "frontend-operator",
  created_at: "2026-08-11T09:00:00Z",
  updated_at: "2026-09-08T12:00:00Z",
};

const documents = [
  { id: "doc-passport", lead_id: fixtureLeadId, document_type: "passport", filename: "passport.pdf", status: "verified", verified_by: "operator-reviewer", expiry_date: "2029-04-12", storage_provider: "minio", storage_reference_present: true, file_hash: "3ad8c9f148deec9a01", mime_type: "application/pdf", file_size_bytes: 480000, signed_access_supported: true, storage_key_exposed: false },
  { id: "doc-degree", lead_id: fixtureLeadId, document_type: "degree", filename: "mba-degree.pdf", status: "verified", verified_by: "operator-reviewer", expiry_date: null, storage_provider: "minio", storage_reference_present: true, file_hash: "84ef11a2d92cc201bb", mime_type: "application/pdf", file_size_bytes: 720000, signed_access_supported: true, storage_key_exposed: false },
  { id: "doc-language", lead_id: fixtureLeadId, document_type: "language_certificate", filename: "german-b2.pdf", status: "reviewed", verified_by: null, expiry_date: "2027-03-01", storage_provider: "minio", storage_reference_present: true, file_hash: "29fba1180d3e9a14cc", mime_type: "application/pdf", file_size_bytes: 310000, signed_access_supported: true, storage_key_exposed: false },
];

const communicationDrafts = [
  {
    draft: { id: "11111111-1111-4111-8111-111111111111", lead_id: fixtureLeadId, channel: "email_draft", status: "pending", created_at: "2026-09-08T15:00:00", updated_at: "2026-09-08T15:00:00" },
    communication: { template_key: "approval_confirmation", title: "Approval confirmation", subject: "Your application has been approved - next steps", body: "Dear Alex Morgan, your authority-approved case is ready for professional review before any manual communication.", note: null, status: "draft", channel: "email_draft", created_at: "2026-09-08T15:00:00", updated_at: "2026-09-08T15:00:00" },
    lead,
  },
  {
    draft: { id: "22222222-2222-4222-8222-222222222222", lead_id: fixtureLeadId, channel: "email_draft", status: "completed", created_at: "2026-09-07T10:00:00", updated_at: "2026-09-08T10:00:00" },
    communication: { template_key: "travel_checklist", title: "Travel checklist", subject: "Travel preparation checklist", body: "Reviewed travel preparation guidance for Alex Morgan.", note: "Reviewed by operator.", status: "reviewed", channel: "email_draft", created_at: "2026-09-07T10:00:00", updated_at: "2026-09-08T10:00:00" },
    lead,
  },
];

const storagePosture = {
  environment: "test",
  backend: "minio",
  strict_mode: true,
  signed_access_secret_configured: true,
  signed_access_ttl_seconds: 120,
  signed_access_max_ttl_seconds: 300,
  minio_tls_enabled: true,
  minio_default_credentials: false,
  bucket_auto_create: false,
  server_side_encryption_enabled: true,
  retention_days: 90,
  backup_strategy_configured: true,
  recovery_test_recorded: true,
  local_storage_allowed_in_production: false,
  failures: [],
  ready: true,
  signed_access_enabled: true,
  direct_object_urls_enabled: false,
  storage_credentials_exposed: false,
  unrestricted_object_keys_exposed: false,
  allowed_purposes: ["operator_review"],
};

async function installOperatorFixture(page: import("@playwright/test").Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const origin = request.headers().origin || "http://127.0.0.1:3000";
    const headers = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    };
    const json = async (body: unknown, status = 200) => route.fulfill({ status, headers, contentType: "application/json", body: JSON.stringify(body) });

    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers, body: "" });
    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);

    if (url.pathname === "/health") return json({ status: "ok", service: "operator-v2-fixture", environment: "test" });

    if (url.pathname === "/api/v1/crm/summary") return json({ leads_total: 0, leads_new: 0, leads_human_review: 0, leads_converted: 0, truth_queue_pending: 0, truth_queue_resolved: 0, recent_leads: [], recent_truth_audits: [] });
    if (url.pathname === "/api/v1/truth/resolution-queue") return json({ total_leads: 0, stage_counts: {}, items: [] });
    if (url.pathname === "/api/v1/applications/queue") return json({ total_leads: 0, stage_counts: {}, items: [] });
    if (url.pathname === "/api/v1/documents/verification-queue") return json({ count: 0, documents: [] });
    if (url.pathname === "/api/v1/agent-output-reviews/dashboard") return json({ version: "operator-v2-proof", filters: {}, counts: {}, items: [] });

    if (url.pathname === "/api/v1/leads") return json([lead]);
    if (url.pathname === `/api/v1/profiles/leads/${fixtureLeadId}/current`) return json(profileFixture);
    if (url.pathname === `/api/v1/profiles/leads/${fixtureLeadId}/history`) return json([
      profileFixture,
      { ...profileFixture, id: "profile-v2", profile_version: 2, lifecycle_status: "superseded", supersedes_profile_id: "profile-v1", completeness_score: 84, readiness_stage: "review_ready", missing_sections: ["employment_reference", "language_evidence"], created_at: "2026-07-15T09:00:00Z", updated_at: "2026-08-10T08:00:00Z" },
    ]);
    if (url.pathname === `/api/v1/leads/${fixtureLeadId}/detail`) return json({ lead, profiles: [], truth_claims: [], source_references: [], reviews: [], workflow_runs: [], agent_runs: [], follow_ups: [], documents, applications: [] });
    if (url.pathname === "/api/v1/client-communications/drafts") return json({ total_drafts: communicationDrafts.length, drafts: communicationDrafts });

    if (url.pathname.toLowerCase().includes("posture")) return json(storagePosture);
    if (url.pathname.toLowerCase().includes("schema")) return json([]);
    if (request.method() === "GET") return json([]);
    return json({ detail: "Operator V2 acceptance fixture blocks writes" }, 405);
  });
}

for (const width of [1280, 390]) {
  test(`Phase 10I Operator primary destinations remain navigable and bounded at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
    await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });

    const writes: string[] = [];
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installOperatorFixture(page, writes);

    for (const route of operatorRoutes) {
      await page.goto(route.href);

      const root = page.locator(".aios-v2-root");
      const main = page.locator("#aios-v2-operator-main");
      const nav = page.getByRole("navigation", { name: "Professional / Operator" });
      const active = nav.getByLabel(route.label, { exact: true });

      await expect(root).toBeVisible();
      await expect(main).toBeVisible();
      await expect(nav).toBeVisible();
      await expect(active).toHaveAttribute("aria-current", "page");
      await expect(page.getByLabel("AIOS V2 theme")).toBeVisible();

      for (const item of operatorRoutes) await expect(nav.getByLabel(item.label, { exact: true })).toBeVisible();

      if (route.label === "Profiles") {
        await expect(page.getByRole("heading", { name: "Alex Morgan" })).toBeVisible();
        await expect(page.getByText("92%", { exact: true })).toBeVisible();
        await expect(page.getByText("Version 3", { exact: true })).toBeVisible();
      }

      if (route.label === "Evidence") {
        await page.getByLabel("Lead").selectOption(fixtureLeadId);
        await expect(page.getByText("Case evidence provenance", { exact: true })).toBeVisible();
        await expect(page.getByText("passport.pdf", { exact: true })).toBeVisible();
        await expect(page.getByText("mba-degree.pdf", { exact: true })).toBeVisible();
        await expect(page.getByText("3 stored documents", { exact: true })).toBeVisible();
      }

      if (route.label === "Communication") {
        await expect(page.getByText("Client communication queue", { exact: true })).toBeVisible();
        await expect(page.getByText("Approval confirmation", { exact: true })).toBeVisible();
        await expect(page.getByText("Travel checklist", { exact: true })).toBeVisible();
        await expect(page.getByText("Your application has been approved - next steps", { exact: true })).toBeVisible();
        await expect(page.getByRole("link", { name: "Review" }).first()).toBeVisible();
      }

      const geometry = await page.evaluate(() => {
        const root = document.querySelector<HTMLElement>(".aios-v2-root");
        const main = document.querySelector<HTMLElement>("#aios-v2-operator-main");
        if (!root || !main) return null;
        const mainRect = main.getBoundingClientRect();
        return { viewport: window.innerWidth, documentWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth, rootWidth: root.scrollWidth, mainLeft: mainRect.left, mainRight: mainRect.right };
      });

      expect(geometry).not.toBeNull();
      expect(geometry!.documentWidth).toBeLessThanOrEqual(geometry!.viewport);
      expect(geometry!.bodyWidth).toBeLessThanOrEqual(geometry!.viewport);
      expect(geometry!.rootWidth).toBeLessThanOrEqual(geometry!.viewport);
      expect(geometry!.mainLeft).toBeGreaterThanOrEqual(-1);
      expect(geometry!.mainRight).toBeLessThanOrEqual(geometry!.viewport + 1);

      if (width === 390) {
        const activeBox = await active.boundingBox();
        expect(activeBox?.height ?? 0).toBeGreaterThanOrEqual(44);
        expect(activeBox?.width ?? 0).toBeGreaterThanOrEqual(44);
      }

      await page.screenshot({ path: `operator-v2-artifacts/${route.label.toLowerCase()}-${width === 390 ? "phone" : "desktop"}.png`, fullPage: true });
    }

    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}
