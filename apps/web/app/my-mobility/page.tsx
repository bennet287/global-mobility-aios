"use client";

import Link from "next/link";

import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";

const mobilityAreas = [
  { title: "Case", detail: "See where your case stands and what your mobility team is waiting for.", meta: "Current stage" },
  { title: "Pathway", detail: "Understand the route being assessed and the status of the guidance behind it.", meta: "Pathway status" },
  { title: "Documents", detail: "Review document requests, evidence status, and items that still need your attention.", meta: "Evidence requests" },
  { title: "Timeline", detail: "Follow the milestones that matter to your journey without internal workflow noise.", meta: "Milestones" },
  { title: "Next actions", detail: "Know what to provide, review, sign, or wait for next.", meta: "Your tasks" },
  { title: "Communication", detail: "Keep important messages connected to your governed mobility case.", meta: "Case messages" },
] as const;

export default function MyMobilityPage() {
  const { health, error } = useBackendStatus();
  const loadStatus = health?.status === "ok" ? "ready" : error ? "offline" : health ? "partial" : "loading";

  return (
    <WorkspaceShell health={health}>
      <Topbar title="My Mobility" kicker="Mobility User · Case-first experience" loadStatus={loadStatus} onRefresh={() => window.location.reload()} />

      <section className="experience-hero mobility-experience-hero">
        <div>
          <span className="eyebrow">Your mobility journey</span>
          <h2>Know where your case stands.<br />Know what comes next.</h2>
          <p>Track your pathway, documents, milestones, requests, and messages in one clear place, while sensitive case data remains protected behind secure access.</p>
          <div className="experience-actions"><Link className="button primary" href="/portal">Open secure case workspace</Link></div>
        </div>
        <aside className="experience-principle-card">
          <span>Protected case access</span>
          <strong>Your case records stay private and access-controlled.</strong>
          <p>Personal case details are shown only after secure portal access is established. This overview never exposes case records on its own.</p>
        </aside>
      </section>

      <section className="experience-section-heading">
        <div><span className="eyebrow">Your journey at a glance</span><h3>Case, pathway, evidence, timeline, action.</h3></div>
        <p>Use the secure case workspace when you are ready to view personal records, upload evidence, or respond to a request.</p>
      </section>

      <section className="experience-module-grid mobility-module-grid" aria-label="My Mobility areas">
        {mobilityAreas.map(({ title, detail, meta }) => (
          <article className="experience-module-card static" key={title}><span>My Mobility</span><strong>{title}</strong><p>{detail}</p><small>{meta}</small></article>
        ))}
      </section>

      <section className="experience-boundary-strip" aria-label="Mobility user authority boundary">
        <strong>Guidance remains evidence-backed.</strong>
        <span>Your workspace keeps verified guidance, professional review, application control, and external-authority decisions clearly separated.</span>
      </section>
    </WorkspaceShell>
  );
}
