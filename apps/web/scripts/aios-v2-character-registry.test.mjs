/**
 * AIOS V2 — Character Presentation Registry tests
 * ================================================
 *
 * Run:  node --test apps/web/scripts/aios-v2-character-registry.test.mjs
 *
 * Presentation-only guard-rail tests for the Phase 2C Character Presentation
 * Registry. These tests verify structure, immutability, presentation-only
 * invariants, resolver precedence and reduced-motion coverage. They never
 * verify canonical organizational truth, because this registry must not
 * contain any.
 *
 * Loading strategy for the TypeScript registry module:
 *   1. Native type stripping (Node >= 22.18 / >= 23.6): direct import.
 *   2. Fallback: transpile with the locally installed `typescript` package
 *      (apps/web devDependency) into a temp .mjs and import that.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..", "..");
const registryPath = path.join(repoRoot, "apps", "web", "lib", "v2", "character-presentation.ts");

const registrySource = readFileSync(registryPath, "utf8");

/* ------------------------------------------------------------------ */
/* Module loading                                                      */
/* ------------------------------------------------------------------ */

const LOAD_ERROR_HINT =
  "Could not load the TypeScript registry module. Node >= 22.18 (native type stripping) or the `typescript` package is required.";

async function importRegistryModule() {
  const registryUrl = pathToFileURL(registryPath).href;
  try {
    return await import(registryUrl);
  } catch (error) {
    const code = error && typeof error === "object" ? error.code : undefined;
    const extensionProblem =
      code === "ERR_UNKNOWN_FILE_EXTENSION" ||
      code === "ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING" ||
      code === "ERR_IMPORT_ATTRIBUTE_MISSING" ||
      (typeof error?.message === "string" && error.message.includes("Unknown file extension"));
    if (!extensionProblem) {
      throw error;
    }
  }
  const require = createRequire(import.meta.url);
  let typescript;
  try {
    typescript = require(path.join(repoRoot, "apps", "web", "node_modules", "typescript"));
  } catch {
    try {
      typescript = require("typescript");
    } catch {
      throw new Error(LOAD_ERROR_HINT, { cause: undefined });
    }
  }
  const transpiled = typescript.transpileModule(registrySource, {
    compilerOptions: {
      module: typescript.ModuleKind.ESNext,
      target: typescript.ScriptTarget.ES2020,
    },
  }).outputText;
  const dir = await mkdtemp(path.join(tmpdir(), "aios-v2-character-registry-"));
  const file = path.join(dir, "character-presentation.transpiled.mjs");
  await writeFile(file, transpiled, "utf8");
  return import(pathToFileURL(file).href + `?t=${Date.now()}`);
}

const mod = await importRegistryModule();
const {
  CHARACTER_PRESENTATION_REGISTRY_CONTRACT,
  CHARACTER_PRESENTATION_INVARIANTS,
  characterPresentationRegistry,
  getCharacterPresentationForPosition,
  getCharacterPresentationForRoleFamily,
  hasExactPositionRegistration,
  getPreferredCharacterPresentation,
  createNeutralPresentationFallback,
} = mod;

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

const FORBIDDEN_KEYS = [
  "workitem",
  "workitemid",
  "workitems",
  "semanticstate",
  "currentsemanticstate",
  "presencestate",
  "currentpresence",
  "reportingline",
  "reportsto",
  "managerof",
  "department",
  "authoritylevel",
  "decisionrights",
];

function collectKeysDeep(value, predicate, seen = new Set(), out = []) {
  if (value === null || typeof value !== "object") {
    return out;
  }
  if (seen.has(value)) {
    return out;
  }
  seen.add(value);
  for (const [key, child] of Object.entries(value)) {
    if (predicate(key)) {
      out.push(key);
    }
    collectKeysDeep(child, predicate, seen, out);
  }
  return out;
}

function isForbiddenKey(key) {
  return FORBIDDEN_KEYS.includes(key.toLowerCase());
}

const allRecords = [
  ...characterPresentationRegistry.records,
  getCharacterPresentationForPosition("definitely-not-a-canonical-position"),
  getCharacterPresentationForRoleFamily("security"),
  createNeutralPresentationFallback("probe"),
];

/* ------------------------------------------------------------------ */
/* Registry structure                                                  */
/* ------------------------------------------------------------------ */

test("registry exposes contract constants with presentation-only flags", () => {
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.registryId, "aios-v2.character-presentation-registry");
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.presentationOnly, true);
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.presenceClaimed, false);
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.canonicalStateWritable, false);
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.semanticActivationPolicy, "capability-declaration-only");
  assert.deepEqual(
    [...CHARACTER_PRESENTATION_REGISTRY_CONTRACT.forbiddenRedefinitions].sort(),
    ["WorkItem", "authority", "canonical role", "department", "presence", "reporting line", "semantic state"],
  );
  assert.equal(CHARACTER_PRESENTATION_INVARIANTS.registryCannotActivateSemanticAnimation, true);
  assert.equal(CHARACTER_PRESENTATION_INVARIANTS.semanticActivationRequiresCanonicalInputsElsewhere, true);
});

test("registry is deeply frozen (no mutation surface)", () => {
  assert.ok(Object.isFrozen(characterPresentationRegistry));
  assert.ok(Object.isFrozen(characterPresentationRegistry.records));
  for (const record of characterPresentationRegistry.records) {
    assert.ok(Object.isFrozen(record), "record must be frozen");
    assert.ok(Object.isFrozen(record.registration), "registration must be frozen");
    assert.ok(Object.isFrozen(record.reducedMotionEquivalent), "reduced-motion record must be frozen");
    for (const behavior of [
      record.idleBehavior, record.workBehavior, record.reviewBehavior, record.waitingBehavior,
      record.blockerBehavior, record.conversationBehavior, record.authorityBehavior,
      record.handoffBehavior, record.completionBehavior,
    ]) {
      assert.ok(Object.isFrozen(behavior), "behavior profile must be frozen");
      assert.ok(Object.isFrozen(behavior.cues), "cues array must be frozen");
    }
    assert.ok(Object.isFrozen(record.accessories));
    assert.ok(Object.isFrozen(record.supportedSemanticAnimationCapabilities));
  }
});

test("registry contains exactly the four hero archetype records with unique animation sets", () => {
  assert.equal(characterPresentationRegistry.records.length, 4);
  const animationSetKeys = characterPresentationRegistry.records.map((r) => r.animationSetKey);
  assert.equal(new Set(animationSetKeys).size, 4);
  for (const key of animationSetKeys) {
    assert.match(key, /^aios-v2:animation-set:/);
  }
});

test("every presentation record carries the complete required schema", () => {
  const requiredFields = [
    "registration", "canonicalPositionKey", "roleFamily", "silhouette", "headShape", "facialLanguage", "hairLanguage",
    "wardrobe", "footwear", "accessories", "signatureObject", "defaultPosture", "gazeBehavior",
    "locomotionPersonality", "idleBehavior", "workBehavior", "reviewBehavior", "waitingBehavior",
    "blockerBehavior", "conversationBehavior", "authorityBehavior", "handoffBehavior",
    "completionBehavior", "reducedMotionEquivalent", "accessibilityDescription", "lodClass",
    "rigClass", "animationSetKey", "supportedSemanticAnimationCapabilities",
    "presentationOnly", "presenceClaimed", "canonicalStateWritable",
  ];
  for (const record of allRecords) {
    for (const field of requiredFields) {
      assert.ok(field in record, `missing required presentation field: ${field}`);
    }
    assert.ok(record.accessibilityDescription.length >= 40, "accessibility description must be substantive");
    assert.ok(Object.keys(record.reducedMotionEquivalent).length >= 3);
  }
});

/* ------------------------------------------------------------------ */
/* Hero archetype registrations                                        */
/* ------------------------------------------------------------------ */

test("CEO exact registry exists with presentation-only exact-position registration", () => {
  const ceo = getCharacterPresentationForPosition("ceo");
  assert.equal(ceo.registration.kind, "exact-position");
  assert.equal(ceo.registration.canonicalPositionKey, "ceo");
  assert.equal(ceo.canonicalPositionKey, "ceo");
  assert.equal(ceo.roleFamily, "executive");
  assert.equal(ceo.wardrobe, "contemporary-tailored-executive");
  assert.equal(ceo.signatureObject, "strategy-briefing-folio");
  assert.equal(ceo.locomotionPersonality, "slower-deliberate");
  assert.ok(hasExactPositionRegistration("ceo"));
  assert.deepEqual([...ceo.supportedSemanticAnimationCapabilities].includes("board-interaction"), true);
  const serialized = JSON.stringify(ceo).toLowerCase();
  assert.ok(!serialized.includes("board approval"), "CEO presentation must not perform Board approval");
});

test("CTO exact registry exists with no generic hoodie stereotype", () => {
  const cto = getCharacterPresentationForPosition("cto");
  assert.equal(cto.registration.kind, "exact-position");
  assert.equal(cto.registration.canonicalPositionKey, "cto");
  assert.equal(cto.canonicalPositionKey, "cto");
  assert.equal(cto.roleFamily, "technology-leadership");
  assert.equal(cto.wardrobe, "architectural-technical-overshirt");
  assert.equal(cto.signatureObject, "system-architecture-tablet");
  assert.ok(hasExactPositionRegistration("cto"));
  assert.ok(!JSON.stringify(cto).toLowerCase().includes("hoodie"));
});

test("regulatory-compliance role-family fallback exists and never claims a canonical position key", () => {
  const record = getCharacterPresentationForRoleFamily("regulatory-compliance");
  assert.equal(record.registration.kind, "role-family-fallback");
  assert.equal(record.registration.roleFamily, "regulatory-compliance");
  assert.equal(record.registration.presentationPositionKey, "role-family:regulatory-compliance");
  assert.equal(record.canonicalPositionKey, null);
  assert.equal(record.roleFamily, "regulatory-compliance");
  assert.equal(record.wardrobe, "evidence-research-attire");
  assert.equal(hasExactPositionRegistration("role-family:regulatory-compliance"), false);
  assert.equal(getCharacterPresentationForPosition("role-family:regulatory-compliance").registration.kind, "neutral-fallback");
});

test("operations role-family fallback exists with practical collaborative presentation", () => {
  const record = getCharacterPresentationForRoleFamily("operations");
  assert.equal(record.registration.kind, "role-family-fallback");
  assert.equal(record.registration.roleFamily, "operations");
  assert.equal(record.registration.presentationPositionKey, "role-family:operations");
  assert.equal(record.canonicalPositionKey, null);
  assert.equal(record.wardrobe, "practical-contemporary-operator");
  assert.ok(record.idleBehavior.cues.includes("local-walking"), "operations idle should show higher local movement frequency");
  assert.ok(record.workBehavior.cues.includes("case-object-carry"));
  assert.equal(hasExactPositionRegistration("role-family:operations"), false);
});

/* ------------------------------------------------------------------ */
/* Presentation-only invariants                                        */
/* ------------------------------------------------------------------ */


test("canonicalPositionKey is explicit: exact records carry the guaranteed key; family and neutral fallbacks carry null", () => {
  for (const record of characterPresentationRegistry.records) {
    if (record.registration.kind === "exact-position") {
      assert.equal(record.canonicalPositionKey, record.registration.canonicalPositionKey);
    } else {
      assert.equal(record.canonicalPositionKey, null);
    }
  }
  assert.equal(getCharacterPresentationForPosition("unknown-canonical-key-probe").canonicalPositionKey, null);
});

test("presentationOnly is always true for every record and fallback", () => {
  for (const record of allRecords) {
    assert.equal(record.presentationOnly, true);
  }
  assert.equal(characterPresentationRegistry.presentationOnly, true);
});

test("presenceClaimed is always false for every record and fallback", () => {
  for (const record of allRecords) {
    assert.equal(record.presenceClaimed, false);
  }
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.presenceClaimed, false);
});

test("canonicalStateWritable is always false for every record and fallback", () => {
  for (const record of allRecords) {
    assert.equal(record.canonicalStateWritable, false);
  }
  assert.equal(CHARACTER_PRESENTATION_REGISTRY_CONTRACT.canonicalStateWritable, false);
});

test("registry does not contain canonical WorkItem data", () => {
  for (const record of allRecords) {
    const keys = collectKeysDeep(record, isForbiddenKey);
    assert.deepEqual(keys.filter((k) => k.toLowerCase().includes("workitem")), []);
    const serialized = JSON.stringify(record);
    assert.ok(!/workitem/i.test(serialized), `no WorkItem data allowed: ${serialized.slice(0, 120)}`);
  }
});

test("registry does not contain current semantic state", () => {
  for (const record of allRecords) {
    const stateKeys = collectKeysDeep(record, (key) =>
      /semanticstate|currentstatus|statestatus|activestate|lifecyclestate/i.test(key),
    );
    assert.deepEqual(stateKeys, []);
  }
});

test("registry does not contain reporting-line truth", () => {
  for (const record of allRecords) {
    const keys = collectKeysDeep(record, isForbiddenKey);
    assert.deepEqual(
      keys.filter((k) => ["reportingline", "reportsto", "managerof"].includes(k.toLowerCase())),
      [],
    );
    assert.ok(!/reports?\s*to\b/i.test(JSON.stringify(record)), "no reporting-line assertions allowed");
  }
});

test("registry does not redefine department, authority level, or presence state fields", () => {
  for (const record of allRecords) {
    const keys = collectKeysDeep(record, isForbiddenKey);
    assert.deepEqual(
      keys.filter((k) => ["department", "authoritylevel", "decisionrights", "presencestate", "currentpresence"].includes(k.toLowerCase())),
      [],
    );
  }
});

test("no Math.random() anywhere in the registry source", () => {
  assert.ok(!registrySource.includes("Math.random"), "registry must be deterministic (no Math.random)");
  assert.ok(!registrySource.includes("Date.now"), "registry must be deterministic (no Date.now)");
});

test("no fake presence state: the only presence-ish key is the presenceClaimed:false flag", () => {
  for (const record of allRecords) {
    const presenceKeys = collectKeysDeep(record, (key) => /presence/i.test(key));
    assert.deepEqual(presenceKeys, ["presenceClaimed"]);
    assert.equal(record.presenceClaimed, false);
  }
});

test("no direct mutation function is exported; exported functions are read-only resolvers", () => {
  const exportedFunctionNames = Object.entries(mod)
    .filter(([, value]) => typeof value === "function")
    .map(([name]) => name);
  assert.deepEqual(
    [...exportedFunctionNames].sort(),
    ["createNeutralPresentationFallback", "getCharacterPresentationForPosition", "getCharacterPresentationForRoleFamily", "getPreferredCharacterPresentation", "hasExactPositionRegistration"].sort(),
  );
  for (const name of exportedFunctionNames) {
    assert.ok(!/set|update|register|mutate|write|patch|apply|commit/i.test(name), `mutation-like export not allowed: ${name}`);
  }
  assert.equal(mod.characterPresentationRegistry.constructor, Object);
});

test("semantic animation capabilities are declared but never activated by this registry", () => {
  for (const record of characterPresentationRegistry.records) {
    for (const capability of record.supportedSemanticAnimationCapabilities) {
      assert.ok(
        ["handoff", "governed-conversation", "blocker-response", "owner-escalation", "board-interaction", "completion"].includes(capability),
      );
    }
  }
  const neutral = getCharacterPresentationForPosition("unknown-neutral-probe");
  assert.deepEqual([...neutral.supportedSemanticAnimationCapabilities], []);
  const triggerWords = ["trigger", "activate", "fire", "dispatch", "emit", "subscribe", "addEventListener", "lifecycle hook"];
  const source = registrySource;
  for (const word of triggerWords) {
    assert.ok(!source.includes(word), `registry must not contain semantic activation machinery: "${word}"`);
  }
});

test("reduced-motion equivalent exists for all registered archetypes and fallbacks", () => {
  for (const record of allRecords) {
    assert.ok(record.reducedMotionEquivalent, "reducedMotionEquivalent required");
    assert.equal(record.reducedMotionEquivalent.mode, "posture-and-state-change-only");
    assert.equal(record.reducedMotionEquivalent.forbidsLongTravelAnimation, true);
    assert.ok(record.reducedMotionEquivalent.summary.length >= 20);
  }
});

/* ------------------------------------------------------------------ */
/* Resolver behavior                                                   */
/* ------------------------------------------------------------------ */

test("unknown position returns a neutral professional fallback without invented truth", () => {
  const fallback = getCharacterPresentationForPosition("definitely-not-a-canonical-position");
  assert.equal(fallback.registration.kind, "neutral-fallback");
  assert.equal(fallback.roleFamily, "neutral-fallback");
  assert.equal(fallback.canonicalPositionKey, null);
  assert.equal(fallback.presentationOnly, true);
  assert.equal(fallback.presenceClaimed, false);
  assert.equal(fallback.canonicalStateWritable, false);
  assert.deepEqual([...fallback.supportedSemanticAnimationCapabilities], []);
  assert.equal(fallback.wardrobe, "neutral-professional-attire");
  assert.ok(Object.isFrozen(fallback));
  const again = getCharacterPresentationForPosition("definitely-not-a-canonical-position");
  assert.deepEqual(again, fallback, "fallback must be deterministic");
});

test("exact position mapping takes precedence over role-family fallback", () => {
  const byPosition = getCharacterPresentationForPosition("ceo");
  assert.equal(byPosition.registration.kind, "exact-position");
  const preferred = getPreferredCharacterPresentation({ positionKey: "ceo", roleFamily: "operations" });
  assert.equal(preferred, byPosition, "exact position must win over role-family fallback");
  assert.equal(hasExactPositionRegistration("ceo"), true);
  const familyOnly = getPreferredCharacterPresentation({ positionKey: "not-guaranteed", roleFamily: "operations" });
  assert.equal(familyOnly.registration.kind, "role-family-fallback");
  assert.equal(familyOnly.registration.roleFamily, "operations");
  const neither = getPreferredCharacterPresentation({ positionKey: null, roleFamily: null });
  assert.equal(neither.registration.kind, "neutral-fallback");
  assert.equal(getCharacterPresentationForPosition("cto"), getCharacterPresentationForPosition("cto"), "exact records are stable references");
});

test("role-family resolver returns registered fallbacks and neutral fallback for unregistered families", () => {
  assert.equal(getCharacterPresentationForRoleFamily("regulatory-compliance").registration.kind, "role-family-fallback");
  assert.equal(getCharacterPresentationForRoleFamily("operations").registration.kind, "role-family-fallback");
  const security = getCharacterPresentationForRoleFamily("security");
  assert.equal(security.registration.kind, "neutral-fallback", "security has no guaranteed registration in this phase");
  const executive = getCharacterPresentationForRoleFamily("executive");
  assert.equal(executive.registration.kind, "neutral-fallback", "no executive family fallback is registered; CEO resolves by exact key only");
});
