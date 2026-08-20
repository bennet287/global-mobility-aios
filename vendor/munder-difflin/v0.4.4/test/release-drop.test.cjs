'use strict';

/**
 * Release drops render REMOTE, AUTHOR-CONTROLLED HTML inside the app. The
 * renderer it would otherwise reach has `window.cth` bridged onto it — spawnPty,
 * writeFileText, updateConfig — so script execution there is arbitrary code
 * execution with the app's authority, available to anyone who can publish a
 * release.
 *
 * The controls are (1) `sandbox=""` on the iframe and (2) `default-src 'none'`
 * in the document's own CSP. This file pins the half that lives in shared code.
 * The sandbox attribute is asserted in ReleaseDrop.tsx and is deliberately NOT
 * the only thing standing between a release body and the user's machine.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const loadTs = require('./load-ts.cjs');

const { extractDropHtml, buildDropSrcDoc } = loadTs('src/shared/releaseDrop.ts');

const wrap = (inner) => `# Release\n\nblurb\n\n<!-- drop -->\n${inner}\n<!-- /drop -->\n\nfooter`;

test('extracts the authored block and leaves the surrounding markdown behind', () => {
  const html = extractDropHtml(wrap('<h1>Hello</h1>'));
  assert.equal(html, '<h1>Hello</h1>');
});

test('a release body with no drop block returns null (digest path stays default)', () => {
  assert.equal(extractDropHtml('## What\'s new\n\n- a bullet'), null);
  assert.equal(extractDropHtml(''), null);
  assert.equal(extractDropHtml(null), null);
  assert.equal(extractDropHtml(undefined), null);
});

test('an unbalanced marker pair returns null rather than half a document', () => {
  assert.equal(extractDropHtml('intro <!-- drop --> <h1>truncated'), null);
  assert.equal(extractDropHtml('intro <!-- /drop --> trailing'), null);
});

test('an empty drop block is treated as no drop', () => {
  assert.equal(extractDropHtml(wrap('   \n  ')), null);
});

test('the CSP denies scripts by omission, not by an allowlist that could widen', () => {
  const doc = buildDropSrcDoc('<h1>hi</h1>');
  // Match the CSP meta specifically — a bare /content="…"/ picks up the
  // viewport tag, which precedes it.
  const csp = /http-equiv="Content-Security-Policy"\s+content="([^"]+)"/.exec(doc);
  assert.ok(csp, 'a CSP meta tag is present');
  const policy = csp[1];
  assert.match(policy, /default-src 'none'/);
  // The point of default-src 'none': an unlisted directive DENIES. If someone
  // ever adds an explicit script-src, this catches it.
  assert.doesNotMatch(policy, /script-src/);
  assert.doesNotMatch(policy, /connect-src/);
  assert.doesNotMatch(policy, /'unsafe-eval'/);
  // Media a launch page genuinely needs, https/data only — never http:.
  assert.match(policy, /img-src https: data: blob:/);
  assert.match(policy, /media-src https: data: blob:/);
  assert.doesNotMatch(policy, /img-src[^;]*\bhttp:/);
});

test('defence in depth: script tags and inline handlers are stripped from the body', () => {
  const doc = buildDropSrcDoc([
    '<h1>Launch</h1>',
    '<script>window.parent.cth.spawnPty({})</script>',
    '<script src="https://evil.example/x.js"></script>',
    '<img src="x.png" onerror="window.parent.cth.writeFileText(\'/tmp/x\',\'y\')">',
    '<div ONCLICK=steal()>click</div>'
  ].join('\n'));
  assert.doesNotMatch(doc, /<script/i);
  assert.doesNotMatch(doc, /onerror/i);
  assert.doesNotMatch(doc, /onclick/i);
  // …while the legitimate content around them survives intact.
  assert.match(doc, /<h1>Launch<\/h1>/);
  assert.match(doc, /<img src="x\.png"/);
});

test('authored markup that merely LOOKS active is preserved', () => {
  // A drop describing the update mechanism shouldn't have its prose mangled.
  const doc = buildDropSrcDoc('<p>We removed the old <code>onclick</code> handler.</p>');
  assert.match(doc, /<code>onclick<\/code>/);
});

test('the document is self-contained and declares its charset before content', () => {
  const doc = buildDropSrcDoc('<h1>é — 🎉</h1>');
  assert.match(doc, /^<!doctype html>/i);
  assert.ok(doc.indexOf('charset') < doc.indexOf('<body'), 'charset precedes the body');
  assert.match(doc, /🎉/);
});
