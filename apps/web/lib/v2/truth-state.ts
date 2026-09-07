export type V2OwnerSourceKey =
  | "board"
  | "humanActions"
  | "blockers"
  | "activity"
  | "livingOrganization";

export type V2OwnerSourceState = "available" | "unavailable" | "not_established";

export type V2OwnerSourceCoverage = Readonly<Record<V2OwnerSourceKey, V2OwnerSourceState>>;

export type V2CountTruthState = "known" | "partial" | "unavailable" | "not_established";

export type V2CountTruth = Readonly<{
  value: number;
  state: V2CountTruthState;
  affectedSources: readonly string[];
}>;

const SOURCE_LABELS: Readonly<Record<V2OwnerSourceKey, string>> = Object.freeze({
  board: "Board packet",
  humanActions: "Human action requests",
  blockers: "Blockers",
  activity: "Activity",
  livingOrganization: "Living Organization scene",
});

export function deriveV2OwnerSourceCoverage(data: {
  unavailableSources: readonly string[];
  organization: { established: boolean };
}): V2OwnerSourceCoverage {
  const unavailable = new Set(data.unavailableSources);
  const state = (label: string): V2OwnerSourceState => unavailable.has(label) ? "unavailable" : "available";
  const livingOrganization = unavailable.has(SOURCE_LABELS.livingOrganization)
    ? "unavailable"
    : data.organization.established
      ? "available"
      : "not_established";

  return Object.freeze({
    board: state(SOURCE_LABELS.board),
    humanActions: state(SOURCE_LABELS.humanActions),
    blockers: state(SOURCE_LABELS.blockers),
    activity: state(SOURCE_LABELS.activity),
    livingOrganization,
  });
}

export function buildV2CountTruth(
  value: number,
  coverage: V2OwnerSourceCoverage,
  requiredSources: readonly V2OwnerSourceKey[],
): V2CountTruth {
  const unavailable = requiredSources.filter((source) => coverage[source] === "unavailable");
  const notEstablished = requiredSources.filter((source) => coverage[source] === "not_established");
  const availableCount = requiredSources.filter((source) => coverage[source] === "available").length;
  const affectedSources = [...unavailable, ...notEstablished].map((source) => SOURCE_LABELS[source]);

  if (!affectedSources.length) {
    return Object.freeze({ value, state: "known" as const, affectedSources: Object.freeze([]) });
  }

  if (availableCount > 0) {
    return Object.freeze({ value, state: "partial" as const, affectedSources: Object.freeze(affectedSources) });
  }

  if (unavailable.length > 0) {
    return Object.freeze({ value, state: "unavailable" as const, affectedSources: Object.freeze(affectedSources) });
  }

  return Object.freeze({ value, state: "not_established" as const, affectedSources: Object.freeze(affectedSources) });
}

export function formatV2CountTruth(metric: V2CountTruth): string {
  if (metric.state === "known") return String(metric.value);
  if (metric.state === "partial") return metric.value > 0 ? `≥${metric.value}` : "Unknown";
  if (metric.state === "not_established") return "Not established";
  return "Unavailable";
}

export function describeV2CountTruth(metric: V2CountTruth, noun: string): string {
  if (metric.state === "known") return `${metric.value} ${noun} returned from available governed sources.`;
  if (metric.state === "partial") {
    const known = metric.value > 0 ? `At least ${metric.value} ${noun} returned` : `Returned ${noun} may be incomplete`;
    return `${known}; coverage is incomplete for ${metric.affectedSources.join(", ")}.`;
  }
  if (metric.state === "not_established") return `${noun} are not established by ${metric.affectedSources.join(", ")}.`;
  return `${noun} are unavailable because ${metric.affectedSources.join(", ")} could not be read.`;
}
