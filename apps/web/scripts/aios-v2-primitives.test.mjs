import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire, Module } from "node:module";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

// Render the real TSX with the repository's compiler and React. Only CSS module
// loading is stubbed; interactions, element types and accessible text are real.
const filename = fileURLToPath(new URL("../components/v2/ui/V2Primitives.tsx", import.meta.url));
const require = createRequire(import.meta.url);
const compiled = ts.transpileModule(readFileSync(filename, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true } }).outputText;
const loaded = new Module(filename);
loaded.filename = filename;
loaded.paths = Module._nodeModulePaths(fileURLToPath(new URL("..", import.meta.url)));
loaded.require = (name) => name.endsWith(".module.css") ? { __esModule: true, default: new Proxy({}, { get: (_, key) => String(key) }) } : require(name);
loaded._compile(compiled, filename);
const ui = loaded.exports;
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));

test("read states distinguish unavailable, empty, partial and retained stale records", () => {
  const unavailable = render(ui.V2DataState, { state: { kind: "unavailable", label: "Evidence unavailable", detail: "The source did not respond." } });
  assert.match(unavailable, /role="alert"/); assert.doesNotMatch(unavailable, /No records|Nothing needs/);
  const partial = render(ui.V2DataState, { state: { kind: "partial", label: "Partial view", unavailableSources: ["Board", "Activity"] } });
  assert.match(partial, /Board, Activity/); assert.match(partial, /completeness is unknown/);
  const stale = render(ui.V2DataState, { state: { kind: "stale", label: "Refresh failed", detail: "Prior records retained", lastLoadedAt: null } });
  assert.match(stale, /Last loaded: Not supplied/); assert.match(stale, /may no longer reflect current state/);
  const empty = render(ui.V2DataState, { state: { kind: "empty", label: "No matching records", detail: "Bounded read returned no matches." } });
  assert.match(empty, /data-state="empty"/); assert.match(empty, /Bounded read/);
});

test("loading is announced once and visual skeleton adds no fabricated content", () => {
  const html = render(ui.V2DataState, { state: { kind: "loading", label: "Loading evidence" } });
  assert.match(html, /aria-busy="true"/); assert.match(html, /aria-hidden="true"/); assert.equal((html.match(/role="status"/g) || []).length, 1);
});

test("object rows separate static content, selection and navigation", () => {
  const staticRow = render(ui.V2ObjectRow, { title: "Mission" });
  assert.doesNotMatch(staticRow, /<button|<a\s|aria-pressed/);
  const selection = render(ui.V2ObjectRow, { title: "Mission", onSelect() {}, selected: true, disabled: true });
  assert.match(selection, /type="button"/); assert.match(selection, /aria-pressed="true"/); assert.match(selection, /disabled=""/); assert.doesNotMatch(selection, /href=/);
  const link = render(ui.V2ObjectRow, { title: "Evidence", href: "/cockpit/v2/evidence" });
  assert.match(link, /href="\/cockpit\/v2\/evidence"/); assert.doesNotMatch(link, /aria-pressed|type="submit"/);
});

test("truth and authority labels do not imply permission from their appearance", () => {
  for (const kind of ["canonical", "recommendation", "historical", "memory", "prediction", "simulation", "unsupported"]) {
    const html = render(ui.V2TruthBadge, { kind }); assert.match(html, new RegExp(`data-truth="${kind}"`)); assert.doesNotMatch(html, /button|onclick|Approved/);
  }
  assert.match(render(ui.V2AuthorityBadge, { level: "L2" }), /Recorded authority: L2/);
  assert.match(render(ui.V2AuthorityBadge, { level: "Board", required: true }), /Authority required: Board/);
  assert.match(render(ui.V2StateBadge, { label: "unrecognized_backend_state" }), /unrecognized_backend_state/);
});

test("provenance stays collapsed by default and escapes record text", () => {
  const html = render(ui.V2ProvenanceDisclosure, { children: '<script>alert("test")</script>' });
  assert.match(html, /<details/); assert.match(html, /<summary/); assert.doesNotMatch(html, /open="|<script>/); assert.match(html, /&lt;script&gt;/);
});

test("timestamps never substitute the current time for absent or invalid provenance", () => {
  assert.equal(ui.formatV2Timestamp(null), "Not supplied");
  assert.equal(ui.formatV2Timestamp("bad-date"), "Timestamp unavailable");
  assert.equal(ui.formatV2Timestamp("2026-09-06T10:15:12Z"), "2026-09-06 10:15 UTC");
});

test("headers preserve heading hierarchy and inspector gets a named close control", () => {
  assert.match(render(ui.V2PageHeader, { title: "Missions" }), /<h1>Missions<\/h1>/);
  assert.match(render(ui.V2SectionHeader, { title: "Participants", level: 3 }), /<h3>Participants<\/h3>/);
  const html = render(ui.V2Inspector, { title: "Employee", children: "Recorded state", onClose() {} });
  assert.match(html, /aria-labelledby=/); assert.match(html, /aria-label="Close Employee"/);
});
