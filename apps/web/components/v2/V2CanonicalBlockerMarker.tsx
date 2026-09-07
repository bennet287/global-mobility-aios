import type { ReactNode } from "react";

import type { V2VisibleBlockerSummary } from "../../lib/v2/visible-blocker";
import styles from "./V2CanonicalBlockerMarker.module.css";

export function V2CanonicalBlockerMarker({
  summary,
  children,
}: {
  readonly summary: V2VisibleBlockerSummary;
  readonly children: ReactNode;
}) {
  const single = summary.single;
  const accessibleLabel = single
    ? `Canonical blocker ${single.title}. Severity ${single.severity}. Type ${single.blockerType}. Status ${single.status}.`
    : `${summary.count} canonical blockers linked to this employee. Open Employee Inspector for exact blocker records.`;

  return (
    <span
      aria-label={accessibleLabel}
      className={styles.root}
      data-aios-v2-blocker="canonical"
      data-blocker-count={String(summary.count)}
      data-blocker-details-claimed="true"
      data-blocker-resolution-claimed="false"
      data-causal-block-claimed="false"
      data-physical-location-claimed="false"
      data-physical-presence-claimed="false"
      data-single-blocker-id={single?.blockerId ?? ""}
      role="group"
      title={accessibleLabel}
    >
      {children}
      <span aria-hidden="true" className={styles.marker}>
        <span className={styles.glyph}>!</span>
        <span className={styles.label}>
          {single ? single.severity.toUpperCase() : `${summary.count} BLOCKERS`}
        </span>
      </span>
    </span>
  );
}
