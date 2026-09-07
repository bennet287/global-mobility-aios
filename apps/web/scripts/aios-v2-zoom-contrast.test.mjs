import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relative) => readFile(new URL(`../${relative}`, import.meta.url), "utf8");
const [tokens, themes, packageJson, workflow, browserProof] = await Promise.all([
  read("styles/v2/tokens.css"),
  read("styles/v2/themes.css"),
  read("package.json"),
  read("../../.github/workflows/v12-production-proof.yml"),
  read("e2e/tests/aios-v2-zoom-contrast.spec.ts"),
]);

function block(source, selector) {
  const selectorIndex = source.indexOf(selector);
  assert.notEqual(selectorIndex, -1, `Missing selector ${selector}`);
  const opening = source.indexOf("{", selectorIndex);
  let depth = 1;
  for (let index = opening + 1; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(opening + 1, index);
  }
  assert.fail(`Unclosed selector ${selector}`);
}

function solidTokens(source) {
  return Object.fromEntries(
    [...source.matchAll(/--aios-v2-color-([a-z-]+):\s*(#[0-9a-fA-F]{6});/g)].map((match) => [match[1], match[2].toLowerCase()]),
  );
}

function luminance(hex) {
  const channels = hex.slice(1).match(/../g).map((channel) => parseInt(channel, 16) / 255);
  return channels
    .map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
    .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
}

function contrast(a, b) {
  const first = luminance(a);
  const second = luminance(b);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

const backgrounds = ["canvas", "canvas-soft", "surface", "surface-raised", "surface-inset"];
const foregrounds = ["text", "text-muted", "text-soft", "accent", "technology", "regulatory", "operations", "security", "success", "warning", "critical", "info"];

function assertPaletteAA(palette, label) {
  for (const foreground of foregrounds) {
    assert.ok(palette[foreground], `${label} missing ${foreground}`);
    for (const background of backgrounds) {
      assert.ok(palette[background], `${label} missing ${background}`);
      const ratio = contrast(palette[foreground], palette[background]);
      assert.ok(ratio >= 4.5, `${label} ${foreground} on ${background} is ${ratio.toFixed(3)}:1`);
    }
  }
}

test("Q14 core dark and light V2 foreground tokens meet AA across V2 surfaces", () => {
  const dark = solidTokens(block(tokens, ".aios-v2-root"));
  const light = solidTokens(block(themes, '.aios-v2-root[data-theme="light"]'));
  assertPaletteAA(dark, "dark");
  assertPaletteAA(light, "light");
});

test("Q14 system-light tokens remain identical to explicit light tokens", () => {
  const corrected = {
    "text-soft": "#6a6962",
    technology: "#406c98",
    regulatory: "#89612c",
    operations: "#397268",
    security: "#5f6599",
    success: "#3b735c",
    warning: "#8e5f24",
    critical: "#a64e48",
    info: "#466c90",
  };
  for (const [name, value] of Object.entries(corrected)) {
    const matches = [...themes.matchAll(new RegExp(`--aios-v2-color-${name}:\\s*${value};`, "g"))];
    assert.equal(matches.length, 2, `${name} must match explicit light and system-light`);
  }
  assert.match(tokens, /--aios-v2-color-text-soft:\s*#84888f;/);
});

test("Q14 browser proof covers 200-percent desktop reflow equivalent and computed contrast", () => {
  assert.match(browserProof, /ZOOM_EQUIVALENT_WIDTH = 640/);
  assert.match(browserProof, /200% browser zoom\/reflow equivalent/);
  assert.match(browserProof, /contrastRatio/);
  assert.match(browserProof, /toBeGreaterThanOrEqual\(4\.5\)/);
  for (const route of ["/cockpit/v2", "/cockpit/v2/organization", "/cockpit/v2/missions", "/cockpit/v2/evidence", "/cockpit/v2/decisions", "/cockpit/v2/history"]) {
    assert.ok(browserProof.includes(`"${route}"`), `Missing zoom route ${route}`);
  }
});

test("Q14 static and Chromium proofs are wired into the existing hardening lane", () => {
  assert.match(packageJson, /scripts\/aios-v2-zoom-contrast\.test\.mjs/);
  assert.match(packageJson, /"test:zoom-contrast"/);
  assert.match(workflow, /tests\/aios-v2-zoom-contrast\.spec\.ts/);
});