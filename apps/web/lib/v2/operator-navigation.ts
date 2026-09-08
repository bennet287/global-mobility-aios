export type OperatorNavLabel =
  | "Work"
  | "Profiles"
  | "Pathways"
  | "Evidence"
  | "Communication"
  | "Tools";

export type OperatorNavigationIcon =
  | "work"
  | "profiles"
  | "pathways"
  | "evidence"
  | "communication"
  | "tools";

export type OperatorNavigationItem = {
  readonly label: OperatorNavLabel;
  readonly icon: OperatorNavigationIcon;
  readonly href: string | null;
  readonly enabled: boolean;
  readonly description: string;
};

export type OperatorContextualDestination = {
  readonly label: string;
  readonly href: string;
  readonly conceptualHome: OperatorNavLabel;
  readonly description: string;
};

export const operatorNavigation: readonly OperatorNavigationItem[] = Object.freeze([
  { label: "Work", icon: "work", href: "/", enabled: true, description: "Cases, review queues, blockers and next professional actions" },
  { label: "Profiles", icon: "profiles", href: "/operator/v2/profiles", enabled: true, description: "Mobility profiles and case context" },
  { label: "Pathways", icon: "pathways", href: "/operator/v2/pathways", enabled: true, description: "Governed pathway catalogue and professional comparison" },
  { label: "Evidence", icon: "evidence", href: "/document-intelligence", enabled: true, description: "Documents, evidence review, validation and provenance" },
  { label: "Communication", icon: "communication", href: "/communications", enabled: true, description: "Governed professional and client communication workflows" },
  { label: "Tools", icon: "tools", href: "/operator/v2/tools", enabled: true, description: "Contextual professional tools and specialist domains" },
]);

export const operatorContextualDestinations: readonly OperatorContextualDestination[] = Object.freeze([
  { label: "Eligibility", href: "/eligibility", conceptualHome: "Work", description: "Profile-backed eligibility and explicit uncertainty" },
  { label: "Planning", href: "/planning", conceptualHome: "Work", description: "Governed planning, comparison, cost and risk" },
  { label: "Timeline", href: "/timelines", conceptualHome: "Work", description: "Generated and activated case milestones" },
  { label: "Authority Appointments", href: "/authority-appointments", conceptualHome: "Work", description: "Authority appointment operations" },
  { label: "Agency Submissions", href: "/agency-submissions", conceptualHome: "Work", description: "Governed agency submission operations" },
  { label: "External Agency Assignments", href: "/external-agency-assignments", conceptualHome: "Work", description: "External agency assignment operations" },
  { label: "Authority Checklist", href: "/authority-submission-checklist", conceptualHome: "Work", description: "Authority readiness and filing controls" },
  { label: "Regulatory Intelligence", href: "/intelligence", conceptualHome: "Evidence", description: "Regulatory intelligence supporting professional review" },
  { label: "Global Intelligence", href: "/global-intelligence", conceptualHome: "Evidence", description: "Global intelligence supporting case context" },
  { label: "Independent Source Review", href: "/source-certification-review", conceptualHome: "Evidence", description: "Independent source certification review" },
  { label: "External Validation", href: "/validation", conceptualHome: "Evidence", description: "External validation and review" },
  { label: "Agent Console", href: "/agents/console", conceptualHome: "Tools", description: "Controlled internal agent operations" },
  { label: "Agent Review Queue", href: "/agents/review", conceptualHome: "Tools", description: "Human review of governed agent output" },
  { label: "Automation", href: "/automation", conceptualHome: "Tools", description: "Automation operations and controls" },
  { label: "Agent Coaching", href: "/coaching", conceptualHome: "Tools", description: "Agent coaching and professional controls" },
  { label: "Corporate Mobility", href: "/corporate-mobility", conceptualHome: "Tools", description: "Corporate mobility specialist workspace" },
  { label: "Business Advisory", href: "/business-advisory", conceptualHome: "Tools", description: "Business and wealth advisory workspace" },
  { label: "Investment Programs", href: "/investment-mobility", conceptualHome: "Tools", description: "Investment mobility programs" },
  { label: "Investor Suitability", href: "/investment-suitability", conceptualHome: "Tools", description: "Investor suitability review" },
  { label: "Family Office", href: "/family-office", conceptualHome: "Tools", description: "Family Office specialist workspace" },
  { label: "Tax & Treaty", href: "/tax-residency", conceptualHome: "Tools", description: "Tax residence and treaty workspace" },
]);
