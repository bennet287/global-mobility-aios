export type WorkspaceExperience = "owner" | "operator" | "mobility";

export type WorkspaceNavIcon =
  | "home"
  | "cockpit"
  | "profiles"
  | "pathways"
  | "planning"
  | "timelines"
  | "documents"
  | "intelligence"
  | "global"
  | "agents"
  | "review"
  | "communications"
  | "automation"
  | "coaching"
  | "corporate"
  | "advisory"
  | "investment"
  | "family"
  | "tax"
  | "appointments"
  | "board"
  | "portal";

export type WorkspaceNavGroup = {
  label: string;
  items: { label: string; href: string; icon: WorkspaceNavIcon }[];
};

export const WORKSPACE_EXPERIENCE_STORAGE_KEY = "gmai-workspace-experience";

export const workspaceExperiences: {
  id: WorkspaceExperience;
  label: string;
  shortLabel: string;
  href: string;
  description: string;
}[] = [
  {
    id: "owner",
    label: "Owner / Board",
    shortLabel: "Cockpit",
    href: "/cockpit",
    description: "Organization control, governance, decisions, evidence, and intelligence",
  },
  {
    id: "operator",
    label: "Professional / Operator",
    shortLabel: "Operations",
    href: "/",
    description: "Cases, pathways, evidence, workflow execution, and authority operations",
  },
  {
    id: "mobility",
    label: "Mobility User",
    shortLabel: "My Mobility",
    href: "/my-mobility",
    description: "Case progress, documents, timeline, next actions, and secure communication",
  },
];

export const workspaceNavigation: Record<WorkspaceExperience, WorkspaceNavGroup[]> = {
  owner: [
    {
      label: "Cockpit",
      items: [
        { label: "Cockpit Overview", href: "/cockpit", icon: "cockpit" },
        { label: "Live Organization", href: "/cockpit/live-organization", icon: "cockpit" },
        { label: "Owner Inbox", href: "/owner-inbox", icon: "review" },
        { label: "Board Room", href: "/board-room", icon: "board" },
        { label: "External Validation", href: "/validation", icon: "review" },
      ],
    },
    {
      label: "Intelligence & Evidence",
      items: [
        { label: "Global Intelligence", href: "/global-intelligence", icon: "global" },
        { label: "Regulatory Intelligence", href: "/intelligence", icon: "intelligence" },
        { label: "Independent Source Review", href: "/source-certification-review", icon: "review" },
        { label: "Document Intelligence", href: "/document-intelligence", icon: "documents" },
      ],
    },
    {
      label: "Department workspaces",
      items: [
        { label: "Cross-department friction", href: "/cross-department-friction", icon: "review" },
      ],
    },
    {
      label: "Organization",
      items: [
        { label: "Agent Review Queue", href: "/agents/review", icon: "review" },
        { label: "Agent Console", href: "/agents/console", icon: "agents" },
        { label: "Automation Hub", href: "/automation", icon: "automation" },
        { label: "Operations Workspace", href: "/", icon: "home" },
      ],
    },
  ],
  operator: [
    {
      label: "Operations",
      items: [
        { label: "Operations Workspace", href: "/", icon: "home" },
        { label: "Mobility Profiles", href: "/profiles", icon: "profiles" },
        { label: "Eligibility", href: "/eligibility", icon: "review" },
        { label: "Mobility Planning", href: "/planning", icon: "planning" },
        { label: "Pathway Catalogue", href: "/pathways", icon: "pathways" },
        { label: "Mobility Timelines", href: "/timelines", icon: "timelines" },
      ],
    },
    {
      label: "Evidence & Review",
      items: [
        { label: "Document Intelligence", href: "/document-intelligence", icon: "documents" },
        { label: "Regulatory Intelligence", href: "/intelligence", icon: "intelligence" },
        { label: "Global Intelligence", href: "/global-intelligence", icon: "global" },
        { label: "Independent Source Review", href: "/source-certification-review", icon: "review" },
        { label: "External Validation", href: "/validation", icon: "review" },
      ],
    },
    {
      label: "Execution",
      items: [
        { label: "Communications", href: "/communications", icon: "communications" },
        { label: "Agent Console", href: "/agents/console", icon: "agents" },
        { label: "Agent Review Queue", href: "/agents/review", icon: "review" },
        { label: "Automation Hub", href: "/automation", icon: "automation" },
        { label: "Agent Coaching", href: "/coaching", icon: "coaching" },
      ],
    },
    {
      label: "Business & Authority",
      items: [
        { label: "Corporate Mobility", href: "/corporate-mobility", icon: "corporate" },
        { label: "Business & Wealth Advisor", href: "/business-advisory", icon: "advisory" },
        { label: "Investment Programs", href: "/investment-mobility", icon: "investment" },
        { label: "Investor Suitability", href: "/investment-suitability", icon: "advisory" },
        { label: "Family Office", href: "/family-office", icon: "family" },
        { label: "Tax & Treaty", href: "/tax-residency", icon: "tax" },
        { label: "Authority Appointments", href: "/authority-appointments", icon: "appointments" },
        { label: "Agency Submissions", href: "/agency-submissions", icon: "documents" },
        { label: "External Agency Assignments", href: "/external-agency-assignments", icon: "corporate" },
        { label: "Authority Checklist", href: "/authority-submission-checklist", icon: "documents" },
      ],
    },
  ],
  mobility: [
    {
      label: "My Mobility",
      items: [
        { label: "My Mobility", href: "/my-mobility", icon: "portal" },
        { label: "Secure Case Workspace", href: "/portal", icon: "documents" },
      ],
    },
  ],
};

export function explicitExperienceForPath(pathname: string | null): WorkspaceExperience | null {
  if (!pathname) return null;
  if (pathname === "/" || pathname.startsWith("/leads/")) return "operator";
  if (pathname.startsWith("/cockpit") || pathname === "/owner-inbox" || pathname.startsWith("/board-room") || pathname.startsWith("/workspace/") || pathname === "/cross-department-friction") return "owner";
  if (pathname === "/my-mobility" || pathname.startsWith("/portal")) return "mobility";
  return null;
}

export function isWorkspaceExperience(value: string | null): value is WorkspaceExperience {
  return value === "owner" || value === "operator" || value === "mobility";
}
