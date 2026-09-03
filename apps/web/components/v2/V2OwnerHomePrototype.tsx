"use client";

import Link from "next/link";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import { V2AttentionList } from "./V2AttentionList";
import { V2MissionStrip } from "./V2MissionStrip";
import { V2OrganizationBlockout } from "./V2OrganizationBlockout";
import { V2RecentChanges } from "./V2RecentChanges";
import { V2Shell } from "./V2Shell";

export function V2OwnerHomePrototype() {
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const backendOnline = health?.status === "ok";

  return (
    <V2Shell activeItem="Home" backendOnline={backendOnline}>
      <div className="aios-v2-content">
        <section className="aios-v2-hero" aria-labelledby="aios-v2-owner-home-title">
          <span className="aios-v2-kicker">Owner Home · canonical integration</span>
          <h1 id="aios-v2-owner-home-title">See what matters. Then inspect the organization behind it.</h1>
          <p>
            AIOS V2 now reads the existing governed Board, Activity, blocker, human-action and Living Organization sources instead of filling the Owner Home with placeholder metrics.
          </p>
        </section>

        {error ? (
          <div className="aios-v2-source-warning" role="alert">
            <div>
              <strong>Owner Home data could not be loaded.</strong>
              <span>{error}</span>
            </div>
            <button onClick={() => void refresh()} type="button">Retry</button>
          </div>
        ) : null}

        {data?.partial ? (
          <div className="aios-v2-source-warning" role="status">
            <div>
              <strong>Partial Owner Home.</strong>
              <span>Unavailable: {data.unavailableSources.join(", ")}.</span>
            </div>
          </div>
        ) : null}

        <section className="aios-v2-situation-grid" aria-label="Owner situation">
          <article className="aios-v2-organization-preview">
            <div className="aios-v2-preview-heading">
              <div>
                <span>Organization</span>
                <strong>Living Organization</strong>
              </div>
              <Link href="/cockpit/v2/organization">Open Organization</Link>
            </div>

            <V2OrganizationBlockout
              compact
              loading={loading}
              organization={data?.organization || null}
            />
          </article>

          <aside className="aios-v2-attention" aria-labelledby="aios-v2-attention-title">
            <header className="aios-v2-attention-heading">
              <div>
                <span>Needs attention</span>
                <strong id="aios-v2-attention-title">Authority & human review</strong>
              </div>
              <small>{data?.attention.length ?? 0} returned</small>
            </header>

            <V2AttentionList items={data?.attention || []} loading={loading} />
          </aside>
        </section>

        <V2MissionStrip missions={data?.missions || []} loading={loading} />
        <V2RecentChanges changes={data?.recentChanges || []} loading={loading} />

        <div className="aios-v2-foundation-note" role="note">
          V2 posture: the architectural topology is a presentation mapping over the existing Living Organization projection. Employee counts are roster counts, not presence claims. Selection changes view focus only and cannot mutate AIOS.
        </div>
      </div>
    </V2Shell>
  );
}
