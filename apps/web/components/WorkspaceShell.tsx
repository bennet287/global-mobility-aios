"use client";

import { ReactNode, useState } from "react";
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

  return (
    <main className={`app-frame ${mobileOpen ? "mobile-nav-open" : ""}`}>
      <MobileHeader onMenuClick={() => setMobileOpen((v) => !v)} />
      <Sidebar health={health} />
      <section className="workspace" onClick={() => mobileOpen && setMobileOpen(false)}>
        {children}
      </section>
    </main>
  );
}

function MobileHeader({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <header className="mobile-header">
      <button className="mobile-menu-button" onClick={onMenuClick} aria-label="Toggle navigation">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <span className="mobile-title">Global Mobility AIOS</span>
    </header>
  );
}
