"use client";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { V2Shell } from "./V2Shell";

export function V2OwnerHomePrototype() {
  const { health } = useBackendStatus();
  const backendOnline = health?.status === "ok";

  return (
    <V2Shell backendOnline={backendOnline}>
      <div className="aios-v2-content">
        <section className="aios-v2-hero" aria-labelledby="aios-v2-owner-home-title">
          <span className="aios-v2-kicker">AIOS V2 · Foundation slice</span>
          <h1 id="aios-v2-owner-home-title">A calmer operating system for a living organization.</h1>
          <p>
            This isolated V2 surface establishes the new hierarchy, materials, navigation model, responsive behavior, and truth boundaries before canonical Mission and Living Organization data are connected.
          </p>
        </section>

        <section className="aios-v2-situation-grid" aria-label="Owner situation preview">
          <article className="aios-v2-organization-preview">
            <header className="aios-v2-preview-heading">
              <div>
                <span>Organization</span>
                <strong>Living Organization viewport</strong>
              </div>
            </header>

            <div className="aios-v2-hq-placeholder">
              <div>
                <strong>Architectural HQ integration is intentionally not connected yet.</strong>
                <p>
                  Phase 2 will mount the governed spatial renderer here. This foundation slice does not invent employees, Missions, presence, handoffs, evidence, or authority state.
                </p>
              </div>
            </div>
          </article>

          <aside className="aios-v2-attention" aria-labelledby="aios-v2-attention-title">
            <header className="aios-v2-attention-heading">
              <div>
                <span>Needs attention</span>
                <strong id="aios-v2-attention-title">Owner authority</strong>
              </div>
            </header>

            <div className="aios-v2-attention-empty">
              <strong>No V2 canonical attention feed is connected in this foundation slice.</strong>
              <p>
                The production Owner attention model will read governed Board, HumanActionRequest, blocker, and evidence states instead of using placeholder counts.
              </p>
            </div>
          </aside>
        </section>

        <div className="aios-v2-foundation-note" role="note">
          Foundation posture: design-system preview only. Existing Cockpit and Living Organization remain the operational surfaces until the V2 vertical slice is connected to canonical state and passes accessibility, truth, performance, and visual review.
        </div>
      </div>
    </V2Shell>
  );
}
