"use client";

import Link from "next/link";

import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { mobilityNavigation } from "../../lib/v2/mobility-navigation";
import styles from "./MyMobilityV2.module.css";

const journeyStages = [
  { title: "Case", detail: "See where your case stands and what your mobility team is waiting for.", meta: "Current stage · Protected in My Case" },
  { title: "Pathway", detail: "Understand the route being assessed and the status of the guidance behind it.", meta: "Reviewed guidance" },
  { title: "Documents", detail: "Know when evidence or a document request needs your attention.", meta: "Evidence requests · Client-safe surface pending" },
  { title: "Timeline", detail: "Follow meaningful milestones without internal operational noise.", meta: "Client-safe surface pending" },
] as const;

const nextActionGuidance = [
  "Open My Case when you need protected personal records or reviewed case status.",
  "Use this overview for orientation only; it intentionally does not expose private case data.",
  "Documents, Timeline and Messages stay unavailable until their client-safe V2 destinations are accepted.",
] as const;

export default function MyMobilityPage() {
  const { health, error } = useBackendStatus();
  const loadStatus = health?.status === "ok" ? "ready" : error ? "offline" : health ? "partial" : "loading";

  return (
    <WorkspaceShell health={health}>
      <Topbar title="My Mobility" kicker="Mobility User · Case-first experience" loadStatus={loadStatus} onRefresh={() => window.location.reload()} />

      <main className={styles.page}>
        <section className={styles.hero} aria-labelledby="mobility-overview-title">
          <div className={styles.heroCopy}>
            <span className={styles.eyebrow}>Your mobility journey</span>
            <h2 id="mobility-overview-title">Know where your case stands.<br />Know what comes next.</h2>
            <p>
              A clear, privacy-safe starting point for your pathway, evidence, milestones and next actions.
              Protected case records remain inside the secure case workspace.
            </p>
            <div className={styles.heroActions}>
              <Link className={styles.primaryAction} href="/portal">Open My Case</Link>
              <a className={styles.secondaryAction} href="#journey-overview">View journey overview</a>
            </div>
          </div>

          <aside className={styles.privacyCard} aria-label="Protected case access">
            <div className={styles.privacyMark} aria-hidden="true">◈</div>
            <div>
              <span>Protected case access</span>
              <strong>Your personal case records stay private and access-controlled.</strong>
              <p>Personal case details are shown only after secure portal access is established. This page does not infer or expose case facts before secure access is established.</p>
            </div>
          </aside>
        </section>

        <nav className={styles.navStrip} aria-label="My Mobility V2 navigation">
          {mobilityNavigation.map((item) => {
            const active = item.label === "Overview";
            if (item.enabled && item.href) {
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`${styles.navItem} ${active ? styles.navItemActive : ""}`}
                  aria-current={active ? "page" : undefined}
                >
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </Link>
              );
            }
            return (
              <div className={styles.navItemDisabled} key={item.label} aria-disabled="true">
                <strong>{item.label}</strong>
                <small>Migration pending · {item.description}</small>
              </div>
            );
          })}
        </nav>

        <section className={styles.contentGrid} id="journey-overview" aria-label="Mobility overview">
          <article className={styles.journeyPanel}>
            <header className={styles.sectionHead}>
              <div>
                <span className={styles.eyebrow}>Journey overview</span>
                <h3>Only the milestones that matter to you.</h3>
              </div>
              <p>Internal workflow details stay out of this view. The secure workspace remains the source for protected case records.</p>
            </header>

            <div className={styles.stageTrack}>
              {journeyStages.map((stage, index) => (
                <div className={styles.stage} key={stage.title}>
                  <span className={styles.stageIndex} aria-hidden="true">0{index + 1}</span>
                  <div>
                    <strong>{stage.title}</strong>
                    <p>{stage.detail}</p>
                  </div>
                  <span className={styles.stageMeta}>{stage.meta}</span>
                </div>
              ))}
            </div>
          </article>

          <aside className={styles.actionPanel} aria-labelledby="mobility-next-action">
            <div>
              <span className={styles.eyebrow}>Next action</span>
              <h3 id="mobility-next-action">Start with the secure case workspace.</h3>
            </div>
            <p className={styles.actionLead}>
              Use My Case whenever you need personal records, reviewed case status, or a protected request. The overview stays intentionally generic until secure access is established.
            </p>
            <ul className={styles.actionList}>
              {nextActionGuidance.map((item) => <li key={item}>{item}</li>)}
            </ul>
            <Link className={styles.primaryAction} href="/portal">Continue to My Case</Link>
          </aside>
        </section>

        <section className={styles.boundary} aria-label="Mobility user authority boundary">
          <strong>Guidance remains evidence-backed.</strong>
          <span>Your Mobility experience keeps verified guidance, professional review, application control and external-authority decisions clearly separated. This page does not create workflow authority.</span>
        </section>
      </main>
    </WorkspaceShell>
  );
}
