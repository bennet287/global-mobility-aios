import Link from "next/link";
import { useId, type ReactNode } from "react";
import styles from "./V2Primitives.module.css";

export type V2SurfaceKind = "base" | "raised" | "inset" | "floating" | "authority";
export type V2Tone = "neutral" | "info" | "success" | "warning" | "critical";
export type V2TruthKind = "canonical" | "recommendation" | "historical" | "memory" | "prediction" | "simulation" | "unsupported";
const truthLabels: Record<V2TruthKind, string> = {
  canonical: "Canonical record", recommendation: "Recommendation", historical: "Historical reconstruction",
  memory: "Aggregate memory", prediction: "Prediction", simulation: "Simulation", unsupported: "Unsupported",
};

export function V2Surface({ children, kind = "base", label, className = "" }: { children: ReactNode; kind?: V2SurfaceKind; label?: string; className?: string }) {
  return <div className={`${styles.surface} ${className}`} data-surface={kind} aria-label={label}>{children}</div>;
}

export function V2PageHeader({ title, description, eyebrow, actions }: { title: string; description?: string; eyebrow?: string; actions?: ReactNode }) {
  return <header className={styles.pageHeader}><div>{eyebrow ? <span className={styles.eyebrow}>{eyebrow}</span> : null}<h1>{title}</h1>{description ? <p>{description}</p> : null}</div>{actions ? <div className={styles.actions}>{actions}</div> : null}</header>;
}

export function V2SectionHeader({ title, description, eyebrow, actions, id, level = 2 }: { title: string; description?: string; eyebrow?: string; actions?: ReactNode; id?: string; level?: 2 | 3 }) {
  const Heading = level === 3 ? "h3" : "h2";
  return <header className={styles.sectionHeader}><div>{eyebrow ? <span className={styles.eyebrow}>{eyebrow}</span> : null}<Heading id={id}>{title}</Heading>{description ? <p>{description}</p> : null}</div>{actions ? <div className={styles.actions}>{actions}</div> : null}</header>;
}

/** Labels come from the caller's typed projection. Styling never infers authority or completion. */
export function V2StateBadge({ label, tone = "neutral" }: { label: string; tone?: V2Tone }) {
  return <span className={styles.badge} data-tone={tone}>{label}</span>;
}
export function V2TruthBadge({ kind }: { kind: V2TruthKind }) {
  return <span className={styles.truth} data-truth={kind}>{truthLabels[kind]}</span>;
}
export function V2AuthorityBadge({ level, required = false }: { level: string; required?: boolean }) {
  return <span className={styles.authority} data-authority-required={required}>{required ? "Authority required" : "Recorded authority"}: {level || "Not supplied"}</span>;
}

type RowContent = { title: string; description?: string; leading?: ReactNode; trailing?: ReactNode };
type RowInteraction = { href: string; onSelect?: never; selected?: never; disabled?: never } | { href?: never; onSelect: () => void; selected?: boolean; disabled?: boolean } | { href?: never; onSelect?: never; selected?: never; disabled?: never };
export function V2ObjectRow(props: RowContent & RowInteraction) {
  const body = <>{props.leading ? <span className={styles.leading}>{props.leading}</span> : null}<span className={styles.rowCopy}><strong>{props.title}</strong>{props.description ? <span>{props.description}</span> : null}</span>{props.trailing ? <span className={styles.trailing}>{props.trailing}</span> : null}</>;
  if (props.href) return <Link href={props.href} className={styles.row}>{body}</Link>;
  if (props.onSelect) return <button type="button" className={styles.row} aria-pressed={props.selected ?? false} disabled={props.disabled} onClick={props.onSelect}>{body}</button>;
  return <div className={styles.row}>{body}</div>;
}

export function V2ProvenanceDisclosure({ children, title = "Evidence & provenance", technical = false }: { children: ReactNode; title?: string; technical?: boolean }) {
  return <details className={styles.disclosure} data-technical={technical}><summary>{title}</summary><div>{children}</div></details>;
}

/** Compact readout for caller-supplied values. The primitive never computes, ranks or infers metrics; values and labels come from the caller's typed projection. */
export type V2MetricItem = { label: string; value: ReactNode; hint?: string };
export function V2MetricGroup({ items, label, className = "" }: { items: readonly V2MetricItem[]; label?: string; className?: string }) {
  return (
    <dl className={`${styles.metricGroup} ${className}`} aria-label={label}>
      {items.map((item) => (
        <div className={styles.metric} key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
          {item.hint ? <dd className={styles.metricHint}>{item.hint}</dd> : null}
        </div>
      ))}
    </dl>
  );
}

export type V2ReadState =
  | { kind: "loading"; label: string }
  | { kind: "empty"; label: string; detail: string }
  | { kind: "error" | "unavailable"; label: string; detail: string; onRetry?: () => void }
  | { kind: "partial"; label: string; unavailableSources: readonly string[]; onRetry?: () => void }
  | { kind: "stale"; label: string; detail: string; lastLoadedAt: string | null; onRetry?: () => void };
export function V2DataState({ state }: { state: V2ReadState }) {
  return <div className={styles.dataState} data-state={state.kind} role={state.kind === "error" || state.kind === "unavailable" ? "alert" : "status"} aria-busy={state.kind === "loading" || undefined}>
    <strong>{state.label}</strong>
    {state.kind === "loading" ? <span className={styles.skeleton} aria-hidden="true" /> : state.kind === "partial" ? <p>Unavailable: {state.unavailableSources.join(", ") || "Source names not supplied"}. Available records remain visible; completeness is unknown.</p> : <p>{state.detail}</p>}
    {state.kind === "stale" ? <p>Last loaded: {formatV2Timestamp(state.lastLoadedAt)}. Previously loaded records may no longer reflect current state.</p> : null}
    {"onRetry" in state && state.onRetry ? <button className={styles.control} type="button" onClick={state.onRetry}>Retry</button> : null}
  </div>;
}

export function V2Inspector({ title, children, onClose, description, className = "" }: { title: string; children: ReactNode; onClose: () => void; description?: string; className?: string }) {
  const id = useId();
  return <aside className={`${styles.inspector} ${className}`} aria-labelledby={id}><V2SectionHeader title={title} id={id} description={description} actions={<button type="button" className={styles.control} onClick={onClose} aria-label={`Close ${title}`}>Close</button>} />{children}</aside>;
}

export function formatV2Timestamp(value: string | null | undefined) {
  if (!value) return "Not supplied";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Timestamp unavailable" : date.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}
export function V2TimelineRow({ title, summary, occurredAt, coverage, selected, onSelect }: { title: string; summary: string; occurredAt: string; coverage: string; selected?: boolean; onSelect: () => void }) {
  return <V2ObjectRow title={title} description={summary} onSelect={onSelect} selected={selected} leading={<time dateTime={Number.isNaN(Date.parse(occurredAt)) ? undefined : occurredAt}>{formatV2Timestamp(occurredAt)}</time>} trailing={<V2StateBadge label={coverage} />} />;
}
export function V2EvidenceChip({ label, state, href }: { label: string; state: string; href?: string }) {
  const body = <><strong>{label}</strong><span>{state}</span></>;
  return href ? <Link href={href} className={styles.evidenceChip}>{body}</Link> : <span className={styles.evidenceChip}>{body}</span>;
}
