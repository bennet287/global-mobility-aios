export type LeadStatus =
  | "new"
  | "qualified"
  | "needs_documents"
  | "human_review"
  | "converted"
  | "closed";

export type Lead = {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  source: string;
  intent: string;
  target_country: string | null;
  status: LeadStatus;
  notes: string | null;
};

export type TruthAudit = {
  id: string;
  claim: string;
  domain: string;
  country: string | null;
  verdict: "VERIFIED" | "REJECTED" | "NEEDS_REVIEW";
  confidence: number;
  official_sources_found: number;
  requires_human_review: boolean;
  explanation: string;
  review_status: "PENDING" | "APPROVED" | "REJECTED";
  reviewed_by: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type DashboardSummary = {
  leads_total: number;
  leads_new: number;
  leads_human_review: number;
  leads_converted: number;
  truth_queue_pending: number;
  truth_queue_resolved: number;
  recent_leads: Lead[];
  recent_truth_audits: TruthAudit[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/api/v1/dashboard/summary");
}

export async function getTruthQueue(status: "pending" | "approved" | "rejected" | "all" = "pending") {
  return request<TruthAudit[]>(`/api/v1/truth/queue?status=${status}`);
}

export async function createLead(payload: {
  full_name: string;
  email?: string;
  phone?: string;
  source?: string;
  intent: string;
  target_country?: string;
  notes?: string;
}) {
  return request<Lead>("/api/v1/leads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function resolveAudit(
  auditId: string,
  payload: { decision: "APPROVED" | "REJECTED"; reviewer: string; notes?: string }
) {
  return request<TruthAudit>(`/api/v1/truth/queue/${auditId}/resolve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
