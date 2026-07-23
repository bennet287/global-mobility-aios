"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HealthStatus, getApiBaseUrl } from "../lib/api";
import { useTheme } from "../hooks/useTheme";

type IconName =
  | "home"
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
  | "coaching"
  | "corporate"
  | "advisory"
  | "investment"
  | "family"
  | "tax";

const navGroups: { label: string; items: { label: string; href: string; icon: IconName }[] }[] = [
  {
    label: "Home",
    items: [{ label: "Operations Workspace", href: "/", icon: "home" }],
  },
  {
    label: "Mobility",
    items: [
      { label: "Mobility Profiles", href: "/profiles", icon: "profiles" },
      { label: "Pathway Catalogue", href: "/pathways", icon: "pathways" },
      { label: "Mobility Planning", href: "/planning", icon: "planning" },
      { label: "Mobility Timelines", href: "/timelines", icon: "timelines" },
    ],
  },
  {
    label: "Operations",
    items: [
      { label: "Document Intelligence", href: "/document-intelligence", icon: "documents" },
      { label: "Regulatory Intelligence", href: "/intelligence", icon: "intelligence" },
      { label: "Global Intelligence", href: "/global-intelligence", icon: "global" },
      { label: "Agent Console", href: "/agents/console", icon: "agents" },
      { label: "Agent Review Queue", href: "/agents/review", icon: "review" },
    ],
  },
  {
    label: "Business",
    items: [
      { label: "Corporate Mobility", href: "/corporate-mobility", icon: "corporate" },
      { label: "Business & Wealth Advisor", href: "/business-advisory", icon: "advisory" },
      { label: "Investment Programs", href: "/investment-mobility", icon: "investment" },
      { label: "Investor Suitability", href: "/investment-suitability", icon: "advisory" },
      { label: "Family Office", href: "/family-office", icon: "family" },
      { label: "Tax & Treaty", href: "/tax-residency", icon: "tax" },
    ],
  },
  {
    label: "Engagement",
    items: [
      { label: "Communications", href: "/communications", icon: "communications" },
      { label: "Agent Coaching", href: "/coaching", icon: "coaching" },
    ],
  },
];

export function Sidebar({ health }: { health: HealthStatus | null }) {
  const pathname = usePathname();
  const backendOnline = health?.status === "ok";
  const apiBase = getApiBaseUrl();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside className="sidebar workspace-rail">
      <Link className="rail-brand" href="/" aria-label="GMAI operations home" data-label="GMAI">
        <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <path d="M8 11.5h16M8 20.5h16M11.5 8v16M20.5 8v16" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
          <circle cx="20.5" cy="11.5" r="3.2" fill="currentColor" />
        </svg>
        <span className="rail-text rail-brand-text">GMAI</span>
      </Link>

      <div className="rail-navigation">
        {navGroups.map((group, groupIndex) => (
          <nav className="rail-group" aria-label={group.label} key={group.label}>
            {groupIndex > 0 ? <span className="rail-separator" aria-hidden="true" /> : null}
            {group.items.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href);
              return (
                <Link
                  className={`rail-link ${active ? "active" : ""}`}
                  href={item.href}
                  key={item.href}
                  aria-label={item.label}
                  aria-current={active ? "page" : undefined}
                  data-label={item.label}
                  title={item.label}
                >
                  <NavIcon name={item.icon} />
                  <span className="rail-text">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        ))}
      </div>

      <div className="rail-footer">
        <button
          className="rail-action"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          data-label={`${theme === "light" ? "Dark" : "Light"} mode`}
          title={`${theme === "light" ? "Dark" : "Light"} mode`}
        >
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M20 15.2A8.5 8.5 0 1 1 8.8 4a6.8 6.8 0 0 0 11.2 11.2Z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="rail-text">{theme === "light" ? "Dark mode" : "Light mode"}</span>
        </button>
        <div
          className={`rail-health ${backendOnline ? "online" : "offline"}`}
          aria-label={backendOnline ? `Backend connected: ${health?.environment || "local"}` : `Backend offline: ${apiBase}`}
          data-label={backendOnline ? "Backend connected" : "Backend offline"}
          title={backendOnline ? "Backend connected" : "Backend offline"}
        >
          <span className="rail-health-dot" />
          <span className="rail-text">{backendOnline ? "Backend online" : "Backend offline"}</span>
        </div>
      </div>
    </aside>
  );
}

function NavIcon({ name }: { name: IconName }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "home":
      return <svg {...common}><path d="m4 10 8-6 8 6v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-9Z" /></svg>;
    case "profiles":
      return <svg {...common}><circle cx="9" cy="8" r="3" /><path d="M3.5 19c.6-3.2 2.4-5 5.5-5s4.9 1.8 5.5 5M16 7h5M18.5 4.5v5" /></svg>;
    case "pathways":
      return <svg {...common}><circle cx="6" cy="6" r="2" /><circle cx="18" cy="18" r="2" /><path d="M8 6h3a3 3 0 0 1 3 3v6a3 3 0 0 0 3 3M11 12H7a3 3 0 0 0-3 3v3" /></svg>;
    case "planning":
      return <svg {...common}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h6" /></svg>;
    case "timelines":
      return <svg {...common}><path d="M5 5v14M5 8h7M5 16h11" /><circle cx="15" cy="8" r="2" /><circle cx="19" cy="16" r="2" /></svg>;
    case "documents":
      return <svg {...common}><path d="M7 3h7l4 4v14H7zM14 3v5h4M10 13h5M10 17h5" /></svg>;
    case "intelligence":
      return <svg {...common}><path d="M4 18V9M9 18V5M14 18v-7M19 18V3M3 21h18" /></svg>;
    case "global":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>;
    case "agents":
      return <svg {...common}><rect x="4" y="7" width="16" height="12" rx="3" /><path d="M9 12h.01M15 12h.01M9 16h6M12 7V3M9 3h6" /></svg>;
    case "review":
      return <svg {...common}><path d="M9 4H5v16h14V4h-4M9 3h6v4H9zM8 12l2 2 5-5M8 18h8" /></svg>;
    case "communications":
      return <svg {...common}><path d="M4 5h16v11H8l-4 4V5Z" /><path d="M8 9h8M8 13h5" /></svg>;
    case "coaching":
      return <svg {...common}><path d="M12 3 3 8l9 5 9-5-9-5ZM6 10v5c3 3 9 3 12 0v-5M21 8v7" /></svg>;
    case "corporate":
      return <svg {...common}><path d="M4 21V7h10v14M14 11h6v10M8 11h2M8 15h2M8 19h2M17 15h1M17 18h1M2 21h20M7 7V4h4v3" /></svg>;
    case "advisory":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="m15.8 8.2-2.1 5.5-5.5 2.1 2.1-5.5 5.5-2.1ZM12 3v2M21 12h-2M12 21v-2M3 12h2" /></svg>;
    case "investment":
      return <svg {...common}><path d="M4 8.5 12 4l8 4.5-8 4.5-8-4.5ZM6 11v6M10 13v6M14 13v6M18 11v6M4 20h16" /></svg>;
    case "family":
      return <svg {...common}><circle cx="9" cy="7" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3.5 20c.5-4 2.3-6 5.5-6s5 2 5.5 6M14 15c3.4-.5 5.5 1.2 6.5 5M4 3h16M4 3v18M20 3v18" /></svg>;
    case "tax":
      return <svg {...common}><path d="M6 3h9l3 3v15H6zM15 3v4h4M9 11h6M9 15h6M9 19h4" /><path d="m9 7 1.2 1.2L13 5.5" /></svg>;
  }
}
