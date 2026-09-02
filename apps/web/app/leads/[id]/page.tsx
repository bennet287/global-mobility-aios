"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AgencySubmission,
  ApplicationAuthorityChecklistItem,
  ApplicationRecord,
  AuthorityAppointment,
  DocumentRecord,
  DocumentRequirementAssessment,
  EligibilityAssessment,
  ExternalAgencyAssignment,
  FollowUp,
  getLatestEligibilityAssessment,
  getLatestPathwayComparison,
  getLeadDetail,
  getLeads,
  HumanReview,
  Lead,
  LeadDetail as LeadDetailType,
  listAgencySubmissions,
  listApplicationAuthorityChecklistItems,
  listAuthorityAppointments,
  listDocumentRequirementAssessments,
  listExternalAgencyAssignments,
  listMobilityTimelines,
  MobilityTimeline,
  PathwayComparison,
  Profile,
  SourceReference,
  WorkflowRun,
} from "../../../lib/api";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { Topbar } from "../../../components/Topbar";
import { StatusBadge } from "../../../components/StatusBadge";
import { SectionTitle } from "../../../components/SectionTitle";
import { EmptyState } from "../../../components/EmptyState";
import { InlineNotice } from "../../../components/InlineNotice";
import { TruthClaimCard } from "../../../components/TruthClaimCard";
import { LeadIdentity } from "../../../components/LeadIdentity";
import { ActionCard, ActionItem } from "../../../components/ActionCard";
import { MetricPill } from "../../../components/MetricPill";
import { TechnicalDisclosure } from "../../../components/TechnicalDisclosure";
import { EvidenceProvenance, type EvidenceProvenanceItem } from "../../../components/EvidenceProvenance";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import { titleCase, statusTone, Tone } from "../../../lib/utils";
import {
  Skeleton,
  MetricSkeleton,
  ActionCardSkeleton,
} from "../../../components/Skeleton";
import { ClientPortalInvite } from "../../../components/ClientPortalInvite";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "truth", label: "Truth Engine" },
  { key: "agents", label: "Agent Outputs" },
  { key: "applications", label: "Applications" },
  { key: "communications", label: "Communications" },
  { key: "activity", label: "Activity" },
];

type ProfessionalCaseContext = {
  eligibility: EligibilityAssessment | null;
  comparison: PathwayComparison | null;
  timelines: MobilityTimeline[];
  requirementAssessments: DocumentRequirementAssessment[];
  appointments: AuthorityAppointment[];
  submissions: AgencySubmission[];
  agencyAssignments: ExternalAgencyAssignment[];
  checklistItems: ApplicationAuthorityChecklistItem[];
  readWarnings: string[];
};

type PersistedBlocker = {
  source: string;
  title: string;
  detail: string;
  severity: "warning" | "high";
};

type DecisionContextSpine = {
  leadId: string;
  assessmentId: string;
  profileId: string;
  profileVersion: number;
  pathwayId: string;
  pathwayVersionId: string;
};

function buildDecisionContextSpine(comparison: PathwayComparison | null): DecisionContextSpine | null {
  const primary = comparison?.primary;
  const assessmentId = comparison?.assessment_id;
  const profileId = comparison?.profile_id;
  const profileVersion = comparison?.profile_version;
  const pathwayId = primary?.pathway.id;
  const pathwayVersionId = primary?.pathway.current_version?.id;

  if (!comparison || !assessmentId || !profileId || profileVersion == null || !pathwayId || !pathwayVersionId) {
    return null;
  }

  return {
    leadId: comparison.lead_id,
    assessmentId,
    profileId,
    profileVersion,
    pathwayId,
    pathwayVersionId,
  };
}

function timelineMatchesDecisionContext(timeline: MobilityTimeline, spine: DecisionContextSpine): boolean {
  return (
    timeline.lead_id === spine.leadId &&
    timeline.comparison_assessment_id === spine.assessmentId &&
    timeline.profile_id === spine.profileId &&
    timeline.profile_version === spine.profileVersion &&
    timeline.primary_pathway_id === spine.pathwayId &&
    timeline.primary_pathway_version_id === spine.pathwayVersionId
  );
}

function requirementAssessmentMatchesDecisionContext(
  assessment: DocumentRequirementAssessment,
  spine: DecisionContextSpine,
): boolean {
  // The current comparison does not expose an eligibility_assessment_id, so eligibility lineage
  // cannot be used to prove or disprove comparison alignment here. Only identifiers present on
  // both persisted contracts are used as decision-context pins.
  return (
    assessment.lead_id === spine.leadId &&
    assessment.profile_id === spine.profileId &&
    assessment.profile_version === spine.profileVersion &&
    assessment.pathway_id === spine.pathwayId &&
    assessment.pathway_version_id === spine.pathwayVersionId
  );
}

const EMPTY_PROFESSIONAL_CONTEXT: ProfessionalCaseContext = {
  eligibility: null,
  comparison: null,
  timelines: [],
  requirementAssessments: [],
  appointments: [],
  submissions: [],
  agencyAssignments: [],
  checklistItems: [],
  readWarnings: [],
};

function formatDate(value: string | undefined | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <div className="detail-row-value">{children}</div>
    </div>
  );
}

function readWarning(label: string, reason: unknown): string | null {
  const message = reason instanceof Error ? reason.message : String(reason || "Read unavailable");
  if (/not found|no .* found|does not exist/i.test(message)) return null;
  return `${label}: ${message}`;
}

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [detail, setDetail] = useState<LeadDetailType | null>(null);
  const [allLeads, setAllLeads] = useState<Lead[]>([]);
  const [professionalContext, setProfessionalContext] = useState<ProfessionalCaseContext>(EMPTY_PROFESSIONAL_CONTEXT);
  const [professionalLoading, setProfessionalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadStatus, setLoadStatus] = useState<"idle" | "loading" | "ready" | "offline">("idle");

  const activeTab = searchParams.get("tab") || "overview";
  const setTab = (key: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", key);
    router.replace(url.pathname + url.search);
  };

  const load = async () => {
    if (!id) return;
    setLoadStatus("loading");
    setProfessionalLoading(true);
    setError(null);
    setProfessionalContext(EMPTY_PROFESSIONAL_CONTEXT);
    try {
      const [data, leads] = await Promise.all([getLeadDetail(id), getLeads()]);
      setDetail(data);
      setAllLeads(leads);
      setLoadStatus("ready");

      const coreReads = await Promise.allSettled([
        getLatestEligibilityAssessment(id),
        getLatestPathwayComparison(id),
        listMobilityTimelines(id),
        listDocumentRequirementAssessments({ lead_id: id }),
      ]);

      const authorityReadSpecs = data.applications.flatMap((application) => [
        { kind: "appointments" as const, label: `Appointments ${application.id}`, promise: listAuthorityAppointments({ application_id: application.id }) },
        { kind: "submissions" as const, label: `Submissions ${application.id}`, promise: listAgencySubmissions({ application_id: application.id }) },
        { kind: "assignments" as const, label: `Agency assignments ${application.id}`, promise: listExternalAgencyAssignments({ application_id: application.id }) },
        { kind: "checklist" as const, label: `Authority checklist ${application.id}`, promise: listApplicationAuthorityChecklistItems({ application_id: application.id }) },
      ]);
      const authorityReads = await Promise.allSettled(authorityReadSpecs.map((spec) => spec.promise));

      const warnings: string[] = [];
      const warningLabels = ["Eligibility assessment", "Pathway comparison", "Mobility timeline", "Evidence assessment"];
      coreReads.forEach((result, index) => {
        if (result.status === "rejected") {
          const warning = readWarning(warningLabels[index], result.reason);
          if (warning) warnings.push(warning);
        }
      });

      const appointments: AuthorityAppointment[] = [];
      const submissions: AgencySubmission[] = [];
      const agencyAssignments: ExternalAgencyAssignment[] = [];
      const checklistItems: ApplicationAuthorityChecklistItem[] = [];
      authorityReads.forEach((result, index) => {
        const spec = authorityReadSpecs[index];
        if (result.status === "rejected") {
          const warning = readWarning(spec.label, result.reason);
          if (warning) warnings.push(warning);
          return;
        }
        if (spec.kind === "appointments") appointments.push(...(result.value as AuthorityAppointment[]));
        if (spec.kind === "submissions") submissions.push(...(result.value as AgencySubmission[]));
        if (spec.kind === "assignments") agencyAssignments.push(...(result.value as ExternalAgencyAssignment[]));
        if (spec.kind === "checklist") checklistItems.push(...(result.value as ApplicationAuthorityChecklistItem[]));
      });

      setProfessionalContext({
        eligibility: coreReads[0].status === "fulfilled" ? coreReads[0].value as EligibilityAssessment : null,
        comparison: coreReads[1].status === "fulfilled" ? coreReads[1].value as PathwayComparison : null,
        timelines: coreReads[2].status === "fulfilled" ? coreReads[2].value as MobilityTimeline[] : [],
        requirementAssessments: coreReads[3].status === "fulfilled" ? coreReads[3].value as DocumentRequirementAssessment[] : [],
        appointments,
        submissions,
        agencyAssignments,
        checklistItems,
        readWarnings: warnings,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lead detail");
      setLoadStatus("offline");
    } finally {
      setProfessionalLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const leadIndex = useMemo(
    () => allLeads.findIndex((l) => l.id === id),
    [allLeads, id]
  );
  const prevLead = leadIndex > 0 ? allLeads[leadIndex - 1] : null;
  const nextLead = leadIndex >= 0 && leadIndex < allLeads.length - 1 ? allLeads[leadIndex + 1] : null;

  const lead = detail?.lead;
  const primaryComparison = professionalContext.comparison?.primary || null;
  const decisionContextSpine = buildDecisionContextSpine(professionalContext.comparison);

  const alignedTimelines = decisionContextSpine
    ? professionalContext.timelines.filter((timeline) => timelineMatchesDecisionContext(timeline, decisionContextSpine))
    : [];
  const alignedTimelinesByRecency = [...alignedTimelines]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
  const alignedTimeline = alignedTimelinesByRecency.find((timeline) => timeline.status === "active") || alignedTimelinesByRecency[0] || null;
  const excludedTimelines = professionalContext.timelines.filter((timeline) => !alignedTimelines.includes(timeline));

  const alignedRequirementAssessments = decisionContextSpine
    ? professionalContext.requirementAssessments.filter((assessment) =>
        requirementAssessmentMatchesDecisionContext(assessment, decisionContextSpine),
      )
    : [];
  const alignedRequirementAssessment = [...alignedRequirementAssessments]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0] || null;
  const excludedRequirementAssessments = professionalContext.requirementAssessments
    .filter((assessment) => !alignedRequirementAssessments.includes(assessment));

  const persistedBlockers = useMemo<PersistedBlocker[]>(() => {
    const blockers: PersistedBlocker[] = [];
    for (const blocker of primaryComparison?.publication_blockers || []) {
      blockers.push({ source: "Pathway review", title: "Publication / reliance blocker", detail: blocker, severity: "high" });
    }
    for (const gap of primaryComparison?.missing_evidence || []) {
      blockers.push({ source: "Pathway evidence", title: "Evidence gap", detail: gap, severity: "warning" });
    }
    for (const finding of alignedRequirementAssessment?.findings || []) {
      if (["missing", "rejected", "expired", "present_unverified", "fact_inconsistency", "duplicate_conflict"].includes(finding.outcome)) {
        blockers.push({
          source: "Document evidence",
          title: finding.requirement_label,
          detail: finding.explanation,
          severity: finding.severity === "high" ? "high" : "warning",
        });
      }
    }
    for (const milestone of alignedTimeline?.milestones || []) {
      for (const blocker of milestone.blockers) {
        blockers.push({ source: "Journey timeline", title: milestone.title, detail: blocker, severity: "warning" });
      }
    }
    return blockers.slice(0, 10);
  }, [alignedRequirementAssessment, alignedTimeline, primaryComparison]);

  const actions: ActionItem[] = useMemo(() => {
    const base: ActionItem[] = [
      {
        label: "Agent",
        title: "Run agent",
        detail: "Execute a controlled agent for this lead.",
        tone: "neutral",
        href: `/agents/console?lead_id=${id}`,
      },
    ];
    if (id) {
      base.push({
        label: "Communicate",
        title: "Draft communication pack",
        detail: "Generate post-approval client communication drafts.",
        tone: "good",
        href: `/communications/leads/${id}`,
      });
    }
    return base;
  }, [id]);

  if (loadStatus === "loading" && !detail) {
    return (
      <WorkspaceShell health={health}>
        <Topbar title="Lead detail" kicker="Professional case workspace" loadStatus="loading" onRefresh={load} />
        <section className="panel">
          <div className="lead-skeleton-header">
            <Skeleton className="skeleton-avatar-lg" />
            <div className="lead-skeleton-title">
              <Skeleton className="skeleton-title" />
              <Skeleton className="skeleton-text" />
            </div>
          </div>
          <div className="metric-row">
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
          </div>
          <div className="action-grid">
            <ActionCardSkeleton />
            <ActionCardSkeleton />
            <ActionCardSkeleton />
          </div>
        </section>
      </WorkspaceShell>
    );
  }

  if (error || !lead) {
    return (
      <WorkspaceShell health={health}>
        <Topbar title="Lead detail" kicker="Professional case workspace" loadStatus={loadStatus} onRefresh={load} />
        <section className="panel">
          <EmptyState
            title={error ? "Unable to load lead" : "Lead not found"}
            detail={error || "The requested lead could not be loaded."}
          />
          <div className="back-link">
            <Link href="/">← Back to workspace</Link>
          </div>
        </section>
      </WorkspaceShell>
    );
  }

  const metricItems: { label: string; value: number; tone: Tone }[] = [
    { label: "Truth claims", value: detail?.truth_claims.length || 0, tone: statusTone(detail?.truth_claims.some((c) => c.verdict === "NEEDS_REVIEW") ? "needs_review" : "verified") },
    { label: "Documents", value: detail?.documents.length || 0, tone: "neutral" },
    { label: "Applications", value: detail?.applications.length || 0, tone: "neutral" },
    { label: "Agent runs", value: detail?.agent_runs.length || 0, tone: "neutral" },
  ];

  const unavailableLabel = professionalLoading ? "Loading" : "Not established";
  const decisionTitle = professionalLoading
    ? "Loading persisted decision context"
    : primaryComparison?.pathway.name || "No persisted pathway decision context";
  const decisionStatus = professionalLoading
    ? "loading"
    : professionalContext.comparison?.status || "not_established";
  const decisionSummary = professionalLoading
    ? "Pathway, evidence, timeline, eligibility, and authority records are still loading. Temporary blanks must not be treated as absent state."
    : professionalContext.comparison?.summary || "No persisted pathway comparison is available for this case. Current pathway evidence and journey state are not inferred from unrelated records.";
  const nextActions = primaryComparison?.next_actions || [];
  const pendingChecklist = professionalContext.checklistItems.filter((item) => item.status === "pending").length;
  const blockedMilestones = alignedTimeline?.milestones.filter((item) => item.status === "blocked").length || 0;
  const certificationStates = Object.values(primaryComparison?.certification_statuses || {});
  const uniqueCertificationStates = Array.from(new Set(certificationStates));
  const contextMismatchCount = excludedTimelines.length + excludedRequirementAssessments.length;
  const contextAlignmentLabel = decisionContextSpine
    ? contextMismatchCount > 0 ? "Context mismatch" : "Context alignment"
    : "Context alignment not established";
  const contextAlignmentDetail = decisionContextSpine
    ? contextMismatchCount > 0
      ? `${excludedTimelines.length} timeline record(s) and ${excludedRequirementAssessments.length} document assessment(s) were excluded from the current decision because their persisted context does not match the comparison profile/pathway/version pins. Latest eligibility is shown separately and is not treated as context-aligned.`
      : "Current journey and document evidence are selected only from records matching the persisted comparison assessment/profile/pathway/version context. Latest eligibility is shown separately and is not treated as context-aligned."
    : professionalContext.comparison
      ? "The latest pathway comparison does not expose a complete assessment/profile/pathway version spine. Timeline and document-assessment records are excluded from current blockers, evidence counts, and journey state rather than being inferred into alignment."
      : "No persisted pathway comparison establishes the current decision context. Timeline and document-assessment records are historical/unassigned for this view and are excluded from current blockers, evidence counts, and journey state.";

  const officialSourceReferenceCount = detail.source_references.filter(
    (reference) => (reference.source_type || "").toLowerCase().includes("official"),
  ).length;
  const currentRuleCount = primaryComparison?.verified_rule_ids.length || 0;
  const currentEvidenceGapCount = primaryComparison?.missing_evidence.length || 0;
  const caseEvidenceState = alignedRequirementAssessment
    ? `${alignedRequirementAssessment.satisfied_count}/${alignedRequirementAssessment.required_count} satisfied`
    : "Not established";
  const caseEvidenceTone: EvidenceProvenanceItem["tone"] = alignedRequirementAssessment
    ? alignedRequirementAssessment.missing_count || alignedRequirementAssessment.inconsistency_count ? "warn" : "good"
    : "warn";
  const caseEvidenceProvenance: EvidenceProvenanceItem[] = [
    {
      key: "official-source",
      stage: "Official source",
      title: `${officialSourceReferenceCount} official-labeled source reference${officialSourceReferenceCount === 1 ? "" : "s"}`,
      state: officialSourceReferenceCount ? "Referenced" : "Not established",
      detail: "Source references support truth review, but a source URL alone does not establish certification, a VerifiedRule, or pathway applicability.",
      meta: `${detail.source_references.length} total truth-source reference${detail.source_references.length === 1 ? "" : "s"} loaded`,
      tone: officialSourceReferenceCount ? "good" : "warn",
    },
    {
      key: "verified-rule",
      stage: "VerifiedRule",
      title: currentRuleCount ? `${currentRuleCount} rule reference${currentRuleCount === 1 ? "" : "s"} pinned` : "No current rule reference",
      state: currentRuleCount ? "Pinned to comparison" : "Not established",
      detail: "Only VerifiedRule identifiers carried by the persisted pathway comparison are presented as current rule evidence here.",
      tone: currentRuleCount ? "good" : "warn",
    },
    {
      key: "pathway-evidence",
      stage: "Pathway evidence",
      title: primaryComparison?.pathway.name || "No current pathway evidence",
      state: primaryComparison ? titleCase(primaryComparison.processing_evidence_status) : "Not established",
      detail: "Pathway evidence belongs to the persisted comparison and remains distinct from an authority outcome or legal certainty.",
      meta: professionalContext.comparison ? `Comparison ${professionalContext.comparison.assessment_id}` : undefined,
      tone: primaryComparison?.processing_evidence_status === "established" ? "good" : "warn",
      current: Boolean(primaryComparison),
    },
    {
      key: "case-evidence",
      stage: "Case evidence",
      title: caseEvidenceState,
      state: alignedRequirementAssessment ? titleCase(alignedRequirementAssessment.review_status) : "Not established",
      detail: "Only the context-aligned document requirement assessment contributes current case evidence to this professional view.",
      meta: alignedRequirementAssessment
        ? `${alignedRequirementAssessment.missing_count} missing · ${alignedRequirementAssessment.inconsistency_count} inconsistencies`
        : "Historical or mismatched assessments are excluded.",
      tone: caseEvidenceTone,
    },
    {
      key: "historical",
      stage: "Superseded / historical",
      title: `${contextMismatchCount} excluded record${contextMismatchCount === 1 ? "" : "s"}`,
      state: contextMismatchCount ? "Excluded from current" : "None excluded",
      detail: "Timeline and document-assessment records that do not match the persisted comparison context remain inspectable but cannot support current blockers, readiness, or evidence conclusions.",
      tone: contextMismatchCount ? "warn" : "neutral",
    },
    {
      key: "gaps",
      stage: "Unresolved gaps",
      title: `${currentEvidenceGapCount} comparison evidence gap${currentEvidenceGapCount === 1 ? "" : "s"}`,
      state: currentEvidenceGapCount ? "Attention required" : "No comparison gap returned",
      detail: "No returned gap does not mean the case is legally clear; human review, source state, and case evidence boundaries still apply.",
      tone: currentEvidenceGapCount ? "warn" : "neutral",
    },
  ];

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={lead.full_name || "Lead detail"}
        kicker="Professional case workspace"
        loadStatus={professionalLoading || loadStatus === "loading" ? "loading" : loadStatus === "offline" ? "offline" : "ready"}
        onRefresh={load}
      />

      <div className="lead-detail-actions">
        <div className="lead-detail-nav">
          <Link href="/" className="button secondary">← Operations</Link>
          {prevLead && <Link href={`/leads/${prevLead.id}`} className="button secondary">← Prev</Link>}
          {nextLead && <Link href={`/leads/${nextLead.id}`} className="button secondary">Next →</Link>}
        </div>
        <div className="metric-row">
          {metricItems.map((m) => (
            <MetricPill key={m.label} label={m.label} value={m.value} tone={m.tone} />
          ))}
        </div>
      </div>

      <section className="lead-hero">
        <div className="lead-hero-main">
          <LeadIdentity lead={lead} />
        </div>
        <StatusBadge value={lead.status} />
      </section>

      <section className="operator-case-workbench" aria-labelledby="professional-decision-heading">
        {professionalLoading ? (
          <InlineNotice
            label="Refreshing professional case reads"
            detail="Eligibility, pathway, evidence, timeline, and authority records are still loading. Do not treat temporary blanks as absent state."
          />
        ) : null}
        {professionalContext.readWarnings.length ? (
          <InlineNotice
            label="Some professional records could not be loaded"
            detail="Treat unavailable signals as unknown, not absent. Read diagnostics are preserved in the technical provenance section below."
            tone="warn"
          />
        ) : null}
        {!professionalLoading ? (
          <InlineNotice
            label={contextAlignmentLabel}
            detail={contextAlignmentDetail}
            tone={decisionContextSpine && contextMismatchCount === 0 ? "good" : "warn"}
          />
        ) : null}
        <article className="panel operator-case-decision">
          <div className="decision-context">
            <span className="page-kicker">Decision / case context</span>
            <div className="operator-case-decision-heading">
              <div>
                <h2 id="professional-decision-heading">{decisionTitle}</h2>
                <p>{decisionSummary}</p>
              </div>
              <div className="operator-case-status-stack" aria-label="Persisted decision state">
                <StatusBadge value={decisionStatus} />
                {professionalContext.comparison?.human_review_required ? (
                  <span className="operator-review-boundary">Human review required by persisted comparison</span>
                ) : null}
              </div>
            </div>
            <div className="operator-reliance-boundary" role="note">
              <strong>Reliance boundary</strong>
              <span>Persisted operator records only. Opening this case does not evaluate eligibility, generate a comparison, create or activate a timeline, certify evidence, submit to an authority, or establish an authority outcome.</span>
            </div>
          </div>
          <div className="operator-decision-signals" aria-label="Professional case signals">
            <div><span>Latest eligibility</span><strong>{professionalContext.eligibility ? titleCase(professionalContext.eligibility.status) : unavailableLabel}</strong><small>{professionalContext.eligibility ? `${Math.round(professionalContext.eligibility.confidence * 100)}% confidence · alignment to current comparison is not established` : professionalLoading ? "Reading persisted assessment" : "No persisted assessment"}</small></div>
            <div><span>Pathway review</span><strong>{professionalContext.comparison ? titleCase(professionalContext.comparison.status) : unavailableLabel}</strong><small>{primaryComparison ? titleCase(primaryComparison.compatibility_status) : professionalLoading ? "Reading persisted comparison" : "No persisted comparison"}</small></div>
            <div><span>Aligned evidence review</span><strong>{alignedRequirementAssessment ? titleCase(alignedRequirementAssessment.review_status) : unavailableLabel}</strong><small>{alignedRequirementAssessment ? `${alignedRequirementAssessment.satisfied_count}/${alignedRequirementAssessment.required_count} required items satisfied` : professionalLoading ? "Reading requirement assessment" : "No context-aligned requirement assessment"}</small></div>
            <div><span>Aligned journey</span><strong>{alignedTimeline ? titleCase(alignedTimeline.status) : unavailableLabel}</strong><small>{alignedTimeline ? `${blockedMilestones} blocked milestone(s)` : professionalLoading ? "Reading persisted timeline" : "No context-aligned timeline"}</small></div>
          </div>
        </article>

        <section className="panel decision-section operator-case-blockers" aria-labelledby="case-blockers-heading">
          <div className="operator-section-heading">
            <div><span className="page-kicker">Blockers & uncertainty</span><h2 id="case-blockers-heading">What prevents progress or requires professional judgment</h2></div>
            <span className="operator-count-chip">{persistedBlockers.length} persisted signal{persistedBlockers.length === 1 ? "" : "s"}</span>
          </div>
          {persistedBlockers.length ? (
            <div className="operator-blocker-list">
              {persistedBlockers.map((blocker, index) => (
                <article className={`operator-blocker ${blocker.severity}`} key={`${blocker.source}-${blocker.title}-${index}`}>
                  <span>{blocker.source}</span>
                  <strong>{blocker.title}</strong>
                  <p>{blocker.detail}</p>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No aligned persisted blocker signal" detail="This does not mean the case is clear. Only the current pathway comparison plus context-aligned document and timeline records contribute here; latest eligibility and historical/mismatched records are not treated as current-decision clearance." />
          )}
        </section>

        <section className="panel decision-section operator-case-next-actions" aria-labelledby="case-actions-heading">
          <div className="operator-section-heading">
            <div><span className="page-kicker">Next governed actions</span><h2 id="case-actions-heading">Move the case forward without bypassing review</h2></div>
            <span className="operator-count-chip">{nextActions.length} persisted action{nextActions.length === 1 ? "" : "s"}</span>
          </div>
          {nextActions.length ? (
            <div className="operator-next-action-list">
              {nextActions.slice(0, 6).map((action) => (
                <article key={`${action.code}-${action.category}`}>
                  <span>{titleCase(action.category)}</span>
                  <strong>{action.title}</strong>
                  <p>{action.detail}</p>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No persisted next action" detail="Open the relevant governed workspace to review or create state deliberately; this case page does not infer a new action." />
          )}
          <nav className="operator-case-links" aria-label="Case decision workspaces">
            <Link href={`/eligibility?lead_id=${lead.id}`}><span>Assess</span><strong>Eligibility record</strong><small>Review the persisted assessment or deliberately run a new evaluation there.</small></Link>
            <Link href={`/planning?lead_id=${lead.id}`}><span>Compare</span><strong>Pathway planning</strong><small>Inspect version-pinned pathway comparison and uncertainty.</small></Link>
            <Link href="/document-intelligence"><span>Evidence</span><strong>Document intelligence</strong><small>Review requirement coverage, validation, extraction, and evidence risk.</small></Link>
            <Link href="/timelines"><span>Execute</span><strong>Mobility timelines</strong><small>Manage deliberate timeline generation, activation, and milestones.</small></Link>
            <Link href="/authority-submission-checklist"><span>Authority</span><strong>Submission controls</strong><small>Work through authority-specific readiness without implying an outcome.</small></Link>
          </nav>
        </section>

        <section className="panel decision-section operator-case-evidence" aria-labelledby="case-evidence-heading">
          <div className="operator-section-heading">
            <div><span className="page-kicker">Supporting evidence & review state</span><h2 id="case-evidence-heading">What supports the current professional view</h2></div>
            {professionalLoading ? <span className="operator-count-chip">Refreshing reads…</span> : null}
          </div>
          <EvidenceProvenance
            title="Current decision evidence chain"
            detail="A consistent presentation of source, rule, pathway, aligned case evidence, historical exclusions, and unresolved gaps. These labels describe existing persisted records; they do not create new evidence authority."
            items={caseEvidenceProvenance}
            boundary="Evidence presentation never upgrades retrieval, a source reference, an assessment, or a pathway comparison into legal truth, certification, publication, or an authority outcome."
          />
          <div className="operator-evidence-grid">
            <article>
              <span>Latest eligibility assessment</span>
              <strong>{professionalContext.eligibility ? titleCase(professionalContext.eligibility.status) : unavailableLabel}</strong>
              <p>{professionalContext.eligibility?.summary || (professionalLoading ? "Reading persisted eligibility assessment." : "No persisted eligibility assessment is available.")}</p>
              <small>{professionalContext.eligibility ? `Created ${formatDate(professionalContext.eligibility.created_at)} · useful case context, but profile/pathway alignment to the current comparison cannot be proven from this contract` : professionalLoading ? "Read in progress" : "No decision inferred"}</small>
            </article>
            <article>
              <span>Pathway comparison</span>
              <strong>{primaryComparison?.pathway.name || unavailableLabel}</strong>
              <p>{primaryComparison ? `${titleCase(primaryComparison.recommendation_status)} · ${titleCase(primaryComparison.processing_evidence_status)} processing evidence` : professionalLoading ? "Reading persisted pathway comparison." : "No persisted pathway comparison is available."}</p>
              <small>{professionalContext.comparison ? `${professionalContext.comparison.missing_evidence.length} assessment-level evidence gap(s)` : professionalLoading ? "Read in progress" : "No route inferred"}</small>
            </article>
            <article>
              <span>Context-aligned document requirements</span>
              <strong>{alignedRequirementAssessment ? titleCase(alignedRequirementAssessment.review_status) : unavailableLabel}</strong>
              <p>{alignedRequirementAssessment?.summary || (professionalLoading ? "Reading persisted document-requirement assessment." : "No context-aligned document-requirement assessment is available for the current decision.")}</p>
              <small>{alignedRequirementAssessment ? `${alignedRequirementAssessment.missing_count} missing · ${alignedRequirementAssessment.inconsistency_count} inconsistency` : professionalLoading ? "Read in progress" : `${excludedRequirementAssessments.length} historical/context-mismatch assessment(s) excluded`}</small>
            </article>
            <article>
              <span>Context-aligned timeline state</span>
              <strong>{alignedTimeline ? titleCase(alignedTimeline.status) : unavailableLabel}</strong>
              <p>{alignedTimeline ? `${titleCase(alignedTimeline.current_stage_key || "stage not set")} · ${alignedTimeline.milestones.length} milestone(s)` : professionalLoading ? "Reading persisted mobility timeline." : "No context-aligned mobility timeline is available for the current decision."}</p>
              <small>{alignedTimeline?.activated_by ? `Activated by ${alignedTimeline.activated_by}` : professionalLoading ? "Read in progress" : `${excludedTimelines.length} historical/context-mismatch timeline(s) excluded`}</small>
            </article>
            <article>
              <span>Case authority operations</span>
              <strong>{detail.applications.length} application{detail.applications.length === 1 ? "" : "s"}</strong>
              <p>{professionalContext.appointments.length} appointment(s) · {professionalContext.submissions.length} submission record(s) · {professionalContext.agencyAssignments.length} agency assignment(s)</p>
              <small>{pendingChecklist} pending authority checklist item(s). These are case operations, not evidence for the current pathway unless an explicit aligned relationship is persisted.</small>
            </article>
            <article>
              <span>Certification / source state</span>
              <strong>{primaryComparison ? titleCase(primaryComparison.processing_evidence_status) : unavailableLabel}</strong>
              <p>{uniqueCertificationStates.length ? uniqueCertificationStates.map(titleCase).join(" · ") : "No pathway certification states are present in the loaded comparison."}</p>
              <small>{primaryComparison ? `${primaryComparison.verified_rule_ids.length} verified rule reference(s)` : `${detail.source_references.length} truth-source reference(s)`}</small>
            </article>
          </div>

          <TechnicalDisclosure detail="Identifiers, version pins, timestamps, and read diagnostics">
            <dl className="technical-metadata-list">
              <div><dt>Lead ID</dt><dd><code>{lead.id}</code></dd></div>
              <div><dt>Eligibility assessment</dt><dd><code>{professionalContext.eligibility?.id || "not-established"}</code></dd></div>
              <div><dt>Comparison assessment</dt><dd><code>{professionalContext.comparison?.assessment_id || "not-established"}</code></dd></div>
              <div><dt>Comparison profile pin</dt><dd><code>{professionalContext.comparison?.profile_id || "not-established"} @ v{professionalContext.comparison?.profile_version ?? "—"}</code></dd></div>
              <div><dt>Primary pathway</dt><dd><code>{primaryComparison?.pathway.id || "not-established"}</code></dd></div>
              <div><dt>Comparison pathway version</dt><dd><code>{primaryComparison?.pathway.current_version?.id || "not-established"}</code></dd></div>
              <div><dt>Aligned timeline pathway version</dt><dd><code>{alignedTimeline?.primary_pathway_version_id || "not-established"}</code></dd></div>
              <div><dt>Aligned timeline</dt><dd><code>{alignedTimeline?.id || "not-established"}</code></dd></div>
              <div><dt>Excluded timeline records</dt><dd><code>{excludedTimelines.map((timeline) => timeline.id).join(", ") || "none"}</code></dd></div>
              <div><dt>Aligned document assessment</dt><dd><code>{alignedRequirementAssessment?.id || "not-established"}</code></dd></div>
              <div><dt>Excluded document assessments</dt><dd><code>{excludedRequirementAssessments.map((assessment) => assessment.id).join(", ") || "none"}</code></dd></div>
              <div><dt>Loaded source references</dt><dd>{detail.source_references.length}</dd></div>
              <div><dt>Read diagnostics</dt><dd>{professionalContext.readWarnings.length ? professionalContext.readWarnings.join(" · ") : "All available professional read contracts returned without an unexpected error."}</dd></div>
            </dl>
          </TechnicalDisclosure>
        </section>
      </section>

      <ClientPortalInvite leadId={lead.id} />

      <section className="panel operator-case-controlled-actions">
        <SectionTitle label="Controlled execution" title="Operator tools" detail="Actions remain in their governed specialist workspaces." />
        <div className="action-grid">
          {actions.map((action) => (
            <ActionCard key={action.title} action={action} />
          ))}
        </div>
      </section>

      {error ? <InlineNotice label="Error" tone="bad" detail={error} /> : null}

      <nav className="tab-bar" aria-label="Case record details">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "overview" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Overview" title="Case record" detail="Core CRM and intake facts retained beneath the professional decision view." />
            <div className="detail-list">
              <DetailRow label="Full name">{lead.full_name || "—"}</DetailRow>
              <DetailRow label="Email">{lead.email || "—"}</DetailRow>
              <DetailRow label="Phone">{lead.phone || "—"}</DetailRow>
              <DetailRow label="Intent">{titleCase(lead.intent)}</DetailRow>
              <DetailRow label="Target country">{lead.target_country || "—"}</DetailRow>
              <DetailRow label="Source">{titleCase(lead.source)}</DetailRow>
              <DetailRow label="Created">{formatDate(lead.created_at)}</DetailRow>
              <DetailRow label="Notes">
                <p className="detail-notes">{lead.notes || "No notes recorded."}</p>
              </DetailRow>
            </div>
          </article>

          <ProfilesPanel profiles={detail?.profiles || []} />

          <article className="panel">
            <SectionTitle label="Documents" title="Verification status" detail={`${detail?.documents.length || 0} document records`} />
            <DocumentList documents={detail?.documents || []} />
          </article>

          <article className="panel">
            <SectionTitle label="Applications" title="Authority pipeline" detail={`${detail?.applications.length || 0} applications`} />
            <ApplicationList applications={detail?.applications || []} />
          </article>
        </div>
      )}

      {activeTab === "truth" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Truth Engine" title="Claim verification" detail={`${detail?.truth_claims.length || 0} claims`} />
            {detail?.truth_claims.length ? (
              <div className="claim-stack">
                {detail.truth_claims.map((claim) => (
                  <TruthClaimCard claim={claim} key={claim.id} />
                ))}
              </div>
            ) : (
              <EmptyState title="No truth claims" detail="Truth Engine results for this lead will appear here." />
            )}
          </article>
          <SourceReferencesPanel references={detail?.source_references || []} />
        </div>
      )}

      {activeTab === "agents" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Agents" title="Controlled outputs" detail={`${detail?.agent_runs.length || 0} runs`} />
            {detail?.agent_runs.length ? (
              <div className="compact-list">
                {detail.agent_runs.map((run) => (
                  <AgentRunRow run={run} key={run.id} />
                ))}
              </div>
            ) : (
              <EmptyState title="No agent runs" detail="Controlled agents have not produced outputs for this lead yet." />
            )}
          </article>
        </div>
      )}

      {activeTab === "applications" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Applications" title="Authority pipeline" detail={`${detail?.applications.length || 0} records`} />
            <ApplicationList applications={detail?.applications || []} />
          </article>
        </div>
      )}

      {activeTab === "communications" && (
        <div className="lead-grid fade-in">
          <CommunicationsPanel followUps={detail?.follow_ups || []} leadId={id} />
        </div>
      )}

      {activeTab === "activity" && (
        <div className="lead-grid fade-in">
          <ActivityPanel workflowRuns={detail?.workflow_runs || []} followUps={detail?.follow_ups || []} />
          <ReviewsPanel reviews={detail?.reviews || []} />
        </div>
      )}
    </WorkspaceShell>
  );
}

function ProfilesPanel({ profiles }: { profiles: Profile[] }) {
  if (!profiles.length) return null;
  const profile = profiles[0];
  return (
    <article className="panel">
      <SectionTitle label="Profile" title="Intake profile" detail={`${profiles.length} profile record(s)`} />
      <div className="detail-list">
        <DetailRow label="Qualification">{profile.highest_qualification || "—"}</DetailRow>
        <DetailRow label="Field of study">{profile.field_of_study || "—"}</DetailRow>
        <DetailRow label="Current country">{profile.current_country || "—"}</DetailRow>
        <DetailRow label="Target country">{profile.target_country || "—"}</DetailRow>
        <DetailRow label="Desired role">{profile.desired_role || "—"}</DetailRow>
        <DetailRow label="Budget (EUR)">{profile.budget_eur ?? "—"}</DetailRow>
      </div>
    </article>
  );
}

function DocumentList({ documents }: { documents: DocumentRecord[] }) {
  if (!documents.length) {
    return <EmptyState title="No documents" detail="Documents uploaded for this lead will appear here." />;
  }
  return (
    <div className="compact-list">
      {documents.map((doc) => (
        <div className="compact-row" key={doc.id}>
          <div>
            <strong>{titleCase(doc.document_type)}</strong>
            <span>{doc.filename}</span>
          </div>
          <StatusBadge value={doc.status} />
        </div>
      ))}
    </div>
  );
}

function ApplicationList({ applications }: { applications: ApplicationRecord[] }) {
  if (!applications.length) {
    return <EmptyState title="No applications" detail="Application drafts and authority decisions will appear here." />;
  }
  return (
    <div className="compact-list">
      {applications.map((app) => (
        <div className="compact-row" key={app.id}>
          <div>
            <strong>{titleCase(app.domain)}</strong>
            <span>{app.target_institution_or_employer || app.target_country || "Application"}</span>
          </div>
          <StatusBadge value={app.status} />
        </div>
      ))}
    </div>
  );
}

function SourceReferencesPanel({ references }: { references: SourceReference[] }) {
  return (
    <article className="panel">
      <SectionTitle label="Sources" title="Official source references" detail={`${references.length} records`} />
      {references.length ? (
        <div className="compact-list">
          {references.map((ref) => (
            <div className="compact-row" key={ref.id}>
              <div>
                <strong>{ref.title || "Source"}</strong>
                <a href={ref.source_url} target="_blank" rel="noreferrer" className="source-link">
                  {ref.source_url}
                </a>
              </div>
              <StatusBadge value={ref.source_type || "official"} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No source references" detail="Official sources attached to truth claims will appear here." />
      )}
    </article>
  );
}

function AgentRunRow({ run }: { run: import("../../../lib/api").AgentRun }) {
  return (
    <div className="compact-row">
      <div>
        <strong>{titleCase(run.agent_name)}</strong>
        <span>{run.task || run.status}</span>
      </div>
      <StatusBadge value={run.status} />
    </div>
  );
}

function CommunicationsPanel({ followUps, leadId }: { followUps: FollowUp[]; leadId?: string }) {
  return (
    <article className="panel">
      <SectionTitle
        label="Communications"
        title="Client communication drafts"
        detail={`${followUps.length} follow-up / draft records`}
      />
      {leadId && (
        <div className="panel-actions">
          <Link className="button" href={`/communications/leads/${leadId}`}>
            Open communication workspace
          </Link>
        </div>
      )}
      {followUps.length ? (
        <div className="compact-list">
          {followUps.map((fu) => (
            <div className="compact-row" key={fu.id}>
              <div>
                <strong>{titleCase(fu.channel)}</strong>
                <span>{fu.message ? fu.message.slice(0, 80) + "..." : "No preview"}</span>
              </div>
              <StatusBadge value={fu.status} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No communications" detail="Client communication drafts and follow-ups will appear here." />
      )}
    </article>
  );
}

function ActivityPanel({ workflowRuns, followUps }: { workflowRuns: WorkflowRun[]; followUps: FollowUp[] }) {
  const items = [
    ...workflowRuns.map((run) => ({ type: "workflow" as const, data: run })),
    ...followUps.map((fu) => ({ type: "followup" as const, data: fu })),
  ].sort((a, b) => {
    const aDate = new Date((a.data as any).created_at || (a.data as any).started_at || 0).getTime();
    const bDate = new Date((b.data as any).created_at || (b.data as any).started_at || 0).getTime();
    return bDate - aDate;
  });

  return (
    <article className="panel">
      <SectionTitle label="Activity" title="Workflow timeline" detail="Recent follow-ups and workflow runs" />
      {items.length ? (
        <div className="timeline">
          {items.slice(0, 8).map((item, idx) =>
            item.type === "workflow" ? (
              <div className="timeline-item" key={`wf-${(item.data as WorkflowRun).id}-${idx}`}>
                <div className="timeline-dot" />
                <div>
                  <strong>{titleCase((item.data as WorkflowRun).workflow_name)}</strong>
                  <span>{formatDate((item.data as WorkflowRun).created_at)}</span>
                </div>
                <StatusBadge value={(item.data as WorkflowRun).status} />
              </div>
            ) : (
              <div className="timeline-item" key={`fu-${(item.data as FollowUp).id}-${idx}`}>
                <div className="timeline-dot" />
                <div>
                  <strong>{titleCase((item.data as FollowUp).channel)} follow-up</strong>
                  <span>{formatDate((item.data as FollowUp).created_at)}</span>
                </div>
                <StatusBadge value={(item.data as FollowUp).status} />
              </div>
            )
          )}
        </div>
      ) : (
        <EmptyState title="No recent activity" detail="Workflow runs and follow-ups will be listed here." />
      )}
    </article>
  );
}

function ReviewsPanel({ reviews }: { reviews: HumanReview[] }) {
  return (
    <article className="panel">
      <SectionTitle label="Reviews" title="Human review history" detail={`${reviews.length} reviews`} />
      {reviews.length ? (
        <div className="compact-list">
          {reviews.map((review) => (
            <div className="compact-row" key={review.id}>
              <div>
                <strong>{titleCase(review.review_type)}</strong>
                <span>{review.reason || review.reviewer_notes || "No reason recorded"}</span>
              </div>
              <StatusBadge value={review.status} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No reviews" detail="Human review decisions for this lead will appear here." />
      )}
    </article>
  );
}
