import { expect, test } from "@playwright/test";

for (const width of [1280, 390]) test(`Q10 themes stay presentation-only and responsive at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const headers = {
      "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000",
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers, body: "" });
      return;
    }
    if (request.method() !== "GET") writes.push(request.method());
    if (new URL(request.url()).pathname === "/health") {
      await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }) });
      return;
    }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Fixture source intentionally unavailable" }) });
  });

  await page.goto("/cockpit/v2");
  const root = page.locator(".aios-v2-root");
  const control = page.getByLabel("AIOS V2 theme");
  const canvas = () => root.evaluate((element) => getComputedStyle(element).getPropertyValue("--aios-v2-color-canvas").trim());

  await expect(root).toHaveAttribute("data-theme", "system");
  await expect(control).toHaveValue("system");
  expect(await canvas()).toBe("#f3f0e9");

  await control.selectOption("dark");
  await expect(root).toHaveAttribute("data-theme", "dark");
  expect(await canvas()).toBe("#0d1014");
  expect(await page.evaluate(() => window.localStorage.getItem("aios-v2-theme"))).toBe("dark");

  await page.reload();
  await expect(root).toHaveAttribute("data-theme", "dark");
  await expect(control).toHaveValue("dark");
  expect(await canvas()).toBe("#0d1014");

  await control.selectOption("light");
  await expect(root).toHaveAttribute("data-theme", "light");
  expect(await canvas()).toBe("#f3f0e9");

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByRole("region", { name: "Living HQ visual stage", exact: true });
  await expect(stage).toHaveAttribute("data-state", "unestablished");
  const heading = stage.getByText("No Living Organization scene is established.", { exact: true });
  await expect(heading).toBeVisible();

  const stagePalette = () => stage.evaluate((element) => {
    const styles = getComputedStyle(element);
    const rgb = (value: string): number[] => value.startsWith("#")
      ? value.slice(1).match(/../g)!.map((channel) => parseInt(channel, 16))
      : value.match(/[\d.]+/g)!.slice(0, 3).map(Number);
    const luminance = (channels: number[]) => channels.map((channel) => {
      const value = channel / 255;
      return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
    // Conservative backdrop: brightest base plus both atmospheric highlights
    // and the stage's white sheen at their maximum opacity simultaneously.
    let backdrop = rgb(styles.getPropertyValue("--hq-bg-1").trim());
    for (const [red, green, blue, alpha] of [[201, 163, 106, 0.055], [122, 162, 214, 0.07], [255, 255, 255, 0.025]]) {
      backdrop = backdrop.map((channel, index) => channel * (1 - alpha) + [red, green, blue][index] * alpha);
    }
    const colors = ["strong", "small"].map((selector) => getComputedStyle(element.querySelector(selector)!).color);
    return {
      colors,
      background: styles.backgroundImage,
      border: styles.borderTopColor,
      contrast: colors.map((color) => (luminance(rgb(color)) + 0.05) / (luminance(backdrop) + 0.05)),
    };
  });

  for (const preference of ["light", "dark"] as const) {
    await control.selectOption(preference);
    await expect(root).toHaveAttribute("data-theme", preference);
    await expect(heading).toHaveCSS("color", "rgb(231, 234, 241)");
    const palette = await stagePalette();
    for (const contrast of palette.contrast) expect(contrast).toBeGreaterThanOrEqual(4.5);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  }
  const darkPalette = await stagePalette();
  await control.selectOption("light");
  await expect(root).toHaveAttribute("data-theme", "light");
  expect(await stagePalette()).toEqual(darkPalette);

  await control.selectOption("system");
  await expect(root).toHaveAttribute("data-theme", "system");
  expect(await canvas()).toBe("#f3f0e9");

  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  expect(await canvas()).toBe("#0d1014");

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
