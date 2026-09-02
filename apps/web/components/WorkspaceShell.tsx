"use client";

import { ReactNode, useEffect, useRef, useState } from "react";
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
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const mobileNavWasOpenRef = useRef(false);

  useEffect(() => {
    if (!mobileOpen) {
      if (mobileNavWasOpenRef.current) menuButtonRef.current?.focus();
      mobileNavWasOpenRef.current = false;
      return;
    }

    mobileNavWasOpenRef.current = true;
    const navigation = document.getElementById("workspace-navigation");
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const focusableTargets = () => {
      const navigationTargets = navigation
        ? Array.from(
            navigation.querySelectorAll<HTMLElement>(
              'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
            ),
          )
        : [];
      return [menuButtonRef.current, ...navigationTargets].filter(
        (node): node is HTMLElement => Boolean(node),
      );
    };

    const focusFrame = window.requestAnimationFrame(() => {
      const targets = focusableTargets();
      (targets.find((node) => node !== menuButtonRef.current) || menuButtonRef.current)?.focus();
    });

    const containMobileNavigationFocus = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileOpen(false);
        return;
      }
      if (event.key !== "Tab") return;

      const targets = focusableTargets();
      if (!targets.length) return;
      const current = document.activeElement as HTMLElement | null;
      const currentIndex = current ? targets.indexOf(current) : -1;

      if (event.shiftKey && currentIndex <= 0) {
        event.preventDefault();
        targets[targets.length - 1]?.focus();
      } else if (!event.shiftKey && (currentIndex === -1 || currentIndex === targets.length - 1)) {
        event.preventDefault();
        targets[0]?.focus();
      }
    };

    document.addEventListener("keydown", containMobileNavigationFocus);
    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", containMobileNavigationFocus);
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileOpen]);

  return (
    <div className={`app-frame ${mobileOpen ? "mobile-nav-open" : ""}`}>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <MobileHeader buttonRef={menuButtonRef} open={mobileOpen} onMenuClick={() => setMobileOpen((v) => !v)} />
      <Sidebar health={health} />
      <main id="main-content" className="workspace" tabIndex={-1} onClick={() => mobileOpen && setMobileOpen(false)}>
        {children}
      </main>
    </div>
  );
}

function MobileHeader({
  buttonRef,
  open,
  onMenuClick,
}: {
  buttonRef: { current: HTMLButtonElement | null };
  open: boolean;
  onMenuClick: () => void;
}) {
  return (
    <header className="mobile-header">
      <button
        ref={buttonRef}
        className="mobile-menu-button"
        type="button"
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
