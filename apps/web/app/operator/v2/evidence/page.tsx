import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import styles from "../operator-v2.module.css";

export default function OperatorEvidenceV2Page() {
  return (
    <V2OperatorShell activeItem="Evidence">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Professional / Operator · Evidence</span>
          <h1>Evidence stays provenance-aware, review-gated, and explicitly separated from conclusions.</h1>
          <p>
            The V2 navigation model now owns evidence discovery. The existing governed document-intelligence workspace remains the single mutation surface until its full shell migration is separately accepted.
          </p>
        </header>

        <section className={styles.primarySection} aria-labelledby="operator-evidence-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Governed source of truth</span>
              <h2 id="operator-evidence-heading">Document intelligence and evidence review</h2>
            </div>
          </div>

          <article className={styles.primaryRow}>
            <div>
              <strong>Documents, extraction, validation, integrity and access controls</strong>
              <p>
                Review provenance, extraction jobs, consistency assessments, fraud-risk signals, expiry and requirement scans, access grants, and secure downloads using the existing governed workflow.
              </p>
            </div>
            <Link href="/document-intelligence">Open governed Evidence workspace</Link>
          </article>
        </section>

        <p className={styles.truthNote}>
          This migration changes navigation and discovery only. Document state, provenance, review decisions, access grants, validation, integrity assessment, persistence, and mutation semantics remain owned by the existing Document Intelligence workspace.
        </p>
      </div>
    </V2OperatorShell>
  );
}
