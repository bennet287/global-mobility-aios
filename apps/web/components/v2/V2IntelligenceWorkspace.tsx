"use client";
import { useState } from "react";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2Read } from "../../hooks/useV2Read";
import { getGlobalIntelligenceDashboard } from "../../lib/api";
import { V2Shell } from "./V2Shell";
import { EmptyState, Provenance, ReadState, RecordFields, RelatedLink, SourceLink, StatusLabel, TruthBadge, V2PageHeader, formatV2Date, v2Styles as s } from "./V2Primitives";
const loadIntelligence = () => getGlobalIntelligenceDashboard(90);

export function V2IntelligenceWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2Read(loadIntelligence);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const data = read.data;
  const changes = [...new Map([...(data?.new_programs ?? []), ...(data?.immigration_changes ?? []), ...(data?.processing_times ?? []), ...(data?.skilled_occupations ?? []), ...(data?.thresholds ?? [])].map((item) => [item.id, item])).values()];
  const visible = changes.filter((item) => (status === "all" || item.status === status) && `${item.country} ${item.title} ${item.summary}`.toLowerCase().includes(query.toLowerCase()));
  return <V2Shell activeItem="Intelligence" backendOnline={health?.status === "ok"}>
    <V2PageHeader eyebrow="Observe before interpreting" title="Intelligence" description="Source-backed changes, their review state, and the limits of coverage."><button type="button" onClick={() => void read.refresh()}>Refresh</button></V2PageHeader>
    <ReadState {...read} hasData={Boolean(data)} onRetry={() => void read.refresh()} />
    {data ? <><div className={s.notice}><p>{data.scope.coverage_warning}</p><p>{data.safety.message}</p><small>Window: {data.window_days} days · Snapshot {formatV2Date(data.generated_at)}</small></div>
      <div className={s.toolbar}><label>Find changes<input type="search" value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>Review state<select value={status} onChange={(e) => setStatus(e.target.value)}><option value="all">All returned</option>{[...new Set(changes.map((item) => item.status))].map((value) => <option key={value}>{value}</option>)}</select></label><span>{visible.length} returned changes</span></div>
      <ul className={s.list}>{visible.map((item) => <li className={s.row} key={item.id}><article><span className={s.eyebrow}>{item.country} · {item.domain}</span><strong>{item.title}</strong><p>{item.summary}</p><div className={s.actions}><StatusLabel value={item.status} /><StatusLabel value={item.freshness} /><StatusLabel value={item.materiality} /></div><p><SourceLink url={item.source_url}>{item.source_name ?? "Source"}</SourceLink></p><Provenance><RecordFields values={{ change_id: item.id, authority: item.authority_name, detected_at: item.detected_at, effective_at: item.effective_at, reviewed_by: item.reviewed_by, reviewed_at: item.reviewed_at, confidence: item.confidence, confidence_source: item.confidence_source, coverage: item.coverage, coverage_gaps: item.coverage_gaps }} /></Provenance>{item.source_id ? <RelatedLink href={`/cockpit/v2/evidence?source=${encodeURIComponent(item.source_id)}`}>Linked source rules</RelatedLink> : null}</article></li>)}</ul>
      {!visible.length ? <EmptyState title="No matching change returned" detail="No claim is made about changes outside the returned monitoring window." /> : null}
      <section className={s.detail}><TruthBadge kind="recommendation" /><h2>Signals for investigation</h2><p>These are classified activity signals. They are not client eligibility or investment recommendations.</p>{data.opportunity_radar.map((item) => <Provenance key={item.jurisdiction_id} label={`${item.country} · ${item.classification}`}><p>{item.explanation}</p><RecordFields values={{ signal_level: item.signal_level, evidence_count: item.evidence_count, classification: item.classification }} /></Provenance>)}</section>
    </> : null}
  </V2Shell>;
}
