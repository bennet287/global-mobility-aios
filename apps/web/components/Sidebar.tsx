"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HealthStatus } from "../lib/api";
import { getApiBaseUrl } from "../lib/api";
import { useTheme } from "../hooks/useTheme";

const navItems = [
  { label: "Workbench", href: "/#workbench" },
  { label: "Pipeline", href: "/#pipeline" },
  { label: "Lead intake", href: "/#intake" },
  { label: "Verification", href: "/#verification" },
  { label: "Governance", href: "/#governance" },
];

const appItems = [
  { label: "Agents", href: "/agents/console" },
  { label: "Review queue", href: "/agents/review" },
  { label: "Communications", href: "/communications" },
];

export function Sidebar({ health }: { health: HealthStatus | null }) {
  const pathname = usePathname();
  const backendOnline = health?.status === "ok";
  const apiBase = getApiBaseUrl();
  const { theme, toggleTheme } = useTheme();

  const isHomeActive = pathname === "/";

  return (
    <aside className="sidebar">
      <Link className="brand-lockup" href="/">
        <span>
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <rect width="32" height="32" rx="10" fill="currentColor" fillOpacity="0.12" />
            <path d="M10 22L16 10L22 22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="16" cy="19" r="2" fill="currentColor" />
          </svg>
        </span>
        <div>
          <strong>Global Mobility AIOS</strong>
          <small>Operator system</small>
        </div>
      </Link>

      <nav className="side-nav" aria-label="Workspace navigation">
        {navItems.map((item) => {
          const isActive = isHomeActive && item.href.startsWith("/#");
          return (
            <Link className={isActive ? "active" : ""} href={item.href} key={item.href}>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-section-title">Tools</div>
      <nav className="side-nav" aria-label="Application navigation">
        {appItems.map((item) => {
          const isActive = pathname?.startsWith(item.href) ?? false;
          return (
            <Link className={isActive ? "active" : ""} href={item.href} key={item.href}>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          <span>{theme === "light" ? "🌙" : "☀️"}</span>
          <small>{theme === "light" ? "Dark mode" : "Light mode"}</small>
        </button>

        <div className="sidebar-status">
          <div className={`pulse ${backendOnline ? "online" : "offline"}`} />
          <div>
            <strong>{backendOnline ? "Backend connected" : "Backend offline"}</strong>
            <small>{backendOnline ? health?.environment || "local" : apiBase}</small>
          </div>
        </div>
      </div>
    </aside>
  );
}
