"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { ownerNavigation, type OwnerNavLabel } from "../../lib/v2/navigation";
import { V2Icon } from "./V2Icon";
import styles from "./V2GuidedExperience.module.css";

type GuideCopy = {
  purpose: string;
  lookFor: string;
  truthBoundary: string;
};

const guideCopy: Record<OwnerNavLabel, GuideCopy> = {
  Home: {
    purpose: "Start with the Owner situation room: scan governed attention, Mission condition, organization context and recent Activity before opening details.",
    lookFor: "Use the five-second scan first, then move into the domain that contains the record you need to inspect.",
    truthBoundary: "Counts describe returned governed records. Home does not create authority, completion, urgency or new canonical state.",
  },
  Organization: {
    purpose: "Inspect the Living Organization structure, rostered employees, wings and Mission context without treating the visual world as a presence system.",
    lookFor: "Use wings and inspectors to understand canonical structure and supplied employee or Mission context.",
    truthBoundary: "Roster is not presence. Visual placement, rooms and character presentation do not prove location, travel, conversation or collaboration.",
  },
  Missions: {
    purpose: "Read the full governed Mission portfolio, exact supplied states, blockers, decisions and participants in one workspace.",
    lookFor: "Filter by supplied Mission state, then select a Mission to inspect its canonical basis and linked counts.",
    truthBoundary: "Selection is inspection only. Counts do not imply health, completion, success, urgency or execution authority.",
  },
  Intelligence: {
    purpose: "Read current governed signals beside aggregate organization memory while keeping present-state information separate from historical aggregates.",
    lookFor: "Distinguish current canonical reads from aggregate memory before interpreting any pattern.",
    truthBoundary: "Aggregate memory is visualization-only and is not prediction, current authority, physical movement or a recommendation.",
  },
  Evidence: {
    purpose: "Inspect recorded Evidence references, verified-rule references, source-snapshot references and supplied grounding posture.",
    lookFor: "Open the recorded reference groups and provenance details without reading meaning into reference identifiers alone.",
    truthBoundary: "Reference presence does not prove source content, legal validity, approval, freshness, correctness or evidence quality.",
  },
  Decisions: {
    purpose: "Inspect recorded Executive Decision state, recommendation, authority, owner-action posture and supersession lineage.",
    lookFor: "Keep recommendation, status, recorded authority and required owner action as separate supplied semantics.",
    truthBoundary: "The Board workspace is read-only. It does not approve, reject, execute, complete or infer authority from styling.",
  },
  History: {
    purpose: "Replay recorded semantic Activity, inspect an explicit as-of cursor and compare two backend-proven historical states.",
    lookFor: "Check replay coverage first, then select an Activity cursor; compare only when you need explicit field-level deltas.",
    truthBoundary: "Historical reconstruction is not current state. Cursor comparison does not prove causality, improvement, deterioration, urgency or authority.",
  },
};

export function V2GuidedExperience({
  open,
  activeItem,
  onClose,
}: {
  open: boolean;
  activeItem: OwnerNavLabel;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const steps = useMemo(
    () => ownerNavigation.filter((item) => item.enabled && item.href),
    [],
  );
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!open) return;
    const activeIndex = steps.findIndex((item) => item.label === activeItem);
    setStepIndex(activeIndex >= 0 ? activeIndex : 0);
  }, [activeItem, open, steps]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      requestAnimationFrame(() => closeRef.current?.focus());
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  const onKeyDown = (event: React.KeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Tab") return;
    const dialog = dialogRef.current;
    if (!dialog) return;
    const focusable = Array.from(dialog.querySelectorAll<HTMLElement>("a[href], button:not(:disabled)"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  const step = steps[stepIndex];
  if (!step || !step.href) return null;
  const copy = guideCopy[step.label];
  const isLast = stepIndex === steps.length - 1;

  return (
    <dialog
      aria-labelledby="aios-v2-guide-title"
      className={styles.dialog}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onKeyDown={onKeyDown}
      ref={dialogRef}
    >
      <div className={styles.frame}>
        <header className={styles.header}>
          <div className={styles.headerCopy}>
            <span className={styles.eyebrow}>Owner orientation</span>
            <h2 id="aios-v2-guide-title">Guided experience</h2>
            <p>Learn where to look, what each workspace is for, and which truth boundary must remain intact.</p>
          </div>
          <button className={styles.close} aria-label="Close guided experience" onClick={onClose} ref={closeRef} type="button">
            <V2Icon name="close" width={17} height={17} />
          </button>
        </header>

        <div className={styles.progress} aria-label="Guide progress">
          <span className={styles.progressCopy}>Step {stepIndex + 1} of {steps.length} · {step.label}</span>
          <progress max={steps.length} value={stepIndex + 1}>{stepIndex + 1} of {steps.length}</progress>
        </div>

        <div className={styles.layout}>
          <ol className={styles.stepList} aria-label="Guided workspace sequence">
            {steps.map((item, index) => (
              <li key={item.label}>
                <button
                  className={styles.stepButton}
                  data-current={index === stepIndex ? "true" : "false"}
                  onClick={() => setStepIndex(index)}
                  type="button"
                >
                  <span className={styles.stepNumber}>{index + 1}</span>
                  <span className={styles.stepLabel}>
                    <strong>{item.label}</strong>
                    <small>{item.label === activeItem ? "You are here" : "Workspace"}</small>
                  </span>
                </button>
              </li>
            ))}
          </ol>

          <section className={styles.content} aria-labelledby="aios-v2-guide-step-title">
            <div className={styles.contentHeading}>
              <div className={styles.titleBlock}>
                <span className={styles.contextLabel}>Owner workspace</span>
                <h3 id="aios-v2-guide-step-title">{step.label}</h3>
              </div>
              {step.label === activeItem ? <span className={styles.here}>You are here</span> : null}
            </div>

            <p>{copy.purpose}</p>

            <dl className={styles.factGrid}>
              <div>
                <dt>What to do here</dt>
                <dd>{copy.lookFor}</dd>
              </div>
              <div>
                <dt>Truth boundary</dt>
                <dd>{copy.truthBoundary}</dd>
              </div>
            </dl>

            <div className={styles.actions}>
              <button className={styles.control} disabled={stepIndex === 0} onClick={() => setStepIndex((index) => Math.max(0, index - 1))} type="button">Previous</button>
              <button className={styles.control} onClick={() => isLast ? onClose() : setStepIndex((index) => Math.min(steps.length - 1, index + 1))} type="button">{isLast ? "Finish" : "Next"}</button>
              <Link className={styles.primary} href={step.href} onClick={onClose}>Open {step.label}</Link>
            </div>

            <p className={styles.footerNote}>Guide state is presentation-only. It performs no backend request, records no completion state, and never turns navigation or selection into an operational action.</p>
          </section>
        </div>
      </div>
    </dialog>
  );
}
