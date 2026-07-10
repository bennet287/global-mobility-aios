import { Lead } from "../lib/api";
import { titleCase } from "../lib/utils";

export function LeadIdentity({ lead }: { lead: Lead }) {
  return (
    <div className="lead-identity">
      <span>{lead.full_name?.slice(0, 1).toUpperCase() || "L"}</span>
      <div>
        <strong>{lead.full_name || "Unnamed lead"}</strong>
        <small>
          {lead.target_country || "No country"} · {titleCase(lead.intent)}
        </small>
      </div>
    </div>
  );
}
