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
  profile_type?: string | null;
  highest_qualification?: string | null;
  field_of_study?: string | null;
  current_country?: string | null;
  target_country?: string | null;
  desired_role?: string | null;
  budget_eur?: number | null;
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
  truth_claim_id?: string | null;
  source_url: string;
  source_type?: string | null;
  title?: string | null;
  country?: string | null;
  retrieved_at?: string | null;
};

export type HumanReview = {
  id: string;
  lead_id?: string | null;
  truth_claim_id?: string | null;
  workflow_run_id?: string | null;
  review_type?: string;
  status: string;
  priority?: string;
  reason?: string;
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
  domain: string;
  target_country?: string | null;
  target_institution_or_employer?: string | null;
  status?: string;
  risk_score?: number;
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
  profiles: Profile[];
  truth_claims: TruthClaim[];
  source_references: SourceReference[];
  reviews: HumanReview[];
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

export type ControlledAgentMeta = {
  version: string;
  department: string;
  role: string;
  guardrails: string[];
  role_card: string;
  output_schema: Record<string, unknown>;
};

export type ControlledAgentsList = {
  version: string;
  mode: string;
  automatic_actions_enabled: boolean;
  agents: Record<string, ControlledAgentMeta>;
};

export type ConsultantDecision = {
  decision: "propose_action" | "ask_clarification" | "wait_for_human";
  agent_name: string | null;
  lead_id: string | null;
  task_template: string | null;
  summary: string | null;
  clarification_question: string | null;
  escalation_reason: string | null;
  confidence: "high" | "medium" | "low";
};

export type AgentChatResponse = {
  decision: ConsultantDecision;
  reply: string;
};

export async function getLeads(): Promise<Lead[]> {
  return request<Lead[]>("/api/v1/leads");
}

export async function getControlledAgents(): Promise<ControlledAgentsList> {
  return request<ControlledAgentsList>("/api/v1/controlled-agents");
}

export async function runControlledAgent(payload: {
  agent_name: string;
  task: string;
  lead_id?: string;
  context?: Record<string, unknown>;
  actor?: string;
}) {
  return request<{ run_id: string; status: string; output: Record<string, unknown>; message: string }>(
    "/api/v1/controlled-agents/run",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function runControlledAgentBatch(payload: {
  agent_name: string;
  lead_ids: string[];
  task_template: string;
  context_per_lead?: Record<string, Record<string, unknown>>;
  actor?: string;
}) {
  return request<{ batch_id: string; agent_name: string; queued: number; run_ids: string[] }>(
    "/api/v1/controlled-agents/run-batch",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function getAgentReviewDashboard(params?: {
  status?: string;
  agent_name?: string;
  lead_id?: string;
}): Promise<AgentReviewDashboard> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.agent_name) search.set("agent_name", params.agent_name);
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  const qs = search.toString();
  return request<AgentReviewDashboard>(`/api/v1/agent-output-reviews/dashboard${qs ? `?${qs}` : ""}`);
}

export async function approveAgentRuns(runIds: string[], note?: string) {
  return request<{ approved: number }>("/api/v1/agent-output-reviews/batch-approve", {
    method: "POST",
    body: JSON.stringify({ run_ids: runIds, actor: "operator", note }),
  });
}

export async function rejectAgentRuns(runIds: string[], note?: string) {
  return request<{ rejected: number }>("/api/v1/agent-output-reviews/batch-reject", {
    method: "POST",
    body: JSON.stringify({ run_ids: runIds, actor: "operator", note }),
  });
}

export async function convertAgentRuns(runIds: string[], note?: string) {
  return request<{ converted: number }>("/api/v1/agent-output-reviews/batch-convert", {
    method: "POST",
    body: JSON.stringify({ run_ids: runIds, actor: "operator", note }),
  });
}

export type AgentRunAuditEntry = {
  id: string;
  action: string;
  actor: string;
  created_at: string;
  reason?: string | null;
};

export type AgentRunDetail = {
  run: AgentRun;
  audit_history: AgentRunAuditEntry[];
  latest_review_note: string | null;
};

export async function getAgentRunDetail(runId: string): Promise<AgentRunDetail> {
  return request<AgentRunDetail>(`/api/v1/agent-output-reviews/runs/${runId}`);
}

export async function approveAgentRun(runId: string, note?: string) {
  return request<{ approved: string; note: string | null }>(`/api/v1/agent-output-reviews/runs/${runId}/approve`, {
    method: "POST",
    body: JSON.stringify({ actor: "operator", note }),
  });
}

export async function rejectAgentRun(runId: string, note?: string) {
  return request<{ rejected: string; note: string | null }>(`/api/v1/agent-output-reviews/runs/${runId}/reject`, {
    method: "POST",
    body: JSON.stringify({ actor: "operator", note }),
  });
}

export async function convertAgentRun(runId: string, note?: string) {
  return request<{ converted: string; note: string | null }>(`/api/v1/agent-output-reviews/runs/${runId}/convert`, {
    method: "POST",
    body: JSON.stringify({ actor: "operator", note }),
  });
}

export async function chatWithAgent(
  message: string,
  conversationHistory: { role: "user" | "assistant"; content: string }[] = [],
  leadHint?: string
): Promise<AgentChatResponse> {
  return request<AgentChatResponse>("/api/v1/agent-chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
      lead_hint: leadHint,
    }),
  });
}

export type CommunicationTemplate = {
  template_key: string;
  title: string;
  subject: string;
};

export type CommunicationDraftParsed = {
  template_key: string;
  title: string;
  subject: string;
  body: string;
  note?: string | null;
  status: string;
  channel?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type CommunicationDraft = {
  draft: FollowUp;
  communication: CommunicationDraftParsed;
  lead: Lead | null;
};

export type CommunicationDraftList = {
  total_drafts: number;
  drafts: CommunicationDraft[];
};

export type CommunicationLeadSummary = {
  stage: string;
  draft_count: number;
  status_counts: Record<string, number>;
  existing_templates: string[];
  missing_templates: string[];
  next_action: string;
};

export type LeadCommunications = {
  lead: Lead;
  approved_applications: ApplicationRecord[];
  summary: CommunicationLeadSummary;
  drafts: CommunicationDraft[];
};

export async function getCommunicationTemplates(): Promise<{
  templates: CommunicationTemplate[];
  safety_rule: string;
}> {
  return request("/api/v1/client-communications/templates");
}

export async function getCommunicationDrafts(params?: {
  status?: string;
  lead_id?: string;
}): Promise<CommunicationDraftList> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  const qs = search.toString();
  return request<CommunicationDraftList>(`/api/v1/client-communications/drafts${qs ? `?${qs}` : ""}`);
}

export async function getCommunicationDraft(draftId: string): Promise<CommunicationDraft> {
  return request<CommunicationDraft>(`/api/v1/client-communications/drafts/${draftId}`);
}

export async function updateCommunicationDraft(
  draftId: string,
  payload: { subject?: string; body?: string; note?: string }
) {
  return request<{ status: string; draft: CommunicationDraft }>(
    `/api/v1/client-communications/drafts/${draftId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function markDraftReviewed(
  draftId: string,
  payload: { subject?: string; body?: string; note?: string } = {}
) {
  return request<{ status: string; draft: CommunicationDraft }>(
    `/api/v1/client-communications/drafts/${draftId}/mark-reviewed`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function generateDraft(leadId: string, templateKey: string, payload: { note?: string } = {}) {
  return request<{ status: string; draft: CommunicationDraft; lead_communications: LeadCommunications }>(
    `/api/v1/client-communications/leads/${leadId}/drafts/${templateKey}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function generateDraftPack(
  leadId: string,
  payload: { template_keys?: string[]; note?: string; skip_existing?: boolean } = {}
) {
  return request<{
    status: string;
    created_count: number;
    skipped_existing_count: number;
    created_drafts: CommunicationDraft[];
    skipped_templates: string[];
    lead_communications: LeadCommunications;
  }>(`/api/v1/client-communications/leads/${leadId}/draft-pack`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getLeadCommunications(leadId: string): Promise<LeadCommunications> {
  return request<LeadCommunications>(`/api/v1/client-communications/leads/${leadId}`);
}

export async function markAllDraftsReviewed(leadId: string, note?: string) {
  return request<{
    status: string;
    reviewed_count: number;
    skipped_count: number;
    reviewed_drafts: CommunicationDraft[];
    lead_communications: LeadCommunications;
  }>(`/api/v1/client-communications/leads/${leadId}/mark-all-reviewed`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });
}
