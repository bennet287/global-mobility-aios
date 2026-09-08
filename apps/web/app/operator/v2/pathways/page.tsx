import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import styles from "../operator-v2.module.css";

export default function OperatorPathwaysV2Page() {
  return (
    <V2OperatorShell activeItem="Pathways">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Professional / Operator · Pathways</span>
          <h1>Pathway discovery moves into V2 while governed versions and publishing stay in one authoritative workflow.</h1>
          <p>
            The V2 navigation model now owns pathway discovery. The existing governed Pathways workspace remains the sole mutation surface until its full shell migration is separately accepted.
          </p>
        </header>

        <section className={styles.primarySection} aria-labelledby="operator-pathways-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Governed source of truth</span>
              <h2 id="operator-pathways-heading">Mobility Pathways workspace</h2>
            </div>
          </div>

          <article className={styles.primaryRow}>
            <div>
              <strong>Catalogue, versions, evidence and regulatory review</strong>
              <p>
                Review pathway criteria, official sources, verified rules, draft versions, publishing state, retirement controls, and regulatory impact review in the existing governed workflow.
              </p>
            </div>
            <Link href="/pathways">Open governed Pathways workspace</Link>
          </article>
        </section>

        <p className={styles.truthNote}>
          This migration changes navigation and discovery only. Pathway creation, versioning, evidence linkage, publish or retire controls, and regulatory-impact review remain owned by the existing Pathways workspace.
        </p>
      </div>
    </V2OperatorShell>
  );
}
