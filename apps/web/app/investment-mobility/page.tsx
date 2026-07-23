"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  InvestmentProgram,
  MobilityPathway,
  OfficialSourceView,
  SourceSnapshotView,
  createInvestmentProgram,
  listInvestmentPrograms,
  listOfficialSources,
  listPathways,
  listSourceSnapshots,
  publishInvestmentProgramVersion,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const emptyForm = {
  program_key: "", name: "", country: "", program_type: "residence_by_investment",
  pathway_id: "", official_source_id: "", source_snapshot_id: "", minimum_commitment: "",
  currency: "EUR", investment_options: "", holding_period_text: "", physical_presence_text: "",
  family_scope: "spouse\ndependent children", due_diligence: "lawful source of funds\nidentity and criminal record review\nsanctions screening",
  fees: "", benefits: "", risks: "capital at risk\nprogram rules and qualifying assets can change", description: "",
};

type ProgramForm = typeof emptyForm;

function lines(value: string) { return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean); }

export default function InvestmentMobilityPage() {
  const { health } = useBackendStatus();
  const [programs, setPrograms] = useState<InvestmentProgram[]>([]);
  const [pathways, setPathways] = useState<MobilityPathway[]>([]);
  const [sources, setSources] = useState<OfficialSourceView[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshotView[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [form, setForm] = useState<ProgramForm>(emptyForm);
  const [reviewNotes, setReviewNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [programRows, activePathways, sourceRows] = await Promise.all([
        listInvestmentPrograms(), listPathways({ catalogue_status: "active" }), listOfficialSources(),
      ]);
      setPrograms(programRows);
      setPathways(activePathways.filter((item) => ["investment", "wealth", "business", "entrepreneur"].includes(item.domain)));
      setSources(sourceRows.sources.filter((item) => item.active));
      setSelectedId((current) => current || programRows[0]?.id || "");
    } catch (err) { setError(err instanceof Error ? err.message : "Investment programme catalogue could not be loaded"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!form.official_source_id) { setSnapshots([]); return; }
    void listSourceSnapshots({ source_id: form.official_source_id, limit: 100 })
      .then((result) => setSnapshots(result.snapshots.filter((item) => Boolean(item.content_hash))))
      .catch((err) => setError(err instanceof Error ? err.message : "Source snapshots could not be loaded"));
  }, [form.official_source_id]);

  const selected = programs.find((item) => item.id === selectedId) || programs[0] || null;
  const selectedPathway = pathways.find((item) => item.id === form.pathway_id) || null;
  const countrySources = useMemo(() => sources.filter((source) => !form.country || source.country.toLowerCase() === form.country.toLowerCase()), [sources, form.country]);
  const publishedCount = programs.filter((item) => item.catalogue_status === "active").length;

  function update<K extends keyof ProgramForm>(key: K, value: ProgramForm[K]) { setForm((current) => ({ ...current, [key]: value })); }

  function choosePathway(pathwayId: string) {
    const pathway = pathways.find((item) => item.id === pathwayId);
    setForm((current) => ({ ...current, pathway_id: pathwayId, country: pathway?.country || current.country }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setWorking("create"); setError(null); setMessage(null);
    try {
      if (!selectedPathway?.current_version) throw new Error("Select a pathway with a published current version");
      const created = await createInvestmentProgram({
        program_key: form.program_key, name: form.name, country: form.country,
        program_type: form.program_type as "residence_by_investment" | "citizenship_by_investment" | "investor_entrepreneur",
        pathway_id: form.pathway_id, description: form.description || undefined,
        pathway_version_id: selectedPathway.current_version.id,
        official_source_id: form.official_source_id, source_snapshot_id: form.source_snapshot_id,
        minimum_commitment_minor: Math.round(Number(form.minimum_commitment) * 100), currency: form.currency.toUpperCase(),
        investment_options: lines(form.investment_options).map((type) => ({ type })),
        holding_period_text: form.holding_period_text || undefined,
        physical_presence_text: form.physical_presence_text || undefined,
        family_scope: lines(form.family_scope), due_diligence: lines(form.due_diligence),
        fees: form.fees ? { notes: form.fees } : {}, benefits: lines(form.benefits), risks: lines(form.risks),
      });
      setPrograms((current) => [created, ...current]); setSelectedId(created.id); setForm(emptyForm);
      setMessage("Draft created from a published pathway and pinned source snapshot. A different reviewer must publish it.");
    } catch (err) { setError(err instanceof Error ? err.message : "Investment program could not be created"); }
    finally { setWorking(null); }
  }

  async function publish() {
    if (!selected?.current_version) return;
    setWorking("publish"); setError(null); setMessage(null);
    try {
      const updated = await publishInvestmentProgramVersion(selected.current_version.id, reviewNotes);
      setPrograms((current) => current.map((item) => item.id === updated.id ? updated : item));
      setReviewNotes(""); setMessage("The independently reviewed version is now available to Business & Wealth advisory grounding.");
    } catch (err) { setError(err instanceof Error ? err.message : "Program version could not be published"); }
    finally { setWorking(null); }
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Investment Programs" kicker="Phase 11 · Source-controlled programme intelligence" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />

      <section className="investment-hero">
        <div><span className="eyebrow">Governed investment mobility</span><h2>Verified programs, not sales promises.</h2><p>Pin every threshold, route, family condition, due-diligence requirement, benefit, and risk to a published pathway and an immutable official-source snapshot.</p></div>
        <div className="investment-hero-metrics"><div><strong>{programs.length}</strong><span>Catalogue entries</span></div><div><strong>{publishedCount}</strong><span>Published</span></div><div><strong>{programs.length - publishedCount}</strong><span>Awaiting review</span></div></div>
      </section>

      {error ? <InlineNotice label="Catalogue action stopped" detail={error} tone="bad" /> : null}
      {message ? <InlineNotice label="Catalogue updated" detail={message} tone="good" /> : null}

      <div className="investment-layout">
        <section className="panel investment-ledger">
          <header className="advisory-panel-head"><div><span className="eyebrow">Programme ledger</span><h3>Controlled entries</h3></div><span>{programs.length} total</span></header>
          <div className="investment-list">
            {programs.length ? programs.map((program) => (
              <button type="button" className={selected?.id === program.id ? "active" : ""} onClick={() => setSelectedId(program.id)} key={program.id}>
                <span><strong>{program.name}</strong><small>{titleCase(program.country)} · {titleCase(program.program_type)}</small></span>
                <StatusBadge value={program.catalogue_status} />
              </button>
            )) : <div className="investment-empty"><strong>No investment programs</strong><span>Create the first source-grounded draft.</span></div>}
          </div>
        </section>

        <section className="investment-detail">
          {selected ? <ProgramDetail program={selected} reviewNotes={reviewNotes} setReviewNotes={setReviewNotes} publish={publish} working={working} /> : (
            <div className="panel investment-empty-detail"><span className="eyebrow">No programme selected</span><h3>Published intelligence will appear here.</h3><p>The catalogue never treats capital alone as eligibility and never expresses authority outcomes as guarantees.</p></div>
          )}
        </section>
      </div>

      <details className="panel investment-create">
        <summary><span><small>New catalogue entry</small><strong>Create source-grounded program</strong></span><b>+</b></summary>
        <form onSubmit={submit}>
          <div className="investment-form-grid">
            <label className="advisory-field"><span>Program key</span><input required pattern="[a-z0-9][a-z0-9_-]+" value={form.program_key} onChange={(e) => update("program_key", e.target.value)} placeholder="pt-investor-route" /></label>
            <label className="advisory-field"><span>Program name</span><input required value={form.name} onChange={(e) => update("name", e.target.value)} /></label>
            <label className="advisory-field"><span>Program type</span><select value={form.program_type} onChange={(e) => update("program_type", e.target.value)}><option value="residence_by_investment">Residence by investment</option><option value="citizenship_by_investment">Citizenship by investment</option><option value="investor_entrepreneur">Investor entrepreneur</option></select></label>
            <label className="advisory-field"><span>Published mobility pathway</span><select required value={form.pathway_id} onChange={(e) => choosePathway(e.target.value)}><option value="">Select pathway</option>{pathways.map((item) => <option value={item.id} key={item.id}>{item.name} · {titleCase(item.country)}</option>)}</select></label>
            <label className="advisory-field"><span>Country</span><input required readOnly value={form.country} /></label>
            <label className="advisory-field"><span>Official source</span><select required value={form.official_source_id} onChange={(e) => update("official_source_id", e.target.value)}><option value="">Select official source</option>{countrySources.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
            <label className="advisory-field"><span>Content-addressed snapshot</span><select required value={form.source_snapshot_id} onChange={(e) => update("source_snapshot_id", e.target.value)}><option value="">Select snapshot</option>{snapshots.map((item) => <option value={item.id} key={item.id}>{new Date(item.captured_at).toLocaleDateString()} · {item.content_hash?.slice(0, 10)}</option>)}</select></label>
            <label className="advisory-field"><span>Minimum commitment</span><input required type="number" min="0" step="0.01" value={form.minimum_commitment} onChange={(e) => update("minimum_commitment", e.target.value)} /></label>
            <label className="advisory-field"><span>Currency</span><input required minLength={3} maxLength={3} value={form.currency} onChange={(e) => update("currency", e.target.value)} /></label>
            <label className="advisory-field"><span>Investment options</span><textarea required rows={3} value={form.investment_options} onChange={(e) => update("investment_options", e.target.value)} placeholder="One qualifying option per line" /></label>
            <label className="advisory-field"><span>Due diligence</span><textarea required rows={3} value={form.due_diligence} onChange={(e) => update("due_diligence", e.target.value)} /></label>
            <label className="advisory-field"><span>Family scope</span><textarea rows={3} value={form.family_scope} onChange={(e) => update("family_scope", e.target.value)} /></label>
            <label className="advisory-field"><span>Benefits</span><textarea rows={3} value={form.benefits} onChange={(e) => update("benefits", e.target.value)} /></label>
            <label className="advisory-field"><span>Risks</span><textarea required rows={3} value={form.risks} onChange={(e) => update("risks", e.target.value)} /></label>
            <label className="advisory-field"><span>Holding period</span><textarea rows={2} value={form.holding_period_text} onChange={(e) => update("holding_period_text", e.target.value)} /></label>
            <label className="advisory-field"><span>Physical presence</span><textarea rows={2} value={form.physical_presence_text} onChange={(e) => update("physical_presence_text", e.target.value)} /></label>
            <label className="advisory-field"><span>Fee notes</span><textarea rows={2} value={form.fees} onChange={(e) => update("fees", e.target.value)} /></label>
            <label className="advisory-field"><span>Description</span><textarea rows={2} value={form.description} onChange={(e) => update("description", e.target.value)} /></label>
          </div>
          <button className="button primary" disabled={working === "create"}>{working === "create" ? "Creating draft…" : "Create controlled draft"}</button>
        </form>
      </details>
    </WorkspaceShell>
  );
}

function ProgramDetail({ program, reviewNotes, setReviewNotes, publish, working }: { program: InvestmentProgram; reviewNotes: string; setReviewNotes: (value: string) => void; publish: () => void; working: string | null }) {
  const version = program.current_version;
  if (!version) return null;
  return <div className="panel investment-program-card">
    <header><div><span className="eyebrow">{titleCase(program.program_type)}</span><h2>{program.name}</h2><p>{titleCase(program.country)} · version {version.version_number}</p></div><StatusBadge value={version.lifecycle_status} /></header>
    <div className="investment-threshold"><span>Minimum recorded commitment</span><strong>{new Intl.NumberFormat("en", { style: "currency", currency: version.currency, maximumFractionDigits: 0 }).format(version.minimum_commitment_minor / 100)}</strong><small>Threshold only; not a qualification or investment recommendation.</small></div>
    <div className="investment-facts"><Fact title="Qualifying structures" items={version.investment_options.map((item) => String(item.type || "Recorded option"))} /><Fact title="Due diligence" items={version.due_diligence} /><Fact title="Family scope" items={version.family_scope} /><Fact title="Material risks" items={version.risks} /></div>
    <div className="investment-provenance"><div><span>Pathway version</span><code>{version.pathway_version_id}</code></div><div><span>Source snapshot</span><code>{version.source_snapshot_id}</code></div><div><span>Independent reviewer</span><strong>{version.approved_by || "Pending"}</strong></div></div>
    {version.lifecycle_status === "draft" ? <div className="investment-review"><label className="advisory-field"><span>Independent review notes</span><textarea minLength={10} rows={3} value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} placeholder="Record how the pathway, source snapshot, threshold, conditions, and risks were verified." /></label><button className="button secondary" type="button" disabled={working === "publish" || reviewNotes.trim().length < 10} onClick={publish}>{working === "publish" ? "Publishing…" : "Publish as independent reviewer"}</button><small>The API rejects publication by the original proposer.</small></div> : null}
  </div>;
}

function Fact({ title, items }: { title: string; items: string[] }) {
  return <section><span>{title}</span>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p>Not recorded</p>}</section>;
}
