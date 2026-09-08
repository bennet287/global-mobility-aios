import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import { operatorContextualDestinations } from "../../../../lib/v2/operator-navigation";
import styles from "../operator-v2.module.css";

const toolRoutes = operatorContextualDestinations.filter((item) => item.conceptualHome === "Tools");

export default function OperatorToolsV2Page() {
  return (
    <V2OperatorShell activeItem="Tools">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Professional / Operator · Tools</span>
          <h1>Specialist tools stay governed, contextual, and explicitly human-controlled.</h1>
          <p>
            This workspace consolidates existing specialist destinations without changing their authority, data sources, review gates, or mutation behavior.
          </p>
        </header>

        <section className={styles.contextSection} aria-labelledby="operator-tools-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Existing governed capability</span>
              <h2 id="operator-tools-heading">Specialist workspaces</h2>
            </div>
          </div>

          <div className={styles.contextGrid}>
            {toolRoutes.map((route) => (
              <section className={styles.contextGroup} key={route.href}>
                <h3>{route.label}</h3>
                <p>{route.description}</p>
                <div>
                  <Link href={route.href}>Open governed workspace</Link>
                </div>
              </section>
            ))}
          </div>
        </section>

        <p className={styles.truthNote}>
          Consolidation changes discovery only. Each specialist route keeps its existing canonical data, permissions, review requirements, and action semantics.
        </p>
      </div>
    </V2OperatorShell>
  );
}
