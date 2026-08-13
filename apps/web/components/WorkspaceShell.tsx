"use client";

import { ReactNode, useEffect, useState } from "react";
import { HealthStatus } from "../lib/api";
import { Sidebar } from "./Sidebar";

export function WorkspaceShell({
  children,
  health,
}: {
  children: ReactNode;
  health: HealthStatus | null;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!mobileOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileOpen]);

  return (
    <div className={`app-frame ${mobileOpen ? "mobile-nav-open" : ""}`}>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <MobileHeader open={mobileOpen} onMenuClick={() => setMobileOpen((v) => !v)} />
      <Sidebar health={health} />
      <main id="main-content" className="workspace" tabIndex={-1} onClick={() => mobileOpen && setMobileOpen(false)}>
        {children}
      </main>
    </div>
  );
}

function MobileHeader({ open, onMenuClick }: { open: boolean; onMenuClick: () => void }) {
  return (
    <header className="mobile-header">
      <button
        className="mobile-menu-button"
        onClick={onMenuClick}
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
        aria-controls="workspace-navigation"
      >
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <span className="mobile-title">GMAI <small>Mobility operating system</small></span>
    </header>
  );
}
