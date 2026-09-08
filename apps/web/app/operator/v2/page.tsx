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

export default function OperatorV2MigrationPage() {
  return (
    <V2OperatorShell activeItem="Work">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Phase 10 · Professional / Operator migration</span>
          <h1>One professional workspace, organized by work rather than module topology.</h1>
          <p>
            This migration shell establishes the accepted Work, Profiles, Pathways, Evidence, Communication and Tools mental model while the existing governed workflows remain authoritative and reachable.
          </p>
        </header>

        <section className={styles.primarySection} aria-labelledby="operator-primary-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Primary destinations</span>
              <h2 id="operator-primary-heading">The six-domain professional model</h2>
            </div>
            <Link className={styles.liveWorkLink} href="/">Open current Work Home</Link>
          </div>

          <div className={styles.primaryList}>
            {operatorNavigation.map((item) => (
              <article className={styles.primaryRow} key={item.label} data-enabled={item.enabled ? "true" : "false"}>
                <div>
                  <strong>{item.label}</strong>
                  <p>{item.description}</p>
                </div>
                {item.enabled && item.href ? (
                  <Link href={item.href}>Open</Link>
                ) : (
                  <span aria-label={`${item.label} is not yet available as a consolidated workspace`}>Migration pending</span>
                )}
              </article>
            ))}
          </div>
        </section>

        <section className={styles.contextSection} aria-labelledby="operator-context-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Contextual capability</span>
              <h2 id="operator-context-heading">Existing specialist workflows remain reachable.</h2>
            </div>
          </div>

          <div className={styles.contextGrid}>
            {enabledPrimary.map((home) => {
              const routes = contextualByHome[home.label] || [];
              if (!routes.length) return null;
              return (
                <section className={styles.contextGroup} key={home.label} aria-label={`${home.label} contextual workflows`}>
                  <h3>{home.label}</h3>
                  <div>
                    {routes.map((route) => (
                      <Link href={route.href} key={route.href} title={route.description}>
                        {route.label}
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}

            <section className={styles.contextGroup} aria-label="Tools contextual workflows">
              <h3>Tools</h3>
              <div>
                {(contextualByHome.Tools || []).map((route) => (
                  <Link href={route.href} key={route.href} title={route.description}>
                    {route.label}
                  </Link>
                ))}
              </div>
            </section>
          </div>
        </section>

        <p className={styles.truthNote}>
          Navigation changes organization and discovery only. Existing workflow data, authority boundaries, review gates and mutation semantics remain unchanged until their individual migration slices are accepted.
        </p>
      </div>
    </V2OperatorShell>
  );
}
