import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import styles from "../operator-v2.module.css";

export default function OperatorProfilesV2Page() {
  return (
    <V2OperatorShell activeItem="Profiles">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Professional / Operator · Profiles</span>
          <h1>Mobility profiles stay versioned, evidence-linked, and explicitly operator controlled.</h1>
          <p>
            The V2 navigation model now owns profile discovery. The existing governed profile editor remains the single mutation surface until its full shell migration is separately accepted.
          </p>
        </header>

        <section className={styles.primarySection} aria-labelledby="operator-profiles-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Governed source of truth</span>
              <h2 id="operator-profiles-heading">Universal Mobility Profile workspace</h2>
            </div>
          </div>

          <article className={styles.primaryRow}>
            <div>
              <strong>Profile editor and history</strong>
              <p>
                Select a lead, review completeness and consent, bind evidence, and create a new immutable profile version using the existing governed workflow.
              </p>
            </div>
            <Link href="/profiles">Open governed Profiles workspace</Link>
          </article>
        </section>

        <p className={styles.truthNote}>
          This migration changes navigation and discovery only. Profile versions, consent, evidence links, validation, persistence, and save semantics remain owned by the existing Profiles workspace.
        </p>
      </div>
    </V2OperatorShell>
  );
}
