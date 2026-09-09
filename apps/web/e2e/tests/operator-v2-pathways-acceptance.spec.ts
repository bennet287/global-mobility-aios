import { expect, test } from "@playwright/test";

test.describe("Operator V2 real Pathways workspace", () => {
  for (const width of [1280, 390]) {
    test(`real /pathways route remains truthful and bounded at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
      await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });

      const writes: string[] = [];
      const pageErrors: string[] = [];
      page.on("pageerror", (error) => pageErrors.push(error.message));

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
            body: JSON.stringify({ status: "ok", service: "operator-v2-pathways-fixture", environment: "test" }),
          });
          return;
        }

        await route.fulfill({
          status: 503,
          headers,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Pathways proof intentionally leaves governed catalogue sources unavailable" }),
        });
      });

      await page.goto("/pathways");

      const root = page.locator(".aios-v2-root");
      const main = page.locator("#aios-v2-operator-main");
      const nav = page.getByRole("navigation", { name: "Professional / Operator" });
      const active = nav.getByLabel("Pathways", { exact: true });

      await expect(root).toBeVisible();
      await expect(main).toBeVisible();
      await expect(active).toHaveAttribute("aria-current", "page");
      await expect(active).toHaveAttribute("href", "/pathways");
      await expect(page.getByText("Mobility routes", { exact: true })).toBeVisible();
      await expect(page.getByText("Source-to-pathway evidence chain", { exact: true })).toBeVisible();
      await expect(page.getByText("Regulatory impact queue", { exact: true })).toBeVisible();
      await expect(page.getByText("Pathway operation blocked", { exact: true })).toBeVisible();

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
        path: `operator-v2-artifacts/pathways-real-${width === 390 ? "phone" : "desktop"}.png`,
        fullPage: true,
      });

      expect(writes).toEqual([]);
      expect(pageErrors).toEqual([]);
    });
  }
});
