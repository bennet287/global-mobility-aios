import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const guide = readFileSync(new URL("../components/v2/V2GuidedExperience.tsx", import.meta.url), "utf8");
const shell = readFileSync(new URL("../components/v2/V2Shell.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../components/v2/V2GuidedExperience.module.css", import.meta.url), "utf8");

const domains = ["Home", "Organization", "Missions", "Intelligence", "Evidence", "Decisions", "History"];

test("Q9 guide covers the seven accepted Owner workspaces", () => {
  for (const domain of domains) assert.match(guide, new RegExp(`${domain}: \\{`));
  assert.match(guide, /ownerNavigation\.filter\(\(item\) => item\.enabled && item\.href\)/);
  assert.match(guide, /Step \{stepIndex \+ 1\} of \{steps\.length\}/);
  assert.match(guide, /Open \{step\.label\}/);
});

test("Q9 guide keeps navigation, truth and action semantics separate", () => {
  assert.match(guide, /Roster is not presence/);
  assert.match(guide, /Aggregate memory is visualization-only and is not prediction/);
  assert.match(guide, /Reference presence does not prove source content/);
  assert.match(guide, /does not approve, reject, execute, complete/);
  assert.match(guide, /Historical reconstruction is not current state/);
  assert.match(guide, /performs no backend request, records no completion state/);
  assert.doesNotMatch(guide, /\bfetch\s*\(/);
  assert.doesNotMatch(guide, /method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
  assert.doesNotMatch(guide, /localStorage|sessionStorage/);
});

test("Q9 guide is explicit, dismissible and does not auto-open", () => {
  assert.match(shell, /const \[guideOpen, setGuideOpen\] = useState\(false\)/);
  assert.match(shell, /aria-label="Open guided experience"/);
  assert.match(shell, /<V2GuidedExperience activeItem=\{activeItem\} open=\{guideOpen\} onClose=\{closeGuide\} \/>/);
  assert.match(guide, /dialog\.showModal\(\)/);
  assert.match(guide, /onCancel=\{\(event\) =>/);
  assert.match(guide, /Close guided experience/);
});

test("Q9 guide has responsive and accessibility treatments", () => {
  assert.match(styles, /@media \(max-width: 720px\)/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(styles, /@media \(forced-colors: active\)/);
  assert.match(guide, /aria-labelledby="aios-v2-guide-title"/);
  assert.match(guide, /aria-label="Guided workspace sequence"/);
  assert.match(guide, /event\.key !== "Tab"/);
});
