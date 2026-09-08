import Link from "next/link";

import { V2OperatorShell } from "../../../../components/v2/V2OperatorShell";
import styles from "../operator-v2.module.css";

export default function OperatorCommunicationV2Page() {
  return (
    <V2OperatorShell activeItem="Communication">
      <div className={styles.page}>
        <header className={styles.header}>
          <span>Professional / Operator · Communication</span>
          <h1>Client communication stays reviewable, governed, and explicitly non-sending in the current MVP.</h1>
          <p>
            The V2 navigation model now owns communication discovery. The existing Communications workspace remains the single governed queue and review surface until its full shell migration is separately accepted.
          </p>
        </header>

        <section className={styles.primarySection} aria-labelledby="operator-communication-heading">
          <div className={styles.sectionHeading}>
            <div>
              <span>Governed source of truth</span>
              <h2 id="operator-communication-heading">Client communication queue</h2>
            </div>
          </div>

          <article className={styles.primaryRow}>
            <div>
              <strong>Draft review and client context</strong>
              <p>
                Filter draft and reviewed communications, inspect the client context, and enter the existing review workflow. Sending remains blocked in the MVP.
              </p>
            </div>
            <Link href="/communications">Open governed Communications workspace</Link>
          </article>
        </section>

        <p className={styles.truthNote}>
          This migration changes navigation and discovery only. Draft content, review state, client context, persistence, approval semantics, and the existing send block remain owned by the Communications workflow.
        </p>
      </div>
    </V2OperatorShell>
  );
}
