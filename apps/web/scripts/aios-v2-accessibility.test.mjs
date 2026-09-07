import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relative) => readFile(new URL(`../${relative}`, import.meta.url), "utf8");

const [shell, palette, situation, primitives, responsive, guided, theme, packageJson] = await Promise.all([
  read("components/v2/V2Shell.tsx"),
  read("components/v2/V2CommandPalette.tsx"),
  read("components/v2/V2OwnerSituationRoom.tsx"),
  read("components/v2/ui/V2Primitives.tsx"),
  read("styles/v2/responsive.css"),
  read("components/v2/V2GuidedExperience.tsx"),
  read("components/v2/V2ThemeControl.tsx"),
  read("package.json"),
]);

test("Q12 Search / Command visible label is present in its accessible name", () => {
  assert.match(shell, /aria-label="Search \/ Command"[\s\S]*<span>Search \/ Command<\/span>/);
  assert.doesNotMatch(shell, /aria-label="Navigate AIOS"[\s\S]*<span>Search \/ Command<\/span>/);
});

test("Q12 preserves native navigation semantics for command results", () => {
  assert.match(palette, /<nav className="aios-v2-palette-list" aria-label="Navigation results">/);
  assert.match(palette, /<Link[\s\S]*href=\{entry\.href\}/);
  assert.doesNotMatch(palette, /role="listbox"|role="option"|aria-selected=/);
});

test("Q12 Owner Home exposes a coherent h1 to h2 hierarchy", () => {
  assert.match(situation, /<h1 id="aios-v2-owner-home-title">/);
  for (const id of [
    "aios-v2-attention-title",
    "aios-v2-situation-missions-title",
    "aios-v2-situation-organization-title",
    "aios-v2-situation-activity-title",
  ]) {
    assert.match(situation, new RegExp(`<h2 id="${id}">`));
  }
  assert.doesNotMatch(situation, /<strong id="aios-v2-(?:attention|situation)/);
});

test("Q12 shared page and section primitives use structural headings", () => {
  assert.match(primitives, /<h1>\{title\}<\/h1>/);
  assert.match(primitives, /const Heading = level === 3 \? "h3" : "h2"/);
});

test("Q12 shell exposes one primary main target and current-page navigation", () => {
  assert.equal((shell.match(/<main\b/g) || []).length, 1);
  assert.match(shell, /<main className="aios-v2-main" id="aios-v2-main">/);
  assert.match(shell, /<nav className="aios-v2-nav" aria-label="Owner"/);
  assert.match(shell, /aria-current=\{active \? "page" : undefined\}/);
  assert.match(shell, /href="#aios-v2-main">Skip to main content<\/a>/);
});

test("Q12 keyboard focus remains visibly perceivable including forced colors", () => {
  assert.match(responsive, /:where\(a\[href\], button, input, select, textarea, summary\):focus-visible/);
  assert.match(responsive, /outline: 2px solid var\(--aios-v2-color-accent\)/);
  assert.match(responsive, /@media \(forced-colors: active\)[\s\S]*outline-color: Highlight/);
});

test("Q12 phone Owner rail retains touch targets and focus-safe scroll padding", () => {
  assert.match(responsive, /@media \(max-width: 600px\)[\s\S]*overflow-x: auto/);
  assert.match(responsive, /scroll-padding-inline: 8px/);
  assert.match(responsive, /min-width: 48px;[\s\S]*min-height: 48px/);
});

test("Q12 dialogs retain Escape handling and trigger focus restoration", () => {
  assert.match(palette, /onCancel=\{\(event\) => \{[\s\S]*onClose\(\)/);
  assert.match(guided, /onCancel=\{\(event\) => \{[\s\S]*onClose\(\)/);
  assert.match(shell, /commandTriggerRef\.current\?\.focus\(\)/);
  assert.match(shell, /guideTriggerRef\.current\?\.focus\(\)/);
});

test("Q12 keeps native labeled theme control and no accessibility interaction mutates AIOS", () => {
  assert.match(theme, /<label className=\{styles\.control\}/);
  assert.match(theme, /<select[\s\S]*aria-label="AIOS V2 theme"/);
  for (const source of [shell, palette, guided, theme]) {
    assert.doesNotMatch(source, /method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
  }
});

test("Q12 accessibility regression remains wired into design-foundation", () => {
  assert.match(packageJson, /scripts\/aios-v2-accessibility\.test\.mjs/);
  assert.match(packageJson, /"test:accessibility"/);
});
