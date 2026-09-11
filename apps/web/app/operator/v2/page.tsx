import Link from "next/link";

import { V2OperatorShell } from "../../../components/v2/V2OperatorShell";
import {
  operatorContextualDestinations,
  operatorNavigation,
} from "../../../lib/v2/operator-navigation";
import styles from "./operator-v2.module.css";

const enabledPrimary = operatorNavigation.filter((item) => item.enabled && item.href);
const contextualByHome = operatorContextualDestinations.reduce<Record<string, typeof operatorContextualDestinations>>((groups, item) => {
  const current = groups[item.conceptualHome] || [];
  groups[item.conceptualHome] = [...current, item];
  return groups;
}, {});

const enabledCount = enabledPrimary.length;
const specialistCount = operatorContextualDestinations.length;

export default function OperatorV2MigrationPage() {
  return (
    <V2OperatorShell activeItem="Work">
      <div className={styles.page}>
        <section className={styles.hero} aria-labelledby="operator-home-title">
          <div className={styles.heroCopy}>
            <span className={styles.eyebrow}>Professional operating environment</span>
            <h1 id="operator-home-title">Run mobility work from one governed command surface.</h1>
            <p>
              Move between case work, client context, pathways, evidence, communication, and specialist tools without losing the review gates or authority boundaries that make the underlying workflows trustworthy.
            </p>
            <div className={styles.heroActions}>
              <Link className={styles.primaryAction} href="/">Open current Work Home</Link>
              <Link className={styles.secondaryAction} href="/operator/v2/tools">Browse specialist tools</Link>
            </div>
          </div>

          <aside className={styles.postureCard} aria-label="Operator workspace posture">
            <span>Operating posture</span>
            <strong>Evidence-aware.<br />Human-controlled.</strong>
            <p>No case state, authority outcome, or mutation semantics are changed by this convergence layer.</p>
            <div className={styles.postureMetrics}>
              <div>
                <strong>{enabledCount}</strong>
                <span>primary workspaces</span>
              </div>
              <div>
                <strong>{specialistCount}</strong>
                <span>specialist routes</span>
              </div>
            </div>
          </aside>
        </section>

        <section className={styles.primarySection} aria-labelledby="operator-primary-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Primary workspaces</span>
              <h2 id="operator-primary-heading">The professional operating model</h2>
            </div>
            <p>Work, Profiles, Pathways, Evidence, Communication and Tools remain the six clear homes. Existing governed workflows stay authoritative beneath them.</p>
          </div>

          <div className={styles.primaryGrid}>
            {operatorNavigation.map((item, index) => (
              <article className={styles.primaryCard} key={item.label} data-enabled={item.enabled ? "true" : "false"}>
                <div className={styles.cardTopline}>
                  <span className={styles.cardIndex}>{String(index + 1).padStart(2, "0")}</span>
                  <span className={styles.cardState}>{item.enabled ? "Available" : "Migration pending"}</span>
                </div>
                <div className={styles.cardCopy}>
                  <h3>{item.label}</h3>
                  <p>{item.description}</p>
                </div>
                {item.enabled && item.href ? (
                  <Link href={item.href} aria-label={`Open ${item.label}`}>Enter workspace <span aria-hidden="true">↗</span></Link>
                ) : (
                  <span aria-label={`${item.label} is not yet available as a consolidated workspace`}>Consolidation pending</span>
                )}
              </article>
            ))}
          </div>
        </section>

        <section className={styles.contextSection} aria-labelledby="operator-context-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Specialist capability map</span>
              <h2 id="operator-context-heading">Reach specialist workflows without exposing module topology.</h2>
            </div>
            <p>Capability is grouped by the professional context in which it is used.</p>
          </div>

          <div className={styles.contextGrid}>
            {enabledPrimary.map((home) => {
              const routes = contextualByHome[home.label] || [];
              if (!routes.length) return null;
              return (
                <section className={styles.contextGroup} key={home.label} aria-label={`${home.label} contextual workflows`}>
                  <div className={styles.contextHeading}>
                    <h3>{home.label}</h3>
                    <span>{routes.length} routes</span>
                  </div>
                  <div className={styles.contextLinks}>
                    {routes.map((route) => (
                      <Link href={route.href} key={route.href} title={route.description}>
                        <span>{route.label}</span>
                        <small>{route.description}</small>
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}

            <section className={styles.contextGroup} aria-label="Tools contextual workflows">
              <div className={styles.contextHeading}>
                <h3>Tools</h3>
                <span>{(contextualByHome.Tools || []).length} routes</span>
              </div>
              <div className={styles.contextLinks}>
                {(contextualByHome.Tools || []).map((route) => (
                  <Link href={route.href} key={route.href} title={route.description}>
                    <span>{route.label}</span>
                    <small>{route.description}</small>
                  </Link>
                ))}
              </div>
            </section>
          </div>
        </section>

        <footer className={styles.truthNote}>
          <span>Convergence boundary</span>
          <p>
            This surface changes organization, hierarchy, and discovery only. Existing workflow data and evidence semantics remain unchanged; authority boundaries, review gates and mutation semantics remain unchanged until their individual migration slices are accepted.
          </p>
        </footer>
      </div>
    </V2OperatorShell>
  );
}
