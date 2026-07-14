"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { MetricPill } from "../../components/MetricPill";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import {
  createPathway,
  createPathwayVersion,
  getHealthStatus,
  getPathway,
  HealthStatus,
  Jurisdiction,
  listJurisdictions,
  listOfficialSources,
  listPathways,
  listSourceSnapshots,
  listVerifiedRules,
  MobilityPathway,
  MobilityPathwayDetail,
  OfficialSourceView,
  PathwayDomain,
  PathwayVersion,
  PathwayVersionInput,
  publishPathwayVersion,
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
      const [healthResult, pathwayRows, jurisdictionRows, sourceRows, snapshotRows, ruleRows] = await Promise.all([
        getHealthStatus(), listPathways(), listJurisdictions(), listOfficialSources(),
        listSourceSnapshots({ limit: 500 }), listVerifiedRules({ active: true, limit: 500 }),
      ]);
      setHealth(healthResult.data);
      setPathways(pathwayRows);
      setJurisdictions(jurisdictionRows.jurisdictions);
      setSources(sourceRows.sources);
      setSnapshots(snapshotRows.snapshots);
      setRules(ruleRows.verified_rules);
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

  const filteredSnapshots = useMemo(() => snapshots.filter((snapshot) => snapshot.official_source_id === form.sourceId), [snapshots, form.sourceId]);
  const filteredRules = useMemo(() => rules.filter((rule) => rule.country.toLowerCase() === form.country.toLowerCase()), [rules, form.country]);
  const counts = {
    active: pathways.filter((item) => item.catalogue_status === "active").length,
    draft: pathways.filter((item) => item.catalogue_status === "draft").length,
    retired: pathways.filter((item) => item.catalogue_status === "retired").length,
    versions: pathways.reduce((total, item) => total + (item.current_version?.version_number || 0), 0),
  };
  const current = selected?.current_version;
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
        </div>

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
