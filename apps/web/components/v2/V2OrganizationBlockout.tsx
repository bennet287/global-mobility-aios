"use client";

import { useMemo, useState } from "react";

import type {
  V2ArchitectureWingKey,
  V2OrganizationOverview,
} from "../../lib/v2/owner-organization";

const WING_ORDER: V2ArchitectureWingKey[] = [
  "executive",
  "regulatory",
  "atrium",
  "technology",
  "operations",
];

export function V2OrganizationBlockout({
  organization,
  loading,
  compact = false,
}: {
  organization: V2OrganizationOverview | null;
  loading: boolean;
  compact?: boolean;
}) {
  const [selectedWing, setSelectedWing] = useState<V2ArchitectureWingKey>("atrium");

  const zones = organization?.zones || [];
  const selected = useMemo(
    () => zones.find((zone) => zone.wingKey === selectedWing) || zones[0] || null,
    [selectedWing, zones],
  );

  const headingId = compact ? "aios-v2-hq-preview-title" : "aios-v2-hq-title";

  return (
    <section
      className={"aios-v2-hq-blockout" + (compact ? " compact" : "")}
      aria-labelledby={headingId}
      data-scene-authoritative={String(organization?.sceneAuthoritative ?? false)}
      data-renderer-authoritative={String(organization?.rendererAuthoritative ?? false)}
      data-mutations-allowed={String(organization?.mutationsAllowed ?? false)}
    >
      <header className="aios-v2-hq-header">
        <div>
          <span>Living Organization</span>
          <strong id={headingId}>Architectural organization blockout</strong>
        </div>
        <small>View focus only · no AIOS mutation</small>
      </header>

      {loading ? (
        <div className="aios-v2-hq-loading" role="status">Loading governed Living Organization scene…</div>
      ) : !organization?.established ? (
        <div className="aios-v2-hq-loading" role="status">
          No Living Organization scene is established. The V2 renderer will not fabricate departments, Missions, employees or presence.
        </div>
      ) : (
        <>
          <div className="aios-v2-hq-canvas" data-presentation-topology="aios-v2-office-bible.v1">
            {WING_ORDER.map((wingKey) => {
              const zone = zones.find((candidate) => candidate.wingKey === wingKey);
              if (!zone) return null;
              const active = selected?.wingKey === wingKey;
              return (
                <button
                  aria-pressed={active}
                  className={"aios-v2-hq-zone zone-" + wingKey}
                  data-active={String(active)}
                  key={wingKey}
                  onClick={() => setSelectedWing(wingKey)}
                  type="button"
                >
                  <span>{zone.label}</span>
                  <strong>{zone.departments.length || "—"}</strong>
                  <small>{zone.departments.length ? "mapped departments" : "presentation zone"}</small>
                  {zone.activeBlockerCount > 0 ? (
                    <em>{zone.activeBlockerCount} blocker{zone.activeBlockerCount === 1 ? "" : "s"}</em>
                  ) : null}
                </button>
              );
            })}

            <div className="aios-v2-hq-mission-hub" aria-label="Mission Hub">
              <span>Mission Hub</span>
              <strong>{organization.missionCount}</strong>
              <small>projected Missions</small>
            </div>
          </div>

          <div className="aios-v2-hq-inspector" aria-live="polite">
            <div>
              <span>View focus</span>
              <strong>{selected?.label || "Organization"}</strong>
            </div>
            {selected ? (
              <>
                <p>
                  {selected.departments.length
                    ? selected.departments.map((department) => department.label).join(" · ")
                    : "No canonical department is mapped to this presentation zone."}
                </p>
                <div className="aios-v2-hq-inspector-metrics">
                  <span><strong>{selected.employeeRosterCount}</strong> rostered positions</span>
                  <span><strong>{selected.workItemCount}</strong> work items</span>
                  <span><strong>{selected.activeBlockerCount}</strong> blockers</span>
                </div>
              </>
            ) : null}
          </div>
        </>
      )}

      <footer className="aios-v2-hq-truth">
        <span>Scene authority: {organization?.sceneAuthoritative ? "authoritative" : "non-authoritative"}</span>
        <span>Renderer authority: {organization?.rendererAuthoritative ? "authoritative" : "none"}</span>
        <span>Mutation: {organization?.mutationsAllowed ? "allowed" : "disabled"}</span>
      </footer>
    </section>
  );
}
