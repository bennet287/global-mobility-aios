import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./V2Primitives.module.css";

export { styles as v2Styles };
export type TruthKind = "canonical" | "authority" | "recommendation" | "historical" | "memory" | "prediction" | "simulation" | "stale" | "unsupported" | "unavailable";
const truthLabels: Record<TruthKind, string> = { canonical: "Canonical record", authority: "Human authority", recommendation: "Recommendation", historical: "Historical reconstruction", memory: "Aggregate memory", prediction: "Prediction", simulation: "Simulation", stale: "Stale view", unsupported: "Unsupported", unavailable: "Unavailable" };
export function TruthBadge({ kind }: { kind: TruthKind }) { return <span className={styles.truth} data-truth={kind}>{truthLabels[kind]}</span>; }
export function StatusLabel({ value }: { value: string }) { return <span className={styles.status}>{value.replaceAll("_", " ")}</span>; }
export function V2PageHeader({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: ReactNode }) {
  return <header className={styles.pageHeader} data-guide="workspace-title"><div><span className={styles.eyebrow}>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{children ? <div className={styles.actions}>{children}</div> : null}</header>;
}
export function ReadState({ loading, error, hasData, onRetry }: { loading: boolean; error: string | null; hasData: boolean; onRetry: () => void }) {
  if (error) return <div className={styles.notice} role="alert"><TruthBadge kind={hasData ? "stale" : "unavailable"} /><strong>{hasData ? "Refresh failed. Previously loaded records remain visible." : "Records could not be loaded."}</strong><p>{error}</p><button type="button" onClick={onRetry}>Retry</button></div>;
  if (loading) return <div className={styles.notice} role="status">{hasData ? "Refreshing records…" : "Loading records…"}</div>;
  return null;
}
export function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className={styles.empty} role="status"><strong>{title}</strong><p>{detail}</p></div>; }
export function Provenance({ children, label = "Evidence & provenance" }: { children: ReactNode; label?: string }) { return <details className={styles.disclosure}><summary>{label}</summary><div>{children}</div></details>; }
export function RecordFields({ values }: { values: Record<string, unknown> }) {
  return <dl className={styles.fields}>{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value === null || value === undefined || value === "" ? "Not supplied" : typeof value === "object" ? <pre>{JSON.stringify(value, null, 2)}</pre> : String(value)}</dd></div>)}</dl>;
}
export function safeSourceUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch { return null; }
}
export function SourceLink({ url, children }: { url: string | null | undefined; children: ReactNode }) { const safe = safeSourceUrl(url); return safe ? <a href={safe} target="_blank" rel="noopener noreferrer">{children} ↗</a> : <span>{children} · URL unavailable</span>; }
export function RelatedLink({ href, children }: { href: string; children: ReactNode }) { return <Link className={styles.related} href={href}>{children} →</Link>; }
export function formatV2Date(value: string | null | undefined) { if (!value || Number.isNaN(Date.parse(value))) return "Not supplied"; return new Date(value).toLocaleString(); }
