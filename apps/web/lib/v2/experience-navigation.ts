import { ownerNavigation } from "./navigation";

export const operatorNavigation = [
  { label: "Work", icon: "home", href: "/", description: "Cases, review queues and next actions" },
  { label: "Profiles", icon: "organization", href: "/profiles", description: "Mobility profiles and case context" },
  { label: "Pathways", icon: "missions", href: "/pathways", description: "Pathways, eligibility and planning" },
  { label: "Evidence", icon: "evidence", href: "/document-intelligence", description: "Documents and governed evidence review" },
  { label: "Communication", icon: "intelligence", href: "/communications", description: "Case communication and draft review" },
  { label: "Tools", icon: "decisions", href: "/tools", description: "Specialist, authority and operational tools" },
] as const;
export const mobilityNavigation = [
  { label: "Overview", icon: "home", href: "/my-mobility", description: "Your mobility workspace" },
  { label: "My Case", icon: "missions", href: "/portal#my-case", description: "Open your securely scoped case" },
  { label: "Documents", icon: "evidence", href: "/portal#documents", description: "Documents shared with you" },
  { label: "Timeline", icon: "history", href: "/portal#timeline", description: "Recorded case milestones" },
  { label: "Messages", icon: "intelligence", href: "/portal#messages", description: "Case communication availability" },
] as const;
export const experienceNavigation = { owner: ownerNavigation, operator: operatorNavigation, mobility: mobilityNavigation };
export type V2Experience = keyof typeof experienceNavigation;
export function operatorItemForPath(path: string): string {
  if (path === "/" || path.startsWith("/leads/") || path === "/intake") return "Work";
  if (path.startsWith("/profiles")) return "Profiles";
  if (["/pathways", "/eligibility", "/planning", "/timelines", "/opportunities"].includes(path)) return "Pathways";
  if (["/document-intelligence", "/intelligence", "/global-intelligence", "/source-certification-review"].includes(path)) return "Evidence";
  if (path.startsWith("/communications")) return "Communication";
  return "Tools";
}
