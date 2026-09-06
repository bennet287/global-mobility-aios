"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2DecisionsScene } from "../../hooks/useV2DecisionsScene";
import {
  buildV2DecisionPortfolio,
  decisionDestination,
  filterV2Decisions,
  selectV2Decision,
} from "../../lib/v2/decisions-workspace";
import { useV2SearchItems } from "./V2NavigationContext";
import { V2Shell } from "./V2Shell";
import {
  V2AuthorityBadge,
  V2DataState,
  V2Inspector,
  V2MetricGroup,
  V2ObjectRow,
  V2PageHeader,
  V2ProvenanceDisclosure,
  V2SectionHeader,
  V2StateBadge,
  V2Surface,
  V2TruthBadge,
  formatV2Timestamp,
} from "./ui/V2Primitives";
import styles from "./V2DecisionsWorkspace.module.css";

export function V2DecisionsWorkspace() {
  const { latest, loading, error, loadedAt, refresh } = useV2DecisionsScene();
  const { health } = useBackendStatus();
  const params = useSearchParams();
  const router = useRouter();
  const selectedId = params.get("decision");
  const query = params.get("q") ?? "";
  const status = params.get("status") ?? "";
  const ownerActionOnly = params.get("owner_action") === "required";
  const portfolio = useMemo(() => buildV2DecisionPortfolio(latest), [latest]);
  const filtered = filterV2Decisions(portfolio.decisions, query, status, ownerActionOnly);
  const selected = selectV2Decision(portfolio.decisions, selectedId);
  const inspectorTarget = useRef<HTMLDivElement>(null);
  const selectionOrigin = useRef<HTMLElement | null>(null);

  useV2SearchItems(portfolio.decisions.map((decision) => ({
    id: decision.decisionId,
    kind: "Decision" as const,
    icon: "decisions" as const,
    label: decision.title,
    description: `${decision.status} · ${decision.authorityLevel}${decision.requiredOwnerAction ? " · owner action recorded" : ""}`,
    href: decisionDestination(decision.decisionId),
  })));

  useEffect(() => {
    if (selectedId && selected) inspectorTarget.current?.focus();
  }, [selectedId, selected]);

  function replaceParams(mutator: (next: URLSearchParams) => void) {
    const next = new URLSearchParams(params.toString());
    mutator(next);
    const suffix = next.toString();
    router.replace(`/cockpit/v2/decisions${suffix ? `?${suffix}` : ""}`, { scroll: false });
  }

  function setParam(name: string, value: string) {
    replaceParams((next) => {
      if (value) next.set(name, value);
      else next.delete(name);
    });
  }

  function selectDecision(decisionId: string) {
    selectionOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const next = new URLSearchParams(params.toString());
    next.set("decision", decisionId);
    router.push(`/cockpit/v2/decisions?${next.toString()}`, { scroll: false });
  }

  function closeInspector() {
    setParam("decision", "");
    requestAnimationFrame(() => selectionOrigin.current?.focus());
  }

  const statuses = [...new Set(portfolio.decisions.map((decision) => decision.status))].sort();

  return (
    <V2Shell activeItem="Decisions" backendOnline={health?.status === "ok"}>
      <div className={`aios-v2-content ${styles.page}`}>
        <V2PageHeader
          eyebrow="Board transparency"
          title="Decisions"
          description="Inspect recorded Executive Decision state, authority, recommendation and supersession without turning selection into approval."
          actions={<button type="button" onClick={() => void refresh()}>Refresh Decisions</button>}
        />

        {loading && !latest ? <V2DataState state={{ kind: "loading", label: "Loading Decision records…" }} /> : null}
        {error && !latest ? <V2DataState state={{ kind: "unavailable", label: "Decision records unavailable", detail: error, onRetry: () => void refresh() }} /> : null}
        {latest && error ? <V2DataState state={{ kind: "stale", label: "Decision refresh failed", detail: error, lastLoadedAt: loadedAt, onRetry: () => void refresh() }} /> : null}
        {latest && !latest.established ? <V2DataState state={{ kind: "unavailable", label: "Decision projection not established", detail: "The Living Organization source returned no established scene. AIOS does not fabricate a Decision portfolio." }} /> : null}

        {portfolio.established ? (
          <>
            <V2ProvenanceDisclosure title="Decision source posture">
              <p>Loaded {formatV2Timestamp(loadedAt)} from the existing Living Organization transparency read.</p>
              <p>Scene generated: {formatV2Timestamp(portfolio.generatedAt)} · Contract: {portfolio.contractVersion ?? "Not supplied"}.</p>
              <p>Canonical authority: {portfolio.canonicalAuthority ?? "Not supplied"}. Scene authoritative: {String(portfolio.sceneAuthoritative)}. Mutations allowed by scene: {String(portfolio.mutationsAllowed)}.</p>
            </V2ProvenanceDisclosure>

            <V2MetricGroup
              label="Decision portfolio readout"
              items={[
                { label: "Returned Decisions", value: portfolio.returnedDecisionCount },
                { label: "Current records", value: portfolio.currentDecisionCount },
                { label: "Owner action recorded", value: portfolio.ownerActionCount },
                { label: "Supersession-linked", value: portfolio.supersessionLinkedCount },
              ]}
            />

            {portfolio.decisions.length ? (
              <div className={styles.workspace}>
                <V2Surface className={styles.portfolio} label="Decision portfolio">
                  <V2SectionHeader
                    eyebrow="Canonical projection"
                    title="Decision records"
                    description="Exact supplied status, authority and owner-action flags. Ordering uses those recorded fields only."
                  />

                  <div className={styles.filters}>
                    <label>
                      <span>Filter Decisions</span>
                      <input aria-label="Filter Decisions" type="search" value={query} onChange={(event) => setParam("q", event.target.value)} />
                    </label>
                    <label>
                      <span>Status</span>
                      <select aria-label="Decision status" value={status} onChange={(event) => setParam("status", event.target.value)}>
                        <option value="">All returned statuses</option>
                        {statuses.map((value) => <option key={value} value={value}>{value}</option>)}
                      </select>
                    </label>
                    <label className={styles.ownerToggle}>
                      <input
                        type="checkbox"
                        checked={ownerActionOnly}
                        onChange={(event) => setParam("owner_action", event.target.checked ? "required" : "")}
                      />
                      <span>Owner action recorded</span>
                    </label>
                  </div>

                  <div className={styles.list} aria-label="Decision records">
                    {filtered.map((decision) => (
                      <V2ObjectRow
                        key={decision.decisionId}
                        title={decision.title}
                        description={`${decision.decisionOwnerPosition} · ${decision.authorityLevel} · ${decision.evidenceItemCount} recorded evidence items`}
                        trailing={(
                          <span className={styles.rowMeta}>
                            {decision.requiredOwnerAction ? <V2StateBadge label="Owner action required" tone="warning" /> : null}
                            <V2StateBadge label={decision.status} />
                            <V2StateBadge label={decision.isCurrent ? "Current record" : "Not current"} />
                          </span>
                        )}
                        selected={selectedId === decision.decisionId}
                        onSelect={() => selectDecision(decision.decisionId)}
                      />
                    ))}
                  </div>

                  {!filtered.length ? <V2DataState state={{ kind: "empty", label: "No returned Decisions match these filters", detail: "The filtered view is empty; this does not describe records outside the loaded canonical projection." }} /> : null}
                </V2Surface>

                <div className={styles.inspectorSlot} ref={inspectorTarget} tabIndex={-1}>
                  {selected ? (
                    <V2Inspector
                      title={selected.title}
                      description="Read-only Decision inspection. Selection changes view context only."
                      onClose={closeInspector}
                    >
                      <div className={styles.stateLine}>
                        <V2StateBadge label={selected.status} />
                        <V2AuthorityBadge level={selected.authorityLevel} />
                        {selected.requiredOwnerAction ? <V2StateBadge label="Owner action required" tone="warning" /> : null}
                      </div>

                      <V2MetricGroup
                        label="Selected Decision readout"
                        items={[
                          { label: "Current record", value: selected.isCurrent ? "Yes" : "No" },
                          { label: "Owner action required", value: selected.requiredOwnerAction ? "Yes" : "No" },
                          { label: "Evidence items", value: selected.evidenceItemCount, hint: "Count only; content is not inferred" },
                        ]}
                      />

                      <V2Surface kind="inset" className={styles.recommendation} label="Recorded recommendation">
                        <V2TruthBadge kind="recommendation" />
                        <strong>Recorded recommendation</strong>
                        <p>{selected.recommendation || "Not supplied"}</p>
                      </V2Surface>

                      <V2SectionHeader level={3} title="Recorded question" />
                      <p className={styles.muted}>{selected.question || "Not supplied"}</p>

                      <V2ProvenanceDisclosure title="Decision provenance & supersession" technical>
                        <dl className={styles.definitionList}>
                          <dt>Decision ID</dt><dd>{selected.decisionId}</dd>
                          <dt>Decision key</dt><dd>{selected.decisionKey}</dd>
                          <dt>Owner position</dt><dd>{selected.decisionOwnerPosition}</dd>
                          <dt>WorkItem</dt><dd>{selected.workItemId ?? "Not supplied"}</dd>
                          <dt>Fingerprint</dt><dd>{selected.recordFingerprint ?? "Not supplied"}</dd>
                          <dt>Source object</dt><dd>{[selected.sourceObjectType, selected.sourceObjectId, selected.sourceObjectVersion].filter(Boolean).join(" · ") || "Not supplied"}</dd>
                          <dt>Supersedes</dt><dd>{selected.supersedesDecisionId ?? "None supplied"}</dd>
                          <dt>Superseded by</dt><dd>{selected.supersededByDecisionId ?? "None supplied"}</dd>
                          <dt>Created</dt><dd>{formatV2Timestamp(selected.createdAt)}</dd>
                          <dt>Decided</dt><dd>{formatV2Timestamp(selected.decidedAt)}</dd>
                          <dt>Superseded-by created</dt><dd>{formatV2Timestamp(selected.supersededByCreatedAt)}</dd>
                          <dt>Superseded in projection week</dt><dd>{String(selected.supersededInProjectionWeek)}</dd>
                        </dl>
                        <p>No approval, legal validity, completion, urgency or execution authority is inferred from recommendation text, timestamps, evidence count or styling.</p>
                      </V2ProvenanceDisclosure>
                    </V2Inspector>
                  ) : selectedId ? (
                    <V2DataState state={{ kind: "unavailable", label: "Selected Decision was not returned", detail: "The exact Decision ID is outside this loaded projection. AIOS will not substitute another record." }} />
                  ) : (
                    <V2Surface kind="inset" className={styles.placeholder} label="Decision inspection">
                      <V2SectionHeader title="Inspect a Decision" description="Choose a returned Decision to inspect its supplied authority, recommendation and supersession lineage." />
                      <p>Selection is presentation-only. Q7 provides no approve, reject, execute or mutation control.</p>
                    </V2Surface>
                  )}
                </div>
              </div>
            ) : (
              <V2DataState state={{ kind: "empty", label: "No Decisions returned", detail: "The established Living Organization projection returned an empty Decision collection." }} />
            )}
          </>
        ) : null}
      </div>
    </V2Shell>
  );
}
