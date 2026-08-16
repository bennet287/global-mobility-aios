"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  BoardPacketSnapshot,
  OrganizationPosition,
  GlobalIntelligenceDashboard,
  OrganizationActivity,
  OrganizationHumanActionRequest,
  ObservatoryDepartments,
  ObservatorySummary,
  getBoardPacket,
  getGlobalIntelligenceDashboard,
  getOrganizationObservatoryDepartments,
  getOrganizationObservatorySummary,
  listOrganizationActivities,
  listOrganizationHumanActionRequests,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

type GeographicPoint = { lat: number; lon: number };
type OrganizationFocus = { kind: "ceo" | "executive" | "domain"; key: string };

const ACTIVE_HUMAN_REQUEST_STATUSES = new Set(["required", "acknowledged", "in_progress"]);

const JURISDICTION_CENTROIDS: Record<string, GeographicPoint> = {
  AT: { lat: 47.52, lon: 14.55 }, DE: { lat: 51.17, lon: 10.45 }, CH: { lat: 46.82, lon: 8.23 },
  FR: { lat: 46.23, lon: 2.21 }, GB: { lat: 55.38, lon: -3.44 }, IE: { lat: 53.14, lon: -7.69 },
  NL: { lat: 52.13, lon: 5.29 }, BE: { lat: 50.50, lon: 4.47 }, IT: { lat: 41.87, lon: 12.57 },
  ES: { lat: 40.46, lon: -3.75 }, PT: { lat: 39.40, lon: -8.22 }, PL: { lat: 51.92, lon: 19.15 },
  CZ: { lat: 49.82, lon: 15.47 }, SK: { lat: 48.67, lon: 19.70 }, HU: { lat: 47.16, lon: 19.50 },
  RO: { lat: 45.94, lon: 24.97 }, SE: { lat: 60.13, lon: 18.64 }, NO: { lat: 60.47, lon: 8.47 },
  DK: { lat: 56.26, lon: 9.50 }, FI: { lat: 61.92, lon: 25.75 }, CA: { lat: 56.13, lon: -106.35 },
  US: { lat: 37.09, lon: -95.71 }, MX: { lat: 23.63, lon: -102.55 }, BR: { lat: -14.24, lon: -51.93 },
  IN: { lat: 20.59, lon: 78.96 }, AE: { lat: 23.42, lon: 53.85 }, SG: { lat: 1.35, lon: 103.82 },
  JP: { lat: 36.20, lon: 138.25 }, KR: { lat: 35.91, lon: 127.77 }, AU: { lat: -25.27, lon: 133.78 },
  NZ: { lat: -40.90, lon: 174.89 }, ZA: { lat: -30.56, lon: 22.94 },
};

const EXECUTIVE_ROLE_LABELS: Record<string, string> = {
  coo: "COO",
  cto: "CTO",
  ciso: "CISO",
  cpo: "CPO",
  cfo: "CFO",
  clo: "CLO",
  cmo: "CMO",
  cco: "CCO",
  chro: "CHRO",
};

const EXECUTIVE_ROLE_ORDER = ["coo", "cto", "ciso", "cpo", "cfo", "clo", "cmo", "cco", "chro"];

function executiveRoleLabel(position: OrganizationPosition): string {
  return EXECUTIVE_ROLE_LABELS[position.position_key] || position.position_key.replaceAll("_", " ").toUpperCase();
}

function cleanExecutiveTitle(title: string): string {
  return title.replace(/\s+Agent$/i, "");
}

function timeLabel(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(date);
}

function dateLabel(value?: string | null): string {
  if (!value) return "Not established";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not established";
  return new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function projectPoint(point: GeographicPoint) {
  return {
    left: `${((point.lon + 180) / 360) * 100}%`,
    top: `${((90 - point.lat) / 180) * 100}%`,
  };
}

export default function CockpitPage() {
  const { health, error: healthError } = useBackendStatus();
  const [packet, setPacket] = useState<BoardPacketSnapshot | null>(null);
  const [observatory, setObservatory] = useState<ObservatorySummary | null>(null);
  const [departmentObservatory, setDepartmentObservatory] = useState<ObservatoryDepartments | null>(null);
  const [intelligence, setIntelligence] = useState<GlobalIntelligenceDashboard | null>(null);
  const [activities, setActivities] = useState<OrganizationActivity[]>([]);
  const [humanRequests, setHumanRequests] = useState<OrganizationHumanActionRequest[]>([]);
  const [organizationFocus, setOrganizationFocus] = useState<OrganizationFocus>({ kind: "ceo", key: "ceo" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      getBoardPacket(),
      getOrganizationObservatorySummary(),
      getOrganizationObservatoryDepartments(),
      getGlobalIntelligenceDashboard(90),
      listOrganizationActivities({ page_size: 20 }),
      listOrganizationHumanActionRequests({ page_size: 50 }),
    ]);

    const failures: string[] = [];
    const [packetResult, observatoryResult, departmentsResult, intelligenceResult, activityResult, humanRequestResult] = results;

    if (packetResult.status === "fulfilled") setPacket(packetResult.value);
    else failures.push("organization control");

    if (observatoryResult.status === "fulfilled") setObservatory(observatoryResult.value);
    else failures.push("observatory");

    if (departmentsResult.status === "fulfilled") setDepartmentObservatory(departmentsResult.value);
    else failures.push("department observatory");

    if (intelligenceResult.status === "fulfilled") setIntelligence(intelligenceResult.value);
    else failures.push("global intelligence");

    if (activityResult.status === "fulfilled") setActivities(activityResult.value.data);
    else failures.push("activity stream");

    if (humanRequestResult.status === "fulfilled") setHumanRequests(humanRequestResult.value.data);
    else failures.push("human attention records");

    if (failures.length) setError(`Some Cockpit signals are temporarily unavailable: ${failures.join(", ")}.`);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const executivePositions = useMemo(() => {
    const order = new Map(EXECUTIVE_ROLE_ORDER.map((key, index) => [key, index]));
    return (packet?.positions || [])
      .filter((position) => position.reports_to_position_key === "ceo" && position.authority_level === "L3")
      .sort((a, b) => (order.get(a.position_key) ?? 99) - (order.get(b.position_key) ?? 99) || a.position_key.localeCompare(b.position_key));
  }, [packet]);

  const operationalDomains = useMemo(() => {
    const positions = packet?.positions || [];
    const byKey = new Map(positions.map((position) => [position.position_key, position]));
    const executiveKeys = new Set(executivePositions.map((position) => position.position_key));
    const groups = new Map<string, { positions: number; ownerKeys: Set<string> }>();

    const executiveOwner = (position: OrganizationPosition): string | null => {
      let current: OrganizationPosition | undefined = position;
      const visited = new Set<string>();
      while (current?.reports_to_position_key && !visited.has(current.position_key)) {
        visited.add(current.position_key);
        const parent = byKey.get(current.reports_to_position_key);
        if (!parent) return null;
        if (executiveKeys.has(parent.position_key)) return parent.position_key;
        if (parent.position_key === "ceo" || parent.position_key === "board") return null;
        current = parent;
      }
      return null;
    };

    for (const position of positions) {
      if (!position.department || position.position_key === "board" || position.position_key === "ceo" || executiveKeys.has(position.position_key)) continue;
      const group = groups.get(position.department) || { positions: 0, ownerKeys: new Set<string>() };
      group.positions += 1;
      const owner = executiveOwner(position);
      if (owner) group.ownerKeys.add(owner);
      groups.set(position.department, group);
    }

    return [...groups.entries()]
      .map(([department, value]) => ({ department, positions: value.positions, ownerKeys: [...value.ownerKeys] }))
      .sort((a, b) => b.positions - a.positions || a.department.localeCompare(b.department));
  }, [executivePositions, packet]);

  const executivePortfolios = useMemo(() => {
    return executivePositions.map((position) => {
      const domains = operationalDomains.filter((domain) => domain.ownerKeys.includes(position.position_key));
      return {
        position,
        domains,
        downstreamPositions: domains.reduce((total, domain) => total + domain.positions, 0),
      };
    });
  }, [executivePositions, operationalDomains]);

  const organizationFocusView = useMemo(() => {
    const positions = packet?.positions || [];
    const byKey = new Map(positions.map((position) => [position.position_key, position]));
    const departmentRows = departmentObservatory?.departments || [];

    const descendsFrom = (position: OrganizationPosition, ancestorKey: string) => {
      let current: OrganizationPosition | undefined = position;
      const visited = new Set<string>();
      while (current?.reports_to_position_key && !visited.has(current.position_key)) {
        visited.add(current.position_key);
        if (current.reports_to_position_key === ancestorKey) return true;
        current = byKey.get(current.reports_to_position_key);
      }
      return false;
    };

    let label = "CEO";
    let title = "Organization-wide executive view";
    let domains = operationalDomains;
    let scopedPositions = positions.filter((position) => position.position_key !== "board");

    if (organizationFocus.kind === "executive") {
      const portfolio = executivePortfolios.find(({ position }) => position.position_key === organizationFocus.key);
      if (portfolio) {
        label = executiveRoleLabel(portfolio.position);
        title = cleanExecutiveTitle(portfolio.position.title);
        domains = portfolio.domains;
        scopedPositions = positions.filter((position) => position.position_key === portfolio.position.position_key || descendsFrom(position, portfolio.position.position_key));
      }
    } else if (organizationFocus.kind === "domain") {
      const domain = operationalDomains.find((item) => item.department === organizationFocus.key);
      if (domain) {
        label = domain.department;
        title = "Operational domain";
        domains = [domain];
        scopedPositions = positions.filter((position) => position.department === domain.department);
      }
    }

    const domainNames = new Set(domains.map((domain) => domain.department));
    const positionKeys = new Set(scopedPositions.map((position) => position.position_key));
    const metrics = departmentRows
      .filter((row) => domainNames.has(row.department))
      .reduce((total, row) => ({
        activeWork: total.activeWork + row.work_items_active,
        openBlockers: total.openBlockers + row.blockers_open,
        activeContributions: total.activeContributions + row.active_contributions,
        pendingHuman: total.pendingHuman + row.pending_human_action_requests_linked_to_work,
      }), { activeWork: 0, openBlockers: 0, activeContributions: 0, pendingHuman: 0 });

    const recentWork = (packet?.recent_work || [])
      .filter((item) => domainNames.has(item.department) || positionKeys.has(item.assigned_position_key))
      .slice(0, 3);
    const recentActivity = activities
      .filter((activity) => (activity.department ? domainNames.has(activity.department) : false) || (activity.position_key ? positionKeys.has(activity.position_key) : false))
      .slice(0, 3);

    const downstreamPositions = organizationFocus.kind === "domain"
      ? scopedPositions.length
      : Math.max(0, scopedPositions.length - 1);
    const scopeSummary = organizationFocus.kind === "domain"
      ? `${downstreamPositions} operational position${downstreamPositions === 1 ? "" : "s"}`
      : organizationFocus.kind === "executive"
        ? `${domains.length} domain${domains.length === 1 ? "" : "s"} · ${downstreamPositions} downstream position${downstreamPositions === 1 ? "" : "s"}`
        : `${executivePortfolios.length} executive${executivePortfolios.length === 1 ? "" : "s"} · ${domains.length} domain${domains.length === 1 ? "" : "s"} · ${downstreamPositions} downstream position${downstreamPositions === 1 ? "" : "s"}`;

    return { label, title, domains, scopedPositions, downstreamPositions, scopeSummary, metrics, recentWork, recentActivity };
  }, [activities, departmentObservatory, executivePortfolios, operationalDomains, organizationFocus, packet]);

  const globalSignals = useMemo(() => {
    return [...(intelligence?.country_heatmap || [])]
      .sort((a, b) => b.critical - a.critical || b.pending_review - a.pending_review || b.activity_count - a.activity_count)
      .slice(0, 7);
  }, [intelligence]);

  const mappedSignals = useMemo(() => {
    return globalSignals.flatMap((country) => {
      const point = JURISDICTION_CENTROIDS[country.code.toUpperCase()];
      return point ? [{ ...country, point }] : [];
    });
  }, [globalSignals]);

  const maxActivity = Math.max(1, ...globalSignals.map((item) => item.activity_count));
  const boardDecisions = (packet?.pending_decisions || []).filter((decision) => decision.status === "pending_board" || decision.decision_owner_position === "board");
  const boardRisks = (packet?.open_risks || []).filter((risk) => risk.requires_board_attention);
  const activeHumanRequests = humanRequests.filter((request) => ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status));
  const boardAttention = boardDecisions.length;
  const openRisks = packet?.metrics.open_risks ?? 0;
  const boardRiskAttention = boardRisks.length;
  const pendingHuman = observatory?.metrics.human_attention.pending_requests ?? activeHumanRequests.length;
  const overdueWork = observatory?.metrics.work.overdue_active ?? 0;
  const ownerAttention = boardAttention + boardRiskAttention;
  const isPaused = packet?.control.status === "paused";

  const headline = isPaused
    ? "Human authority has paused autonomous execution."
    : ownerAttention > 0
      ? `${ownerAttention} owner signal${ownerAttention === 1 ? " requires" : "s require"} attention.`
      : "Operating within delegated authority.";

  const loadStatus = health?.status !== "ok"
    ? "offline"
    : loading
      ? "loading"
      : error || healthError
        ? "partial"
        : "ready";

  const generatedAt = packet?.generated_at || observatory?.as_of || intelligence?.generated_at;

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Cockpit"
        kicker="Global Mobility AIOS · Owner / Board"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <section className="cockpit-command" aria-labelledby="cockpit-state-title">
        <div className="cockpit-command-copy">
          <div className="cockpit-live-line">
            <span className={`cockpit-live-dot ${isPaused ? "paused" : ""}`} aria-hidden="true" />
            <span>{isPaused ? "Human hold active" : "Live organization"}</span>
            <small>{generatedAt ? `Updated ${timeLabel(generatedAt)}` : "Connecting"}</small>
          </div>
          <h2 id="cockpit-state-title">{headline}</h2>
          <p>
            One governed view of human authority, organizational execution, reviewed intelligence, and durable Activity.
          </p>
          <div className="cockpit-command-actions">
            <Link className="premium-button primary" href="/board-room">Enter Board Room</Link>
            <Link className="premium-button ghost" href="/global-intelligence">Open Global Intelligence</Link>
          </div>
        </div>

        <aside className="cockpit-command-state" aria-label="Organization control status">
          <span>Autonomous runtime</span>
          <strong>{packet?.control.status ? titleCase(packet.control.status) : "Connecting"}</strong>
          <p>{packet?.control.reason || "Governed execution remains bounded by human-owned authority."}</p>
          <div className="cockpit-state-rule"><i aria-hidden="true" /><span>Server authorization remains authoritative</span></div>
        </aside>

        <div className="cockpit-command-metrics" aria-label="Live organization metrics">
          <article><strong>{packet?.metrics.active_positions ?? "—"}</strong><span>Active positions</span></article>
          <article><strong>{operationalDomains.length || "—"}</strong><span>Operational domains</span></article>
          <article><strong>{observatory?.metrics.work.active ?? "—"}</strong><span>Active work</span></article>
          <article><strong>{observatory?.metrics.contributions.active_outcomes ?? "—"}</strong><span>Active contributions</span></article>
          <article><strong>{openRisks}</strong><span>Open risk escalations</span></article>
        </div>
      </section>

      {error ? <div className="cockpit-partial-note" role="status"><strong>Partial live picture.</strong><span>{error}</span></div> : null}

      <section className="cockpit-primary-grid">
        <article className="cockpit-surface cockpit-pulse" aria-labelledby="organization-pulse-title">
          <header className="cockpit-surface-header">
            <div>
              <span className="premium-label">Organization pulse</span>
              <h3 id="organization-pulse-title">Human authority → governed execution</h3>
            </div>
            <span className="cockpit-surface-status"><i aria-hidden="true" />{isPaused ? "Paused" : "Governed"}</span>
          </header>

          <div className="organization-pulse-map enterprise-authority-map" aria-label="Live organization authority and execution visualization">
            <div className="pulse-enterprise-stack">
              <div className="pulse-node human-board"><small>L4 human authority</small><strong>Human Board</strong></div>
              <div className={`pulse-layer-connector ${isPaused ? "paused" : "active"}`} aria-hidden="true"><span /></div>
              <button
                className={`pulse-node ceo pulse-selectable ${organizationFocus.kind === "ceo" ? "selected" : ""}`}
                type="button"
                aria-pressed={organizationFocus.kind === "ceo"}
                onClick={() => setOrganizationFocus({ kind: "ceo", key: "ceo" })}
              >
                <small>L3 executive integrator</small><strong>CEO</strong><span />
              </button>
              <div className={`pulse-layer-connector ${isPaused ? "paused" : "active"}`} aria-hidden="true"><span /></div>

              <section className="pulse-executive-layer" aria-labelledby="executive-leadership-title">
                <header className="pulse-layer-heading">
                  <div><small>L3 executive authority</small><strong id="executive-leadership-title">Executive leadership</strong></div>
                  <span>{executivePortfolios.length} active officers</span>
                </header>
                <div className="pulse-executive-grid">
                  {executivePortfolios.length ? executivePortfolios.map(({ position, domains, downstreamPositions }) => (
                    <button
                      className={`pulse-executive-card pulse-selectable ${organizationFocus.kind === "executive" && organizationFocus.key === position.position_key ? "selected" : ""}`}
                      key={position.position_key}
                      type="button"
                      aria-pressed={organizationFocus.kind === "executive" && organizationFocus.key === position.position_key}
                      onClick={() => setOrganizationFocus({ kind: "executive", key: position.position_key })}
                    >
                      <span className="pulse-executive-mark">{executiveRoleLabel(position)}</span>
                      <div>
                        <small>{position.department} · {position.authority_level}</small>
                        <strong>{cleanExecutiveTitle(position.title)}</strong>
                        <p>{domains.length ? domains.map((domain) => domain.department).join(" · ") : "Executive authority"}</p>
                      </div>
                      <em>{downstreamPositions} downstream</em>
                    </button>
                  )) : (
                    <div className="pulse-layer-empty">No active L3 officers currently report to the CEO.</div>
                  )}
                </div>
              </section>

              <div className={`pulse-layer-connector domain ${isPaused ? "paused" : "active"}`} aria-hidden="true"><span /></div>

              <section className="pulse-operational-layer" aria-labelledby="operational-domains-title">
                <header className="pulse-layer-heading">
                  <div><small>L2 / L1 organizational execution</small><strong id="operational-domains-title">Operational domains</strong></div>
                  <span>{operationalDomains.length} live domains</span>
                </header>
                <div className="pulse-domain-grid">
                  {operationalDomains.length ? operationalDomains.map((domain) => {
                    const owners = domain.ownerKeys.map((key) => EXECUTIVE_ROLE_LABELS[key] || key.toUpperCase());
                    return (
                      <button
                        className={`pulse-domain-card pulse-selectable ${organizationFocus.kind === "domain" && organizationFocus.key === domain.department ? "selected" : ""}`}
                        key={domain.department}
                        type="button"
                        aria-pressed={organizationFocus.kind === "domain" && organizationFocus.key === domain.department}
                        onClick={() => setOrganizationFocus({ kind: "domain", key: domain.department })}
                      >
                        <div><span aria-hidden="true" /><small>{owners.length ? `${owners.join(" / ")} portfolio` : "Executive ownership unresolved"}</small></div>
                        <strong>{domain.department}</strong>
                        <p>{domain.positions} operational position{domain.positions === 1 ? "" : "s"}</p>
                      </button>
                    );
                  }) : <div className="pulse-layer-empty">Waiting for active operational positions.</div>}
                </div>
              </section>

              <section className="pulse-focus-panel" aria-live="polite" aria-label="Selected organization focus">
                <header>
                  <div>
                    <small>Interactive organization focus</small>
                    <strong>{organizationFocusView.label}</strong>
                    <span>{organizationFocusView.title}</span>
                  </div>
                  <p>{organizationFocusView.scopeSummary}</p>
                </header>

                <div className="pulse-focus-metrics">
                  <div><small>Execution</small><strong>{departmentObservatory ? organizationFocusView.metrics.activeWork : "—"}</strong><span>Active work</span></div>
                  <div><small>Governance</small><strong>{departmentObservatory ? organizationFocusView.metrics.openBlockers : "—"}</strong><span>Open blockers</span></div>
                  <div><small>Evidence</small><strong>{departmentObservatory ? organizationFocusView.metrics.activeContributions : "—"}</strong><span>Active contributions</span></div>
                  <div><small>Human attention</small><strong>{departmentObservatory ? organizationFocusView.metrics.pendingHuman : "—"}</strong><span>Pending requests</span></div>
                </div>

                <div className="pulse-focus-detail">
                  <div>
                    <small>Portfolio</small>
                    <div className="pulse-focus-tags">
                      {organizationFocusView.domains.length ? organizationFocusView.domains.map((domain) => <span key={domain.department}>{domain.department}</span>) : <span>No resolved operational domains</span>}
                    </div>
                  </div>
                  <div>
                    <small>Recent durable signal</small>
                    {organizationFocusView.recentActivity[0] ? (
                      <p><strong>{organizationFocusView.recentActivity[0].title}</strong><span>{timeLabel(organizationFocusView.recentActivity[0].occurred_at)} · {organizationFocusView.recentActivity[0].department || titleCase(organizationFocusView.recentActivity[0].activity_class)}</span></p>
                    ) : organizationFocusView.recentWork[0] ? (
                      <p><strong>{organizationFocusView.recentWork[0].title}</strong><span>{titleCase(organizationFocusView.recentWork[0].status)} · {organizationFocusView.recentWork[0].department}</span></p>
                    ) : (
                      <p><strong>No recent durable signal in the loaded window.</strong><span>The Cockpit does not synthesize activity for presentation.</span></p>
                    )}
                  </div>
                </div>
              </section>

              <div className={`pulse-layer-connector execution ${isPaused ? "paused" : "active"}`} aria-hidden="true"><span /></div>
              <div className="pulse-node aios"><small>L1 governed execution</small><strong>AIOS</strong><span /></div>
            </div>

            <div className="pulse-runtime-fabric">
              <span className={isPaused ? "paused" : "active"} aria-hidden="true" />
              <div><strong>{isPaused ? "Human hold" : "Governed runtime fabric"}</strong><small>{packet?.metrics.active_positions ?? 0} active positions · {executivePortfolios.length} executives · {operationalDomains.length} domains</small></div>
            </div>
          </div>

          <footer className="pulse-integrity">
            <span>Activity history</span>
            <strong>{observatory?.coverage.activity_history_established ? `Established ${dateLabel(observatory.coverage.activity_history_coverage_start)}` : "Partial coverage"}</strong>
            <small>{observatory?.coverage.activity_history_established ? "Durable Activity coverage epoch is explicit." : "Historical activity before the explicit coverage epoch is not inferred."}</small>
          </footer>
        </article>

        <article className="cockpit-surface owner-attention" aria-labelledby="owner-attention-title">
          <header className="cockpit-surface-header compact">
            <div>
              <span className="premium-label">Requires your authority</span>
              <h3 id="owner-attention-title">Owner attention</h3>
            </div>
          </header>

          <div className={`owner-authority-orbit ${ownerAttention > 0 ? "needs-attention" : "clear"}`}>
            <div className="authority-ring" aria-hidden="true"><span /></div>
            <div className="authority-orbit-value">
              <strong>{ownerAttention}</strong>
              <span>{ownerAttention > 0 ? "interventions" : "clear"}</span>
            </div>
          </div>

          <div className={`owner-attention-state ${ownerAttention > 0 ? "needs-attention" : "clear"}`}>
            <span className="attention-emblem" aria-hidden="true">{ownerAttention > 0 ? "!" : "✓"}</span>
            <div>
              <strong>{ownerAttention > 0 ? "Reserved-authority signals are waiting." : "No owner intervention required."}</strong>
              <p>{ownerAttention > 0 ? "Review the Board decision and Board-attention risk lanes before changing organizational control." : "All observed execution remains inside delegated authority. Human ownership remains intact."}</p>
            </div>
          </div>

          <section className="owner-authority-queue" aria-label="Reserved authority queue">
            <header><span>Reserved authority queue</span><strong>{ownerAttention ? `${ownerAttention} waiting` : "Clear"}</strong></header>
            {ownerAttention ? (
              <div className="owner-queue-items">
                {boardDecisions.slice(0, 3).map((decision) => (
                  <Link href="/board-room" key={`decision-${decision.id}`}>
                    <span className="owner-queue-kind">Decision</span>
                    <strong>{decision.title}</strong>
                    <small>{decision.decision_owner_position.toUpperCase()} · {titleCase(decision.status)}</small>
                  </Link>
                ))}
                {boardRisks.slice(0, Math.max(0, 3 - boardDecisions.length)).map((risk) => (
                  <Link href="/board-room" key={`risk-${risk.id}`}>
                    <span className="owner-queue-kind risk">Risk</span>
                    <strong>{risk.title}</strong>
                    <small>{titleCase(risk.severity)} · {titleCase(risk.category)}</small>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="owner-queue-empty"><span aria-hidden="true">✓</span><p><strong>No reserved-authority records in the current Board Packet.</strong><small>Delegated human requests and operational exceptions remain visible below without being counted as Owner authority.</small></p></div>
            )}
          </section>

          <div className="attention-rows">
            <Link href="/board-room"><span>Board decisions</span><strong>{boardAttention}</strong></Link>
            <Link href="/board-room"><span>Board risk escalations</span><strong>{boardRiskAttention}</strong></Link>
            <div><span>Pending human requests</span><strong>{pendingHuman}</strong></div>
            <Link href="/"><span>Overdue active work</span><strong>{overdueWork}</strong></Link>
          </div>

          {activeHumanRequests.length ? (
            <div className="owner-human-lane">
              <span>Delegated human attention</span>
              {activeHumanRequests.slice(0, 2).map((request) => (
                <div key={request.id}><strong>{request.title}</strong><small>{titleCase(request.priority)} · {request.required_role} · {titleCase(request.status)}</small></div>
              ))}
              <small>These records are not counted as Owner authority unless they are escalated into a Board-reserved lane.</small>
            </div>
          ) : null}

          <Link className="surface-link" href="/board-room">Open executive authority →</Link>
        </article>
      </section>

      <section className="cockpit-secondary-grid">
        <article className="cockpit-surface global-mobility-pulse" aria-labelledby="global-pulse-title">
          <header className="cockpit-surface-header compact">
            <div>
              <span className="premium-label">Global mobility pulse</span>
              <h3 id="global-pulse-title">Reviewed intelligence by jurisdiction</h3>
            </div>
            <div className="global-scope-number">
              <strong>{intelligence?.scope.coverage_ready ?? "—"}</strong>
              <span>coverage ready</span>
            </div>
          </header>

          <div className="global-coverage-map" aria-label="Geographic view of reviewed jurisdiction signals">
            <svg className="global-world-shape" viewBox="0 0 720 340" preserveAspectRatio="none" aria-hidden="true">
              <g className="world-graticule">
                <path d="M0 85H720M0 170H720M0 255H720" />
                <path d="M120 0V340M240 0V340M360 0V340M480 0V340M600 0V340" />
              </g>
              <g className="world-region-labels">
                <text x="130" y="82" textAnchor="middle">NORTH AMERICA</text>
                <text x="205" y="244" textAnchor="middle">SOUTH AMERICA</text>
                <text x="365" y="86" textAnchor="middle">EUROPE</text>
                <text x="365" y="224" textAnchor="middle">AFRICA</text>
                <text x="535" y="118" textAnchor="middle">ASIA</text>
                <text x="612" y="268" textAnchor="middle">OCEANIA</text>
              </g>
              <path className="world-equator" d="M0 170H720" />
            </svg>

            <div className="global-map-legend"><span><i />Reviewed signal</span><small>{mappedSignals.length} of {globalSignals.length} current signals mapped</small></div>

            {mappedSignals.map((country) => {
              const position = projectPoint(country.point);
              const severity = country.critical > 0 ? "critical" : country.pending_review > 0 ? "review" : "reviewed";
              return (
                <Link
                  className={`global-map-marker ${severity}`}
                  href="/global-intelligence"
                  key={country.jurisdiction_id}
                  style={{ left: position.left, top: position.top }}
                  title={`${country.country}: ${country.activity_count} reviewed signals, ${country.pending_review} pending review`}
                >
                  <span aria-hidden="true" />
                  <b>{country.code}</b>
                </Link>
              );
            })}

            {!mappedSignals.length ? <div className="global-map-empty">No mappable reviewed jurisdiction signals in the current window.</div> : null}
          </div>

          <div className="global-signal-list">
            {globalSignals.length ? globalSignals.slice(0, 5).map((country) => (
              <Link href="/global-intelligence" key={country.jurisdiction_id}>
                <div className="global-signal-country"><strong>{country.country}</strong><small>{country.code} · {titleCase(country.coverage)}</small></div>
                <div className="global-signal-volume"><i style={{ width: `${Math.max(6, Math.round((country.activity_count / maxActivity) * 100))}%` }} /><span>{country.activity_count} reviewed signals</span></div>
                <div className="global-signal-meta"><strong>{country.pending_review}</strong><small>pending</small></div>
              </Link>
            )) : <div className="cockpit-empty-line">No reviewed jurisdiction activity is available in the current window.</div>}
          </div>

          <footer><span>Geographic placement is contextual. Activity volume reflects sourced reviewed change, not destination quality.</span><Link href="/global-intelligence">Open intelligence →</Link></footer>
        </article>

        <article className="cockpit-surface live-organization" aria-labelledby="live-activity-title">
          <header className="cockpit-surface-header compact">
            <div>
              <span className="premium-label">Live organization</span>
              <h3 id="live-activity-title">Durable Activity stream</h3>
            </div>
            <span className="live-activity-total">{activities.length ? `${activities.length} recent` : "Ready"}</span>
          </header>

          <div className="live-activity-list">
            {activities.length ? activities.map((activity) => (
              <article key={activity.id}>
                <time dateTime={activity.occurred_at}>{timeLabel(activity.occurred_at)}</time>
                <span className={`activity-mark ${activity.activity_class}`} aria-hidden="true" />
                <div><strong>{activity.title}</strong><p>{activity.summary}</p><small>{activity.department || titleCase(activity.activity_class)} · {titleCase(activity.actor_type)} · {activity.actor_id}</small></div>
              </article>
            )) : (
              <div className="activity-empty-state">
                <div className={`activity-coverage-viz ${observatory?.coverage.activity_history_established ? "established" : "partial"}`}>
                  <div className="activity-coverage-track" aria-hidden="true">
                    <span className="activity-history-zone" />
                    <span className="activity-coverage-line" />
                    <i className="activity-coverage-boundary" />
                    <i className="activity-now-point" />
                  </div>
                  <div className="activity-coverage-labels">
                    <div><small>Earlier history</small><strong>Not inferred</strong></div>
                    <div><small>{observatory?.coverage.activity_history_established ? "Explicit coverage epoch" : "Coverage boundary"}</small><strong>{observatory?.coverage.activity_history_established ? dateLabel(observatory.coverage.activity_history_coverage_start) : "Not established"}</strong></div>
                    <div><small>Now</small><strong>Ready for durable Activity</strong></div>
                  </div>
                </div>
                <div>
                  <strong>{observatory?.coverage.activity_history_established ? "Durable Activity coverage is established." : "Durable Activity is ready."}</strong>
                  <p>{observatory?.coverage.activity_history_established ? "New governed actions will enter the canonical stream here. History before the explicit coverage epoch remains outside the asserted durable record." : "New governed actions will enter the canonical stream here. Earlier history remains explicitly unclaimed until a coverage epoch is established."}</p>
                </div>
              </div>
            )}
          </div>

          <footer className="activity-coverage-note">
            <span>{observatory?.coverage.activity_history_established ? "Explicit Activity coverage" : "Partial Activity coverage"}</span>
            <small>{observatory?.warnings?.[0] || "The Cockpit does not invent historical activity."}</small>
          </footer>
        </article>
      </section>

      <section className="cockpit-control-links cockpit-control-dock" aria-label="Owner control surfaces">
        <Link href="/board-room"><span>Executive authority</span><strong>Board Room</strong><small>Decisions, control, escalations</small></Link>
        <Link href="/validation"><span>Independent acceptance</span><strong>External Validation</strong><small>Real external-human evidence</small></Link>
        <Link href="/source-certification-review"><span>Evidence governance</span><strong>Source Review</strong><small>Independent certification</small></Link>
        <Link href="/agents/review"><span>Human review</span><strong>Agent Review</strong><small>Controlled AI output</small></Link>
      </section>
    </WorkspaceShell>
  );
}
