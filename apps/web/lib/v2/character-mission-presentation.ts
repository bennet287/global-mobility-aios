import {
  type CharacterPresentationRecord,
  type CharacterRoleFamily,
  getPreferredCharacterPresentation,
} from "./character-presentation";

export type V2CharacterPresentationIdentity = {
  positionKey: string;
  title: string;
  department: string;
};

export type V2CharacterPresentationResolution = {
  identity: V2CharacterPresentationIdentity;
  roleFamilyHint: CharacterRoleFamily | null;
  presentationKey: string;
  resolutionKind: CharacterPresentationRecord["registration"]["kind"];
  resolutionReason: string;
  presentation: CharacterPresentationRecord;
  presentationOnly: true;
  presenceClaimed: false;
  canonicalStateWritable: false;
  semanticAnimationActive: false;
};

type PresentationFamilyRule = {
  family: CharacterRoleFamily;
  pattern: RegExp;
};

const PRESENTATION_FAMILY_RULES: readonly PresentationFamilyRule[] = Object.freeze([
  Object.freeze({
    family: "regulatory-compliance",
    pattern: /(regulat|compliance|policy|legal|evidence|eligibility|visa|document)/i,
  }),
  Object.freeze({
    family: "operations",
    pattern: /(operations?|coordination|mobility|client|case|service|delivery|recruit)/i,
  }),
  Object.freeze({
    family: "security",
    pattern: /(security|ciso|soc|cyber|risk)/i,
  }),
  Object.freeze({
    family: "technology-leadership",
    pattern: /(technology|technical|engineering|platform|systems?|product|architecture|cto)/i,
  }),
  Object.freeze({
    family: "executive",
    pattern: /(executive|chief|board|strategy|ceo|cfo|coo)/i,
  }),
]);

function normalizeIdentity(input: V2CharacterPresentationIdentity): string {
  return [input.positionKey, input.title, input.department]
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean)
    .join(" ");
}

/**
 * Presentation-only family hint.
 *
 * This is deliberately not canonical organization classification. The hint is
 * used only after canonical identity fields have already been supplied by the
 * Living Organization scene, and it can only select reusable visual metadata.
 */
export function inferV2CharacterRoleFamily(
  input: V2CharacterPresentationIdentity,
): CharacterRoleFamily | null {
  const normalized = normalizeIdentity(input);
  for (const rule of PRESENTATION_FAMILY_RULES) {
    if (rule.pattern.test(normalized)) return rule.family;
  }
  return null;
}

function presentationKeyFor(record: CharacterPresentationRecord): string {
  if (record.registration.kind === "exact-position") {
    return record.registration.canonicalPositionKey;
  }
  if (record.registration.kind === "role-family-fallback") {
    return record.registration.presentationPositionKey;
  }
  return "neutral-professional";
}

function resolutionReason(
  record: CharacterPresentationRecord,
  roleFamilyHint: CharacterRoleFamily | null,
): string {
  if (record.registration.kind === "exact-position") {
    return "Exact canonical position matched a registered character presentation.";
  }
  if (record.registration.kind === "role-family-fallback") {
    return "Canonical employee identity selected a reusable presentation-only role-family fallback.";
  }
  if (roleFamilyHint) {
    return "No registered exact or family presentation exists for this employee; neutral presentation is used.";
  }
  return "No supported presentation family was inferred; neutral presentation is used.";
}

export function resolveV2CharacterPresentation(
  input: V2CharacterPresentationIdentity,
): V2CharacterPresentationResolution {
  const identity = Object.freeze({
    positionKey: input.positionKey,
    title: input.title,
    department: input.department,
  });
  const roleFamilyHint = inferV2CharacterRoleFamily(identity);
  const presentation = getPreferredCharacterPresentation({
    positionKey: identity.positionKey,
    roleFamily: roleFamilyHint,
  });

  return Object.freeze({
    identity,
    roleFamilyHint,
    presentationKey: presentationKeyFor(presentation),
    resolutionKind: presentation.registration.kind,
    resolutionReason: resolutionReason(presentation, roleFamilyHint),
    presentation,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}
