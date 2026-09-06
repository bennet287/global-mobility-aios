import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const layout = readFileSync(new URL("../app/cockpit/v2/layout.tsx", import.meta.url), "utf8");
const shell = readFileSync(new URL("../components/v2/V2Shell.tsx", import.meta.url), "utf8");
const control = readFileSync(new URL("../components/v2/V2ThemeControl.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../components/v2/V2ThemeControl.module.css", import.meta.url), "utf8");
const themes = readFileSync(new URL("../styles/v2/themes.css", import.meta.url), "utf8");
const tokens = readFileSync(new URL("../styles/v2/tokens.css", import.meta.url), "utf8");
const hqStyles = readFileSync(new URL("../components/v2/V2LivingHqVisualStage.module.css", import.meta.url), "utf8");

test("Q10 permanently dark HQ owns its foreground and edge palette", () => {
  const stage = hqStyles.match(/\.stageRoot\s*\{([^}]+)\}/)?.[1];
  assert.ok(stage);
  for (const token of ["text", "text-dim", "text-muted", "edge", "edge-strong"]) {
    const value = stage.match(new RegExp(`--hq-${token}:\\s*([^;]+);`))?.[1];
    assert.ok(value, `Missing stage-local ${token}`);
    assert.doesNotMatch(value, /var\(/, `${token} must not inherit the surrounding theme`);
  }
});

test("Q10 keeps themes scoped to AIOS V2", () => {
  assert.match(layout, /styles\/v2\/themes\.css/);
  assert.match(themes, /\.aios-v2-root\[data-theme="light"\]/);
  assert.match(themes, /\.aios-v2-root\[data-theme="system"\]/);
  assert.match(themes, /@media \(prefers-color-scheme: light\)/);
  assert.match(tokens, /\.aios-v2-root \{/);
  assert.doesNotMatch(themes, /html\[data-theme/);
});

test("Q10 offers explicit system, light and dark preferences", () => {
  assert.match(control, /V2ThemePreference = "system" \| "light" \| "dark"/);
  assert.match(control, /option value="system">System/);
  assert.match(control, /option value="light">Light/);
  assert.match(control, /option value="dark">Dark/);
  assert.match(control, /aria-label="AIOS V2 theme"/);
  assert.match(shell, /data-theme=\{themePreference\}/);
});

test("Q10 persists only the presentation preference", () => {
  assert.match(shell, /localStorage\.getItem\(V2_THEME_STORAGE_KEY\)/);
  assert.match(shell, /localStorage\.setItem\(V2_THEME_STORAGE_KEY, next\)/);
  assert.match(control, /aios-v2-theme/);
  assert.doesNotMatch(shell, /\bfetch\s*\(/);
  assert.doesNotMatch(control, /\bfetch\s*\(/);
  assert.doesNotMatch(shell, /method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
});

test("Q10 themes retain semantic colors and accessibility treatments", () => {
  for (const token of ["success", "warning", "critical", "info"]) {
    assert.match(themes, new RegExp(`--aios-v2-color-${token}:`));
  }
  assert.match(styles, /@media \(max-width: 560px\)/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(styles, /@media \(forced-colors: active\)/);
  assert.match(themes, /color-scheme: light/);
  assert.match(themes, /color-scheme: dark/);
});
