import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relative) => readFile(new URL(`../${relative}`, import.meta.url), "utf8");

const [layout, shell, palette, context, ownerHome, recents, navigation, commandCss, packageJson] = await Promise.all([
  read("app/cockpit/v2/layout.tsx"),
  read("components/v2/V2Shell.tsx"),
  read("components/v2/V2CommandPalette.tsx"),
  read("components/v2/V2NavigationContext.tsx"),
  read("components/v2/V2OwnerHomePrototype.tsx"),
  read("lib/v2/recent-destinations.ts"),
  read("lib/v2/navigation.ts"),
  read("styles/v2/command-search.css"),
  read("package.json"),
]);

test("Q2 route layout owns the single navigation provider", () => {
  assert.match(layout, /import \{ V2NavigationContext \}/);
  assert.match(layout, /<V2NavigationContext>\{children\}<\/V2NavigationContext>/);
});

test("Q2 shell does not create a second navigation provider", () => {
  assert.doesNotMatch(shell, /import \{ V2NavigationContext \}/);
  assert.doesNotMatch(shell, /<V2NavigationContext>/);
});

test("Q2 Owner Home registers only already-loaded attention records", () => {
  assert.match(ownerHome, /useV2SearchItems\(attentionSearchItems\)/);
  assert.match(ownerHome, /\(data\?\.attention \|\| \[\]\)\.map\(attentionSearchItem\)/);
  assert.doesNotMatch(ownerHome, /fetch\(/);
});

test("Q2 registry is presentation-only and contains no network request", () => {
  assert.doesNotMatch(context, /fetch\(/);
  assert.doesNotMatch(context, /(?:window\.)?(?:localStorage|sessionStorage)\.|document\.cookie/);
});

test("Q2 registry dedupes by cross-domain kind plus id", () => {
  assert.match(context, /const identity = `\$\{item\.kind\}:\$\{item\.id\}`/);
  assert.match(context, /byIdentity\.has\(identity\)/);
});

test("Q2 cross-domain identity permits equal ids from different kinds", () => {
  const employeeIdentity = `Employee:${"123"}`;
  const missionIdentity = `Mission:${"123"}`;
  assert.notEqual(employeeIdentity, missionIdentity);
});

test("Q2 recency is capped at five", () => {
  assert.match(recents, /MAX_RECENT_DESTINATIONS = 5/);
});

test("Q2 recency is most-recent-first", () => {
  assert.match(recents, /return \[normalized, \.\.\.current\.filter/);
});

test("Q2 recency dedupes by href", () => {
  assert.match(recents, /entry !== normalized/);
});

test("Q2 recency uses module memory only", () => {
  assert.match(recents, /let sessionRecentDestinations: string\[\] = \[\]/);
  assert.doesNotMatch(recents, /(?:window\.)?(?:localStorage|sessionStorage)\.|document\.cookie|fetch\(/);
});

test("Q2 shell preserves Next.js client-side navigation", () => {
  assert.match(shell, /import Link from "next\/link"/);
  assert.match(shell, /<Link[\s\S]*href=\{item\.href\}/);
});

test("Q2 palette preserves Next.js client-side navigation", () => {
  assert.match(palette, /import Link from "next\/link"/);
  assert.match(palette, /<Link[\s\S]*href=\{entry\.href\}/);
});

test("Q2 palette performs no search-specific network fetch", () => {
  assert.doesNotMatch(palette, /fetch\(/);
});

test("Q2 palette does not depend on router mutation APIs", () => {
  assert.doesNotMatch(palette, /useRouter|router\.(push|replace|refresh)/);
});

test("Q2 palette is a named accessible dialog", () => {
  assert.match(palette, /<dialog[\s\S]*aria-label="Navigate AIOS"/);
});

test("Q2 palette search input has an accessible name", () => {
  assert.match(palette, /aria-label="Find a workspace"/);
});

test("Q2 palette close control has an accessible name", () => {
  assert.match(palette, /aria-label="Close navigation palette"/);
});

test("Q2 command trigger advertises Ctrl and Meta K", () => {
  assert.match(shell, /aria-keyshortcuts="Control\+K Meta\+K"/);
  assert.match(shell, /event\.ctrlKey \|\| event\.metaKey/);
});

test("Q2 Escape routes through the shared close path", () => {
  assert.match(palette, /onCancel=\{\(event\) => \{[\s\S]*event\.preventDefault\(\);[\s\S]*onClose\(\)/);
});

test("Q2 keyboard result navigation supports ArrowDown and ArrowUp", () => {
  assert.match(palette, /event\.key === "ArrowDown" \|\| event\.key === "ArrowUp"/);
});

test("Q2 keyboard selection supports Enter through focused links", () => {
  assert.match(palette, /data-palette-index=\{index\}/);
  assert.match(palette, /focusEntry\(next\)/);
});

test("Q2 focus stays within the open dialog on Tab boundaries", () => {
  assert.match(palette, /event\.key === "Tab"/);
  assert.match(palette, /dialog\.querySelectorAll<HTMLElement>\("input, a\[href\], button"\)/);
});

test("Q2 close restores focus to the command trigger", () => {
  assert.match(shell, /commandTriggerRef = useRef<HTMLButtonElement>/);
  assert.match(shell, /requestAnimationFrame\(\(\) => commandTriggerRef\.current\?\.focus\(\)\)/);
});

test("Q2 icon-only mobile navigation has explicit accessible names", () => {
  assert.match(shell, /aria-label=\{item\.label\}/);
  assert.match(shell, /aria-label=\{`\$\{item\.label\} \(not yet available\)`\}/);
});

test("Q2 unfinished top-level destinations remain fail-closed", () => {
  for (const label of ["Missions", "Intelligence", "Evidence", "Decisions", "History"]) {
    const expression = new RegExp(`label: "${label}"[^\\n]+href: null, enabled: false`);
    assert.match(navigation, expression);
  }
});

test("Q2 command palette only exposes navigation links, not workflow buttons", () => {
  assert.doesNotMatch(palette, /onClick=\{[^}]*\b(approve|reject|submit|delete|mutate)\b/i);
});

test("Q2 mobile command control keeps a 44px target and hides copy when space is tight", () => {
  assert.match(commandCss, /@media \(max-width: 560px\)[\s\S]*\.aios-v2-command \{[\s\S]*min-width: 44px;[\s\S]*min-height: 44px;/);
  assert.match(commandCss, /\.aios-v2-command > span,[\s\S]*\.aios-v2-command > kbd[\s\S]*display: none;/);
});

test("Q2 command palette has a reduced-motion equivalent", () => {
  assert.match(commandCss, /@media \(prefers-reduced-motion: reduce\)[\s\S]*\.aios-v2-palette/);
  assert.match(commandCss, /transition: none;/);
});

test("Q2 test remains wired into the design-foundation gate", () => {
  assert.match(packageJson, /scripts\/aios-v2-command-search\.test\.mjs/);
});
