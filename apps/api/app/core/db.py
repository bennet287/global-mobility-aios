from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings
from app.core.database_url import is_sqlite_url, normalize_database_url, should_auto_create_tables

DATABASE_URL = normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if is_sqlite_url(DATABASE_URL) else {}
engine = create_engine(
    DATABASE_URL,
    echo=settings.database_echo,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite_url(DATABASE_URL),
)

def register_models() -> None:
    from app.models.domain import (  # noqa: F401
        AgentRun,
        AuditLog,
        BoardPacket,
        AgencySubmission,
        AuthorityAppointment,
        AutomationConnectorConfig,
        AutomationDelivery,
        AutomationEvent,
        AutomationRule,
        BusinessMobilityAdvisoryAssessment,
        BusinessMobilityAdvisoryReview,
        ApplicationRecord,
        AuthorityChecklistTemplate,
        ApplicationAuthorityChecklistItem,
        CoachReview,
        DelegationRecord,
        ClientPortalAccessGrant,
        EcosystemPortalAccessGrant,
        PartnerApiCredential,
        CorporateAccount,
        CorporateCaseDependant,
        CorporateCaseSponsorAssignment,
        CorporateComplianceEvent,
        CorporateMobilityCase,
        CorporateRelocationTask,
        CorporateRelocationTaskDecision,
        CorporateSponsorEntity,
        CountryPolicy,
        CountryRankingAssessment,
        DocumentAccessGrant,
        DocumentExpiryReminderTask,
        DocumentFraudRiskAssessment,
        DocumentRequirementAssessment,
        DocumentRecord,
        EntrepreneurVentureProfile,
        ExternalValidationEvidence,
        ExternalValidationFinding,
        ExternalValidationReview,
        ExternalValidationRun,
        ExternalValidationScenario,
        EligibilityAssessment,
        ExecutiveDecision,
        ExternalAgency,
        ExternalAgencyAssignment,
        FamilyOfficeMobilityAssessment,
        FamilyOfficeMobilityReview,
        FollowUp,
        HumanReview,
        InitialRuleAssertion,
        IntakeSession,
        InvestmentMobilityProgram,
        InvestmentMobilityProgramVersion,
        InvestmentMobilityRuleDecision,
        InvestmentMobilityRuleProposal,
        InvestmentMobilitySuitabilityAssessment,
        InvestmentMobilitySuitabilityReview,
        Jurisdiction,
        JurisdictionCoverageEvidenceBatch,
        JurisdictionCoverageEvidenceBatchItem,
        JurisdictionImmigrationAssessment,
        JurisdictionRegistryEntry,
        JurisdictionRegistryRelease,
        JurisdictionSourceCertification,
        Lead,
        MobilityScenario,
        MobilityScenarioStage,
        OrganizationActivity,
        OrganizationActivityStream,
        OrganizationBlocker,
        OrganizationContribution,
        OrganizationControl,
        OrganizationExecutionAttempt,
        OrganizationHumanAction,
        OrganizationHumanActionRequest,
        OrganizationRecordReference,
        OrganizationWorkItemDependency,
        OrganizationalActionOutput,
        OrganizationalWorkItem,
        OrganizationPosition,
        OfficialSource,
        Opportunity,
        PathwayRegulatoryImpact,
        Profile,
        ReassessmentAcceptance,
        RegulatoryAuthority,
        RegulatoryClassificationProposal,
        RegulatoryChange,
        RegulatoryKnowledgeEdge,
        RegulatoryKnowledgeNode,
        RiskEscalation,
        SourceCheckRun,
        SourceMonitor,
        SourceRetrievalRun,
        SourceReference,
        SourceSnapshot,
        TaxResidencyAssessment,
        TaxResidencyAssessmentReview,
        TaxTreatyEvidence,
        TaxTreatyEvidenceDecision,
        TrainingCase,
        TruthClaim,
        VerificationAudit,
        VerifiedRule,
        VisaCheck,
        VentureEvidenceItem,
        VentureReviewDecision,
        WorkflowRun,
    )
    from app.models.autonomy_profile import (  # noqa: F401
        CapabilityAutonomyEvidence,
        CapabilityAutonomyProfile,
    )
    from app.models.autonomy_evidence_profile import (  # noqa: F401
        CapabilityAutonomyEvidenceObservation,
    )
    from app.models.autonomy_promotion_policy import (  # noqa: F401
        CapabilityAutonomyPromotionPolicy,
    )
    from app.models.eligibility_revision import EligibilityAssessmentRevision  # noqa: F401

def create_db_and_tables() -> None:
    register_models()
    if should_auto_create_tables(DATABASE_URL, settings.database_auto_create_tables):
        SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session