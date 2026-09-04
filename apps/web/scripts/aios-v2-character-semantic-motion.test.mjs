/**
 * AIOS V2 - Phase 2E Governed Handoff Motion Descriptor tests
 * ==========================================================
 *
 * Run (repo CI, Node >= 22.18):
 *   node --test apps/web/scripts/aios-v2-character-semantic-motion.test.mjs
 *   (or) node --experimental-strip-types --test scripts/aios-v2-character-semantic-motion.test.mjs
 *
 * Loading strategy for the TypeScript module (mirrors
 * aios-v2-character-registry.test.mjs):
 *   1. Native type stripping (Node >= 22.18 / >= 23.6): direct import.
 *   2. Fallback: transpile with the locally installed `typescript` package
 *      (apps/web devDependency; external temp output, never repo-local).
 *
 * These tests EXECUTE the pure descriptor builder and the real, frozen
 * Character Presentation Registry records (real imports, not regex-only),
 * proving canonical preservation, capability gating, truth boundaries,
 * reduced-motion form, determinism, deep immutability and the absence of
 * any animation-activation machinery.
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
const modulePath = path.join(here, "..", "lib", "v2", "character-semantic-motion.ts");
const registryPath = path.join(here, "..", "lib", "v2", "character-presentation.ts");
const moduleSource = readFileSync(modulePath, "utf8");

/* ------------------------------------------------------------------ */
/* Module loading                                                      */
/* ------------------------------------------------------------------ */

function loadTypeScriptCompiler() {
  const request = createRequire(import.meta.url);
  try {
    return request("typescript");
  } catch {
    // fall through to explicit external entry (sandbox/CI without repo node_modules)
  }
  if (process.env.AIOS_TYPESCRIPT_ENTRY) {
    return request(path.resolve(process.env.AIOS_TYPESCRIPT_ENTRY));
  }
  throw new Error(
    "Could not load the TypeScript descriptor module. Node >= 22.18 (native type stripping) or the `typescript` package (apps/web devDependency, or AIOS_TYPESCRIPT_ENTRY) is required.",
  );
}

async function importTsModule(tsPath) {
  try {
    return await import(pathToFileURL(tsPath).href);
  } catch {
    // Native stripping unavailable (older Node or unknown extension): transpile to a temp dir OUTSIDE the repo.
    const ts = loadTypeScriptCompiler();
    const emitted = ts.transpileModule(readFileSync(tsPath, "utf8"), {
      compilerOptions: {
        target: ts.ScriptTarget.ES2022,
        module: ts.ModuleKind.ESNext,
        esModuleInterop: true,
      },
      fileName: tsPath,
    });
    const tempDir = await mkdtemp(path.join(tmpdir(), "aios-v2-phase2e-"));
    const outPath = path.join(tempDir, path.basename(tsPath).replace(/\.ts$/, ".mjs"));
    await writeFile(outPath, emitted.outputText, "utf8");
    return import(pathToFileURL(outPath).href);
  }
}

const motion = await importTsModule(modulePath);
const registry = await importTsModule(registryPath);

const { buildV2HandoffMotionDescriptor } = motion;

/* ------------------------------------------------------------------ */
/* Fixtures (canonical evidence verbatim from LivingSceneHandoff)      */
/* ------------------------------------------------------------------ */

const CEOT0_CTO_HANDOFF = Object.freeze({
  activity_id: "act-handoff-0001",
  work_item_id: "wi-2481",
  previous_position_key: "ceo",
  assigned_position_key: "cto",
  status: "assigned",
  occurred_at: "2026-09-03T12:00:00.000Z",
  causation_activity_id: "act-decision-0099",
  canonical_basis: "living_scene.handoff:act-handoff-0001",
});

const REGULATORY_TO_OPERATIONS_HANDOFF = Object.freeze({
  activity_id: "act-handoff-0002",
  work_item_id: "wi-2502",
  previous_position_key: "regulatory-intelligence",
  assigned_position_key: "operations-coordinator",
  status: "assigned",
  occurred_at: "2026-09-03T12:05:00.000Z",
  causation_activity_id: null,
  canonical_basis: "living_scene.handoff:act-handoff-0002",
});

/** Mirrors V2CharacterPresentationResolution around a real frozen registry record. */
function resolutionFor(presentation, identity) {
  const registration = presentation.registration;
  const presentationKey =
    registration.kind === "exact-position"
      ? registration.canonicalPositionKey
      : registration.kind === "role-family-fallback"
        ? registration.presentationPositionKey
        : "neutral-professional";
  return Object.freeze({
    identity: Object.freeze({
      positionKey: identity.positionKey,
      title: identity.title,
      department: identity.department,
    }),
    roleFamilyHint: presentation.roleFamily,
    presentationKey,
    resolutionKind: registration.kind,
    resolutionReason: "test fixture constructed around the real frozen registry record",
    presentation,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}

const ceoResolution = resolutionFor(registry.getCharacterPresentationForPosition("ceo"), {
  positionKey: "ceo",
  title: "Chief Executive Officer",
  department: "Executive Leadership",
});
const ctoResolution = resolutionFor(registry.getCharacterPresentationForPosition("cto"), {
  positionKey: "cto",
  title: "Chief Technology Officer",
  department: "Technology",
});
const regulatoryResolution = resolutionFor(
  registry.getCharacterPresentationForRoleFamily("regulatory-compliance"),
  { positionKey: "regulatory-intelligence", title: "Regulatory Intelligence Analyst", department: "Regulatory Compliance" },
);
const operationsResolution = resolutionFor(
  registry.getCharacterPresentationForRoleFamily("operations"),
  { positionKey: "operations-coordinator", title: "Operations Coordinator", department: "Operations" },
);
const neutralSenderResolution = resolutionFor(
  registry.createNeutralPresentationFallback("ceo"),
  { positionKey: "ceo", title: "Chief Executive Officer", department: "Executive Leadership" },
);
const neutralReceiverResolution = resolutionFor(
  registry.createNeutralPresentationFallback("cto"),
  { positionKey: "cto", title: "Chief Technology Officer", department: "Technology" },
);

/* ------------------------------------------------------------------ */
/* Shared assertions helpers                                           */
/* ------------------------------------------------------------------ */

function assertDeeplyFrozen(value, label = "descriptor") {
  if (value === null || typeof value !== "object") return;
  assert.ok(Object.isFrozen(value), `${label} must be frozen`);
  for (const [key, child] of Object.entries(value)) assertDeeplyFrozen(child, `${label}.${key}`);
}

function assertNoValueClaim(descriptor, flagNames) {
  for (const flag of flagNames) {
    assert.equal(descriptor.truth[flag], false, `truth.${flag} must be false`);
    assert.ok(
      Object.getOwnPropertyDescriptor(Object.getPrototypeOf(descriptor.truth) ?? descriptor.truth, flag) === undefined ||
        descriptor.truth[flag] === false,
      `truth.${flag} must never flip`,
    );
  }
}

/* ------------------------------------------------------------------ */
/* 1-2: Supported handoffs (executive + role-family paths)             */
/* ------------------------------------------------------------------ */

test("CEO -> CTO handoff is supported when both presentations declare handoff capability", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.kind, "handoff");
  assert.equal(descriptor.supported, true);
  assert.equal(descriptor.limitation, null);
  assert.equal(descriptor.senderCapabilitySupported, true);
  assert.equal(descriptor.receiverCapabilitySupported, true);
  assert.equal(descriptor.senderPresentationKey, "ceo");
  assert.equal(descriptor.receiverPresentationKey, "cto");
  assert.equal(descriptor.visualMode, "bounded-transfer-emphasis");
  assert.equal(descriptor.semanticAnimationActive, false);
  // The capability declarations come from the REAL frozen registry records:
  assert.ok(ceoResolution.presentation.supportedSemanticAnimationCapabilities.includes("handoff"));
  assert.ok(ctoResolution.presentation.supportedSemanticAnimationCapabilities.includes("handoff"));
});

test("regulatory -> operations role-family handoff is supported when both family presentations declare handoff", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: REGULATORY_TO_OPERATIONS_HANDOFF,
    sender: regulatoryResolution,
    receiver: operationsResolution,
  });
  assert.equal(descriptor.supported, true);
  assert.equal(descriptor.limitation, null);
  assert.equal(descriptor.senderPresentationKey, "role-family:regulatory-compliance");
  assert.equal(descriptor.receiverPresentationKey, "role-family:operations");
  assert.equal(descriptor.semanticAnimationActive, false);
  assert.ok(regulatoryResolution.presentation.supportedSemanticAnimationCapabilities.includes("handoff"));
  assert.ok(operationsResolution.presentation.supportedSemanticAnimationCapabilities.includes("handoff"));
});

/* ------------------------------------------------------------------ */
/* 3-4: Neutral endpoints block semantic handoff animation             */
/* ------------------------------------------------------------------ */

test("neutral sender blocks semantic handoff animation", () => {
  // Real neutral fallback record: zero semantic capabilities.
  assert.deepEqual([...neutralSenderResolution.presentation.supportedSemanticAnimationCapabilities], []);
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: neutralSenderResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.limitation, "sender-presentation-lacks-handoff-capability");
  assert.equal(descriptor.senderCapabilitySupported, false);
  assert.equal(descriptor.receiverCapabilitySupported, true);
  assert.equal(descriptor.semanticAnimationActive, false);
  // Canonical identity is still preserved for the static/reduced forms:
  assert.equal(descriptor.activityId, "act-handoff-0001");
  assert.equal(descriptor.reducedMotion.relation, "ceo -> cto");
});

test("neutral receiver blocks semantic handoff animation", () => {
  assert.deepEqual([...neutralReceiverResolution.presentation.supportedSemanticAnimationCapabilities], []);
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: neutralReceiverResolution,
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.limitation, "receiver-presentation-lacks-handoff-capability");
  assert.equal(descriptor.senderCapabilitySupported, true);
  assert.equal(descriptor.receiverCapabilitySupported, false);
  assert.equal(descriptor.semanticAnimationActive, false);
});

/* ------------------------------------------------------------------ */
/* 5-7: Canonical identifiers / timestamp / basis preserved exactly    */
/* ------------------------------------------------------------------ */

test("canonical handoff identifiers are preserved exactly", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.activityId, "act-handoff-0001");
  assert.equal(descriptor.workItemId, "wi-2481");
  assert.equal(descriptor.fromPositionKey, "ceo");
  assert.equal(descriptor.toPositionKey, "cto");
  assert.equal(descriptor.causationActivityId, "act-decision-0099");
  assert.equal(descriptor.handoffStatus, "assigned");
  const family = buildV2HandoffMotionDescriptor({
    handoff: REGULATORY_TO_OPERATIONS_HANDOFF,
    sender: regulatoryResolution,
    receiver: operationsResolution,
  });
  assert.equal(family.causationActivityId, null);
});

test("occurred_at is preserved exactly and never becomes animation duration", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.occurredAt, "2026-09-03T12:00:00.000Z");
  assert.equal(descriptor.truth.occurredAtIsEventTimeOnly, true);
  assert.equal(descriptor.truth.occurredAtIsAnimationDuration, false);
  // No duration VALUE of any kind exists on the descriptor: duration-named
  // fields may only be explicit boolean false not-claims (never numbers).
  const walk = (value, label) => {
    if (value === null || typeof value !== "object") return;
    for (const [key, child] of Object.entries(value)) {
      if (/duration/i.test(key)) {
        assert.equal(typeof child, "boolean", `duration-named field ${label}.${key} must be a boolean flag`);
        assert.equal(child, false, `duration-named field ${label}.${key} must be an explicit not-claim (false)`);
      } else if (typeof child === "number") {
        assert.ok(!/ms|second|millis|elapsed/i.test(key), `no timing number expected at ${label}.${key}`);
      }
      walk(child, `${label}.${key}`);
    }
  };
  walk(descriptor, "descriptor");
});

test("canonical_basis is preserved exactly", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.canonicalBasis, "living_scene.handoff:act-handoff-0001");
});

/* ------------------------------------------------------------------ */
/* 8-11: Truth boundaries                                              */
/* ------------------------------------------------------------------ */

test("no physical transfer duration, travel, or room traversal claim", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assertNoValueClaim(descriptor, [
    "physicalTransferDurationClaimed",
    "physicalTravelClaimed",
    "roomTraversalClaimed",
  ]);
});

test("no conversation, transcript, or spoken words claim", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assertNoValueClaim(descriptor, ["conversationClaimed", "transcriptClaimed", "spokenWordsClaimed"]);
});

test("no physical presence claim", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assertNoValueClaim(descriptor, ["physicalPresenceClaimed"]);
});

test("no work-completion, dependency-resolution, authority, or approval claim; status stays verbatim", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assertNoValueClaim(descriptor, [
    "workCompletionClaimed",
    "dependencyResolutionClaimed",
    "authorityChangeClaimed",
    "approvalOrRejectionClaimed",
    "handoffStatusIsCompletionClaim",
  ]);
  // Canonical status is echoed, never promoted to completion:
  assert.equal(descriptor.handoffStatus, "assigned");
});

/* ------------------------------------------------------------------ */
/* 12: No canonical mutation surface                                   */
/* ------------------------------------------------------------------ */

test("no canonical mutation surface: frozen in depth and no exported mutation API", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.truth.canonicalStateWritable, false);
  // Strict-mode writes against frozen data throw:
  assert.throws(() => {
    descriptor.supported = false;
  }, TypeError);
  assert.throws(() => {
    descriptor.truth.canonicalStateWritable = true;
  }, TypeError);
  // Module exports no mutation API:
  const exportNames = Object.keys(motion).sort();
  assert.deepEqual(exportNames.filter((name) => typeof motion[name] === "function"), [
    "buildV2HandoffMotionDescriptor",
  ]);
});

/* ------------------------------------------------------------------ */
/* 13: Reduced motion is first-class                                   */
/* ------------------------------------------------------------------ */

test("reduced-motion form is a static sender -> receiver relation with brief emphasis only", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.reducedMotion.mode, "static-relation-brief-emphasis");
  assert.equal(descriptor.reducedMotion.relation, "ceo -> cto");
  assert.equal(descriptor.reducedMotion.fromPositionKey, "ceo");
  assert.equal(descriptor.reducedMotion.toPositionKey, "cto");
  assert.equal(descriptor.reducedMotion.direction, "sender-to-receiver");
  assert.equal(descriptor.reducedMotion.briefEmphasisOnly, true);
  assert.equal(descriptor.reducedMotion.forbidsLongTravelAnimation, true);
  assert.equal(descriptor.reducedMotion.preservesCanonicalIdentity, true);
  // Same canonical identity, even when unsupported (neutral sender):
  const unsupported = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: neutralSenderResolution,
    receiver: ctoResolution,
  });
  assert.equal(unsupported.reducedMotion.mode, "static-relation-brief-emphasis");
  assert.equal(unsupported.reducedMotion.relation, "ceo -> cto");
});

/* ------------------------------------------------------------------ */
/* 14-15: Determinism and deep immutability                            */
/* ------------------------------------------------------------------ */

test("identical inputs produce an identical descriptor (deterministic)", () => {
  const a = buildV2HandoffMotionDescriptor({ handoff: CEOT0_CTO_HANDOFF, sender: ceoResolution, receiver: ctoResolution });
  const b = buildV2HandoffMotionDescriptor({ handoff: CEOT0_CTO_HANDOFF, sender: ceoResolution, receiver: ctoResolution });
  assert.notEqual(a, b); // distinct instances, same truth
  assert.deepEqual(a, b);
  assert.equal(JSON.stringify(a), JSON.stringify(b));
});

test("descriptor and all nested truth/reduced-motion structures are deeply frozen", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.ok(Object.isFrozen(descriptor));
  assert.ok(Object.isFrozen(descriptor.truth));
  assert.ok(Object.isFrozen(descriptor.reducedMotion));
  assertDeeplyFrozen(descriptor);
});

/* ------------------------------------------------------------------ */
/* 16: No activation machinery (executable + structural)               */
/* ------------------------------------------------------------------ */

test("module contains no random/time/timer/network/renderer activation machinery", () => {
  // Executable behavior: the descriptor carries no functions and never activates.
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  const walkForFunctions = (value, label) => {
    assert.notEqual(typeof value, "function", `${label} must not be a function`);
    if (value !== null && typeof value === "object") {
      for (const [key, child] of Object.entries(value)) walkForFunctions(child, `${label}.${key}`);
    }
  };
  walkForFunctions(descriptor, "descriptor");
  assert.equal(descriptor.semanticAnimationActive, false);

  // Structural: comment-stripped source must not contain forbidden machinery.
  const stripped = moduleSource
    .replace(/\/\*[\s\S]*?\*\//g, " ")
    .replace(/^[^'"`]*\/\/.*$/gm, " ");
  const forbidden = [
    /Math\.random/, /Date\.now/, /new\s+Date\b/,
    /\bsetTimeout\b/, /\bsetInterval\b/, /\bsetImmediate\b/, /requestAnimationFrame/,
    /addEventListener/, /removeEventListener/,
    /\bfetch\b/, /XMLHttpRequest/, /\bWebSocket\b/,
    /\bwindow\b/, /\bdocument\b/, /\bglobalThis\b/, /localStorage|sessionStorage|indexedDB/,
    /from\s+["']react["']/, /from\s+["']react-dom["']/, /\.css\b/, /\.scss\b/,
    /\brequire\s*\(/, /\bimport\s*\(/, /\bprocess\.(?:env|exit|cwd)\b/,
    /\b(?:POST|PUT|PATCH|DELETE)\b/,
  ];
  for (const pattern of forbidden) {
    assert.doesNotMatch(stripped, pattern, `forbidden machinery pattern matched: ${pattern}`);
  }
  // Every import in the pure module is a type-only import (no runtime coupling):
  const importLines = moduleSource.match(/^import[^\n]*$/gm) ?? [];
  assert.ok(importLines.length > 0, "expected type-only imports for canonical shapes");
  for (const line of importLines) {
    assert.match(line, /^import type /, `non-type import found in pure module: ${line}`);
  }
});

/* ------------------------------------------------------------------ */
/* Bonus: incomplete/missing canonical input is deterministically gated */
/* ------------------------------------------------------------------ */

test("missing or incomplete canonical handoff yields unsupported descriptor, never an inference", () => {
  const missing = buildV2HandoffMotionDescriptor({ handoff: null, sender: ceoResolution, receiver: ctoResolution });
  assert.equal(missing.supported, false);
  assert.equal(missing.limitation, "canonical-handoff-record-missing-or-incomplete");
  assert.equal(missing.truth.canonicalEvent, false);
  assert.equal(missing.truth.canonicalEventSource, "none");
  assert.equal(missing.semanticAnimationActive, false);

  const incomplete = buildV2HandoffMotionDescriptor({
    handoff: { ...CEOT0_CTO_HANDOFF, occurred_at: "" },
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(incomplete.supported, false);
  assert.equal(incomplete.limitation, "canonical-handoff-record-missing-or-incomplete");
  assert.equal(incomplete.occurredAt, "");
});


/* ------------------------------------------------------------------ */
/* Independent review hardening: canonical endpoint binding            */
/* ------------------------------------------------------------------ */

test("handoff support requires sender and receiver identities to match canonical endpoints", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: ctoResolution,
    receiver: ceoResolution,
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.senderIdentityMatchesCanonicalHandoff, false);
  assert.equal(descriptor.receiverIdentityMatchesCanonicalHandoff, false);
  assert.equal(descriptor.limitation, "sender-and-receiver-presentation-identities-mismatch");
  assert.equal(descriptor.semanticAnimationActive, false);
});

test("a wrong sender presentation is rejected even when both presentations declare handoff capability", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: CEOT0_CTO_HANDOFF,
    sender: operationsResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.senderIdentityMatchesCanonicalHandoff, false);
  assert.equal(descriptor.receiverIdentityMatchesCanonicalHandoff, true);
  assert.equal(descriptor.limitation, "sender-presentation-identity-mismatch");
  assert.equal(descriptor.senderCapabilitySupported, true);
  assert.equal(descriptor.receiverCapabilitySupported, true);
});

test("empty canonical handoff status is incomplete and cannot authorize semantic motion", () => {
  const descriptor = buildV2HandoffMotionDescriptor({
    handoff: { ...CEOT0_CTO_HANDOFF, status: "" },
    sender: ceoResolution,
    receiver: ctoResolution,
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.truth.canonicalEvent, false);
  assert.equal(descriptor.limitation, "canonical-handoff-record-missing-or-incomplete");
  assert.equal(descriptor.semanticAnimationActive, false);
});
