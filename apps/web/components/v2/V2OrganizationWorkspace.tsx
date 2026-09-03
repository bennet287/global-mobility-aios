"use client";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import { V2MissionStrip } from "./V2MissionStrip";
import { V2OrganizationBlockout } from "./V2OrganizationBlockout";
import { V2Shell } from "./V2Shell";

export function V2OrganizationWorkspace() {
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();

  return (
    <V2Shell activeItem="Organization" backendOnline={health?.status === "ok"}>
      <div className="aios-v2-content">
        <section className="aios-v2-hero aios-v2-hero-compact" aria-labelledby="aios-v2-organization-title">
          <span className="aios-v2-kicker">Organization · governed spatial view</span>
          <h1 id="aios-v2-organization-title">One organization. Two representations.</h1>
          <p>
            The architectural world and the structured organization below are read-only presentations of the connected Living Organization scene. Selection changes view focus only.
          </p>
        </section>

        {error ? (
          <div className="aios-v2-source-warning" role="alert">
            <div>
              <strong>Organization data could not be loaded.</strong>
              <span>{error}</span>
            </div>
            <button onClick={() => void refresh()} type="button">Retry</button>
          </div>
        ) : null}

        {data?.partial ? (
          <div className="aios-v2-source-warning" role="status">
            <div>
              <strong>Partial organization view.</strong>
              <span>Unavailable: {data.unavailableSources.join(", ")}.</span>
            </div>
          </div>
        ) : null}

        <V2OrganizationBlockout organization={data?.organization || null} loading={loading} />
        <V2MissionStrip missions={data?.missions || []} loading={loading} />

        <section className="aios-v2-structured-fallback" aria-labelledby="aios-v2-structured-title">
          <header className="aios-v2-section-heading">
            <div>
              <span>Accessible equivalent</span>
              <strong id="aios-v2-structured-title">Structured organization</strong>
            </div>
            <small>Available independently of the spatial renderer.</small>
          </header>

          {loading ? (
            <div className="aios-v2-empty-line" role="status">Loading structured organization…</div>
          ) : data?.organization.established ? (
            <div className="aios-v2-structured-grid">
              {data.organization.zones.map((zone) => (
                <section key={zone.wingKey}>
                  <strong>{zone.label}</strong>
                  {zone.departments.length ? (
                    <ul>
                      {zone.departments.map((department) => (
                        <li key={department.key}>
                          <span>{department.label}</span>
                          <small>
                            {department.employeeRosterCount} rostered · {department.workItemCount} work · {department.activeBlockerCount} blockers
                          </small>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No canonical department mapped.</p>
                  )}
                </section>
              ))}
            </div>
          ) : (
            <div className="aios-v2-empty-line" role="status">No structured Living Organization scene is established.</div>
          )}
        </section>
      </div>
    </V2Shell>
  );
}
