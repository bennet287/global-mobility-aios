"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { InlineNotice } from "../../components/InlineNotice";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { BoardPacketSnapshot, decideBoardItem, getBoardPacket, updateOrganizationControl } from "../../lib/api";
import { titleCase } from "../../lib/utils";

const executiveAcronyms = new Set(["cco", "cfo", "clo", "cmo", "coo", "chro", "cpo", "ciso", "cto"]);

function executivePositionLabel(positionKey: string): string {
  const normalized = positionKey.toLowerCase();
  return executiveAcronyms.has(normalized) ? normalized.toUpperCase() : titleCase(positionKey);
}

export default function BoardRoomPage() {
  const { health } = useBackendStatus();
  const [packet, setPacket] = useState<BoardPacketSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setPacket(await getBoardPacket()); }
    catch (err) { setError(err instanceof Error ? err.message : "Board packet could not be loaded"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  const executives = useMemo(() => packet?.positions.filter((position) => position.reports_to_position_key === "ceo") || [], [packet]);

  async function toggleControl() {
    if (!packet) return;
    const next = packet.control.status === "active" ? "paused" : "active";
    setWorking("control"); setError(null); setMessage(null);
    try {
      await updateOrganizationControl(next, next === "paused" ? "Human Board paused autonomous execution." : "Human Board resumed governed execution.");
      setMessage(next === "paused" ? "Autonomous execution is paused. Queued work is preserved." : "Governed autonomous execution resumed.");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Organization control could not be changed"); }
    finally { setWorking(null); }
  }

  async function decide(id: string, outcome: "approved" | "rejected" | "returned") {
    const reason = window.prompt(`Record the Board rationale for ${outcome}:`);
    if (!reason || reason.trim().length < 8) return;
    setWorking(id); setError(null); setMessage(null);
    try {
      await decideBoardItem(id, outcome, reason.trim());
      setMessage(`Board decision recorded: ${outcome}.`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Board decision could not be recorded"); }
    finally { setWorking(null); }
  }

  return <WorkspaceShell health={health}>
    <Topbar title="Board Room" kicker="Phase 13 · Human-owned AI organization" loadStatus={loading ? "loading" : error ? "partial" : "ready"} onRefresh={() => void load()} />

    <section className="board-hero">
      <div>
        <span className="eyebrow">Board control plane</span>
        <h2>One organization.<br />One accountable chain.</h2>
        <p>The CEO coordinates the executive team. Authority boundaries, risks, decisions, delegations, and outcomes remain visible to the human owner.</p>
      </div>
      <div className="board-control-card">
        <span>Autonomous runtime</span>
        <strong className={packet?.control.status === "paused" ? "paused" : "active"}>{packet?.control.status || "loading"}</strong>
        <p>{packet?.control.reason || "Governed event processing is enabled."}</p>
        <button className="button" disabled={!packet || working === "control"} onClick={() => void toggleControl()}>
          {packet?.control.status === "active" ? "Pause organization" : "Resume organization"}
        </button>
      </div>
    </section>

    {error ? <InlineNotice label="Board Room unavailable" detail={error} tone="bad" /> : null}
    {message ? <InlineNotice label="Board action recorded" detail={message} tone="good" /> : null}

    <section className="board-metrics" aria-label="Organization status">
      {([
        ["Active positions", packet?.metrics.active_positions ?? 0],
        ["Queued work", packet?.metrics.queued_work ?? 0],
        ["CEO decisions", packet?.metrics.pending_ceo ?? 0],
        ["Board decisions", packet?.metrics.pending_board ?? 0],
        ["Open risks", packet?.metrics.open_risks ?? 0],
      ] as const).map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
    </section>

    <section className="panel organization-chart">
      <header><div><span className="eyebrow">Accountability map</span><h3>Human Board → CEO → executive departments</h3></div><small>Role cards + runtime positions</small></header>
      <div className="org-board-node"><span>Human owner</span><strong>Board</strong><small>L4 · reserved authority</small></div>
      <div className="org-connector" />
      <div className="org-ceo-node"><span>Executive integrator</span><strong>CEO Agent</strong><small>L3 · reports to Board</small></div>
      <div className="org-executives">
        {executives.map((position) => <article key={position.id}><span>{position.department}</span><strong>{executivePositionLabel(position.position_key)}</strong><small>{position.authority_level} · {position.role_card_name}</small></article>)}
      </div>
    </section>

    <div className="board-grid">
      <section className="panel board-decisions">
        <header><div><span className="eyebrow">Owner attention</span><h3>Decision inbox</h3></div><strong>{packet?.pending_decisions.length ?? 0}</strong></header>
        {!packet?.pending_decisions.length ? <div className="board-empty"><strong>No Board decisions waiting</strong><span>The CEO continues within its delegated authority.</span></div> : packet.pending_decisions.map((decision) => <article key={decision.id}>
          <div><span>{decision.authority_level} · {decision.decision_owner_position}</span><h4>{decision.title}</h4><p>{decision.recommendation}</p></div>
          {decision.status === "pending_board" ? <div className="board-decision-actions">
            <button disabled={working === decision.id} onClick={() => void decide(decision.id, "approved")}>Approve</button>
            <button disabled={working === decision.id} onClick={() => void decide(decision.id, "returned")}>Return</button>
            <button disabled={working === decision.id} onClick={() => void decide(decision.id, "rejected")}>Reject</button>
          </div> : <span className="board-ceo-badge">CEO action</span>}
        </article>)}
      </section>

      <section className="panel board-risks">
        <header><div><span className="eyebrow">Exceptions</span><h3>Risk escalations</h3></div><strong>{packet?.open_risks.length ?? 0}</strong></header>
        {!packet?.open_risks.length ? <div className="board-empty"><strong>No material exceptions</strong><span>Routine work remains inside governed lanes.</span></div> : packet.open_risks.map((risk) => <article key={risk.id}><span>{risk.severity} · {risk.category}</span><h4>{risk.title}</h4><p>{risk.description}</p><small>Escalated to {risk.escalated_to_position_key}</small></article>)}
      </section>
    </div>

    <section className="panel board-workstream">
      <header><div><span className="eyebrow">Operating pulse</span><h3>Recent organizational work</h3></div><small>Event-driven and auditable</small></header>
      <div className="board-work-rows">
        {!packet?.recent_work.length ? <div className="board-empty"><strong>No work routed yet</strong><span>Governed automation events will enter the COO lane here.</span></div> : packet.recent_work.map((work) => <article key={work.id}><div><span>{work.department} · {work.authority_level}</span><strong>{work.title}</strong></div><div><small>{work.assigned_position_key}</small><b>{work.status}</b></div></article>)}
      </div>
    </section>
  </WorkspaceShell>;
}
