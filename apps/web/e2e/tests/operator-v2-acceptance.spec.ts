import { expect, test } from "@playwright/test";

const profileFixtureLeadId = "operator-v2-profile-fixture";

const operatorRoutes = [
  { href: "/", label: "Work" },
  { href: `/profiles?lead_id=${profileFixtureLeadId}`, label: "Profiles" },
  { href: "/operator/v2/pathways", label: "Pathways" },
  { href: "/operator/v2/evidence", label: "Evidence" },
  { href: "/operator/v2/communication", label: "Communication" },
  { href: "/operator/v2/tools", label: "Tools" },
] as const;

const profileFixture = {
  id: "profile-v3",
  lead_id: profileFixtureLeadId,
  profile_version: 3,
  lifecycle_status: "active",
  supersedes_profile_id: "profile-v2",
  current_country: "Austria",
  education: [
    {
      qualification: "Master of Business Administration",
      field_of_study: "Supply Chain Management",
      institution: "AIOS Professional Institute",
      country: "Austria",
      completion_year: 2026,
    },
  ],
  employment: [
    {
      role: "Operations Analyst",
      employer: "Northstar Mobility",
      country: "Austria",
      years: 3.5,
      current: true,
    },
  ],
  years_experience: 3.5,
  skills: ["Operations", "Supply chain", "Project delivery"],
  languages: [
    {
      language: "German",
      level: "B2",
      test_name: "Goethe-Zertifikat",
      test_score: "B2",
    },
  ],
  family: {
    status: "single",
    members: [],
    details_confirmed: true,
  },
  finances: {
    budget_eur: 18000,
    funding_source: "Personal savings",
  },
  goals: [
    {
      domain: "work",
      target_country: "Austria",
      desired_role_or_program: "Supply Chain Specialist",
      target_date: "2027-06-01T00:00:00Z",
      priority: "high",
    },
  ],
  constraints: {
    items: [{ type: "operator_note", value: "Prefer Vienna or Lower Austria" }],
    confirmed: true,
  },
  consent: {
    status: "granted",
    purposes: ["eligibility", "document_processing", "communications"],
    expires_at: "2027-06-30T00:00:00Z",
    recorded_at: "2026-08-10T10:00:00Z",
  },
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

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers, body: "" });
      return;
    }

    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);

    if (url.pathname === "/health") {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok", service: "operator-v2-fixture", environment: "test" }),
      });
      return;
    }

    if (url.pathname === "/api/v1/leads") {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: profileFixtureLeadId,
            full_name: "Alex Morgan",
            email: "alex@example.test",
            phone: null,
            source: "operator-v2-proof",
            intent: "work",
            target_country: "Austria",
            status: "qualified",
            notes: null,
          },
        ]),
      });
      return;
    }

    if (url.pathname === `/api/v1/profiles/leads/${profileFixtureLeadId}/current`) {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify(profileFixture),
      });
      return;
    }

    if (url.pathname === `/api/v1/profiles/leads/${profileFixtureLeadId}/history`) {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify([
          profileFixture,
          {
            ...profileFixture,
            id: "profile-v2",
            profile_version: 2,
            lifecycle_status: "superseded",
            supersedes_profile_id: "profile-v1",
            completeness_score: 84,
            readiness_stage: "review_ready",
            missing_sections: ["employment_reference", "language_evidence"],
            created_at: "2026-07-15T09:00:00Z",
            updated_at: "2026-08-10T08:00:00Z",
          },
        ]),
      });
      return;
    }

    if (url.pathname === `/api/v1/leads/${profileFixtureLeadId}/detail`) {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify({
          lead: {
            id: profileFixtureLeadId,
            full_name: "Alex Morgan",
            target_country: "Austria",
          },
          documents: [
            { id: "doc-passport", lead_id: profileFixtureLeadId, document_type: "passport", filename: "passport.pdf", status: "verified" },
            { id: "doc-degree", lead_id: profileFixtureLeadId, document_type: "degree", filename: "mba-degree.pdf", status: "verified" },
            { id: "doc-language", lead_id: profileFixtureLeadId, document_type: "language_certificate", filename: "german-b2.pdf", status: "reviewed" },
          ],
        }),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Operator V2 acceptance fixture intentionally leaves unrelated governed sources unavailable" }),
    });
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

      for (const item of operatorRoutes) {
        await expect(nav.getByLabel(item.label, { exact: true })).toBeVisible();
      }

      if (route.label === "Profiles") {
        await expect(page.getByRole("heading", { name: "Alex Morgan" })).toBeVisible();
        await expect(page.getByText("92%", { exact: true })).toBeVisible();
        await expect(page.getByText("Version 3", { exact: true })).toBeVisible();
      }

      const geometry = await page.evaluate(() => {
        const root = document.querySelector<HTMLElement>(".aios-v2-root");
        const main = document.querySelector<HTMLElement>("#aios-v2-operator-main");
        if (!root || !main) return null;
        const mainRect = main.getBoundingClientRect();
        return {
          viewport: window.innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          rootWidth: root.scrollWidth,
          mainLeft: mainRect.left,
          mainRight: mainRect.right,
        };
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

      await page.screenshot({
        path: `operator-v2-artifacts/${route.label.toLowerCase()}-${width === 390 ? "phone" : "desktop"}.png`,
        fullPage: true,
      });
    }

    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}
