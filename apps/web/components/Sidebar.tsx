"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { HealthStatus, getApiBaseUrl } from "../lib/api";
import {
  explicitExperienceForPath,
  isWorkspaceExperience,
  WORKSPACE_EXPERIENCE_STORAGE_KEY,
  WorkspaceExperience,
  WorkspaceNavIcon,
  workspaceExperiences,
  workspaceNavigation,
} from "../lib/workspace-navigation";
import { useTheme } from "../hooks/useTheme";

export function Sidebar({ health }: { health: HealthStatus | null }) {
  const pathname = usePathname();
  const explicitExperience = explicitExperienceForPath(pathname);
  const [experience, setExperience] = useState<WorkspaceExperience>(explicitExperience || "operator");
  const backendOnline = health?.status === "ok";
  const apiBase = getApiBaseUrl();
  const { theme, toggleTheme } = useTheme();
  const [railTooltip, setRailTooltip] = useState<{ label: string; detail?: string; left: number; top: number } | null>(null);

  function showRailTooltip(node: HTMLElement, label: string, detail?: string) {
    const rect = node.getBoundingClientRect();
    setRailTooltip({
      label,
      detail,
      left: Math.round(rect.right + 12),
      top: Math.round(rect.top + rect.height / 2),
    });
  }

  function hideRailTooltip() {
    setRailTooltip(null);
  }

  useEffect(() => {
    if (explicitExperience) {
      setExperience(explicitExperience);
      window.localStorage.setItem(WORKSPACE_EXPERIENCE_STORAGE_KEY, explicitExperience);
      return;
    }
    const stored = window.localStorage.getItem(WORKSPACE_EXPERIENCE_STORAGE_KEY);
    if (isWorkspaceExperience(stored)) setExperience(stored);
  }, [explicitExperience]);

  const currentExperience = useMemo(
    () => workspaceExperiences.find((item) => item.id === experience) || workspaceExperiences[1],
    [experience]
  );
  const navGroups = workspaceNavigation[experience];

  function selectExperience(next: WorkspaceExperience) {
    setExperience(next);
    window.localStorage.setItem(WORKSPACE_EXPERIENCE_STORAGE_KEY, next);
  }

  return (
    <>
    <aside
      id="workspace-navigation"
      className={`sidebar workspace-rail ${experience}-rail`}
      aria-label={`${currentExperience.label} navigation`}
    >
      <Link
        className="rail-brand"
        href={currentExperience.href}
        aria-label={`Global Mobility AIOS ${currentExperience.shortLabel} home`}
        data-label="Global Mobility AIOS"
        onMouseEnter={(event) => showRailTooltip(event.currentTarget, "Global Mobility AIOS", `${currentExperience.shortLabel} experience`)}
        onMouseLeave={hideRailTooltip}
        onFocus={(event) => showRailTooltip(event.currentTarget, "Global Mobility AIOS", `${currentExperience.shortLabel} experience`)}
        onBlur={hideRailTooltip}
      >
        <span className="rail-brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M25 10.2A10.2 10.2 0 1 0 25.3 21H17v-5h8.5" stroke="currentColor" strokeWidth="2.15" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="23.7" cy="16" r="2.15" fill="currentColor" />
            <path d="M8.2 16h4.2M10.3 13.9v4.2" stroke="currentColor" strokeWidth="1.55" strokeLinecap="round" />
          </svg>
        </span>
        <span className="rail-brand-copy">
          <strong>GMAI</strong>
          <small>Global Mobility AIOS</small>
        </span>
      </Link>

      <div className="rail-experience" aria-label="Workspace experience">
        <span className="rail-experience-label">Experience</span>
        <div className="rail-experience-links">
          {workspaceExperiences.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={experience === item.id ? "active" : ""}
              aria-current={experience === item.id ? "true" : undefined}
              aria-label={`${item.shortLabel}: ${item.label}`}
              data-label={`${item.shortLabel} · ${item.label}`}
              title={`${item.label}: ${item.description}`}
              onClick={() => selectExperience(item.id)}
              onMouseEnter={(event) => showRailTooltip(event.currentTarget, item.shortLabel, item.label)}
              onMouseLeave={hideRailTooltip}
              onFocus={(event) => showRailTooltip(event.currentTarget, item.shortLabel, item.label)}
              onBlur={hideRailTooltip}
            >
              <span className="rail-experience-icon" aria-hidden="true"><ExperienceIcon experience={item.id} /></span>
              <span className="rail-experience-copy">
                <strong>{item.shortLabel}</strong>
                <small>{item.label}</small>
              </span>
            </Link>
          ))}
        </div>
      </div>

      <div className="rail-navigation" onScroll={hideRailTooltip}>
        {navGroups.map((group, groupIndex) => (
          <nav className="rail-group" aria-label={group.label} key={group.label}>
            {groupIndex > 0 ? <span className="rail-separator" aria-hidden="true" /> : null}
            <span className="rail-group-label">{group.label}</span>
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
                  onMouseEnter={(event) => showRailTooltip(event.currentTarget, item.label, group.label)}
                  onMouseLeave={hideRailTooltip}
                  onFocus={(event) => showRailTooltip(event.currentTarget, item.label, group.label)}
                  onBlur={hideRailTooltip}
                >
                  <span className="rail-icon" aria-hidden="true"><NavIcon name={item.icon} /></span>
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
          onMouseEnter={(event) => showRailTooltip(event.currentTarget, `${theme === "light" ? "Dark" : "Light"} mode`, "Appearance")}
          onMouseLeave={hideRailTooltip}
          onFocus={(event) => showRailTooltip(event.currentTarget, `${theme === "light" ? "Dark" : "Light"} mode`, "Appearance")}
          onBlur={hideRailTooltip}
        >
          <span className="rail-icon utility" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M20 15.2A8.5 8.5 0 1 1 8.8 4a6.8 6.8 0 0 0 11.2 11.2Z" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="rail-text">{theme === "light" ? "Dark mode" : "Light mode"}</span>
        </button>
        <div
          className={`rail-health ${backendOnline ? "online" : "offline"}`}
          aria-label={backendOnline ? `Backend connected: ${health?.environment || "local"}` : `Backend offline: ${apiBase}`}
          data-label={backendOnline ? "Backend connected" : "Backend offline"}
          title={backendOnline ? "Backend connected" : "Backend offline"}
          onMouseEnter={(event) => showRailTooltip(event.currentTarget, backendOnline ? "Backend online" : "Backend offline", backendOnline ? (health?.environment || "Connected") : apiBase)}
          onMouseLeave={hideRailTooltip}
        >
          <span className="rail-health-dot" />
          <span className="rail-text">{backendOnline ? "Backend online" : "Backend offline"}</span>
        </div>
      </div>
    </aside>
    {railTooltip ? (
      <div
        className="rail-hover-label"
        role="tooltip"
        style={{ left: railTooltip.left, top: railTooltip.top }}
      >
        <strong>{railTooltip.label}</strong>
        {railTooltip.detail ? <span>{railTooltip.detail}</span> : null}
      </div>
    ) : null}
    </>
  );
}

function ExperienceIcon({ experience }: { experience: WorkspaceExperience }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  if (experience === "owner") {
    return <svg {...common}><circle cx="12" cy="12" r="7.5" /><path d="M12 4.5v3M12 16.5v3M4.5 12h3M16.5 12h3M8.4 8.4l2.1 2.1M15.6 8.4l-2.1 2.1" /><circle cx="12" cy="12" r="2.1" fill="currentColor" stroke="none" /></svg>;
  }
  if (experience === "operator") {
    return <svg {...common}><rect x="4" y="4" width="6.5" height="6.5" rx="1.5" /><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5" /><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5" /><path d="M13.5 16.75h6.5M16.75 13.5V20" /></svg>;
  }
  return <svg {...common}><circle cx="12" cy="12" r="8" /><path d="m15.8 8.2-2 5.6-5.6 2 2-5.6 5.6-2Z" /><circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" /></svg>;
}

function NavIcon({ name }: { name: WorkspaceNavIcon }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.95,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "home": return <svg {...common}><path d="m4 10 8-6 8 6v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-9Z" /></svg>;
    case "cockpit": return <svg {...common}><circle cx="12" cy="12" r="8" /><path d="M12 12 17 8M7.5 16.5h9M12 4v2M5.6 7.2l1.4 1M18.4 7.2l-1.4 1" /></svg>;
    case "profiles": return <svg {...common}><circle cx="9" cy="8" r="3" /><path d="M3.5 19c.6-3.2 2.4-5 5.5-5s4.9 1.8 5.5 5M16 7h5M18.5 4.5v5" /></svg>;
    case "pathways": return <svg {...common}><circle cx="6" cy="6" r="2" /><circle cx="18" cy="18" r="2" /><path d="M8 6h3a3 3 0 0 1 3 3v6a3 3 0 0 0 3 3M11 12H7a3 3 0 0 0-3 3v3" /></svg>;
    case "planning": return <svg {...common}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h6" /></svg>;
    case "timelines": return <svg {...common}><path d="M5 5v14M5 8h7M5 16h11" /><circle cx="15" cy="8" r="2" /><circle cx="19" cy="16" r="2" /></svg>;
    case "documents": return <svg {...common}><path d="M7 3h7l4 4v14H7zM14 3v5h4M10 13h5M10 17h5" /></svg>;
    case "intelligence": return <svg {...common}><path d="M4 18V9M9 18V5M14 18v-7M19 18V3M3 21h18" /></svg>;
    case "global": return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>;
    case "agents": return <svg {...common}><rect x="4" y="7" width="16" height="12" rx="3" /><path d="M9 12h.01M15 12h.01M9 16h6M12 7V3M9 3h6" /></svg>;
    case "review": return <svg {...common}><path d="M9 4H5v16h14V4h-4M9 3h6v4H9zM8 12l2 2 5-5M8 18h8" /></svg>;
    case "communications": return <svg {...common}><path d="M4 5h16v11H8l-4 4V5Z" /><path d="M8 9h8M8 13h5" /></svg>;
    case "automation": return <svg {...common}><path d="M6 6h5M13 6h5M6 18h5M13 18h5M6 6v12M18 6v12M9 12h6" /><circle cx="12" cy="6" r="2" /><circle cx="12" cy="18" r="2" /><circle cx="18" cy="12" r="2" /></svg>;
    case "coaching": return <svg {...common}><path d="M12 3 3 8l9 5 9-5-9-5ZM6 10v5c3 3 9 3 12 0v-5M21 8v7" /></svg>;
    case "corporate": return <svg {...common}><path d="M4 21V7h10v14M14 11h6v10M8 11h2M8 15h2M8 19h2M17 15h1M17 18h1M2 21h20M7 7V4h4v3" /></svg>;
    case "advisory": return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="m15.8 8.2-2.1 5.5-5.5 2.1 2.1-5.5 5.5-2.1ZM12 3v2M21 12h-2M12 21v-2M3 12h2" /></svg>;
    case "investment": return <svg {...common}><path d="M4 8.5 12 4l8 4.5-8 4.5-8-4.5ZM6 11v6M10 13v6M14 13v6M18 11v6M4 20h16" /></svg>;
    case "family": return <svg {...common}><circle cx="9" cy="7" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3.5 20c.5-4 2.3-6 5.5-6s5 2 5.5 6M14 15c3.4-.5 5.5 1.2 6.5 5M4 3h16M4 3v18M20 3v18" /></svg>;
    case "tax": return <svg {...common}><path d="M6 3h9l3 3v15H6zM15 3v4h4M9 11h6M9 15h6M9 19h4" /><path d="m9 7 1.2 1.2L13 5.5" /></svg>;
    case "appointments": return <svg {...common}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h6" /><circle cx="17" cy="17" r="2" /></svg>;
    case "board": return <svg {...common}><path d="M4 20h16M6 20v-8h12v8M8 12V8h8v4M10 8V4h4v4" /><path d="M9 16h6" /></svg>;
    case "portal": return <svg {...common}><path d="M5 4h14v16H5zM9 8h6M9 12h6M9 16h3" /><path d="M3 8h2M19 8h2" /></svg>;
  }
}
