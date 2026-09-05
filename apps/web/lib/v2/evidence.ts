import { listOfficialSources, listSourceSnapshots, listVerifiedRules } from "../api";

export async function loadV2Evidence() {
  const [rules, sources, snapshots] = await Promise.allSettled([
    listVerifiedRules({ limit: 100 }), listOfficialSources(), listSourceSnapshots({ limit: 100 }),
  ]);
  return {
    rules: rules.status === "fulfilled" ? rules.value.verified_rules : [],
    sources: sources.status === "fulfilled" ? sources.value.sources : [],
    snapshots: snapshots.status === "fulfilled" ? snapshots.value.snapshots : [],
    unavailable: [rules.status === "rejected" ? "Verified rules" : null, sources.status === "rejected" ? "Official sources" : null, snapshots.status === "rejected" ? "Source snapshots" : null].filter((value): value is string => value !== null),
  };
}
