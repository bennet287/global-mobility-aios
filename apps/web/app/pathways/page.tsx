"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { EvidenceProvenance, type EvidenceProvenanceItem } from "../../components/EvidenceProvenance";
import {
  createPathway,
  createPathwayVersion,
  getHealthStatus,
  getPathway,
  HealthStatus,
  Jurisdiction,
  listJurisdictions,
  listOfficialSources,
  listPathwayRegulatoryImpacts,
  listPathways,
  listSourceSnapshots,
  listVerifiedRules,
  MobilityPathway,
  MobilityPathwayDetail,
  OfficialSourceView,
  PathwayDomain,
  PathwayRegulatoryImpact,
  PathwayRegulatoryImpactQueue,
  PathwayVersion,
  PathwayVersionInput,
  publishPathwayVersion,
  reviewPathwayRegulatoryImpact,
  retirePathway,
  SourceSnapshotView,
  VerifiedRule,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

type FormState = {
  pathwayKey: string; name: string; country: string; domain: PathwayDomain;
  jurisdictionId: string; description: string; sourceId: string; snapshotId: string;
  ruleIds: string[]; minimumExperience: string; requiredSkills: string;
  qualificationKeywords: string; requiredLanguages: string; minimumFunds: string; requiredEvidence: string;
  requiredDocuments: string; fee: string; currency: string; minimumWeeks: string;
  maximumWeeks: string; benefits: string; risks: string; effectiveFrom: string;
  effectiveTo: string; reviewNotes: string;
};

const EMPTY: FormState = {
  pathwayKey: "", name: "", country: "", domain: "work", jurisdictionId: "",
  description: "", sourceId: "", snapshotId: "", ruleIds: [], minimumExperience: "",
  requiredSkills: "", qualificationKeywords: "", requiredLanguages: "", minimumFunds: "", requiredEvidence: "",
  requiredDocuments: "", fee: "", currency: "EUR", minimumWeeks: "", maximumWeeks: "",
  benefits: "", risks: "", effectiveFrom: "", effectiveTo: "", reviewNotes: "",
};

const splitComma = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);
const splitLines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);
const dateValue = (value?: string | null) => value ? value.slice(0, 10) : "";

function formFromPathway(pathway: MobilityPathwayDetail): FormState {
  const version = pathway.current_version;
  const criteria = version?.eligibility_criteria || {};
  return {
    ...EMPTY,
    pathwayKey: pathway.pathway_key,
    name: pathway.name,
    country: pathway.country,
    domain: pathway.domain,
    jurisdictionId: pathway.jurisdiction_id || "",
    description: pathway.description || "",
    sourceId: version?.official_source_id || "",
    snapshotId: version?.source_snapshot_id || "",
    ruleIds: version?.verified_rule_ids || [],
    minimumExperience: criteria.minimum_years_experience == null ? "" : String(criteria.minimum_years_experience),
    requiredSkills: Array.isArray(criteria.required_skills) ? criteria.required_skills.join(", ") : "",
    qualificationKeywords: Array.isArray(criteria.qualification_keywords) ? criteria.qualification_keywords.join(", ") : "",
    requiredLanguages: Array.isArray(criteria.required_languages) ? criteria.required_languages.join(", ") : "",
    minimumFunds: criteria.minimum_funds_eur == null ? "" : String(criteria.minimum_funds_eur),
    requiredEvidence: Array.isArray(criteria.required_evidence) ? criteria.required_evidence.join(", ") : "",
    requiredDocuments: version?.required_documents.join(", ") || "",
    fee: version?.costs.government_fee == null ? "" : String(version.costs.government_fee),
    currency: String(version?.costs.currency || "EUR"),
    minimumWeeks: version?.processing_time.minimum_weeks == null ? "" : String(version.processing_time.minimum_weeks),
    maximumWeeks: version?.processing_time.maximum_weeks == null ? "" : String(version.processing_time.maximum_weeks),
    benefits: version?.benefits.join("\n") || "",
    risks: version?.risks.join("\n") || "",
    effectiveFrom: dateValue(version?.effective_from),
    effectiveTo: dateValue(version?.effective_to),
    reviewNotes: "",
  };
}

function SectionMarker({ number, title, detail }: { number: string; title: string; detail: string }) {
  return <div className="form-section-title"><span>{number}</span><div><strong>{title}</strong><small>{detail}</small></div></div>;
}

export default function PathwaysPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [pathways, setPathways] = useState<MobilityPathway[]>([]);
  const [selected, setSelected] = useState<MobilityPathwayDetail | null>(null);
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [sources, setSources] = useState<OfficialSourceView[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshotView[]>([]);
  const [rules, setRules] = useState<VerifiedRule[]>([]);
  const [impactQueue, setImpactQueue] = useState<PathwayRegulatoryImpactQueue>({
    total_returned: 0,
    counts_by_status: {},
    pending_review: 0,
    client_assessments_unchanged: true,
    impacts: [],
  });
  const [impactNotes, setImpactNotes] = useState<Record<string, string>>({});
  const [form, setForm] = useState<FormState>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthResult, pathwayRows, jurisdictionRows, sourceRows, snapshotRows, ruleRows, impacts] = await Promise.all([
        getHealthStatus(), listPathways(), listJurisdictions(), listOfficialSources(),
        listSourceSnapshots({ limit: 500 }), listVerifiedRules({ active: true, limit: 500 }),
        listPathwayRegulatoryImpacts({ limit: 200 }),
      ]);
      setHealth(healthResult.data);
      setPathways(pathwayRows);
      setJurisdictions(jurisdictionRows.jurisdictions);
      setSources(sourceRows.sources);
      setSnapshots(snapshotRows.snapshots);
      setRules(ruleRows.verified_rules);
      setImpactQueue(impacts);
      if (selected) {
        const refreshed = await getPathway(selected.id);
        setSelected(refreshed);
        setForm(formFromPathway(refreshed));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load pathway catalogue");
    } finally {
      setLoading(false);
    }
  }, [selected]);

  useEffect(() => { void load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  async function choosePathway(pathwayId: string) {
    setBusy(`select-${pathwayId}`);
    setError(null);
    try {
      const detail = await getPathway(pathwayId);
      setSelected(detail);
      setForm(formFromPathway(detail));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load pathway versions");
    } finally { setBusy(null); }
  }

  function newPathway() { setSelected(null); setForm(EMPTY); setMessage(null); setError(null); }

  function versionPayload(): PathwayVersionInput {
    return {
      official_source_id: form.sourceId || null,
      source_snapshot_id: form.snapshotId || null,
      verified_rule_ids: form.ruleIds,
      eligibility_criteria: {
        ...(form.minimumExperience ? { minimum_years_experience: Number(form.minimumExperience) } : {}),
        required_skills: splitComma(form.requiredSkills),
        qualification_keywords: splitComma(form.qualificationKeywords),
        required_languages: splitComma(form.requiredLanguages),
        ...(form.minimumFunds ? { minimum_funds_eur: Number(form.minimumFunds) } : {}),
        required_evidence: splitComma(form.requiredEvidence),
      },
      required_documents: splitComma(form.requiredDocuments),
      costs: { currency: form.currency || "EUR", ...(form.fee ? { government_fee: Number(form.fee) } : {}) },
      processing_time: {
        ...(form.minimumWeeks ? { minimum_weeks: Number(form.minimumWeeks) } : {}),
        ...(form.maximumWeeks ? { maximum_weeks: Number(form.maximumWeeks) } : {}),
      },
      benefits: splitLines(form.benefits),
      risks: splitLines(form.risks),
      metadata: {},
      effective_from: form.effectiveFrom ? new Date(`${form.effectiveFrom}T00:00:00Z`).toISOString() : null,
      effective_to: form.effectiveTo ? new Date(`${form.effectiveTo}T23:59:59Z`).toISOString() : null,
    };
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy("save"); setError(null); setMessage(null);
    try {
      if (selected) {
        const version = await createPathwayVersion(selected.id, versionPayload());
        setMessage(`Draft version ${version.version_number} created. It remains non-publishable until an operator reviews its evidence.`);
        const detail = await getPathway(selected.id); setSelected(detail); setForm(formFromPathway(detail));
      } else {
        const created = await createPathway({
          ...versionPayload(), pathway_key: form.pathwayKey, name: form.name, country: form.country,
          domain: form.domain, jurisdiction_id: form.jurisdictionId || null, description: form.description || null,
        });
        const detail = await getPathway(created.id); setSelected(detail); setForm(formFromPathway(detail));
        setMessage("Pathway and draft version 1 created.");
      }
      setPathways(await listPathways());
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save pathway draft"); }
    finally { setBusy(null); }
  }

  async function publish() {
    const version = selected?.current_version;
    if (!version || version.lifecycle_status !== "draft") return;
    setBusy("publish"); setError(null); setMessage(null);
    try {
      await publishPathwayVersion(version.id, form.reviewNotes);
      const detail = await getPathway(selected.id); setSelected(detail); setForm(formFromPathway(detail));
      setPathways(await listPathways()); setMessage(`Version ${version.version_number} published with verified evidence provenance.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Publication was rejected"); }
    finally { setBusy(null); }
  }

  async function retire() {
    if (!selected || !form.reviewNotes.trim()) return;
    setBusy("retire"); setError(null);
    try {
      await retirePathway(selected.id, form.reviewNotes);
      const detail = await getPathway(selected.id); setSelected(detail); setForm(formFromPathway(detail));
      setPathways(await listPathways()); setMessage("Pathway retired and removed from matching.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not retire pathway"); }
    finally { setBusy(null); }
  }

  async function reviewImpact(
    impact: PathwayRegulatoryImpact,
    decision: "acknowledged" | "no_change_required" | "new_version_required" | "resolved",
    replacementPathwayVersionId?: string,
  ) {
    const notes = (impactNotes[impact.id] || "").trim();
    if (notes.length < 3) return;
    setBusy(`impact-${impact.id}-${decision}`); setError(null); setMessage(null);
    try {
      await reviewPathwayRegulatoryImpact(impact.id, {
        decision,
        notes,
        replacement_pathway_version_id: replacementPathwayVersionId || null,
      });
      setImpactQueue(await listPathwayRegulatoryImpacts({ limit: 200 }));
      setImpactNotes((currentNotes) => ({ ...currentNotes, [impact.id]: "" }));
      setMessage(
        decision === "resolved"
          ? "Regulatory impact resolved against a newer human-published pathway version."
          : "Regulatory impact review recorded without changing client assessments or pathway criteria."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not review regulatory impact");
    } finally { setBusy(null); }
  }

  const filteredSnapshots = useMemo(() => snapshots.filter((snapshot) => snapshot.official_source_id === form.sourceId), [snapshots, form.sourceId]);
  const filteredRules = useMemo(() => rules.filter((rule) => rule.country.toLowerCase() === form.country.toLowerCase()), [rules, form.country]);
  const counts = {
    active: pathways.filter((item) => item.catalogue_status === "active").length,
    draft: pathways.filter((item) => item.catalogue_status === "draft").length,
    retired: pathways.filter((item) => item.catalogue_status === "retired").length,
    versions: pathways.reduce((total, item) => total + (item.current_version?.version_number || 0), 0),
  };
  const current = selected?.current_version;
  const selectedSource = sources.find((source) => source.id === form.sourceId) || null;
  const selectedSnapshot = snapshots.find((snapshot) => snapshot.id === form.snapshotId) || null;
  const selectedRules = rules.filter((rule) => form.ruleIds.includes(rule.id));
  const supersededVersionCount = selected?.versions.filter((version) => version.lifecycle_status === "superseded").length || 0;
  const publicationEvidenceGaps = [
    form.sourceId ? null : "official source",
    form.snapshotId ? null : "immutable source snapshot",
    form.ruleIds.length ? null : "VerifiedRule",
  ].filter((value): value is string => Boolean(value));
  const pathwayEvidenceProvenance: EvidenceProvenanceItem[] = [
    {
      key: "official-source",
      stage: "Official source",
      title: selectedSource?.name || "No official source selected",
      state: selectedSource ? "Selected" : "Not established",
      detail: selectedSource
        ? `${titleCase(selectedSource.country)} · ${titleCase(selectedSource.domain)}`
        : "A pathway draft may be edited without a source, but publication remains evidence-gated.",
      tone: selectedSource ? "good" : "warn",
    },
    {
      key: "snapshot",
      stage: "Immutable snapshot",
      title: selectedSnapshot ? `Snapshot ${selectedSnapshot.id.slice(0, 8)}` : "No snapshot pinned",
      state: selectedSnapshot ? titleCase(selectedSnapshot.status) : "Not established",
      detail: selectedSnapshot
        ? `Captured ${new Date(selectedSnapshot.captured_at).toLocaleString()}`
        : "The current pathway version has no immutable retrieval pin selected in the editor.",
      meta: selectedSnapshot?.content_hash ? `Hash ${selectedSnapshot.content_hash.slice(0, 16)}…` : undefined,
      tone: selectedSnapshot ? "good" : "warn",
    },
    {
      key: "verified-rules",
      stage: "VerifiedRule",
      title: selectedRules.length ? `${selectedRules.length} human-published rule${selectedRules.length === 1 ? "" : "s"} pinned` : "No VerifiedRule pinned",
      state: selectedRules.length ? "Selected" : "Not established",
      detail: "VerifiedRule records remain distinct from raw source text and snapshots; only their identifiers are attached to the pathway version.",
      meta: selectedRules.length ? selectedRules.map((rule) => rule.rule_key).slice(0, 3).join(" · ") : undefined,
      tone: selectedRules.length ? "good" : "warn",
    },
    {
      key: "pathway-version",
      stage: "Pathway evidence",
      title: selected && current ? `${selected.name} · version ${current.version_number}` : "Draft composition",
      state: current ? titleCase(current.lifecycle_status) : "Not established",
      detail: "The pathway version packages selected source/snapshot/rule evidence with criteria. Drafting never makes it client-facing.",
      tone: current?.lifecycle_status === "published" ? "good" : current ? "warn" : "neutral",
      current: current?.lifecycle_status === "published",
    },
    {
      key: "historical",
      stage: "Superseded / historical",
      title: `${supersededVersionCount} superseded version${supersededVersionCount === 1 ? "" : "s"}`,
      state: supersededVersionCount ? "Historical only" : "None recorded",
      detail: "Superseded pathway versions stay in the immutable version ledger and do not silently replace the selected current version.",
      tone: "neutral",
    },
    {
      key: "gaps",
      stage: "Unresolved gaps",
      title: publicationEvidenceGaps.length ? publicationEvidenceGaps.join(" · ") : "Core publication evidence selected",
      state: publicationEvidenceGaps.length ? "Incomplete" : "Selected",
      detail: "This presentation does not decide publishability; the backend publication gate and explicit human review remain authoritative.",
      tone: publicationEvidenceGaps.length ? "warn" : "good",
    },
  ];
  const loadStatus = loading ? "loading" : health?.status === "ok" ? "ready" : "partial";

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Pathway Catalogue" kicker="Evidence-backed mobility routes" loadStatus={loadStatus} onRefresh={load} />
      <div className="page-pad pathways-page">
        {error && <InlineNotice label="Pathway operation blocked" detail={error} tone="bad" />}
        {message && <InlineNotice label="Catalogue updated" detail={message} tone="good" />}
        <div className="metric-row pathway-metrics">
          <MetricPill label="Catalogue entries" value={pathways.length} />
          <MetricPill label="Published" value={counts.active} tone="good" />
          <MetricPill label="Draft" value={counts.draft} tone="warn" />
          <MetricPill label="Retired" value={counts.retired} />
          <MetricPill label="Total versions" value={counts.versions} />
          <MetricPill label="Evidence rules" value={rules.length} tone="good" />
          <MetricPill label="Pending impacts" value={impactQueue.pending_review} tone={impactQueue.pending_review ? "warn" : "good"} />
        </div>

        <EvidenceProvenance
          title="Source-to-pathway evidence chain"
          detail="Trace the exact official source, immutable retrieval snapshot, human-published rules, pathway version, historical state, and unresolved evidence before relying on a mobility route."
          items={pathwayEvidenceProvenance}
          boundary="This is a presentation of existing evidence pins. Publishing a pathway remains a separate human-reviewed backend action; draft or superseded versions never gain authority from this panel."
        />

        <section className="panel pathway-impact-panel">
          <div className="panel-header-row">
            <SectionTitle
              label="Regulatory impact queue"
              title="Reviewed graph changes linked to exact pathway versions"
              detail="These records never rewrite published criteria, comparisons, timelines, or client conclusions."
            />
            <StatusBadge value={impactQueue.client_assessments_unchanged ? "assessments_unchanged" : "integrity_warning"} />
          </div>
          {impactQueue.impacts.length ? <div className="pathway-impact-list">
            {impactQueue.impacts.map((impact) => {
              const currentPathway = pathways.find((item) => item.id === impact.pathway_id);
              const replacement = currentPathway?.current_version;
              const replacementEligible = Boolean(
                replacement
                && replacement.version_number > impact.pathway_version_number
                && ["published", "superseded"].includes(replacement.lifecycle_status)
              );
              const terminal = ["resolved", "no_change_required"].includes(impact.status);
              return <article key={impact.id} className="pathway-impact-card">
                <div className="pathway-impact-heading">
                  <div>
                    <span className="eyebrow">{titleCase(impact.impact_type)} · {titleCase(impact.materiality)}</span>
                    <strong>{impact.pathway_name} · version {impact.pathway_version_number}</strong>
                    <p>{impact.rule_key} · {titleCase(impact.change_type)}</p>
                  </div>
                  <StatusBadge value={impact.status} />
                </div>
                <div className="pathway-impact-facts">
                  <span>Graph {impact.graph_projection_version}</span>
                  <span>{impact.client_assessment_count_at_detection} pinned comparisons</span>
                  <span>{impact.timeline_count_at_detection} pinned timelines</span>
                  <span>{impact.match_basis.map(titleCase).join(" · ")}</span>
                </div>
                <small>Rule {impact.verified_rule_id.slice(0, 8)} · snapshot {impact.source_snapshot_id.slice(0, 8)} · detected {new Date(impact.event_at).toLocaleString()}</small>
                {!terminal && <div className="pathway-impact-review">
                  <textarea
                    rows={2}
                    value={impactNotes[impact.id] || ""}
                    onChange={(event) => setImpactNotes((currentNotes) => ({ ...currentNotes, [impact.id]: event.target.value }))}
                    placeholder="Record the evidence reviewed and whether a new immutable pathway version is required."
                  />
                  <div className="pathway-editor-actions">
                    <button type="button" className="button secondary small" disabled={(impactNotes[impact.id] || "").trim().length < 3 || Boolean(busy)} onClick={() => void reviewImpact(impact, "acknowledged")}>Acknowledge</button>
                    <button type="button" className="button secondary small" disabled={(impactNotes[impact.id] || "").trim().length < 3 || Boolean(busy)} onClick={() => void reviewImpact(impact, "no_change_required")}>No change required</button>
                    <button type="button" className="button primary small" disabled={(impactNotes[impact.id] || "").trim().length < 3 || Boolean(busy)} onClick={() => void reviewImpact(impact, "new_version_required")}>Require new version</button>
                    {replacementEligible && replacement && <button type="button" className="button primary small" disabled={(impactNotes[impact.id] || "").trim().length < 3 || Boolean(busy)} onClick={() => void reviewImpact(impact, "resolved", replacement.id)}>Resolve with v{replacement.version_number}</button>}
                  </div>
                </div>}
                {impact.review_notes && <p className="pathway-impact-note"><strong>{impact.reviewed_by || "Reviewer"}:</strong> {impact.review_notes}</p>}
              </article>;
            })}
          </div> : <EmptyState title="No regulatory impacts" detail="New human-published rule changes will appear here when they affect a currently published pathway version." />}
        </section>

        <div className="pathway-workspace-grid">
          <section className="panel pathway-list-panel">
            <div className="panel-header-row"><SectionTitle label="Catalogue" title="Mobility routes" detail="Only published versions participate in matching." /><button className="button secondary small" onClick={newPathway}>New pathway</button></div>
            <div className="pathway-list">{pathways.length ? pathways.map((pathway) => <button key={pathway.id} className={`pathway-list-item ${selected?.id === pathway.id ? "selected" : ""}`} onClick={() => void choosePathway(pathway.id)} disabled={busy === `select-${pathway.id}`}><span><StatusBadge value={pathway.catalogue_status} /><small>{titleCase(pathway.domain)} · {titleCase(pathway.country)}</small></span><strong>{pathway.name}</strong><p>Version {pathway.current_version?.version_number || 0} · {titleCase(pathway.current_version?.lifecycle_status || "none")}</p></button>) : <EmptyState title="No pathways" detail="Create the first governed pathway draft." />}</div>
          </section>

          <form className="panel intelligence-form pathway-editor" onSubmit={save}>
            <SectionTitle label={selected ? "New immutable version" : "New catalogue entry"} title={selected?.name || "Create pathway"} detail="Drafting never makes regulated criteria client-facing. Publication is a separate human-reviewed action." />
            <SectionMarker number="01" title="Catalogue identity" detail="Stable route identity and jurisdiction" />
            <div className="pathway-field-grid three">
              <label>Pathway key<input required disabled={Boolean(selected)} value={form.pathwayKey} onChange={(e) => update("pathwayKey", e.target.value.toLowerCase().replace(/\s+/g, "-"))} placeholder="de-skilled-worker" /></label>
              <label>Name<input required disabled={Boolean(selected)} value={form.name} onChange={(e) => update("name", e.target.value)} /></label>
              <label>Domain<select disabled={Boolean(selected)} value={form.domain} onChange={(e) => update("domain", e.target.value as PathwayDomain)}>{["study", "work", "visa", "scholarship", "settlement", "family", "digital_nomad"].map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}</select></label>
              <label>Country<input required disabled={Boolean(selected)} value={form.country} onChange={(e) => update("country", e.target.value)} /></label>
              <label>Jurisdiction<select disabled={Boolean(selected)} value={form.jurisdictionId} onChange={(e) => update("jurisdictionId", e.target.value)}><option value="">No linked jurisdiction</option>{jurisdictions.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label>
              <label className="pathway-wide">Description<textarea disabled={Boolean(selected)} rows={2} value={form.description} onChange={(e) => update("description", e.target.value)} /></label>
            </div>

            <SectionMarker number="02" title="Official evidence" detail="Source, immutable snapshot, and approved rules required for publication" />
            <div className="pathway-field-grid two">
              <label>Official source<select value={form.sourceId} onChange={(e) => { update("sourceId", e.target.value); update("snapshotId", ""); }}><option value="">Select official source</option>{sources.filter((source) => !form.country || source.country.toLowerCase() === form.country.toLowerCase()).map((source) => <option key={source.id} value={source.id}>{source.name} · {source.domain}</option>)}</select></label>
              <label>Source snapshot<select value={form.snapshotId} onChange={(e) => update("snapshotId", e.target.value)}><option value="">Select immutable snapshot</option>{filteredSnapshots.map((snapshot) => <option key={snapshot.id} value={snapshot.id}>{new Date(snapshot.captured_at).toLocaleDateString()} · {snapshot.content_hash?.slice(0, 10) || snapshot.status}</option>)}</select></label>
              <div className="pathway-rule-picker pathway-wide"><span>Verified rules</span>{filteredRules.length ? filteredRules.map((rule) => <label className="profile-check" key={rule.id}><input type="checkbox" checked={form.ruleIds.includes(rule.id)} onChange={(e) => update("ruleIds", e.target.checked ? [...form.ruleIds, rule.id] : form.ruleIds.filter((id) => id !== rule.id))} /><span><strong>{rule.rule_key}</strong><small>{rule.statement}</small></span></label>) : <small>No active verified rules match this country.</small>}</div>
            </div>

            <SectionMarker number="03" title="Eligibility criteria" detail="Deterministic matching inputs; unknown facts become evidence gaps" />
            <div className="pathway-field-grid three">
              <label>Minimum experience<input type="number" min="0" step="0.5" value={form.minimumExperience} onChange={(e) => update("minimumExperience", e.target.value)} /></label>
              <label>Minimum funds<input type="number" min="0" value={form.minimumFunds} onChange={(e) => update("minimumFunds", e.target.value)} /></label>
              <label>Required skills<input value={form.requiredSkills} onChange={(e) => update("requiredSkills", e.target.value)} placeholder="nursing, patient care" /></label>
              <label>Qualification keywords<input value={form.qualificationKeywords} onChange={(e) => update("qualificationKeywords", e.target.value)} placeholder="bachelor, degree" /></label>
              <label>Required languages<input value={form.requiredLanguages} onChange={(e) => update("requiredLanguages", e.target.value)} placeholder="english, german" /></label>
              <label>Required evidence types<input value={form.requiredEvidence} onChange={(e) => update("requiredEvidence", e.target.value)} placeholder="passport, degree" /></label>
              <label>Required documents<input value={form.requiredDocuments} onChange={(e) => update("requiredDocuments", e.target.value)} /></label>
            </div>

            <SectionMarker number="04" title="Cost, timing, benefits, and risk" detail="Structured explanations carried into later planning stages" />
            <div className="pathway-field-grid three">
              <label>Government fee<input type="number" min="0" value={form.fee} onChange={(e) => update("fee", e.target.value)} /></label>
              <label>Currency<input value={form.currency} onChange={(e) => update("currency", e.target.value.toUpperCase())} /></label>
              <label>Minimum weeks<input type="number" min="0" value={form.minimumWeeks} onChange={(e) => update("minimumWeeks", e.target.value)} /></label>
              <label>Maximum weeks<input type="number" min="0" value={form.maximumWeeks} onChange={(e) => update("maximumWeeks", e.target.value)} /></label>
              <label>Effective from<input type="date" value={form.effectiveFrom} onChange={(e) => update("effectiveFrom", e.target.value)} /></label>
              <label>Effective to<input type="date" value={form.effectiveTo} onChange={(e) => update("effectiveTo", e.target.value)} /></label>
              <label className="pathway-wide">Benefits, one per line<textarea rows={3} value={form.benefits} onChange={(e) => update("benefits", e.target.value)} /></label>
              <label className="pathway-wide">Risks, one per line<textarea rows={3} value={form.risks} onChange={(e) => update("risks", e.target.value)} /></label>
            </div>

            <div className="pathway-editor-actions"><button className="button primary" type="submit" disabled={busy === "save"}>{busy === "save" ? "Saving…" : selected ? `Create version ${(current?.version_number || 0) + 1}` : "Create draft version 1"}</button></div>

            {selected && <div className="pathway-governance-box"><div><strong>Current version {current?.version_number}</strong><StatusBadge value={current?.lifecycle_status} /></div><label>Human review notes<textarea rows={3} value={form.reviewNotes} onChange={(e) => update("reviewNotes", e.target.value)} placeholder="Record the evidence checked and publication or retirement rationale." /></label><div className="pathway-editor-actions"><button type="button" className="button primary" disabled={current?.lifecycle_status !== "draft" || form.reviewNotes.trim().length < 3 || busy === "publish"} onClick={() => void publish()}>{busy === "publish" ? "Publishing…" : "Publish reviewed version"}</button><button type="button" className="button secondary" disabled={selected.catalogue_status === "retired" || form.reviewNotes.trim().length < 3 || busy === "retire"} onClick={() => void retire()}>Retire pathway</button></div></div>}
          </form>

          <aside className="panel pathway-history-panel">
            <SectionTitle label="Version ledger" title="Immutable history" detail={selected ? `${selected.versions.length} recorded versions` : "Select a pathway"} />
            {selected ? <div className="pathway-version-list">{selected.versions.map((version: PathwayVersion) => <article key={version.id}><div><strong>Version {version.version_number}</strong><StatusBadge value={version.lifecycle_status} /></div><p>{version.verified_rule_ids.length} rules · {version.required_documents.length} documents</p><small>{new Date(version.created_at).toLocaleString()} · {version.approved_by || version.created_by}</small></article>)}</div> : <EmptyState title="No pathway selected" detail="Choose a catalogue entry to inspect its evidence and history." />}
          </aside>
        </div>
      </div>
    </WorkspaceShell>
  );
}
