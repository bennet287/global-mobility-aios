"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AgentReviewDashboard,
  ControlledAgentsList,
  getAgentReviewDashboard,
  getControlledAgents,
  getHealthStatus,
  getLeads,
  HealthStatus,
  Lead,
  runControlledAgent,
  runControlledAgentBatch,
} from "../../../lib/api";
import { EmptyState } from "../../../components/EmptyState";
import { InlineNotice } from "../../../components/InlineNotice";
import { SectionTitle } from "../../../components/SectionTitle";
import { StatusBadge } from "../../../components/StatusBadge";
import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { titleCase } from "../../../lib/utils";

export default function AgentConsolePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [agents, setAgents] = useState<ControlledAgentsList | null>(null);
  const [dashboard, setDashboard] = useState<AgentReviewDashboard | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [agentName, setAgentName] = useState<string>("");
  const [taskTemplate, setTaskTemplate] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const agentEntries = useMemo(() => {
    if (!agents) return [];
    return Object.entries(agents.agents).map(([name, meta]) => ({ name, ...meta }));
  }, [agents]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [leadsData, agentsData, dashboardData, healthData] = await Promise.all([
          getLeads(),
          getControlledAgents(),
          getAgentReviewDashboard({ status: "all" }),
          getHealthStatus(),
        ]);
        if (cancelled) return;
        setLeads(leadsData);
        setAgents(agentsData);
        setDashboard(dashboardData);
        setHealth(healthData.data);
        const firstAgent = Object.keys(agentsData.agents)[0];
        if (firstAgent) setAgentName(firstAgent);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load console data");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleLead = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === leads.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(leads.map((l) => l.id)));
    }
  };

  const handleRunSingle = async (leadId: string) => {
    if (!agentName || !taskTemplate.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runControlledAgent({
        agent_name: agentName,
        task: taskTemplate,
        lead_id: leadId,
        actor: "operator_console",
      });
      setResult(`Run ${res.run_id} created with status ${res.status}.`);
      refreshDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRunBatch = async () => {
    if (!agentName || selected.size === 0 || !taskTemplate.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runControlledAgentBatch({
        agent_name: agentName,
        lead_ids: Array.from(selected),
        task_template: taskTemplate,
        actor: "operator_console",
      });
      setResult(`Batch ${res.batch_id} queued ${res.queued} run(s).`);
      setSelected(new Set());
      refreshDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch run failed");
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = async () => {
    try {
      const data = await getAgentReviewDashboard({ status: "all" });
      setDashboard(data);
    } catch {
      // ignore refresh errors
    }
  };

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Agent Console" kicker="Controlled agents" loadStatus={loading ? "loading" : "ready"} onRefresh={refreshDashboard} />
      <div className="agent-console-grid">
        <section className="panel agent-console-form">
          <SectionTitle
            label="Manual"
            title="Run agent manually"
            detail="Select one or more leads, choose a controlled agent, and submit a task. All outputs go to the review queue."
          />
          {error && <InlineNotice label="Error" detail={error} />}
          {result && <InlineNotice label="Success" detail={result} />}

          <div className="agent-form">
            <label className="full-field">
              <span>Agent</span>
              <select value={agentName} onChange={(e) => setAgentName(e.target.value)}>
                {agentEntries.map((agent) => (
                  <option key={agent.name} value={agent.name}>
                    {titleCase(agent.name)} — {agent.role}
                  </option>
                ))}
              </select>
            </label>

            <label className="full-field">
              <span>Task template</span>
              <textarea
                value={taskTemplate}
                onChange={(e) => setTaskTemplate(e.target.value)}
                placeholder="e.g. Draft a follow-up email summarizing the current status"
                rows={3}
              />
            </label>

            <div className="form-actions full-field">
              <button
                className="button primary"
                disabled={loading || selected.size === 0 || !taskTemplate.trim()}
                onClick={handleRunBatch}
              >
                {loading ? "Running..." : `Run for ${selected.size} selected lead(s)`}
              </button>
              <button
                className="button secondary"
                disabled={loading || selected.size !== 1 || !taskTemplate.trim()}
                onClick={() => handleRunSingle(Array.from(selected)[0])}
              >
                Run for single lead
              </button>
            </div>
          </div>

          <div className="agent-safety-note">
            <strong>Safety mode</strong>
            <p>Automatic sending and auto-conversion are disabled. Every output requires human review.</p>
          </div>
        </section>

        <section className="panel agent-console-leads">
          <div className="panel-header-row">
            <SectionTitle label="Leads" title="Leads" detail={`${leads.length} total`} />
            <button className="button secondary" onClick={toggleAll}>
              {selected.size === leads.length && leads.length > 0 ? "Deselect all" : "Select all"}
            </button>
          </div>
          {leads.length === 0 ? (
            <EmptyState title="No leads" detail="Create a lead from the dashboard first." />
          ) : (
            <div className="agent-lead-list">
              {leads.map((lead) => (
                <label key={lead.id} className="agent-lead-row">
                  <input
                    type="checkbox"
                    checked={selected.has(lead.id)}
                    onChange={() => toggleLead(lead.id)}
                  />
                  <span className="lead-identity">
                    <span>{lead.full_name.charAt(0)}</span>
                    <span>
                      <strong>{lead.full_name}</strong>
                      <small>
                        {lead.email || "no email"} · {lead.target_country || "no country"} · {lead.intent}
                      </small>
                    </span>
                  </span>
                  <StatusBadge value={lead.status} />
                </label>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="panel agent-console-runs">
        <SectionTitle label="History" title="Recent agent runs" detail="Outputs from the review dashboard" />
        {!dashboard || dashboard.items.length === 0 ? (
          <EmptyState title="No runs" detail="No agent runs yet." />
        ) : (
          <div className="agent-runs-table">
            <div className="agent-runs-head">
              <span>Run</span>
              <span>Agent</span>
              <span>Lead</span>
              <span>Status</span>
              <span>Summary</span>
              <span>Action</span>
            </div>
            {dashboard.items.slice(0, 20).map((run) => (
              <div key={run.id} className="agent-runs-row">
                <span className="monospace">{run.id.slice(0, 8)}</span>
                <span>{titleCase(run.agent_name)}</span>
                <span>{run.lead_id ? run.lead_id.slice(0, 8) : "—"}</span>
                <span>
                  <StatusBadge value={run.status} />
                </span>
                <span className="run-summary">{run.summary}</span>
                <span>
                  <Link href={`/agents/review?status=all&lead_id=${run.lead_id || ""}`} className="button secondary">
                    Review
                  </Link>
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}
