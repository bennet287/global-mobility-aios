"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2Read } from "../../hooks/useV2Read";
import { loadV2Evidence } from "../../lib/v2/evidence";
import { V2Shell } from "./V2Shell";
import { useV2SearchItems } from "./V2NavigationContext";
import { EmptyState, Provenance, ReadState, RecordFields, RelatedLink, SourceLink, StatusLabel, TruthBadge, V2PageHeader, formatV2Date, v2Styles as s } from "./V2Primitives";

export function V2EvidenceWorkspace() {
  const { health } = useBackendStatus();
  const read = useV2Read(loadV2Evidence);
  const params = useSearchParams();
  const [query, setQuery] = useState("");
  const [state, setState] = useState("all");
  const [selected, setSelected] = useState<string | null>(null);
  const rules = read.data?.rules ?? [];
  useV2SearchItems(rules.map((item) => ({ kind: "Evidence", label: item.rule_key, description: `${item.country} · ${item.domain}`, icon: "evidence", href: `/cockpit/v2/evidence?rule=${encodeURIComponent(item.id)}` })));
  const current = params.get("rule") ?? selected ?? rules.find((item) => !params.get("source") || item.official_source_id === params.get("source"))?.id;
  const rule = rules.find((item) => item.id === current);
  const visible = rules.filter((item) => (state === "all" || item.active === (state === "active")) && (!params.get("source") || item.official_source_id === params.get("source")) && `${item.rule_key} ${item.statement} ${item.country} ${item.domain}`.toLowerCase().includes(query.toLowerCase()));
  const source = read.data?.sources.find((item) => item.id === rule?.official_source_id);
  const snapshot = read.data?.snapshots.find((item) => item.id === rule?.source_snapshot_id);
  return <V2Shell activeItem="Evidence" backendOnline={health?.status === "ok"}>
    <V2PageHeader eyebrow="Know what supports it" title="Evidence" description="Read the governed rule, trace its source, and keep uncertainty visible."><button type="button" onClick={() => void read.refresh()}>Refresh</button></V2PageHeader>
    <ReadState {...read} hasData={Boolean(read.data)} onRetry={() => void read.refresh()} />
    {read.data?.unavailable.length ? <div className={s.notice} role="status"><TruthBadge kind="unavailable" /><p>Unavailable: {read.data.unavailable.join(", ")}. Missing reads do not establish an empty evidence base.</p><button type="button" onClick={() => void read.refresh()}>Retry sources</button></div> : null}
    <div className={s.toolbar}><label>Search returned rules<input type="search" value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>Rule state<select value={state} onChange={(e) => setState(e.target.value)}><option value="all">All returned</option><option value="active">Active</option><option value="retired">Inactive</option></select></label><span>{visible.length} matching · up to 100 rules and snapshots</span></div>
    <div className={s.split}><nav aria-label="Verified rules"><ul className={s.list}>{visible.map((item) => <li key={item.id}><button type="button" className={s.row} aria-pressed={current === item.id} onClick={() => { setSelected(item.id); window.history.replaceState(null, "", `?rule=${encodeURIComponent(item.id)}`); }}><div><strong>{item.rule_key}</strong><small>{item.country} · {item.domain}</small></div><StatusLabel value={item.active ? "active" : "inactive"} /></button></li>)}</ul>{!read.loading && !read.data?.unavailable.includes("Verified rules") && !visible.length ? <EmptyState title="No matching rules returned" detail="Adjust your filter. This list is bounded and is not a global coverage claim." /> : null}</nav>
      {rule ? <article className={s.detail} data-guide="evidence-detail"><TruthBadge kind="canonical" /><h2>{rule.rule_key}</h2><p>{rule.statement}</p><div className={s.actions}><StatusLabel value={rule.active ? "active rule" : "inactive rule"} /><span>{rule.country} · {rule.domain}</span></div>
        <h3>Official source</h3>{source ? <><SourceLink url={source.url}>{source.name}</SourceLink><p>{source.authority ?? "Authority not supplied"} · {source.source_type}</p><StatusLabel value={source.active ? "source active" : "source inactive"} /></> : <p>Linked source not in the returned source set.</p>}
        <h3>Snapshot & freshness</h3>{snapshot ? <><p>Captured {formatV2Date(snapshot.captured_at)}</p><StatusLabel value={snapshot.status} /><p>{snapshot.content_preview}</p><SourceLink url={snapshot.url}>Inspect source URL</SourceLink></> : <p>Linked snapshot not in the returned snapshot set.</p>}<p>Current freshness is not established by the rule's active flag or capture time alone.</p>
        <h3>Effective period</h3><p>{rule.effective_from ?? "Start not supplied"} → {rule.effective_to ?? "End not supplied"}</p>
        <Provenance><RecordFields values={{ rule_id: rule.id, official_source_id: rule.official_source_id, source_snapshot_id: rule.source_snapshot_id, content_hash: snapshot?.content_hash, approved_by: rule.approved_by, published_at: rule.published_at, confidence: rule.confidence, supersedes_rule_id: rule.supersedes_rule_id, regulatory_change_id: rule.regulatory_change_id, initial_rule_assertion_id: rule.initial_rule_assertion_id, retired_at: rule.retired_at, retirement_reason: rule.retirement_reason, parser_version: snapshot?.parser_version, retrieval_method: snapshot?.retrieval_method }} /><p>Confidence is the stored rule score, not a probability of legal correctness. Independent professional-review evidence is not supplied by this record contract.</p></Provenance>
        {rule.supersedes_rule_id ? <RelatedLink href={`/cockpit/v2/evidence?rule=${encodeURIComponent(rule.supersedes_rule_id)}`}>Prior rule</RelatedLink> : null}<RelatedLink href="/source-certification-review">Source review workspace</RelatedLink>
      </article> : current && !read.loading ? <EmptyState title="Selected rule not returned" detail="The rule may be outside this bounded read. Its content and status are not inferred." /> : null}
    </div>
    <Provenance label="Official source registry"><ul className={s.list}>{read.data?.sources.map((item) => <li className={s.row} key={item.id}><div><SourceLink url={item.url}>{item.name}</SourceLink><p>{item.country} · {item.domain} · {item.authority ?? "Authority not supplied"}</p></div><StatusLabel value={item.active ? "active" : "inactive"} /></li>)}</ul></Provenance>
  </V2Shell>;
}
