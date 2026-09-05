import type { HqWingVisualLayout } from "../../lib/v2/hq-visual-presentation";
import styles from "./V2WingFocusPanel.module.css";

export type V2WingFocusPanelProps = {
  readonly zone: HqWingVisualLayout;
  readonly missionCount: number;
  readonly mode?: "focus" | "detail";
};

function plural(count: number, singular: string, pluralForm = `${singular}s`) {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

export function V2WingFocusPanel({
  zone,
  missionCount,
  mode = "focus",
}: V2WingFocusPanelProps) {
  const detailMode = mode === "detail";
  const hasMappedContent =
    zone.departmentCount > 0 ||
    zone.employeeCount > 0 ||
    zone.workItemCount > 0 ||
    zone.activeBlockerCount > 0 ||
    zone.characters.length > 0 ||
    (zone.isHub && missionCount > 0);

  return (
    <aside
      aria-live="polite"
      className={styles.root}
      data-selected-wing={zone.wingKey}
      data-wing-focus="true"
      data-wing-mode={mode}
    >
      <div className={styles.identity}>
        <span className={styles.eyebrow}>
          {detailMode ? "Wing detail · presentation only" : "Wing focus · presentation only"}
        </span>
        <div className={styles.titleRow}>
          <strong>{zone.label}</strong>
          <span className={styles.focusedBadge}>{detailMode ? "Detail" : "Focused"}</span>
        </div>
        <p>
          {hasMappedContent
            ? detailMode
              ? "This dedicated route presents governed context for this wing. The content is read-only and may not be interpreted as physical presence, location or canonical mutation."
              : "Inspect the governed presentation context for this wing. Selection changes view focus only; it does not navigate or mutate AIOS state."
            : "No canonical department, employee, work or Mission content is mapped to this presentation wing. AIOS will not invent activity or presence."}
        </p>
      </div>

      <dl className={styles.metrics}>
        <div>
          <dt>Departments</dt>
          <dd>{zone.departmentCount}</dd>
        </div>
        <div>
          <dt>Rostered</dt>
          <dd>{zone.employeeCount}</dd>
        </div>
        <div>
          <dt>Work</dt>
          <dd>{zone.workItemCount}</dd>
        </div>
        <div>
          <dt>Blockers</dt>
          <dd>{zone.activeBlockerCount}</dd>
        </div>
        <div>
          <dt>Characters</dt>
          <dd>{zone.characters.length}</dd>
        </div>
        {zone.isHub ? (
          <div>
            <dt>Missions</dt>
            <dd>{missionCount}</dd>
          </div>
        ) : null}
      </dl>

      {zone.characters.length > 0 ? (
        <div className={styles.characters}>
          <span>Placed presentations</span>
          <ul>
            {zone.characters.map((character) => (
              <li key={character.positionKey}>
                <strong>{character.title || character.positionKey}</strong>
                <small>{character.department || "Department unavailable"}</small>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className={styles.emptyLine}>
          {zone.isHub && missionCount > 0
            ? plural(missionCount, "canonical Mission")
            : "No placed character presentations"}
        </div>
      )}

      <div className={styles.truthLine}>
        <span>{detailMode ? "Read-only detail" : "Focus only"}</span>
        <span>No physical presence claimed</span>
        <span>No canonical state written</span>
      </div>
    </aside>
  );
}

export default V2WingFocusPanel;
