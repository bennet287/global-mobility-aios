import { expect, test } from "@playwright/test";

const ownerRoutes = [
  { href: "/cockpit/v2", label: "Home" },
  { href: "/cockpit/v2/organization", label: "Organization" },
  { href: "/cockpit/v2/missions", label: "Missions" },
  { href: "/cockpit/v2/intelligence", label: "Intelligence" },
  { href: "/cockpit/v2/evidence", label: "Evidence" },
  { href: "/cockpit/v2/decisions", label: "Decisions" },
  { href: "/cockpit/v2/history", label: "History" },
] as const;

async function installReadOnlyFixture(page: import("@playwright/test").Page, writes: string[]) {
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
        body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Q11 fixture intentionally leaves governed sources unavailable" }),
    });
  });
}

for (const width of [1280, 768, 390]) {
  test(`Q11 Owner workspaces reprioritize without page overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });

    const writes: string[] = [];
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installReadOnlyFixture(page, writes);

    for (const route of ownerRoutes) {
      await page.goto(route.href);
      const root = page.locator(".aios-v2-root");
      const ownerNav = page.getByRole("navigation", { name: "Owner" });
      const active = ownerNav.getByLabel(route.label, { exact: true });
      await expect(root).toBeVisible();
      await expect(active).toHaveAttribute("aria-current", "page");

      const geometry = await page.evaluate(() => {
        const root = document.querySelector<HTMLElement>(".aios-v2-root");
        const main = document.querySelector<HTMLElement>(".aios-v2-main");
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

      const guide = page.getByRole("button", { name: "Open guided experience" });
      const command = page.getByRole("button", { name: "Navigate AIOS" });
      await expect(guide).toBeVisible();
      await expect(command).toBeVisible();
      await expect(page.getByLabel("AIOS V2 theme")).toBeVisible();

      if (width <= 600) {
        const guideBox = await guide.boundingBox();
        const commandBox = await command.boundingBox();
        const activeBox = await active.boundingBox();
        const navBox = await ownerNav.boundingBox();
        expect(guideBox?.height ?? 0).toBeGreaterThanOrEqual(44);
        expect(commandBox?.height ?? 0).toBeGreaterThanOrEqual(44);
        expect(activeBox?.height ?? 0).toBeGreaterThanOrEqual(44);
        expect(activeBox?.width ?? 0).toBeGreaterThanOrEqual(44);
        expect(navBox).not.toBeNull();
        expect(activeBox).not.toBeNull();
        expect(activeBox!.x).toBeGreaterThanOrEqual(navBox!.x - 1);
        expect(activeBox!.x + activeBox!.width).toBeLessThanOrEqual(navBox!.x + navBox!.width + 1);

        const navOverflow = await ownerNav.evaluate((nav) => getComputedStyle(nav).overflowX);
        expect(["auto", "scroll"]).toContain(navOverflow);
      }
    }

    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}

test("Q11 phone guide reprioritizes steps as a readable scrollable task rail", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
  const writes: string[] = [];
  await installReadOnlyFixture(page, writes);

  await page.goto("/cockpit/v2");
  await page.getByRole("button", { name: "Open guided experience" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();

  const stepList = dialog.locator("ol");
  await expect(stepList).toBeVisible();
  const stepLayout = await stepList.evaluate((element) => {
    const styles = getComputedStyle(element);
    const items = Array.from(element.children).map((item) => {
      const itemRect = item.getBoundingClientRect();
      const button = item.querySelector<HTMLElement>("button");
      const buttonRect = button?.getBoundingClientRect();
      return {
        itemWidth: itemRect.width,
        buttonWidth: buttonRect?.width ?? 0,
        buttonHeight: buttonRect?.height ?? 0,
      };
    });
    return {
      display: styles.display,
      overflowX: styles.overflowX,
      scrollWidth: element.scrollWidth,
      clientWidth: element.clientWidth,
      items,
    };
  });
  expect(stepLayout.display).toBe("flex");
  expect(["auto", "scroll"]).toContain(stepLayout.overflowX);
  expect(stepLayout.scrollWidth).toBeGreaterThan(stepLayout.clientWidth);
  expect(stepLayout.items).toHaveLength(7);
  for (const item of stepLayout.items) {
    expect(item.itemWidth).toBeGreaterThanOrEqual(150);
    expect(item.buttonWidth).toBeGreaterThanOrEqual(150);
    expect(item.buttonHeight).toBeGreaterThanOrEqual(52);
  }

  const organizationStep = dialog.getByRole("button", { name: /Organization/ });
  await organizationStep.scrollIntoViewIfNeeded();
  await expect(organizationStep).toBeVisible();
  const organizationBox = await organizationStep.boundingBox();
  expect(organizationBox?.width ?? 0).toBeGreaterThanOrEqual(150);

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
});
