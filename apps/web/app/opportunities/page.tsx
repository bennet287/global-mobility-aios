"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  listOpportunities,
  seedOpportunities,
  matchOpportunities,
  Opportunity,
  OpportunityMatch,
} from "../../lib/api";

function MatchCard({ match }: { match: OpportunityMatch }) {
  const pct = Math.round(match.match_score * 100);
  return (
    <div className="opportunity-card match">
      <div className="match-score" style={{ "--score": `${pct}%` } as React.CSSProperties}>
        {pct}%
      </div>
      <div className="opportunity-card-body">
        <h3>{match.opportunity.title}</h3>
        <p className="opportunity-meta">
          {match.opportunity.organization} &middot; {match.opportunity.country} &middot; {match.opportunity.domain}
        </p>
        <p className="opportunity-description">{match.opportunity.description}</p>
        <div className="match-details">
          {match.reasons.length > 0 && (
            <div>
              <strong>Match reasons</strong>
              <ul>
                {match.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
          {match.risks.length > 0 && (
            <div className="risks">
              <strong>Considerations</strong>
              <ul>
                {match.risks.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [leadId, setLeadId] = useState("");
  const [matches, setMatches] = useState<OpportunityMatch[] | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadOpportunities() {
    try {
      const data = await listOpportunities();
      setOpportunities(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load opportunities");
    }
  }

  useEffect(() => {
    loadOpportunities();
  }, []);

  async function seed() {
    setLoading(true);
    try {
      await seedOpportunities();
      await loadOpportunities();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to seed opportunities");
    } finally {
      setLoading(false);
    }
  }

  async function runMatch() {
    if (!leadId.trim()) return;
    setLoading(true);
    setError(null);
    setMatches(null);
    setSummary(null);
    try {
      const data = await matchOpportunities(leadId.trim());
      setMatches(data.matches);
      setSummary(data.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matching failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="opportunities-page">
      <header className="page-header">
        <Link href="/" className="brand-lockup">
          <span>GMAI</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Opportunity matching</small>
          </div>
        </Link>
      </header>

      <main className="page-main">
        <section className="panel">
          <div className="section-header-row">
            <div>
              <h1>Opportunities</h1>
              <p className="intake-lead">
                Match leads against jobs, study programs, and visa pathways.
              </p>
            </div>
            <button className="button secondary" onClick={seed} disabled={loading}>
              Seed demo opportunities
            </button>
          </div>

          <div className="matcher-bar">
            <label>
              Lead ID
              <input
                value={leadId}
                onChange={(e) => setLeadId(e.target.value)}
                placeholder="Paste lead UUID"
              />
            </label>
            <button className="button primary" onClick={runMatch} disabled={loading || !leadId.trim()}>
              {loading ? "Matching..." : "Match opportunities"}
            </button>
          </div>

          {error && <div className="inline-notice error">{error}</div>}
          {summary && <div className="inline-notice info">{summary}</div>}

          {matches && matches.length > 0 && (
            <div className="matches-list">
              <h2>Top matches</h2>
              {matches.map((m) => (
                <MatchCard key={m.opportunity.id} match={m} />
              ))}
            </div>
          )}

          <h2>Catalog ({opportunities.length})</h2>
          <div className="opportunities-list">
            {opportunities.map((opp) => (
              <div key={opp.id} className="opportunity-card">
                <div className="opportunity-card-body">
                  <h3>{opp.title}</h3>
                  <p className="opportunity-meta">
                    {opp.organization} &middot; {opp.country} &middot; {opp.domain} &middot;{" "}
                    {opp.active ? "Active" : "Inactive"}
                  </p>
                  <p className="opportunity-description">{opp.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
