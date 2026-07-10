import Link from "next/link";
import { Lead } from "../lib/api";
import { LeadIdentity } from "./LeadIdentity";
import { StatusBadge } from "./StatusBadge";
import { EmptyState } from "./EmptyState";
import { titleCase } from "../lib/utils";
import { CaseRowSkeleton } from "./Skeleton";

export function CaseTable({ leads, loading }: { leads: Lead[]; loading?: boolean }) {
  if (loading) {
    return (
      <div className="case-table" role="table" aria-label="Recent leads">
        <div className="case-table-head" role="row">
          <span>Client</span>
          <span>Pathway</span>
          <span>Country</span>
          <span>Status</span>
        </div>
        <CaseRowSkeleton />
        <CaseRowSkeleton />
        <CaseRowSkeleton />
        <CaseRowSkeleton />
      </div>
    );
  }

  if (!leads.length) {
    return <EmptyState title="No live leads" detail="Create a lead or run demo seed data after starting the backend." />;
  }

  return (
    <div className="case-table" role="table" aria-label="Recent leads">
      <div className="case-table-head" role="row">
        <span>Client</span>
        <span>Pathway</span>
        <span>Country</span>
        <span>Status</span>
      </div>
      {leads.map((lead) => (
        <Link className="case-row case-row-link" href={`/leads/${lead.id}`} key={lead.id}>
          <LeadIdentity lead={lead} />
          <span>{titleCase(lead.intent)}</span>
          <span>{lead.target_country || "—"}</span>
          <StatusBadge value={lead.status} />
        </Link>
      ))}
    </div>
  );
}
