import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import { test } from "node:test";
import { ownerNavigation, navigationCommands, filterNavigationCommands } from "../lib/v2/navigation.ts";

test("navigation never offers an unimplemented V2 route as a command", async () => {
  assert.equal(ownerNavigation.length, 7);
  assert.ok(ownerNavigation.every((item) => item.href));
  assert.equal(new Set(navigationCommands.map((item) => item.href)).size, navigationCommands.length);
  for (const command of navigationCommands) {
    assert.ok(command.href.startsWith("/cockpit"));
    await access(new URL(`../app${command.href}/page.tsx`, import.meta.url));
  }
});

test("workspace search matches normalized words across label and context", () => {
  assert.deepEqual(filterNavigationCommands("   "), navigationCommands);
  assert.deepEqual(filterNavigationCommands("  ORGANIZATION   rooms ").map((item) => item.label), ["Organization"]);
  assert.deepEqual(filterNavigationCommands("decisions").map((item) => item.label), ["Decisions", "Decision Explorer"]);
  assert.deepEqual(filterNavigationCommands("no-such-workspace"), []);
  assert.deepEqual(filterNavigationCommands("approve"), []);
});
