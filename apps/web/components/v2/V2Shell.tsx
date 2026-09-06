"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { ownerNavigation, type OwnerNavLabel } from "../../lib/v2/navigation";
import { V2CommandPalette } from "./V2CommandPalette";
import { V2GuidedExperience } from "./V2GuidedExperience";
import guideStyles from "./V2GuidedExperience.module.css";
import { V2Icon } from "./V2Icon";
import {
  V2_THEME_STORAGE_KEY,
  V2ThemeControl,
  isV2ThemePreference,
  type V2ThemePreference,
} from "./V2ThemeControl";

export function V2Shell({
  children,
  backendOnline,
  activeItem = "Home",
}: {
  children: ReactNode;
  backendOnline: boolean;
  activeItem?: OwnerNavLabel;
}) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [themePreference, setThemePreference] = useState<V2ThemePreference>("system");
  const commandTriggerRef = useRef<HTMLButtonElement>(null);
  const guideTriggerRef = useRef<HTMLButtonElement>(null);
  const closePalette = useCallback(() => {
    setPaletteOpen(false);
    requestAnimationFrame(() => commandTriggerRef.current?.focus());
  }, []);
  const closeGuide = useCallback(() => {
    setGuideOpen(false);
    requestAnimationFrame(() => guideTriggerRef.current?.focus());
  }, []);
  const changeTheme = useCallback((next: V2ThemePreference) => {
    setThemePreference(next);
    try {
      window.localStorage.setItem(V2_THEME_STORAGE_KEY, next);
    } catch {
      // Presentation preference persistence is best-effort only.
    }
  }, []);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(V2_THEME_STORAGE_KEY);
      if (isV2ThemePreference(stored)) setThemePreference(stored);
    } catch {
      // Storage can be unavailable in hardened/private browser contexts.
    }
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (guideOpen) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (paletteOpen) closePalette();
        else setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closePalette, guideOpen, paletteOpen]);

  return (
    <div className="aios-v2-root" data-theme={themePreference}>
      <a className="aios-v2-skip-link" href="#aios-v2-main">Skip to main content</a>

      <div className="aios-v2-shell">
        <aside className="aios-v2-rail" aria-label="AIOS V2 Owner navigation">
          <div className="aios-v2-brand">
            <div className="aios-v2-brand-mark" aria-hidden="true">AI</div>
            <div className="aios-v2-brand-copy">
              <strong>AIOS</strong>
              <span>Living Organization OS</span>
            </div>
          </div>

          <nav className="aios-v2-nav" aria-label="Owner">
            {ownerNavigation.map((item) => {
              const active = item.label === activeItem;
              if (item.enabled && item.href) {
                return (
                  <Link
                    className={"aios-v2-nav-item" + (active ? " active" : "")}
                    href={item.href}
                    key={item.label}
                    aria-current={active ? "page" : undefined}
                    aria-label={item.label}
                    title={item.description}
                  >
                    <span className="aios-v2-nav-glyph" aria-hidden="true">
                      <V2Icon name={item.icon} width={18} height={18} />
                    </span>
                    <span>{item.label}</span>
                  </Link>
                );
              }

              return (
                <span
                  className="aios-v2-nav-item"
                  aria-disabled="true"
                  aria-label={`${item.label} (not yet available)`}
                  key={item.label}
                  title={item.description}
                >
                  <span className="aios-v2-nav-glyph" aria-hidden="true">
                    <V2Icon name={item.icon} width={18} height={18} />
                  </span>
                  <span>{item.label}</span>
                </span>
              );
            })}
          </nav>

          <div className="aios-v2-rail-footer">
            <div className="aios-v2-health" data-state={backendOnline ? "online" : "unknown"}>
              <span className="aios-v2-health-dot" aria-hidden="true" />
              <span>{backendOnline ? "Backend online" : "Backend status unavailable"}</span>
            </div>
          </div>
        </aside>

        <main className="aios-v2-main" id="aios-v2-main">
          <div className="aios-v2-topline">
            <div className="aios-v2-topline-context">
              <strong>Owner</strong>
              <span>AIOS V2</span>
            </div>
            <div className={guideStyles.topActions}>
              <button
                aria-label="Open guided experience"
                className={`aios-v2-command ${guideStyles.guideTrigger}`}
                onClick={() => {
                  setPaletteOpen(false);
                  setGuideOpen(true);
                }}
                ref={guideTriggerRef}
                type="button"
              >
                <V2Icon name="organization" width={16} height={16} />
                <span>Guide</span>
              </button>
              <V2ThemeControl value={themePreference} onChange={changeTheme} />
              <button
                aria-keyshortcuts="Control+K Meta+K"
                ref={commandTriggerRef}
                aria-label="Navigate AIOS"
                className="aios-v2-command"
                onClick={() => setPaletteOpen(true)}
                type="button"
              >
                <V2Icon name="search" width={16} height={16} />
                <span>Search / Command</span>
                <kbd aria-hidden="true">Ctrl K</kbd>
              </button>
            </div>
          </div>

          {children}
        </main>
      </div>

      <V2CommandPalette open={paletteOpen} onClose={closePalette} />
      <V2GuidedExperience activeItem={activeItem} open={guideOpen} onClose={closeGuide} />
    </div>
  );
}
