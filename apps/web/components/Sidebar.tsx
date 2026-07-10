"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HealthStatus } from "../lib/api";
import { getApiBaseUrl } from "../lib/api";

const navItems = [
  { label: "Workbench", href: "/#workbench" },
  { label: "Pipeline", href: "/#pipeline" },
  { label: "Lead intake", href: "/#intake" },
  { label: "Verification", href: "/#verification" },
  { label: "Governance", href: "/#governance" },
];

export function Sidebar({ health }: { health: HealthStatus | null }) {
  const pathname = usePathname();
  const backendOnline = health?.status === "ok";
  const apiBase = getApiBaseUrl();

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
          const isActive = pathname === "/" && item.href.startsWith("/#");
          return (
            <Link className={isActive ? "active" : ""} href={item.href} key={item.href}>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-status">
        <div className={`pulse ${backendOnline ? "online" : "offline"}`} />
        <div>
          <strong>{backendOnline ? "Backend connected" : "Backend offline"}</strong>
          <small>{backendOnline ? health?.environment || "local" : apiBase}</small>
        </div>
      </div>
    </aside>
  );
}
