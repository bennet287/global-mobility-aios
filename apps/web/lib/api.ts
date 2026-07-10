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
  status: LeadStatus | string;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
};

export type Profile = {
  id: string;
  lead_id: string;
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  target_country?: string | null;
  intent?: string | null;
  budget?: string | null;
  timeline?: string | null;
  language_score?: string | null;
  raw_intake_json?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type TruthClaim = {
  id: string;
  lead_id?: string | null;
  workflow_run_id?: string | null;
  claim: string;
  domain: string;
  country: string | null;
  verdict: "VERIFIED" | "REJECTED" | "NEEDS_REVIEW" | string;
  confidence: number;
  requires_human_review: boolean;
  explanation: string;
  red_flags_json?: string | null;
  recommended_next_step?: string | null;
  created_at: string;
};

export type SourceReference = {
  id: string;
  url: string;
  title?: string | null;
  domain?: string | null;
  country?: string | null;
  topic?: string | null;
  confidence?: number | null;
  checked_at?: string | null;
};

export type HumanReview = {
  id: string;
  lead_id?: string | null;
  status: string;
  reviewer_notes?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type WorkflowRun = {
  id: string;
  lead_id?: string | null;
  workflow_name?: string | null;
  status?: string;
  created_at?: string;
};

export type AgentRun = {
  id: string;
  lead_id?: string | null;
  agent_name?: string | null;
  task?: string | null;
  status?: string;
  output_json?: string | null;
  created_at?: string;
};

export type FollowUp = {
  id: string;
  lead_id?: string | null;
  channel?: string | null;
  message?: string | null;
  status?: string;
  scheduled_at?: string | null;
  created_at?: string;
};

export type DocumentRecord = {
  id: string;
  lead_id?: string | null;
  document_type: string;
  filename: string;
  status: string;
  uploaded_at?: string | null;
  verified_by?: string | null;
  expiry_date?: string | null;
};

export type ApplicationRecord = {
  id: string;
  lead_id?: string | null;
  status?: string;
  authority?: string | null;
  decision?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type DashboardSummary = {
  leads_total: number;
  leads_new: number;
  leads_human_review: number;
  leads_converted: number;
  truth_queue_pending: number;
  truth_queue_resolved: number;
  recent_leads: Lead[];
  recent_truth_audits: TruthClaim[];
};

export type QueueCounts = Record<string, number>;

export type TruthResolutionItem = {
  lead: Lead;
  stage: string;
  can_progress: boolean;
  blockers: string[];
  counts: {
    truth_claims: number;
    rejected_truth_claims: number;
    truth_claims_needing_review: number;
    human_reviews: number;
    pending_reviews: number;
  };
  claims: TruthClaim[];
  next_action: string;
};

export type TruthResolutionQueue = {
  total_leads: number;
  stage_counts: QueueCounts;
  items: TruthResolutionItem[];
};

export type ApplicationQueueItem = {
  lead: Lead;
  stage: string;
  can_create_application?: boolean;
  can_approve?: boolean;
  can_submit?: boolean;
  blockers?: string[];
  warnings?: string[];
  counts?: Record<string, number>;
  next_action: string;
};

export type ApplicationQueue = {
  total_leads: number;
  stage_counts: QueueCounts;
  items: ApplicationQueueItem[];
};

export type DocumentVerificationQueue = {
  count: number;
  documents: DocumentRecord[];
};

export type AgentReviewItem = {
  id: string;
  lead_id: string | null;
  workflow_run_id: string | null;
  agent_name: string;
  task: string;
  status: string;
  summary: string;
  conversion_target?: string | null;
  requires_human_review: boolean;
  created_at: string;
};

export type AgentReviewDashboard = {
  version: string;
  filters: Record<string, string | null>;
  counts: QueueCounts;
  items: AgentReviewItem[];
};

export type HealthStatus = {
  status: string;
  service: string;
  environment: string;
};

export type OptionalData<T> = {
  data: T | null;
  error: string | null;
};

export type LeadDetail = {
  lead: Lead;
  profile?: Profile | null;
  truth_claims: TruthClaim[];
  source_references: SourceReference[];
  human_reviews: HumanReview[];
  workflow_runs: WorkflowRun[];
  agent_runs: AgentRun[];
  follow_ups: FollowUp[];
  documents: DocumentRecord[];
  applications: ApplicationRecord[];
};

export type LeadSyncPayload = {
  lead: Lead;
  readiness_stage?: string;
  lifecycle_stage?: string;
  authority_stage?: string;
  document_summary?: Record<string, unknown>;
  truth_summary?: Record<string, unknown>;
  application_summary?: Record<string, unknown>;
  next_action?: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return API_BASE.replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "x-gmai-role": "admin",
      "x-gmai-user": "frontend-operator",
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

async function optionalRequest<T>(path: string): Promise<OptionalData<T>> {
  try {
    return { data: await request<T>(path), error: null };
  } catch (err) {
    return { data: null, error: err instanceof Error ? err.message : "Request failed" };
  }
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/api/v1/crm/summary");
}

export async function getTruthResolutionQueue(): Promise<OptionalData<TruthResolutionQueue>> {
  return optionalRequest<TruthResolutionQueue>("/api/v1/truth/resolution-queue");
}

export async function getApplicationQueue(): Promise<OptionalData<ApplicationQueue>> {
  return optionalRequest<ApplicationQueue>("/api/v1/applications/queue");
}

export async function getDocumentVerificationQueue(): Promise<OptionalData<DocumentVerificationQueue>> {
  return optionalRequest<DocumentVerificationQueue>("/api/v1/documents/verification-queue");
}

export async function getAgentReviewDashboard(): Promise<OptionalData<AgentReviewDashboard>> {
  return optionalRequest<AgentReviewDashboard>("/api/v1/agent-output-reviews/dashboard");
}

export async function getHealthStatus(): Promise<OptionalData<HealthStatus>> {
  return optionalRequest<HealthStatus>("/health");
}

export async function getLead(id: string): Promise<Lead> {
  return request<Lead>(`/api/v1/leads/${id}`);
}

export async function getLeadDetail(id: string): Promise<LeadDetail> {
  return request<LeadDetail>(`/api/v1/leads/${id}/detail`);
}

export async function getLeadSync(id: string): Promise<LeadSyncPayload> {
  return request<LeadSyncPayload>(`/api/v1/admin-ui-sync/leads/${id}`);
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
