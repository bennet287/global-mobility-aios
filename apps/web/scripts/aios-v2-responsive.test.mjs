import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

const layout = read("../app/cockpit/v2/layout.tsx");
const shell = read("../components/v2/V2Shell.tsx");
const responsive = read("../styles/v2/responsive.css");
const primitives = read("../components/v2/ui/V2Primitives.module.css");
const guide = read("../components/v2/V2GuidedExperience.module.css");
const command = read("../styles/v2/command-search.css");
const theme = read("../components/v2/V2ThemeControl.module.css");

const routeStyles = [
  "../components/v2/V2OwnerSituationRoom.module.css",
  "../components/v2/V2MissionsWorkspace.module.css",
  "../components/v2/V2EvidenceWorkspace.module.css",
  "../components/v2/V2IntelligenceWorkspace.module.css",
  "../components/v2/V2DecisionsWorkspace.module.css",
  "../components/v2/V2HistoryWorkspace.module.css",
  "../components/v2/V2OrganizationBlockout.module.css",
].map(read);

test("Q11 loads responsive hardening after the existing V2 presentation layers", () => {
  assert.match(layout, /styles\/v2\/responsive\.css/);
  assert.ok(layout.indexOf("command-search.css") < layout.indexOf("responsive.css"));
});

test("Q11 reprioritizes shell navigation instead of shrinking it", () => {
  for (const width of [1180, 980, 820, 600, 380]) {
    assert.match(responsive, new RegExp(`max-width: ${width}px`));
  }
  assert.match(responsive, /grid-template-columns:\s*repeat\(7, minmax\(44px, 1fr\)\)/);
  assert.match(responsive, /overflow-x:\s*auto/);
  assert.match(responsive, /scroll-snap-type:\s*x proximity/);
  assert.match(responsive, /min-height:\s*48px/);
  assert.doesNotMatch(responsive, /overflow-x:\s*(?:hidden|clip)/);
  assert.doesNotMatch(responsive, /(?:zoom\s*:|transform\s*:\s*scale\()/);

  // Icon-only tablet/phone navigation keeps an accessible route name and
  // centers a clipped active route within its own navigation scroll surface.
  assert.match(shell, /aria-label=\{item\.label\}/);
  assert.match(shell, /aria-label=\{`\$\{item\.label\} \(not yet available\)`\}/);
  assert.match(shell, /matchMedia\("\(max-width: 600px\)"\)/);
  assert.match(shell, /nav\.scrollTo\(\{ left: Math\.max\(0, left\), behavior: "auto" \}\)/);
});

test("Q11 keeps shared controls and primitives touchable at narrow widths", () => {
  assert.match(primitives, /@media \(max-width: 520px\)/);
  assert.match(primitives, /grid-template-columns:\s*minmax\(0, 1fr\)/);
  assert.match(primitives, /\.metricGroup\s*\{\s*grid-template-columns:\s*minmax\(0, 1fr\)/s);
  assert.match(command, /min-width:\s*44px/);
  assert.match(command, /min-height:\s*44px/);
  assert.match(theme, /min-height:\s*44px/);
});

test("Q11 guided experience becomes a readable horizontal task rail on phones", () => {
  assert.match(guide, /@media \(max-width: 520px\)/);
  assert.match(guide, /\.stepList\s*\{[^}]*display:\s*flex[^}]*overflow-x:\s*auto/s);
  assert.match(guide, /\.stepList\s*>\s*li\s*\{[^}]*flex:\s*0 0 154px[^}]*scroll-snap-align:\s*start/s);
  assert.match(guide, /\.stepButton\s*\{[^}]*width:\s*100%[^}]*min-height:\s*52px/s);
  assert.match(guide, /\.stepLabel strong\s*\{[^}]*overflow-wrap:\s*normal[^}]*word-break:\s*normal/s);
  assert.match(guide, /\.contentHeading\s*\{[^}]*flex-direction:\s*column/s);
});

test("Q11 retains route-level reprioritization for every Owner workspace", () => {
  for (const styles of routeStyles) {
    assert.match(styles, /@media \(max-width:/);
  }
  for (const styles of routeStyles.slice(0, 6)) {
    assert.match(styles, /grid-template-columns:\s*(?:minmax\(0, 1fr\)|1fr)/);
  }
});

test("Q11 responsive behavior is presentation-only", () => {
  const presentationFiles = [responsive, primitives, guide].join("\n");
  assert.doesNotMatch(presentationFiles, /\bfetch\s*\(/);
  assert.doesNotMatch(presentationFiles, /method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
  assert.doesNotMatch(presentationFiles, /localStorage|sessionStorage/);
  assert.doesNotMatch(shell, /\bfetch\s*\(/);
  assert.doesNotMatch(shell, /method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
});
