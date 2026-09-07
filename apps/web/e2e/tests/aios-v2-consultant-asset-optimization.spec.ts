import { expect, test, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const PROFILE_DIR = join(process.cwd(), "asset-results");
const PROFILE_PATH = join(PROFILE_DIR, "aios-v2-consultant-assets.json");

type ResourceSnapshot = {
  resourceCount: number;
  transferBytes: number;
  encodedBodyBytes: number;
  decodedBodyBytes: number;
  scriptCount: number;
  scriptTransferBytes: number;
  scriptEncodedBodyBytes: number;
  scriptDecodedBodyBytes: number;
  scriptUrls: string[];
};

async function installReadOnlyFixture(page: Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
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

    if (new URL(request.url()).pathname === "/health") {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok", service: "q18-fixture", environment: "test" }),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Q18 frozen fixture leaves unrelated governed sources unavailable" }),
    });
  });
}

async function resourceSnapshot(page: Page): Promise<ResourceSnapshot> {
  return page.evaluate(() => {
    const resources = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
    const scripts = resources.filter((entry) => entry.initiatorType === "script" || entry.name.includes("/_next/static/chunks/"));
    const sum = (entries: PerformanceResourceTiming[], key: "transferSize" | "encodedBodySize" | "decodedBodySize") =>
      entries.reduce((total, entry) => total + (Number.isFinite(entry[key]) ? entry[key] : 0), 0);

    return {
      resourceCount: resources.length,
      transferBytes: sum(resources, "transferSize"),
      encodedBodyBytes: sum(resources, "encodedBodySize"),
      decodedBodyBytes: sum(resources, "decodedBodySize"),
      scriptCount: scripts.length,
      scriptTransferBytes: sum(scripts, "transferSize"),
      scriptEncodedBodyBytes: sum(scripts, "encodedBodySize"),
      scriptDecodedBodyBytes: sum(scripts, "decodedBodySize"),
      scriptUrls: scripts.map((entry) => entry.name).sort(),
    };
  });
}

function writeProfile(profile: unknown) {
  mkdirSync(PROFILE_DIR, { recursive: true });
  writeFileSync(PROFILE_PATH, `${JSON.stringify(profile, null, 2)}\n`, "utf8");
}

test("Q18 closed consultant is intent-lazy and records the actual activation asset delta", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installReadOnlyFixture(page, writes);

  await page.goto("/cockpit/v2");
  const openButton = page.getByRole("button", { name: "Open consultant chat" });
  await expect(openButton).toBeVisible();
  await expect(page.getByText("In-House Consultant", { exact: true })).toHaveCount(0);

  const before = await resourceSnapshot(page);
  await openButton.click();

  await expect(page.getByText("In-House Consultant", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Close consultant chat" })).toBeVisible();
  await expect(page.getByPlaceholder("Ask the consultant...")).toBeVisible();

  const after = await resourceSnapshot(page);
  const beforeScripts = new Set(before.scriptUrls);
  const newScriptUrls = after.scriptUrls.filter((url) => !beforeScripts.has(url));
  const delta = {
    resourceCount: after.resourceCount - before.resourceCount,
    transferBytes: after.transferBytes - before.transferBytes,
    encodedBodyBytes: after.encodedBodyBytes - before.encodedBodyBytes,
    decodedBodyBytes: after.decodedBodyBytes - before.decodedBodyBytes,
    scriptCount: after.scriptCount - before.scriptCount,
    scriptTransferBytes: after.scriptTransferBytes - before.scriptTransferBytes,
    scriptEncodedBodyBytes: after.scriptEncodedBodyBytes - before.scriptEncodedBodyBytes,
    scriptDecodedBodyBytes: after.scriptDecodedBodyBytes - before.scriptDecodedBodyBytes,
    newScriptUrls,
  };

  expect(newScriptUrls.length).toBeGreaterThan(0);
  expect(delta.scriptCount).toBeGreaterThan(0);
  expect(delta.scriptTransferBytes > 0 || delta.scriptEncodedBodyBytes > 0).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);

  writeProfile({
    contractVersion: "aios-v2-consultant-assets.v1",
    generatedAt: new Date().toISOString(),
    route: "/cockpit/v2",
    measurementPosture: "production-build Chromium resource timing; one CI/device sample",
    hardBudgetsEnforced: false,
    truth: {
      consultantLoadsAfterExplicitUserIntent: true,
      transferValuesAreBrowserResourceTimingObservations: true,
      universalProductSavingsClaimed: false,
    },
    beforeActivation: before,
    afterActivation: after,
    activationDelta: delta,
    writes,
    pageErrors,
  });
});

test("Q18 client-facing routes do not load or expose the global consultant launcher", async ({ page }) => {
  const writes: string[] = [];
  const scriptRequests: string[] = [];
  page.on("request", (request) => {
    if (request.resourceType() === "script") scriptRequests.push(request.url());
  });
  await installReadOnlyFixture(page, writes);

  await page.goto("/portal");
  await expect(page.getByRole("button", { name: /consultant chat/i })).toHaveCount(0);
  await expect(page.getByText("In-House Consultant", { exact: true })).toHaveCount(0);
  expect(writes).toEqual([]);
  expect(scriptRequests.length).toBeGreaterThan(0);
});
