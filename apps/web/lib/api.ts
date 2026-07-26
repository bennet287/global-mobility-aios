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

export type EducationEntry = {
  qualification: string;
  field_of_study?: string | null;
  institution?: string | null;
  country?: string | null;
  completion_year?: number | null;
};

export type EmploymentEntry = {
  role: string;
  employer?: string | null;
  country?: string | null;
  years: number;
  current: boolean;
};

export type LanguageAbility = {
  language: string;
  level?: string | null;
  test_name?: string | null;
  test_score?: string | null;
};

export type MobilityGoal = {
  domain: "study" | "work" | "visa" | "settlement" | "family" | "business";
  target_country: string;
  desired_role_or_program?: string | null;
  target_date?: string | null;
  priority: "low" | "medium" | "high";
};

export type UniversalMobilityProfileInput = {
  current_country?: string | null;
  education: EducationEntry[];
  employment: EmploymentEntry[];
  years_experience?: number | null;
  skills: string[];
  languages: LanguageAbility[];
  family_status: "unknown" | "single" | "partnered" | "dependants";
  family: Record<string, unknown>[];
  family_details_confirmed: boolean;
  finances: Record<string, unknown>;
  goals: MobilityGoal[];
  constraints: Record<string, unknown>[];
  constraints_confirmed: boolean;
  consent_status: "not_recorded" | "granted" | "withdrawn";
  consent_purposes: string[];
  consent_expires_at?: string | null;
  evidence_document_ids: string[];
};

export type UniversalMobilityProfile = {
  id: string;
  lead_id: string;
  profile_version: number;
  lifecycle_status: string;
  supersedes_profile_id?: string | null;
  current_country?: string | null;
  education: EducationEntry[];
  employment: EmploymentEntry[];
  years_experience?: number | null;
  skills: string[];
  languages: LanguageAbility[];
  family: { status?: string; members?: Record<string, unknown>[]; details_confirmed?: boolean };
  finances: Record<string, unknown>;
  goals: MobilityGoal[];
  constraints: { items?: Record<string, unknown>[]; confirmed?: boolean };
  consent: { status?: string; purposes?: string[]; expires_at?: string | null; recorded_at?: string };
  evidence_document_ids: string[];
  completeness_score: number;
  readiness_stage: string;
  consent_status: string;
  missing_sections: string[];
  activated_at?: string | null;
  updated_by?: string | null;
  created_at: string;
  updated_at: string;
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
  storage_provider?: string | null;
  storage_reference_present?: boolean;
  file_hash?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  signed_access_supported?: boolean;
  storage_key_exposed?: boolean;
};

export type DocumentAccessGrant = {
  id: string;
  document_id: string;
  lead_id: string;
  issued_to: string;
  issued_role: string;
  purpose: string;
  status: string;
  expires_at: string;
  max_uses: number;
  use_count: number;
  remaining_uses: number;
  storage_provider: string;
  filename: string;
  created_by: string;
  last_accessed_by: string | null;
  last_accessed_at: string | null;
  revoked_by: string | null;
  revoked_at: string | null;
  revocation_reason: string | null;
  created_at: string;
  updated_at: string;
  expired: boolean;
  token_returned: boolean;
  storage_key_exposed: boolean;
};

export type DocumentAccessGrantIssued = {
  grant: DocumentAccessGrant;
  token: string;
  token_type: "gmai_document_access";
  direct_object_url: null;
  storage_credentials_exposed: boolean;
  storage_key_exposed: boolean;
};

export type DocumentStoragePosture = {
  environment: string;
  backend: string;
  strict_mode: boolean;
  signed_access_secret_configured: boolean;
  signed_access_ttl_seconds: number;
  signed_access_max_ttl_seconds: number;
  minio_tls_enabled: boolean;
  minio_default_credentials: boolean;
  bucket_auto_create: boolean;
  server_side_encryption_enabled: boolean;
  retention_days: number;
  backup_strategy_configured: boolean;
  recovery_test_recorded: boolean;
  local_storage_allowed_in_production: boolean;
  failures: string[];
  ready: boolean;
  signed_access_enabled: boolean;
  direct_object_urls_enabled: boolean;
  storage_credentials_exposed: boolean;
  unrestricted_object_keys_exposed: boolean;
  allowed_purposes: string[];
};

export type DocumentSchemaDefinition = {
  id: string;
  schema_key: string;
  document_type: string;
  version_number: number;
  lifecycle_status: string;
  json_schema: Record<string, unknown>;
  extraction_rules: Record<string, unknown>;
  human_review_required: boolean;
  approved_by: string | null;
  review_notes: string | null;
  published_at: string | null;
};

export type DocumentExtractionJob = {
  id: string;
  document_id: string;
  lead_id: string | null;
  schema_definition_id: string;
  schema_version: number;
  schema_key: string;
  document_type: string;
  status: string;
  engine: string;
  language: string;
  task_id: string | null;
  attempt_count: number;
  input_file_hash: string | null;
  extracted_text: string | null;
  structured_data: Record<string, unknown>;
  field_confidence: Record<string, number>;
  warnings: string[];
  error_code: string | null;
  error_message: string | null;
  requested_by: string;
  reviewed_by: string | null;
  review_notes: string | null;
  queued_at: string;
  completed_at: string | null;
  reviewed_at: string | null;
};

export type DocumentConsistencyFinding = {
  finding_key: string;
  document_field: string;
  source: "lead" | "profile" | "application" | "system";
  source_path: string;
  outcome: "match" | "mismatch" | "missing_document_value" | "missing_source_value" | "not_comparable";
  severity: "info" | "warning" | "high";
  extracted_value: unknown;
  source_value: unknown;
  explanation: string;
};

export type DocumentConsistencyAssessment = {
  id: string;
  extraction_job_id: string;
  document_id: string;
  lead_id: string;
  profile_id: string;
  profile_version: number;
  application_id: string | null;
  result_status: string;
  review_status: string;
  match_count: number;
  mismatch_count: number;
  missing_count: number;
  findings: DocumentConsistencyFinding[];
  source_facts: Record<string, unknown>;
  summary: string;
  human_review_required: boolean;
  generated_by: string;
  reviewed_by: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentExpiryReminder = {
  id: string;
  reminder_key: string;
  document_id: string;
  lead_id: string | null;
  document_type: string;
  filename: string;
  expiry_date: string;
  reminder_type: string;
  threshold_days: number;
  due_at: string;
  status: string;
  priority: string;
  source: string;
  human_review_required: boolean;
  external_delivery_status: string;
  external_message_sent: boolean;
  generated_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  superseded_by_id: string | null;
  days_until_expiry: number;
  created_at: string;
  updated_at: string;
};

export type DocumentExpiryScanResult = {
  as_of: string;
  lead_id: string | null;
  documents_scanned: number;
  created: number;
  existing: number;
  superseded: number;
  outside_window: number;
  reminder_ids: string[];
  external_messages_sent: number;
};

export type DocumentRequirementFinding = {
  finding_key: string;
  finding_type: "requirement_coverage" | "cross_document_inconsistency";
  requirement_key: string;
  requirement_label: string;
  expected_document_types: string[];
  optional: boolean;
  outcome: "satisfied" | "missing" | "optional_missing" | "rejected" | "expired" | "present_unverified" | "fact_inconsistency" | "duplicate_conflict";
  severity: "info" | "warning" | "high";
  document_ids: string[];
  document_names: string[];
  explanation: string;
  evidence: Record<string, unknown>;
};

export type DocumentRequirementAssessment = {
  id: string;
  assessment_key: string;
  lead_id: string;
  application_id: string | null;
  pathway_id: string | null;
  pathway_version_id: string | null;
  eligibility_assessment_id: string | null;
  profile_id: string | null;
  profile_version: number | null;
  requirement_source: string;
  result_status: string;
  review_status: string;
  required_count: number;
  satisfied_count: number;
  missing_count: number;
  inconsistency_count: number;
  requirements: Array<Record<string, unknown>>;
  findings: DocumentRequirementFinding[];
  source_snapshot: Record<string, unknown>;
  document_snapshot: Array<Record<string, unknown>>;
  summary: string;
  human_review_required: boolean;
  generated_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  source_records_unchanged: boolean;
  documents_created: number;
  eligibility_changed: boolean;
  created_at: string;
  updated_at: string;
};

export type DocumentRequirementScanResult = {
  lead_id: string | null;
  leads_scanned: number;
  created: number;
  existing: number;
  skipped: number;
  assessment_ids: string[];
  documents_created: number;
  external_messages_sent: number;
};


export type DocumentFraudRiskIndicator = {
  indicator_key: string;
  indicator_type: "exact_file_reuse_across_leads" | "same_file_multiple_document_types" | "approved_identity_mismatch" | "approved_material_fact_mismatch" | "conflicting_duplicate_evidence" | "approved_cross_document_inconsistency" | "rejected_or_invalid_evidence" | "extraction_integrity_failure" | "approved_identifier_reuse_across_leads";
  severity: "warning" | "high";
  document_ids: string[];
  document_names: string[];
  source_record_type: string;
  source_record_ids: string[];
  explanation: string;
  evidence: Record<string, unknown>;
  human_review_required: boolean;
};

export type DocumentFraudRiskAssessment = {
  id: string;
  assessment_key: string;
  lead_id: string;
  profile_id: string | null;
  profile_version: number | null;
  application_id: string | null;
  result_status: string;
  review_status: string;
  risk_band: string;
  indicator_count: number;
  high_indicator_count: number;
  warning_indicator_count: number;
  indicators: DocumentFraudRiskIndicator[];
  source_snapshot: Record<string, unknown>;
  summary: string;
  human_review_required: boolean;
  automated_fraud_determination: boolean;
  adverse_action_taken: boolean;
  generated_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  fraud_determined: boolean;
  documents_rejected: number;
  eligibility_changed: boolean;
  external_actions_triggered: number;
  created_at: string;
  updated_at: string;
};

export type DocumentFraudRiskScanResult = {
  lead_id: string | null;
  leads_scanned: number;
  created: number;
  existing: number;
  skipped: number;
  assessment_ids: string[];
  fraud_determinations: number;
  documents_rejected: number;
  eligibility_changed: boolean;
  external_actions_triggered: number;
};

export type GlobalIntelligenceChange = {
  id: string;
  jurisdiction_id: string;
  jurisdiction_code: string | null;
  country: string;
  jurisdiction_type: string | null;
  region: string | null;
  change_type: string;
  title: string;
  summary: string;
  program_id: string | null;
  program_name: string | null;
  domain: string;
  materiality: string;
  status: string;
  source_id: string | null;
  source_name: string | null;
  source_url: string | null;
  authority_id: string | null;
  authority_name: string | null;
  freshness: "fresh" | "stale" | "never_checked" | "inactive" | "unmonitored";
  monitor_status: string | null;
  last_checked_at: string | null;
  coverage: "ready" | "gap" | "not_required" | "unregistered";
  coverage_gaps: string[];
  confidence: number | null;
  confidence_band: "high" | "medium" | "low" | "unknown";
  confidence_source: string;
  effective_at: string | null;
  detected_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  published_at: string | null;
};

export type GlobalIntelligenceDashboard = {
  generated_at: string;
  window_days: number;
  filters: {
    applied: {
      freshness: string;
      coverage: string;
      authority_id: string | null;
      authority_name: string | null;
      confidence: string;
      materiality: string;
      review_state: string;
    };
    matched_changes: number;
    available_changes: number;
    options: {
      authorities: Array<{ id: string; name: string; jurisdiction_id: string; count: number }>;
      freshness: Record<string, number>;
      coverage: Record<string, number>;
      confidence: Record<string, number>;
      materiality: Record<string, number>;
      review_state: Record<string, number>;
    };
  };
  scope: {
    registered_jurisdictions: number;
    registered_countries: number;
    registered_territories: number;
    registered_autonomous_jurisdictions: number;
    official_sources: number;
    active_verified_rules: number;
    global_coverage_claim_ready: boolean;
    coverage_warning: string;
    registry_version: string | null;
    registry_entries: number;
    coverage_ready: number;
  };
  today: { changes_detected: number; countries_updated: number; country_names: string[] };
  counts: Record<string, number>;
  change_type_counts: Record<string, number>;
  status_counts: Record<string, number>;
  materiality_counts: Record<string, number>;
  new_programs: GlobalIntelligenceChange[];
  immigration_changes: GlobalIntelligenceChange[];
  processing_times: GlobalIntelligenceChange[];
  skilled_occupations: GlobalIntelligenceChange[];
  thresholds: GlobalIntelligenceChange[];
  country_heatmap: Array<{
    jurisdiction_id: string; code: string; country: string; jurisdiction_type: string; region: string | null; coverage: string;
    activity_count: number; activity_level: string; pending_review: number; published: number; critical: number;
    official_sources: number; active_verified_rules: number; last_detected_at: string | null;
  }>;
  opportunity_radar: Array<{
    jurisdiction_id: string; country: string; region: string | null; activity_score: number; signal_level: string;
    evidence_count: number; evidence: GlobalIntelligenceChange[]; classification: string; explanation: string;
  }>;
  safety: { reviewed_activity_only_for_radar: boolean; predictive: boolean; client_recommendation: boolean; message: string };
};

export type JurisdictionImmigrationAssessment = {
  id: string;
  jurisdiction_id: string;
  registry_entry_id: string;
  assessment_version: number;
  rule_relationship: string;
  parent_code: string | null;
  evidence_url: string;
  evidence_title: string;
  official_source_id: string | null;
  source_snapshot_id: string | null;
  rationale: string;
  status: string;
  proposed_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  supersedes_assessment_id: string | null;
  created_at: string;
  updated_at: string;
};

export type JurisdictionSourceCertification = {
  id: string;
  jurisdiction_id: string;
  registry_entry_id: string;
  regulatory_authority_id: string;
  official_source_id: string;
  certification_version: number;
  certification_scope: string;
  coverage_domains: string[];
  evidence_notes: string;
  status: string;
  proposed_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  supersedes_certification_id: string | null;
  created_at: string;
  updated_at: string;
};

export type JurisdictionCoverageWorklist = {
  generated_at?: string;
  release: GlobalJurisdictionRegistry["release"];
  filters: { gap: string; region: string; limit: number };
  total: number;
  items: Array<{
    jurisdiction_id: string;
    registry_entry_id: string;
    alpha2_code: string;
    name: string;
    region: string | null;
    jurisdiction_type: string;
    immigration_rule_status: string;
    missing: string[];
    has_authority: boolean;
    has_official_source: boolean;
    pending_assessment: JurisdictionImmigrationAssessment | null;
    pending_source_certification: JurisdictionSourceCertification | null;
  }>;
  safety: { creates_coverage_claim: boolean; human_review_required: boolean; message: string };
};

export type JurisdictionCoverageEvidenceBatch = {
  id: string;
  registry_release_id: string;
  batch_key: string;
  name: string;
  notes: string;
  item_count: number;
  immigration_assessment_count: number;
  source_certification_count: number;
  source_onboarding_count: number;
  status: string;
  stored_status: string;
  submitted_by: string;
  created_at: string;
  created?: boolean;
  review_counts: Record<string, number>;
  items?: Array<{
    id: string;
    row_number: number;
    jurisdiction_id: string;
    registry_entry_id: string;
    alpha2_code: string;
    payload_sha256: string;
    immigration_assessment: JurisdictionImmigrationAssessment | null;
    source_certification: JurisdictionSourceCertification | null;
    source_onboarding: null | {
      regulatory_authority_id: string | null;
      authority_name: string | null;
      official_source_id: string | null;
      source_name: string | null;
      source_url: string | null;
      source_monitor_id: string | null;
      monitor_status: string | null;
      next_check_at: string | null;
    };
    created_at: string;
  }>;
};

export type JurisdictionCoverageBaselineStatus = {
  batch_id: string;
  batch_name: string;
  submitted_by: string;
  item_count: number;
  counts: Record<string, number>;
  eligible_to_queue: number;
  baseline_ready: number;
  in_progress: number;
  failed: number;
  pending_review: number;
  queued?: number;
  queue_failures?: Array<{ retrieval_run_id: string; monitor_id: string; error: string }>;
  skipped?: Array<{ alpha2_code: string; state: string }>;
  items: Array<{
    batch_item_id: string;
    alpha2_code: string;
    jurisdiction_id: string;
    official_source_id: string | null;
    source_monitor_id: string | null;
    assessment_status: string;
    certification_status: string;
    source_active: boolean;
    monitor_status: string;
    state: string;
    eligible_to_queue: boolean;
    latest_run: null | {
      id: string;
      status: string;
      attempt: number;
      started_at: string;
      completed_at: string | null;
      error_code: string | null;
      error_message: string | null;
    };
    latest_snapshot: null | {
      id: string;
      status: string;
      content_hash: string | null;
      captured_at: string;
      url: string;
    };
  }>;
  safety: {
    publishes_verified_rule: boolean;
    creates_coverage_claim: boolean;
    requires_approved_assessment_and_certification: boolean;
    message: string;
  };
};

export type CoverageTrancheAssistantConfig = {
  enabled: boolean;
  max_items: number;
  defaults: {
    dry_run: boolean;
    queue_eligible_baselines: boolean;
    default_batch_size: number;
  };
  safety: {
    creates_review_records: boolean;
    approves_evidence: boolean;
    creates_assertions: boolean;
    publishes_verified_rules: boolean;
    creates_coverage_claim: boolean;
    mutates_immutable_snapshots: boolean;
    message: string;
  };
};

export type CoverageTrancheAssistantResult = {
  batch_id: string;
  batch_name: string;
  actor: string;
  dry_run: boolean;
  selected_count: number;
  selected_codes: string[];
  would_queue_baselines: string[];
  queued_baselines: number;
  queue_result: JurisdictionCoverageBaselineStatus | null;
  items: Array<{
    batch_item_id: string;
    alpha2_code: string;
    jurisdiction_name: string | null;
    stage: string;
    baseline: JurisdictionCoverageBaselineStatus["items"][number];
    review_packet: {
      immigration_assessment: null | Record<string, unknown>;
      source_certification: null | Record<string, unknown>;
      authority: null | { id: string; name: string; authority_type: string; website_url: string | null; active: boolean };
      official_source: null | { id: string; name: string; url: string; domain: string; source_type: string; active: boolean };
      monitor: null | Record<string, unknown>;
      review_checks: string[];
    };
    snapshot_analysis: null | {
      snapshot_id: string;
      snapshot_url: string;
      captured_at: string;
      content_hash: string | null;
      content_characters: number;
      unique_lines: number;
      navigation_lines: number;
      navigation_ratio: number;
      keyword_hits: string[];
      quality_score: number;
      classification: string;
      candidate_excerpt_lines: string[];
      preview: string;
    };
    candidate_assertion: null | {
      alpha2_code: string;
      domain: string;
      title: string;
      rule_key: string;
      statement: string;
      evidence_excerpt: string;
      rationale: string;
      confidence: number;
      requires_human_edit: boolean;
      creates_pending_assertion: boolean;
    };
    existing_assertion: null | {
      id: string;
      status: string;
      title: string;
      rule_key: string;
      proposed_by: string;
      reviewed_by: string | null;
      published_by: string | null;
      published_rule_id: string | null;
    };
    coverage_receipt: JurisdictionCoverageReceipt;
    next_action: string;
  }>;
  safety: CoverageTrancheAssistantConfig["safety"];
};

export type InitialRuleAssertion = {
  id: string;
  assertion_sha256: string;
  coverage_batch_item_id: string | null;
  jurisdiction_id: string;
  official_source_id: string;
  source_snapshot_id: string;
  alpha2_code: string | null;
  jurisdiction_name: string | null;
  source_name: string | null;
  source_url: string | null;
  domain: string;
  title: string;
  rule_key: string;
  statement: string;
  rationale: string;
  evidence_excerpt: string;
  confidence: number;
  effective_from: string | null;
  effective_to: string | null;
  status: string;
  proposed_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  published_rule_id: string | null;
  published_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  snapshot: null | {
    id: string;
    status: string;
    content_hash: string | null;
    captured_at: string;
    url: string;
  };
  verified_rule: null | {
    id: string;
    rule_key: string;
    active: boolean;
    published_at: string | null;
  };
  safety: {
    source_change_claimed: boolean;
    human_review_required: boolean;
    publishes_automatically: boolean;
    message: string;
  };
  created?: boolean;
};

export type JurisdictionCoverageReceipt = {
  registry_release_version: string | null;
  registry_entry_id: string;
  jurisdiction_id: string;
  alpha2_code: string;
  name: string;
  coverage_required: boolean;
  coverage_ready: boolean;
  status: "ready" | "gap" | "not_required";
  missing: string[];
  gates: {
    immigration_rule_assessment: boolean;
    reviewed_primary_authority: boolean;
    reviewed_primary_source: boolean;
    fresh_monitor: boolean;
    verified_rule: boolean;
  };
  registry_summary: {
    coverage_ready: number;
    coverage_required: number;
    with_verified_rule: number;
  };
  global_coverage_claim_ready: boolean;
};

export type InitialRulePublicationReceipt = {
  idempotent: boolean;
  became_ready: boolean;
  before: JurisdictionCoverageReceipt;
  after: JurisdictionCoverageReceipt;
  verified_rule_id: string;
  message: string;
};

export type GlobalJurisdictionRegistry = {
  generated_at?: string;
  release: null | {
    id: string;
    version: string;
    source_name: string;
    source_url: string;
    source_sha256: string;
    source_retrieved_at: string;
    released_at: string;
    released_by: string;
    status: string;
  };
  summary: {
    registry_entries: number;
    coverage_required: number;
    un_members?: number;
    un_observers?: number;
    countries?: number;
    territories?: number;
    autonomous_jurisdictions?: number;
    with_authority?: number;
    with_official_source?: number;
    with_authority_onboarded?: number;
    with_official_source_onboarded?: number;
    with_fresh_monitor?: number;
    with_verified_rule?: number;
    coverage_ready?: number;
    immigration_rule_assessed?: number;
    assessments_pending_review?: number;
    source_certifications_pending_review?: number;
  };
  release_gate: {
    registry_complete: boolean;
    authority_coverage_complete: boolean;
    source_coverage_complete: boolean;
    monitor_coverage_complete: boolean;
    verified_rule_coverage_complete: boolean;
    immigration_rule_assessment_complete?: boolean;
    global_coverage_claim_ready: boolean;
    message?: string;
  };
  regions: Array<{ region: string; entries: number; coverage_required: number; coverage_ready: number }>;
  entries: Array<{
    id: string;
    jurisdiction_id: string;
    alpha2_code: string;
    alpha3_code: string;
    m49_code: string;
    name: string;
    jurisdiction_type: string;
    membership_status: string;
    parent_code: string | null;
    region: string | null;
    subregion: string | null;
    coverage_required: boolean;
    immigration_rule_status: string;
    approved_assessment: JurisdictionImmigrationAssessment | null;
    pending_assessment: JurisdictionImmigrationAssessment | null;
    has_authority: boolean;
    has_official_source: boolean;
    has_reviewed_primary_authority: boolean;
    has_reviewed_primary_source: boolean;
    approved_source_certification: JurisdictionSourceCertification | null;
    pending_source_certification: JurisdictionSourceCertification | null;
    approved_supplemental_source_certifications: JurisdictionSourceCertification[];
    pending_supplemental_source_certifications: JurisdictionSourceCertification[];
    has_fresh_monitor: boolean;
    has_verified_rule: boolean;
    coverage_ready: boolean;
    missing: string[];
  }>;
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
  const useLocalHeaderAuth =
    process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE === "true" ||
    (process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE !== "false");

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(useLocalHeaderAuth
        ? {
            "x-gmai-role": process.env.NEXT_PUBLIC_GMAI_ROLE || "admin",
            "x-gmai-user": process.env.NEXT_PUBLIC_GMAI_USER || "frontend-operator",
          }
        : {}),
      ...(init?.headers || {}),
    },
    credentials: "include",
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

export async function getCurrentMobilityProfile(leadId: string): Promise<UniversalMobilityProfile> {
  return request<UniversalMobilityProfile>(`/api/v1/profiles/leads/${leadId}/current`);
}

export async function getMobilityProfileHistory(leadId: string): Promise<UniversalMobilityProfile[]> {
  return request<UniversalMobilityProfile[]>(`/api/v1/profiles/leads/${leadId}/history`);
}

export async function replaceCurrentMobilityProfile(
  leadId: string,
  payload: UniversalMobilityProfileInput
): Promise<UniversalMobilityProfile> {
  return request<UniversalMobilityProfile>(`/api/v1/profiles/leads/${leadId}/current`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
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


export type PublicIntakePayload = {
  full_name: string;
  email?: string;
  phone?: string;
  goal: string;
  nationality: string;
  profession: string;
  years_experience?: number;
  target_country: string;
  notes?: string;
};

export type PublicIntakeResponse = {
  session_token: string;
  lead_id: string | null;
  status: string;
  checklist: string[];
  message: string;
};

export type CoachReview = {
  id: string;
  lead_id: string | null;
  agent_run_id: string | null;
  coach_agent_name: string;
  target_agent_name: string;
  conclusion_valid: boolean;
  missing_facts_json: string | null;
  source_issues_json: string | null;
  corrected_summary: string | null;
  confidence: "low" | "medium" | "high";
  operator_feedback: string | null;
  operator_override_json: string | null;
  status: "pending" | "approved" | "overridden";
  created_at: string;
  updated_at: string;
};

export type TrainingCase = {
  id: string;
  lead_id: string | null;
  title: string;
  country: string;
  profession: string;
  scenario_json: string | null;
  expected_outcome_json: string | null;
  source: string;
  times_run: number;
  avg_score: number | null;
  created_at: string;
  updated_at: string;
};

export async function createPublicIntake(payload: PublicIntakePayload): Promise<PublicIntakeResponse> {
  return request<PublicIntakeResponse>("/api/v1/public/intake", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPublicIntake(sessionToken: string): Promise<PublicIntakeResponse> {
  return request<PublicIntakeResponse>(`/api/v1/public/intake/${sessionToken}`);
}

export type DocumentOcrPayload = {
  lead_id: string;
  document_type: string;
  filename: string;
  extracted_text: string;
  language?: string;
  confidence?: number;
};

export type DocumentOcrResponse = {
  document_id: string;
  document_type: string;
  extracted_text: string;
  parsed_fields: Record<string, unknown>;
  message: string;
};

export async function submitDocumentOcr(payload: DocumentOcrPayload): Promise<DocumentOcrResponse> {
  return request<DocumentOcrResponse>("/api/v1/documents/ocr-extract", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runEligibilityCoach(leadId: string): Promise<CoachReview> {
  return request<CoachReview>(`/api/v1/coaching/eligibility/${leadId}`, {
    method: "POST",
  });
}

export async function listCoachReviews(leadId: string): Promise<CoachReview[]> {
  return request<CoachReview[]>(`/api/v1/coaching/eligibility/${leadId}/reviews`);
}

export async function listAllCoachReviews(params?: {
  status?: "pending" | "approved" | "overridden";
  target_agent_name?: string;
}): Promise<CoachReview[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.target_agent_name) qs.set("target_agent_name", params.target_agent_name);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<CoachReview[]>(`/api/v1/coaching/reviews${query}`);
}

export async function submitCoachFeedback(
  reviewId: string,
  feedback: { operator_feedback: string; override_decision?: "pending" | "approved" | "overridden" }
): Promise<CoachReview> {
  return request<CoachReview>(`/api/v1/coaching/reviews/${reviewId}/feedback`, {
    method: "POST",
    body: JSON.stringify(feedback),
  });
}

export async function generateTrainingCases(payload: {
  count: number;
  country?: string;
  profession?: string;
}): Promise<TrainingCase[]> {
  return request<TrainingCase[]>("/api/v1/training-cases/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type EligibilityAssessment = {
  id: string;
  lead_id: string;
  agent_run_id: string | null;
  target_country: string | null;
  domain: string;
  overall_score: number;
  confidence: number;
  status: "eligible" | "likely_eligible" | "needs_documents" | "insufficient_profile" | "ineligible" | string;
  summary: string | null;
  risks: string[];
  required_documents: string[];
  pathways: string[];
  factors: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export async function evaluateEligibility(
  leadId: string,
  profile: Record<string, unknown> = {}
): Promise<EligibilityAssessment> {
  return request<EligibilityAssessment>("/api/v1/eligibility/evaluate", {
    method: "POST",
    body: JSON.stringify({ lead_id: leadId, profile }),
  });
}

export async function getLatestEligibilityAssessment(leadId: string): Promise<EligibilityAssessment> {
  return request<EligibilityAssessment>(`/api/v1/eligibility/${leadId}/latest`);
}

export type ClientLookupPayload = {
  email?: string;
  phone?: string;
  session_token?: string;
};

export type ClientLookupResult = {
  lead_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  target_country: string | null;
  status: string;
  updated_at: string;
};

export type ClientDashboardDocument = {
  id: string;
  document_type: string;
  filename: string;
  status: string;
  uploaded_at: string | null;
};

export type ClientDashboardFollowUp = {
  id: string;
  channel: string;
  status: string;
  message: string;
  due_at: string | null;
};

export type ClientReturnDashboard = {
  lead_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  target_country: string | null;
  status: string;
  intent: string;
  checklist: string[];
  session_token: string | null;
  eligibility: EligibilityAssessment | null;
  documents: ClientDashboardDocument[];
  follow_ups: ClientDashboardFollowUp[];
  application_stage: string | null;
  next_action: string;
  updated_at: string;
};

export async function lookupClientCases(payload: ClientLookupPayload): Promise<ClientLookupResult[]> {
  return request<ClientLookupResult[]>("/api/v1/public/lookup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getClientReturnDashboard(
  leadId: string,
  portalToken: string
): Promise<ClientReturnDashboard> {
  return request<ClientReturnDashboard>(`/api/v1/public/return/${leadId}`, {
    headers: { "X-GMAI-Portal-Token": portalToken },
  });
}

export type ClientPortalGrant = {
  id: string;
  lead_id: string;
  label: string;
  status: "active" | "expired" | "revoked";
  expires_at: string;
  created_by: string;
  access_count: number;
  last_accessed_at: string | null;
  revoked_by: string | null;
  revoked_at: string | null;
  revocation_reason: string | null;
  created_at: string;
  updated_at: string;
  expired: boolean;
};

export type ClientPortalGrantIssued = {
  grant: ClientPortalGrant;
  token: string;
  portal_path: string;
};

export type ClientPortalDocument = {
  id: string;
  document_type: string;
  filename: string;
  status: string;
  uploaded_at: string | null;
  expiry_date: string | null;
};

export type ClientPortalMilestone = {
  key: string;
  label: string;
  state: "complete" | "current" | "upcoming";
};

export type ClientPortalDashboard = {
  grant_id: string;
  client_name: string;
  target_country: string | null;
  intent: string;
  case_status: string;
  application_stage: string | null;
  next_action: string;
  documents: ClientPortalDocument[];
  document_counts: Record<string, number>;
  milestones: ClientPortalMilestone[];
  expires_at: string;
  updated_at: string;
};

export async function issueClientPortalGrant(
  leadId: string,
  expiresInDays = 30
): Promise<ClientPortalGrantIssued> {
  return request<ClientPortalGrantIssued>("/api/v1/client-portal/grants", {
    method: "POST",
    body: JSON.stringify({
      lead_id: leadId,
      label: "Primary client access",
      expires_in_days: expiresInDays,
    }),
  });
}

export async function getClientPortalDashboard(token: string): Promise<ClientPortalDashboard> {
  return request<ClientPortalDashboard>("/api/v1/public/client-portal/dashboard", {
    headers: { "X-GMAI-Portal-Token": token },
  });
}

export type EcosystemPortalGrantIssued = {
  grant: {
    id: string;
    corporate_account_id: string;
    audience_type: "employer" | "partner";
    label: string;
    status: "active" | "expired" | "revoked";
    expires_at: string;
  };
  token: string;
  portal_path: string;
};

export type EcosystemPortalCase = {
  case_reference: string;
  case_type: string;
  status: string;
  employee_name: string | null;
  origin_country: string | null;
  destination_country: string;
  target_start_date: string | null;
  compliance_due_date: string | null;
  open_compliance_items: number;
  open_tasks: number;
  next_action: string;
  updated_at: string;
};

export type EcosystemPortalDashboard = {
  grant_id: string;
  audience_type: "employer" | "partner";
  account_name: string;
  primary_country: string;
  account_status: string;
  case_counts: Record<string, number>;
  cases: EcosystemPortalCase[];
  upcoming_compliance: Array<{
    case_reference: string;
    title: string;
    event_type: string;
    due_at: string;
    status: string;
    evidence_required: boolean;
  }>;
  expires_at: string;
  updated_at: string;
};

export async function issueEcosystemPortalGrant(
  corporateAccountId: string,
  audienceType: "employer" | "partner",
  label: string,
  expiresInDays = 30,
): Promise<EcosystemPortalGrantIssued> {
  return request<EcosystemPortalGrantIssued>("/api/v1/ecosystem-portal/grants", {
    method: "POST",
    body: JSON.stringify({
      corporate_account_id: corporateAccountId,
      audience_type: audienceType,
      label,
      expires_in_days: expiresInDays,
    }),
  });
}

export async function getEcosystemPortalDashboard(
  token: string,
): Promise<EcosystemPortalDashboard> {
  return request<EcosystemPortalDashboard>("/api/v1/public/ecosystem-portal/dashboard", {
    headers: { "X-GMAI-Ecosystem-Token": token },
  });
}

export type Opportunity = {
  id: string;
  title: string;
  organization: string | null;
  country: string;
  domain: string;
  profession_tags: string[];
  field_tags: string[];
  required_years_experience: number | null;
  language_requirement: string | null;
  salary_eur: number | null;
  budget_eur: number | null;
  description: string | null;
  source: string;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type OpportunityMatch = {
  opportunity: Opportunity;
  match_score: number;
  confidence: number;
  reasons: string[];
  risks: string[];
};

export type OpportunityMatchResponse = {
  lead_id: string;
  matches: OpportunityMatch[];
  top_opportunity_id: string | null;
  summary: string;
};

export async function listOpportunities(params?: {
  country?: string;
  domain?: string;
  active?: boolean;
}): Promise<Opportunity[]> {
  const qs = new URLSearchParams();
  if (params?.country) qs.set("country", params.country);
  if (params?.domain) qs.set("domain", params.domain);
  if (params?.active !== undefined) qs.set("active", String(params.active));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<Opportunity[]>(`/api/v1/opportunities${query}`);
}

export async function seedOpportunities(): Promise<{ status: string; seeded: number }> {
  return request<{ status: string; seeded: number }>("/api/v1/opportunities/seed", {
    method: "POST",
  });
}

export async function matchOpportunities(leadId: string): Promise<OpportunityMatchResponse> {
  return request<OpportunityMatchResponse>(`/api/v1/opportunities/match/${leadId}`, {
    method: "POST",
  });
}

export type AutoCommunicationTemplate = {
  subject: string;
  body: string;
};

export type AutoCommunication = {
  trigger: string;
  subject: string;
  body: string;
  status: string;
  channel: string;
  due_at: string | null;
  created_at: string | null;
};

export type AutoCommunicationsList = {
  lead_id: string;
  total: number;
  communications: AutoCommunication[];
};

export async function getAutoCommunicationTemplates(): Promise<{
  templates: Record<string, AutoCommunicationTemplate>;
}> {
  return request<{ templates: Record<string, AutoCommunicationTemplate> }>("/api/v1/auto-communications/templates");
}

export async function createAutoCommunication(
  leadId: string,
  trigger: string,
  context: Record<string, unknown> = {}
): Promise<{ status: string; lead_id: string; trigger: string; created_count: number; communications: AutoCommunication[] }> {
  return request<{
    status: string;
    lead_id: string;
    trigger: string;
    created_count: number;
    communications: AutoCommunication[];
  }>(`/api/v1/auto-communications/leads/${leadId}?trigger=${encodeURIComponent(trigger)}`, {
    method: "POST",
    body: JSON.stringify(context),
  });
}

export async function listAutoCommunications(leadId: string): Promise<AutoCommunicationsList> {
  return request<AutoCommunicationsList>(`/api/v1/auto-communications/leads/${leadId}`);
}

export type AutomationChannel = "email" | "messaging" | "calendar" | "crm";

export type AutomationRule = {
  id: string;
  corporate_account_id: string;
  name: string;
  event_type: string;
  channels: AutomationChannel[];
  destinations: Record<string, string>;
  subject_template: string | null;
  body_template: string | null;
  requires_human_approval: boolean;
  status: string;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type AutomationEvent = {
  id: string;
  idempotency_key: string;
  corporate_account_id: string;
  corporate_mobility_case_id: string | null;
  event_type: string;
  entity_type: string;
  entity_id: string;
  source: string;
  payload: Record<string, unknown>;
  status: string;
  occurred_at: string;
  created_by: string;
  created_at: string;
  delivery_count: number;
};

export type AutomationDelivery = {
  id: string;
  automation_event_id: string;
  automation_rule_id: string;
  channel: AutomationChannel;
  destination: string | null;
  subject: string | null;
  payload: Record<string, unknown>;
  status: string;
  requires_human_approval: boolean;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_reason: string | null;
  dispatched_by: string | null;
  dispatched_at: string | null;
  provider_message_id: string | null;
  attempt_count: number;
  last_error: string | null;
  created_at: string;
  updated_at: string;
};

export async function listAutomationRules(accountId?: string): Promise<AutomationRule[]> {
  const suffix = accountId ? `?corporate_account_id=${encodeURIComponent(accountId)}` : "";
  return request<AutomationRule[]>(`/api/v1/automation/rules${suffix}`);
}

export async function createAutomationRule(payload: {
  corporate_account_id: string;
  name: string;
  event_type: string;
  channels: AutomationChannel[];
  destinations: Record<string, string>;
  subject_template?: string;
  body_template?: string;
  requires_human_approval: boolean;
}): Promise<AutomationRule> {
  return request<AutomationRule>("/api/v1/automation/rules", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAutomationRuleStatus(
  ruleId: string,
  status: "active" | "paused",
  reason: string
): Promise<AutomationRule> {
  return request<AutomationRule>(`/api/v1/automation/rules/${ruleId}/status`, {
    method: "POST",
    body: JSON.stringify({ status, reason }),
  });
}

export async function listAutomationEvents(accountId?: string): Promise<AutomationEvent[]> {
  const suffix = accountId ? `?corporate_account_id=${encodeURIComponent(accountId)}` : "";
  return request<AutomationEvent[]>(`/api/v1/automation/events${suffix}`);
}

export async function listAutomationDeliveries(accountId?: string): Promise<AutomationDelivery[]> {
  const suffix = accountId ? `?corporate_account_id=${encodeURIComponent(accountId)}` : "";
  return request<AutomationDelivery[]>(`/api/v1/automation/deliveries${suffix}`);
}

export async function decideAutomationDelivery(
  deliveryId: string,
  decision: "approved" | "rejected",
  reason: string
): Promise<AutomationDelivery> {
  return request<AutomationDelivery>(`/api/v1/automation/deliveries/${deliveryId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, reason }),
  });
}

export async function listTrainingCases(params?: {
  country?: string;
  profession?: string;
  limit?: number;
}): Promise<TrainingCase[]> {
  const qs = new URLSearchParams();
  if (params?.country) qs.set("country", params.country);
  if (params?.profession) qs.set("profession", params.profession);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return request<TrainingCase[]>(`/api/v1/training-cases${query}`);
}

export async function runTrainingCase(caseId: string): Promise<CoachReview> {
  return request<CoachReview>(`/api/v1/training-cases/${caseId}/run`, {
    method: "POST",
  });
}

export type Jurisdiction = {
  id: string;
  code: string;
  name: string;
  jurisdiction_type: "country" | "territory" | "autonomous_jurisdiction";
  parent_code: string | null;
  region: string | null;
  active: boolean;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
};

export type RegulatoryAuthority = {
  id: string;
  jurisdiction_id: string;
  name: string;
  authority_type: string;
  website_url: string | null;
  domains_json: string | null;
  active: boolean;
};

export type OfficialSourceView = {
  id: string;
  jurisdiction_id: string | null;
  regulatory_authority_id: string | null;
  country: string;
  domain: string;
  name: string;
  url: string;
  source_type: string;
  authority: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type RegulatoryChange = {
  id: string;
  jurisdiction_id: string;
  official_source_id: string;
  previous_snapshot_id: string | null;
  current_snapshot_id: string;
  domain: string;
  change_type: string;
  title: string;
  summary: string;
  diff_json: string | null;
  materiality: "informational" | "material" | "critical";
  status: "pending_review" | "approved" | "rejected" | "published" | string;
  effective_at: string | null;
  detected_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_notes: string | null;
  published_at: string | null;
};

export type RegulatoryClassificationEvidence = {
  line_number: number;
  direction: "added" | "removed" | "context";
  text: string;
};

export type RegulatoryClassificationProposal = {
  id: string;
  regulatory_change_id: string;
  previous_snapshot_id: string | null;
  current_snapshot_id: string;
  proposed_change_type: string;
  proposed_materiality: "informational" | "material" | "critical";
  proposed_summary: string;
  rationale: string;
  evidence: RegulatoryClassificationEvidence[];
  confidence: number;
  method: "deterministic" | "model_assisted";
  provider: string | null;
  model: string | null;
  prompt_version: string;
  model_metadata: Record<string, unknown>;
  fallback_reason: string | null;
  status: "pending_review" | "accepted" | "rejected" | "superseded" | string;
  created_by: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
};

export type RegulatoryKnowledgeNode = {
  id: string;
  node_key: string;
  node_type: string;
  label: string;
  properties: Record<string, unknown>;
  active: boolean;
  created_from_verified_rule_id: string;
  last_verified_rule_id: string;
  created_at: string;
  updated_at: string;
};

export type RegulatoryKnowledgeEdge = {
  id: string;
  edge_key: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: string;
  verified_rule_id: string;
  source_snapshot_id: string;
  regulatory_change_id: string | null;
  initial_rule_assertion_id: string | null;
  projection_version: string;
  active: boolean;
  effective_from: string | null;
  effective_to: string | null;
  retired_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RegulatoryKnowledgeGraph = {
  projection_version: string;
  generated_at?: string;
  human_published_only: boolean;
  provenance_complete: boolean;
  counts: { nodes: number; edges: number; verified_rules: number };
  nodes: RegulatoryKnowledgeNode[];
  edges: RegulatoryKnowledgeEdge[];
};

export type SourceRetrievalRun = {
  id: string;
  monitor_id: string;
  official_source_id: string;
  status: "running" | "baseline" | "unchanged" | "changed" | "not_modified" | "failed" | string;
  attempt: number;
  requested_url: string;
  final_url: string | null;
  http_status: number | null;
  content_type: string | null;
  bytes_received: number;
  snapshot_id: string | null;
  regulatory_change_id: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
};

export type SourceMonitorView = {
  id: string;
  official_source_id: string;
  source_name: string | null;
  source_url: string | null;
  country: string | null;
  domain: string | null;
  schedule_minutes: number;
  fetch_method: string;
  allowed_domains: string[];
  max_redirects: number;
  parser_profile: "generic" | "gazette_html_v1" | "structured_program_catalog_v1" | string;
  parser_config: Record<string, unknown>;
  status: string;
  fresh: boolean;
  last_checked_at: string | null;
  next_check_at: string | null;
  last_http_status: number | null;
  last_error: string | null;
  etag: string | null;
  last_modified: string | null;
};

export type RegulatoryDashboard = {
  generated_at: string;
  counts: {
    jurisdictions: number;
    authorities: number;
    official_sources: number;
    monitors: number;
    monitors_active: number;
    monitors_error: number;
    monitors_due: number;
    monitors_stale: number;
    changes_pending_review: number;
    changes_critical_pending: number;
    changes_published: number;
    recent_failed_retrievals: number;
  };
  monitors: SourceMonitorView[];
  recent_failures: SourceRetrievalRun[];
  coverage: {
    jurisdictions: Array<{
      id: string;
      code: string;
      name: string;
      region: string | null;
      authorities: number;
      official_sources: number;
      monitored_sources: number;
      fresh_monitors: number;
      stale_monitors: number;
      pending_changes: number;
      active_rules: number;
      domains: string[];
      monitoring_coverage_percent: number;
      freshness_percent: number;
    }>;
    authorities: Array<{
      id: string;
      name: string;
      authority_type: string;
      jurisdiction_id: string;
      jurisdiction_code: string | null;
      declared_domains: string[];
      official_sources: number;
      monitored_sources: number;
      fresh_monitors: number;
      monitor_errors: number;
      monitoring_coverage_percent: number;
      freshness_percent: number;
    }>;
    domains: Array<{
      domain: string;
      jurisdictions: number;
      authorities: number;
      official_sources: number;
      monitored_sources: number;
      fresh_monitors: number;
      pending_changes: number;
      active_rules: number;
      monitoring_coverage_percent: number;
      freshness_percent: number;
    }>;
  };
};

export type SourceSnapshotView = {
  id: string;
  official_source_id: string | null;
  previous_snapshot_id: string | null;
  url: string;
  content_hash: string | null;
  content_preview: string;
  http_status: number | null;
  retrieval_method: string;
  parser_version: string | null;
  status: string;
  metadata: Record<string, unknown>;
  captured_at: string;
};

export type VerifiedRule = {
  id: string;
  country: string;
  domain: string;
  rule_key: string;
  statement: string;
  official_source_id: string | null;
  jurisdiction_id: string | null;
  regulatory_change_id: string | null;
  initial_rule_assertion_id: string | null;
  source_snapshot_id: string | null;
  supersedes_rule_id: string | null;
  confidence: number;
  active: boolean;
  effective_from: string | null;
  effective_to: string | null;
  approved_by: string | null;
  published_at: string | null;
  retired_at: string | null;
  retired_by: string | null;
  retirement_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type PathwayDomain = "study" | "work" | "visa" | "scholarship" | "settlement" | "family" | "digital_nomad" | "business" | "entrepreneur" | "startup" | "investment" | "wealth" | "tax" | "corporate";

export type PathwayVersionInput = {
  official_source_id?: string | null;
  source_snapshot_id?: string | null;
  verified_rule_ids: string[];
  eligibility_criteria: Record<string, unknown>;
  required_documents: string[];
  costs: Record<string, unknown>;
  processing_time: Record<string, unknown>;
  benefits: string[];
  risks: string[];
  metadata?: Record<string, unknown>;
  effective_from?: string | null;
  effective_to?: string | null;
};

export type PathwayVersion = PathwayVersionInput & {
  id: string;
  pathway_id: string;
  version_number: number;
  lifecycle_status: string;
  supersedes_version_id: string | null;
  human_review_required: boolean;
  approved_by: string | null;
  review_notes: string | null;
  published_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type MobilityPathway = {
  id: string;
  pathway_key: string;
  name: string;
  country: string;
  domain: PathwayDomain;
  jurisdiction_id: string | null;
  description: string | null;
  catalogue_status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  current_version: PathwayVersion | null;
};

export type MobilityPathwayDetail = MobilityPathway & { versions: PathwayVersion[] };

export type PathwayRegulatoryImpact = {
  id: string;
  impact_type: string;
  status: string;
  materiality: string;
  event_at: string;
  pathway_id: string;
  pathway_key: string;
  pathway_name: string;
  pathway_country: string;
  pathway_domain: string;
  pathway_version_id: string;
  pathway_version_number: number;
  pathway_version_lifecycle_status: string;
  verified_rule_id: string;
  rule_key: string;
  rule_active: boolean;
  superseded_rule_id: string | null;
  regulatory_change_id: string;
  change_type: string;
  source_snapshot_id: string;
  graph_rule_node_id: string | null;
  graph_projection_version: string;
  match_basis: string[];
  impact_context: Record<string, unknown>;
  client_assessment_count_at_detection: number;
  timeline_count_at_detection: number;
  client_assessments_unchanged: boolean;
  human_review_required: boolean;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  replacement_pathway_version_id: string | null;
  created_at: string;
  updated_at: string;
};

export type PathwayRegulatoryImpactQueue = {
  total_returned: number;
  counts_by_status: Record<string, number>;
  pending_review: number;
  client_assessments_unchanged: boolean;
  impacts: PathwayRegulatoryImpact[];
};

export type PathwayCostExplanation = {
  currency: string;
  one_time_total: number | null;
  monthly_total: number | null;
  annual_total: number | null;
  minimum_funds: number | null;
  components: Record<string, number>;
  notes: string[];
};

export type PathwayRiskExplanation = {
  level: "low" | "medium" | "high";
  score: number;
  declared_risks: string[];
  evidence_risks: string[];
  regulatory_risks: string[];
};

export type PathwayComparisonItem = {
  pathway: MobilityPathway;
  match_score: number;
  confidence: number;
  reasons: string[];
  cost: PathwayCostExplanation;
  risk: PathwayRiskExplanation;
  missing_evidence: string[];
  benefits: string[];
  tradeoffs: string[];
  explanation: string;
  verified_rule_ids: string[];
};

export type PathwayComparison = {
  assessment_id: string | null;
  lead_id: string;
  profile_id: string | null;
  profile_version: number | null;
  status: string;
  consent_status: string;
  primary: PathwayComparisonItem | null;
  alternatives: PathwayComparisonItem[];
  missing_evidence: string[];
  summary: string;
  human_review_required: boolean;
  generated_by: string;
  generated_at: string;
};

export type ReassessmentRegulatoryChange = {
  impact_id: string;
  pathway_id: string;
  pathway_name: string;
  affected_pathway_version_id: string;
  affected_pathway_version_number: number;
  replacement_pathway_version_id: string;
  replacement_pathway_version_number: number;
  verified_rule_id: string;
  materiality: string;
  reviewed_by: string;
  reviewed_at: string;
  review_notes: string;
};

export type ReassessmentCandidate = {
  lead_id: string;
  baseline_assessment_id: string;
  baseline_profile_id: string | null;
  baseline_profile_version: number | null;
  current_profile_id: string | null;
  current_profile_version: number | null;
  profile_update_available: boolean;
  regulatory_changes: ReassessmentRegulatoryChange[];
  requires_acceptance: boolean;
  pinned_assessment_unchanged: boolean;
  summary: string;
};

export type ReassessmentAcceptance = {
  id: string;
  lead_id: string;
  baseline_assessment_id: string;
  accepted_profile_id: string | null;
  accepted_profile_version: number | null;
  regulatory_impact_ids: string[];
  accepted_pathway_version_ids: string[];
  explicit_user_acceptance: boolean;
  user_attestation: string;
  notes: string;
  status: string;
  recorded_by: string;
  accepted_at: string;
  consumed_at: string | null;
  generated_assessment_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CountryLongTermDependency = {
  stage: "permanent_residence" | "citizenship";
  status: "recorded" | "not_recorded" | "not_applicable";
  summary: string;
  minimum_years: number | null;
  dependencies: string[];
  pathway_version_id: string | null;
  verified_rule_ids: string[];
  human_reviewed_source: boolean;
};

export type CountryRankingUncertainty = {
  level: "low" | "medium" | "high";
  score: number;
  factors: string[];
  global_coverage_boundary: boolean;
};

export type CountryRankingScope = {
  ranking_scope: "complete_global_catalogue" | "reviewed_published_catalogue_only";
  global_coverage_claim_ready: boolean;
  complete_global_ranking_claim_allowed: boolean;
  registry_release_version: string | null;
  registry_entries: number;
  coverage_required: number;
  coverage_ready: number;
  published_catalogue_countries: number;
  published_pathway_versions: number;
  message: string;
};

export type CountryRankingItem = {
  rank: number;
  country: string;
  ranking_score: number;
  profile_match_score: number;
  confidence: number;
  reviewed_coverage_ready: boolean;
  pathway_count: number;
  primary_pathway: PathwayComparisonItem;
  alternative_pathways: PathwayComparisonItem[];
  tradeoffs: string[];
  long_term_dependencies: CountryLongTermDependency[];
  uncertainty: CountryRankingUncertainty;
  explanation: string;
};

export type CountryRanking = {
  assessment_id: string | null;
  lead_id: string;
  profile_id: string | null;
  profile_version: number | null;
  status: string;
  consent_status: string;
  scope: CountryRankingScope;
  countries: CountryRankingItem[];
  explicit_user_acceptance: boolean;
  user_attestation: string;
  notes: string;
  summary: string;
  human_review_required: boolean;
  generated_by: string;
  generated_at: string;
};

export type MobilityTimelineMilestone = {
  id: string;
  timeline_id: string;
  stage_order: number;
  stage_key: string;
  title: string;
  description: string | null;
  status: string;
  dependencies: string[];
  required_evidence: string[];
  owner_role: string;
  due_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  blockers: string[];
  notes: string | null;
  requires_human_approval: boolean;
  approved_by: string | null;
};

export type MobilityTimeline = {
  id: string;
  lead_id: string;
  profile_id: string | null;
  profile_version: number | null;
  comparison_assessment_id: string;
  primary_pathway_id: string;
  primary_pathway_version_id: string;
  title: string;
  status: string;
  current_stage_key: string | null;
  target_date: string | null;
  schedule: Record<string, unknown>;
  generated_by: string;
  activated_by: string | null;
  activated_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  milestones: MobilityTimelineMilestone[];
};

export type MobilityScenarioStageType =
  | "study"
  | "graduate_rights"
  | "work_permit"
  | "skilled_migration"
  | "settlement"
  | "permanent_residence"
  | "citizenship_review";

export type MobilityScenarioStage = {
  id: string;
  scenario_id: string;
  stage_order: number;
  stage_type: MobilityScenarioStageType;
  title: string;
  country: string;
  domain: string;
  pathway_id: string;
  pathway_version_id: string;
  planned_start: string;
  planned_end: string;
  duration_months: number;
  gap_months_before: number;
  dependencies: string[];
  verified_rule_ids: string[];
  source_snapshot_ids: string[];
  timing_basis: Record<string, unknown>;
  uncertainty: Record<string, unknown>;
  human_confirmation_required: boolean;
  created_at: string;
};

export type MobilityScenario = {
  id: string;
  lead_id: string;
  profile_id: string | null;
  profile_version: number | null;
  baseline_timeline_id: string | null;
  scenario_version: number;
  supersedes_scenario_id: string | null;
  title: string;
  status: string;
  start_date: string;
  countries: string[];
  pathway_version_ids: string[];
  verified_rule_ids: string[];
  regulatory_impact_ids: string[];
  explicit_user_acceptance: boolean;
  user_attestation: string;
  review_notes: string;
  human_confirmation_required: boolean;
  original_scenario_preserved: boolean;
  global_coverage_claim_ready: boolean;
  warning: string;
  reviewed_by: string;
  reviewed_at: string;
  created_at: string;
  stages: MobilityScenarioStage[];
};

export type MobilityScenarioRecalculationCandidate = {
  scenario_id: string;
  scenario_version: number;
  available: boolean;
  impacts: Array<{
    impact_id: string;
    pathway_version_id: string;
    replacement_pathway_version_id: string;
    impact_type: string;
    materiality: string;
    review_notes: string | null;
    affected_stage_orders: number[];
    event_at: string;
  }>;
  message: string;
  original_scenario_preserved: boolean;
  automatic_recalculation_performed: boolean;
};

export async function listOfficialSources(params?: { country?: string; domain?: string }): Promise<{ total: number; sources: OfficialSourceView[] }> {
  const search = new URLSearchParams();
  if (params?.country) search.set("country", params.country);
  if (params?.domain) search.set("domain", params.domain);
  const query = search.toString();
  return request<{ total: number; sources: OfficialSourceView[] }>(`/api/v1/official-sources${query ? `?${query}` : ""}`);
}

export async function listPathways(params?: { country?: string; domain?: string; catalogue_status?: string }): Promise<MobilityPathway[]> {
  const search = new URLSearchParams();
  if (params?.country) search.set("country", params.country);
  if (params?.domain) search.set("domain", params.domain);
  if (params?.catalogue_status) search.set("catalogue_status", params.catalogue_status);
  const query = search.toString();
  return request<MobilityPathway[]>(`/api/v1/pathways${query ? `?${query}` : ""}`);
}

export async function listPathwayRegulatoryImpacts(params?: {
  status?: string;
  pathway_id?: string;
  pathway_version_id?: string;
  verified_rule_id?: string;
  impact_type?: string;
  limit?: number;
}): Promise<PathwayRegulatoryImpactQueue> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.pathway_id) search.set("pathway_id", params.pathway_id);
  if (params?.pathway_version_id) search.set("pathway_version_id", params.pathway_version_id);
  if (params?.verified_rule_id) search.set("verified_rule_id", params.verified_rule_id);
  if (params?.impact_type) search.set("impact_type", params.impact_type);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return request<PathwayRegulatoryImpactQueue>(`/api/v1/pathways/regulatory-impacts${query ? `?${query}` : ""}`);
}

export async function reviewPathwayRegulatoryImpact(
  impactId: string,
  payload: {
    decision: "acknowledged" | "no_change_required" | "new_version_required" | "resolved";
    notes: string;
    replacement_pathway_version_id?: string | null;
  }
): Promise<PathwayRegulatoryImpact> {
  return request<PathwayRegulatoryImpact>(`/api/v1/pathways/regulatory-impacts/${impactId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPathway(pathwayId: string): Promise<MobilityPathwayDetail> {
  return request<MobilityPathwayDetail>(`/api/v1/pathways/${pathwayId}`);
}

export async function createPathway(payload: PathwayVersionInput & {
  pathway_key: string;
  name: string;
  country: string;
  domain: PathwayDomain;
  jurisdiction_id?: string | null;
  description?: string | null;
}): Promise<MobilityPathway> {
  return request<MobilityPathway>("/api/v1/pathways", { method: "POST", body: JSON.stringify(payload) });
}

export async function createPathwayVersion(pathwayId: string, payload: PathwayVersionInput): Promise<PathwayVersion> {
  return request<PathwayVersion>(`/api/v1/pathways/${pathwayId}/versions`, { method: "POST", body: JSON.stringify(payload) });
}

export async function publishPathwayVersion(versionId: string, reviewNotes: string): Promise<MobilityPathway> {
  return request<MobilityPathway>(`/api/v1/pathways/versions/${versionId}/publish`, {
    method: "POST",
    body: JSON.stringify({ review_notes: reviewNotes }),
  });
}

export async function retirePathway(pathwayId: string, reason: string): Promise<MobilityPathway> {
  return request<MobilityPathway>(`/api/v1/pathways/${pathwayId}/retire`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function generateCountryRanking(
  leadId: string,
  payload: {
    explicit_user_acceptance: boolean;
    user_attestation: string;
    notes: string;
    limit_countries?: number;
  },
): Promise<CountryRanking> {
  return request<CountryRanking>(`/api/v1/pathways/country-rankings/${leadId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getLatestCountryRanking(leadId: string): Promise<CountryRanking> {
  return request<CountryRanking>(`/api/v1/pathways/country-rankings/${leadId}/latest`);
}

export async function getCountryRankingHistory(leadId: string): Promise<CountryRanking[]> {
  return request<CountryRanking[]>(`/api/v1/pathways/country-rankings/${leadId}`);
}

export async function comparePathways(leadId: string, limit = 5): Promise<PathwayComparison> {
  return request<PathwayComparison>(`/api/v1/pathways/compare/${leadId}?limit=${limit}`, { method: "POST" });
}

export async function getLatestPathwayComparison(leadId: string): Promise<PathwayComparison> {
  return request<PathwayComparison>(`/api/v1/pathways/comparisons/${leadId}/latest`);
}

export async function getPathwayComparisonHistory(leadId: string): Promise<PathwayComparison[]> {
  return request<PathwayComparison[]>(`/api/v1/pathways/comparisons/${leadId}`);
}

export async function getReassessmentCandidate(leadId: string): Promise<ReassessmentCandidate> {
  return request<ReassessmentCandidate>(`/api/v1/pathways/comparisons/${leadId}/reassessment`);
}

export async function listReassessmentAcceptances(leadId: string): Promise<ReassessmentAcceptance[]> {
  return request<ReassessmentAcceptance[]>(`/api/v1/pathways/comparisons/${leadId}/reassessment-acceptances`);
}

export async function createReassessmentAcceptance(
  leadId: string,
  payload: {
    baseline_assessment_id: string;
    accept_profile_version: boolean;
    regulatory_impact_ids: string[];
    explicit_user_acceptance: boolean;
    user_attestation: string;
    notes: string;
  },
): Promise<ReassessmentAcceptance> {
  return request<ReassessmentAcceptance>(`/api/v1/pathways/comparisons/${leadId}/reassessment-acceptances`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function executeReassessmentAcceptance(acceptanceId: string): Promise<PathwayComparison> {
  return request<PathwayComparison>(`/api/v1/pathways/reassessment-acceptances/${acceptanceId}/execute`, {
    method: "POST",
  });
}

export async function listMobilityTimelines(leadId?: string): Promise<MobilityTimeline[]> {
  return request<MobilityTimeline[]>(`/api/v1/mobility-timelines${leadId ? `?lead_id=${leadId}` : ""}`);
}

export async function generateMobilityTimeline(assessmentId: string): Promise<MobilityTimeline> {
  return request<MobilityTimeline>(`/api/v1/mobility-timelines/from-comparison/${assessmentId}`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function activateMobilityTimeline(timelineId: string): Promise<MobilityTimeline> {
  return request<MobilityTimeline>(`/api/v1/mobility-timelines/${timelineId}/activate`, { method: "POST" });
}

export async function transitionMobilityMilestone(
  timelineId: string,
  milestoneId: string,
  action: "start" | "complete" | "block" | "unblock",
  note?: string,
): Promise<MobilityTimeline> {
  return request<MobilityTimeline>(`/api/v1/mobility-timelines/${timelineId}/milestones/${milestoneId}/transition`, {
    method: "POST",
    body: JSON.stringify({ action, note: note || null }),
  });
}

export async function listMobilityScenarios(leadId?: string): Promise<MobilityScenario[]> {
  return request<MobilityScenario[]>(`/api/v1/mobility-timelines/scenarios${leadId ? `?lead_id=${leadId}` : ""}`);
}

export async function createMobilityScenario(payload: {
  lead_id: string;
  title: string;
  start_date: string;
  baseline_timeline_id?: string | null;
  stages: Array<{
    stage_type: MobilityScenarioStageType;
    pathway_version_id: string;
    duration_months: number;
    gap_months_before: number;
    title?: string | null;
  }>;
  explicit_user_acceptance: boolean;
  user_attestation: string;
  review_notes: string;
}): Promise<MobilityScenario> {
  return request<MobilityScenario>("/api/v1/mobility-timelines/scenarios", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMobilityScenarioRecalculationCandidate(
  scenarioId: string,
): Promise<MobilityScenarioRecalculationCandidate> {
  return request<MobilityScenarioRecalculationCandidate>(
    `/api/v1/mobility-timelines/scenarios/${scenarioId}/recalculation-candidate`,
  );
}

export async function recalculateMobilityScenario(
  scenarioId: string,
  payload: {
    regulatory_impact_ids: string[];
    explicit_user_acceptance: boolean;
    user_attestation: string;
    review_notes: string;
  },
): Promise<MobilityScenario> {
  return request<MobilityScenario>(`/api/v1/mobility-timelines/scenarios/${scenarioId}/recalculate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getDocumentStoragePosture(): Promise<DocumentStoragePosture> {
  return request<DocumentStoragePosture>("/api/v1/document-access/storage-posture");
}

export async function listDocumentAccessGrants(params?: { lead_id?: string; document_id?: string; status?: string }): Promise<DocumentAccessGrant[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.document_id) search.set("document_id", params.document_id);
  if (params?.status) search.set("status", params.status);
  const query = search.toString();
  return request<DocumentAccessGrant[]>(`/api/v1/document-access/grants${query ? `?${query}` : ""}`);
}

export async function issueDocumentAccessGrant(
  documentId: string,
  leadId: string,
  purpose = "operator_review",
): Promise<DocumentAccessGrantIssued> {
  return request<DocumentAccessGrantIssued>(`/api/v1/document-access/documents/${documentId}/grants`, {
    method: "POST",
    body: JSON.stringify({ lead_id: leadId, purpose, ttl_seconds: 120, max_uses: 1 }),
  });
}

export async function revokeDocumentAccessGrant(grantId: string, reason: string): Promise<DocumentAccessGrant> {
  return request<DocumentAccessGrant>(`/api/v1/document-access/grants/${grantId}/revoke`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function downloadDocumentWithAccessToken(token: string): Promise<{ blob: Blob; filename: string }> {
  const useLocalHeaderAuth =
    process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE === "true" ||
    (process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE !== "false");
  const response = await fetch(`${API_BASE}/api/v1/document-access/content`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(useLocalHeaderAuth
        ? {
            "x-gmai-role": process.env.NEXT_PUBLIC_GMAI_ROLE || "admin",
            "x-gmai-user": process.env.NEXT_PUBLIC_GMAI_USER || "frontend-operator",
          }
        : {}),
    },
    credentials: "include",
    cache: "no-store",
    body: JSON.stringify({ token }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  const disposition = response.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return { blob: await response.blob(), filename: match?.[1] || "document.bin" };
}

export async function listDocumentSchemas(): Promise<DocumentSchemaDefinition[]> {
  return request<DocumentSchemaDefinition[]>("/api/v1/document-intelligence/schemas");
}

export async function seedDocumentSchemas(): Promise<DocumentSchemaDefinition[]> {
  return request<DocumentSchemaDefinition[]>("/api/v1/document-intelligence/schemas/seed", { method: "POST" });
}

export async function listDocumentExtractions(params?: { lead_id?: string; document_id?: string; status?: string }): Promise<DocumentExtractionJob[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.document_id) search.set("document_id", params.document_id);
  if (params?.status) search.set("status", params.status);
  const query = search.toString();
  return request<DocumentExtractionJob[]>(`/api/v1/document-intelligence/extractions${query ? `?${query}` : ""}`);
}

export async function queueDocumentExtraction(documentId: string, language = "eng"): Promise<DocumentExtractionJob> {
  return request<DocumentExtractionJob>(`/api/v1/document-intelligence/documents/${documentId}/extract`, {
    method: "POST",
    body: JSON.stringify({ language }),
  });
}

export async function reviewDocumentExtraction(jobId: string, decision: "approved" | "rejected", notes: string): Promise<DocumentExtractionJob> {
  return request<DocumentExtractionJob>(`/api/v1/document-intelligence/extractions/${jobId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}

export async function listDocumentConsistencyAssessments(leadId?: string): Promise<DocumentConsistencyAssessment[]> {
  return request<DocumentConsistencyAssessment[]>(`/api/v1/document-intelligence/validations${leadId ? `?lead_id=${leadId}` : ""}`);
}

export async function validateDocumentExtraction(jobId: string, applicationId?: string): Promise<DocumentConsistencyAssessment> {
  return request<DocumentConsistencyAssessment>(`/api/v1/document-intelligence/extractions/${jobId}/validate`, {
    method: "POST",
    body: JSON.stringify({ application_id: applicationId || null }),
  });
}

export async function reviewDocumentConsistencyAssessment(
  assessmentId: string,
  decision: "approved" | "rejected",
  notes: string,
): Promise<DocumentConsistencyAssessment> {
  return request<DocumentConsistencyAssessment>(`/api/v1/document-intelligence/validations/${assessmentId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}

export async function listDocumentExpiryReminders(params?: { lead_id?: string; status?: string }): Promise<DocumentExpiryReminder[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.status) search.set("status", params.status);
  const query = search.toString();
  return request<DocumentExpiryReminder[]>(`/api/v1/document-intelligence/expiry-reminders${query ? `?${query}` : ""}`);
}

export async function scanDocumentExpiryReminders(leadId?: string): Promise<DocumentExpiryScanResult> {
  return request<DocumentExpiryScanResult>("/api/v1/document-intelligence/expiry-reminders/scan", {
    method: "POST",
    body: JSON.stringify({ lead_id: leadId || null }),
  });
}

export async function reviewDocumentExpiryReminder(
  reminderId: string,
  decision: "acknowledged" | "dismissed" | "resolved",
  notes: string,
): Promise<DocumentExpiryReminder> {
  return request<DocumentExpiryReminder>(`/api/v1/document-intelligence/expiry-reminders/${reminderId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}

export async function listDocumentRequirementAssessments(params?: { lead_id?: string; review_status?: string; result_status?: string }): Promise<DocumentRequirementAssessment[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.review_status) search.set("review_status", params.review_status);
  if (params?.result_status) search.set("result_status", params.result_status);
  const query = search.toString();
  return request<DocumentRequirementAssessment[]>(`/api/v1/document-intelligence/requirement-assessments${query ? `?${query}` : ""}`);
}

export async function scanDocumentRequirementAssessments(leadId?: string): Promise<DocumentRequirementScanResult> {
  return request<DocumentRequirementScanResult>("/api/v1/document-intelligence/requirement-assessments/scan", {
    method: "POST",
    body: JSON.stringify({ lead_id: leadId || null }),
  });
}

export async function generateDocumentRequirementAssessment(payload: {
  lead_id: string;
  application_id?: string | null;
  pathway_version_id?: string | null;
}): Promise<DocumentRequirementAssessment> {
  return request<DocumentRequirementAssessment>("/api/v1/document-intelligence/requirement-assessments/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewDocumentRequirementAssessment(
  assessmentId: string,
  decision: "approved" | "rejected",
  notes: string,
): Promise<DocumentRequirementAssessment> {
  return request<DocumentRequirementAssessment>(`/api/v1/document-intelligence/requirement-assessments/${assessmentId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}


export async function listDocumentFraudRiskAssessments(params?: { lead_id?: string; review_status?: string; risk_band?: string }): Promise<DocumentFraudRiskAssessment[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.review_status) search.set("review_status", params.review_status);
  if (params?.risk_band) search.set("risk_band", params.risk_band);
  const query = search.toString();
  return request<DocumentFraudRiskAssessment[]>(`/api/v1/document-intelligence/fraud-risk-assessments${query ? `?${query}` : ""}`);
}

export async function scanDocumentFraudRiskAssessments(leadId?: string): Promise<DocumentFraudRiskScanResult> {
  return request<DocumentFraudRiskScanResult>("/api/v1/document-intelligence/fraud-risk-assessments/scan", {
    method: "POST",
    body: JSON.stringify({ lead_id: leadId || null }),
  });
}

export async function reviewDocumentFraudRiskAssessment(
  assessmentId: string,
  decision: "cleared" | "specialist_review_required" | "dismissed",
  notes: string,
): Promise<DocumentFraudRiskAssessment> {
  return request<DocumentFraudRiskAssessment>(`/api/v1/document-intelligence/fraud-risk-assessments/${assessmentId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });
}

export type GlobalIntelligenceFilterParams = {
  freshness?: string;
  coverage?: string;
  authority_id?: string;
  confidence?: string;
  materiality?: string;
  review_state?: string;
};

export async function getGlobalIntelligenceDashboard(
  windowDays = 90,
  filters: GlobalIntelligenceFilterParams = {},
): Promise<GlobalIntelligenceDashboard> {
  const params = new URLSearchParams({ window_days: String(windowDays) });
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "all") params.set(key, value);
  });
  return request<GlobalIntelligenceDashboard>(`/api/v1/global-intelligence/dashboard?${params.toString()}`);
}

export async function getGlobalJurisdictionRegistry(): Promise<GlobalJurisdictionRegistry> {
  return request<GlobalJurisdictionRegistry>("/api/v1/global-intelligence/registry");
}

export async function getJurisdictionCoverageWorklist(
  gap = "all",
  region = "all",
  limit = 249,
): Promise<JurisdictionCoverageWorklist> {
  const params = new URLSearchParams({ gap, region, limit: String(limit) });
  return request<JurisdictionCoverageWorklist>(
    `/api/v1/global-intelligence/registry/coverage-worklist?${params.toString()}`,
  );
}

export async function listJurisdictionCoverageBatches(
  limit = 50,
): Promise<{ total: number; batches: JurisdictionCoverageEvidenceBatch[] }> {
  return request<{ total: number; batches: JurisdictionCoverageEvidenceBatch[] }>(
    `/api/v1/global-intelligence/registry/coverage-batches?limit=${limit}`,
  );
}

export async function getCoverageTrancheAssistantConfig(): Promise<CoverageTrancheAssistantConfig> {
  return request<CoverageTrancheAssistantConfig>(
    "/api/v1/global-intelligence/registry/coverage-tranche-assistant/config",
  );
}

export async function prepareCoverageTranche(
  batchId: string,
  payload: {
    alpha2_codes: string[];
    dry_run?: boolean;
    queue_eligible_baselines?: boolean;
    include_candidate_assertions?: boolean;
    max_candidate_lines?: number;
  },
): Promise<CoverageTrancheAssistantResult> {
  return request<CoverageTrancheAssistantResult>(
    `/api/v1/global-intelligence/registry/coverage-batches/${batchId}/assistant/prepare`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function getJurisdictionCoverageBaselineStatus(
  batchId: string,
): Promise<JurisdictionCoverageBaselineStatus> {
  return request<JurisdictionCoverageBaselineStatus>(
    `/api/v1/global-intelligence/registry/coverage-batches/${batchId}/baseline-status`,
  );
}

export async function queueJurisdictionCoverageBaselines(
  batchId: string,
): Promise<JurisdictionCoverageBaselineStatus> {
  return request<JurisdictionCoverageBaselineStatus>(
    `/api/v1/global-intelligence/registry/coverage-batches/${batchId}/capture-baselines`,
    { method: "POST" },
  );
}

export async function listInitialRuleAssertions(
  batchId: string,
): Promise<{ total: number; assertions: InitialRuleAssertion[] }> {
  return request<{ total: number; assertions: InitialRuleAssertion[] }>(
    `/api/v1/global-intelligence/registry/coverage-batches/${batchId}/initial-rule-assertions`,
  );
}

export async function proposeInitialRuleAssertion(
  batchId: string,
  payload: {
    alpha2_code: string;
    domain: string;
    title: string;
    rule_key: string;
    statement: string;
    rationale: string;
    evidence_excerpt: string;
    confidence: number;
    effective_from?: string | null;
    effective_to?: string | null;
  },
): Promise<InitialRuleAssertion> {
  return request<InitialRuleAssertion>(
    `/api/v1/global-intelligence/registry/coverage-batches/${batchId}/initial-rule-assertions`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function reviewInitialRuleAssertion(
  assertionId: string,
  decision: "approved" | "rejected",
  notes: string,
): Promise<InitialRuleAssertion> {
  return request<InitialRuleAssertion>(
    `/api/v1/global-intelligence/registry/initial-rule-assertions/${assertionId}/review`,
    { method: "POST", body: JSON.stringify({ decision, notes }) },
  );
}

export async function publishInitialRuleAssertion(
  assertionId: string,
  publicationNotes: string,
): Promise<{
  initial_rule_assertion: InitialRuleAssertion;
  verified_rule: VerifiedRule;
  coverage_receipt: InitialRulePublicationReceipt;
}> {
  return request<{
    initial_rule_assertion: InitialRuleAssertion;
    verified_rule: VerifiedRule;
    coverage_receipt: InitialRulePublicationReceipt;
  }>(
    `/api/v1/global-intelligence/registry/initial-rule-assertions/${assertionId}/publish`,
    { method: "POST", body: JSON.stringify({ attestation: true, publication_notes: publicationNotes }) },
  );
}

export async function createJurisdictionCoverageBatch(payload: {
  name: string;
  notes: string;
  items: Array<{
    alpha2_code: string;
    immigration_assessment?: {
      rule_relationship: "independent" | "parent_inherited" | "shared_or_coordinated" | "not_applicable" | "unclear";
      parent_code?: string | null;
      evidence_url: string;
      evidence_title: string;
      rationale: string;
      official_source_id?: string | null;
      source_snapshot_id?: string | null;
    };
    source_certification?: {
      regulatory_authority_id: string;
      official_source_id: string;
      coverage_domains: string[];
      evidence_notes: string;
    };
    source_onboarding?: {
      authority_name: string;
      authority_type?: string;
      authority_website_url?: string | null;
      authority_domains: string[];
      source_name: string;
      source_url: string;
      source_domain: string;
      source_type?: "government" | "official" | "official_portal" | "official_agency" | "gazette";
      schedule_minutes?: number;
      fetch_method?: "http" | "browser" | "api" | "manual";
      allowed_domains?: string[];
      max_redirects?: number;
      parser_profile?: "generic" | "gazette_html_v1" | "structured_program_catalog_v1";
      parser_config?: Record<string, unknown>;
      certification_domains: string[];
      evidence_notes: string;
    };
  }>;
}): Promise<JurisdictionCoverageEvidenceBatch> {
  return request<JurisdictionCoverageEvidenceBatch>(
    "/api/v1/global-intelligence/registry/coverage-batches",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function proposeJurisdictionImmigrationAssessment(
  jurisdictionId: string,
  payload: {
    rule_relationship: "independent" | "parent_inherited" | "shared_or_coordinated" | "not_applicable" | "unclear";
    parent_code?: string | null;
    evidence_url: string;
    evidence_title: string;
    rationale: string;
    official_source_id?: string | null;
    source_snapshot_id?: string | null;
  },
): Promise<JurisdictionImmigrationAssessment> {
  return request<JurisdictionImmigrationAssessment>(
    `/api/v1/global-intelligence/registry/${jurisdictionId}/immigration-assessments`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function reviewJurisdictionImmigrationAssessment(
  assessmentId: string,
  decision: "approved" | "rejected",
  notes: string,
): Promise<JurisdictionImmigrationAssessment> {
  return request<JurisdictionImmigrationAssessment>(
    `/api/v1/global-intelligence/registry/immigration-assessments/${assessmentId}/review`,
    { method: "POST", body: JSON.stringify({ decision, notes }) },
  );
}

export async function proposeJurisdictionSourceCertification(
  jurisdictionId: string,
  payload: {
    regulatory_authority_id: string;
    official_source_id: string;
    certification_scope?: string;
    coverage_domains: string[];
    evidence_notes: string;
  },
): Promise<JurisdictionSourceCertification> {
  return request<JurisdictionSourceCertification>(
    `/api/v1/global-intelligence/registry/${jurisdictionId}/source-certifications`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function reviewJurisdictionSourceCertification(
  certificationId: string,
  decision: "approved" | "rejected",
  notes: string,
): Promise<JurisdictionSourceCertification> {
  return request<JurisdictionSourceCertification>(
    `/api/v1/global-intelligence/registry/source-certifications/${certificationId}/review`,
    { method: "POST", body: JSON.stringify({ decision, notes }) },
  );
}

export async function listJurisdictions(): Promise<{ total: number; jurisdictions: Jurisdiction[] }> {
  return request<{ total: number; jurisdictions: Jurisdiction[] }>(
    "/api/v1/regulatory-intelligence/jurisdictions"
  );
}

export async function listRegulatoryAuthorities(jurisdictionId?: string): Promise<{
  total: number;
  authorities: RegulatoryAuthority[];
}> {
  const query = jurisdictionId ? `?jurisdiction_id=${encodeURIComponent(jurisdictionId)}` : "";
  return request<{ total: number; authorities: RegulatoryAuthority[] }>(
    `/api/v1/regulatory-intelligence/authorities${query}`
  );
}

export async function createJurisdiction(payload: {
  code: string;
  name: string;
  jurisdiction_type?: "country" | "territory" | "autonomous_jurisdiction";
  parent_code?: string;
  region?: string;
  metadata?: Record<string, unknown>;
}): Promise<{ jurisdiction: Jurisdiction }> {
  return request<{ jurisdiction: Jurisdiction }>("/api/v1/regulatory-intelligence/jurisdictions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function onboardRegulatorySource(payload: {
  jurisdiction_code: string;
  jurisdiction_name: string;
  jurisdiction_type?: "country" | "territory" | "autonomous_jurisdiction";
  parent_code?: string;
  region?: string;
  authority_name: string;
  authority_type?: string;
  authority_website_url?: string;
  authority_domains: string[];
  source_name: string;
  source_url: string;
  source_domain: string;
  source_type?: "government" | "official" | "official_portal" | "official_agency" | "gazette";
  schedule_minutes?: number;
  fetch_method?: "http" | "browser" | "api" | "manual";
  allowed_domains: string[];
  max_redirects?: number;
  parser_profile?: "generic" | "gazette_html_v1" | "structured_program_catalog_v1";
  parser_config?: Record<string, unknown>;
}): Promise<{
  jurisdiction: Jurisdiction;
  authority: RegulatoryAuthority;
  official_source: OfficialSourceView;
  monitor: SourceMonitorView;
}> {
  return request("/api/v1/regulatory-intelligence/source-onboarding", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listRegulatoryChanges(status?: string): Promise<{
  total_returned: number;
  changes: RegulatoryChange[];
}> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<{ total_returned: number; changes: RegulatoryChange[] }>(
    `/api/v1/regulatory-intelligence/changes${query}`
  );
}

export async function listRegulatoryClassificationProposals(params?: {
  change_id?: string;
  status?: string;
  limit?: number;
}): Promise<{ total_returned: number; classification_proposals: RegulatoryClassificationProposal[] }> {
  const query = new URLSearchParams();
  if (params?.change_id) query.set("change_id", params.change_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/regulatory-intelligence/classification-proposals${suffix}`);
}

export async function generateRegulatoryClassificationProposal(
  changeId: string,
  payload: { use_model: boolean; actor: string }
): Promise<{ classification_proposal: RegulatoryClassificationProposal }> {
  return request(`/api/v1/regulatory-intelligence/changes/${changeId}/classification-proposals`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewRegulatoryClassificationProposal(
  proposalId: string,
  payload: { decision: "accepted" | "rejected"; reviewer: string; notes: string }
): Promise<{ classification_proposal: RegulatoryClassificationProposal }> {
  return request(`/api/v1/regulatory-intelligence/classification-proposals/${proposalId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getRegulatoryKnowledgeGraph(params?: {
  jurisdiction_id?: string;
  verified_rule_id?: string;
  active?: boolean;
  limit?: number;
}): Promise<RegulatoryKnowledgeGraph> {
  const query = new URLSearchParams();
  if (params?.jurisdiction_id) query.set("jurisdiction_id", params.jurisdiction_id);
  if (params?.verified_rule_id) query.set("verified_rule_id", params.verified_rule_id);
  if (params?.active !== undefined) query.set("active", String(params.active));
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/regulatory-intelligence/knowledge-graph${suffix}`);
}

export async function syncRegulatoryKnowledgeGraph(payload: {
  actor: string;
}): Promise<{ sync: {
  published_rules_considered: number;
  projected_rules: number;
  deactivated_edges: number;
  skipped: { verified_rule_id: string; reason: string }[];
  projection_version: string;
} }> {
  return request("/api/v1/regulatory-intelligence/knowledge-graph/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewRegulatoryChange(
  changeId: string,
  payload: { decision: "approved" | "rejected"; reviewer: string; notes: string }
): Promise<{ change: RegulatoryChange }> {
  return request<{ change: RegulatoryChange }>(
    `/api/v1/regulatory-intelligence/changes/${changeId}/review`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export async function publishRegulatoryChange(
  changeId: string,
  payload: {
    rule_key: string;
    statement: string;
    reviewer: string;
    confidence?: number;
    effective_from?: string;
    effective_to?: string;
    supersedes_rule_id?: string;
  }
): Promise<{ verified_rule: VerifiedRule }> {
  return request<{ verified_rule: VerifiedRule }>(
    `/api/v1/regulatory-intelligence/changes/${changeId}/publish`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export async function runSourceMonitor(monitorId: string): Promise<{
  status: "queued";
  monitor_id: string;
  task_id: string | null;
}> {
  return request(`/api/v1/regulatory-intelligence/source-monitors/${monitorId}/run`, {
    method: "POST",
  });
}

export async function listSourceRetrievalRuns(params?: {
  monitor_id?: string;
  status?: string;
  limit?: number;
}): Promise<{ total_returned: number; retrieval_runs: SourceRetrievalRun[] }> {
  const query = new URLSearchParams();
  if (params?.monitor_id) query.set("monitor_id", params.monitor_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/regulatory-intelligence/retrieval-runs${suffix}`);
}

export async function getRegulatoryDashboard(): Promise<RegulatoryDashboard> {
  return request<RegulatoryDashboard>("/api/v1/regulatory-intelligence/dashboard");
}

export async function listSourceMonitors(status?: string): Promise<{
  total: number;
  monitors: SourceMonitorView[];
}> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/v1/regulatory-intelligence/source-monitors${query}`);
}

export async function listSourceSnapshots(params?: {
  source_id?: string;
  status?: string;
  limit?: number;
}): Promise<{ total_returned: number; snapshots: SourceSnapshotView[] }> {
  const query = new URLSearchParams();
  if (params?.source_id) query.set("source_id", params.source_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/regulatory-intelligence/snapshots${suffix}`);
}

export async function listVerifiedRules(params?: {
  active?: boolean;
  jurisdiction_id?: string;
  domain?: string;
  limit?: number;
}): Promise<{ total_returned: number; verified_rules: VerifiedRule[] }> {
  const query = new URLSearchParams();
  if (params?.active !== undefined) query.set("active", String(params.active));
  if (params?.jurisdiction_id) query.set("jurisdiction_id", params.jurisdiction_id);
  if (params?.domain) query.set("domain", params.domain);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/regulatory-intelligence/verified-rules${suffix}`);
}

export async function retireVerifiedRule(
  ruleId: string,
  payload: { reviewer: string; reason: string; effective_to?: string }
): Promise<{ verified_rule: VerifiedRule }> {
  return request(`/api/v1/regulatory-intelligence/verified-rules/${ruleId}/retire`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type CorporateMobilityCase = {
  id: string;
  corporate_account_id: string;
  employee_lead_id: string | null;
  case_reference: string;
  case_type: "employee_relocation" | "dependant" | "sponsor_compliance" | "entrepreneur_startup" | string;
  status: "draft" | "active" | "on_hold" | "completed" | "closed" | string;
  origin_country: string | null;
  destination_country: string;
  sponsor_name: string | null;
  target_start_date: string | null;
  compliance_due_date: string | null;
  human_review_required: boolean;
  notes: string | null;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type CorporateAccount = {
  id: string;
  legal_name: string;
  display_name: string | null;
  account_status: "active" | "suspended" | "closed" | string;
  primary_country: string;
  registration_number: string | null;
  contact_name: string | null;
  contact_email: string | null;
  compliance_owner: string | null;
  notes: string | null;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type CorporateAccountDetail = CorporateAccount & { cases: CorporateMobilityCase[] };

export async function listCorporateAccounts(params?: {
  status?: string;
  country?: string;
}): Promise<CorporateAccount[]> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.country) query.set("country", params.country);
  const suffix = query.size ? `?${query.toString()}` : "";
  return request<CorporateAccount[]>(`/api/v1/corporate-mobility/accounts${suffix}`);
}

export async function getCorporateAccount(id: string): Promise<CorporateAccountDetail> {
  return request<CorporateAccountDetail>(`/api/v1/corporate-mobility/accounts/${id}`);
}

export async function createCorporateAccount(payload: {
  legal_name: string;
  display_name?: string;
  primary_country: string;
  registration_number?: string;
  contact_name?: string;
  contact_email?: string;
  compliance_owner?: string;
  notes?: string;
}): Promise<CorporateAccount> {
  return request<CorporateAccount>("/api/v1/corporate-mobility/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCorporateAccount(
  id: string,
  payload: Partial<Pick<CorporateAccount, "account_status" | "display_name" | "primary_country" | "registration_number" | "contact_name" | "contact_email" | "compliance_owner" | "notes">>,
): Promise<CorporateAccount> {
  return request<CorporateAccount>(`/api/v1/corporate-mobility/accounts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function listCorporateMobilityCases(params?: {
  account_id?: string;
  status?: string;
}): Promise<CorporateMobilityCase[]> {
  const query = new URLSearchParams();
  if (params?.account_id) query.set("account_id", params.account_id);
  if (params?.status) query.set("status", params.status);
  const suffix = query.size ? `?${query.toString()}` : "";
  return request<CorporateMobilityCase[]>(`/api/v1/corporate-mobility/cases${suffix}`);
}

export async function createCorporateMobilityCase(
  accountId: string,
  payload: {
    employee_lead_id?: string;
    case_reference?: string;
    case_type: "employee_relocation" | "dependant" | "sponsor_compliance" | "entrepreneur_startup";
    origin_country?: string;
    destination_country: string;
    sponsor_name?: string;
    target_start_date?: string;
    compliance_due_date?: string;
    notes?: string;
  },
): Promise<CorporateMobilityCase> {
  return request<CorporateMobilityCase>(`/api/v1/corporate-mobility/accounts/${accountId}/cases`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCorporateMobilityCase(
  id: string,
  payload: Partial<Pick<CorporateMobilityCase, "status" | "employee_lead_id" | "origin_country" | "destination_country" | "sponsor_name" | "target_start_date" | "compliance_due_date" | "notes">>,
): Promise<CorporateMobilityCase> {
  return request<CorporateMobilityCase>(`/api/v1/corporate-mobility/cases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export type CorporateSponsorEntity = {
  id: string; corporate_account_id: string; legal_name: string;
  sponsor_type: "employing_entity" | "host_entity" | "authorized_agent" | string;
  country: string; registration_number: string | null; contact_name: string | null;
  contact_email: string | null; status: "active" | "suspended" | "retired" | string;
  created_by: string; updated_by: string; created_at: string; updated_at: string;
};

export type CorporateCaseSponsorAssignment = {
  id: string; corporate_mobility_case_id: string; sponsor_entity_id: string;
  status: "active" | "removed" | string; created_by: string; updated_by: string;
  created_at: string; updated_at: string;
};

export type CorporateCaseDependant = {
  id: string; corporate_mobility_case_id: string; dependant_lead_id: string;
  relationship_to_employee: "spouse" | "partner" | "child" | "parent" | "other" | string;
  sponsorship_required: boolean; status: "active" | "removed" | string;
  created_by: string; updated_by: string; created_at: string; updated_at: string;
};

export type CorporateComplianceEvent = {
  id: string; corporate_mobility_case_id: string; event_type: string; title: string;
  due_at: string; status: "open" | "completed" | "waived" | string;
  evidence_required: boolean; human_review_required: boolean;
  completion_notes: string | null; completed_by: string | null; completed_at: string | null;
  created_by: string; updated_by: string; created_at: string; updated_at: string;
};

export async function listCorporateSponsors(accountId: string): Promise<CorporateSponsorEntity[]> {
  return request(`/api/v1/corporate-mobility/accounts/${accountId}/sponsors`);
}

export async function createCorporateSponsor(accountId: string, payload: {
  legal_name: string; sponsor_type: "employing_entity" | "host_entity" | "authorized_agent";
  country: string; registration_number?: string; contact_name?: string; contact_email?: string;
}): Promise<CorporateSponsorEntity> {
  return request(`/api/v1/corporate-mobility/accounts/${accountId}/sponsors`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function listCaseSponsorAssignments(caseId: string): Promise<CorporateCaseSponsorAssignment[]> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/sponsors`);
}

export async function assignCorporateSponsor(caseId: string, sponsorEntityId: string): Promise<CorporateCaseSponsorAssignment> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/sponsors`, {
    method: "POST", body: JSON.stringify({ sponsor_entity_id: sponsorEntityId }),
  });
}

export async function listCaseDependants(caseId: string): Promise<CorporateCaseDependant[]> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/dependants`);
}

export async function addCaseDependant(caseId: string, payload: {
  dependant_lead_id: string; relationship_to_employee: "spouse" | "partner" | "child" | "parent" | "other";
  sponsorship_required: boolean;
}): Promise<CorporateCaseDependant> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/dependants`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function listComplianceEvents(caseId: string): Promise<CorporateComplianceEvent[]> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/compliance-events`);
}

export async function createComplianceEvent(caseId: string, payload: {
  event_type: "filing_deadline" | "document_expiry" | "permit_renewal" | "registration" | "sponsor_report" | "payroll" | "tax" | "custom";
  title: string; due_at: string; evidence_required: boolean;
}): Promise<CorporateComplianceEvent> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/compliance-events`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function resolveComplianceEvent(
  eventId: string, status: "completed" | "waived", completionNotes?: string,
): Promise<CorporateComplianceEvent> {
  return request(`/api/v1/corporate-mobility/compliance-events/${eventId}`, {
    method: "PATCH", body: JSON.stringify({ status, completion_notes: completionNotes }),
  });
}

export type CorporateRelocationTask = {
  id: string; corporate_mobility_case_id: string; depends_on_task_id: string | null;
  title: string; category: string;
  status: "planned" | "ready" | "in_progress" | "blocked" | "awaiting_approval" | "completed" | "cancelled" | string;
  owner_role: string; due_at: string | null; requires_human_approval: boolean;
  approval_status: string; work_notes: string | null; submitted_by: string | null;
  submitted_at: string | null; completed_by: string | null; completed_at: string | null;
  created_by: string; updated_by: string; created_at: string; updated_at: string;
};

export async function listRelocationTasks(caseId: string): Promise<CorporateRelocationTask[]> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/relocation-tasks`);
}

export async function createRelocationTask(caseId: string, payload: {
  title: string;
  category: "immigration" | "relocation" | "payroll" | "tax" | "housing" | "travel" | "onboarding" | "custom";
  owner_role: string; due_at?: string; depends_on_task_id?: string; requires_human_approval: boolean;
}): Promise<CorporateRelocationTask> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/relocation-tasks`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function transitionRelocationTask(
  taskId: string,
  payload: { status: "ready" | "in_progress" | "blocked" | "completed" | "cancelled"; work_notes?: string },
): Promise<CorporateRelocationTask> {
  return request(`/api/v1/corporate-mobility/relocation-tasks/${taskId}`, {
    method: "PATCH", body: JSON.stringify(payload),
  });
}

export type EntrepreneurVentureProfile = {
  id: string; corporate_mobility_case_id: string; founder_lead_id: string;
  venture_name: string; venture_stage: string; sector: string; target_country: string;
  incorporation_country: string | null; founder_role: string; business_model_summary: string;
  status: "draft" | "evidence_pending" | "review_ready" | "reviewed" | string;
  human_review_required: boolean; submitted_by: string | null; submitted_at: string | null;
  reviewed_by: string | null; reviewed_at: string | null; review_notes: string | null;
  created_by: string; updated_by: string; created_at: string; updated_at: string;
};

export type VentureEvidenceItem = {
  id: string; venture_profile_id: string; evidence_type: string; title: string;
  declared_amount_minor: number | null; currency: string | null; document_record_id: string | null;
  notes: string | null; created_by: string; created_at: string;
};

export async function getVentureProfile(caseId: string): Promise<EntrepreneurVentureProfile> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/venture-profile`);
}

export async function createVentureProfile(caseId: string, payload: {
  founder_lead_id: string; venture_name: string; venture_stage: "idea" | "pre_seed" | "seed" | "growth" | "established";
  sector: string; target_country: string; incorporation_country?: string; founder_role: string; business_model_summary: string;
}): Promise<EntrepreneurVentureProfile> {
  return request(`/api/v1/corporate-mobility/cases/${caseId}/venture-profile`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function listVentureEvidence(profileId: string): Promise<VentureEvidenceItem[]> {
  return request(`/api/v1/corporate-mobility/venture-profiles/${profileId}/evidence`);
}

export async function addVentureEvidence(profileId: string, payload: {
  evidence_type: "business_plan" | "incorporation" | "bank_statement" | "investment_commitment" | "grant" | "revenue" | "capitalization" | "intellectual_property" | "other";
  title: string; declared_amount_minor?: number; currency?: string; document_record_id?: string; notes?: string;
}): Promise<VentureEvidenceItem> {
  return request(`/api/v1/corporate-mobility/venture-profiles/${profileId}/evidence`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function submitVentureProfile(profileId: string): Promise<EntrepreneurVentureProfile> {
  return request(`/api/v1/corporate-mobility/venture-profiles/${profileId}/submit`, {
    method: "POST", body: JSON.stringify({ evidence_complete_attestation: true }),
  });
}

export type BusinessStrategyOption = {
  strategy_key: string; title: string; fit_score: number; fit_band: string;
  rationale: string[]; blockers: string[]; next_actions: string[];
  published_pathways: Array<{ pathway_id: string; pathway_version_id: string; name: string; country: string; domain: string }>;
  verified_programs: Array<{ program_id: string; program_version_id: string; name: string; country: string; program_type: string; minimum_commitment_minor: number; currency: string }>;
  verification_state: string;
};

export type BusinessAdvisoryAssessment = {
  id: string; lead_id: string | null; corporate_mobility_case_id: string | null;
  primary_intent: string; situation_text: string; feasibility_score: number; feasibility_band: string;
  information_score: number; evidence_score: number; commercial_fit_score: number; pathway_grounding_score: number;
  strategy_options: BusinessStrategyOption[]; blockers: string[]; next_actions: string[];
  evidence_basis: Array<Record<string, unknown>>; risk_flags: string[]; strategic_memo: string | null; escalation_required: boolean;
  status: string; human_review_required: boolean; generated_by: string; reviewed_by: string | null;
  reviewed_at: string | null; review_notes: string | null; score_semantics: string;
  created_at: string; updated_at: string;
};

export async function listBusinessAdvisories(): Promise<BusinessAdvisoryAssessment[]> {
  return request("/api/v1/business-mobility-advisory/assessments");
}

export async function createBusinessAdvisory(payload: {
  lead_id?: string; corporate_mobility_case_id?: string; primary_intent: string; situation: string;
  target_countries: string[]; capital_available_minor?: number; net_worth_minor?: number;
  annual_revenue_minor?: number; currency?: string; employees?: number; business_age_years?: number;
  founder_experience_years?: number; timeline_months?: number; family_relocation: boolean;
  lawful_source_of_funds_confirmed: boolean; risk_disclosures: string[]; document_record_ids: string[];
}): Promise<BusinessAdvisoryAssessment> {
  return request("/api/v1/business-mobility-advisory/assessments", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export type InvestmentProgramVersion = {
  id: string; program_id: string; version_number: number; lifecycle_status: string;
  supersedes_version_id: string | null; pathway_version_id: string; official_source_id: string;
  source_snapshot_id: string; minimum_commitment_minor: number; currency: string;
  investment_options: Array<Record<string, unknown>>; holding_period_text: string | null;
  physical_presence_text: string | null; family_scope: string[]; due_diligence: string[];
  fees: Record<string, unknown>; benefits: string[]; risks: string[];
  effective_from: string | null; effective_to: string | null; human_review_required: boolean;
  created_by: string; approved_by: string | null; review_notes: string | null;
  published_at: string | null; created_at: string; updated_at: string;
};

export type InvestmentProgram = {
  id: string; program_key: string; name: string; country: string; program_type: string;
  pathway_id: string; description: string | null; catalogue_status: string; created_by: string;
  created_at: string; updated_at: string; current_version: InvestmentProgramVersion | null;
  versions: InvestmentProgramVersion[];
};

export type InvestmentProgramOnboardingItem = {
  country: string; readiness_state: string; active_official_sources: number;
  content_addressed_snapshots: number; active_verified_rules: number;
  draft_pathways: number; published_pathways: number;
  draft_programs: number; published_programs: number; blockers: string[]; next_action: string;
};

export type InvestmentProgramOnboardingReadiness = {
  total_jurisdictions: number; source_ready: number; pathway_ready: number;
  awaiting_independent_review: number; published: number; blocked: number;
  items: InvestmentProgramOnboardingItem[];
};

export type InvestmentRuleProposal = {
  id: string; pathway_version_id: string; pathway_id: string; pathway_name: string;
  country: string; domain: string; official_source_id: string; source_snapshot_id: string;
  source_url: string; source_content_hash: string;
  rules: Array<{ rule_key: string; statement: string; evidence_scope: string }>;
  status: string; proposed_by: string; reviewed_by: string | null; reviewed_at: string | null;
  review_notes: string | null; created_verified_rule_ids: string[];
  replacement_pathway_version_id: string | null; created_at: string; updated_at: string;
};

export type InvestmentProgramInput = {
  pathway_version_id: string; official_source_id: string; source_snapshot_id: string;
  minimum_commitment_minor: number; currency: string; investment_options: Array<Record<string, unknown>>;
  holding_period_text?: string; physical_presence_text?: string; family_scope: string[];
  due_diligence: string[]; fees: Record<string, unknown>; benefits: string[]; risks: string[];
  effective_from?: string; effective_to?: string;
};

export async function listInvestmentPrograms(params?: { country?: string; program_type?: string; catalogue_status?: string }): Promise<InvestmentProgram[]> {
  const search = new URLSearchParams();
  if (params?.country) search.set("country", params.country);
  if (params?.program_type) search.set("program_type", params.program_type);
  if (params?.catalogue_status) search.set("catalogue_status", params.catalogue_status);
  return request(`/api/v1/investment-mobility/programs${search.toString() ? `?${search}` : ""}`);
}

export async function getInvestmentProgramOnboardingReadiness(limit = 8): Promise<InvestmentProgramOnboardingReadiness> {
  return request(`/api/v1/investment-mobility/onboarding/readiness?limit=${limit}`);
}

export async function listInvestmentRuleProposals(status?: string): Promise<InvestmentRuleProposal[]> {
  const search = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/v1/investment-mobility/rule-proposals${search}`);
}

export async function reviewInvestmentRuleProposal(
  proposalId: string,
  decision: "approved" | "rejected",
  reason: string,
): Promise<InvestmentRuleProposal> {
  return request(`/api/v1/investment-mobility/rule-proposals/${proposalId}/review`, {
    method: "POST", body: JSON.stringify({ decision, reason }),
  });
}

export async function createInvestmentProgram(payload: InvestmentProgramInput & {
  program_key: string; name: string; country: string;
  program_type: "residence_by_investment" | "citizenship_by_investment" | "investor_entrepreneur";
  pathway_id: string; description?: string;
}): Promise<InvestmentProgram> {
  return request("/api/v1/investment-mobility/programs", { method: "POST", body: JSON.stringify(payload) });
}

export async function publishInvestmentProgramVersion(versionId: string, reviewNotes: string): Promise<InvestmentProgram> {
  return request(`/api/v1/investment-mobility/versions/${versionId}/publish`, {
    method: "POST", body: JSON.stringify({ review_notes: reviewNotes }),
  });
}

export type InvestmentSuitabilityProgramResult = {
  program_id: string; program_version_id: string; name: string; country: string; program_type: string;
  minimum_commitment_minor: number; currency: string; readiness_score: number; readiness_band: string;
  capital_coverage_score: number; evidence_score: number; family_fit_score: number; risk_alignment_score: number;
  findings: string[]; blockers: string[]; next_actions: string[]; official_source_id: string;
  source_snapshot_id: string; pathway_version_id: string;
};

export type InvestmentSuitabilityAssessment = {
  id: string; lead_id: string; business_advisory_assessment_id: string | null;
  candidate_program_version_ids: string[]; ranked_programs: InvestmentSuitabilityProgramResult[];
  blockers: string[]; next_actions: string[]; evidence_basis: Array<Record<string, unknown>>;
  overall_readiness_score: number; readiness_band: string; status: string; human_review_required: boolean;
  generated_by: string; reviewed_by: string | null; reviewed_at: string | null; review_notes: string | null;
  score_semantics: string; created_at: string; updated_at: string;
};

export async function listInvestmentSuitabilityAssessments(leadId?: string): Promise<InvestmentSuitabilityAssessment[]> {
  return request(`/api/v1/investment-mobility/suitability/assessments${leadId ? `?lead_id=${encodeURIComponent(leadId)}` : ""}`);
}

export async function createInvestmentSuitabilityAssessment(payload: {
  lead_id: string; business_advisory_assessment_id?: string; target_countries: string[]; program_ids: string[];
  available_capital_minor: number; liquid_capital_minor?: number; net_worth_minor?: number; currency: string;
  risk_tolerance: "conservative" | "balanced" | "growth"; family_members: number; timeline_months: number;
  capital_preservation_required: boolean; lawful_source_of_funds_confirmed: boolean;
  disclosed_constraints: string[]; document_record_ids: string[];
}): Promise<InvestmentSuitabilityAssessment> {
  return request("/api/v1/investment-mobility/suitability/assessments", { method: "POST", body: JSON.stringify(payload) });
}

export type FamilyOfficeStructure = {
  name: string; structure_type: "operating_company" | "holding_company" | "trust" | "foundation";
  jurisdiction: string; beneficial_ownership_disclosed: boolean;
};

export type FamilyOfficeWorkstream = {
  workstream_key: string; title: string; readiness_score: number; readiness_band: string;
  findings: string[]; blockers: string[]; next_actions: string[];
};

export type FamilyOfficeAssessment = {
  id: string; lead_id: string; business_advisory_assessment_id: string | null;
  family_office_name: string | null; readiness_score: number; readiness_band: string;
  identity_score: number; wealth_evidence_score: number; ownership_transparency_score: number;
  governance_score: number; mobility_grounding_score: number; workstreams: FamilyOfficeWorkstream[];
  blockers: string[]; next_actions: string[]; evidence_basis: Array<Record<string, unknown>>;
  grounded_pathway_versions: Array<Record<string, unknown>>;
  grounded_program_versions: Array<Record<string, unknown>>; escalation_flags: string[];
  status: string; human_review_required: boolean; generated_by: string;
  reviewed_by: string | null; reviewed_at: string | null; review_notes: string | null;
  score_semantics: string; created_at: string; updated_at: string;
};

export async function listFamilyOfficeAssessments(params?: { lead_id?: string; status?: string }): Promise<FamilyOfficeAssessment[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.status) search.set("status", params.status);
  return request(`/api/v1/family-office-mobility/assessments${search.toString() ? `?${search}` : ""}`);
}

export async function createFamilyOfficeAssessment(payload: {
  lead_id: string; family_office_name?: string; primary_objectives: string[];
  target_jurisdictions: string[]; current_tax_residencies: string[]; citizenships: string[];
  family_members: number; structures: FamilyOfficeStructure[]; asset_classes: string[];
  estimated_net_worth_minor?: number; liquid_assets_minor?: number; currency?: string;
  source_of_wealth_status: "unconfirmed" | "documented" | "independently_verified";
  source_of_funds_status: "unconfirmed" | "documented" | "independently_verified";
  beneficial_ownership_documented: boolean; screening_status: "pending" | "cleared" | "escalated";
  pep_or_sanctions_exposure_disclosed: boolean; tax_adviser_engaged: boolean;
  legal_adviser_engaged: boolean; succession_plan_documented: boolean;
  banking_relationships_confirmed: boolean; disclosed_constraints: string[];
  document_record_ids: string[];
}): Promise<FamilyOfficeAssessment> {
  return request("/api/v1/family-office-mobility/assessments", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function reviewFamilyOfficeAssessment(
  assessmentId: string,
  decision: "approved" | "revision_required",
  reason: string,
): Promise<{ id: string; assessment_id: string; decision: string; reason: string; reviewer: string; created_at: string }> {
  return request(`/api/v1/family-office-mobility/assessments/${assessmentId}/reviews`, {
    method: "POST", body: JSON.stringify({ decision, reason }),
  });
}

export type TaxTreatyEvidence = {
  id: string; evidence_key: string; jurisdiction_a: string; jurisdiction_b: string;
  topic: string; title: string; statement: string; official_source_id: string;
  source_snapshot_id: string; source_url: string; source_content_hash: string;
  effective_from: string | null; effective_to: string | null; status: string;
  proposed_by: string; reviewed_by: string | null; reviewed_at: string | null;
  review_notes: string | null; created_at: string; updated_at: string;
};

export type TaxResidencyIssue = {
  issue_key: string; title: string; jurisdictions: string[];
  severity: "information_gap" | "specialist_review" | "material";
  rationale: string; evidence_state: string;
};

export type TaxResidencyWorkstream = {
  workstream_key: string; title: string; readiness_score: number;
  readiness_band: string; blockers: string[]; next_actions: string[];
};

export type TaxResidencyAssessment = {
  id: string; lead_id: string; family_office_assessment_id: string | null;
  business_advisory_assessment_id: string | null; tax_year: number;
  readiness_score: number; readiness_band: string; fact_completeness_score: number;
  controlled_evidence_score: number; treaty_grounding_score: number;
  specialist_coordination_score: number; issue_matrix: TaxResidencyIssue[];
  workstreams: TaxResidencyWorkstream[]; blockers: string[]; next_actions: string[];
  evidence_basis: Array<Record<string, unknown>>; treaty_evidence_ids: string[];
  escalation_flags: string[]; status: string; human_review_required: boolean;
  generated_by: string; reviewed_by: string | null; reviewed_at: string | null;
  review_notes: string | null; score_semantics: string; created_at: string; updated_at: string;
};

export async function listTaxTreatyEvidence(params?: {
  status?: string; jurisdiction?: string;
}): Promise<TaxTreatyEvidence[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.jurisdiction) search.set("jurisdiction", params.jurisdiction);
  return request(`/api/v1/tax-residency/treaty-evidence${search.toString() ? `?${search}` : ""}`);
}

export async function createTaxTreatyEvidence(payload: {
  evidence_key: string; jurisdiction_a: string; jurisdiction_b: string; topic: string;
  title: string; statement: string; official_source_id: string; source_snapshot_id: string;
  effective_from?: string; effective_to?: string;
}): Promise<TaxTreatyEvidence> {
  return request("/api/v1/tax-residency/treaty-evidence", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function decideTaxTreatyEvidence(
  evidenceId: string, decision: "approved" | "rejected", reason: string,
): Promise<TaxTreatyEvidence> {
  return request(`/api/v1/tax-residency/treaty-evidence/${evidenceId}/decisions`, {
    method: "POST", body: JSON.stringify({ decision, reason }),
  });
}

export async function listTaxResidencyAssessments(params?: {
  lead_id?: string; status?: string;
}): Promise<TaxResidencyAssessment[]> {
  const search = new URLSearchParams();
  if (params?.lead_id) search.set("lead_id", params.lead_id);
  if (params?.status) search.set("status", params.status);
  return request(`/api/v1/tax-residency/assessments${search.toString() ? `?${search}` : ""}`);
}

export async function createTaxResidencyAssessment(payload: {
  lead_id: string; family_office_assessment_id?: string;
  business_advisory_assessment_id?: string; tax_year: number;
  current_residencies: string[]; target_residencies: string[]; citizenships: string[];
  presence_periods: Array<{ jurisdiction: string; days: number }>;
  available_homes: Array<{
    jurisdiction: string;
    home_type: "owned" | "leased" | "family_home" | "employer_provided" | "other";
    continuously_available: boolean;
  }>;
  spouse_or_dependant_jurisdictions: string[]; employment_jurisdictions: string[];
  director_or_control_jurisdictions: string[]; business_structure_jurisdictions: string[];
  income_categories: string[]; planned_arrival_date?: string; planned_departure_date?: string;
  objectives: string[]; disclosed_constraints: string[]; tax_adviser_engaged: boolean;
  home_jurisdiction_adviser_engaged: boolean; destination_adviser_engaged: boolean;
  document_record_ids: string[]; treaty_evidence_ids: string[];
}): Promise<TaxResidencyAssessment> {
  return request("/api/v1/tax-residency/assessments", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export async function reviewTaxResidencyAssessment(
  assessmentId: string,
  decision: "specialist_reviewed" | "revision_required",
  reason: string,
): Promise<{ id: string; assessment_id: string; decision: string; reason: string; reviewer: string; created_at: string }> {
  return request(`/api/v1/tax-residency/assessments/${assessmentId}/reviews`, {
    method: "POST", body: JSON.stringify({ decision, reason }),
  });
}
