"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2EnvironmentalMemory } from "../../hooks/useV2EnvironmentalMemory";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import {
  activityDestination,
  buildV2IntelligenceModel,
  selectRecentChange,
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
  V2TimelineRow,
  V2TruthBadge,
  formatV2Timestamp,
} from "./ui/V2Primitives";
import styles from "./V2IntelligenceWorkspace.module.css";

export function V2IntelligenceWorkspace() {
  const { health } = useBackendStatus();
  const owner = useV2OwnerOrganization();
  const memoryRead = useV2EnvironmentalMemory();
  const params = useSearchParams();
  const router = useRouter();
  const model = buildV2IntelligenceModel(owner.data, memoryRead.latest?.memory);
  const selectedActivity = selectRecentChange(model.current?.recentChanges ?? [], params.get("activity"));
  const inspectorTarget = useRef<HTMLDivElement>(null);
  const selectionOrigin = useRef<HTMLElement | null>(null);

  useV2SearchItems((model.current?.recentChanges ?? []).map((change) => ({
    id: change.id,
    kind: "Event" as const,
    icon: "intelligence" as const,
    label: change.title,
    description: `${change.activityClass} · ${change.summary}`,
    href: activityDestination(change.id),
  })));

  useEffect(() => {
    if (selectedActivity) inspectorTarget.current?.focus();
  }, [selectedActivity]);

  function selectActivity(activityId: string) {
    selectionOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    router.push(activityDestination(activityId), { scroll: false });
  }

  function closeInspector() {
    router.replace("/cockpit/v2/intelligence", { scroll: false });
    requestAnimationFrame(() => selectionOrigin.current?.focus());
  }

  const activityUnavailable = owner.data?.unavailableSources.includes("Activity") === true;
  const memory = model.memory;

  return (
    <V2Shell activeItem="Intelligence" backendOnline={health?.status === "ok"}>
      <div className={`aios-v2-content ${styles.page}`}>
        <V2PageHeader
          eyebrow="Governed signals"
          title="Intelligence"
          description="Read current governed signals beside aggregate organization memory without treating either surface as prediction, authority or instruction."
          actions={<button type="button" onClick={() => { void owner.refresh(); void memoryRead.refresh(); }}>Refresh Intelligence</button>}
        />

        {owner.loading && !owner.data ? <V2DataState state={{ kind: "loading", label: "Loading current organization signals…" }} /> : null}
        {owner.error && !owner.data ? <V2DataState state={{ kind: "unavailable", label: "Current organization signals unavailable", detail: owner.error, onRetry: () => void owner.refresh() }} /> : null}
        {owner.data && owner.error ? <V2DataState state={{ kind: "stale", label: "Current signal refresh failed", detail: owner.error, lastLoadedAt: owner.data.loadedAt, onRetry: () => void owner.refresh() }} /> : null}
        {owner.data?.partial ? <V2DataState state={{ kind: "partial", label: "Partial current-source coverage", unavailableSources: owner.data.unavailableSources }} /> : null}

        {model.current ? (
          <>
            <V2MetricGroup
              label="Current intelligence readout"
              items={[
                { label: "Attention records", value: model.current.attentionCount, hint: "Governed records returned" },
                { label: "Projected Missions", value: model.current.missionCount },
                { label: "Department blocker entries", value: model.current.departmentBlockerCount },
                { label: "Recent Activity records", value: model.current.recentActivityCount },
              ]}
            />

            <div className={styles.currentWorkspace}>
              <V2Surface className={styles.currentColumn} label="Current governed signals">
                <V2SectionHeader
                  eyebrow="Current canonical reads"
                  title="Owner attention"
                  description="Records are shown in the ordering supplied by the governed Owner read."
                />
                {owner.data?.attention.length ? owner.data.attention.map((item) => (
                  <V2ObjectRow
                    key={item.id}
                    href={item.href}
                    title={item.title}
                    description={item.detail}
                    trailing={<V2StateBadge label={item.kind} />}
                  />
                )) : <V2DataState state={{ kind: "empty", label: "No Owner-attention records returned", detail: "This bounded read returned no attention records; it is not a global claim that no work needs attention." }} />}

                <V2SectionHeader
                  eyebrow="Recent canonical Activity"
                  title="Significant change"
                  description="Activity rows are selectable for inspection; selection does not act on the underlying record."
                />
                {activityUnavailable ? <V2DataState state={{ kind: "unavailable", label: "Activity source unavailable", detail: "The governed Owner read could not retrieve Activity. No empty Activity conclusion is made." }} /> : model.current.recentChanges.length ? (
                  <div className={styles.list}>
                    {model.current.recentChanges.map((change) => (
                      <V2TimelineRow
                        key={change.id}
                        title={change.title}
                        summary={change.summary}
                        occurredAt={change.occurredAt}
                        coverage={change.activityClass}
                        selected={selectedActivity?.id === change.id}
                        onSelect={() => selectActivity(change.id)}
                      />
                    ))}
                  </div>
                ) : <V2DataState state={{ kind: "empty", label: "No recent Activity records returned", detail: "The available Activity read returned no recent records within its bounded page." }} />}
              </V2Surface>

              <div className={styles.inspectorSlot} ref={inspectorTarget} tabIndex={-1}>
                {selectedActivity ? (
                  <V2Inspector
                    title={selectedActivity.title}
                    description="Read-only Activity inspection."
                    onClose={closeInspector}
                  >
                    <V2StateBadge label={selectedActivity.activityClass} />
                    <p className={styles.summary}>{selectedActivity.summary}</p>
                    <V2ProvenanceDisclosure title="Activity provenance" technical>
                      <dl className={styles.definitionList}>
                        <dt>Activity ID</dt><dd>{selectedActivity.id}</dd>
                        <dt>Occurred at</dt><dd>{formatV2Timestamp(selectedActivity.occurredAt)}</dd>
                        <dt>Department</dt><dd>{selectedActivity.department ?? "Not supplied"}</dd>
                        <dt>Position</dt><dd>{selectedActivity.positionKey ?? "Not supplied"}</dd>
                      </dl>
                      <p>No completion, authority, physical presence or conversation is inferred from this Activity row.</p>
                    </V2ProvenanceDisclosure>
                  </V2Inspector>
                ) : params.get("activity") ? (
                  <V2DataState state={{ kind: "unavailable", label: "Selected Activity was not returned", detail: "The exact Activity ID is outside the loaded recent-change page. AIOS will not substitute another event." }} />
                ) : (
                  <V2Surface kind="inset" className={styles.placeholder} label="Activity inspection">
                    <V2SectionHeader title="Inspect Activity" description="Choose a returned Activity record to inspect its supplied provenance." />
                    <p>Selection changes context only.</p>
                  </V2Surface>
                )}
              </div>
            </div>
          </>
        ) : null}

        <V2Surface className={styles.memorySection} label="Aggregate organization memory">
          <V2SectionHeader
            eyebrow="Historical aggregate"
            title="Organization memory"
            description="Bounded Activity aggregates for orientation. They are not current-state authority and are not predictions."
            actions={<V2TruthBadge kind="memory" />}
          />

          {memoryRead.loading && !memoryRead.latest ? <V2DataState state={{ kind: "loading", label: "Loading aggregate organization memory…" }} /> : null}
          {memoryRead.error && !memoryRead.latest ? <V2DataState state={{ kind: "unavailable", label: "Aggregate memory unavailable", detail: memoryRead.error, onRetry: () => void memoryRead.refresh() }} /> : null}
          {memoryRead.latest && memoryRead.error ? <V2DataState state={{ kind: "stale", label: "Aggregate memory refresh failed", detail: memoryRead.error, lastLoadedAt: memoryRead.loadedAt, onRetry: () => void memoryRead.refresh() }} /> : null}
          {memoryRead.latest && !memoryRead.latest.established ? <V2DataState state={{ kind: "unavailable", label: "Aggregate memory not established", detail: "The environmental-memory endpoint returned no established memory projection. AIOS does not convert this to zero historical activity." }} /> : null}

          {memory ? (
            <>
              <V2MetricGroup
                label="Aggregate memory readout"
                items={[
                  { label: "Window events", value: memory.windowEventCount },
                  { label: "Event kinds", value: memory.kindAggregates.length },
                  { label: "Assignment relation paths", value: memory.pathFrequencies.length, hint: "Not physical movement" },
                  { label: "Timeline buckets", value: memory.timeline.length },
                ]}
              />

              <div className={styles.memoryGrid}>
                <div>
                  <V2SectionHeader title="Event-kind aggregates" level={3} description="Literal counts from the bounded replay-derived memory window." />
                  <div className={styles.list}>
                    {memory.kindAggregates.map((item) => <V2ObjectRow key={item.event_kind} title={item.event_kind} description={`${item.event_count} recorded events`} />)}
                  </div>
                </div>
                <div>
                  <V2SectionHeader title="Timeline buckets" level={3} description="Counts by supplied bucket; no trend or forecast is inferred." />
                  <div className={styles.list}>
                    {memory.timeline.slice(-6).map((item) => <V2ObjectRow key={item.bucket_start} title={formatV2Timestamp(item.bucket_start)} description={`${item.event_count} events · ${item.blocker_count} blockers · ${item.decision_count} decisions · ${item.conversation_count} conversations`} trailing={<V2StateBadge label={item.coverage_state} />} />)}
                  </div>
                </div>
              </div>

              <V2ProvenanceDisclosure title="Aggregate-memory truth posture" technical>
                <dl className={styles.definitionList}>
                  <dt>Generated</dt><dd>{formatV2Timestamp(memory.generatedAt)}</dd>
                  <dt>Window</dt><dd>{formatV2Timestamp(memory.windowStart)} → {formatV2Timestamp(memory.windowEnd)}</dd>
                  <dt>Canonical projection</dt><dd>{String(memory.canonicalProjection)}</dd>
                  <dt>Authoritative</dt><dd>{String(memory.authoritative)}</dd>
                  <dt>Predictive</dt><dd>{String(memory.predictive)}</dd>
                  <dt>Mutations allowed</dt><dd>{String(memory.mutationsAllowed)}</dd>
                  <dt>Visualization only</dt><dd>{String(memory.visualizationOnly)}</dd>
                  <dt>Unsupported dimensions</dt><dd>{memory.unsupportedDimensions.join(" · ") || "None supplied"}</dd>
                </dl>
                <h3>Recorded assignment relation frequencies</h3>
                {memory.pathFrequencies.length ? memory.pathFrequencies.map((path) => (
                  <p key={`${path.previous_position_key}:${path.assigned_position_key}`}>{path.previous_position_key} → {path.assigned_position_key}: {path.handoff_count} recorded handoffs across {path.work_item_count} WorkItems. This is assignment lineage, not physical movement.</p>
                )) : <p>No assignment relation frequencies were returned in this bounded memory window.</p>}
              </V2ProvenanceDisclosure>
            </>
          ) : null}
        </V2Surface>
      </div>
    </V2Shell>
  );
}
