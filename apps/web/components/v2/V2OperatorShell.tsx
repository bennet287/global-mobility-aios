"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  operatorNavigation,
  type OperatorNavLabel,
} from "../../lib/v2/operator-navigation";
import { V2Icon } from "./V2Icon";
import shellStyles from "./V2Shell.module.css";
import {
  V2_THEME_STORAGE_KEY,
  V2ThemeControl,
  isV2ThemePreference,
  type V2ThemePreference,
} from "./V2ThemeControl";

export function V2OperatorShell({
  children,
  activeItem = "Work",
}: {
  children: ReactNode;
  activeItem?: OperatorNavLabel;
}) {
  const [themePreference, setThemePreference] = useState<V2ThemePreference>("system");
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

  return (
    <div className="aios-v2-root" data-theme={themePreference}>
      <a className="aios-v2-skip-link" href="#aios-v2-operator-main">Skip to main content</a>

      <div className="aios-v2-shell">
        <aside className={`aios-v2-rail ${shellStyles.shellRail}`} aria-label="AIOS V2 Professional / Operator navigation">
          <div className="aios-v2-brand">
            <div className="aios-v2-brand-mark" aria-hidden="true">AI</div>
            <div className="aios-v2-brand-copy">
              <strong>AIOS</strong>
              <span>Professional workspace</span>
            </div>
          </div>

          <nav className="aios-v2-nav" aria-label="Professional / Operator">
            {operatorNavigation.map((item) => {
              const active = item.label === activeItem;
              if (item.enabled && item.href) {
                return (
                  <Link
                    className={`aios-v2-nav-item ${shellStyles.navItem}${active ? " active" : ""}`}
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
                  className={`aios-v2-nav-item ${shellStyles.navItem}`}
                  aria-disabled="true"
                  aria-label={`${item.label} (contextual workspace not yet migrated)`}
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
        </aside>

        <main className="aios-v2-main" id="aios-v2-operator-main">
          <div className={`aios-v2-topline ${shellStyles.topline}`}>
            <div className="aios-v2-topline-context">
              <strong>Professional / Operator</strong>
              <span>AIOS V2 migration</span>
            </div>
            <V2ThemeControl value={themePreference} onChange={changeTheme} />
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
