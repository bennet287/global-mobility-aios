"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2EvidenceSnapshot } from "../../hooks/useV2EvidenceSnapshot";
import {
  buildV2EvidenceWorkspace,
  evidenceDestination,
  selectEvidenceReference,
} from "../../lib/v2/evidence-intelligence";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import {
  V2DataState,
  V2Inspector,
  V2MetricGroup,
  V2ObjectRow,
  V2PageHeader,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
  V2Surface,
  formatV2Timestamp,
} from "./ui/V2Primitives";
import styles from "./V2EvidenceWorkspace.module.css";

export function V2EvidenceWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2EvidenceSnapshot();
  const params = useSearchParams();
  const router = useRouter();
  const model = read.latest?.snapshot ? buildV2EvidenceWorkspace(read.latest.snapshot) : null;
  const selected = model ? selectEvidenceReference(model.references, params.get("kind"), params.get("ref")) : null;
  const inspectorTarget = useRef<HTMLDivElement>(null);
  const selectionOrigin = useRef<HTMLElement | null>(null);

  useV2SearchItems((model?.references ?? []).map((reference) => ({
    id: reference.key,
    kind: "Evidence" as const,
    icon: "evidence" as const,
    label: `${reference.label}: ${reference.id}`,
    description: "Recorded Evidence reference from the loaded Austria organization snapshot",
    href: evidenceDestination(reference),
  })));

  useEffect(() => {
    if (selected) inspectorTarget.current?.focus();
  }, [selected]);

  function selectReference(kind: string, id: string) {
    selectionOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const next = new URLSearchParams({ kind, ref: id });
    router.push(`/cockpit/v2/evidence?${next.toString()}`, { scroll: false });
  }

  function closeInspector() {
    router.replace("/cockpit/v2/evidence", { scroll: false });
    requestAnimationFrame(() => selectionOrigin.current?.focus());
  }

  return (
    <V2Shell activeItem="Evidence" backendOnline={health?.status === "ok"}>
      <div className={`aios-v2-content ${styles.page}`}>
        <V2PageHeader
          eyebrow="Grounding ledger"
          title="Evidence"
          description="Inspect the Evidence references recorded by the bounded Austria organization snapshot without inventing source contents or verification beyond the supplied record."
          actions={<button type="button" onClick={() => void read.refresh()}>Refresh Evidence</button>}
        />

        {read.loading && !read.latest ? <V2DataState state={{ kind: "loading", label: "Loading Evidence ledger…" }} /> : null}
        {read.error && !read.latest ? <V2DataState state={{ kind: "unavailable", label: "Evidence source unavailable", detail: read.error, onRetry: () => void read.refresh() }} /> : null}
        {read.latest && read.error ? <V2DataState state={{ kind: "stale", label: "Evidence refresh failed", detail: read.error, lastLoadedAt: read.loadedAt, onRetry: () => void read.refresh() }} /> : null}
        {read.latest && !read.latest.established ? <V2DataState state={{ kind: "unavailable", label: "Evidence snapshot not established", detail: "The transparency endpoint returned no established Austria organization snapshot. AIOS does not convert that absence into zero Evidence." }} /> : null}

        {model ? (
          <>
            <V2ProvenanceDisclosure title="Evidence source posture">
              <p>Snapshot generated: {formatV2Timestamp(model.generatedAt)} · Loaded: {formatV2Timestamp(read.loadedAt)}.</p>
              <p>Root WorkItem: {model.rootWorkItemId} · Objective: {model.objectiveKey}.</p>
              <p>External action authorized: {String(model.externalActionAuthorized)}. This workspace performs no action.</p>
            </V2ProvenanceDisclosure>

            <V2MetricGroup
              label="Evidence ledger readout"
              items={[
                { label: "Domain evidence refs", value: model.domainEvidenceCount },
                { label: "Verified rule refs", value: model.verifiedRuleCount },
                { label: "Source snapshot refs", value: model.sourceSnapshotCount },
                { label: "Specialist outputs", value: model.specialists.length },
              ]}
            />

            {model.references.length ? (
              <div className={styles.workspace}>
                <V2Surface className={styles.ledger} label="Recorded Evidence references">
                  <V2SectionHeader
                    eyebrow="Recorded references"
                    title="Evidence ledger"
                    description="Identifiers are rendered exactly as supplied. Selecting a row opens inspection only."
                  />
                  <div className={styles.list}>
                    {model.references.map((reference) => (
                      <V2ObjectRow
                        key={reference.key}
                        title={reference.id}
                        description={reference.label}
                        trailing={<V2StateBadge label="Recorded reference" />}
                        selected={selected?.key === reference.key}
                        onSelect={() => selectReference(reference.kind, reference.id)}
                      />
                    ))}
                  </div>
                </V2Surface>

                <div className={styles.inspectorSlot} ref={inspectorTarget} tabIndex={-1}>
                  {selected ? (
                    <V2Inspector
                      title={selected.label}
                      description="Reference inspection only. Q6 does not claim the referenced source contents are loaded here."
                      onClose={closeInspector}
                    >
                      <V2StateBadge label="Recorded reference" />
                      <V2ProvenanceDisclosure title="Reference identity" technical>
                        <dl className={styles.definitionList}>
                          <dt>Kind</dt><dd>{selected.kind}</dd>
                          <dt>Reference ID</dt><dd>{selected.id}</dd>
                          <dt>Snapshot root WorkItem</dt><dd>{model.rootWorkItemId}</dd>
                        </dl>
                        <p>No source text, approval, freshness or legal conclusion is inferred from the existence of this identifier.</p>
                      </V2ProvenanceDisclosure>
                    </V2Inspector>
                  ) : params.get("ref") ? (
                    <V2DataState state={{ kind: "unavailable", label: "Selected Evidence reference was not returned", detail: "The exact kind/reference identity is outside this loaded snapshot. AIOS will not substitute another reference." }} />
                  ) : (
                    <V2Surface kind="inset" className={styles.placeholder} label="Evidence inspection">
                      <V2SectionHeader title="Inspect a reference" description="Choose a recorded reference to see its exact identity and source posture." />
                      <p>Selection is presentation-only and cannot mutate AIOS.</p>
                    </V2Surface>
                  )}
                </div>
              </div>
            ) : (
              <V2DataState state={{ kind: "empty", label: "No Evidence references returned", detail: "This established bounded snapshot returned no domain Evidence, verified-rule or source-snapshot references. It is not a global Evidence conclusion." }} />
            )}

            <V2Surface label="Specialist Evidence posture" className={styles.specialists}>
              <V2SectionHeader
                eyebrow="Supplied validation fields"
                title="Specialist Evidence posture"
                description="Exact specialist status and evidence_valid fields; no confidence or authority is inferred."
              />
              {model.specialists.length ? model.specialists.map((specialist) => (
                <V2ObjectRow
                  key={`${specialist.positionKey}:${specialist.workItemId}`}
                  title={specialist.positionKey}
                  description={`${specialist.status} · WorkItem ${specialist.workItemId}${specialist.groundingState ? ` · Grounding ${specialist.groundingState}` : ""}`}
                  trailing={<V2StateBadge label={`evidence_valid=${String(specialist.evidenceValid)}`} />}
                />
              )) : <V2DataState state={{ kind: "empty", label: "No specialist outputs returned", detail: "The bounded snapshot contains no specialist output records." }} />}
              {model.specialists.length ? (
                <V2ProvenanceDisclosure title="Specialist Evidence counts and warnings" technical>
                  {model.specialists.map((specialist) => (
                    <dl className={styles.definitionList} key={`detail:${specialist.positionKey}:${specialist.workItemId}`}>
                      <dt>Position</dt><dd>{specialist.positionKey}</dd>
                      <dt>Evidence reason</dt><dd>{specialist.evidenceReason ?? "Not supplied"}</dd>
                      <dt>Evidence refs</dt><dd>{specialist.evidenceRefCount ?? "Not supplied"}</dd>
                      <dt>Verified rule refs</dt><dd>{specialist.verifiedRuleRefCount ?? "Not supplied"}</dd>
                      <dt>Source snapshot refs</dt><dd>{specialist.sourceSnapshotRefCount ?? "Not supplied"}</dd>
                      <dt>Warnings</dt><dd>{specialist.warnings.join(" · ") || "None supplied"}</dd>
                    </dl>
                  ))}
                </V2ProvenanceDisclosure>
              ) : null}
            </V2Surface>
          </>
        ) : null}
      </div>
    </V2Shell>
  );
}
