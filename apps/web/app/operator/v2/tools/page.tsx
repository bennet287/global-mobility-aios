import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import { operatorContextualDestinations } from "../../../../lib/v2/operator-navigation";
import styles from "./V2OperatorTools.module.css";

const toolRoutes = operatorContextualDestinations.filter((item) => item.conceptualHome === "Tools");

export default function OperatorToolsV2Page() {
  return (
    <V2OperatorShell activeItem="Tools">
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.headerIntro}>
            <span>Professional / Operator · Tools</span>
            <h1>Specialist capability, without turning AIOS into a tool drawer.</h1>
            <p>
              Existing specialist workspaces remain governed by their own data, permissions, review gates, and action semantics. This surface improves discovery and context only.
            </p>
          </div>
          <div className={styles.posture} aria-label="Tools authority posture">
            <span>Authority posture</span>
            <strong>Contextual · governed</strong>
            <p>No capability shown here receives broader permission or mutation authority because it is easier to discover.</p>
          </div>
        </header>

        <section className={styles.contextSection} aria-labelledby="operator-tools-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Existing governed capability</span>
              <h2 id="operator-tools-heading">Specialist workspaces</h2>
            </div>
            <p>Use the narrowest specialist surface that matches the work. Tools support professional judgment; they do not replace authority or evidence.</p>
          </div>

          <div className={styles.toolLedger}>
            {toolRoutes.map((route, index) => (
              <section className={styles.toolRow} key={route.href}>
                <div className={styles.toolIdentity}>
                  <span>{String(index + 1).padStart(2, "0")} · specialist domain</span>
                  <h3>{route.label}</h3>
                </div>
                <p>{route.description}</p>
                <Link href={route.href}>Open workspace</Link>
              </section>
            ))}
          </div>
        </section>

        <div className={styles.truthNote}>
          <span>Truth boundary</span>
          <p>
            Consolidation changes discovery only. Each destination keeps its canonical data, permissions, human-review requirements, and existing action semantics.
          </p>
        </div>
      </div>
    </V2OperatorShell>
  );
}
